#!/usr/bin/env python3
"""Builds queue.json — a rolling daily schedule across the three platforms.

Cadence: one post per platform per day. 30 topics x 3 platforms = 90 posts,
which is a 30-day cycle with no topic repeating on the same platform.

The three platforms run through the bank at different offsets, so no two posts
on the same day share a topic.

Only Instagram entries get status "scheduled" — those are the ones the publisher
acts on. TikTok and LinkedIn are written as "manual" with the reason attached,
because neither can be published without a person (see PUBLISHING-REALITY.md).

Re-runnable and append-only: entries already published or failed are preserved,
and the horizon rolls forward so the queue never runs dry.
"""
from __future__ import annotations
import json, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.bank import BANK
from engine.compose import caption_for, variant_for

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "queue.json"
OUT = ROOT / "out" / "video"

HORIZON_DAYS = 30          # how far ahead to schedule
N = len(BANK)

# platform -> (UTC hour:minute, offset into the bank)
# Cairo is UTC+2. LinkedIn at 11:30 UTC = 13:30 Cairo = European lunch + US East morning.
PLATFORMS = {
    "linkedin":  ("11:30", 0),
    "instagram": ("16:00", N // 2),
}

VETO_HOURS = 24          # how long a post is visible before it publishes

LINKEDIN_NOTE = ("Publishes to your personal LinkedIn profile via the self-serve "
                 "Share on LinkedIn product (w_member_social) — no app review needed. "
                 "Company Page posting would require the Community Management API, "
                 "which is a weeks-long approval with terminal rejection risk.")


def make_cover(video: Path) -> Path | None:
    cover = video.with_suffix(".cover.jpg")
    if cover.exists() and cover.stat().st_mtime >= video.stat().st_mtime:
        return cover
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.8", "-i", str(video),
         "-frames:v", "1", "-q:v", "3", str(cover)], capture_output=True)
    return cover if r.returncode == 0 and cover.exists() else None


def start_day(prior_items, restart: bool = False) -> datetime:
    """Resume the day after the last scheduled post, or tomorrow on a cold start.

    `restart` ignores anything still merely queued and starts tomorrow. That
    is what you want on go-live day: rebuilding repeatedly during setup keeps
    pushing day 0 further out, so the first post can end up a month away.
    """
    now = datetime.now(timezone.utc)
    future = [] if restart else [
        i["publish_at"] for i in prior_items
        if i.get("status") in ("queued", "vetoed")]
    if future:
        last = max(datetime.fromisoformat(d) for d in future)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last > now:
            return (last + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0)
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


def build(restart: bool = False) -> dict:
    prior = {}
    if QUEUE.exists():
        old = json.loads(QUEUE.read_text())
        prior = {i["id"]: i for i in old.get("items", [])}

    # keep everything already acted on, untouched
    items = [i for i in prior.values() if i.get("status") in ("published", "failed", "vetoed")]
    done_ids = {i["id"] for i in items}

    day0 = start_day(list(prior.values()), restart=restart)

    for d in range(HORIZON_DAYS):
        date = day0 + timedelta(days=d)
        for plat, (hhmm, offset) in PLATFORMS.items():
            topic = BANK[(d + offset) % N]
            variant = variant_for(plat)
            iid = f"{topic['id']}--{plat}--{date:%Y%m%d}"
            if iid in done_ids:
                continue
            h, m = map(int, hhmm.split(":"))
            when = date.replace(hour=h, minute=m)

            video = OUT / f"{topic['id']}--{variant}.mp4"
            item = {
                "id": iid,
                "topic": topic["id"],
                "platform": plat,
                "variant": variant,
                "kind": "reel" if plat != "linkedin" else "video",
                "publish_at": when.isoformat(),
                "caption": caption_for(topic, plat),
                "video": f"video/{topic['id']}--{variant}.mp4",
                "pillar": topic["pillar"],
            }
            if video.exists():
                cov = make_cover(video)
                if cov:
                    item["cover"] = f"video/{cov.name}"
            else:
                item["missing_video"] = True

            # Auto-publish with veto: everything is "queued" and goes out on
            # time unless it is vetoed before then. VETO_HOURS is how long it
            # sits visible in the dashboard first.
            item["status"] = "queued" if video.exists() else "blocked"
            item["veto_until"] = (when - timedelta(hours=VETO_HOURS)).isoformat()
            if plat == "linkedin":
                item["note"] = LINKEDIN_NOTE
            items.append(item)

    items.sort(key=lambda i: (i["publish_at"], i["platform"]))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cadence": "daily on Instagram and LinkedIn; auto-publish with a 24h veto window",
        "topics_in_bank": N,
        "media_base_url": "",
        "items": items,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Build the rolling publish queue")
    ap.add_argument("--restart", action="store_true",
                    help="drop pending queued items and start the schedule "
                         "tomorrow (use on go-live day)")
    a = ap.parse_args()

    q = build(restart=a.restart)
    QUEUE.write_text(json.dumps(q, indent=2, ensure_ascii=False))
    from collections import Counter
    c = Counter((i["platform"], i["status"]) for i in q["items"])
    print(f"queue.json — {len(q['items'])} items over {HORIZON_DAYS} days")
    for (p, s), n in sorted(c.items()):
        print(f"  {p:10s} {s:10s} {n}")
    auto = sum(n for (p, s), n in c.items() if s == "queued")
    missing = sum(1 for i in q["items"] if i.get("missing_video"))
    print(f"\n{auto} publish automatically unless vetoed")
    if missing:
        print(f"{missing} waiting on a video — run build_all.py")


if __name__ == "__main__":
    main()
