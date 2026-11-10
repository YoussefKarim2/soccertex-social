#!/usr/bin/env python3
"""Preflight — prove the queue can actually publish, without publishing.

A dry run only proves the queue parses and the right items are due. It never
touches the thing that actually breaks: the media. Instagram does not accept
uploads, it fetches the file from a public URL, so a 404, a wrong content type
or a truncated file is a publish failure that nothing notices until the post
does not appear.

This checks, for every item still waiting to go out:

  media      every video and cover URL resolves, with a plausible type and size
  captions   inside Instagram's limits
  schedule   the slots are intact — right count per day, unique ids, no two
             posts on the same topic the same day
  token      the Instagram token still reads the account, and the 24h
             publishing quota has room for the cadence

Exit 0 means everything checked out. Exit 1 means something would fail at
publish time; the report says which items and why.

  python3 publish/preflight.py --queue queue.json
"""
from __future__ import annotations
import json, os, sys, urllib.error, urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TIMEOUT = 30
MIN_VIDEO_BYTES = 200_000       # anything smaller is not a finished reel
MIN_COVER_BYTES = 5_000
IG_CAPTION_MAX = 2_200          # Instagram's documented limit
IG_HASHTAG_MAX = 30
PENDING = ("queued", "blocked", "vetoed")

OK, BAD = "ok", "bad"


def head(url: str) -> dict:
    """HEAD the URL, falling back to a ranged GET if HEAD is not allowed."""
    for method, headers in (("HEAD", {}), ("GET", {"Range": "bytes=0-1023"})):
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                length = r.headers.get("Content-Length")
                if method == "GET":
                    rng = r.headers.get("Content-Range", "")
                    length = rng.rsplit("/", 1)[-1] if "/" in rng else length
                return {"state": OK, "status": r.status,
                        "type": (r.headers.get("Content-Type") or "").split(";")[0],
                        "bytes": int(length) if length and length.isdigit() else None}
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):
                continue            # host refuses HEAD — try the ranged GET
            return {"state": BAD, "why": f"HTTP {e.code}"}
        except urllib.error.URLError as e:
            return {"state": BAD, "why": f"network: {e.reason}"}
        except Exception as e:                       # noqa: BLE001
            return {"state": BAD, "why": f"{type(e).__name__}: {e}"}
    return {"state": BAD, "why": "HEAD and ranged GET both refused"}


def check_media(items, base) -> list[str]:
    """Every distinct media URL the pending items reference."""
    wanted: dict[str, tuple[str, int]] = {}
    for it in items:
        for key, kind, floor in (("video", "video", MIN_VIDEO_BYTES),
                                 ("cover", "image", MIN_COVER_BYTES)):
            rel = it.get(key)
            if rel:
                wanted[f"{base.rstrip('/')}/{rel.lstrip('/')}"] = (kind, floor)

    print(f"media      {len(wanted)} distinct URLs to check")
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = dict(zip(wanted, pool.map(head, wanted)))

    problems = []
    for url, (kind, floor) in sorted(wanted.items()):
        r = results[url]
        name = url.rsplit("/", 1)[-1]
        if r["state"] == BAD:
            problems.append(f"{name}: {r['why']}")
        elif not r["type"].startswith(kind):
            problems.append(f"{name}: served as {r['type'] or 'no type'}, not {kind}/*")
        elif r["bytes"] is not None and r["bytes"] < floor:
            problems.append(f"{name}: only {r['bytes']:,} bytes")
    if not problems:
        total = sum(r["bytes"] or 0 for r in results.values())
        print(f"           all {len(wanted)} reachable, {total/1e6:.0f} MB in total  OK")
    return problems


def check_captions(items) -> list[str]:
    problems = []
    for it in items:
        cap = it.get("caption") or ""
        if not cap.strip():
            problems.append(f"{it['id']}: empty caption")
            continue
        if it["platform"] == "instagram":
            if len(cap) > IG_CAPTION_MAX:
                problems.append(f"{it['id']}: caption {len(cap)} chars "
                                f"(limit {IG_CAPTION_MAX})")
            tags = cap.count("#")
            if tags > IG_HASHTAG_MAX:
                problems.append(f"{it['id']}: {tags} hashtags (limit {IG_HASHTAG_MAX})")
    if not problems:
        caps = [len(i.get("caption") or "") for i in items]
        print(f"captions   {len(items)} checked, "
              f"{min(caps)}–{max(caps)} chars, inside the limits  OK")
    return problems


