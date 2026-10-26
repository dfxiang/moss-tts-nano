"""OpenAI 兼容的 MOSS-TTS-Nano HTTP 服务（CPU）。

主要接口：

- ``POST /v1/audio/speech``        OpenAI /v1/audio/speech（含 stream_format=sse）
- ``POST /v1/audio/speech/stream`` 扩展：低延迟流式 PCM，边生成边播放
- ``POST /v1/audio/speech/clone``  扩展：上传参考音频做音色克隆
- ``GET  /v1/audio/voices``        扩展：内置音色目录
- ``GET  /v1/models``              OpenAI /v1/models
- ``GET  /health``                 存活与预热状态
- ``GET  /``                       简单 Web 界面
"""

from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
import time
from urllib.parse import quote
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Optional

import uvicorn
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict

from . import __version__
from .audio import (
    STREAMABLE_FORMATS,
    encode_audio,
    ffmpeg_path,
    normalize_format,
    requires_ffmpeg,
)
from .config import WEB_DIR, settings
from .engine import TTSEngine
from .models import hub_cache_dir, offline_mode_enabled
from .streaming import (
    SESSION_DONE,
    DisconnectTrackingMiddleware,
    GeneratorWorker,
    disconnect_event_for,
)
from .voices import mounted_voice_status, registry


LOGGER = logging.getLogger("moss_tts_nano.server")

MODEL_IDS = ("moss-tts-nano",)
# 便于直接替换 OpenAI 客户端的 model 参数
MODEL_ALIASES = ("tts-1", "tts-1-hd", "gpt-4o-mini-tts")

MAX_PROMPT_AUDIO_BYTES = 32 * 1024 * 1024

engine = TTSEngine(settings, registry)


# --------------------------------------------------------------------- schema


class SpeechRequest(BaseModel):
    """OpenAI /v1/audio/speech 请求体（含本项目扩展字段）。"""

    model_config = ConfigDict(extra="allow")

    model: Optional[str] = None
    input: str = ""
    voice: Optional[str] = None
    response_format: Optional[str] = None
    speed: Optional[float] = 1.0
    stream_format: Optional[str] = "audio"

    # ---- 本项目扩展 ----
    seed: Optional[int] = None
    prompt_text: Optional[str] = None
    max_new_frames: Optional[int] = None
    voice_clone_max_text_tokens: Optional[int] = None
    do_sample: Optional[bool] = None
    text_temperature: Optional[float] = None
    text_top_p: Optional[float] = None
    text_top_k: Optional[int] = None
    audio_temperature: Optional[float] = None
    audio_top_p: Optional[float] = None
    audio_top_k: Optional[int] = None
    audio_repetition_penalty: Optional[float] = None


def _error_payload(message: str, *, status_code: int, error_type: str = "invalid_request_error") -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"message": message, "type": error_type, "code": None, "param": None}},
    )


class APIError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, error_type: str = "invalid_request_error"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type


# ----------------------------------------------------------------------- app


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine_status = engine.status()
    LOGGER.info(
        "starting MOSS-TTS-Nano server: checkpoint=%s tokenizer=%s device=%s dtype=%s attn=%s threads=%s",
        engine.checkpoint_path,
        engine.audio_tokenizer_path,
        engine_status["device"],
        engine_status["dtype"],
        engine_status["attn_implementation"],
        engine.cpu_threads,
    )
    LOGGER.info(
        "huggingface 缓存: dir=%s offline=%s（本地缓存已含模型时自动离线，避免联网探测卡顿）",
        hub_cache_dir(),
        offline_mode_enabled(),
    )
    voice_status = mounted_voice_status()
    if voice_status["enabled"]:
        LOGGER.info(
            "挂载音色目录: dir=%s exists=%s 已登记=%s（按文件名当音色用，客户端无需上传参考音频）",
            voice_status["dir"],
            voice_status["exists"],
            ", ".join(voice_status["voices"]) or "无",
        )
    else:
        LOGGER.info("挂载音色目录: 未启用（TTS_VOICE_DIR 为空），只用内置音色。")
    engine.start()
    yield


app = FastAPI(
    title="MOSS-TTS-Nano OpenAI-compatible TTS",
    description="基于 OpenMOSS MOSS-TTS-Nano 的 TTS 服务，兼容 OpenAI /v1/audio/speech。",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()] or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Voice",
        "X-Sample-Rate",
        "X-Channels",
        "X-Audio-Seconds",
        "X-Elapsed-Ms",
        "X-Text-Normalization",
        "X-Audio-Codec",
        "X-Input-Chars",
        "X-Audio-Warning",
    ],
)
app.add_middleware(DisconnectTrackingMiddleware)


