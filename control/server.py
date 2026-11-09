#!/usr/bin/env python3
"""SoccerTex Control — the local dashboard.

Same shape as ChatNest: one process, no dependencies beyond the standard
library, a web dashboard on localhost, and the AI work happening behind it.

    python3 control/server.py
    → http://localhost:4100

Why local rather than a hosted page: a page you serve yourself is not
sandboxed, so its buttons can actually run things — render a video, publish a
post, roll the schedule. A hosted dashboard can only ever show you a snapshot.

This process does the interactive half. The GitHub workflows do the unattended
half. They share one file, queue.json, so neither can drift from the other.
"""
from __future__ import annotations
import json, os, re, subprocess, sys, threading, time, traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = Path(__file__).resolve().parent / "public"
QUEUE = ROOT / "queue.json"
VIDEO = ROOT / "out" / "video"
LOGFILE = ROOT / "control" / "activity.log"
PORT = int(os.environ.get("PORT", "4100"))

LOCK = threading.Lock()
JOBS: dict[str, dict] = {}          # name -> {running, started, lines, rc}


# ───────────────────────────────────────────────────────────── logging ──
def log(msg: str, level: str = "info"):
    line = {"t": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "level": level, "msg": msg}
    LOGFILE.parent.mkdir(parents=True, exist_ok=True)
    with LOCK:
        with LOGFILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
    print(f"[{level}] {msg}", flush=True)


def tail_log(n=120):
    if not LOGFILE.exists():
        return []
    lines = LOGFILE.read_text(encoding="utf-8").splitlines()[-n:]
    out = []
    for l in lines:
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


# ───────────────────────────────────────────────────────────── helpers ──
def load_queue() -> dict:
    if not QUEUE.exists():
        return {"items": []}
    return json.loads(QUEUE.read_text(encoding="utf-8"))


def save_queue(q: dict):
    tmp = QUEUE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(QUEUE)


def have(cmd: str) -> bool:
    from shutil import which
    return which(cmd) is not None


def env_state() -> dict:
    tok = os.environ.get("IG_ACCESS_TOKEN", "")
    return {
        # Optional under Unified Login: the publisher discovers the account
        # via /me/assigned_instagram_accounts unless several are shared.
        "ig_user_id": bool(os.environ.get("IG_USER_ID")),
        "li_token": bool(os.environ.get("LI_ACCESS_TOKEN")),
        "ig_token": bool(tok),
        "ig_token_hint": (tok[:4] + "…" + tok[-4:]) if len(tok) > 12 else "",
        "media_base_url": os.environ.get("MEDIA_BASE_URL", ""),
        "ffmpeg": have("ffmpeg"),
        "python": sys.version.split()[0],
    }