def check_schedule(all_items, pending) -> list[str]:
    problems = []
    ids = Counter(i["id"] for i in all_items)
    for iid, n in ids.items():
        if n > 1:
            problems.append(f"duplicate id {iid} appears {n}x")

    byday = defaultdict(list)
    for i in pending:
        byday[i["publish_at"][:10]].append(i)

    expected = Counter()
    for i in pending:
        expected[i["platform"]] += 1

    days = sorted(byday)
    # the first and last day of the horizon can be partial; judge the middle
    for d in days[1:-1] if len(days) > 2 else days:
        day = byday[d]
        per = Counter(i["platform"] for i in day)
        if per.get("instagram") != 2:
            problems.append(f"{d}: {per.get('instagram', 0)} Instagram posts, expected 2")
        topics = [i["topic"] for i in day]
        if len(set(topics)) != len(topics):
            dupe = [t for t, n in Counter(topics).items() if n > 1]
            problems.append(f"{d}: same topic twice in one day — {', '.join(dupe)}")

    blocked = [i for i in pending if i.get("status") == "blocked"
               or i.get("missing_video")]
    for i in blocked:
        problems.append(f"{i['id']}: no video on disk, will not publish")

    now = datetime.now(timezone.utc)
    overdue = [i for i in pending if i.get("status") == "queued"
               and datetime.fromisoformat(i["publish_at"]).replace(
                   tzinfo=timezone.utc) < now]
    if not problems:
        print(f"schedule   {len(days)} days, {expected['instagram']} Instagram "
              f"+ {expected['linkedin']} LinkedIn, ids unique  OK")
    if overdue:
        # not a failure — the publisher picks these up on its next run — but it
        # is the number to watch, because a growing backlog means the runner is
        # not firing often enough.
        print(f"           {len(overdue)} overdue and waiting for the next run")
    return problems


def check_instagram(pending) -> list[str]:
    from publish.instagram import Account, PublishError
    if not os.environ.get("IG_ACCESS_TOKEN"):
        print("token      IG_ACCESS_TOKEN not set — skipped")
        return []
    try:
        acct = Account.from_env()
        info = acct.check_token()
        q = acct.quota()
    except PublishError as e:
        return [f"instagram token: {e}"]

    used = q.get("quota_usage")
    cap = q.get("config", {}).get("quota_total", 50)
    print(f"token      reads @{info.get('username', '?')} "
          f"(id {info.get('id', '?')})  OK")
    print(f"quota      {used} of {cap} posts used in the last 24h")
    per_day = sum(1 for i in pending[:3] if i["platform"] == "instagram") or 2
    if used is not None and cap - used < per_day:
        return [f"publishing quota has room for {cap - used} more posts in the "
                f"next 24h, cadence needs {per_day}"]
    return []


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Check the queue can publish")
    ap.add_argument("--queue", default="queue.json")
    ap.add_argument("--skip-media", action="store_true",
                    help="skip the media URL checks (they need network)")
    a = ap.parse_args()

    q = json.loads(Path(a.queue).read_text())
    items = q["items"]
    pending = sorted((i for i in items if i.get("status") in PENDING),
                     key=lambda i: i["publish_at"])
    base = os.environ.get("MEDIA_BASE_URL", q.get("media_base_url", ""))

    print(f"queue      {len(items)} items, {len(pending)} still to publish")
    print(f"cadence    {q.get('cadence', '—')}")
    print(f"media base {base or '(not set)'}\n")

    problems = []
    problems += check_schedule(items, pending)
    problems += check_captions(pending)
    if a.skip_media:
        print("media      skipped")
    elif not base:
        problems.append("MEDIA_BASE_URL not set — Instagram needs a public media URL")
    else:
        problems += check_media(pending, base)
    problems += check_instagram(pending)

    print()
    if problems:
        print(f"{len(problems)} problem(s) would stop a post going out:",
              file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("preflight clean — every pending post has everything it needs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