@app.exception_handler(APIError)
async def _handle_api_error(request: Request, exc: APIError) -> JSONResponse:
    return _error_payload(exc.message, status_code=exc.status_code, error_type=exc.error_type)


@app.exception_handler(RequestValidationError)
async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_payload(f"Invalid request body: {exc.errors()}", status_code=400)


# ------------------------------------------------------------------- helpers


def _require_auth(request: Request) -> None:
    if not settings.api_key:
        return
    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""
    if token != settings.api_key:
        raise APIError("Invalid API key.", status_code=401, error_type="invalid_request_error")


def _ensure_ready() -> None:
    """等待模型预热完成。"""
    try:
        engine.ensure_ready(timeout=settings.request_timeout_seconds)
    except TimeoutError as exc:
        raise APIError(str(exc), status_code=503, error_type="server_error") from exc
    except RuntimeError as exc:
        raise APIError(f"模型预热失败：{exc}", status_code=500, error_type="server_error") from exc


def _validate_text(text: str) -> str:
    normalized = str(text or "").strip()
    if not normalized:
        raise APIError("`input` is required.")
    if len(normalized) > settings.max_input_chars:
        raise APIError(
            f"`input` is too long: {len(normalized)} characters (limit {settings.max_input_chars})."
        )
    return normalized


def _overrides_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "seed",
        "max_new_frames",
        "voice_clone_max_text_tokens",
        "do_sample",
        "text_temperature",
        "text_top_p",
        "text_top_k",
        "audio_temperature",
        "audio_top_p",
        "audio_top_k",
        "audio_repetition_penalty",
    )
    return {key: payload.get(key) for key in keys}


def _voice_from_payload(payload: dict[str, Any]) -> str:
    requested = payload.get("voice")
    if requested and not registry.is_known(requested):
        LOGGER.info("unknown voice %r, using default %r", requested, registry.default_voice_id)
    return registry.get(requested).id


def _validate_encoder(response_format: str, speed: float) -> None:
    """mp3/opus/aac/flac 与变速都依赖 ffmpeg，缺失时提前给出明确报错。"""
    if requires_ffmpeg(response_format, speed) and ffmpeg_path(settings.ffmpeg_bin) is None:
        raise APIError(
            f"服务器未安装 ffmpeg，无法输出 {response_format}（或变速）；"
            "请改用 response_format=wav / pcm 且 speed=1.0。",
            status_code=500,
            error_type="server_error",
        )


def _header_safe(value: Any) -> str:
    """HTTP 头只能是 latin-1：非 ASCII 的音色名（如中文文件名）用百分号编码。"""
    text = str(value)
    try:
        text.encode("latin-1")
        return text
    except UnicodeEncodeError:
        return quote(text, safe="")


def _audio_headers(result: dict[str, Any]) -> dict[str, str]:
    voice = result.get("voice")
    normalization = result.get("normalization") or {}
    headers = {
        "X-Voice": _header_safe(getattr(voice, "id", str(voice))),
        "X-Sample-Rate": str(result.get("sample_rate", "")),
        "X-Channels": str(result.get("channels", "")),
        "X-Audio-Seconds": f"{result.get('audio_seconds', 0.0):.3f}",
        "X-Elapsed-Ms": f"{result.get('elapsed_seconds', 0.0) * 1000:.0f}",
        "X-Text-Normalization": str(normalization.get("normalization_method", "none")),
        "X-Input-Chars": str(result.get("input_chars", "")),
        "Cache-Control": "no-store",
    }
    if result.get("audio_suspect"):
        # 音频远长于文本预期 / 大段静音：多半是这一轮没生成出结束符，具体原因见服务端日志
        headers["X-Audio-Warning"] = "degenerate-audio"
    if int(result.get("attempts") or 1) > 1:
        headers["X-Retries"] = str(int(result["attempts"]) - 1)
    return headers


def _start_stream_session(
    request: Request,
    *,
    text: str,
    voice_id: str,
    prompt_text: str,
    overrides: dict[str, Any],
    name: str,
) -> GeneratorWorker:
    """把流式合成放到后台线程执行（客户端断开时能立刻取消并释放推理锁）。"""
    return GeneratorWorker(
        lambda: engine.stream(
            text=text,
            voice_id=voice_id,
            prompt_text=prompt_text,
            overrides=overrides,
        ),
        cancels=[disconnect_event_for(request.scope)],
        name=name,
    ).start()


def _encode_stream_chunk(event: dict[str, Any], response_format: str, speed: float) -> bytes:
    if response_format == "pcm":
        return event["pcm"]
    chunk, _ = encode_audio(
        event["waveform"],
        int(event["sample_rate"]),
        response_format,
        speed,
        ffmpeg_bin=settings.ffmpeg_bin,
    )
    return chunk


# ------------------------------------------------------------------ endpoints


