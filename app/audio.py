"""音频编码工具：PCM / WAV / MP3 / Opus / AAC / FLAC。

模型输出是 float32 波形，这里负责：

- 转成 PCM s16le（流式播放用）
- 打包成 WAV（无 ffmpeg 也能用）
- 调用 ffmpeg 编码 mp3 / opus / aac / flac，并支持 atempo 变速率（不变调）
"""

from __future__ import annotations

import io
import logging
import shutil
import subprocess
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np


LOGGER = logging.getLogger(__name__)

# OpenAI response_format -> (ffmpeg 输出参数, MIME)
#
# wav / pcm 这里让 ffmpeg 只输出裸 PCM：RIFF 头由我们自己写，
# 因为 ffmpeg 往管道写 wav 时无法回填长度字段（会写成 0xFFFFFFFF），
# 播放器与 wave 库都会读错时长。
_FFMPEG_FORMATS: dict[str, tuple[list[str], str]] = {
    "mp3": (["-c:a", "libmp3lame", "-b:a", "128k", "-f", "mp3"], "audio/mpeg"),
    "opus": (["-c:a", "libopus", "-b:a", "64k", "-ar", "48000", "-f", "ogg"], "audio/ogg"),
    "aac": (["-c:a", "aac", "-b:a", "128k", "-f", "adts"], "audio/aac"),
    "flac": (["-c:a", "flac", "-f", "flac"], "audio/flac"),
    "wav": (["-f", "s16le"], "audio/wav"),
    "pcm": (["-f", "s16le"], "audio/pcm"),
}

MIME_TYPES: dict[str, str] = {
    "wav": "audio/wav",
    "pcm": "audio/pcm",
    **{name: mime for name, (_, mime) in _FFMPEG_FORMATS.items()},
}

SUPPORTED_FORMATS: tuple[str, ...] = ("mp3", "opus", "aac", "flac", "wav", "pcm")

# SSE 逐块编码：帧式容器可以按块独立编码并顺序拼接。
STREAMABLE_FORMATS: tuple[str, ...] = ("mp3", "aac", "pcm")

OPENAI_FORMAT_ALIASES: dict[str, str] = {
    "mp3": "mp3",
    "opus": "opus",
    "aac": "aac",
    "flac": "flac",
    "wav": "wav",
    "pcm": "pcm",
    "ogg": "opus",
    "mpeg": "mp3",
    "wave": "wav",
    "linear16": "pcm",
}


