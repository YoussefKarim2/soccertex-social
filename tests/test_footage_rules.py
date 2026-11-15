#!/usr/bin/env python3
"""The promises about library footage, checked without rendering a frame.

    python3 tests/test_footage_rules.py

1. SoccerTex's own voice is refused over library footage.
2. Every clip in every reel is marked as stock and carries the on-screen stamp.
3. Two reels that post back to back do not open on the same clip.
4. Every reel has real footage in it.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_vibes as B
from engine import vibes as V
from engine.bank import BANK
from engine.footage import StockMisuse

fails = []


def check(ok, what):
    print(("  ok   " if ok else "  FAIL ") + what)
    if not ok:
        fails.append(what)


for bad in ("Our line runs four of these", "We cut sixty layers", "Inside SoccerTex", ["SEND", "US", "A SKETCH"]):
    try:
        V.stock_ok(bad)
        check(False, f"refuses {bad!r}")
    except StockMisuse:
        check(True, f"refuses {bad!r}")
try:
    V.stock_ok("Fabric spread in layers, pattern laid out as a marker.")
    check(True, "allows a line that describes a process")
except StockMisuse:
    check(False, "allows a line that describes a process")


def shots(scene):
    if isinstance(scene, V.Plate):
        return [scene]
    if isinstance(scene, V.BlueprintScene):
        return list(scene.shots.values())
    if isinstance(scene, V.Breaks):
        inner = [scene.inner.hookshot] if scene.inner.hookshot else []
        return inner + [p for _, _, p, _ in scene.parts if p is not None]
    return []


unstamped, without = [], []
for t in BANK:
    v, _ = B.build(t["id"], "social")
    found = [s for scene in v.scenes for s in shots(scene)]
    if not found:
        without.append(t["id"])
    unstamped += [f"{t['id']}:{s.path.stem}" for s in found
                  if s.source != "stock" or not s.label_stock or s.credit]
    for scene in v.scenes:
        scene.close()
check(not unstamped, f"every library clip is stamped on screen {unstamped or ''}")
check(not without, f"every reel has real footage in it {without or ''}")

try:
    B.check_footage()
    check(True, "no two back-to-back reels open on the same clip")
except SystemExit as e:
    check(False, str(e))

print(f"\n{'FAILED' if fails else 'passed'}: {len(fails)} failure(s)")
sys.exit(1 if fails else 0)
