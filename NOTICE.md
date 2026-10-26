# 第三方组件与许可

本仓库是基于 [OpenMOSS/MOSS-TTS-Nano](https://github.com/OpenMOSS/MOSS-TTS-Nano)
修改并发布的衍生项目，整体按 Apache License 2.0 分发，许可证副本见根目录
[`LICENSE`](LICENSE)。上游项目原有的版权、归属和许可声明均予以保留。

## 本项目

`app/`、`tools/`、`Dockerfile` 等由本项目编写，用于把 MOSS-TTS-Nano 包装成
OpenAI 兼容的 CPU TTS 服务。

## vendored 上游代码（Apache-2.0）

`vendor/upstream/` 下的 Python 运行时代码、参考音频与 demo 文本来自
[OpenMOSS/MOSS-TTS-Nano](https://github.com/OpenMOSS/MOSS-TTS-Nano)，
遵循 Apache License 2.0（见 `vendor/upstream/LICENSE`），
来源 commit 记录在 `vendor/upstream/UPSTREAM_VERSION`。
其中 `onnx_tts_runtime.py` 与 `ort_cpu_runtime.py` 为官方 ONNX Runtime 推理实现。
这些文件保持上游原样；本仓库对其的使用方式是将其作为可替换的运行时依赖。

## 模型权重

镜像构建时会下载以下模型权重，使用时请遵守其许可与使用条款：

- `OpenMOSS-Team/MOSS-TTS-Nano-100M`
- `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano`

## 运行依赖

Python 侧依赖见 `requirements.txt`（Apache/MIT/BSD 等），
音频编码使用系统 `ffmpeg`（LGPL/GPL，按发行版打包方式而定）。
