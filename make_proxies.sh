#!/usr/bin/env bash
# Rebuild 9:16 proxies from both footage pools.
#
# WHY THESE ARE NO LONGER 1080 WIDE
# ---------------------------------
# The reel format crops into a plate to make a close-up — `tight=1.9` keeps
# roughly the middle half. Against a 1080-wide proxy that means sampling ~570
# pixels and stretching them back to 1080, and it looked exactly like what it
# was: mush. Every tight shot in the first narrated cut was soft.
#
# So a proxy is now rendered at whatever the source can honestly give, up to
# 2x, and `engine/reel.py` reads the proxy's real width and refuses to crop in
# further than that width supports. A clip that was shot wide and landscape
# cannot be rescued by either — it just does not have the pixels — and the
# guard will say so rather than quietly blurring.
#
# Height is capped at 3840 to keep decode cost sane; above that the renderer
# spends longer resizing than composing.
set -e
cd "$(dirname "$0")"
mkdir -p assets/footage/proxy

TARGET_W=2160        # 2x the 1080 canvas
MAX_W=2160

for pool in own stock; do
  for f in assets/footage/$pool/*.mp4 assets/footage/$pool/*.mov; do
    [ -e "$f" ] || continue
    n=$(basename "${f%.*}")
    out="assets/footage/proxy/$n.mp4"
    [ "$out" -nt "$f" ] 2>/dev/null && continue

    # What width survives a 9:16 crop of this source, at its native pixels?
    # two calls rather than one: ffprobe's csv separator syntax differs
    # between builds and silently yields an empty string on the wrong one,
    # which then falls through to 1080 and undoes the whole point of this file
    sw=$(ffprobe -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 "$f")
    sh=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$f")
    : "${sw:?could not read width of $f}" "${sh:?could not read height of $f}"
    # a 9:16 crop takes the full height and 9/16 of it in width, or the full
    # width and 16/9 of it in height, whichever the source actually limits
    crop_w=$(( sh * 9 / 16 ))
    [ "$crop_w" -gt "$sw" ] && crop_w=$sw
    w=$crop_w
    [ "$w" -gt "$MAX_W" ] && w=$MAX_W
    [ "$w" -lt 1080 ] && w=1080          # never go below the delivery canvas
    w=$(( w / 2 * 2 ))                    # keep it even for yuv420p
    h=$(( w * 16 / 9 )); h=$(( h / 2 * 2 ))

    echo "  $n  ${sw}x${sh} -> ${w}x${h}$( [ "$crop_w" -lt 1080 ] && echo '  (source is short on pixels for a vertical crop)' )"
    # No -t truncation any more. The old 12s cap threw away more than half of
    # the longest clip, and with four clips carrying thirty videos every
    # second of distinct material counts.
    ffmpeg -v error -y -i "$f" \
      -vf "scale=${w}:${h}:force_original_aspect_ratio=increase,crop=${w}:${h},fps=30" \
      -c:v libx264 -crf 18 -preset fast -an "$out"
  done
done
echo "proxies rebuilt"