@app.get("/health")
async def health() -> dict[str, Any]:
    status = engine.status()
    status["status"] = "ok" if status["ready"] else "warming_up"
    status["version"] = __version__
    status["model_ids"] = list(MODEL_IDS)
    status["max_input_chars"] = settings.max_input_chars
    status["ffmpeg"] = bool(ffmpeg_path(settings.ffmpeg_bin))
    status["default_response_format"] = settings.default_response_format
    status["huggingface"] = {
        "offline": offline_mode_enabled(),
        "cache_dir": str(hub_cache_dir()),
    }
    status["mounted_voices"] = mounted_voice_status()
    return status


@app.get("/v1/models")
async def list_models() -> dict[str, Any]:
    created = int(time.time())
    data = [
        {
            "id": model_id,
            "object": "model",
            "created": created,
            "owned_by": "moss-tts-nano",
            "permission": [],
        }
        for model_id in MODEL_IDS + MODEL_ALIASES
    ]
    return {"object": "list", "data": data}


@app.get("/v1/audio/voices")
async def list_voices() -> dict[str, Any]:
    return {
        "object": "list",
        "default_voice": registry.default_voice_id,
        "data": [
            {
                "id": voice.id,
                "object": "voice",
                "name": voice.name,
                "language": voice.language,
                "description": voice.description,
                "sample_text": voice.sample_text,
                "aliases": list(voice.aliases),
                "recommended": voice.recommended,
                "default": voice.id == registry.default_voice_id,
                # source=builtin 为镜像内置音色；source=mounted 为挂载目录里的参考音频
                "source": voice.source,
                "file": voice.file_name,
            }
            for voice in registry.voices
        ],
    }


@app.post("/v1/audio/speech")
async def create_speech(request: Request, payload: SpeechRequest) -> Response:
    _require_auth(request)
    raw_payload = payload.model_dump()
    text = _validate_text(payload.input)
    voice_id = _voice_from_payload(raw_payload)
    stream_format = str(payload.stream_format or "audio").strip().lower()
    try:
        response_format = normalize_format(payload.response_format, settings.default_response_format)
    except ValueError as exc:
        raise APIError(str(exc)) from exc
    speed = float(payload.speed if payload.speed is not None else 1.0)
    overrides = _overrides_from_payload(raw_payload)
    _validate_encoder(response_format, speed)
    await run_in_threadpool(_ensure_ready)

    if stream_format == "sse":
        if response_format not in STREAMABLE_FORMATS:
            raise APIError(
                f"stream_format=sse 暂只支持 {', '.join(STREAMABLE_FORMATS)}，收到 {response_format!r}。"
                "需要边生成边播放可改用 /v1/audio/speech/stream。"
            )

        session = _start_stream_session(
            request,
            text=text,
            voice_id=voice_id,
            prompt_text=payload.prompt_text or "",
            overrides=overrides,
            name="moss-tts-sse",
        )

        async def _sse_events() -> AsyncIterator[bytes]:
            audio_seconds = 0.0
            sample_rate = engine.sample_rate or 0
            failed = False
            try:
                while True:
                    event = await run_in_threadpool(session.next_event, 0.5)
                    if event is None:
                        continue
                    if event is SESSION_DONE:
                        break
                    if event["type"] == "done":
                        audio_seconds = float(event.get("audio_seconds") or 0.0)
                        sample_rate = int(event.get("sample_rate") or 0)
                        continue
                    if event["type"] != "audio":
                        continue
                    chunk = _encode_stream_chunk(event, response_format, speed)
                    if not chunk:
                        continue
                    payload_out = {"type": "speech.audio.delta", "audio": base64.b64encode(chunk).decode("ascii")}
                    yield f"event: speech.audio.delta\ndata: {json.dumps(payload_out)}\n\n".encode("utf-8")
            except Exception:  # noqa: BLE001 - 流已开始，只能记日志并中断
                failed = True
                LOGGER.exception("SSE streaming failed")
            finally:
                session.close()
            if failed:
                return
            done = {
                "type": "speech.audio.done",
                "usage": {"type": "duration", "seconds": round(audio_seconds, 3)},
                "sample_rate": sample_rate,
                "audio_seconds": round(audio_seconds, 3),
            }
            yield f"event: speech.audio.done\ndata: {json.dumps(done)}\n\n".encode("utf-8")

        return StreamingResponse(
            _sse_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-store",
                "X-Audio-Format": response_format,
                "X-Voice": _header_safe(voice_id),
                "X-Audio-Codec": response_format,
                "X-Sample-Rate": str(engine.sample_rate or ""),
            },
        )

    result = await run_in_threadpool(
        engine.synthesize,
        text=text,
        voice_id=voice_id,
        response_format=response_format,
        speed=speed,
        prompt_text=payload.prompt_text or "",
        overrides=overrides,
    )
    return Response(
        content=result["audio_bytes"],
        media_type=result["media_type"],
        headers=_audio_headers(result),
    )


