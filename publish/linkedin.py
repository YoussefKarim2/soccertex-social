#!/usr/bin/env python3
"""LinkedIn publisher — personal profile, via the self-serve route.

WHICH LINKEDIN THIS POSTS TO, AND WHY
-------------------------------------
This posts to **your personal profile**, not the SoccerTex Company Page.

That is a deliberate trade, not an oversight:

  • Personal profile uses `w_member_social`, from LinkedIn's **Share on
    LinkedIn** product. Self-serve — you add the product in the Developer
    Portal and it works. No review, no waiting.

  • Company Page needs the **Community Management API**: Development tier,
    then Standard tier requiring a finished integration and a single-take
    narrated screen recording. Rejection is terminal for that app — you start
    over with a new one.

For a manufacturer selling to other businesses, a founder's own profile
usually outperforms a company page anyway. People follow people.

If you later want the Company Page too, apply for the Community Management
API and only `AUTHOR_URN` below changes.

Env:
  LI_ACCESS_TOKEN   member token with w_member_social (and openid, profile)
  LI_AUTHOR_URN     urn:li:person:xxxx  — or leave unset and it is fetched
  MEDIA_BASE_URL    public https base where out/ is served
"""
from __future__ import annotations
import json, os, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.linkedin.com"
VERSION = "202506"          # LinkedIn-Version header; month-stamped
TIMEOUT = 90


class PublishError(RuntimeError):
    def __init__(self, msg, code=None, retryable=False):
        super().__init__(msg)
        self.code, self.retryable = code, retryable


def _req(method, url, token, body=None, raw=None, ctype="application/json",
         extra_headers=None, expect_json=True):
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": VERSION,
    }
    if extra_headers:
        headers.update(extra_headers)
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None and raw is None:
        headers["Content-Type"] = ctype
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            payload = r.read()
            hdrs = dict(r.headers)
            if not expect_json:
                return payload, hdrs
            return (json.loads(payload) if payload else {}), hdrs
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        raise PublishError(f"HTTP {e.code}: {text[:400]}", e.code,
                           retryable=e.code >= 500 or e.code == 429) from None
    except urllib.error.URLError as e:
        raise PublishError(f"network: {e.reason}", retryable=True) from None


def author_urn(token: str) -> str:
    env = os.environ.get("LI_AUTHOR_URN")
    if env:
        return env
    me, _ = _req("GET", f"{API}/v2/userinfo", token)
    sub = me.get("sub")
    if not sub:
        raise PublishError(f"could not read member id: {me}")
    return f"urn:li:person:{sub}"


def _fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
        return r.read()


def upload_video(token: str, owner: str, video_url: str) -> str:
    """initializeUpload → PUT the bytes → finalizeUpload. Returns the video URN."""
    data = _fetch(video_url)
    init, _ = _req("POST", f"{API}/rest/videos?action=initializeUpload", token,
                   body={"initializeUploadRequest": {
                       "owner": owner, "fileSizeBytes": len(data),
                       "uploadCaptions": False, "uploadThumbnail": False}})
    value = init.get("value") or {}
    urn = value.get("video")
    instructions = value.get("uploadInstructions") or []
    token_up = value.get("uploadToken", "")
    if not urn or not instructions:
        raise PublishError(f"unexpected initializeUpload response: {init}")

    etags = []
    for ins in instructions:
        first, last = ins.get("firstByte", 0), ins.get("lastByte", len(data) - 1)
        chunk = data[first:last + 1]
        _, hdrs = _req("PUT", ins["uploadUrl"], token, raw=chunk,
                       extra_headers={"Content-Type": "application/octet-stream"},
                       expect_json=False)
        etag = hdrs.get("ETag") or hdrs.get("etag")
        if not etag:
            raise PublishError("upload chunk returned no ETag")
        etags.append(etag.strip('"'))

    _req("POST", f"{API}/rest/videos?action=finalizeUpload", token,
         body={"finalizeUploadRequest": {
             "video": urn, "uploadToken": token_up, "uploadedPartIds": etags}},
         expect_json=False)
    return urn


def post_video(token: str, owner: str, video_url: str, text: str) -> dict:
    urn = upload_video(token, owner, video_url)
    body = {
        "author": owner,
        "commentary": text[:3000],
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED",
                         "targetEntities": [], "thirdPartyDistributionChannels": []},
        "content": {"media": {"id": urn, "title": text.split("\n")[0][:180]}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    _, hdrs = _req("POST", f"{API}/rest/posts", token, body=body, expect_json=False)
    post_id = hdrs.get("x-restli-id") or hdrs.get("X-RestLi-Id")
    if not post_id:
        raise PublishError("post created but no id returned — cannot verify")
    return {"post_id": post_id,
            "permalink": f"https://www.linkedin.com/feed/update/{post_id}/"}


def verify(token: str, post_id: str) -> dict:
    """Read the post back. Never report published without this."""
    enc = urllib.parse.quote(post_id, safe="")
    got, _ = _req("GET", f"{API}/rest/posts/{enc}", token)
    if not got.get("id"):
        raise PublishError(f"{post_id} not readable back — not confirmed live")
    return got


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Publish due LinkedIn posts")
    ap.add_argument("--queue", default="queue.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--now")
    a = ap.parse_args()

    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    qp = Path(a.queue)
    q = json.loads(qp.read_text())
    base = os.environ.get("MEDIA_BASE_URL", q.get("media_base_url", ""))

    due = [i for i in q["items"]
           if i.get("platform") == "linkedin" and i.get("status") == "queued"
           and not i.get("manual")                   # held back for manual posting
           and datetime.fromisoformat(i["publish_at"]).replace(tzinfo=timezone.utc) <= now]

    if not due:
        print("nothing due"); return 0
    print(f"{len(due)} due")
    if a.dry_run:
        for i in due:
            print(f"  DRY  {i['id']:44s} {i['publish_at']}")
        return 0

    token = os.environ.get("LI_ACCESS_TOKEN")
    if not token:
        # Not configured yet is a SKIP, not a failure. Returning 2 here made
        # every hourly run red, which buried the one thing a red run should
        # mean: a post that was supposed to go out and didn't. The overdue
        # items stay queued and the review desk shows them in red, so the
        # signal is not lost — it is just reported where it belongs.
        print(f"LI_ACCESS_TOKEN not set — skipping {len(due)} LinkedIn post(s). "
              f"They stay queued and will go out once LinkedIn is connected.")
        return 0
    if not base:
        print("ERROR: MEDIA_BASE_URL not set — LinkedIn needs a public media URL",
              file=sys.stderr); return 2

    owner = author_urn(token)
    print(f"posting as {owner}")
    changed = False

    for it in due:
        try:
            url = f"{base.rstrip('/')}/{it['video'].lstrip('/')}"
            res = post_video(token, owner, url, it["caption"])
            verify(token, res["post_id"])
            it.update(status="published", result={**res, "verified": True,
                                                 "published_at": now.isoformat()})
            changed = True
            print(f"  OK   {it['id']}  {res['permalink']}")
        except PublishError as e:
            it["attempts"] = it.get("attempts", 0) + 1
            it["last_error"] = str(e)
            if not e.retryable or it["attempts"] >= 3:
                it["status"] = "failed"
                print(f"  FAIL {it['id']}  {e}", file=sys.stderr)
            else:
                print(f"  RETRY LATER {it['id']}  {e}", file=sys.stderr)
            changed = True

    if changed:
        qp.write_text(json.dumps(q, indent=2, ensure_ascii=False))
    return 1 if any(i.get("status") == "failed" for i in due) else 0


if __name__ == "__main__":
    sys.exit(main())
