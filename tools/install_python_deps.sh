#!/bin/sh
set -eu

wheel_dir="${1:-/wheels}"
requirements_file="${2:-/srv/requirements.txt}"
wheel_count=0
set --

for wheel in "$wheel_dir"/*.whl; do
    [ -f "$wheel" ] || continue
    filename="$(basename "$wheel")"

    # torch / torchaudio 已经由基础镜像或前面的安装步骤提供，避免 wheelhouse
    # 中误放的 CPU/CUDA 变体覆盖它们。
    case "$filename" in
        torch-*|torchaudio-*|nvidia-*|triton-*)
            printf 'skip base-image package: %s\n' "$filename"
            continue
            ;;
    esac

    python - "$wheel" <<'PY'
import sys
import zipfile

path = sys.argv[1]
try:
    with zipfile.ZipFile(path) as archive:
        broken = archive.testzip()
        if broken:
            raise RuntimeError(f"damaged member: {broken}")
except Exception as exc:
    raise SystemExit(
        f"invalid or incomplete wheel: {path}\n"
        f"  {type(exc).__name__}: {exc}\n"
        "请重新下载该文件，确保它是完整的 .whl 而不是网页或未完成下载。"
    )
print(f"wheel ok: {path}")
PY

    set -- "$@" "$wheel"
    wheel_count=$((wheel_count + 1))
done

if [ "$wheel_count" -gt 0 ]; then
    printf 'installing %s local wheel(s) from %s\n' "$wheel_count" "$wheel_dir"
    python -m pip install \
        --timeout 600 \
        --retries 20 \
        --find-links "$wheel_dir" \
        "$@"
fi

python -m pip install \
    --timeout 600 \
    --retries 20 \
    --prefer-binary \
    --find-links "$wheel_dir" \
    -r "$requirements_file"
