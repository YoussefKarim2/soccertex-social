#!/usr/bin/env python3
"""Renders every topic in the bank, both cuts. Idempotent.

  python3 build_all.py            render anything missing
  python3 build_all.py --force    re-render everything
  python3 build_all.py seams gsm  render just those topics

A finished video is only re-rendered if its source is newer, so the weekly
GitHub run normally does nothing and costs a minute. The first run does the
whole library.
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine.bank import BANK, BY_ID
from engine.compose import compose

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out" / "video"
SOURCES = [ROOT / "engine" / "bank.py", ROOT / "engine" / "compose.py",
           ROOT / "engine" / "render.py", ROOT / "engine" / "motion.py",
           ROOT / "engine" / "footage.py", ROOT / "engine" / "audio.py"]


def stale(path: Path) -> bool:
    if not path.exists():
        return True
    t = path.stat().st_mtime
    return any(s.exists() and s.stat().st_mtime > t for s in SOURCES)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    force = "--force" in sys.argv
    topics = [BY_ID[a] for a in args] if args else BANK

    OUT.mkdir(parents=True, exist_ok=True)
    t0, made, skipped, failed = time.time(), 0, 0, []

    for t in topics:
        for variant in ("social", "business"):
            dest = OUT / f"{t['id']}--{variant}.mp4"
            if not force and not stale(dest):
                skipped += 1
                continue
            try:
                s = time.time()
                v = compose(t, variant)
                v.write()
                made += 1
                print(f"  {t['id']+'--'+variant:34s} {v.seconds:5.1f}s  "
                      f"{dest.stat().st_size/1024/1024:5.2f} MB  {time.time()-s:5.1f}s")
            except Exception as e:
                failed.append((t["id"], variant, str(e)[:120]))
                print(f"  {t['id']+'--'+variant:34s} FAILED  {e}", file=sys.stderr)

    print(f"\nrendered {made}, up to date {skipped}, failed {len(failed)} "
          f"— {time.time()-t0:.0f}s")
    for tid, var, err in failed:
        print(f"  ! {tid}--{var}: {err}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
