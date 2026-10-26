#!/usr/bin/env python3
"""下载并固定 MOSS-TTS-Nano 所需权重。

在镜像构建阶段执行，把两个 HuggingFace 仓库快照下载到 ``HF_HOME``，
并在 ``TTS_MODEL_LINK_DIR``（默认 /opt/models）建立稳定路径的软链接，
这样运行时的模型路径不依赖 snapshot 的哈希目录名。

本地开发也可以直接跑：``python tools/download_models.py``。
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path


REPOS = {
    # HuggingFace 仓库已从 MOSS-TTS-Nano 改名为 MOSS-TTS-Nano-100M。
    # 继续使用旧 ID 会触发跨仓库 307 跳转，新版 huggingface_hub 会拒绝下载。
    "MOSS-TTS-Nano": "OpenMOSS-Team/MOSS-TTS-Nano-100M",
    "MOSS-Audio-Tokenizer-Nano": "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano",
}


def _download_snapshot(repo_id: str) -> Path:
    from huggingface_hub import snapshot_download

    attempts = max(1, int(os.environ.get("MODEL_DOWNLOAD_RETRIES", "3")))
    for attempt in range(1, attempts + 1):
        try:
            return Path(snapshot_download(repo_id=repo_id, max_workers=4))
        except Exception as exc:  # noqa: BLE001 - 构建阶段需要重试网络错误
            if attempt >= attempts:
                raise
            wait_seconds = min(10 * attempt, 30)
            print(
                f"  attempt {attempt}/{attempts} failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )
            print(f"  retrying in {wait_seconds}s ...", flush=True)
            time.sleep(wait_seconds)
    raise RuntimeError(f"failed to download {repo_id}")


def main() -> int:
    link_dir = Path(os.environ.get("TTS_MODEL_LINK_DIR", "/opt/models"))
    link_dir.mkdir(parents=True, exist_ok=True)

    for name, repo_id in REPOS.items():
        print(f"downloading {repo_id} ...", flush=True)
        snapshot_path = _download_snapshot(repo_id)
        link_path = link_dir / name
        if link_path.is_symlink() or link_path.exists():
            if link_path.is_dir() and not link_path.is_symlink():
                print(f"  {link_path} 已存在目录，跳过软链接")
                continue
            link_path.unlink()
        link_path.symlink_to(snapshot_path)
        print(f"  {repo_id} -> {link_path}")

    print("models ready:", ", ".join(str(link_dir / name) for name in REPOS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
