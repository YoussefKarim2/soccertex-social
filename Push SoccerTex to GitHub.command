#!/bin/bash
# Double-click me. Sends everything in this folder to GitHub, keeping whatever
# GitHub recorded in the meantime (posts that went out, review-desk decisions).
cd "$(dirname "$0")" || exit 1
clear
echo "SoccerTex → GitHub"
echo
/usr/bin/env python3 tools/sync_and_push.py
echo
read -n 1 -s -r -p "Press any key to close this window."
