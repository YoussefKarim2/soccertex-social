#!/usr/bin/env python3
"""Instagram publisher — Instagram API with Unified Login.

WHY THIS IS NOT THE INSTAGRAM-LOGIN VERSION
--------------------------------------------
This file used to talk to `graph.instagram.com` with `instagram_business_*`
permissions and an Instagram User access token refreshed every 60 days.

That route is closed to us. Meta's migration guide is blunt about it:

    "Newly created apps can't set up the Instagram API with Instagram Login."

The SoccerTex Publisher app was created after that cutoff, so the App
Dashboard offers only two setups: Unified Login (recommended, the only one
getting new features) and Facebook Login (legacy, needs the Instagram account
wired to a Facebook Page). We use Unified Login.

WHAT CHANGED, CONCRETELY
------------------------
  host          graph.instagram.com     -> graph.facebook.com
  permissions   instagram_business_*    -> instagram_basic, instagram_content_publish
  account id    came back with token    -> GET /me/assigned_instagram_accounts
  token         IG User token, 60 days  -> Business Integration System User token
  refresh       ig_refresh_token        -> none; see TOKEN LIFETIME below

The publish sequence itself is unchanged: create a container, poll it until
FINISHED, publish it, then read the media back for a permalink. We still never
report a post as live without that read-back.

APP REVIEW
----------
Not required here. Meta: "When you save your configuration... your app gets
Standard Access to its permissions, which is enough to test with people who
have a role on your app." Youssef owns the account and holds a role on the
app. Advanced Access exists for onboarding *other people's* accounts.

TOKEN LIFETIME
--------------
Whether a Business Integration System User Access Token expires depends on the
configuration; the configuration preview in the App Dashboard states it. There
is no ig_refresh_token equivalent, so the old 25-day refresh workflow is gone.
`main --check-token` reports what the token can still do, so a scheduled run
can warn before anything silently stops publishing.

A token also dies if the Instagram account is removed from the business
portfolio or moved to a different one. That surfaces here as a 190, which is
reported as fatal rather than retried.

Env:
  IG_ACCESS_TOKEN   Business Integration System User Access Token
  IG_USER_ID        optional; discovered via /me/assigned_instagram_accounts
  MEDIA_BASE_URL    public https base where out/ is served, no trailing slash
"""
from __future__ import annotations
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from dataclasses import dataclass
from pathlib import Path

GRAPH = "https://graph.facebook.com"
API_VERSION = "v27.0"
POLL_SECONDS = 5
POLL_MAX = 60          # 5 minutes; Reels encoding is usually well under this

# Instagram fetches media from a public URL rather than accepting an upload,
# so everything in out/ has to be served over public HTTPS before we call this.
# GitHub Pages does that for free. This has not changed with Unified Login.


class PublishError(RuntimeError):
    def __init__(self, msg, code=None, retryable=False):
        super().__init__(msg)
        self.code, self.retryable = code, retryable


def _call(method, path, params, timeout=60):
    """One Graph call. `path` is version-less; the version is added here."""
    url = f"{GRAPH}/{API_VERSION}/{path.lstrip('/')}"
    if method == "GET":
        req = urllib.request.Request(
            f"{url}?{urllib.parse.urlencode(params)}", method="GET")
    else:
        req = urllib.request.Request(
            url, data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body).get("error", {})
            msg, code = err.get("message", body), err.get("code")
        except Exception:
            msg, code = body, None
        # 4 app rate limit, 17 user rate limit, 341 temporarily blocked.
        # 190 is an invalid/expired token — never worth retrying.
        raise PublishError(f"HTTP {e.code}: {msg}", code,
                           retryable=(e.code >= 500 or code in (4, 17, 341))
                           and code != 190) from None
    except urllib.error.URLError as e:
        raise PublishError(f"network: {e.reason}", retryable=True) from None


