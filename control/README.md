# SoccerTex Control

The local dashboard. Same shape as ChatNest: one process, no dependencies
beyond the standard library, a web panel on localhost, and the work happening
behind it.

```bash
./start.sh          →  http://localhost:4100
```

## Why local

A page hosted on claude.ai is sandboxed — it cannot reach GitHub, your repo or
the Instagram API, so it can only ever show a snapshot. A page you serve
yourself has none of those limits, so its buttons can actually run things.

That is the whole reason this exists.

## The pages

| Page | Address | What's there |
|---|---|---|
| **Home** | `/` | Where things stand in one line, the two things needed before anything can post (videos made, accounts connected), and the next three posts |
| **Schedule** | `/schedule` | Every planned post, soonest first |
| **Stopped** | `/stopped` | Posts you took off the schedule |
| **Published** | `/published` | Posts that have gone out |
| **Tools** | `/tools` | Publish now, Test run, Remake all videos, and the history |

On Home, Schedule and Stopped:

| Button | What actually happens |
|---|---|
| **Watch** | Plays the video with its caption, so you can judge it before it goes out. If the video hasn't been made yet, it says so |
| **Stop** | Takes a post off the schedule. It never publishes. Reversible — **Put back** returns it |
| **Make videos** | Runs `build_all.py` (only what's missing), then refreshes the schedule so finished videos become "ready". Needs ffmpeg |

On **Tools**:

| Button | What actually happens |
|---|---|
| **Publish now** | Publishes whatever is due to Instagram and LinkedIn, reads each post back to confirm a permalink, writes the result into `queue.json`. Needs a second click within 5 seconds |
| **Test run** | Runs both publishers with `--dry-run`. Lists what *would* post and calls nothing |
| **Remake all videos** | `build_all.py --force` |

The schedule keeps itself filled: each time the panel starts it makes sure the next 30 days
are planned, without moving or dropping anything already there.

Everything is logged to `control/activity.log`, shown on the Tools page under History.

## How posting works

Every post is visible here before its time. Stopping one is the only action, and it is
optional. Posts go out at their time through the GitHub workflow (hourly), or when you
press **Publish now** — this panel does not publish on its own in the background.

## Configuration

Copy `.env.example` to `.env` and fill it in:

```
IG_USER_ID=17841400000000000
IG_ACCESS_TOKEN=IGQ…
LI_ACCESS_TOKEN=AQV…
MEDIA_BASE_URL=https://you.github.io/soccertex-social
```

`start.sh` loads it. Without them the panel still runs — you can make videos, watch
and stop posts — but publishing is off and the page says what's missing.

## This and GitHub are two halves

| | Runs when | Good for |
|---|---|---|
| **This panel** | Your Mac is awake | Control: render, publish on demand, mark done, watch |
| **GitHub Actions** | Always | The unattended daily publish and weekly render |

They share one file, `queue.json`, so neither can drift from the other. Pull
before you start it, push after you've marked things, and the two stay in step.

If you only ever run this panel, nothing posts while your Mac is asleep. If you
only use GitHub, you have no control surface. Most people want both.

## Safety

- Binds to `127.0.0.1` only — not reachable from your network
- Serves files from `control/public/`, `out/video/` and `fonts/` and nowhere else
- The live-publish button arms and disarms within 5 seconds, so a stray click
  cannot post
- No credential is ever written to disk by this panel; it reads them from the
  environment
