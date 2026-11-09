# SoccerTex Content Engine

Writes, renders, schedules and publishes SoccerTex's social content.
Markets: USA and Europe. Cost: **$0**, with nothing that expires.

**Start with [`SETUP.md`](SETUP.md).** Then [`PUBLISHING-REALITY.md`](PUBLISHING-REALITY.md),
which is the honest ceiling on how autonomous this can be.

---

## What it does

```
engine/bank.py      30 topics, as data
      ↓
engine/compose.py   each topic → two cuts (social ~15s, business ~20s)
      ↓
engine/render.py    PIL frames → ffmpeg          out/video/*.mp4
engine/motion.py      animated machines
engine/footage.py     real licensed clips
engine/audio.py       synthesised soundtrack
      ↓
engine/queue_build.py   rolling 30-day schedule   queue.json
      ↓
publish/instagram.py    Graph API, verified       Instagram
```

**30 topics × 3 platforms = 90 posts a month**, one per platform per day, with no topic
repeating on the same platform inside the cycle. The three platforms run through the bank at
different offsets, so no two posts on the same day share a topic.

TikTok and Instagram share the *social* cut but carry different captions, and TikTok gets a
trending sound added in the app. LinkedIn gets the *business* cut: slower, more text, fewer
hashtags.

---

## Running it

```bash
pip install pillow numpy          # ffmpeg must be on PATH

python3 build_all.py              # render anything missing (idempotent)
python3 build_all.py --force      # re-render everything
python3 build_all.py gsm seams    # just those topics
python3 -m engine.queue_build     # roll the schedule forward, make Reel covers
python3 -m engine.bank            # validate the bank
python3 publish/instagram.py --dry-run
./make_proxies.sh                 # rebuild 9:16 proxies from new footage
```

`build_all.py` only re-renders when a source file is newer than the output, so the weekly
GitHub run normally costs about a minute.

---

## Adding a topic

One dict in `engine/bank.py`:

```python
T(id="pilling", pillar="2 Kit School", kind="list", footage=STITCH,
  hook="RUB IT TWENTY TIMES", sub="If it fuzzes, walk away.",
  overlay=("THE PILLING TEST", "Two seconds, no equipment."),
  items=["Rub the fabric against itself twenty times",
         "Fuzz balls mean short staple fibres",
         "Ask for a Martindale figure if the quote is serious"],
  caption="…",
  tags="#fabric #cutandsew #teamwear", li_tags="#sourcing"),
```

Then `python3 build_all.py && python3 -m engine.queue_build`. Both cuts render, the scheduler
picks it up, and GitHub publishes it. No other code changes.

`kind` decides the scene sequence:

| kind | Sequence |
|---|---|
| `list` | hook → footage → numbered list → CTA |
| `stat` | hook → big number → footage → list → CTA |
| `compare` | hook → footage → number → A-vs-B → CTA |
| `process` | hook → machine → list → CTA |

---

## Scenes

| Scene | For |
|---|---|
| `PunchScene` | Word-by-word type that lands with a shake. The first 2 seconds |
| `StatScene` | One number counting up |
| `ListScene` | Numbered points arriving one at a time. The workhorse |
| `CompareScene` | A vs B — the best-performing teamwear format in the benchmark set |
| `FootageScene` | Real video, cropped to 9:16, graded, with overlay |
| `SewingScene` `CutScene` `PressScene` `EmbroideryScene` | Drawn machines, for what no clip covers |
| `CTAScene` | Brand close. Identical every time, which is the point |

Layout is measured before anything is drawn, so wrapped text cannot collide and type shrinks
to fit instead of overflowing.

---

## Footage

Two pools that never mix — see `assets/footage/README.md`.

- `own/` — filmed at SoccerTex. May say "our floor".
- `stock/` — licensed from Pexels. **May not.** `FootageScene(source="stock")` raises
  `StockMisuse` before rendering if the overlay contains first-person factory language, and
  stamps "Library footage · not SoccerTex's floor" on the frame.

Partly licence (Pexels prohibits implying endorsement), mostly because buyers vetting a
supplier specifically check whether factory video is real. Stock dressed up as your own floor
would cost more trust than it buys attention.

**Twenty minutes of real phone footage would change every video in the library.** Drop the
clips in `own/`, run `./make_proxies.sh`, and point topics at them.

---

## Audio

`engine/audio.py` synthesises the soundtrack — kick, bass, hats and a plucked line in A minor
at 124bpm, with a whoosh and an impact on every cut. Generated rather than licensed, so
nobody owns it but you.

It sits deliberately low. On TikTok you push it to ~20% and a trending sound to ~80%; the
whooshes still land on the cuts. See `TRENDING-SOUNDS.md`.

---

## Rules the code enforces

1. Every claim traces to the Verified Facts Register — no certification claim, no MOQ figure,
   no US duty claim, no named customer.
2. Stock and own footage stay separate, enforced at render time.
3. Nothing is reported as published until read back from the API with a permalink.
4. No simulated factory footage presented as real.
5. $0 — no subscription, trial, paid API or credits.

---

## Known limits

- **TikTok cannot be published by API.** Policy exclusion, not pricing. ~2 min/day.
- **LinkedIn Company Pages** need Community Management API approval. Use the native
  scheduler, ~15 min/month.
- **No photoreal AI video.** No free generator clears licence, API access and quota at once —
  see `AUDIT-AI-TOOLS.md`. Code-rendered motion plus licensed clips is what survives.
- **Trending sounds must be added in-app.** Platform licensing, not a tooling gap.
