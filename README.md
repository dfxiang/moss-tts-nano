# MOSS-TTS-Nano · OpenAI 兼容 TTS 服务（CPU / CUDA）

把 [OpenMOSS/MOSS-TTS-Nano](https://github.com/OpenMOSS/MOSS-TTS-Nano) 封装成一个
**兼容 OpenAI `/v1/audio/speech` 的 TTS 服务**，外加一个简单网页界面。
提供纯 CPU 和 CUDA GPU 两套 Docker 镜像；GPU 镜像的 PyTorch、CUDA 运行库和模型权重都已内置。

默认音色是**台湾腔**（`zh_taiwan`）。

## 与上游 MOSS-TTS-Nano 的区别

当前仓库不是重新训练的模型，也不是上游仓库的镜像；它复用相同的 MOSS-TTS-Nano 模型权重，
重点把模型整理成可直接部署和调用的 TTS 服务。

| 方面 | 上游原项目 | 当前项目 |
| --- | --- | --- |
| 定位 | 模型推理、本地 Demo、CLI 与微调工具 | 面向上线调用的 OpenAI 兼容 TTS 服务 |
| 客户端接入 | `infer.py`、`app.py`、`app_onnx.py` 等入口 | 统一的 `/v1/audio/speech` HTTP API，可直接使用官方 OpenAI SDK |
| 推理后端 | 按脚本选择 PyTorch 或 ONNX | 同一套 API 和环境变量切换 native / ONNX，并提供 CPU / CUDA 镜像 |
| 音色 | 以参考音频和演示音色为主 | 13 个稳定音色 id、OpenAI 别名、上传克隆和挂载目录音色 |
| 流式能力 | 模型侧流式推理 | 原生 PCM、OpenAI SSE、断线取消和安全释放推理资源 |
| 中英混排 | 提供 robust normalizer 与中英文 WeTextProcessing | 在统一请求层执行同一套预处理，保证普通与流式请求进入 native / ONNX 前行为一致 |

简而言之，上游项目回答“如何运行模型”，当前项目回答“如何把模型稳定地接入现有文本和语音应用”。

### 中英文混排处理

当前项目默认启用中英文混排预处理，链路位于模型生成之前：

1. 先做结构清洗。URL、邮箱、`@mention`、`#hashtag`、文件名、路径和版本号会先被保护，
   避免其中的点、下划线、斜杠被当成普通标点清坏。
2. 按文本内容选择 TN 分支。只要包含汉字，就使用中文 TN；纯拉丁字母文本使用英文 TN。
   因此 `这是Anthropic的npm包` 会走中文分支，同时保留其中英文品牌和产品名。
3. 在汉字与拉丁 token 之间补一个空格，例如 `今天update到v2.3.1了` 会变成
   `今天 update 到 v2.3.1 了。`。连续英文空格会被压缩，汉字之间多余的空格会被删除。
4. 再做一次结构清洗和分段。中文与 ASCII 的句号、问号、感叹号、分号、逗号都可作为
   长文本分段边界；常见 Markdown、社交噪声和重复标点也会被转为适合 TTS 的停顿。
5. 普通语音接口和流式接口共用这一预处理；ONNX 后端不会再做第二次语义 TN，确保中英混排
   文本在两条推理路径上的处理一致。

可用下面的命令核对混排规则（包含 46 个清洗、保真与幂等性用例）：

```bash
python vendor/upstream/tts_robust_normalizer_single_script.py
```

这些优化改善的是文本清洗、中英文边界、技术 token 保真和长文本分段，不会在中英文之间
逐词切换音色，也不会改变模型权重。品牌名、缩写、生僻专有名词的实际发音仍取决于模型；
确需固定读法时，建议直接改写输入，或选择更合适的参考音色。

混排能力的基础实现来自 vendored 的上游运行时；本仓库的价值在于把它统一接入所有 API
与推理后端，而不是声称一套独立训练的混排模型。默认同时启用两级清洗，也可以用
`TTS_ENABLE_TEXT_NORMALIZATION=0` 或 `TTS_ENABLE_NORMALIZE_TTS_TEXT=0` 分别关闭。

## 特性

- **OpenAI 兼容接口**：`POST /v1/audio/speech`，支持 `response_format` = `mp3` / `opus` / `aac` / `flac` / `wav` / `pcm`，支持 `speed` 变速和 `stream_format="sse"` 流式事件；官方 `openai` SDK 只需改 `base_url` 即可直接用。
- **低延迟流式合成**：`POST /v1/audio/speech/stream` 边生成边返回 16bit PCM，网页端边收边播（4 核 CPU 实测首包 0.6~0.9 秒）。客户端可随时中断，服务会立刻释放推理资源，不会阻塞后续请求。
- **13 个内置音色**：中文（台湾腔、京味、温柔女声、讲座男声…）、英文、日文；OpenAI 音色名（`nova`、`alloy`、`onyx`…）会自动映射到内置音色，未知音色回退默认音色，客户端不会因为音色名报错。
- **音色克隆**：`POST /v1/audio/speech/clone` 上传参考音频即可用自定义音色合成。
- **CPU / CUDA 容器**：`Dockerfile` 使用 PyTorch CPU；`Dockerfile.gpu` 基于 `moss-tts-nano:base`，使用官方 ONNX Runtime CUDA 后端。两者都在构建阶段把模型权重放进镜像，容器启动后无需联网。
- **简单网页界面**：`GET /`，流式播放、语速与采样参数、示例文本、调用代码片段，全部离线自包含（不依赖 CDN）。

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
docker compose up -d --build
# 打开 http://localhost:8000
```

宿主机 8000 端口被占用时可以换端口：`TTS_PUBLISH_PORT=8080 docker compose up -d`。

### 方式二：docker 命令

```bash
docker build -t moss-tts-nano:latest .
docker run --rm -p 8000:8000 --cpus=4 moss-tts-nano:latest
# 打开 http://localhost:8000
```

镜像里已经预置了模型权重，**不需要挂载 HuggingFace 缓存**，也不需要在启动时联网。

首次启动会后台预热（加载权重 + 跑一次短合成 + 编译文本正则化），本机 4 核实测约 9 秒；
期间 `/health` 返回 `"status": "warming_up"`，合成请求会自动等待预热完成而不是失败。

```bash
curl -s localhost:8000/health | python -m json.tool
```

### 方式三：CUDA GPU 镜像

宿主机需要 NVIDIA 驱动和 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。
先确认 Docker 能看到 GPU：

```bash
docker run --rm --gpus all nvidia/cuda:12.6.3-base-ubuntu24.04 nvidia-smi
```

构建并启动 GPU 镜像：

```bash
docker build -f Dockerfile.gpu -t moss-tts-nano:gpu .
docker run --rm --gpus all -p 8000:8000 moss-tts-nano:gpu
# 打开 http://localhost:8000
```

`moss-tts-nano:base` 是已经构建好并验证可运行的完整 GPU 环境，包含 Python 依赖、
CUDA 运行库、ffmpeg 和基础模型。`Dockerfile.gpu` 只覆盖当前版本的
`app/`、`vendor/` 和 `tools/`；首次构建会安装 `onnxruntime-gpu` 并下载官方 ONNX
模型，之后相同层会复用缓存。

镜像默认使用 `TTS_BACKEND=onnx`、`TTS_ONNX_EXECUTION_PROVIDER=cuda`，
推理走 ONNX Runtime 的 `CUDAExecutionProvider`，并使用官方 ONNX 模型内置的
`fixed` 采样节点，不经过 PyTorch-CUDA 生成路径。
可以这样确认容器确实运行在 GPU 上：

```bash
curl -s localhost:8000/health | python -m json.tool
# device 应为 "cuda"
```

GPU 镜像继承基础镜像的体积；新增层包含应用代码、ONNX Runtime GPU 和
约 760MB 的官方 ONNX 模型。相同构建层会被 Docker 缓存。

### 方式四：本地直接运行

```bash
sudo apt-get install -y ffmpeg            # mp3/aac/opus/flac 与变速需要 ffmpeg
python -m venv .venv && source .venv/bin/activate

# 关键：用 PyTorch 官方 CPU 索引装 torch，避免拉入 CUDA 包
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.7.0 torchaudio==2.7.0
pip install -r requirements.txt

python -m app.main                        # 默认监听 0.0.0.0:8000
```

权重默认从 HuggingFace 拉取（`OpenMOSS-Team/MOSS-TTS-Nano-100M`、`OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano`）；
也可以先执行 `python tools/download_models.py` 预下载到 `/opt/models`（用 `TTS_MODEL_LINK_DIR` 改目录），
服务检测到本地快照后会自动使用。

## 接口

### 1) `POST /v1/audio/speech`（OpenAI 兼容）

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `model` | string | `moss-tts-nano` | 也接受 `tts-1` / `tts-1-hd` / `gpt-4o-mini-tts` 等别名 |
| `input` | string | 必填 | 待合成文本（上限见 `TTS_MAX_INPUT_CHARS`，默认 8192 字符） |
| `voice` | string | `zh_taiwan` | 内置音色 id 或别名；未知值回退默认音色 |
| `response_format` | string | `mp3` | `mp3` / `opus` / `aac` / `flac` / `wav` / `pcm` |
| `speed` | number | `1.0` | 0.25~4.0，用 ffmpeg `atempo` 实现变速不变调 |
| `stream_format` | string | `audio` | 设为 `sse` 时返回 OpenAI 风格的 `speech.audio.delta` 事件流 |

扩展字段（可选）：`seed`、`prompt_text`、`max_new_frames`、`voice_clone_max_text_tokens`、
`do_sample`、`text_temperature`、`text_top_p`、`text_top_k`、`audio_temperature`、`audio_top_p`、
`audio_top_k`、`audio_repetition_penalty`。未知字段会被忽略，方便客户端携带私有参数。

> 官方 `openai` SDK 会校验参数名，扩展字段需要通过 `extra_body` 传入，例如
> `client.audio.speech.create(..., extra_body={"seed": 42})`。

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"tts-1","input":"你好，欢迎使用 MOSS-TTS-Nano。","voice":"zh_taiwan","response_format":"mp3"}' \
  --output hello.mp3
```

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="not-needed")

