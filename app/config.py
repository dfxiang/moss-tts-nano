"""服务配置。

所有配置项都可以通过环境变量覆盖，默认值面向 CPU 容器化部署
（与上游 app.py 在 CPU 上的默认参数保持一致）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .models import prepare_huggingface_offline_mode


REPO_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_DIR = REPO_ROOT / "vendor" / "upstream"
VOICE_PROMPT_DIR = UPSTREAM_DIR / "assets" / "audio"
WEB_DIR = Path(__file__).resolve().parent / "web"


def _env_str(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(float(raw.strip()))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw.strip())
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_optional_str(name: str, default: str = "") -> str:
    """可为空的配置项：显式设成空值 / 0 / off / none / - 表示关闭。"""
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip()
    if value.lower() in {"", "0", "off", "none", "false", "-"}:
        return ""
    return value


def _model_source(env_name: str, local_dir: str, repo_id: str) -> str:
    """优先使用环境变量；否则若镜像内已预下载模型，就用本地快照目录。"""
    value = os.environ.get(env_name)
    if value is not None and value.strip():
        return value.strip()
    if Path(local_dir).is_dir():
        return local_dir
    return repo_id


@dataclass(frozen=True)
class Settings:
    # ---- 模型 ----
    backend: str = "native"
    checkpoint_path: str = "OpenMOSS-Team/MOSS-TTS-Nano-100M"
    audio_tokenizer_path: str = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano"
    onnx_model_dir: str = "/opt/onnx_models"
    onnx_execution_provider: str = "cpu"
    device: str = "cpu"
    dtype: str = "float32"
    attn_implementation: str = "eager"
    cpu_threads: int = 0
    warmup: bool = True
    output_dir: str = ""

    # ---- 服务 ----
    host: str = "0.0.0.0"
    port: int = 8000
    api_key: str = ""
    cors_origins: str = "*"
    log_level: str = "INFO"
    max_concurrency: int = 1
    max_input_chars: int = 8192
    request_timeout_seconds: float = 600.0
    # 挂载进来的参考音频目录：里面的音频会注册成音色（id = 文件名），空字符串表示关闭。
    voice_dir: str = ""

    # ---- 合成默认值（与上游 app.py 的 CPU 默认一致）----
    default_voice: str = "zh_taiwan"
    default_response_format: str = "mp3"
    max_new_frames: int = 375
    voice_clone_max_text_tokens: int = 75
    # 生成结果明显异常（音频远长于文本 / 大段静音）时自动换随机 seed 重试
    auto_retry_degenerate: bool = True
    auto_retry_attempts: int = 1
    do_sample: bool = True
    text_temperature: float = 1.0
    text_top_p: float = 1.0
    text_top_k: int = 50
    audio_temperature: float = 0.8
    audio_top_p: float = 0.95
    audio_top_k: int = 25
    audio_repetition_penalty: float = 1.2

    # ---- 文本正则化 ----
    enable_text_normalization: bool = True
    enable_normalize_tts_text: bool = True

    # ---- 音频编码 ----
    ffmpeg_bin: str = "ffmpeg"

    @classmethod
    def from_env(cls) -> "Settings":
        default_output_dir = str(Path(os.environ.get("TMPDIR", "/tmp")) / "moss-tts-nano")
        model_link_dir = os.environ.get("TTS_MODEL_LINK_DIR", "/opt/models")
        return cls(
            backend=_env_str("TTS_BACKEND", "native").lower(),
            checkpoint_path=_model_source(
                "TTS_CHECKPOINT_PATH",
                str(Path(model_link_dir) / "MOSS-TTS-Nano"),
                "OpenMOSS-Team/MOSS-TTS-Nano-100M",
            ),
            audio_tokenizer_path=_model_source(
                "TTS_AUDIO_TOKENIZER_PATH",
                str(Path(model_link_dir) / "MOSS-Audio-Tokenizer-Nano"),
                "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano",
            ),
            onnx_model_dir=_env_str("TTS_ONNX_MODEL_DIR", "/opt/onnx_models"),
            onnx_execution_provider=_env_str("TTS_ONNX_EXECUTION_PROVIDER", "cpu").lower(),
            device=_env_str("TTS_DEVICE", "cpu"),
            dtype=_env_str("TTS_DTYPE", "float32"),
            attn_implementation=_env_str("TTS_ATTN_IMPLEMENTATION", "eager"),
            cpu_threads=_env_int("TTS_CPU_THREADS", 0),
            warmup=_env_bool("TTS_WARMUP", True),
            output_dir=_env_str("TTS_OUTPUT_DIR", default_output_dir),
            host=_env_str("TTS_HOST", "0.0.0.0"),
            port=_env_int("TTS_PORT", 8000),
            api_key=_env_str("TTS_API_KEY", ""),
            cors_origins=_env_str("TTS_CORS_ORIGINS", "*"),
            log_level=_env_str("TTS_LOG_LEVEL", "INFO").upper(),
            max_concurrency=max(1, _env_int("TTS_MAX_CONCURRENCY", 1)),
            max_input_chars=max(1, _env_int("TTS_MAX_INPUT_CHARS", 8192)),
            request_timeout_seconds=_env_float("TTS_REQUEST_TIMEOUT_SECONDS", 600.0),
            voice_dir=_env_optional_str("TTS_VOICE_DIR", ""),
            default_voice=_env_str("TTS_DEFAULT_VOICE", "zh_taiwan"),
            default_response_format=_env_str("TTS_DEFAULT_RESPONSE_FORMAT", "mp3"),
            max_new_frames=_env_int("TTS_MAX_NEW_FRAMES", 375),
            voice_clone_max_text_tokens=_env_int("TTS_VOICE_CLONE_MAX_TEXT_TOKENS", 75),
            auto_retry_degenerate=_env_bool("TTS_AUTO_RETRY_DEGENERATE", True),
            auto_retry_attempts=max(0, _env_int("TTS_AUTO_RETRY_ATTEMPTS", 1)),
            do_sample=_env_bool("TTS_DO_SAMPLE", True),
            text_temperature=_env_float("TTS_TEXT_TEMPERATURE", 1.0),
            text_top_p=_env_float("TTS_TEXT_TOP_P", 1.0),
            text_top_k=_env_int("TTS_TEXT_TOP_K", 50),
            audio_temperature=_env_float("TTS_AUDIO_TEMPERATURE", 0.8),
            audio_top_p=_env_float("TTS_AUDIO_TOP_P", 0.95),
            audio_top_k=_env_int("TTS_AUDIO_TOP_K", 25),
            audio_repetition_penalty=_env_float("TTS_AUDIO_REPETITION_PENALTY", 1.2),
            enable_text_normalization=_env_bool("TTS_ENABLE_TEXT_NORMALIZATION", True),
            enable_normalize_tts_text=_env_bool("TTS_ENABLE_NORMALIZE_TTS_TEXT", True),
            ffmpeg_bin=_env_str("TTS_FFMPEG_BIN", "ffmpeg"),
        )


settings = Settings.from_env()

# 必须在 transformers / huggingface_hub 被导入之前决定离线模式：
# 它们在 import 时会读取 HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE。
# app.engine 在导入 vendored 运行时的时候会导入 transformers，
# 而 engine 又先导入本模块，所以放在这里是安全的。
prepare_huggingface_offline_mode(settings.checkpoint_path, settings.audio_tokenizer_path)
