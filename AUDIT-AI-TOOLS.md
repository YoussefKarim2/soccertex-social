# Free AI tooling audit — November 2026

Why the content is code-rendered rather than AI-generated. Every row was read on the
provider's own page; anything I could not confirm is marked UNCERTAIN.

---

## AI video generation — nothing here survives

**There is no AI video generation API with a renewing free tier. Not one.**

| Provider | Free tier | API on free | Commercial use | Verdict |
|---|---|---|---|---|
| **Google Veo** 3.1 / 3 / 2 | **"Not available"** | — | — | Paid tier only. [pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| **OpenAI Sora 2** | **"Not supported"** | **API shut down 24 Sep 2026** | — | Gone. [docs](https://developers.openai.com/api/docs/models/sora-2) |
| **Runway** | 125 credits, **one-time** | No — separate paid product | Not stated | *"do not renew or refresh once spent"*; watermarked |
| **Pika** | **0 monthly credits** | Top-ups *"can't be used with the API"* | **"Not included: Commercial license"** | Disqualified twice |
| **Luma** | No stated allowance | — | Only *"during an active Subscription Term"* | Disqualified |
| **LTX Studio** | 800 credits, **one-time** | No | *"For personal projects only. Cannot be used for business, marketing, or paid work"* | Disqualified |
| **Kling** | Purchase-based | No free credits documented | — | Web-UI only for free use |
| **Hailuo / MiniMax** | — | — | — | UNCERTAIN (site blocks fetching) |
| **Haiper** | Appears defunct | — | — | UNCERTAIN |

A "free plan" with one-time non-renewing credits is a trial wearing a different label.

## Self-hosting open models — fails on hardware first

| Model | Licence | Commercial? | VRAM needed |
|---|---|---|---|
| **Wan 2.2 TI2V-5B** | Apache 2.0 | **Yes** | **24 GB** |
| Wan 2.2 T2V-A14B | Apache 2.0 | Yes | 80 GB |
| LTX-Video 0.9.x | LTXV Open Weights | Yes, under $10M revenue | — |
| LTX-Video 2B **v0.9–0.9.5** | per-version | **NO — research only** | — |
| Mochi-1 | Apache 2.0 | Yes | 22–60 GB |
| HunyuanVideo | Tencent community | Yes, **but not in EU / UK / South Korea** | 45–80 GB |
| CogVideoX-5b | unverified | UNCERTAIN | 4.4 GB |
| SVD-XT | Stability Community | Yes, under $1M revenue | — |

**Free compute available:** Colab and Kaggle give **16 GB**. HuggingFace ZeroGPU gives a
free account **5 minutes of GPU per day**.

The best commercially-licensed open model needs 24 GB. The gap isn't closeable with
offloading the repo doesn't ship. The one model that fits 16 GB — CogVideoX-5b — outputs
**720×480 at 8 fps**, which reads as broken rather than stylised.

And **Colab's AUP prohibits the access pattern itself** on free runtimes:
*"bypassing the notebook UI,"* *"running distributed computing workers,"* and
*"using multiple accounts to work around... resource usage restrictions."* Terminable
without warning.

Two traps worth naming: **older LTX-Video weights are research-only** (*"explicitly excludes
commercialization"*) — a tutorial pointing at an old checkpoint inherits that licence. And
**HunyuanVideo is geofenced out of the EU and UK**, which matters for a company selling into
Europe.

---

## What does work, sustainably, forever

| Layer | Tool | Licence | Free capacity | Our need |
|---|---|---|---|---|
| **Video** | **ffmpeg + this engine** | LGPL / ours | unbounded | 10/wk |
| **Stills** | **Cloudflare Workers AI** — FLUX.1-schnell, FLUX.2-klein-4B | **Apache 2.0** | **10,000 neurons/day**, resets 00:00 UTC ≈ 230–380 images | ~3/day |
| **Stock video/photo** | **Pexels** API | Pexels licence | 200/hr, 20,000/mo | ~40/mo |
| | **Pixabay** API | Pixabay licence | 100/60s, **must cache 24h** | — |
| | **Coverr** Demo API | Coverr licence | 50/hr, **must credit on free tier** | — |
| **Voiceover** | **Kokoro-82M** | **Apache 2.0**, runs locally on CPU | unbounded | 10/wk |
| **Music / SFX** | Coverr + Freesound **CC0 only** | varies per sound | 2,000/day | 10/wk |

**Cloudflare Workers AI is the one genuine find.** 10,000 neurons/day resetting at midnight
UTC, Apache 2.0 models, outputs you own, no training on your content, a real REST API, and
no prohibition on programmatic use. Roughly **75× our requirement**.
UNCERTAIN: whether account creation needs a card — verify at signup.

**Kokoro over Piper for voiceover.** Both are local and free, but Piper's own docs say it
*"is intended for personal use and text to speech research only"* and warn that individual
voices carry their own licences. Kokoro is Apache 2.0 throughout and its card notes
deployment in *"commercial APIs"*.

**Avoid edge-tts and gTTS.** Both call undocumented Microsoft/Google endpoints from outside
the products they belong to, with no licence granting commercial use. Fine for a hobby
script; not something to build a business on.

---

## Two things that got worse recently

**HuggingFace Inference API no longer has a free allowance.** The pricing page now reads
**"Free Users — Monthly Credits: None."** If you remember a small free monthly inference
quota, it's gone.

**Pollinations.ai is no longer a free keyless API.** It runs on paid "Pollen" at $1 each and
requires a key; free credit comes only from one-off GitHub quests.

---

## Licence conditions the code has to honour

These are access conditions, not courtesies — breaching them revokes the key, and a revoked
key is how a "$0 forever" pipeline silently dies.

- **Pexels:** *"Whenever you make an API request, you must show a prominent link to Pexels."*
  Licence prohibits implying that people or brands endorse your product.
- **Pixabay:** cache results 24h; **no permanent hotlinking**; *"the API is for real human
  requests... systematic mass downloads are prohibited."* Cannot use content containing
  recognisable third-party trademarks commercially — and sportswear b-roll is full of them.
- **Coverr:** free Demo API tier **requires crediting Coverr and the creator**, and calling
  `PATCH /videos/:id/stats/downloads` on use.
- **Freesound:** filter to **CC0 only**. CC-BY-NC is unusable commercially.

---

## The verdict

Four independent walls stand between a free AI video generator and a weekly publishing
cadence: no free API, no commercial licence, insufficient VRAM, and terms that prohibit the
access pattern. An autonomous system must clear all four every week, indefinitely.

**ffmpeg clears all four permanently**, because it runs on hardware we already have under a
licence with no ceiling. Five videos rendered in 89 seconds. That number is the same next
year.

AI video belongs in this system as an occasional flourish a human triggers, never on the
critical path.
