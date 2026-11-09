#!/usr/bin/env bash
# Rebuild 9:16 proxies from both footage pools.
set -e
cd "$(dirname "$0")"
mkdir -p assets/footage/proxy
for pool in own stock; do
  for f in assets/footage/$pool/*.mp4 assets/footage/$pool/*.mov; do
    [ -e "$f" ] || continue
    n=$(basename "${f%.*}")
    out="assets/footage/proxy/$n.mp4"
    [ "$out" -nt "$f" ] 2>/dev/null && continue
    echo "  $n"
    ffmpeg -v error -y -i "$f" -t 12 \
      -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
      -c:v libx264 -crf 20 -preset veryfast -an "$out"
  done
done