with client.audio.speech.with_streaming_response.create(
    model="moss-tts-nano",
    voice="zh_taiwan",
    input="你好，欢迎使用 MOSS-TTS-Nano。",
    response_format="mp3",
) as response:
    response.stream_to_file("hello.mp3")
```

响应头（便于排查性能）：`X-Voice`、`X-Sample-Rate`、`X-Channels`、`X-Audio-Seconds`、
`X-Elapsed-Ms`、`X-Text-Normalization`。

### 2) `POST /v1/audio/speech/stream`（扩展：低延迟流式）

请求体同上，响应为 `application/octet-stream` 的裸 PCM（16bit little-endian，交错声道），
采样率与声道数在响应头 `X-Sample-Rate`、`X-Channels` 里。适合边生成边播放。

```python
import numpy as np, requests, soundfile as sf

resp = requests.post(
    "http://localhost:8000/v1/audio/speech/stream",
    json={"input": "边生成边播放。", "voice": "zh_taiwan"},
    stream=True,
)
sample_rate = int(resp.headers["X-Sample-Rate"])
channels = int(resp.headers["X-Channels"])
pcm = b"".join(resp.iter_content(chunk_size=8192))
data = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768.0
sf.write("stream.wav", data.reshape(-1, channels), sample_rate)
```

### 3) `POST /v1/audio/speech/clone`（扩展：音色克隆）

`multipart/form-data`：`input`（文本）、`prompt_audio`（参考音频文件），
可选 `prompt_text`、`response_format`、`speed`、`seed`、`max_new_frames`。
参考音频建议 3~30 秒清晰人声。

```bash
curl -X POST http://localhost:8000/v1/audio/speech/clone \
  -F 'input=用这个音色念一句话' \
  -F 'response_format=wav' \
  -F 'prompt_audio=@my_voice.wav' \
  --output clone.wav
