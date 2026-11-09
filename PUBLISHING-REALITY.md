# What can and cannot publish without you

Researched against official platform documentation, 6 November 2026. Read this before
anything else, because it defines the ceiling on "fully autonomous".

---

## The short version

| Platform | Autonomous? | Why |
|---|---|---|
| **Instagram** | ✅ **Yes, fully** | Graph API publishes Reels, images and carousels at Standard Access with **no App Review** for an app used only on a business you own |
| **LinkedIn Page** | ⚠️ **Not yet** | Needs Community Management API approval — a real process, free, but weeks of work with terminal rejection risk |
| **TikTok** | ❌ **No. Not at any price** | Policy exclusion, not a pricing one |

**4 of 10 posts in the first queue publish with nobody present. That is 40%, and Instagram
is the whole of it.**

---

## TikTok: the one genuine dead end

TikTok's Content Posting API is free. But unaudited clients are hard-limited — from
[TikTok's Content Sharing Guidelines](https://developers.tiktok.com/docs/en/content-sharing-guidelines):

> *"All content posted by unaudited clients will be restricted to private viewing mode."*

Only `SELF_ONLY` visibility, and the posting account itself must be set to private. To lift
that you need an audit. The same page says eligible clients:

> *"must not be limited to test applications and should be intended for a wide audience"*

and explicitly excludes:

> *"internal utilities for posting to accounts your team manages."*

**A business building an app to post to its own TikTok account is, in writing, ineligible.**
No amount of money changes this. Self-hosting doesn't either — Postiz's own documentation
confirms it forces `SELF_ONLY` regardless of what you select.

The only legitimate route is a third-party tool whose own TikTok app is already audited
(Buffer's is). That tool still needs a human to drop the video in, or a paid API plan that
Buffer's free tier doesn't include.

**Practical consequence: TikTok videos are rendered, captioned and queued automatically, and
a person uploads them.** Roughly 10 minutes a week for three videos. If that's still too
much, the honest options are to drop TikTok or to revisit a paid scheduler.

---

## LinkedIn: possible, but it's a project

Posting to a **Company Page** requires the
[Community Management API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management-app-review).
It is free of charge, and SoccerTex is eligible (registered company, real website, business
email). But:

- Two tiers. **Development** is granted on use case and Page verification. **Standard**
  additionally requires a *completed integration*, test credentials, and a **single-take
  narrated screen recording** demonstrating every use case.
- **Rejection is terminal for that app.** You create a brand-new app and restart.

The self-serve alternative, `w_member_social`, posts only to a **person's profile**, never a
Company Page.

**Recommendation: use LinkedIn's own free scheduler** — Page posts can be scheduled from 1
hour to 3 months ahead. The content is generated and queued here; a person pastes a month of
it into LinkedIn's scheduler in one sitting, roughly 15 minutes monthly. Pursue the
Community Management API later, once the account has a track record worth the application.

---

## Instagram: this one genuinely works

From [Meta's App Review page](https://developers.facebook.com/documentation/instagram-platform/app-review):
an app used *"only for a business I own or manage"* runs at **Standard Access** and does
**not require App Review**. Content publishing works at Standard Access. Business
Verification is only needed for Advanced Access, i.e. serving accounts you don't own.

No fee is documented anywhere for Instagram organic content publishing.

**Two constraints that shaped the build:**

1. **Instagram fetches the media itself from a public URL.** It will not accept an upload.
   So every video must already be served over public HTTPS before the API is called. That's
   why this repo publishes `out/` to GitHub Pages — free, and the URL is stable.
2. **The API route changed under us, mid-build.** Meta's migration guide (updated 1 Oct 2026)
   states: *"Newly created apps can't set up the Instagram API with Instagram Login."* The
   original design — `graph.instagram.com`, `instagram_business_*` scopes, an Instagram User
   token refreshed every 60 days — is still valid for apps created before the cutoff, and
   closed to ours. The publisher now uses **Unified Login**: host `graph.facebook.com`,
   scopes `instagram_basic` + `instagram_content_publish`, account id from
   `/me/assigned_instagram_accounts`, and a Business Integration System User Access Token
   whose expiry depends on the configuration. There is no refresh call, so there is no
   refresh job — `token-health.yml` checks weekly that the token still works instead.
   The cost of the change was one file; the publish sequence and all 60 rendered videos were
   unaffected. The requirement it added is that the app must be owned by a business
   portfolio, which is free.

**Limits:** 50 published posts per rolling 24h (Meta's own docs say 50 in the reference and
100 in the guide — the publisher asks the API at runtime rather than trusting either),
400 containers per 24h, captions ≤2,200 characters, ≤30 hashtags. Reels: 3s–15min, ≤300MB,
9:16, H.264/HEVC, AAC audio. Our videos are ~20s and under 1MB.

**What the API cannot do, ever:** attach Instagram's licensed music, use effects or Topics,
add product tags, or post Stories with interactive stickers. Our videos carry no licensed
audio by design, so this costs us nothing.

---

## Why the content is code-rendered and not AI-generated video

A full audit is in `AUDIT-AI-TOOLS.md`. The conclusion in one table — every free AI video
tier fails on at least one disqualifying axis:

| Provider | What kills it |
|---|---|
| Google Veo | **No free tier.** Pricing page reads "Not available" |
| OpenAI Sora | **API shut down 24 Sept 2026.** Free tier "Not supported" |
| Runway | 125 credits **one-time**, *"do not renew or refresh once spent"*; watermarked |
| Pika | **0 monthly credits**; *"Not included: Commercial license"*; top-ups *"can't be used with the API"* |
| Luma | Commercial use only *"during an active Subscription Term"* |
| LTX Studio | 800 credits **one-time**; *"For personal projects only. Cannot be used for business, marketing, or paid work"* |
| Self-host on free GPU | Best commercially-licensed open model (Wan 2.2 TI2V-5B, Apache 2.0) needs **24GB VRAM**; Colab and Kaggle free give **16GB**. HuggingFace ZeroGPU gives a free account **5 minutes of GPU per day** |
| Google Colab | Its AUP prohibits *"bypassing the notebook UI"* and *"running distributed computing workers"* on free runtimes — the exact pattern an autonomous system needs |

Four independent walls: no free API, no commercial licence, insufficient VRAM, prohibited by
terms. An autonomous system has to clear all four every week, forever.

**ffmpeg plus a frame renderer clears all four permanently.** No quota, no account, no
licence ceiling, no credits to run out. Five videos rendered in 89 seconds on this machine.
That number doesn't change next month.

**What this trades away, honestly:** no photoreal factory footage. The videos are motion
graphics — typography, numbers, comparisons, process diagrams. For the Kit School and
Sourcing Math pillars, which are the two that reach buyers on LinkedIn, that's the right
form anyway. For "Inside the Floor" it isn't, and no amount of AI fixes that — a generated
sewing line would be a fabrication of your factory, which you told me never to do and which
I won't.

**The upgrade path costs you 3 hours, once:** 20 minutes of phone footage of the real floor
turns every one of these videos from a motion graphic into a motion graphic cut with real
production footage. The engine already supports it — drop clips into `assets/footage/` and
they get used. That is the single highest-return thing you could do for this account, and
it is a one-off, not an ongoing commitment.

---

## What is genuinely free and sustainable, forever

| Layer | Tool | Free capacity | Our need | Headroom |
|---|---|---|---|---|
| Video rendering | **ffmpeg + this engine** | unbounded | 10/wk | ∞ |
| Generated stills | **Cloudflare Workers AI, FLUX.1-schnell** (Apache 2.0) | ~230/day, resets 00:00 UTC | ~3/day | ~75× |
| Licensed b-roll | **Pexels** API | 200/hr, 20,000/mo | ~40/mo | ~500× |
| Voiceover | **Kokoro-82M** (Apache 2.0, runs locally) | unbounded | 10/wk | ∞ |
| Publishing | **GitHub Actions** | 2,000 min/mo private, unlimited public | ~60 min/mo | large |
| Media hosting | **GitHub Pages** | free | — | — |

Nothing in that column is a trial. Nothing expires. Nothing needs a card.

**One rule the renderer enforces, not just documents:** licensed stock and SoccerTex-owned
media live in separate pools, and any caption template saying "our factory", "our team" or
"our floor" can only draw from the owned pool. Pexels' licence prohibits implying
endorsement; Pixabay's prohibits misleading use. Presenting someone else's sewing floor as
yours would breach both, independently of advertising law.
