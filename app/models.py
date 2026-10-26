"""模型路径解析。

如果直接使用 HuggingFace repo id（例如 ``OpenMOSS-Team/MOSS-TTS-Nano-100M``），
transformers / huggingface_hub 会先联网做 HEAD 探测；在离线或网络受限的环境里
每个文件都要重试 5 次（几十秒），启动看起来就像卡死。

所以这里统一做「离线优先」解析：

1. 已经是本地目录 -> 直接使用；
2. 是 repo id 且本地 HF 缓存里已经有完整快照 -> 换成快照目录（运行时完全不联网）；
3. 否则保持原样，交给 transformers 联网下载。

另外还有一个容易踩的坑：本地缓存里的 snapshots 目录**可能是不完整的**
（transformers 会把远程代码单独缓存在 ``modules/`` 下，hub 快照里可能只有
config.json 和权重）。这种情况下直接把 repo id 当成「本地目录」用会报
``FileNotFoundError: .../prompting.py``，所以第 2 步只对「文件齐全」的快照生效；
快照不齐时保持 repo id，并让 ``prepare_huggingface_offline_mode`` 打开离线模式，
让 transformers 直接走模块缓存，而不是先卡在网络探测上。
"""

from __future__ import annotations

import ast
import logging
import os
from pathlib import Path
from typing import Optional


LOGGER = logging.getLogger(__name__)

#: 本地目录加载时必须存在的文件（缺任何一个都说明快照不完整）
_REQUIRED_FILES = ("config.json",)
_WEIGHT_FILES = ("pytorch_model.bin", "model.safetensors", "model.safetensors.index.json")
_TOKENIZER_FILES = ("tokenizer.model", "tokenizer.json", "spiece.model", "vocab.json")

#: 是否由本模块打开了离线模式（供 /health 与启动日志展示）
_offline_mode_enabled = False


def offline_mode_enabled() -> bool:
    return _offline_mode_enabled


def looks_like_repo_id(value: str) -> bool:
    raw = str(value or "").strip()
    if not raw or " " in raw or "://" in raw:
        return False
    if raw.startswith(("/", "./", "../", "~", ".")):
        return False
    return raw.count("/") == 1


def hub_cache_dir() -> Path:
    """本地 HuggingFace hub 缓存目录。"""
    explicit = os.environ.get("HF_HUB_CACHE") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if explicit:
        return Path(explicit).expanduser()
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        return Path(hf_home).expanduser() / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def modules_cache_dir() -> Path:
    """transformers 远程代码缓存目录（trust_remote_code 用）。"""
    explicit = os.environ.get("HF_MODULES_CACHE")
    if explicit:
        return Path(explicit).expanduser()
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        return Path(hf_home).expanduser() / "modules"
    return Path.home() / ".cache" / "huggingface" / "modules"


def _hub_repo_dir(repo_id: str) -> Path:
    return hub_cache_dir() / f"models--{repo_id.replace('/', '--')}"


def cache_has_repo(repo_id: str) -> bool:
    """本地 hub 缓存里是否有该 repo 的快照（不校验完整性）。"""
    repo_dir = _hub_repo_dir(repo_id)
    snapshots = repo_dir / "snapshots"
    try:
        return snapshots.is_dir() and any(snapshots.iterdir())
    except OSError:
        return False