```

#### 免上传：把参考音频挂进容器，按文件名调用

每次请求都上传参考音频（几十秒的 mp3 约几百 KB）没必要，可以把宿主机目录只读挂载进容器：
启动时扫描一次，目录里的 `abc.mp3` 会登记成音色 `abc`，之后直接当普通音色用。

```bash
cp abc.mp3 /home/danny/tts-voices/         # compose 默认把该目录挂到容器 /voices（只读）
docker compose up -d                       # 首次、或改了挂载配置时需要重建容器

curl -s localhost:8000/v1/audio/voices | python -m json.tool | grep -A3 '"source": "mounted"'
curl -X POST http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"input":"用 abc 这个音色念一句话。","voice":"abc","response_format":"wav"}' \
  --output abc.wav
```

几点说明：

- 挂载路径由 compose 的 `TTS_VOICE_DIR_HOST` 决定（默认 `/home/danny/tts-voices`），容器内固定是 `/voices`，可用 `TTS_VOICE_DIR` 改容器内路径（镜像默认已是 `/voices`）。
- 音色 id 就是文件名去掉扩展名（小写、空白转 `-`）：`My Voice.mp3` → `my-voice`；也接受带扩展名的写法（`my-voice.mp3`）。
- 支持 `wav` / `flac` / `mp3` / `ogg` / `opus` / `aif` / `caf` / `au`（底层 libsndfile 后端）；`m4a`、`aac` 需要先转码。
- 只扫顶层文件，忽略子目录、隐藏文件和非音频扩展名；与内置音色 id/别名重名的文件会被跳过并在启动日志里告警（内置音色优先）。
- 扫描只登记路径，不预加载音频：挂很多文件也不增加启动耗时和内存。音频在每次请求时读取，所以替换宿主机上的文件下一个请求就生效。
- `GET /health` 的 `mounted_voices` 字段能看到挂载目录状态和已登记的音色（启动日志里也会打印一行）。
- 未知音色名仍然按 OpenAI 兼容行为回退到默认音色（不会报错），可以用响应头 `X-Voice` 确认真实生效的音色。
- 参考音频越长，每次合成的固定开销越大（服务端每次都要重新编码参考音频）：实测 1 秒参考约 2.6 秒、25 秒参考约 6.2 秒（同一句文本、4 核 CPU）。建议控制在 3~8 秒。

### 4) 其它接口

| 接口 | 说明 |
| --- | --- |
| `GET /v1/audio/voices` | 音色目录（id、名称、语言、说明、示例文本、OpenAI 别名、默认音色） |
| `GET /v1/models` | OpenAI 风格模型列表 |
| `GET /health` | 存活与预热状态、设备/线程数/采样率、请求统计、ffmpeg 是否可用 |
| `GET /` | 网页界面 |

错误返回统一为 OpenAI 风格：`{"error": {"message": ..., "type": ..., "code": null, "param": null}}`。

## 内置音色

| id | 名称 | 语言 | 说明 |
| --- | --- | --- | --- |
| `zh_taiwan` ★ | 台湾腔 | 中文 | 台湾口音女声，语气自然松弛（**默认音色**） |
| `zh_welcome` | 欢迎关注模思智能 | 中文 | 男声，播音感 |
| `zh_beijing` | 京味胡同闲聊 | 中文 | 北京口音闲谈 |
| `zh_night` | 深夜温柔晚安 | 中文 | 温柔女声，长文朗读 |
| `zh_lecture` | 讲座/纪录片旁白 | 中文 | 男声旁白 |
| `zh_yangmi` | 女性独白（杨幂风格） | 中文 | 女性独白 / 文案 |
| `en_welcome` | Welcome to OpenMOSS | 英文 | 介绍性语气 |
| `en_bitter_lesson` | The Bitter Lesson | 英文 | 讲稿 / 论文朗读 |
| `en_news` | English News | 英文 | 新闻播报 |
| `en_gentle` | A Gentle Reminder | 英文 | 平静温柔 |
| `en_taylor` | Taylor Swift Style | 英文 | 舞台感演讲 |
| `en_quiet_motion` | The Quiet Motion of the World | 英文 | 纪录片旁白 |
| `ja_news` | ニュース | 日文 | 日语新闻 |

别名映射：`nova` / `shimmer` → `zh_taiwan`，`onyx` → `zh_lecture`，`coral` → `zh_yangmi`，
`alloy` / `ash` → `en_bitter_lesson`，`echo` → `en_news`，`fable` / `sage` → `en_gentle`，
`verse` → `en_welcome`，`ballad` → `en_quiet_motion`。

## 配置（环境变量）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `TTS_HOST` / `TTS_PORT` | `0.0.0.0` / `8000` | 监听地址与端口 |
| `TTS_DEVICE` | `cpu` | 推理设备；`Dockerfile.gpu` 默认设为 `cuda`，也可设为 `auto` |
| `TTS_DTYPE` | `float32` | `float32` / `float16` / `bfloat16` / `auto`；GPU 镜像默认 `float32` |
| `TTS_ATTN_IMPLEMENTATION` | `eager` | CPU / GPU 镜像默认 `eager`；GPU 可尝试 `sdpa` |
| `TTS_BACKEND` | `native` | `native`（PyTorch）或 `onnx`；GPU 镜像默认 `onnx` |
| `TTS_ONNX_MODEL_DIR` | `/opt/onnx_models` | ONNX 模型目录 |
| `TTS_ONNX_EXECUTION_PROVIDER` | `cpu` | ONNX Execution Provider；GPU 镜像默认 `cuda` |
| `TTS_CPU_THREADS` | 0（自动） | torch 线程数，默认取容器可用核数 |
| `TTS_MAX_CONCURRENCY` | `1` | 同时合成数；CPU 上并发会互相抢核，建议保持 1 |
| `TTS_MAX_INPUT_CHARS` | `8192` | 单次请求文本长度上限 |
| `TTS_DEFAULT_VOICE` | `zh_taiwan` | 默认音色 |
| `TTS_VOICE_DIR` | 镜像内为 `/voices`，裸跑为空 | 挂载的参考音频目录：里面的音频按文件名登记成音色，免上传（空值关闭） |
| `TTS_DEFAULT_RESPONSE_FORMAT` | `mp3` | `response_format` 缺省值 |
| `TTS_API_KEY` | 空（不鉴权） | 设置后所有 `/v1/*` 需要 `Authorization: Bearer <key>` |
| `TTS_CORS_ORIGINS` | `*` | 允许的跨域来源，逗号分隔 |
| `TTS_WARMUP` | `1` | 启动时是否跑一次预热合成（`0` 表示只加载权重） |
| `TTS_ENABLE_TEXT_NORMALIZATION` | `1` | 是否用 WeTextProcessing 做数字/日期等正则化 |
| `TTS_CHECKPOINT_PATH` | HF repo id 或 `/opt/models/MOSS-TTS-Nano` | 模型路径 / 仓库 |
| `TTS_AUDIO_TOKENIZER_PATH` | HF repo id 或 `/opt/models/MOSS-Audio-Tokenizer-Nano` | 音频 tokenizer 路径 / 仓库 |
| `TTS_HF_OFFLINE` | `1` | 本地缓存已含模型时自动离线（避免联网探测卡顿）；设为 `0` 关闭 |
| `TTS_FFMPEG_BIN` | `ffmpeg` | ffmpeg 可执行文件路径 |
| `TTS_OUTPUT_DIR` | `/tmp/moss-tts-nano` | 运行时临时音频目录 |

## 性能参考

4 核 CPU（`TTS_CPU_THREADS=4`）、台湾腔、48kHz 立体声输出：

| 场景 | 实测 |
| --- | --- |
| 整段合成 `/v1/audio/speech` | 5.8s 音频耗时 4.9s（RTF ≈ 0.85） |
| 流式 `/v1/audio/speech/stream` | 首包 ≈ 0.6~0.9s，之后基本实时 |
| 容器冷启动（权重在镜像里） | 约 9s 完成预热，`/health` 转为 `ready` |

RTF = 生成耗时 / 音频时长，越小越快。核数越多越快；长文本会按标点自动分段合成。
输出为模型原生的 48kHz 立体声。镜像大小约 3.9GB（主要是 PyTorch CPU 与模型权重）。

## 项目结构

```
app/
  main.py         FastAPI 服务与全部接口
  engine.py       对上游运行时的封装（预热、串行推理、流式、统计）
  voices.py       音色目录与别名映射
  audio.py        PCM/WAV/MP3/Opus/AAC/FLAC 编码与变速（ffmpeg）
  config.py       环境变量配置
  web/index.html  网页界面（单文件、无外部依赖）
tests/api_smoke.py    接口自检脚本
tools/
  download_models.py  预下载模型权重
  download_onnx_models.py  预下载官方 ONNX 模型
  sync_upstream.sh    同步上游 vendored 代码
vendor/upstream/      上游运行时代码 + 参考音频（Apache-2.0，见 NOTICE.md）
Dockerfile / Dockerfile.gpu / docker-compose.yml / requirements*.txt
```

数据流：文本 →（robust 清洗 + WeTextProcessing 正则化）→ 按标点分段 →
以参考音频做 voice clone 生成音频 token → 解码为 48kHz 波形 → PCM 流式输出或 ffmpeg 编码。

## 自检

```bash
python tests/api_smoke.py --base-url http://localhost:8000
python vendor/upstream/tts_robust_normalizer_single_script.py
```

覆盖健康检查、模型列表、音色列表、各输出格式、SSE 流式、PCM 流式、音色克隆与错误处理。
第一条命令覆盖服务接口；第二条覆盖文本清洗的中英文混排、技术 token 保真和幂等性。
未安装 ffmpeg 时，接口自检会自动跳过依赖 ffmpeg 的用例并给出提示。

## 关于 CPU / CUDA 依赖

- Dockerfile 只用 PyTorch 官方 CPU 索引安装 `torch==2.7.0+cpu` / `torchaudio==2.7.0+cpu`，
  并且**不会**执行上游 `pyproject.toml` / `requirements.txt` 里的 `torch==2.7.0`（那会从 PyPI 拉到 CUDA 版）。
- Dockerfile.gpu 基于 `moss-tts-nano:base`，使用官方 `onnx_tts_runtime.py` /
  `ort_cpu_runtime.py` 和 `onnxruntime-gpu`；GPU 生成路径不再使用 PyTorch CUDA。
- 上游运行时代码以 vendored 方式放在 `vendor/upstream/`，不额外引入依赖。
- 验证镜像里没有 CUDA 包：

  ```bash
  docker run --rm moss-tts-nano:latest pip list | grep -iE "nvidia|triton" || echo "无 CUDA 相关包"
  ```

- 验证 GPU 镜像能看到显卡并加载了 CUDA 版 PyTorch：

  ```bash
  docker run --rm --gpus all moss-tts-nano:gpu \
    python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
  ```

## 常见问题

**mp3 报 500，提示需要 ffmpeg？**
镜像里已包含 ffmpeg。本地裸跑请先 `apt-get install -y ffmpeg`；
或者只用 `response_format=wav` / `pcm`（不需要 ffmpeg），此时 `speed` 必须为 1.0。

**构建时下载模型失败（网络受限）**
镜像默认走国内镜像站 `https://hf-mirror.com`（仅构建阶段生效）。

如果日志出现 `Distant resource does not seem to be on huggingface.co`，通常是因为使用了
已改名的旧仓库 ID。当前主模型仓库是 `OpenMOSS-Team/MOSS-TTS-Nano-100M`；
本项目会使用新 ID 下载，并自动重试 3 次。

若仍失败，可换其他镜像站，或改走宿主网络：

```bash
# 覆盖为其他镜像站，或设回 https://huggingface.co 直连官方站
docker build --build-arg HF_ENDPOINT=https://hf-mirror.com -t moss-tts-nano:latest .
# 或：docker build --network=host -t moss-tts-nano:latest .
```

**`apt` 或 `pip` 下载依赖失败（网络受限）**
CPU Dockerfile 默认使用阿里云 Debian 和 PyPI 镜像。
GPU Dockerfile 复用 `moss-tts-nano:base`，不执行 `apt-get`；首次构建会从阿里云
PyPI 安装 `onnxruntime-gpu`，并从 `HF_ENDPOINT` 下载官方 ONNX 模型。

**想用挂载缓存代替镜像内置权重（镜像小约 600MB）**

构建时跳过下载，运行时把本机缓存挂进来即可。服务会「离线优先」使用本地缓存，
不会卡在 huggingface_hub 的联网探测上：

```bash
docker build --build-arg PRELOAD_MODELS=0 -t moss-tts-nano:slim .
docker run --rm -p 8000:8000 \
  -v ~/.cache/huggingface:/opt/huggingface \
  -e TTS_CHECKPOINT_PATH=OpenMOSS-Team/MOSS-TTS-Nano-100M \
  -e TTS_AUDIO_TOKENIZER_PATH=OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano \
  moss-tts-nano:slim
```

几点说明：

- 缓存目录里只要**有**模型（哪怕 snapshots 目录不完整，远程代码在 transformers 的 `modules/` 缓存里也算），
  启动时就会自动打开 `HF_HUB_OFFLINE=1`，`/health` 的 `huggingface.offline` 字段可以看到；
  想强制关闭这个行为用 `-e TTS_HF_OFFLINE=0`。
- 缓存完全是空的、且容器没有外网时，`/health` 会给出明确的失败原因和三种修法（见下）。
- 想主动补全缓存（例如在能联网的机器上先下载好）：

  ```bash
  HF_ENDPOINT=https://hf-mirror.com python tools/download_models.py   # 会写进 $HF_HOME（默认 ~/.cache/huggingface）
  ```

  注意用 `from_pretrained(repo_id)` 跑出来的缓存可能只有 config.json 和权重；
  本服务在检测到快照不完整时会退回用 repo id + 离线模式加载（远程代码走 `modules/` 缓存）。

**第一次请求很慢？**
预热在后台进行（加载权重 + 预热合成），完成后 `/health` 的 `ready` 为 `true`。
预热期间的请求会等待而不是报错；也可以把 `HEALTHCHECK` 接入编排系统，等健康后再接流量。

**网页里「生成并播放」要先等两三秒才出声，是卡住了吗？**
不是。CPU 单机生成速度大约 1.3× 实时（**比播放慢**），边生成边播必然出现断断续续的声音，
所以网页默认走「连贯优先」：先缓冲 `(生成倍率-1)/生成倍率 × 音频时长` 秒再开播
（本机约 1.5~2 秒音频、首音延迟 3 秒左右，全程连贯，统计栏会显示「预缓冲」）。
想要更低延迟就把「播放模式」切成「低延迟」，代价是生成跟不上时会有空档；
长文本建议用「下载音频」按整段合成再播放。同一段音频的音质不受模式影响。
4 核 CPU 上实测：2 线程 RTF 1.57、4 线程 1.30、6 线程 1.47、8 线程 1.92，
bf16/fp16 反而更慢 —— 也就是说 4 线程已是这台机器的最优点，换更多线程不能解决。

**为什么偶尔会生成出特别长的音频（比如 26 个字生成 29 秒）？**
两种情况，看长度就能分辨：

1. 文本其实比想象的长：中文约 5 字/秒（实测 155 字 → 28.96 秒），长文本本来就长。
2. 模型这一轮没生成出结束符（`audio_end_token`），一路生成到 `max_new_frames` 的帧上限：
   默认 375 帧 ÷ 12.5 帧/秒 = **正好 30.00 秒**，听感上像同一句话被反复重复（自回归 TTS 的已知失效模式）。
   想复现可以传 `max_new_frames=40`，音频会精确截断在 3.200 秒。

服务端会记录每条请求的 `chars / audio / elapsed`，并在音频超过「预期 2 倍 + 3 秒」时打上
`[疑似未正常结束]` 告警；响应头也会带上 `X-Input-Chars`，异常时追加
`X-Audio-Warning: audio-longer-than-expected`，网页界面同步给出红字提示。
**并且服务端会自动换一个随机 seed 重生成一次**（`TTS_AUTO_RETRY_DEGENERATE=1`，
重试次数用 `TTS_AUTO_RETRY_ATTEMPTS` 调，默认 1 次）——判定条件是任一成立：
时长 > 「文本预期 2 倍 + 3 秒」、静音占比 > 40%、最长连续静音 > 3 秒。
两次都异常时返回较短的那条，并在日志里告警；命中重试时响应头会带 `X-Retries`。
想彻底避免 30 秒循环也可以把 `max_new_frames` 调到 150 左右（≈12 秒上限，代价是超长句会被截断）。

**能只跑 CPU 吗？**
可以。默认的 `Dockerfile` / `docker-compose.yml` 就是 CPU 版本，整条链路上没有任何 CUDA 依赖；
需要 GPU 时改用 `Dockerfile.gpu` 并以 `--gpus all` 启动。

**长文本怎么办？**
服务会按标点自动分段（每段约 75 个文本 token，可用 `voice_clone_max_text_tokens` 调整），
逐段合成；`max_new_frames` 控制单段音频长度上限。超长文本建议用流式接口，边播边生成。

## 上游同步与许可

- 本仓库作为上游项目的衍生项目按 Apache License 2.0 分发，许可证副本见 [LICENSE](LICENSE)。
- 运行时代码来自上游 commit `8b7bcc9`（见 `vendor/upstream/UPSTREAM_VERSION`），
  可用 `tools/sync_upstream.sh ~/github/MOSS-TTS-Nano main` 重新同步。
- 上游代码与参考音频遵循 Apache License 2.0；模型权重遵循各自许可。详见 [NOTICE.md](NOTICE.md)。

## 关联项目文档

- [med-sales 医药销售管理系统文档（含 Android APK 与演示视频）](docs/med-sales/README.md)