@app.post("/v1/audio/speech/stream")
async def stream_speech(request: Request, payload: SpeechRequest) -> Response:
    """扩展接口：边生成边返回 16bit PCM（``application/octet-stream``）。"""
    _require_auth(request)
    raw_payload = payload.model_dump()
    text = _validate_text(payload.input)
    voice_id = _voice_from_payload(raw_payload)
    speed = float(payload.speed if payload.speed is not None else 1.0)
    overrides = _overrides_from_payload(raw_payload)
    _validate_encoder("pcm", speed)
    await run_in_threadpool(_ensure_ready)

    session = _start_stream_session(
        request,
        text=text,
        voice_id=voice_id,
        prompt_text=payload.prompt_text or "",
        overrides=overrides,
        name="moss-tts-pcm",
    )

    async def _pcm_chunks() -> AsyncIterator[bytes]:
        try:
            while True:
                event = await run_in_threadpool(session.next_event, 0.5)
                if event is None:
                    continue
                if event is SESSION_DONE:
                    break
                if event["type"] != "audio":
                    continue
                if speed == 1.0:
                    yield event["pcm"]
                    continue
                chunk, _ = encode_audio(
                    event["waveform"],
                    int(event["sample_rate"]),
                    "pcm",
                    speed,
                    ffmpeg_bin=settings.ffmpeg_bin,
                )
                if chunk:
                    yield chunk
        except Exception:  # noqa: BLE001 - 流已开始，只能记日志并中断
            LOGGER.exception("PCM streaming failed")
        finally:
            session.close()

    return StreamingResponse(
        _pcm_chunks(),
        media_type="application/octet-stream",
        headers={
            "X-Audio-Codec": "pcm_s16le",
            "X-Sample-Rate": str(engine.sample_rate or ""),
            "X-Channels": str(engine.channels or 1),
            "X-Speed": f"{speed}",
            "X-Voice": _header_safe(voice_id),
            "Cache-Control": "no-store",
        },
    )


@app.post("/v1/audio/speech/clone")
async def clone_speech(
    request: Request,
    input: str = Form(...),
    prompt_audio: UploadFile = File(...),
    prompt_text: str = Form(""),
    response_format: str = Form(""),
    speed: float = Form(1.0),
    seed: str = Form(""),
    max_new_frames: int = Form(0),
) -> Response:
    """扩展接口：用上传的参考音频做一次性音色克隆（multipart/form-data）。"""
    _require_auth(request)
    text = _validate_text(input)
    try:
        audio_format = normalize_format(response_format, settings.default_response_format)
    except ValueError as exc:
        raise APIError(str(exc)) from exc
    _validate_encoder(audio_format, float(speed or 1.0))

    suffix = Path(prompt_audio.filename or "prompt.wav").suffix or ".wav"
    payload_bytes = await prompt_audio.read()
    if not payload_bytes:
        raise APIError("`prompt_audio` 不能为空。")
    if len(payload_bytes) > MAX_PROMPT_AUDIO_BYTES:
        raise APIError(f"`prompt_audio` 过大（>{MAX_PROMPT_AUDIO_BYTES // (1024 * 1024)}MB）。")

    temp_path = Path(tempfile.mkstemp(prefix="moss-tts-prompt-", suffix=suffix)[1])
    temp_path.write_bytes(payload_bytes)
    overrides: dict[str, Any] = {
        "seed": int(seed) if str(seed).strip().isdigit() else None,
        "max_new_frames": int(max_new_frames) or None,
    }
    try:
        await run_in_threadpool(_ensure_ready)
        result = await run_in_threadpool(
            engine.synthesize,
            text=text,
            voice_id=registry.default_voice_id,
            response_format=audio_format,
            speed=float(speed or 1.0),
            prompt_audio_path=str(temp_path),
            prompt_text=prompt_text,
            overrides=overrides,
        )
    finally:
        temp_path.unlink(missing_ok=True)
    return Response(
        content=result["audio_bytes"],
        media_type=result["media_type"],
        headers=_audio_headers(result),
    )


@app.get("/")
async def index() -> Response:
    index_path = WEB_DIR / "index.html"
    if not index_path.is_file():
        return JSONResponse(
            {
                "service": "moss-tts-nano",
                "version": __version__,
                "docs": "POST /v1/audio/speech",
                "voices": [voice.id for voice in registry.voices],
            }
        )
    return FileResponse(index_path, media_type="text/html", headers={"Cache-Control": "no-store"})


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    uvicorn.run(
        app,
        host=os.environ.get("TTS_HOST", settings.host),
        port=int(os.environ.get("TTS_PORT", settings.port)),
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
