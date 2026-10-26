#!/usr/bin/env python3
"""Minimal ONNX backend smoke test (CPU provider is sufficient for CI)."""

from __future__ import annotations

from app.config import settings
from app.onnx_service import OnnxTTSService
from app.voices import registry


def main() -> int:
    service = OnnxTTSService(settings, registry)
    service.warmup(voice="zh_taiwan")
    result = service.synthesize(
        text="你好，这是 ONNX 推理测试。",
        voice="zh_taiwan",
        mode="voice_clone",
        max_new_frames=75,
        voice_clone_max_text_tokens=75,
        do_sample=True,
        seed=1,
    )
    waveform = result["waveform_numpy"]
    assert result["sample_rate"] == 48000
    assert waveform.ndim == 2 and waveform.shape[0] > 0
    print("ONNX smoke OK", waveform.shape, result["audio_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
