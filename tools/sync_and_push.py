#!/usr/bin/env python3
"""Send what is on this Mac to GitHub, without losing what GitHub recorded meanwhile.

Double-click "Push SoccerTex to GitHub.command" in this folder, or run:

    python3 tools/sync_and_push.py

Anything new or changed in the folder is committed first, so an update that
was unzipped here goes up with it.

Why this is not just `git push`: GitHub's copy keeps changing on its own. The
publisher records each post that goes out, the review desk records every
decision, the agents record their work — all as commits to the same branch. A
plain push is refused the moment any of that has happened, and a plain merge
of queue.json (one big JSON file, edited on both sides) produces either a
conflict or, worse, a file that parses and is wrong.

So this merges by meaning instead of by line:
  * a post GitHub says went out, failed, was stopped or was missed stays that
    way — GitHub is the record of what happened;
  * a decision made on the review desk (stop, hold, edited caption) is carried
    onto the matching post here;
  * comments made on the desk are kept, every one;
  * everything else comes from this Mac.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECIDED = ("published", "failed", "vetoed", "missed")
DESK_FIELDS = ("manual", "review_note", "caption_edited", "caption_original",
               "attempts", "last_error")


def git(*a, check=True):
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"\ngit {' '.join(a)} failed:\n{r.stdout}{r.stderr}")
    return r


def show(path):
    r = git("show", f"origin/main:{path}", check=False)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def merge_queue(local: dict, remote: dict) -> dict:
    out = {i["id"]: i for i in local["items"]}
    waiting = [i["publish_at"] for i in local["items"] if i.get("status") in ("queued", "blocked")]
    first = min(waiting) if waiting else None
    for r in remote.get("items", []):
        l = out.get(r["id"])
        if l is None:
            # Only GitHub has it: history, or a post from before this Mac's
            # schedule begins that is still due to go out.
            if r.get("status") in DECIDED or first is None or r["publish_at"] < first:
                out[r["id"]] = r
        elif r.get("status") in DECIDED:
            out[r["id"]] = r                      # GitHub is the record of what happened
        elif l.get("status") not in DECIDED:
            for k in DESK_FIELDS:                 # both still waiting: desk decisions win
                if k in r:
                    l[k] = r[k]
            if r.get("caption_edited"):
                l["caption"] = r["caption"]
    merged = dict(local)
    merged["items"] = sorted(out.values(), key=lambda i: (i["publish_at"], i["platform"]))
    return merged


def merge_feedback(local: dict | None, remote: dict | None) -> dict:
    threads = {t["id"]: t for t in (local or {}).get("threads", [])}
    for t in (remote or {}).get("threads", []):
        threads[t["id"]] = t                      # the desk and the agents write on GitHub
    return {"version": 1, "threads": sorted(threads.values(), key=lambda t: t.get("created_at", ""))}


def write(path, data):
    (ROOT / path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main() -> int:
    # Work that arrived as files (an update unzipped into this folder) is saved
    # as a commit first. The update can bring its own description of what it
    # is in .commit-message; that file is used once and removed.
    note = ROOT / ".commit-message"
    message = "Changes made on this Mac"
    if note.exists():
        message = note.read_text().strip() or message
        note.unlink()
    dirty = git("status", "--porcelain").stdout.strip()
    if dirty:
        print(f"Saving {len(dirty.splitlines())} new or changed file(s) from this Mac…")
        git("add", "-A")
        git("commit", "-q", "-m", message)

    for attempt in range(1, 4):
        print(f"Checking what GitHub has… (try {attempt})")
        git("fetch", "-q", "origin")
        ahead = int(git("rev-list", "--count", "origin/main..HEAD").stdout or 0)
        behind = int(git("rev-list", "--count", "HEAD..origin/main").stdout or 0)
        if not ahead and not behind:
            print("Nothing to send — GitHub already has everything."); return 0

        if behind:
            print(f"GitHub recorded {behind} change(s) since this Mac last looked. Merging them in…")
            lq = json.loads((ROOT / "queue.json").read_text())
            lf = json.loads((ROOT / "feedback.json").read_text()) if (ROOT / "feedback.json").exists() else None
            rq, rf = show("queue.json"), show("feedback.json")
            mr = git("merge", "--no-commit", "--no-ff", "-X", "ours", "origin/main", check=False)
            if git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode:
                print("Git would not start the merge:\n" + (mr.stderr or mr.stdout).strip() +
                      "\nNothing was sent. Tell Claude."); return 1
            if rq:
                write("queue.json", merge_queue(lq, rq))
            write("feedback.json", merge_feedback(lf, rf))
            # files only GitHub's robots write: theirs, as they are
            for p in ("agents/status.json", "out/desk/preflight.txt"):
                if git("cat-file", "-e", f"origin/main:{p}", check=False).returncode == 0:
                    git("checkout", "origin/main", "--", p)
            mine = [f for f in ("queue.json", "feedback.json", "agents/status.json",
                                "out/desk/preflight.txt") if (ROOT / f).exists()]
            git("add", "-A", *mine)
            left = git("diff", "--name-only", "--diff-filter=U").stdout.strip()
            if left:
                git("merge", "--abort", check=False)
                print("Could not merge these by themselves:\n" + left + "\nNothing was sent. Tell Claude."); return 1
            git("commit", "-q", "-m", "Merge what GitHub recorded while this Mac was working\n\n"
                "Posts that went out, desk decisions and comments are kept from GitHub;\n"
                "everything else from this Mac.")

        print("Sending to GitHub… (videos are large; this can take a few minutes)")
        r = git("push", "origin", "HEAD:main", check=False)
        if r.returncode == 0:
            print("\nSent. GitHub now has everything."
                  "\nThe review desk updates itself within a minute; new videos are online in about five.")
            return 0
        if "rejected" not in r.stderr and "fetch first" not in r.stderr:
            print("\nGitHub refused the push:\n" + r.stderr.strip()); return 1
        print("GitHub changed again while sending. Going round once more…")
    print("\nGitHub kept changing. Wait a minute and run this again."); return 1


if __name__ == "__main__":
    sys.exit(main())
