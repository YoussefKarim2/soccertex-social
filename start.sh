#!/usr/bin/env bash
# SoccerTex Control — one command.
#
#   ./start.sh
#
# Put your Instagram values in a file called .env next to this script and they
# get loaded automatically. .env is gitignored and never leaves this machine.
set -e
cd "$(dirname "$0")"
[ -f .env ] && set -a && . ./.env && set +a
# ffmpeg may live where a bare shell doesn't look
for d in "$PWD/bin" /opt/homebrew/bin /usr/local/bin; do [ -d "$d" ] && PATH="$PATH:$d"; done
export PATH
command -v ffmpeg >/dev/null || echo "  note: ffmpeg not found — videos can't be made until it is installed (brew install ffmpeg)"
python3 -c "import PIL" 2>/dev/null || { echo "  installing pillow…"; python3 -m pip install --quiet pillow numpy; }
exec python3 control/server.py