def run_job(name: str, argv: list[str], cwd: Path = ROOT):
    """Run a command in the background, streaming its output into JOBS."""
    if JOBS.get(name, {}).get("running"):
        return False
    JOBS[name] = {"running": True, "started": time.time(), "lines": [], "rc": None}

    def worker():
        log(f"{name}: {' '.join(argv)}")
        try:
            p = subprocess.Popen(argv, cwd=str(cwd), stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in p.stdout:
                line = line.rstrip()
                if line:
                    JOBS[name]["lines"].append(line)
                    JOBS[name]["lines"] = JOBS[name]["lines"][-400:]
            rc = p.wait()
            JOBS[name]["rc"] = rc
            log(f"{name} finished rc={rc}", "info" if rc == 0 else "error")
        except Exception as e:
            JOBS[name]["lines"].append(f"ERROR {e}")
            JOBS[name]["rc"] = -1
            log(f"{name} crashed: {e}", "error")
        finally:
            JOBS[name]["running"] = False

    threading.Thread(target=worker, daemon=True).start()
    return True


# ───────────────────────────────────────────────────────────── the API ──
def api_status():
    q = load_queue()
    items = q.get("items", [])
    now = datetime.now(timezone.utc)

    def when(i):
        d = datetime.fromisoformat(i["publish_at"])
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

    counts: dict[str, int] = {}
    for i in items:
        k = f'{i["platform"]}:{i.get("status","?")}'
        counts[k] = counts.get(k, 0) + 1

    due = [i for i in items if i.get("status") == "queued" and when(i) <= now]
    # posts inside the veto window: visible, still stoppable
    in_window = sorted([i for i in items if i.get("status") == "queued" and when(i) > now],
                       key=when)[:12]
    vetoed = [i for i in items if i.get("status") == "vetoed"]
    upcoming = sorted([i for i in items if when(i) > now], key=when)[:12]
    published = [i for i in items if i.get("status") == "published"]
    failed = [i for i in items if i.get("status") == "failed"]

    videos = {p.stem for p in VIDEO.glob("*.mp4")} if VIDEO.exists() else set()
    missing = sorted({Path(i["video"]).stem for i in items
                      if Path(i["video"]).stem not in videos})

    return {
        "now": now.isoformat(timespec="seconds"),
        "total": len(items),
        "counts": counts,
        "due_now": len(due),
        "in_window": in_window,
        "vetoed": len(vetoed),
        "published": len(published),
        "failed": len(failed),
        "videos_rendered": len(videos),
        "videos_missing": missing[:20],
        "videos_missing_n": len(missing),
        "upcoming": upcoming,
        "recent_published": sorted(published, key=when, reverse=True)[:8],
        "failures": failed[:8],
        "env": env_state(),
        "jobs": {k: {"running": v["running"], "rc": v["rc"],
                     "lines": v["lines"][-40:]} for k, v in JOBS.items()},
    }


def api_queue(qs):
    q = load_queue()
    items = q.get("items", [])
    plat = (qs.get("platform") or [None])[0]
    status = (qs.get("status") or [None])[0]
    if plat:
        items = [i for i in items if i["platform"] == plat]
    if status:
        items = [i for i in items if i.get("status") == status]
    return {"items": items[: int((qs.get("limit") or [200])[0])]}


def api_mark(body):
    """Veto a post, un-veto it, or record one as published."""
    iid, status = body.get("id"), body.get("status", "published")
    if status not in ("published", "queued", "vetoed", "failed"):
        return {"error": "bad status"}, 400
    q = load_queue()
    for i in q["items"]:
        if i["id"] == iid:
            i["status"] = status
            if status == "vetoed":
                i["vetoed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                i["veto_reason"] = (body.get("reason") or "")[:300]
            if status == "queued":
                i.pop("vetoed_at", None); i.pop("veto_reason", None)
            if status == "published":
                i.setdefault("result", {})["published_at"] = \
                    datetime.now(timezone.utc).isoformat(timespec="seconds")
                i["result"]["by"] = "marked in control panel"
                if body.get("permalink"):
                    i["result"]["permalink"] = body["permalink"]
            save_queue(q)
            log(f"marked {iid} -> {status}")
            return {"ok": True, "item": i}, 200
    return {"error": "not found"}, 404


ROUTES_POST = {
    "/api/publish":    lambda b: (_publish(b), 200),
    "/api/render":     lambda b: (_render(b), 200),
    "/api/reschedule": lambda b: (_reschedule(), 200),
    "/api/mark":       api_mark,
}


def _publish(b):
    """Both platforms, one button. Each publisher only touches its own rows."""
    dry = bool(b.get("dry_run", True))
    which = b.get("platform") or "both"
    started = []
    for name, script in (("instagram", "publish/instagram.py"),
                         ("linkedin", "publish/linkedin.py")):
        if which not in ("both", name):
            continue
        argv = [sys.executable, script, "--queue", "queue.json"]
        if dry:
            argv.append("--dry-run")
        if run_job(f"publish-{name}", argv):
            started.append(name)
    return {"started": started, "dry_run": dry}


def _render(b):
    argv = [sys.executable, "build_all.py"]
    if b.get("force"):
        argv.append("--force")
    for t in (b.get("topics") or []):
        if re.fullmatch(r"[a-z0-9-]{1,40}", t):
            argv.append(t)
    return {"started": run_job("render", argv)}


def _reschedule():
    return {"started": run_job("reschedule",
                               [sys.executable, "-m", "engine.queue_build"])}


# ──────────────────────────────────────────────────────────── the server ──
class Handler(BaseHTTPRequestHandler):
    server_version = "SoccerTexControl/1.0"

    def log_message(self, *a):
        pass                                    # quiet; we have our own log

    def _send(self, code, payload, ctype="application/json"):
        body = (json.dumps(payload).encode() if ctype == "application/json"
                else payload)
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def do_GET(self):
        u = urlparse(self.path)
        p, qs = u.path, parse_qs(u.query)
        try:
            if p == "/api/status":
                return self._send(200, api_status())
            if p == "/api/queue":
                return self._send(200, api_queue(qs))
            if p == "/api/log":
                return self._send(200, {"lines": tail_log()})
            if p.startswith("/video/"):
                return self._video(p[len("/video/"):])
            return self._static(p)
        except Exception as e:
            log(f"GET {p} failed: {e}", "error")
            traceback.print_exc()
            return self._send(500, {"error": str(e)})

    def do_POST(self):
        u = urlparse(self.path)
        fn = ROUTES_POST.get(u.path)
        if not fn:
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        except Exception:
            return self._send(400, {"error": "bad json"})
        try:
            out = fn(body)
            payload, code = out if isinstance(out, tuple) else (out, 200)
            return self._send(code, payload)
        except Exception as e:
            log(f"POST {u.path} failed: {e}", "error")
            traceback.print_exc()
            return self._send(500, {"error": str(e)})

    # -- static + media -------------------------------------------------
    def _static(self, p):
        name = "dashboard.html" if p in ("/", "") else p.lstrip("/")
        f = (PUBLIC / name).resolve()
        if not str(f).startswith(str(PUBLIC.resolve())) or not f.exists():
            return self._send(404, {"error": "not found"})
        ctype = {".html": "text/html; charset=utf-8", ".js": "text/javascript",
                 ".css": "text/css", ".json": "application/json",
                 ".png": "image/png", ".jpg": "image/jpeg"}.get(f.suffix, "text/plain")
        return self._send(200, f.read_bytes(), ctype)

    def _video(self, name):
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", name):
            return self._send(400, {"error": "bad name"})
        f = (VIDEO / name).resolve()
        if not str(f).startswith(str(VIDEO.resolve())) or not f.exists():
            return self._send(404, {"error": "not found"})
        data = f.read_bytes()
        ctype = "video/mp4" if f.suffix == ".mp4" else "image/jpeg"
        return self._send(200, data, ctype)


def main():
    PUBLIC.mkdir(parents=True, exist_ok=True)
    env = env_state()
    print("\n  SoccerTex Control")
    print(f"  → http://localhost:{PORT}\n")
    print(f"  queue        {'found' if QUEUE.exists() else 'MISSING — run engine.queue_build'}")
    print(f"  videos       {len(list(VIDEO.glob('*.mp4'))) if VIDEO.exists() else 0} rendered")
    print(f"  ffmpeg       {'yes' if env['ffmpeg'] else 'NO — rendering will fail'}")
    print(f"  Instagram    {'configured' if env['ig_token'] and env['ig_user_id'] else 'not configured (publishing disabled)'}")
    if not env["media_base_url"]:
        print("  MEDIA_BASE_URL unset — Instagram fetches media by URL, so publishing needs it")
    print()
    log("control panel started")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
