# vendored upstream

本目录是 [OpenMOSS/MOSS-TTS-Nano](https://github.com/OpenMOSS/MOSS-TTS-Nano)
运行时代码的**原样拷贝**（Apache-2.0），由 `tools/sync_upstream.sh` 同步：

| 文件 / 目录 | 说明 |
| --- | --- |
| `moss_tts_nano_runtime.py` | `NanoTTSService`：模型加载、`synthesize` / `synthesize_stream` / `warmup` |
| `onnx_tts_runtime.py` | 官方 ONNX Runtime 推理封装（CPU / CUDA execution provider） |
| `ort_cpu_runtime.py` | ONNX session、token 采样与完整/流式 codec 解码 |
| `text_normalization_pipeline.py` | 文本正则化（WeTextProcessing + robust normalizer 编排） |
| `tts_robust_normalizer_single_script.py` | 输入清洗（Markdown、符号、URL 保护等） |
| `moss_tts_nano/defaults.py` | 上游默认路径常量 |
| `assets/audio/*.wav` | 上游参考音频（voice clone 的 prompt），本项目音色目录的数据来源 |
| `assets/demo.jsonl` | 上游示例文本（用于界面「填入示例文本」） |
| `LICENSE` | 上游 Apache-2.0 许可证 |

同步来源与版本记录在 `UPSTREAM_VERSION`。

> 说明：上游的 `_DEFAULT_VOICE_FILES` 里登记了 zh_2 / zh_5 / en_1 / en_5 / jp_1 /
> jp_3~5 等参考音频，但仓库中并不存在这些文件。本项目的音色目录
> （`app/voices.py`）只登记实际存在的 13 个参考音频。