def normalize_format(value: str | None, default: str = "mp3") -> str:
    key = str(value or "").strip().lower()
    if not key:
        key = default
    resolved = OPENAI_FORMAT_ALIASES.get(key)
    if resolved is None:
        raise ValueError(
            f"Unsupported response_format: {value!r}. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )
    return resolved


def waveform_to_pcm16le(waveform: np.ndarray) -> bytes:
    """float32 波形（[-1, 1]，形状 [n] 或 [n, channels]）-> PCM s16le。"""
    array = np.asarray(waveform, dtype=np.float32)
    if array.size == 0:
        return b""
    clipped = np.clip(array, -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2", copy=False).tobytes()


def pcm16le_to_wav_bytes(pcm_bytes: bytes, sample_rate: int, channels: int) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(max(1, int(channels)))
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(pcm_bytes)
    return buffer.getvalue()


def _atempo_filter(speed: float) -> str:
    """把任意倍速拆成 ffmpeg atempo 支持的 0.5~2.0 区间。"""
    remaining = float(speed)
    parts: list[str] = []
    while remaining > 2.0:
        parts.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        parts.append("atempo=0.5")
        remaining /= 0.5
    parts.append(f"atempo={remaining:.6f}")
    return ",".join(parts)


@lru_cache(maxsize=4)
def ffmpeg_path(ffmpeg_bin: str = "ffmpeg") -> str | None:
    return shutil.which(ffmpeg_bin)


def _run_ffmpeg(args: list[str], stdin_bytes: bytes) -> bytes:
    process = subprocess.run(args, input=stdin_bytes, capture_output=True, check=False)
    if process.returncode != 0:
        message = process.stderr.decode("utf-8", errors="replace").strip().splitlines()
        detail = message[-1] if message else "unknown error"
        raise RuntimeError(f"ffmpeg failed ({process.returncode}): {detail}")
    return process.stdout


def _ffmpeg_encode(
    pcm: bytes,
    *,
    sample_rate: int,
    channels: int,
    output_args: list[str],
    speed: float,
    ffmpeg_bin: str,
    seekable_output: bool = False,
) -> bytes:
    """把裸 PCM 交给 ffmpeg，可选 atempo 变速。

    默认输出到管道；``seekable_output=True`` 时先写临时文件再读回，
    这样容器格式（如 flac）能回填总时长等元数据。
    """
    args = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-f",
        "s16le",
        "-ar",
        str(int(sample_rate)),
        "-ac",
        str(max(1, int(channels))),
        "-i",
        "pipe:0",
    ]
    if speed != 1.0:
        args += ["-filter:a", _atempo_filter(speed)]

    if not seekable_output:
        return _run_ffmpeg([*args, *output_args, "pipe:1"], pcm)

    with tempfile.NamedTemporaryFile(prefix="moss-tts-encode-", delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        process = subprocess.run(
            [*args, *output_args, str(temp_path)], input=pcm, capture_output=True, check=False
        )
        if process.returncode != 0:
            message = process.stderr.decode("utf-8", errors="replace").strip().splitlines()
            raise RuntimeError(f"ffmpeg failed ({process.returncode}): {message[-1] if message else 'unknown error'}")
        return temp_path.read_bytes()
    finally:
        temp_path.unlink(missing_ok=True)


def requires_ffmpeg(response_format: str, speed: float = 1.0) -> bool:
    """该格式/倍速是否需要 ffmpeg 编码。"""
    return normalize_format(response_format) in {"mp3", "opus", "aac", "flac"} or float(speed or 1.0) != 1.0


def encode_audio(
    waveform: np.ndarray,
    sample_rate: int,
    response_format: str = "mp3",
    speed: float = 1.0,
    *,
    ffmpeg_bin: str = "ffmpeg",
) -> tuple[bytes, str]:
    """把波形编码为指定格式，返回 (音频字节, MIME)。"""
    fmt = normalize_format(response_format)
    speed = float(speed or 1.0)
    if speed <= 0:
        raise ValueError("speed must be greater than 0")
    speed = min(max(speed, 0.25), 4.0)

    array = np.asarray(waveform, dtype=np.float32)
    channels = 1 if array.ndim == 1 else int(array.shape[1])
    pcm = waveform_to_pcm16le(array)

    if speed == 1.0:
        if fmt == "wav":
            return pcm16le_to_wav_bytes(pcm, sample_rate, channels), MIME_TYPES["wav"]
        if fmt == "pcm":
            return pcm, MIME_TYPES["pcm"]

    resolved_ffmpeg = ffmpeg_path(ffmpeg_bin)
    if resolved_ffmpeg is None:
        raise RuntimeError(
            f"编码 {fmt} / 变速需要 ffmpeg（未找到 {ffmpeg_bin!r}）；"
            "请安装 ffmpeg，或改用 response_format=wav / pcm 且 speed=1.0。"
        )

    output_args, media_type = _FFMPEG_FORMATS[fmt]
    encoded = _ffmpeg_encode(
        pcm,
        sample_rate=sample_rate,
        channels=channels,
        output_args=output_args,
        speed=speed,
        ffmpeg_bin=resolved_ffmpeg,
        # flac 走管道输出时无法回填总时长，改用临时文件
        seekable_output=fmt == "flac",
    )
    if fmt == "wav":
        # ffmpeg 只给了裸 PCM，这里补一个长度正确的 RIFF 头
        return pcm16le_to_wav_bytes(encoded, sample_rate, channels), MIME_TYPES["wav"]
    return encoded, media_type


def encode_pcm_chunk(waveform: np.ndarray) -> bytes:
    """流式分块编码（PCM s16le）。"""
    return waveform_to_pcm16le(waveform)
