#!/usr/bin/env python3
"""Download the official ONNX model assets into the image."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path


REPOS = {
    "MOSS-TTS-Nano-100M-ONNX": (
        "OpenMOSS-Team/MOSS-TTS-Nano-100M-ONNX",
        ("*.onnx", "*.data", "*.json", "tokenizer.model"),
    ),
    "MOSS-Audio-Tokenizer-Nano-ONNX": (
        "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX",
        ("*.onnx", "*.data", "*.json"),
    ),
}


def _download(repo_id: str, local_dir: Path, patterns: tuple[str, ...]) -> None:
    from huggingface_hub import snapshot_download

    attempts = max(1, int(os.environ.get("MODEL_DOWNLOAD_RETRIES", "3")))
    for attempt in range(1, attempts + 1):
        try:
            snapshot_download(
                repo_id=repo_id,
                local_dir=str(local_dir),
                local_dir_use_symlinks=False,
                allow_patterns=list(patterns),
                max_workers=4,
            )
            return
        except Exception as exc:  # noqa: BLE001
            if attempt >= attempts:
                raise
            wait_seconds = min(10 * attempt, 30)
            print(
                f"  attempt {attempt}/{attempts} failed: {type(exc).__name__}: {exc}",
                flush=True,
            )
            print(f"  retrying in {wait_seconds}s ...", flush=True)
            time.sleep(wait_seconds)


def main() -> int:
    root = Path(os.environ.get("TTS_ONNX_MODEL_DIR", "/opt/onnx_models")).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    for name, (repo_id, patterns) in REPOS.items():
        target = root / name
        print(f"downloading {repo_id} -> {target}", flush=True)
        _download(repo_id, target, patterns)
    required = (
        root / "MOSS-TTS-Nano-100M-ONNX" / "browser_poc_manifest.json",
        root / "MOSS-TTS-Nano-100M-ONNX" / "tts_browser_onnx_meta.json",
        root / "MOSS-Audio-Tokenizer-Nano-ONNX" / "codec_browser_onnx_meta.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("ONNX assets incomplete: " + ", ".join(missing))
    print("onnx models ready:", root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