@dataclass
class Account:
    user_id: str
    token: str

    @classmethod
    def from_env(cls):
        tok = os.environ.get("IG_ACCESS_TOKEN")
        if not tok:
            raise PublishError("IG_ACCESS_TOKEN must be set")
        uid = os.environ.get("IG_USER_ID") or cls.discover_user_id(tok)
        return cls(uid, tok)

    # -- account ----------------------------------------------------------
    @staticmethod
    def discover_user_id(token: str) -> str:
        """Under Unified Login the account ID is not implied by the token:
        /me returns the app user, not the Instagram account. Ask for the
        accounts the business portfolio shared with this app."""
        r = _call("GET", "me/assigned_instagram_accounts",
                  {"access_token": token})
        accounts = r.get("data") or []
        if not accounts:
            raise PublishError(
                "no Instagram accounts assigned to this app — check the "
                "account is shared with the app in the business portfolio")
        if len(accounts) > 1:
            ids = ", ".join(a.get("id", "?") for a in accounts)
            raise PublishError(
                f"{len(accounts)} Instagram accounts assigned ({ids}); "
                "set IG_USER_ID to pick one")
        return accounts[0]["id"]

    # -- quota ------------------------------------------------------------
    def quota(self):
        """Meta's docs disagree with themselves (50 vs 100 per 24h). Ask the
        API rather than trusting either number."""
        r = _call("GET", f"{self.user_id}/content_publishing_limit",
                  {"fields": "config,quota_usage", "access_token": self.token})
        d = (r.get("data") or [{}])[0]
        used = d.get("quota_usage", 0)
        cap = (d.get("config") or {}).get("quota_total", 50)
        return used, cap

    # -- publish ----------------------------------------------------------
    def _container(self, params):
        params["access_token"] = self.token
        r = _call("POST", f"{self.user_id}/media", params)
        cid = r.get("id")
        if not cid:
            raise PublishError(f"no container id in response: {r}")
        return cid

    def _wait(self, container_id):
        for _ in range(POLL_MAX):
            r = _call("GET", container_id,
                      {"fields": "status_code,status", "access_token": self.token})
            s = r.get("status_code")
            if s == "FINISHED":
                return
            if s in ("ERROR", "EXPIRED"):
                raise PublishError(f"container {s}: {r.get('status')}")
            time.sleep(POLL_SECONDS)
        raise PublishError("container never reached FINISHED", retryable=True)

    def _publish(self, container_id):
        r = _call("POST", f"{self.user_id}/media_publish",
                  {"creation_id": container_id, "access_token": self.token})
        mid = r.get("id")
        if not mid:
            raise PublishError(f"no media id in response: {r}")
        return mid

    def post_reel(self, video_url, caption, cover_url=None, share_to_feed=True):
        p = {"media_type": "REELS", "video_url": video_url,
             "caption": caption[:2200], "share_to_feed": str(share_to_feed).lower()}
        if cover_url:
            p["cover_url"] = cover_url
        cid = self._container(p)
        self._wait(cid)
        return self._publish(cid)

    def post_image(self, image_url, caption):
        cid = self._container({"image_url": image_url, "caption": caption[:2200]})
        self._wait(cid)
        return self._publish(cid)

    def post_carousel(self, image_urls, caption):
        if not 2 <= len(image_urls) <= 10:
            raise PublishError("carousel needs 2-10 images")
        children = []
        for u in image_urls:
            r = _call("POST", f"{self.user_id}/media",
                      {"image_url": u, "is_carousel_item": "true",
                       "access_token": self.token})
            children.append(r["id"])
        cid = self._container({"media_type": "CAROUSEL",
                               "children": ",".join(children),
                               "caption": caption[:2200]})
        self._wait(cid)
        return self._publish(cid)

    # -- verification -----------------------------------------------------
    def verify_live(self, media_id):
        """Never report a post as published without reading it back."""
        r = _call("GET", media_id,
                  {"fields": "id,permalink,timestamp,media_type",
                   "access_token": self.token})
        if not r.get("permalink"):
            raise PublishError(f"media {media_id} has no permalink — not live")
        return r

    # -- token ------------------------------------------------------------
    def check_token(self):
        """There is no refresh call under Unified Login. The useful check is
        whether the token still resolves the account and the publishing quota
        — if the account left the portfolio, both fail with a 190."""
        who = _call("GET", self.user_id,
                    {"fields": "id,username", "access_token": self.token})
        used, cap = self.quota()
        return {"id": who.get("id"), "username": who.get("username"),
                "quota_used": used, "quota_total": cap}


def publish_item(acct: Account, item: dict, media_base: str) -> dict:
    """Publish one queue entry. Returns the result record to write back."""
    kind = item.get("kind", "reel")
    cap = item["caption"]
    url = lambda rel: f"{media_base.rstrip('/')}/{rel.lstrip('/')}"

    if kind == "reel":
        mid = acct.post_reel(url(item["video"]), cap,
                             cover_url=url(item["cover"]) if item.get("cover") else None)
    elif kind == "image":
        mid = acct.post_image(url(item["image"]), cap)
    elif kind == "carousel":
        mid = acct.post_carousel([url(u) for u in item["images"]], cap)
    else:
        raise PublishError(f"unknown kind {kind!r}")

    live = acct.verify_live(mid)
    return {"media_id": mid, "permalink": live["permalink"],
            "published_at": live.get("timestamp"), "verified": True}


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Publish due Instagram posts")
    ap.add_argument("--queue", default="queue.json")
    ap.add_argument("--dry-run", action="store_true",
                    help="resolve what would publish, call nothing")
    ap.add_argument("--check-token", action="store_true",
                    help="report what the token can still reach, publish nothing")
    ap.add_argument("--now", help="ISO datetime override, for testing")
    a = ap.parse_args()

    if a.check_token:
        try:
            acct = Account.from_env()
            info = acct.check_token()
        except PublishError as e:
            print(f"token check FAILED: {e}", file=sys.stderr)
            return 2
        print(f"token OK  account {info['id']} (@{info['username']})  "
              f"quota {info['quota_used']}/{info['quota_total']}")
        return 0

    from datetime import datetime, timezone
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    qp = Path(a.queue)
    q = json.loads(qp.read_text())
    media_base = os.environ.get("MEDIA_BASE_URL", q.get("media_base_url", ""))

    due = [it for it in q["items"]
           if it.get("platform") == "instagram"
           and it.get("status") == "queued"          # "vetoed" is never picked up
           and datetime.fromisoformat(it["publish_at"]).replace(
               tzinfo=timezone.utc) <= now]

    if not due:
        print("nothing due"); return 0
    print(f"{len(due)} due")

    if a.dry_run:
        for it in due:
            print(f"  DRY  {it['id']:22s} {it['kind']:9s} {it['publish_at']}")
        return 0

    if not media_base:
        print("ERROR: MEDIA_BASE_URL not set — Instagram fetches media by URL",
              file=sys.stderr)
        return 2

    acct = Account.from_env()
    print(f"posting as Instagram account {acct.user_id}")
    used, cap_ = acct.quota()
    print(f"quota {used}/{cap_} used in the last 24h")
    changed = False

    for it in due:
        if used >= cap_:
            print(f"  quota reached, stopping; {it['id']} stays queued")
            break
        try:
            res = publish_item(acct, it, media_base)
            it.update(status="published", result=res)
            used += 1; changed = True
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
