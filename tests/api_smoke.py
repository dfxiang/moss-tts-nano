#!/usr/bin/env python3
"""对 TTS 服务做一次端到端接口自检（只用标准库）。

用法：
    python tests/api_smoke.py                      # 默认 http://127.0.0.1:8000
    python tests/api_smoke.py --base-url http://host:8000
    python tests/api_smoke.py --skip mp3           # 跳过依赖 ffmpeg 的用例
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
import io
from pathlib import Path


def request(base_url: str, path: str, *, payload=None, form=None, timeout=300.0, stream=False):
    url = base_url.rstrip("/") + path
    headers = {}
    data = None
    if form is not None:
        boundary = "----moss-tts-smoke"
        body = io.BytesIO()
        for name, value in form.items():
            body.write(f"--{boundary}\r\n".encode())
            if isinstance(value, tuple):
                filename, content = value
                body.write(
                    f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
                )
                body.write(b"Content-Type: application/octet-stream\r\n\r\n")
                body.write(content)
                body.write(b"\r\n")
            else:
                body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
                body.write(str(value).encode())
                body.write(b"\r\n")
        body.write(f"--{boundary}--\r\n".encode())
        data = body.getvalue()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    if stream:
        return urllib.request.urlopen(req, timeout=timeout)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        # HTTP 头大小写不敏感，统一转小写方便比较
        return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()


def check(name: str, condition: bool, detail: str = "") -> bool:
    print(f"{'PASS' if condition else 'FAIL'}  {name}{(' — ' + detail) if detail else ''}")
    return condition


def wav_seconds(payload: bytes) -> float:
    with wave.open(io.BytesIO(payload)) as handle:
        return handle.getnframes() / float(handle.getframerate())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--voice", default="zh_taiwan")
    parser.add_argument("--text", default="你好，这是一次接口自检。今天天气不错。")
    parser.add_argument(
        "--skip", nargs="*", default=[], help="跳过的用例：mp3 opus aac flac sse clone mounted"
    )
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    skip = {item.lower() for item in args.skip}
    ok = True

    # 1. 健康检查 + 等待预热
    deadline = time.time() + 600
    while True:
        try:
            _, _, body = request(base, "/health")
            health = json.loads(body)
        except Exception as exc:  # noqa: BLE001
            if time.time() > deadline:
                print(f"FAIL  /health 不可用: {exc}")
                return 1
            time.sleep(5)
            continue
        if health.get("ready") or health.get("warmup", {}).get("state") == "failed":
            break
        if time.time() > deadline:
            print("FAIL  /health 超时仍在预热")
            return 1
        print(f"… 等待模型预热：{health.get('warmup', {}).get('message')}")
        time.sleep(5)

    ok &= check("/health ready", bool(health.get("ready")), f"device={health.get('device')} threads={health.get('cpu_threads')} sr={health.get('sample_rate')}")
    ffmpeg_ok = bool(health.get("ffmpeg"))
    if ffmpeg_ok:
        print("PASS  /health ffmpeg — 可用，mp3/opus/aac/flac 与变速功能正常")
    else:
        print("WARN  /health ffmpeg — 未安装 ffmpeg，自动跳过 mp3/opus/aac/flac 用例")
        skip |= {"mp3", "opus", "aac", "flac"}

    # 2. /v1/models
    _, _, body = request(base, "/v1/models")
    models = [item["id"] for item in json.loads(body)["data"]]
    ok &= check("/v1/models", "moss-tts-nano" in models and "tts-1" in models, ", ".join(models))

    # 3. /v1/audio/voices
    _, _, body = request(base, "/v1/audio/voices")
    voices = json.loads(body)
    ids = [item["id"] for item in voices["data"]]
    ok &= check("/v1/audio/voices", args.voice in ids, f"默认={voices.get('default_voice')} 共 {len(ids)} 个音色")

    # 3b. 挂载目录里的参考音频（TTS_VOICE_DIR）：按文件名当音色用，免上传
    mounted = [item for item in voices["data"] if item.get("source") == "mounted"]
    if mounted and "mounted" not in skip:
        mounted_voice = mounted[0]["id"]
        status, headers, payload = request(
            base,
            "/v1/audio/speech",
            payload={"input": "这是挂载音色的自检。", "voice": mounted_voice, "response_format": "wav"},
        )
        ok &= check(
            f"/v1/audio/speech 挂载音色 {mounted_voice}",
            status == 200 and payload[:4] == b"RIFF" and wav_seconds(payload) > 0.3,
            f"{len(payload) / 1024:.0f}KB 音频 / 文件 {mounted[0].get('file')} / 共 {len(mounted)} 个挂载音色",
        )
        ok &= check("响应头 X-Voice（挂载音色）", headers.get("x-voice") == mounted_voice, str(headers.get("x-voice")))

        # 非 ASCII 音色名（例如中文文件名）：HTTP 头只能 latin-1，服务端会百分号编码
        non_ascii = [item for item in mounted if not item["id"].isascii()]
        if non_ascii:
            voice_id = non_ascii[0]["id"]
            status, headers, payload = request(
                base,
                "/v1/audio/speech",
                payload={"input": "非 ASCII 音色名自检。", "voice": voice_id, "response_format": "wav"},
            )
            expected = urllib.parse.quote(voice_id, safe="")
            ok &= check(
                f"/v1/audio/speech 非 ASCII 音色 {voice_id}",
                status == 200 and payload[:4] == b"RIFF" and headers.get("x-voice") in (voice_id, expected),
                f"X-Voice={headers.get('x-voice')}",
            )
    else:
        print("SKIP  挂载音色用例（当前没有 TTS_VOICE_DIR 挂载的参考音频）")

    # 4. OpenAI 兼容：WAV
    started = time.time()
    status, headers, payload = request(
        base,
        "/v1/audio/speech",
        payload={
            "model": "tts-1",
            "input": args.text,
            "voice": args.voice,
            "response_format": "wav",
        },
    )
    elapsed = time.time() - started
    seconds = wav_seconds(payload)
    ok &= check(
        "/v1/audio/speech wav",
        status == 200 and payload[:4] == b"RIFF" and seconds > 0.5,
        f"{len(payload) / 1024:.0f}KB / {seconds:.2f}s 音频 / 耗时 {elapsed:.2f}s / RTF {elapsed / seconds:.2f}",
    )
    ok &= check("响应头 X-Voice", headers.get("x-voice") == args.voice, str(headers.get("x-voice")))

    # 5. 其它格式
    for fmt, magic, size in (
        ("mp3", b"ID3", 1000),
        ("opus", b"OggS", 500),
        ("aac", b"\xff\xf1", 500),
        ("flac", b"fLaC", 500),
        ("pcm", None, 1000),
    ):
        if fmt in skip:
            continue
        try:
            _, _, data = request(
                base,
                "/v1/audio/speech",
                payload={"input": "格式测试。", "voice": args.voice, "response_format": fmt},
            )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:200]
            ok &= check(f"response_format={fmt}", False, f"HTTP {exc.code} {detail}")
            continue
        if fmt == "mp3":
            matched = data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")
        elif magic:
            matched = data[: len(magic)] == magic
        else:
            matched = len(data) > 0
        ok &= check(f"response_format={fmt}", matched and len(data) > size, f"{len(data) / 1024:.0f}KB")

    # 6. SSE 流式（OpenAI stream_format=sse）
    if "sse" not in skip:
        sse_format = "mp3" if ffmpeg_ok else "pcm"
        dl = b""
        with request(
            base,
            "/v1/audio/speech",
            payload={
                "input": args.text,
                "voice": args.voice,
                "response_format": sse_format,
                "stream_format": "sse",
            },
            stream=True,
        ) as resp:
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                dl += chunk
        text = dl.decode("utf-8", "replace")
        delta_count = text.count("speech.audio.delta")
        ok &= check(
            "stream_format=sse",
            "speech.audio.done" in text and delta_count > 1,
            f"{delta_count} 个 audio delta（{sse_format}）",
        )

    # 7. PCM 流式（本项目扩展，低延迟播放）
    started = time.time()
    first_chunk_at = None
    total = 0
    with request(
        base,
        "/v1/audio/speech/stream",
        payload={"input": args.text, "voice": args.voice},
        stream=True,
    ) as resp:
        sample_rate = int(resp.headers.get("X-Sample-Rate") or 0)
        channels = int(resp.headers.get("X-Channels") or 1)
        while True:
            chunk = resp.read(8192)
            if not chunk:
                break
            if first_chunk_at is None:
                first_chunk_at = time.time() - started
            total += len(chunk)
    stream_seconds = total / (2 * max(1, channels) * max(1, sample_rate))
    ok &= check(
        "/v1/audio/speech/stream",
        first_chunk_at is not None and stream_seconds > 0.5,
        f"首包 {first_chunk_at:.2f}s / {stream_seconds:.2f}s 音频 / {sample_rate}Hz {channels}ch",
    )

    # 8. 音色克隆（扩展接口）
    if "clone" not in skip:
        prompt_path = (
            Path(__file__).resolve().parents[1] / "vendor" / "upstream" / "assets" / "audio" / "zh_1.wav"
        )
        try:
            with open(prompt_path, "rb") as handle:
                prompt_bytes = handle.read()
        except OSError:
            prompt_bytes = b""
        if prompt_bytes:
            _, _, data = request(
                base,
                "/v1/audio/speech/clone",
                form={
                    "input": "用自定义参考音频合成一句话。",
                    "response_format": "wav",
                    "prompt_audio": ("zh_1.wav", prompt_bytes),
                },
            )
            ok &= check("/v1/audio/speech/clone", data[:4] == b"RIFF" and len(data) > 1000, f"{len(data) / 1024:.0f}KB")
        else:
            print("SKIP  /v1/audio/speech/clone（找不到参考音频）")

    # 9. 错误处理
    for name, payload, expect in (
        ("空 input", {"input": "   "}, 400),
        ("非法 response_format", {"input": "你好", "response_format": "m4a"}, 400),
        ("非法 voice 回退默认音色", {"input": "你好", "voice": "不存在的音色", "response_format": "wav"}, 200),
    ):
        try:
            _, headers, _ = request(base, "/v1/audio/speech", payload=payload)
            code = 200
        except urllib.error.HTTPError as exc:
            code = exc.code
            headers = {}
        ok &= check(f"错误处理：{name}", code == expect, f"HTTP {code}（期望 {expect}）")

    # 10. 回归：客户端中途断开流式请求后，服务必须立刻恢复可用
    long_text = "这是一段足够长的文本，用来模拟用户在流式播放中途点击停止。" * 8
    resp = request(
        base,
        "/v1/audio/speech/stream",
        payload={"input": long_text, "voice": args.voice},
        stream=True,
    )
    resp.read(16384)   # 只读一小段就断开
    resp.close()
    started = time.time()
    try:
        _, _, payload_bytes = request(
            base,
            "/v1/audio/speech",
            payload={"input": "断开之后还能继续合成。", "voice": args.voice, "response_format": "wav"},
            timeout=90.0,
        )
        recovered = payload_bytes[:4] == b"RIFF"
    except Exception as exc:  # noqa: BLE001
        recovered = False
        print(f"      断开后的请求失败: {exc}")
    ok &= check(
        "中断流式请求后服务仍可用",
        recovered,
        f"恢复耗时 {time.time() - started:.2f}s",
    )

    print()
    print("全部通过 ✅" if ok else "存在失败用例 ❌")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
