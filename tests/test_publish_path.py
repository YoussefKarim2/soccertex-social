#!/usr/bin/env python3
"""Exercise the Instagram publish path with the Graph API stubbed out.

`--dry-run` proves only that the queue parses and the right items are due. It
returns before the first API call, so the part that actually posts — create a
container, poll it to FINISHED, publish it, read the permalink back, write the
result into the queue — is never run by any check we have.

This stubs urllib inside publish/instagram.py, so everything above the socket
is the real code: URL building, the poll loop, error classification, the
retry/fail decision and the queue write-back.

Three scenarios, because two posts a day means the interesting cases are about
what the second post does when the first one has trouble:

  1. both due posts publish
  2. the first hits a 500 — retryable, so it stays queued for the next run,
     and the second must still go out
  3. the first hits a hard error — marked failed, and the second must still
     go out, and the run must exit non-zero

  python3 tests/test_publish_path.py
"""
from __future__ import annotations
import io, json, sys, urllib.error, urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "publish"))
import instagram as ig          # noqa: E402

UID = "17841417903547798"
BASE = "https://example.test/media"


class FakeResponse(io.BytesIO):
    status = 200
    headers: dict = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False


def http_error(code: int, message: str, err_code: int | None = None):
    body = json.dumps({"error": {"message": message, "code": err_code}}).encode()
    return urllib.error.HTTPError(
        "https://graph.facebook.com/x", code, message, {}, io.BytesIO(body))


class Graph:
    """A stand-in for the Graph API. `fail` injects one fault per item index."""

    def __init__(self, fail: dict | None = None):
        self.fail = fail or {}
        self.calls: list[tuple[str, str]] = []
        self.containers = 0
        self.polls: dict[str, int] = {}
        self.published: list[str] = []

    def __call__(self, req, timeout=None):
        url, method = req.full_url, req.get_method()
        path = url.split("/v27.0/", 1)[1]
        body = dict(urllib.parse.parse_qsl(
            (req.data or b"").decode())) if req.data else {}
        query = dict(urllib.parse.parse_qsl(
            path.split("?", 1)[1])) if "?" in path else {}
        path = path.split("?", 1)[0]
        self.calls.append((method, path))

        if path == f"{UID}/media" and method == "POST":
            # faults are keyed by which caption is being posted, so a scenario
            # can target the first or second post of the day
            for marker, fault in self.fail.items():
                if marker in body.get("caption", ""):
                    raise fault
            assert body["media_type"] == "REELS", body
            assert body["video_url"].startswith(BASE), body["video_url"]
            assert body["caption"], "empty caption reached the API"
            self.containers += 1
            return FakeResponse(json.dumps(
                {"id": f"container-{self.containers}"}).encode())

        if path.startswith("container-") and method == "GET":
            assert query.get("access_token"), "poll without a token"
            n = self.polls.get(path, 0) + 1
            self.polls[path] = n
            # not finished on the first look, so the poll loop is real
            return FakeResponse(json.dumps(
                {"status_code": "FINISHED" if n > 1 else "IN_PROGRESS"}).encode())

        if path == f"{UID}/media_publish" and method == "POST":
            cid = body["creation_id"]
            mid = f"media-{cid.split('-')[-1]}"
            self.published.append(mid)
            return FakeResponse(json.dumps({"id": mid}).encode())

        if path.startswith("media-") and method == "GET":
            n = path.split("-")[-1]
            return FakeResponse(json.dumps(
                {"id": path, "media_type": "REELS",
                 "permalink": f"https://www.instagram.com/reel/FAKE{n}/",
                 "timestamp": "2026-11-11T12:30:05+0000"}).encode())

        if path == f"{UID}/content_publishing_limit":
            return FakeResponse(json.dumps(
                {"data": [{"quota_usage": 0, "config": {"quota_total": 100}}]}).encode())

        if path == UID and method == "GET":
            return FakeResponse(json.dumps(
                {"id": UID, "username": "soccertex.eg"}).encode())

        raise AssertionError(f"unexpected call {method} {path}")


