#!/usr/bin/env python3
"""Builds queue.json — a rolling daily schedule of publish slots.

Cadence: two Instagram reels and two LinkedIn posts a day. Four slots a day
over a 30-day horizon is 120 entries, 60 per platform.

Each slot runs through the topic bank at its own offset, so the four posts on
any given day are always four different topics.

Everything is written as "queued" and publishes on time unless it is vetoed
first; see VETO_HOURS below.

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
# A platform may appear more than once; both run twice a day.
#
# Times are chosen for buyers in the US and Europe, not for Cairo, and the four
# are spread across the working day rather than bunched:
#   11:30 UTC = 06:30 New York, 11:30 London, 12:30 Berlin — European midday,
#               the start of the US day.
#   12:30 UTC = 07:30 New York, 13:30 London, 14:30 Berlin — US morning.
#   15:30 UTC = 10:30 New York, 15:30 London, 16:30 Berlin — US late morning,
#               the European afternoon.
#   17:30 UTC = 12:30 New York, 17:30 London, 18:30 Berlin — US midday,
#               European commute.
#
# All four sit on the half hour deliberately. GitHub's scheduler delivers this
# repository about four runs a DAY whatever the cron says — measured gaps of
# 234 to 493 minutes against a cron offering 144 chances — so the real trigger
# is an external one firing at :32, two minutes after each slot. Four slots on
# the same minute is what lets a single cron expression cover all of them.
#
# The offsets do two jobs. They keep all four slots on different topics on any
# given day, and they space each platform's two airings of a topic as far apart
# as the bank allows. A topic from a platform's first slot comes back round on
# its second after (offset_a - offset_b) mod N days, so each pair is set exactly
# half the bank apart: 15 days with 30 topics, the widest gap available.
# Anything closer — thirds, say — would bunch the repeat to 10 days.
#
# LinkedIn takes 0 and N//2, Instagram N//4 and N//4 + N//2. Those four are
# distinct modulo N for any even N, which is what stops two platforms posting
# the same topic on the same day.
SLOTS = [
    ("linkedin",  "11:30", 0),
    ("instagram", "12:30", N // 4),
    ("linkedin",  "15:30", N // 2),
    ("instagram", "17:30", N // 4 + N // 2),
]

# CONTENT SUPPLY
# --------------
# Four posts a day against a bank of 30 topics is 120 posts a month, and every
# topic now airs FOUR times inside a 30-day window: twice on Instagram and twice
# on LinkedIn, each pair 15 days apart. 15 days is already the best the offsets
# can do, so this is not something a cleverer schedule fixes.
#
# The audiences barely overlap, so a topic appearing on both platforms is far
# less visible than it sounds — but twice a month on the same platform is
# visible, and someone who follows the account will notice inside three weeks.
# The fix is more topics: the bank needs to reach 60 before this cadence stops
# repeating inside a month, and that number has not moved since 10 November.
POSTS_PER_DAY = {}
for _p, _t, _o in SLOTS:
    POSTS_PER_DAY[_p] = POSTS_PER_DAY.get(_p, 0) + 1

# Guard the property the offsets above are chosen for, because a later edit to
# SLOTS is exactly the kind of change that quietly breaks it and nobody notices
# until two posts on one day carry the same topic.
_by_day = [o % N for _p, _t, o in SLOTS]
assert len(set(_by_day)) == len(SLOTS), (
    f"two slots share a bank offset {_by_day} — every day would publish the "
    f"same topic twice")
VETO_HOURS = 24          # how long a post is visible before it publishes

LINKEDIN_NOTE = ("Publishes to the SoccerTex Company Page once LI_ORGANIZATION_ID "
                 "is set, and to the signed-in member's profile until then. The "
                 "Page route needs Community Management API Development tier — "
                 "a 1–4 week review, gated on a confirmed account email, a "
                 "LinkedIn Page, a business email and a published privacy policy.")


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


def slot_shape(items) -> dict:
    """The busiest day's post count per platform, as the queue actually is."""
    from collections import Counter, defaultdict
    byday = defaultdict(Counter)
    for i in items:
        if i.get("status") == "queued":
            byday[i["publish_at"][:10]][i["platform"]] += 1
    shape = {}
    for counts in byday.values():
        for plat, n in counts.items():
            shape[plat] = max(shape.get(plat, 0), n)
    return shape


def build(restart: bool = False) -> dict:
    prior = {}
    if QUEUE.exists():
        old = json.loads(QUEUE.read_text())
        prior = {i["id"]: i for i in old.get("items", [])}

    # CHANGING THE SLOT TABLE WITHOUT --restart IS A MONTH OF SILENCE
    # ---------------------------------------------------------------
    # start_day() resumes the day after the last *queued* post, which is
    # correct when the schedule is unchanged and the horizon is just rolling
    # forward. But a rebuild discards queued items and regenerates them, so
    # when SLOTS has changed the regenerated days land after the old horizon —
    # a month out — and everything between now and then is simply gone. The
    # first run of the four-slot schedule did exactly that: 5 published posts
    # preserved, 120 new ones starting 11 December, and nothing at all for the
    # four weeks in between. It looked like a clean build.
    was = slot_shape(prior.values())
    if was and was != POSTS_PER_DAY and not restart:
        raise SystemExit(
            f"the slot table changed: queue has {was}, SLOTS now says "
            f"{POSTS_PER_DAY}.\n"
            f"Rebuilding without --restart would regenerate the new schedule "
            f"after the old horizon and leave a gap with nothing queued.\n"
            f"Run:  python3 engine/queue_build.py --restart")

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
        "cadence": ("two Instagram reels (12:30, 17:30 UTC) and two LinkedIn "
                    "posts (11:30, 15:30 UTC) a day; auto-publish with a 24h "
                    "veto window"),
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
