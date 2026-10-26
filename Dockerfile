# MOSS-TTS-Nano OpenAI 兼容 TTS 服务（CPU only / 无 CUDA 依赖）
FROM python:3.12-slim

# 国内构建默认使用阿里云；可通过 --build-arg 覆盖。
ARG DEBIAN_MIRROR=http://mirrors.aliyun.com
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    HF_HOME=/opt/huggingface \
    HF_HUB_DISABLE_XET=1 \
    HF_HUB_DOWNLOAD_TIMEOUT=120 \
    TTS_HOST=0.0.0.0 \
    TTS_PORT=8000

# 挂载进来的参考音频目录：里面的音频会被登记成音色（id = 文件名去掉扩展名），
# 客户端用 voice=<名字> 直接调用，不需要每次上传参考音频。
# 目录不存在时会被忽略（继续只用内置音色）；设为空字符串可显式关闭扫描。
ENV TTS_VOICE_DIR=/voices

# ffmpeg: mp3/aac/opus/flac 编码与 atempo 变速；libsndfile1: soundfile 后端
RUN sed -i \
        -e "s|http://deb.debian.org|${DEBIAN_MIRROR}|g" \
        -e "s|http://security.debian.org|${DEBIAN_MIRROR}|g" \
        /etc/apt/sources.list.d/debian.sources \
 && apt-get -o Acquire::Retries=5 update \
 && apt-get install -y --no-install-recommends ffmpeg libsndfile1 ca-certificates curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt ./
COPY tools/install_python_deps.sh /usr/local/bin/install-python-deps
RUN sed -i 's/\r$//' /usr/local/bin/install-python-deps

# 1) 先装 CPU-only 的 torch（PyTorch 官方 CPU 索引，不会拉取 CUDA 包）
# 2) 再装其余依赖；优先使用 wheels/ 中的离线包，其余从阿里云 PyPI 下载
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --timeout 600 --retries 20 \
        --index-url https://download.pytorch.org/whl/cpu \
        torch==2.7.0 torchaudio==2.7.0

RUN --mount=type=bind,source=wheels,target=/wheels \
    --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    sh /usr/local/bin/install-python-deps /wheels

RUN python -c "import torch; print('torch', torch.__version__, 'cuda:', torch.version.cuda)"

# 上游运行时（vendored）+ 参考音频
COPY vendor ./vendor

# 预编译文本正则化 FST，避免首次请求时再编译
RUN python -c "\
import sys; sys.path.insert(0, 'vendor/upstream');\
from text_normalization_pipeline import WeTextProcessingManager;\
m = WeTextProcessingManager(); m.start(); s = m.ensure_ready();\
print('wetext:', s.state, s.message)"

COPY tools ./tools

# 预下载模型权重（MOSS-TTS-Nano + MOSS-Audio-Tokenizer-Nano，约 310MB）
# 如需镜像更小，可用 --build-arg PRELOAD_MODELS=0，改为运行时挂载 HF 缓存。
# 默认走国内镜像站；需要直连官方站时用 --build-arg HF_ENDPOINT=https://huggingface.co。
# HF_ENDPOINT 只在构建阶段生效，不会写进镜像的运行时环境。
ARG PRELOAD_MODELS=1
ARG HF_ENDPOINT=https://hf-mirror.com
RUN if [ "$PRELOAD_MODELS" = "1" ]; then HF_ENDPOINT="$HF_ENDPOINT" python tools/download_models.py; fi

COPY app ./app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=240s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health | grep -q '"ready":true' || exit 1

CMD ["python", "-m", "app.main"]