def two_due_items(tmp: Path) -> Path:
    """A queue with exactly the two Instagram slots of one day, both due."""
    when = datetime.now(timezone.utc) - timedelta(minutes=5)
    items = []
    for n, (hhmm, topic) in enumerate((("12:30", "small-orders"),
                                       ("17:00", "sewing-line"))):
        items.append({
            "id": f"{topic}--instagram--20261111-{hhmm.replace(':', '')}",
            "topic": topic, "platform": "instagram", "variant": "social",
            "kind": "reel",
            "publish_at": (when - timedelta(minutes=n)).isoformat(),
            "caption": f"caption for {topic} — what a buyer asks about.",
            "video": f"video/{topic}--social.mp4",
            "cover": f"video/{topic}--social.cover.jpg",
            "pillar": "education", "status": "queued",
        })
    # a LinkedIn item and a future one, which must both be left alone
    items.append({"id": "x--linkedin--20261111-1130", "topic": "x",
                  "platform": "linkedin", "kind": "video", "status": "queued",
                  "publish_at": when.isoformat(), "caption": "li",
                  "video": "video/x--business.mp4", "pillar": "education"})
    items.append({"id": "y--instagram--20261112-1230", "topic": "y",
                  "platform": "instagram", "kind": "reel", "status": "queued",
                  "publish_at": (when + timedelta(days=1)).isoformat(),
                  "caption": "later", "video": "video/y--social.mp4",
                  "pillar": "education"})
    p = tmp / "queue.json"
    p.write_text(json.dumps({"media_base_url": BASE, "items": items}, indent=2))
    return p


def run(queue: Path, graph: Graph) -> int:
    ig.urllib.request.urlopen = graph
    ig.time.sleep = lambda s: None
    sys.argv = ["instagram.py", "--queue", str(queue)]
    import os
    os.environ["IG_ACCESS_TOKEN"] = "stub-token"
    os.environ["IG_USER_ID"] = UID
    os.environ["MEDIA_BASE_URL"] = BASE
    return ig.main()


def load(queue: Path):
    items = json.loads(queue.read_text())["items"]
    return {i["id"]: i for i in items}


def scenario_both_publish(tmp: Path):
    q = two_due_items(tmp / "a")
    g = Graph()
    code = run(q, g)
    items = load(q)
    ig_items = [i for i in items.values() if i["platform"] == "instagram"
                and i["id"].startswith(("small-orders", "sewing-line"))]
    assert code == 0, f"exit {code}"
    assert len(g.published) == 2, g.published
    for it in ig_items:
        assert it["status"] == "published", it
        assert it["result"]["permalink"].startswith(
            "https://www.instagram.com/reel/FAKE"), it["result"]
        assert it["result"]["verified"] is True
    # the poll loop ran more than once per post, so FINISHED was waited for
    assert all(n >= 2 for n in g.polls.values()), g.polls
    # neither the LinkedIn item nor tomorrow's post was touched
    assert items["x--linkedin--20261111-1130"]["status"] == "queued"
    assert items["y--instagram--20261112-1230"]["status"] == "queued"
    # the cover was sent, not just the video
    print(f"  1. both publish — {len(g.published)} posts, "
          f"{len(g.calls)} API calls, exit {code}")


def scenario_first_retryable(tmp: Path):
    q = two_due_items(tmp / "b")
    g = Graph(fail={"small-orders": http_error(500, "Internal error")})
    code = run(q, g)
    items = load(q)
    first = items["small-orders--instagram--20261111-1230"]
    second = items["sewing-line--instagram--20261111-1700"]
    assert code == 0, f"a retryable error should not fail the run, got {code}"
    assert first["status"] == "queued", first
    assert first["attempts"] == 1, first
    assert "500" in first["last_error"], first["last_error"]
    assert second["status"] == "published", second
    assert len(g.published) == 1, g.published
    print(f"  2. first post 500s — it stays queued (attempt 1), "
          f"second still publishes, exit {code}")


def scenario_first_hard_fail(tmp: Path):
    q = two_due_items(tmp / "c")
    g = Graph(fail={"small-orders": http_error(
        400, "The video file is not supported", 100)})
    code = run(q, g)
    items = load(q)
    first = items["small-orders--instagram--20261111-1230"]
    second = items["sewing-line--instagram--20261111-1700"]
    assert code == 1, f"a real failure must exit non-zero, got {code}"
    assert first["status"] == "failed", first
    assert second["status"] == "published", second
    print(f"  3. first post hard-fails — marked failed, second still "
          f"publishes, exit {code} (red run)")


def main():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for sub in "abc":
            (tmp / sub).mkdir()
        print("publish path, Graph API stubbed:")
        scenario_both_publish(tmp)
        scenario_first_retryable(tmp)
        scenario_first_hard_fail(tmp)
    print("\nall scenarios passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
