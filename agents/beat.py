#!/usr/bin/env python3
"""An agent's heartbeat: say what you are doing, where the review desk can see it.

    python3 agents/beat.py video-editor working "Re-rendering gsm (Instagram cut)"
    python3 agents/beat.py video-editor log     "picked up 2 comments"
    python3 agents/beat.py video-editor idle    "Changed 1 video, asked 1 question"
    python3 agents/beat.py video-editor blocked "ffmpeg would not install"

Each call updates agents/status.json, commits it as `agent(<id>): <text>` and
pushes. The desk's Agents tab reads that file every 15 seconds, and the commit
itself shows in its change feed — so a beat is the difference between "working"
and "nobody knows". Beat at the start, at every step worth a line, and at the
end. An agent that says "working" and then goes quiet for an hour is shown as
stopped, whatever the file says.

`--no-push` writes the file only (for a beat that rides along with other
changes in the agent's next commit).
"""
from __future__ import annotations
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "agents" / "status.json"
STATES = ("working", "idle", "blocked", "log")
KEEP_LOG = 200


def git(*a, check=True):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=check)


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--no-push"]
    push = "--no-push" not in sys.argv
    if len(args) != 3 or args[1] not in STATES:
        print(__doc__); return 2
    agent, state, text = args
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    data = json.loads(FILE.read_text()) if FILE.exists() else {}
    data.setdefault("agents", {}); data.setdefault("log", [])
    me = data["agents"].setdefault(agent, {})
    if state == "working":
        if me.get("state") != "working":
            me["started_at"] = now
        me.update(state="working", step=text)
    elif state == "idle":
        me.update(state="idle", last_result=text); me.pop("step", None)
    elif state == "blocked":
        me.update(state="blocked", last_result=text); me.pop("step", None)
    me["updated_at"] = now
    data["log"] = (data["log"] + [{"t": now, "agent": agent, "text": text}])[-KEEP_LOG:]
    FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    if not push:
        return 0

    git("add", "agents/status.json")
    if git("diff", "--staged", "--quiet", check=False).returncode == 0:
        return 0
    git("commit", "-q", "-m", f"agent({agent}): {text}")
    # the publisher, the desk and other agents all commit to main: rebase and retry
    for _ in range(4):
        if git("push", "-q", "origin", "HEAD:main", check=False).returncode == 0:
            return 0
        git("pull", "-q", "--rebase", "--autostash", "origin", "main", check=False)
    print("beat: could not push after 4 tries", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
