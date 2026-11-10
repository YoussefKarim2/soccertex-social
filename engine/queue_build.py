#!/usr/bin/env python3
"""Builds queue.json — a rolling daily schedule of publish slots.

Cadence: two Instagram reels a day plus one LinkedIn post a day. Three slots
a day over a 30-day horizon is 90 entries: 60 Instagram, 30 LinkedIn.

Each slot runs through the topic bank at its own offset, so the three posts on
any given day are always three different topics.

Everything is written as "queued" and publishes on time unless it is vetoed
first; see VETO_HOURS below. LinkedIn entries carry a note explaining that
they go to the personal profile rather than the Company Page.

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

# (platform, UTC hour:minute, offset into the bank) — one entry per daily slot.
# A platform may appear more than once; Instagram runs twice a day.
#
# Times are chosen for buyers in the US and Europe, not for Cairo:
#   12:30 UTC = 07:30 New York, 13:30 London, 14:30 Berlin — US morning,
#               European early afternoon.
#   17:00 UTC = 12:00 New York, 17:00 London, 18:00 Berlin — US midday,
#               European commute.
# LinkedIn stays at 11:30 UTC, which is the middle of the European working day
# and the start of the US one.
#
# The offsets do two jobs. They keep the three slots on different topics on any
# given day, and they space a topic's two Instagram airings as far apart as the
# bank allows. A topic from the first Instagram slot comes back round on the
# second after (offset_a - offset_b) mod N days, so the two offsets are set
# exactly half the bank apart: 15 days with 30 topics, the widest possible gap.
# Anything closer — thirds, say — would bunch the repeat to 10 days.
SLOTS = [
    ("linkedin",  "11:30", 0),
    ("instagram", "12:30", N // 4),
    ("instagram", "17:00", N // 4 + N // 2),
]

# CONTENT SUPPLY
# --------------
# Two Instagram posts a day is 60 Instagram posts a month against a bank of 30
# topics, so every topic is published twice in a 30-day window, 15 days apart.
# That is a real repetition, not a rounding error, and 15 days is already the
# best the offsets can do. The fix is more topics, not a cleverer offset: the
# bank needs to reach 60 before this cadence stops repeating inside a month.
POSTS_PER_DAY = {}
for _p, _t, _o in SLOTS:
    POSTS_PER_DAY[_p] = POSTS_PER_DAY.get(_p, 0) + 1

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
        for plat, hhmm, offset in SLOTS:
            topic = BANK[(d + offset) % N]
            variant = variant_for(plat)
            # The time is part of the id now. Two Instagram posts on the same
            # day would otherwise collide whenever the offsets wrapped onto
            # the same topic, and one of them would silently vanish.
            iid = f"{topic['id']}--{plat}--{date:%Y%m%d}-{hhmm.replace(':', '')}"
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
        "cadence": ("two Instagram reels a day (12:30 and 17:00 UTC) plus one "
                    "LinkedIn post (11:30 UTC); auto-publish with a 24h veto window"),
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
