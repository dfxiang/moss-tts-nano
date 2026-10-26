"""对上游 MOSS-TTS-Nano 运行时（vendor/upstream）的封装。

封装目标：

- 统一在 CPU 上串行执行推理（CPU 上并发跑只会互相抢核，反而更慢）
- 启动时后台预热（加载权重 + 跑一次短合成 + 预热文本正则化）
- 把「参考音频 voice clone」包装成固定音色目录
- 同时提供整段合成与流式合成两种能力
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Iterator, Optional

from .audio import encode_audio, waveform_to_pcm16le
from .config import UPSTREAM_DIR, Settings
from .models import resolve_model_reference
from .voices import VoiceRegistry


LOGGER = logging.getLogger(__name__)

# 上游运行时代码是 vendored 的顶层模块，按原样导入（保持与上游一致，便于同步升级）。
if str(UPSTREAM_DIR) not in sys.path:
    sys.path.insert(0, str(UPSTREAM_DIR))

from moss_tts_nano_runtime import NanoTTSService, VoicePreset  # noqa: E402
from text_normalization_pipeline import (  # noqa: E402
    WeTextProcessingManager,
    prepare_tts_request_texts,
)


class TTSEngine:
    def __init__(self, settings: Settings, registry: VoiceRegistry) -> None:
        self.settings = settings
        self.registry = registry

        self._run_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._warmup_thread: Optional[threading.Thread] = None
        self._warmup_state = "pending"
        self._warmup_message = "等待预热。"
        self._warmup_error: Optional[str] = None
        self._started_at = time.time()
        self._requests = 0
        self._generated_audio_seconds = 0.0
        self._generated_synthesis_seconds = 0.0
        self._sample_rate: Optional[int] = None
        self._channels: Optional[int] = None

        self._configure_numeric_precision()
        self._configure_cpu_threads()

        Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
        self._text_normalizer_manager = (
            WeTextProcessingManager() if settings.enable_text_normalization else None
        )
        if settings.backend == "onnx":
            from .onnx_service import OnnxTTSService

            self.checkpoint_path = settings.onnx_model_dir
            self.audio_tokenizer_path = settings.onnx_model_dir
            self._service = OnnxTTSService(settings, registry)
        else:
            # 离线优先：repo id 能命中本地 HF 缓存时换成本地快照目录
            self.checkpoint_path = resolve_model_reference(
                settings.checkpoint_path, require_tokenizer=True
            )
            self.audio_tokenizer_path = resolve_model_reference(settings.audio_tokenizer_path)
            self._service = NanoTTSService(
                checkpoint_path=self.checkpoint_path,
                audio_tokenizer_path=self.audio_tokenizer_path,
                device=settings.device,
                dtype=settings.dtype,
                attn_implementation=settings.attn_implementation,
                output_dir=settings.output_dir,
                voice_presets=self._build_voice_presets(),
            )
        self._prime_output_format()
        LOGGER.info(
            "TTS engine ready: device=%s dtype=%s attn=%s threads=%s voices=%d",
            self._service.device,
            self._service.dtype,
            self._service.attn_implementation or "model_default",
            self.cpu_threads,
            len(self.registry.voices),
        )

    def _prime_output_format(self) -> None:
        """尽量在首次请求前就知道输出采样率/声道数（流式响应头要用）。

        音频 tokenizer 的 config.json 里有 sample_rate / number_channels；
        模型以 HF repo id 形式提供时读不到，此时等预热或首次合成再补上。
        """
        if self.settings.backend == "onnx":
            codec_config = self._service.runtime.codec_meta["codec_config"]
            with self._state_lock:
                self._sample_rate = int(codec_config["sample_rate"])
                self._channels = int(codec_config["channels"])
            return

        config_path = Path(str(self.audio_tokenizer_path)) / "config.json"
        try:
            if not config_path.is_file():
                return
            import json

            config = json.loads(config_path.read_text(encoding="utf-8"))
            sample_rate = config.get("sample_rate") or config.get("sampling_rate")
            channels = config.get("number_channels")
            with self._state_lock:
                if sample_rate:
                    self._sample_rate = int(sample_rate)
                if channels:
                    self._channels = int(channels)
        except Exception:  # pragma: no cover - 仅影响响应头里的元信息
            LOGGER.debug("failed to prime output format from %s", config_path, exc_info=True)

    def _build_output_path(self, prefix: str) -> Path:
        return Path(self.settings.output_dir) / f"{prefix}-{uuid.uuid4().hex}.wav"

    # ---------------------------------------------------------------- 初始化

    def _configure_numeric_precision(self) -> None:
        """CUDA 上也使用完整 FP32 精度，避免 TF32 改变音频生成结果。"""
        import torch

        requested = self.settings.device.strip().lower()
        use_cuda = requested.startswith("cuda") or (
            requested == "auto" and torch.cuda.is_available()
        )
        if not use_cuda:
            return

        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.set_float32_matmul_precision("highest")
        LOGGER.info("CUDA numeric precision: TF32 disabled, float32_matmul_precision=highest")

    def _configure_cpu_threads(self) -> None:
        import torch

        requested = self.settings.cpu_threads
        resolved = requested if requested and requested > 0 else max(1, int(os.cpu_count() or 1))
        torch.set_num_threads(resolved)
        self.cpu_threads = resolved

    def _build_voice_presets(self) -> dict[str, VoicePreset]:
        return {
            voice.id: VoicePreset(
                name=voice.id,
                prompt_audio_path=voice.path,
                description=voice.description or voice.name,
            )
            for voice in self.registry.voices
        }

    # ------------------------------------------------------------------ 预热

    def start(self) -> None:
        with self._state_lock:
            if self._warmup_thread is not None:
                return
            self._warmup_thread = threading.Thread(
                target=self._run_warmup, name="moss-tts-warmup", daemon=True
            )
            self._warmup_thread.start()

    def _set_warmup(self, *, state: str, message: str, error: Optional[str] = None) -> None:
        with self._state_lock:
            self._warmup_state = state
            self._warmup_message = message
            self._warmup_error = error

    def _run_warmup(self) -> None:
        try:
            self._set_warmup(state="running", message="加载 MOSS-TTS-Nano 权重。")
            started = time.monotonic()
            self._service.get_model()
            LOGGER.info("model loaded in %.2fs", time.monotonic() - started)

            if self.settings.warmup:
                self._set_warmup(state="running", message="执行启动预热合成。")
                started = time.monotonic()
                with self._run_lock:
                    result = self._service.warmup(voice=self.registry.default_voice_id)
                    self._cleanup_audio_file(result.get("audio_path"))
                    self._record_audio_layout(int(result["sample_rate"]), result["waveform_numpy"])
                LOGGER.info("warmup synthesis finished in %.2fs", time.monotonic() - started)

            if self._text_normalizer_manager is not None:
                self._set_warmup(state="running", message="加载 WeTextProcessing 文本正则化。")
                snapshot = self._text_normalizer_manager.ensure_ready()
                if not snapshot.ready:
                    LOGGER.warning("text normalization unavailable: %s", snapshot.error or snapshot.message)

            self._set_warmup(state="ready", message="预热完成，可以开始合成。")
        except Exception as exc:  # noqa: BLE001 - 需要把失败原因透出到 /health
            LOGGER.exception("warmup failed")
            self._set_warmup(state="failed", message="预热失败。", error=_warmup_error_text(exc))


    def ensure_ready(self, timeout: Optional[float] = None) -> None:
        """等待预热完成；预热失败时抛错（由调用方转成 HTTP 错误）。"""
        self.start()
        thread = self._warmup_thread
        if thread is not None:
            thread.join(timeout=timeout)
        with self._state_lock:
            state = self._warmup_state
            message = self._warmup_message
            error = self._warmup_error
        if state == "ready":
            return
        if state == "failed":
            raise RuntimeError(error or message)
        raise TimeoutError(f"模型仍在预热中：{message}")

    def warmup_snapshot(self) -> dict[str, Any]:
        with self._state_lock:
            return {
                "state": self._warmup_state,
                "message": self._warmup_message,
                "error": self._warmup_error,
                "ready": self._warmup_state == "ready",
            }

    # -------------------------------------------------------------- 文本处理

    def prepare_text(self, *, text: str, voice_id: str, prompt_text: str = "") -> dict[str, Any]:
        return prepare_tts_request_texts(
            text=text,
            prompt_text=prompt_text,
            voice=voice_id,
            enable_wetext=bool(
                self.settings.enable_text_normalization and self._text_normalizer_manager is not None
            ),
            enable_normalize_tts_text=bool(self.settings.enable_normalize_tts_text),
            text_normalizer_manager=self._text_normalizer_manager,
        )

    # ---------------------------------------------------------------- 合成参数

    def _synth_kwargs(self, overrides: dict[str, Any]) -> dict[str, Any]:
        s = self.settings
        kwargs: dict[str, Any] = {
            "max_new_frames": s.max_new_frames,
            "voice_clone_max_text_tokens": s.voice_clone_max_text_tokens,
            "do_sample": s.do_sample,
            "text_temperature": s.text_temperature,
            "text_top_p": s.text_top_p,
            "text_top_k": s.text_top_k,
            "audio_temperature": s.audio_temperature,
            "audio_top_p": s.audio_top_p,
            "audio_top_k": s.audio_top_k,
            "audio_repetition_penalty": s.audio_repetition_penalty,
            "seed": None,
            "attn_implementation": s.attn_implementation,
        }
        for key, value in overrides.items():
            if value is None:
                continue
            if key not in kwargs:
                continue
            kwargs[key] = value
        return kwargs

    # -------------------------------------------------------------- 整段合成

    def synthesize(
        self,
        *,
        text: str,
        voice_id: str,
        response_format: str,
        speed: float,
        prompt_audio_path: Optional[str | Path] = None,
        prompt_text: str = "",
        overrides: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        voice = self.registry.get(voice_id)
        overrides = overrides or {}
        prepared = self.prepare_text(text=text, voice_id=voice.id, prompt_text=prompt_text)

        synth_kwargs = self._synth_kwargs(overrides)
        started = time.monotonic()
        output_path = self._build_output_path(f"synthesize-{voice.id}")
        chars = len(str(prepared["text"]))
        max_attempts = 1 + (self.settings.auto_retry_attempts if self.settings.auto_retry_degenerate else 0)
        attempts = 0
        best: Optional[dict[str, Any]] = None
        while True:
            attempts += 1
            try:
                with self._run_lock:
                    result = self._service.synthesize(
                        text=str(prepared["text"]),
                        mode="voice_clone",
                        voice=voice.id,
                        prompt_audio_path=prompt_audio_path,
                        prompt_text=prompt_text or None,
                        output_audio_path=output_path,
                        **synth_kwargs,
                    )
            finally:
                self._cleanup_audio_file(output_path)

            waveform = result["waveform_numpy"]
            sample_rate = int(result["sample_rate"])
            audio_seconds = float(len(waveform)) / float(sample_rate) if sample_rate else 0.0
            warning = _degenerate_reason(
                chars=chars,
                audio_seconds=audio_seconds,
                waveform=waveform,
                sample_rate=sample_rate,
                max_new_frames=synth_kwargs.get("max_new_frames"),
            )
            # 正常的（无告警）尝试最优；都异常时优先取短的（重复/静音型退化通常更长）
            penalty = -1.0 if not warning else audio_seconds
            if best is None or penalty < best["penalty"]:
                best = {
                    "penalty": penalty,
                    "result": result,
                    "waveform": waveform,
                    "sample_rate": sample_rate,
                    "audio_seconds": audio_seconds,
                    "warning": warning,
                }
            if not warning or attempts >= max_attempts:
                break
            LOGGER.warning(
                "合成结果异常（%s）：voice=%s chars=%d audio=%.2fs，自动换随机 seed 重试（第 %d 次）",
                warning,
                voice.id,
                chars,
                audio_seconds,
                attempts,
            )
            synth_kwargs["seed"] = None  # 换一次抽签，避免同一条退化轨迹
        elapsed = time.monotonic() - started
        result = best["result"]
        waveform = best["waveform"]
        sample_rate = best["sample_rate"]
        audio_seconds = best["audio_seconds"]
        warning = best["warning"]

        self._record_audio_layout(sample_rate, waveform)

        audio_bytes, media_type = encode_audio(
            waveform,
            sample_rate,
            response_format,
            speed,
            ffmpeg_bin=self.settings.ffmpeg_bin,
        )
        self._record_metrics(audio_seconds, elapsed)
        LOGGER.info(
            "synthesize: voice=%s chars=%d audio=%.2fs elapsed=%.2fs attempts=%d%s",
            voice.id,
            chars,
            audio_seconds,
            elapsed,
            attempts,
            f" [疑似未正常结束：{warning}]" if warning else "",
        )
        return {
            "audio_bytes": audio_bytes,
            "media_type": media_type,
            "sample_rate": sample_rate,
            "sample_width": 2,
            "channels": 1 if waveform.ndim == 1 else int(waveform.shape[1]),
            "audio_seconds": audio_seconds,
            "voice": voice,
            "elapsed_seconds": elapsed,
            "normalization": prepared,
            "text": str(prepared["text"]),
            "mode": "voice_clone",
            "input_chars": chars,
            "audio_suspect": bool(warning),
            "audio_warning": warning,
            "attempts": attempts,
        }

    # -------------------------------------------------------------- 流式合成

    def stream(
        self,
        *,
        text: str,
        voice_id: str,
        prompt_audio_path: Optional[str | Path] = None,
        prompt_text: str = "",
        overrides: Optional[dict[str, Any]] = None,
    ) -> Iterator[dict[str, Any]]:
        """边生成边产出 PCM 分块。

        产出事件：

        - ``{"type": "start", ...}``：文本已正则化，带上采样率等元信息
        - ``{"type": "audio", "pcm": bytes, ...}``：一块 16bit PCM
        - ``{"type": "done", ...}``：合成结束，附带统计信息
        """
        voice = self.registry.get(voice_id)
        overrides = overrides or {}
        prepared = self.prepare_text(text=text, voice_id=voice.id, prompt_text=prompt_text)
        synth_kwargs = self._synth_kwargs(overrides)
        # 流式接口不需要整段写盘，但运行时仍会写一个 wav；这里指定路径以便必定清理
        # （客户端中途断开时也能删掉，不残留临时文件）。
        output_path = self._build_output_path(f"stream-{voice.id}")
        started = time.monotonic()
        first_chunk_at: Optional[float] = None
        sample_rate = 0
        channels = 1
        emitted_seconds = 0.0

        try:
            with self._run_lock:
                events = self._service.synthesize_stream(
                    text=str(prepared["text"]),
                    mode="voice_clone",
                    voice=voice.id,
                    prompt_audio_path=prompt_audio_path,
                    prompt_text=prompt_text or None,
                    output_audio_path=output_path,
                    **synth_kwargs,
                )
                try:
                    for event in events:
                        event_type = str(event.get("type", ""))
                        if event_type == "audio":
                            waveform = event["waveform_numpy"]
                            if sample_rate == 0:
                                sample_rate = int(event["sample_rate"])
                            chunk_channels = 1 if waveform.ndim == 1 else int(waveform.shape[1])
                            channels = chunk_channels
                            pcm = waveform_to_pcm16le(waveform)
                            if not pcm:
                                continue
                            if first_chunk_at is None:
                                first_chunk_at = time.monotonic() - started
                            emitted_seconds = float(event.get("emitted_audio_seconds") or emitted_seconds)
                            yield {
                                "type": "audio",
                                "pcm": pcm,
                                "waveform": waveform,
                                "sample_rate": int(event["sample_rate"]),
                                "channels": chunk_channels,
                                "is_pause": bool(event.get("is_pause", False)),
                                "chunk_index": int(event.get("chunk_index", 0)),
                                "emitted_audio_seconds": emitted_seconds,
                            }
                            continue
                        if event_type == "result":
                            sample_rate = int(event.get("sample_rate") or sample_rate)
                            waveform = event["waveform_numpy"]
                            channels = 1 if waveform.ndim == 1 else int(waveform.shape[1])
                            elapsed = float(event.get("elapsed_seconds") or (time.monotonic() - started))
                            audio_seconds = float(len(waveform)) / float(sample_rate) if sample_rate else 0.0
                            self._record_audio_layout(sample_rate, waveform)
                            self._record_metrics(audio_seconds, elapsed)
                            chars = len(str(prepared["text"]))
                            audio_warning = _degenerate_reason(
                                chars=chars,
                                audio_seconds=audio_seconds,
                                waveform=waveform,
                                sample_rate=sample_rate,
                                max_new_frames=synth_kwargs.get("max_new_frames"),
                            )
                            LOGGER.info(
                                "stream: voice=%s chars=%d audio=%.2fs elapsed=%.2fs first_chunk=%s%s",
                                voice.id,
                                chars,
                                audio_seconds,
                                elapsed,
                                "n/a" if first_chunk_at is None else f"{first_chunk_at:.2f}s",
                                f" [疑似未正常结束：{audio_warning}]" if audio_warning else "",
                            )
                            yield {
                                "type": "done",
                                "sample_rate": sample_rate,
                                "channels": channels,
                                "audio_seconds": audio_seconds,
                                "elapsed_seconds": elapsed,
                                "first_chunk_seconds": first_chunk_at,
                                "voice": voice,
                                "normalization": prepared,
                                "text": str(prepared["text"]),
                                "input_chars": chars,
                                "audio_suspect": bool(audio_warning),
                                "audio_warning": audio_warning,
                            }
                finally:
                    # 客户端中途断开（例如网页点「停止」）时，外层生成器会被关闭，
                    # 但运行时生成器内部还持有推理锁；必须显式关闭它，
                    # 否则后续请求会一直等到它被垃圾回收才会恢复。
                    events.close()
        finally:
            self._cleanup_audio_file(output_path)

    def _cleanup_audio_file(self, path: Any) -> None:
        if not path:
            return
        try:
            Path(str(path)).unlink(missing_ok=True)
        except OSError:  # pragma: no cover - 清理失败不影响请求
            LOGGER.debug("failed to remove temporary audio file: %s", path)

    def _record_audio_layout(self, sample_rate: int, waveform: Any) -> None:
        """记录输出音频的采样率/声道数，供流式接口在响应头里返回。"""
        try:
            with self._state_lock:
                self._sample_rate = int(sample_rate)
                self._channels = 1 if waveform.ndim == 1 else int(waveform.shape[1])
        except Exception:  # pragma: no cover - 仅用于展示
            LOGGER.debug("failed to record output audio layout", exc_info=True)

    # ------------------------------------------------------------------ 统计

    def _record_metrics(self, audio_seconds: float, synthesis_seconds: float) -> None:
        with self._state_lock:
            self._requests += 1
            self._generated_audio_seconds += audio_seconds
            self._generated_synthesis_seconds += synthesis_seconds

    @property
    def sample_rate(self) -> Optional[int]:
        with self._state_lock:
            return self._sample_rate

    @property
    def channels(self) -> Optional[int]:
        with self._state_lock:
            return self._channels

    def status(self) -> dict[str, Any]:
        warmup = self.warmup_snapshot()
        with self._state_lock:
            requests = self._requests
            audio_seconds = self._generated_audio_seconds
            synthesis_seconds = self._generated_synthesis_seconds
        realtime_factor = (
            audio_seconds / synthesis_seconds if synthesis_seconds > 0 else None
        )
        return {
            "ready": warmup["ready"],
            "warmup": warmup,
            "backend": self.settings.backend,
            "device": str(self._service.device),
            "dtype": str(self._service.dtype),
            "attn_implementation": self._service.attn_implementation or "model_default",
            "onnx_execution_provider": (
                self.settings.onnx_execution_provider
                if self.settings.backend == "onnx"
                else None
            ),
            "cpu_threads": self.cpu_threads,
            "checkpoint": str(self._service.checkpoint_path),
            "audio_tokenizer": str(self._service.audio_tokenizer_path),
            "voices": len(self.registry.voices),
            "default_voice": self.registry.default_voice_id,
            "text_normalization": (
                None
                if self._text_normalizer_manager is None
                else self._text_normalizer_manager.snapshot().state
            ),
            "requests": requests,
            "generated_audio_seconds": round(audio_seconds, 3),
            "generated_synthesis_seconds": round(synthesis_seconds, 3),
            "realtime_factor": None if realtime_factor is None else round(realtime_factor, 3),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "uptime_seconds": round(time.time() - self._started_at, 1),
        }


# 中文实测约 5 字/秒（数字、英文会略慢），用于判断「音频是不是长得离谱」。
_CHARS_PER_SECOND = 5.0
# 音频 tokenizer 的帧率：48kHz ÷ downsample_rate(3840) = 12.5 帧/秒
_FRAME_RATE = 12.5


def _expected_audio_seconds(chars: int) -> float:
    return max(2.0, float(chars) / _CHARS_PER_SECOND)


def _silence_profile(waveform: Any, sample_rate: int, *, window: float = 0.02, threshold: float = 0.005):
    """返回 (静音总秒数, 最长连续静音秒数)，20ms 一帧按 RMS 判定。"""
    import numpy as np

    array = np.asarray(waveform, dtype=np.float32)
    if array.ndim > 1:
        array = array.mean(axis=1)
    if array.size == 0 or sample_rate <= 0:
        return 0.0, 0.0
    win = max(1, int(window * sample_rate))
    usable = array.size // win * win
    if usable == 0:
        return 0.0, 0.0
    rms = np.sqrt((array[:usable].reshape(-1, win) ** 2).mean(axis=1))
    silent = rms < threshold
    total = float(silent.sum()) * win / float(sample_rate)
    longest = current = 0
    for flag in silent:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return total, longest * win / float(sample_rate)


def _degenerate_reason(
    *,
    chars: int,
    audio_seconds: float,
    waveform: Any,
    sample_rate: int,
    max_new_frames: Optional[int] = None,
) -> str:
    """判断这一轮合成是不是退化输出（返回原因，空字符串表示正常）。

    成因通常是模型这一轮没吐出结束符（audio_end_token），一路生成到 ``max_new_frames``
    的帧上限（默认 375 帧 ÷ 12.5 帧/秒 = 30 秒），听感上像同一句话被反复重复。
    """
    if audio_seconds <= 0:
        return "生成音频为空"

    reasons: list[str] = []
    expected = _expected_audio_seconds(chars)
    if audio_seconds > expected * 2.0 + 3.0:
        reasons.append(f"时长 {audio_seconds:.1f}s 远超文本预期 {expected:.1f}s")

    silence_total, silence_longest = _silence_profile(waveform, sample_rate)
    if audio_seconds > 8 and silence_total > audio_seconds * 0.4:
        reasons.append(f"静音占比 {silence_total / audio_seconds:.0%}")
    if silence_longest > 3.0:
        reasons.append(f"最长连续静音 {silence_longest:.1f}s")

    if max_new_frames and abs(audio_seconds - int(max_new_frames) / _FRAME_RATE) < 0.06:
        # 撞上限本身不一定算异常（调用方可能故意压低 max_new_frames），只记录
        LOGGER.info("音频正好压在 max_new_frames 上限（%.2fs），可能被截断", audio_seconds)

    return "；".join(reasons)


def _warmup_error_text(exc: BaseException) -> str:
    """给模型加载失败补一句可操作的提示。"""
    message = str(exc)
    looks_like_cache_problem = isinstance(exc, FileNotFoundError) or any(
        token in message for token in ("LocalEntryNotFound", "Cannot find the requested files", "couldn't connect")
    )
    if not looks_like_cache_problem:
        return message
    return (
        f"{message} | 本地模型缓存可能不完整或不可用：可以 1) 用默认镜像（权重已预置，"
        "不需要挂载缓存）；2) 在能联网的机器上执行 `python tools/download_models.py` 补全缓存后挂载；"
        "3) 只挂载缓存时加 `-e HF_HUB_OFFLINE=1`。"
    )
