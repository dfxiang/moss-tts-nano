"""ONNX Runtime backend for MOSS-TTS-Nano."""

from __future__ import annotations

import os
import queue
import threading
import time
from pathlib import Path
from typing import Any, Iterator, Optional

import numpy as np

from onnx_tts_runtime import (
    OnnxTtsRuntime,
    _concat_waveforms,
    _merge_audio_channels,
    _write_waveform_to_wav,
)
from ort_cpu_runtime import _resolve_stream_decode_frame_budget

from .config import Settings
from .voices import VoiceRegistry


class _DeviceInfo:
    def __init__(self, device_type: str) -> None:
        self.type = device_type

    def __str__(self) -> str:
        return self.type


class OnnxTTSService:
    """Expose the official ONNX runtime with the interface used by TTSEngine."""

    def __init__(self, settings: Settings, registry: VoiceRegistry) -> None:
        self.settings = settings
        self.registry = registry
        thread_count = settings.cpu_threads or max(1, int(os.cpu_count() or 1))
        self.runtime = OnnxTtsRuntime(
            model_dir=settings.onnx_model_dir,
            thread_count=thread_count,
            max_new_frames=settings.max_new_frames,
            execution_provider=settings.onnx_execution_provider,
            output_dir=settings.output_dir,
        )
        provider = self.runtime.execution_provider
        self.device = _DeviceInfo("cuda" if provider == "cuda" else "cpu")
        self.dtype = "float32"
        self.attn_implementation = f"onnxruntime_{provider}"
        self.checkpoint_path = str(self.runtime.tts_meta_path.parent.resolve())
        self.audio_tokenizer_path = str(self.runtime.codec_meta_path.parent.resolve())
        self.cpu_threads = thread_count

    def get_model(self):
        return self.runtime

    def warmup(self, *, voice: str | None = None) -> dict[str, Any]:
        self.runtime.warmup()
        sample_rate = int(self.runtime.codec_meta["codec_config"]["sample_rate"])
        channels = int(self.runtime.codec_meta["codec_config"]["channels"])
        return {
            "audio_path": None,
            "sample_rate": sample_rate,
            "waveform_numpy": np.zeros((0, channels), dtype=np.float32),
        }

    def _prompt_audio_path(self, voice_id: str, explicit: str | Path | None) -> str:
        if explicit:
            return str(Path(explicit).expanduser().resolve())
        return str(self.registry.get(voice_id).path)

    def _configure_generation(
        self,
        *,
        max_new_frames: int,
        do_sample: bool,
        text_temperature: float,
        text_top_p: float,
        text_top_k: int,
        audio_temperature: float,
        audio_top_p: float,
        audio_top_k: int,
        audio_repetition_penalty: float,
    ) -> None:
        defaults = self.runtime.manifest["generation_defaults"]
        defaults["max_new_frames"] = int(max_new_frames)
        # 官方 ONNX 默认使用模型内烘焙的 fixed sampling 节点；
        # full 会绕过该节点并在 Python 里重新采样。
        defaults["sample_mode"] = "fixed" if do_sample else "greedy"
        defaults["do_sample"] = bool(do_sample)
        defaults["text_temperature"] = float(text_temperature)
        defaults["text_top_p"] = float(text_top_p)
        defaults["text_top_k"] = int(text_top_k)
        defaults["audio_temperature"] = float(audio_temperature)
        defaults["audio_top_p"] = float(audio_top_p)
        defaults["audio_top_k"] = int(audio_top_k)
        defaults["audio_repetition_penalty"] = float(audio_repetition_penalty)

    def synthesize(
        self,
        *,
        text: str,
        mode: str,
        voice: str,
        prompt_audio_path: Optional[str | Path] = None,
        prompt_text: str = "",
        output_audio_path: Optional[str | Path] = None,
        max_new_frames: int = 375,
        voice_clone_max_text_tokens: int = 75,
        do_sample: bool = True,
        text_temperature: float = 1.0,
        text_top_p: float = 1.0,
        text_top_k: int = 50,
        audio_temperature: float = 0.8,
        audio_top_p: float = 0.95,
        audio_top_k: int = 25,
        audio_repetition_penalty: float = 1.2,
        seed: int | None = None,
        attn_implementation: str | None = None,
        **_unused: Any,
    ) -> dict[str, Any]:
        del mode, prompt_text, attn_implementation
        reference = self._prompt_audio_path(voice, prompt_audio_path)
        self._configure_generation(
            max_new_frames=max_new_frames,
            do_sample=do_sample,
            text_temperature=text_temperature,
            text_top_p=text_top_p,
            text_top_k=text_top_k,
            audio_temperature=audio_temperature,
            audio_top_p=audio_top_p,
            audio_top_k=audio_top_k,
            audio_repetition_penalty=audio_repetition_penalty,
        )
        started = time.perf_counter()
        result = self.runtime.synthesize(
            text=text,
            prompt_audio_path=reference,
            output_audio_path=output_audio_path,
            sample_mode="fixed" if do_sample else "greedy",
            do_sample=do_sample,
            streaming=False,
            max_new_frames=max_new_frames,
            voice_clone_max_text_tokens=voice_clone_max_text_tokens,
            enable_wetext=False,
            enable_normalize_tts_text=False,
            seed=seed,
        )
        waveform = np.asarray(result["waveform"], dtype=np.float32)
        return {
            "audio_path": str(result["audio_path"]),
            "waveform_numpy": waveform,
            "sample_rate": int(result["sample_rate"]),
            "elapsed_seconds": time.perf_counter() - started,
            "mode": "voice_clone",
            "voice": voice,
            "prompt_audio_path": reference,
            "voice_clone_text_chunks": list(result.get("text_chunks", [])),
            "effective_global_attn_implementation": self.attn_implementation,
            "effective_local_attn_implementation": self.attn_implementation,
        }

    def synthesize_stream(
        self,
        *,
        text: str,
        mode: str,
        voice: str,
        prompt_audio_path: Optional[str | Path] = None,
        prompt_text: str = "",
        output_audio_path: Optional[str | Path] = None,
        max_new_frames: int = 375,
        voice_clone_max_text_tokens: int = 75,
        do_sample: bool = True,
        text_temperature: float = 1.0,
        text_top_p: float = 1.0,
        text_top_k: int = 50,
        audio_temperature: float = 0.8,
        audio_top_p: float = 0.95,
        audio_top_k: int = 25,
        audio_repetition_penalty: float = 1.2,
        seed: int | None = None,
        attn_implementation: str | None = None,
        **_unused: Any,
    ) -> Iterator[dict[str, Any]]:
        del mode, prompt_text, attn_implementation
        reference = self._prompt_audio_path(voice, prompt_audio_path)
        self._configure_generation(
            max_new_frames=max_new_frames,
            do_sample=do_sample,
            text_temperature=text_temperature,
            text_top_p=text_top_p,
            text_top_k=text_top_k,
            audio_temperature=audio_temperature,
            audio_top_p=audio_top_p,
            audio_top_k=audio_top_k,
            audio_repetition_penalty=audio_repetition_penalty,
        )
        if seed is not None:
            self.runtime.rng = np.random.default_rng(int(seed))

        events: "queue.Queue[dict[str, Any] | None]" = queue.Queue(maxsize=64)

        def worker() -> None:
            try:
                prompt_codes = self.runtime.resolve_prompt_audio_codes(
                    voice=None, prompt_audio_path=reference
                )
                chunks = self.runtime.split_voice_clone_text(
                    str(text or ""), max_tokens=int(voice_clone_max_text_tokens)
                )
                sample_rate = int(self.runtime.codec_meta["codec_config"]["sample_rate"])
                channels = int(self.runtime.codec_meta["codec_config"]["channels"])
                waveforms: list[np.ndarray] = []
                total_samples = 0
                first_audio_at: float | None = None
                started = time.perf_counter()

                for chunk_index, chunk_text in enumerate(chunks):
                    text_ids = self.runtime.encode_text(chunk_text)
                    request_rows = self.runtime.build_voice_clone_request_rows(prompt_codes, text_ids)
                    pending_frames: list[list[int]] = []
                    chunk_waveforms: list[np.ndarray] = []
                    self.runtime.codec_streaming_session.reset()

                    def emit(waveform: np.ndarray, is_pause: bool = False) -> None:
                        nonlocal total_samples, first_audio_at
                        waveform = np.asarray(waveform, dtype=np.float32)
                        if waveform.size == 0:
                            return
                        if first_audio_at is None and not is_pause:
                            first_audio_at = time.perf_counter()
                        total_samples += int(waveform.shape[0])
                        waveforms.append(waveform)
                        chunk_waveforms.append(waveform)
                        lead = 0.0
                        if first_audio_at is not None:
                            lead = total_samples / sample_rate - (time.perf_counter() - first_audio_at)
                        events.put(
                            {
                                "type": "audio",
                                "waveform_numpy": waveform,
                                "sample_rate": sample_rate,
                                "chunk_index": chunk_index,
                                "emitted_audio_seconds": total_samples / sample_rate,
                                "lead_seconds": lead,
                                "is_pause": is_pause,
                            }
                        )

                    def decode_pending(force: bool) -> None:
                        if not pending_frames:
                            return
                        budget = _resolve_stream_decode_frame_budget(
                            total_samples, sample_rate, first_audio_at
                        )
                        if not force and len(pending_frames) < max(1, budget):
                            return
                        count = len(pending_frames) if force else min(len(pending_frames), max(1, budget))
                        frame_chunk = pending_frames[:count]
                        del pending_frames[:count]
                        decoded = self.runtime.codec_streaming_session.run_frames(frame_chunk)
                        if decoded is None:
                            return
                        audio, audio_length = decoded
                        if audio_length <= 0:
                            return
                        channel_arrays = [
                            audio[0, channel_index, :audio_length]
                            for channel_index in range(audio.shape[1])
                        ]
                        emit(_merge_audio_channels(channel_arrays))

                    def on_frame(_items: list[list[int]], _index: int, frame: list[int]) -> None:
                        pending_frames.append(list(frame))
                        decode_pending(False)

                    try:
                        self.runtime.generate_audio_frames(request_rows, on_frame=on_frame)
                        decode_pending(True)
                    finally:
                        self.runtime.codec_streaming_session.reset()

                    if chunk_index < len(chunks) - 1:
                        pause_seconds = self.runtime.estimate_voice_clone_inter_chunk_pause_seconds(
                            chunk_text
                        )
                        pause_samples = max(0, int(round(sample_rate * pause_seconds)))
                        if pause_samples:
                            emit(np.zeros((pause_samples, channels), dtype=np.float32), True)

                waveform = _concat_waveforms(waveforms)
                path = Path(output_audio_path) if output_audio_path else (
                    Path(self.settings.output_dir) / "onnx-stream.wav"
                )
                audio_path = _write_waveform_to_wav(path, waveform, sample_rate)
                events.put(
                    {
                        "type": "result",
                        "audio_path": str(audio_path),
                        "waveform_numpy": waveform,
                        "sample_rate": sample_rate,
                        "elapsed_seconds": time.perf_counter() - started,
                        "voice": voice,
                        "prompt_audio_path": reference,
                        "voice_clone_text_chunks": chunks,
                        "effective_global_attn_implementation": self.attn_implementation,
                        "effective_local_attn_implementation": self.attn_implementation,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                events.put({"type": "error", "error": str(exc)})
            finally:
                events.put(None)

        thread = threading.Thread(target=worker, name="onnx-tts-stream", daemon=True)
        thread.start()
        while True:
            item = events.get()
            if item is None:
                break
            if item.get("type") == "error":
                raise RuntimeError(str(item.get("error") or "ONNX streaming failed"))
            yield item
