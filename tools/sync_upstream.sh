#!/usr/bin/env bash
# 从上游 MOSS-TTS-Nano 仓库同步 vendored 运行时代码与参考音频。
#
# 用法：
#   tools/sync_upstream.sh [上游仓库路径] [git ref]
# 例：
#   tools/sync_upstream.sh ~/github/MOSS-TTS-Nano main
set -euo pipefail

UPSTREAM_REPO="${1:-${MOSS_TTS_UPSTREAM:-$HOME/github/MOSS-TTS-Nano}}"
UPSTREAM_REF="${2:-main}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO_ROOT/vendor/upstream"

if [[ ! -d "$UPSTREAM_REPO" ]]; then
  echo "找不到上游仓库: $UPSTREAM_REPO" >&2
  echo "可先执行: git clone https://github.com/OpenMOSS/MOSS-TTS-Nano.git ~/github/MOSS-TTS-Nano" >&2
  exit 1
fi

rm -rf "$DEST"           # 恢复：从上游重新拷贝即可（UPSTREAM_VERSION 里记录了来源 commit）
mkdir -p "$DEST/moss_tts_nano" "$DEST/assets"

cp "$UPSTREAM_REPO/moss_tts_nano_runtime.py" \
   "$UPSTREAM_REPO/text_normalization_pipeline.py" \
   "$UPSTREAM_REPO/tts_robust_normalizer_single_script.py" \
   "$DEST/"
cp "$UPSTREAM_REPO/moss_tts_nano/__init__.py" "$UPSTREAM_REPO/moss_tts_nano/defaults.py" "$DEST/moss_tts_nano/"
cp -r "$UPSTREAM_REPO/assets/audio" "$DEST/assets/"
cp "$UPSTREAM_REPO/assets/demo.jsonl" "$DEST/assets/"
cp "$UPSTREAM_REPO/LICENSE" "$DEST/LICENSE"

COMMIT="$(git -C "$UPSTREAM_REPO" rev-parse "$UPSTREAM_REF")"
COMMIT_DATE="$(git -C "$UPSTREAM_REPO" log -1 --format=%cs "$COMMIT")"
cat > "$DEST/UPSTREAM_VERSION" <<EOF
repo=$(git -C "$UPSTREAM_REPO" remote get-url origin)
commit=$COMMIT
commit_date=$COMMIT_DATE
synced_files=moss_tts_nano_runtime.py,text_normalization_pipeline.py,tts_robust_normalizer_single_script.py,moss_tts_nano/__init__.py,moss_tts_nano/defaults.py,assets/audio,assets/demo.jsonl
EOF

echo "已同步上游代码到 $DEST (commit $COMMIT)"
echo "如有需要，请同步检查 app/engine.py 是否仍与上游接口兼容。"
