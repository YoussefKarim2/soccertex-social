# Setup — the one-time work

You chose **"let GitHub do everything"**: you hold every credential, I hold none, and the
repo renders and posts on its own.

Cadence is **daily on Instagram and LinkedIn** — 14 posts a week, 60 a month, drawn from a
bank of 30 topics so nothing repeats on the same platform inside a month.

**About 45 minutes, once.** Nothing below needs a payment card.

---

## What runs by itself afterwards

| | Who | Time |
|---|---|---|
| Writing, rendering, scheduling | GitHub, weekly | none |
| **Instagram — 7 posts/week** | **Automatic** | **none** |
| **LinkedIn — 7 posts/week** | **Automatic** | **none** |
| Vetoing anything you don't want out | You, in the dashboard | only when you want to |

TikTok was dropped deliberately. Their Content Posting API excludes internal utilities that
post to accounts your own team manages, and trending sounds can only be attached inside the
app — so TikTok could never be anything but manual daily work. The brief was zero
involvement, so TikTok is out rather than pretending otherwise.

---

## Step 1 · Check your Instagram account type

The API cannot touch a personal account. Open Instagram → Settings → Account type →
**Switch to professional → Business**. If you already did, skip this.

---

## Step 2 · The Meta app (~15 min, free, no review)

> **Why this isn't the older instructions.** Meta's migration guide says plainly:
> *"Newly created apps can't set up the Instagram API with Instagram Login."* That was the
> `graph.instagram.com` route with `instagram_business_*` scopes and a 60-day refresh. An app
> created now gets two choices instead — **Unified Login** (recommended, the only one still
> getting features) and **Facebook Login** (legacy, requires wiring Instagram to a Facebook
> Page). We use Unified Login, which needs no Facebook Page at all.

1. **developers.facebook.com** → My Apps → **Create App**
2. Use case: **Manage messaging & content on Instagram**. Business portfolio: you can skip it
   here, but see the next step.
3. **Create a business portfolio** at **business.facebook.com** and connect the app to it.
   This is not optional: the *API setup with Unified login* tab only appears for an app owned
   by a business portfolio. It is free and takes about two minutes.
4. App Dashboard → **Use cases → Manage messaging & content on Instagram → Customize →
   API setup with Unified login**
5. **Create new configuration.** Keep `instagram_basic` and add `instagram_content_publish`;
   drop the messaging and ads permissions unless you want them. Then **Use this configuration**.
6. Under **Redirect URL**, put your GitHub Pages URL. Nothing is served there for this —
   Meta just requires the field — because step 8 generates the token in the dashboard.
7. **Add account** → invite your Instagram professional account as an **Instagram Tester**,
   then accept it at instagram.com → Settings → Website permissions → Apps and websites →
   **Tester invites**.
8. **Generate token**, complete the login, and copy it. **It is shown only once.**
9. The account ID is discovered automatically from the token, so you don't need to find it.
   Set `IG_USER_ID` only if more than one Instagram account is shared with the app.

> Do **not** request Advanced Access and do **not** submit for App Review. Meta's own
> migration guide: *"When you save your configuration... your app gets Standard Access to its
> permissions, which is enough to test with people who have a role on your app."* You hold a
> role on the app and own the account. Advanced Access exists for onboarding *other people's*
> accounts, and review would only add weeks.

**Keep the token out of this chat.** It goes straight into GitHub in step 3.

---

## Step 3 · The repository (~20 min)

1. Create a **private** GitHub repo, e.g. `soccertex-social`
2. Upload this folder to it — drag the files into GitHub's web uploader, or
   `git init && git add -A && git commit -m "initial" && git remote add origin <url> && git push -u origin main`
3. **Settings → Pages** → Source: **GitHub Actions**. Note the URL it gives you.
   This serves `out/` publicly so Instagram can fetch the videos — Instagram pulls media from
   a URL rather than accepting an upload, so this is required, not optional. Only finished
   marketing content lives there.
4. **Settings → Secrets and variables → Actions**

   | Type | Name | Value |
   |---|---|---|
   | Secret | `IG_ACCESS_TOKEN` | the token from step 2 |
   | Secret | `IG_USER_ID` | *optional* — only if several Instagram accounts are shared with the app |
   | Secret | `LI_ACCESS_TOKEN` | the LinkedIn member token |
   | Secret | `LI_AUTHOR_URN` | *optional* — fetched from `/v2/userinfo` if blank |
   | Variable | `MEDIA_BASE_URL` | your Pages URL, no trailing slash |

   No `REPO_PAT` any more. It existed so the old workflow could rotate the Instagram token
   into the secrets store every 25 days; Unified Login has no refresh call, so nothing
   writes secrets and nothing needs that permission.

5. **Settings → Actions → General** → Workflow permissions → **Read and write**.
   Without this the workflows cannot commit rendered videos back.

---

## Step 4 · Prove it before it goes live

**Actions → Publish due posts → Run workflow**, leave `dry_run` **true**.

It reports what *would* publish and calls nothing. That's your proof the wiring works.

Then run it again with `dry_run` **false**. It publishes anything due, reads the post back
from the API to confirm a permalink exists, and records the result in `queue.json`.

Nothing is ever reported as published unless that read-back succeeded.

---

## What happens from then on

| Workflow | When | What |
|---|---|---|
| `render.yml` | Sundays 03:00 UTC | Renders any missing video, rolls the schedule 30 days forward, commits |
| `publish.yml` | Hourly | Publishes anything due to Instagram and LinkedIn, verifies each one, records the permalink |
| `token-health.yml` | Mondays 07:00 UTC | Checks both tokens still work and fails loudly if not |
| `pages.yml` | On any change to `out/` | Redeploys the media so Instagram can fetch it |

**You never need to touch it.** The queue rolls forward automatically, so it cannot run dry.

---

## Your daily nothing

There is no daily task. Both platforms publish on their own.

What you *can* do, whenever you feel like it, is open the control panel (`./start.sh`, then
127.0.0.1:4100) and look at **Going out** — everything due in the next 24 hours, with the
video playable inline. If you don't want one of them to go, hit **Veto** and it stops. Vetoed
posts sit in their own panel and rejoin the schedule if you put one back.

Silence from you means everything ships. That was the point.

---

## Adding new topics later

The content bank is `engine/bank.py` — 30 entries, each one a dict. Adding a topic is adding
a dict; the composer turns it into both cuts and the scheduler picks it up on the next run.

You can write one yourself by copying an existing entry, or ask me and I'll send you the
block to paste in. Either way the repo keeps running without me having any access to it.

---

## If something stops

- **Nothing publishing?** Actions tab → check `publish.yml` runs. The commonest cause is
  `MEDIA_BASE_URL` unset or Pages not enabled, so Instagram cannot fetch the video.
- **Token stopped working?** `token-health.yml` runs every Monday and fails loudly if either
  token is dead. Under Unified Login a token also dies if the Instagram account is removed
  from the business portfolio or moved to a different one — in that case reconnect and
  generate a new token from step 2, then update `IG_ACCESS_TOKEN`. You can check any time
  with `python3 publish/instagram.py --check-token`.
- **A post marked `failed`?** `queue.json` records the error on the entry. Three retries,
  then it stops and waits for you.
