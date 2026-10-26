"""音色目录。

上游 MOSS-TTS-Nano 采用「以参考音频做 voice clone」的方式合成，
因此每个音色就是一个参考音频文件。这里只登记仓库中实际存在的
参考音频（vendor/upstream/assets/audio），并根据上游 assets/demo.jsonl
给出可读的名称、语言和示例文本。

除内置音色外，还可以把一个宿主机目录（通常是只读挂载进容器）里的参考音频
扫描进来，见 ``TTS_VOICE_DIR`` / ``scan_voice_dir``。
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from .config import UPSTREAM_DIR, VOICE_PROMPT_DIR, settings


LOGGER = logging.getLogger(__name__)

DEMO_METADATA_PATH = UPSTREAM_DIR / "assets" / "demo.jsonl"

# 挂载目录里允许出现的参考音频扩展名（底层是 torchaudio + libsndfile 后端）。
# 容器里的 libsndfile 1.2 支持 WAV/FLAC/MP3/OGG(Vorbis,Opus)/AIFF/CAF/AU 等；
# m4a、aac 不在其中，需要先转码。
SUPPORTED_PROMPT_AUDIO_SUFFIXES: tuple[str, ...] = (
    ".wav",
    ".wave",
    ".flac",
    ".mp3",
    ".ogg",
    ".oga",
    ".opus",
    ".aif",
    ".aiff",
    ".aifc",
    ".caf",
    ".au",
)

# 挂载音色在 /v1/audio/voices 里的 language 字段，前端据此单独分组。
MOUNTED_VOICE_LANGUAGE = "custom"


@dataclass(frozen=True)
class Voice:
    id: str
    name: str
    language: str
    file_name: str
    description: str = ""
    sample_text: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)
    recommended: bool = False
    source: str = "builtin"
    root: Optional[Path] = None

    @property
    def path(self) -> Path:
        return (self.root or VOICE_PROMPT_DIR) / self.file_name


# 目录顺序即 /v1/audio/voices 的返回顺序，第一个为默认音色。
CATALOG: tuple[Voice, ...] = (
    Voice(
        id="zh_taiwan",
        name="台湾腔",
        language="zh",
        file_name="zh_4.wav",
        description="台湾口音女声，语气自然松弛（默认音色）",
        sample_text=(
            "唉你知道吗，今天真的有够热欸，我一出门就觉得整个人快融化了啦。"
            "然后我刚刚去买饮料，结果前面排超多人，我就在那边等超久，真的有点小崩溃欸。"
            "不过还好最后买到我最爱的珍奶，心情就有比较好一点这样。"
        ),
        aliases=("nova", "shimmer", "zh-TW", "tw"),
        recommended=True,
    ),
    Voice(
        id="zh_welcome",
        name="欢迎关注模思智能",
        language="zh",
        file_name="zh_1.wav",
        description="中文男声，播音感，适合正式内容",
        sample_text="欢迎关注模思智能、上海创智学院与复旦大学自然语言处理实验室。",
    ),
    Voice(
        id="zh_beijing",
        name="京味胡同闲聊",
        language="zh",
        file_name="zh_3.wav",
        description="北京口音，闲谈语气",
        sample_text=(
            "您说这天儿啊，这两天是真不错，风也不大，太阳一出来吧，人心里头都跟着亮堂了不少。"
            "早上起来溜达一圈儿，公园里那大爷大妈都开始活动开了。"
        ),
    ),
    Voice(
        id="zh_night",
        name="深夜温柔晚安",
        language="zh",
        file_name="zh_6.wav",
        description="温柔女声，适合长文朗读、助眠内容",
        sample_text=(
            "夜深了，城市的灯一盏一盏慢慢安静下来，你也终于有了一点属于自己的时间。"
            "或许今天并不轻松，但没关系，现在这一刻，你不需要证明什么。"
        ),
        aliases=("shimmer_soft",),
    ),
    Voice(
        id="zh_lecture",
        name="讲座/纪录片旁白",
        language="zh",
        file_name="zh_10.wav",
        description="男声，讲座、纪录片式旁白",
        sample_text=(
            "各位观众朋友，大家好。今天这一讲，我们从一个几乎每个人都绕不开的话题谈起——"
            "中国人的时间观念。"
        ),
        aliases=("onyx",),
    ),
    Voice(
        id="zh_yangmi",
        name="女性独白（杨幂风格）",
        language="zh",
        file_name="zh_11.wav",
        description="女性独白，适合文案、旁白短片",
        sample_text="有些人喜欢被照顾，而我更习惯照亮自己。不是不需要依靠，只是明白——真正能陪你走到最后的，从来都不是运气。",
        aliases=("coral",),
    ),
    Voice(
        id="en_welcome",
        name="Welcome to OpenMOSS",
        language="en",
        file_name="en_6.wav",
        description="English voice, informative tone",
        sample_text=(
            "OpenMOSS Team is jointly established by Shanghai Innovation Institution, "
            "Fudan University NLP Lab, and MOSI Intelligence."
        ),
        aliases=("verse",),
    ),
    Voice(
        id="en_bitter_lesson",
        name="The Bitter Lesson",
        language="en",
        file_name="en_2.wav",
        description="English voice, essay / lecture style",
        sample_text=(
            "The biggest lesson that can be read from 70 years of AI research is that "
            "general methods that leverage computation are ultimately the most effective."
        ),
        aliases=("ash", "alloy"),
    ),
    Voice(
        id="en_news",
        name="English News",
        language="en",
        file_name="en_4.wav",
        description="English news anchor voice",
        sample_text=(
            "Good evening, and welcome to the news. Today's top stories: global economic "
            "activity continues to show steady growth."
        ),
        aliases=("echo",),
    ),
    Voice(
        id="en_gentle",
        name="A Gentle Reminder",
        language="en",
        file_name="en_3.wav",
        description="English voice, calm and gentle",
        sample_text=(
            "It's okay to feel a little tired or unsure sometimes. Not everything needs "
            "to be clear right away."
        ),
        aliases=("fable", "sage"),
    ),
    Voice(
        id="en_taylor",
        name="Taylor Swift Style",
        language="en",
        file_name="en_7.wav",
        description="English voice, stage speech style",
        sample_text=(
            "Tonight, I just want to take a second and breathe this in with you. "
            "Because moments like this don't happen by accident."
        ),
    ),
    Voice(
        id="en_quiet_motion",
        name="The Quiet Motion of the World",
        language="en",
        file_name="en_8.wav",
        description="English voice, documentary narration",
        sample_text=(
            "In the quiet hours before dawn, the world looks unfinished. Streets are empty, "
            "windows are dark, and the air holds its breath."
        ),
        aliases=("ballad",),
    ),
    Voice(
        id="ja_news",
        name="ニュース",
        language="ja",
        file_name="jp_2.wav",
        description="日本語のニュース読み上げ",
        sample_text=(
            "こんばんは、ニュースです。本日、技術革新の分野で重要な進展があり、"
            "経済成長への期待が高まっています。"
        ),
    ),
)


def _load_demo_samples() -> dict[str, str]:
    """读取上游 demo.jsonl，用完整示例文本补全音色说明。"""
    samples: dict[str, str] = {}
    if not DEMO_METADATA_PATH.is_file():
        return samples
    for line in DEMO_METADATA_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            logging.debug("skip invalid demo metadata line: %s", line[:60])
            continue
        role = str(payload.get("role", "")).strip()
        text = str(payload.get("text", "")).strip()
        if role and text:
            samples.setdefault(Path(role).name, text)
    return samples


_DEMO_SAMPLES = _load_demo_samples()


def _with_demo_text(voice: Voice) -> Voice:
    sample = _DEMO_SAMPLES.get(voice.file_name)
    if not sample or sample == voice.sample_text:
        return voice
    # 保留更完整的示例文本，便于界面「填入示例文本」使用。
    return Voice(
        id=voice.id,
        name=voice.name,
        language=voice.language,
        file_name=voice.file_name,
        description=voice.description,
        sample_text=sample,
        aliases=voice.aliases,
        recommended=voice.recommended,
        source=voice.source,
        root=voice.root,
    )


def available_voices() -> tuple[Voice, ...]:
    """返回磁盘上参考音频确实存在的音色。"""
    voices = [_with_demo_text(voice) for voice in CATALOG if voice.path.is_file()]
    if not voices:
        raise RuntimeError(f"没有找到任何参考音频，请检查目录: {VOICE_PROMPT_DIR}")
    return tuple(voices)


def _slugify_voice_id(stem: str) -> str:
    """文件名 -> 音色 id：小写、空白转连字符、去掉首尾的连字符/点。"""
    return re.sub(r"\s+", "-", str(stem or "").strip().lower()).strip("-.")


def _reserved_keys(voices: Iterable[Voice]) -> tuple[str, ...]:
    """已有音色的 id / 名称 / 别名，挂载音色不能与它们重名。"""
    keys: list[str] = []
    for voice in voices:
        keys.append(voice.id)
        keys.append(voice.name)
        keys.extend(voice.aliases)
    return tuple(keys)


def scan_voice_dir(root: Path, reserved_keys: Iterable[str] = ()) -> tuple[Voice, ...]:
    """扫描挂载目录，把里面的参考音频登记成音色（id = 文件名去掉扩展名）。

    只扫顶层文件：忽略子目录、隐藏文件与非音频扩展名；重名（与内置音色或
    同目录其他文件冲突）的条目会被跳过并打日志，不会让服务启动失败。
    """
    if not root.is_dir():
        LOGGER.debug("挂载音色目录不存在或不是目录，跳过扫描：%s", root)
        return ()

    taken = {str(key).strip().lower() for key in reserved_keys if str(key).strip()}
    voices: list[Voice] = []
    skipped: list[str] = []
    try:
        entries = sorted(root.iterdir(), key=lambda item: item.name.lower())
    except OSError as exc:  # pragma: no cover - 目录不可读时不影响内置音色
        LOGGER.warning("挂载音色目录无法读取（%s）：%s", root, exc)
        return ()

    for entry in entries:
        name = entry.name
        if name.startswith("."):
            continue
        try:
            if not entry.is_file():
                continue
        except OSError:  # pragma: no cover - 悬空软链接等
            skipped.append(name)
            continue
        if entry.suffix.lower() not in SUPPORTED_PROMPT_AUDIO_SUFFIXES:
            skipped.append(name)
            continue

        stem = entry.stem.strip()
        voice_id = _slugify_voice_id(stem)
        if not voice_id:
            skipped.append(name)
            continue
        if voice_id in taken:
            LOGGER.warning(
                "挂载音色 %s 与已有音色 id/别名 %r 冲突，已跳过（不会覆盖内置音色）。", name, voice_id
            )
            continue

        voice = Voice(
            id=voice_id,
            name=stem or voice_id,
            language=MOUNTED_VOICE_LANGUAGE,
            file_name=name,
            description=f"挂载参考音频：{name}",
            sample_text="",
            # 除了 id（文件名去掉扩展名）之外，也允许直接用完整文件名指定音色
            aliases=(name,),
            source="mounted",
            root=root,
        )
        taken.add(voice_id)
        taken.update(alias.lower() for alias in voice.aliases)
        voices.append(voice)

    if voices:
        LOGGER.info(
            "挂载音色目录 %s：登记 %d 个音色（%s）",
            root,
            len(voices),
            ", ".join(voice.id for voice in voices),
        )
    if skipped:
        LOGGER.info("挂载音色目录 %s：跳过 %d 个非参考音频文件（%s）", root, len(skipped), ", ".join(skipped[:8]))
    return tuple(voices)


def mounted_voice_dir() -> Optional[Path]:
    """TTS_VOICE_DIR 指向的目录；未配置时返回 None。"""
    raw = str(getattr(settings, "voice_dir", "") or "").strip()
    if not raw:
        return None
    return Path(raw).expanduser()


class VoiceRegistry:
    """音色 ID / 别名 -> Voice 的解析器。"""

    def __init__(self, voices: Iterable[Voice], default_voice_id: str = "") -> None:
        self._voices = tuple(voices)
        self._by_id = {voice.id: voice for voice in self._voices}
        self._aliases: dict[str, str] = {}
        for voice in self._voices:
            self._aliases[voice.id.lower()] = voice.id
            self._aliases[voice.name.lower()] = voice.id
            for alias in voice.aliases:
                self._aliases.setdefault(alias.lower(), voice.id)

        if default_voice_id and default_voice_id in self._by_id:
            self.default_voice_id = default_voice_id
        else:
            self.default_voice_id = self._voices[0].id

    def __iter__(self):
        return iter(self._voices)

    @property
    def voices(self) -> tuple[Voice, ...]:
        return self._voices

    def get(self, voice_id: str | None) -> Voice:
        """兼容 OpenAI 客户端：未知音色回退到默认音色，而不是报错。"""
        key = str(voice_id or "").strip().lower()
        if not key:
            return self._by_id[self.default_voice_id]
        resolved = self._aliases.get(key)
        if resolved is None:
            return self._by_id[self.default_voice_id]
        return self._by_id[resolved]

    def is_known(self, voice_id: str | None) -> bool:
        key = str(voice_id or "").strip().lower()
        return bool(key) and key in self._aliases


BUILTIN_VOICES: tuple[Voice, ...] = available_voices()

# 只读挂载目录里的参考音频（TTS_VOICE_DIR）在进程启动时扫描一次，
# 之后按文件名当音色用，不需要每次请求上传音频。
MOUNTED_VOICE_DIR: Optional[Path] = mounted_voice_dir()
MOUNTED_VOICES: tuple[Voice, ...] = (
    scan_voice_dir(MOUNTED_VOICE_DIR, _reserved_keys(BUILTIN_VOICES)) if MOUNTED_VOICE_DIR else ()
)

registry = VoiceRegistry(BUILTIN_VOICES + MOUNTED_VOICES, settings.default_voice)


def mounted_voices() -> tuple[Voice, ...]:
    """当前已登记的挂载音色。"""
    return tuple(voice for voice in registry.voices if voice.source == "mounted")


def mounted_voice_status() -> dict[str, object]:
    """给 /health 用的挂载音色状态（便于确认挂载是否生效）。"""
    return {
        "enabled": MOUNTED_VOICE_DIR is not None,
        "dir": "" if MOUNTED_VOICE_DIR is None else str(MOUNTED_VOICE_DIR),
        "exists": bool(MOUNTED_VOICE_DIR is not None and MOUNTED_VOICE_DIR.is_dir()),
        "voices": [voice.id for voice in mounted_voices()],
    }
