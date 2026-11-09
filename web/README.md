# The Review Desk — deploying it

A single Cloudflare Worker: it serves the page, reads the live queue and the
workflow runs from GitHub, and writes your decisions straight back into
`queue.json`. A veto here is a commit; the next hourly publish run obeys it.
Nobody has to be in the loop.

## Why Cloudflare and not Render or Railway

| | Free? | Sleeps? |
|---|---|---|
| **Cloudflare Workers** | yes — 100k requests/day | **no** |
| Render | yes — Hobby $0 | yes, after 15 idle minutes, ~1 min to wake |
| Railway | no — $5 one-off trial, then $1–5/month | no |

This is a page plus four small API calls. Workers fits it exactly, costs
nothing, and is the only one of the three with no cold start.

## Deploy

Three secrets and one command.

1. **A GitHub token.** github.com → Settings → Developer settings →
   **Fine-grained personal access tokens** → Generate new token.
   - Repository access: **Only select repositories** → `soccertex-social`
   - Permissions → Repository permissions → **Contents: Read and write**
   - Nothing else. Not your account, not other repos.

   This token can edit one repository. That is the entire blast radius if the
   Worker is ever compromised, and it is why a classic (non fine-grained)
   token is the wrong choice here.

2. **Deploy and set the secrets:**

   ```sh
   cd web
   npx wrangler login              # opens a browser, once
   npx wrangler deploy
   npx wrangler secret put GH_TOKEN
   npx wrangler secret put APP_PASSWORD
   npx wrangler secret put SESSION_SECRET      # any long random string
   ```

   `wrangler` prints the URL. Open it, enter the password, and the desk is live.

   To generate a session secret: `openssl rand -hex 32`

3. **Rotate** by running `wrangler secret put` again with a new value; the old
   one is replaced immediately and existing sessions stop working.

## What it writes

Decisions become fields on the queue entry, committed to `main`:

| Action | Field | Effect on the next publish run |
|---|---|---|
| Don't post this | `status: "vetoed"` | skipped; `status` is not `queued` |
| Trending sound | `manual: true` | skipped; both publishers check this |
| Changes you want | `review_note: "..."` | none — it is a note for the next render |

A post that has already published cannot be vetoed; the API returns 409. Each
write sends the file's SHA, so two people editing at once cannot silently
overwrite each other — the second write fails rather than clobbering.

## Auth

One password, checked against `APP_PASSWORD`, exchanged for a cookie signed
with HMAC-SHA256 over its own expiry. The cookie is `HttpOnly`, `Secure`,
`SameSite=Lax`, and lasts 14 days. A forged or expired cookie is rejected
before any GitHub call is made.

This is deliberately modest: it guards a publishing queue, not money. If more
than one person ever needs the desk, move to Cloudflare Access rather than
sharing the password.