def _relative_import_files(module_path: Path) -> set[str]:
    """模块里的相对 import（``from .x import y`` -> ``x.py``）。"""
    try:
        tree = ast.parse(module_path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return set()
    needed: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level and node.module:
            needed.add(node.module.replace(".", "/") + ".py")
        elif isinstance(node, ast.ImportFrom) and node.level and not node.module:
            needed.update(f"{alias.name}.py" for alias in node.names)
    return needed


def _auto_map_entries(snapshot: Path) -> list[str]:
    try:
        import json

        config = json.loads((snapshot / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    entries: list[str] = []
    for value in (config.get("auto_map") or {}).values():
        if not isinstance(value, str):
            continue
        entries.extend(part for part in value.split(",") if part)
    files: list[str] = []
    for entry in entries:
        module = entry.split(".")[0].strip()
        if module and f"{module}.py" not in files:
            files.append(f"{module}.py")
    return files


def snapshot_is_self_contained(snapshot: Path, *, require_tokenizer: bool = False) -> bool:
    """快照能否作为「本地目录」直接加载（远程代码、tokenizer、权重都要在）。"""
    if not snapshot.is_dir():
        return False
    if not all((snapshot / name).is_file() for name in _REQUIRED_FILES):
        return False
    if not any((snapshot / name).is_file() for name in _WEIGHT_FILES):
        return False
    # 语音合成模型需要文本 tokenizer；音频 tokenizer（codec）仓库没有这些文件。
    if require_tokenizer and not any((snapshot / name).is_file() for name in _TOKENIZER_FILES):
        return False

    pending = _auto_map_entries(snapshot)
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        path = snapshot / name
        if not path.is_file():
            LOGGER.debug("快照缺少远程代码文件: %s", path)
            return False
        pending.extend(_relative_import_files(path) - seen)
    return True


def local_snapshot_path(repo_id: str) -> Optional[str]:
    """在本地 HF 缓存里找 repo 的完整快照（不联网）。"""
    try:
        from huggingface_hub import snapshot_download

        path = snapshot_download(repo_id=repo_id, local_files_only=True)
    except Exception as exc:  # noqa: BLE001 - 缓存未命中属于正常情况
        LOGGER.debug("本地缓存中没有 %s 的完整快照: %s", repo_id, exc)
        return None
    return str(Path(path).resolve())


def resolve_model_reference(value: str, *, require_tokenizer: bool = False) -> str:
    """把 repo id 解析成本地快照目录（能解析就解析，不能就原样返回）。"""
    raw = str(value or "").strip()
    if not raw:
        return raw

    path = Path(raw).expanduser()
    if path.exists():
        return str(path.resolve())

    if not looks_like_repo_id(raw):
        return raw

    local = local_snapshot_path(raw)
    if local is not None:
        snapshot = Path(local)
        if not snapshot_is_self_contained(snapshot, require_tokenizer=require_tokenizer):
            # 快照不齐（常见：远程代码只在 modules 缓存里），
            # 直接用本地目录会报 FileNotFoundError，保持 repo id 更稳。
            LOGGER.info(
                "本地快照 %s 不完整（缺少部分远程代码/tokenizer 文件），保留 repo id 并用本地缓存加载",
                snapshot,
            )
            return raw
        LOGGER.info("模型 %s 命中本地缓存，使用 %s（运行时无需联网）", raw, local)
        return local

    LOGGER.warning(
        "模型 %s 不在本地 HuggingFace 缓存中，启动时会尝试联网下载；"
        "离线环境请挂载缓存目录（HF_HOME），或使用构建时已预下载权重的镜像。",
        raw,
    )
    return raw


def prepare_huggingface_offline_mode(*references: str) -> bool:
    """本地缓存里已有模型时，打开 HF 离线模式，跳过联网探测。

    必须在导入 transformers / huggingface_hub **之前** 调用
    （它们在 import 时读取 ``HF_HUB_OFFLINE`` / ``TRANSFORMERS_OFFLINE``），
    所以这里是 ``app/config.py`` 在构造 Settings 之后立刻调用的。

    背景：容器里网络受限时，huggingface_hub 对每个文件都会重试 5 次
    （每次几秒到几十秒），启动会看起来像卡死；而缓存本身其实够用。

    设置 ``TTS_HF_OFFLINE=0`` 可以关掉这个自动行为。
    """
    if os.environ.get("TTS_HF_OFFLINE", "1").strip().lower() in {"0", "false", "no", "off"}:
        return False
    if os.environ.get("HF_HUB_OFFLINE", "").strip() or os.environ.get("TRANSFORMERS_OFFLINE", "").strip():
        return False  # 用户已经显式配置过，不覆盖

    repo_ids = [ref for ref in references if looks_like_repo_id(ref)]
    if not repo_ids:
        return False
    if not all(cache_has_repo(repo_id) for repo_id in repo_ids):
        return False  # 缓存里没有，得联网下载

    global _offline_mode_enabled
    _offline_mode_enabled = True
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    LOGGER.info(
        "检测到本地 HuggingFace 缓存已包含 %s，启用离线模式（HF_HUB_OFFLINE=1），跳过联网探测",
        ", ".join(repo_ids),
    )
    return True
