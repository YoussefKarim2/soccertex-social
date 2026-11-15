# Video playbook — what makes a SoccerTex reel better, and in what order

Written 14 Nov 2026 from two things: what the platforms themselves say ranks a
video, and a frame-by-frame look at the 60 videos in `out/video/`. Every rule
below says where it comes from. Rules marked **measured** were checked against
our own files; rules marked **platform** come from the platform or its head;
rules marked **industry** come from third-party studies and are weaker.

## What the platform rewards

| Signal | Source | What it means for a cut |
|---|---|---|
| Watch time, likes and **sends** are the three ranking signals; sends per reach is what reaches non-followers | Adam Mosseri, head of Instagram (Jan 2025; repeated Oct 2026, "a lot more" weight on sends than comments) — **platform** | End on a reason to forward it. Make one idea per reel that a kit manager would send to a colleague. |
| Original content is favoured; accounts that mostly repost lose recommendation | Instagram, 2026 — **platform** | Four stock clips recycled across 60 videos is the opposite of original. Own footage is the biggest lever we have. |
| Keep the top 14%, bottom 35% and 6% each side clear of text | Meta's Reels safe-zone guidance — **platform** | Captions at 60% height are safe. Anything below 65% is under the app's own caption. |
| The steepest drop is in the first 3 seconds | retention studies — **industry** | Motion and the promise both on screen at frame 0. |
| A picture that moves holds better than a title card | VidMob, reported second-hand — **industry**, treat as a lean not a law | Hook goes over footage, not on a flat colour. |

Not adopted: "longer reels reach more" (Buffer, 2.7M reels: 90s+ reached 4–7%
above an account's own average). The effect is small, and a 20-second reel
that is watched to the end beats a 90-second one that is not.

## Seven formats, not one (15 Nov)

Youssef, 15 Nov: "all the videos are the same but only the words are
different." It was structural: thirty topics, two templates, four clips.
Each topic now has a format with its own picture, palette, type, motion and
soundtrack (`engine/vibes.py`, assigned in `build_vibes.py`):

| Format | Look | Sound | Topics |
|---|---|---|---|
| chat | a message thread, dark | calm, 96 bpm | price-drivers, small-orders, buyer-questions, sublimation-limits, goalkeeper |
| poster | giant type on flat colour, hard cuts | drums only, 134 | lead-time, europe-duty, trading-company, recovery-test, sewing-line |
| notebook | paper checklist, ticks, highlighter | calm, 100 | season-calendar, tech-pack, fabric-glossary, factory-questions, nameset, packing |
| versus | red column against green | driving, 118 | wrong-supplier, shrinkage, reorder |
| blueprint | line drawings on a drafting grid | calm, 108 | pem-cumulation, decoration, seams, quality, kit-decisions |
| doc | black-and-white footage, one amber word | slow drums, 90 | cutting, embroidery |
| cuts | fast captions over footage | driving, 126 | gsm, cheap-vs-good, white-kit, heat-press |

Two rules, both enforced by `check_spread()`:

- Instagram posts topic *i* and topic *i+15* on the same day, and topic *i+1*
  the next. A format never sits beside itself in the bank and never shares a
  day with itself.
- Five of the seven draw everything themselves. Only `cuts` and `doc` use the
  four library clips — six topics out of thirty, down from all of them.

Where a format needed a line the bank does not have — a buyer's opening
message in a chat — it is a question, never a claim, and the thread is headed
"Illustration".

## What the audit found (measured, 14 Nov)

1. **The "library footage" label was hidden on Instagram.** It sat at 86% of the
   frame height, under the app's caption stack. Fixed: now at 15%, 30 px.
2. **Every reel opened on two seconds of flat colour.** Fixed: every format
   has its hook on screen, with something moving, on frame 0.
3. **The close asked for nothing.** Fixed: the Instagram cut ends "Send this to
   whoever orders your kit"; the LinkedIn cut ends on the quote page.
4. **20 of 30 topics were the old slide format.** Fixed 15 Nov: all 30 rebuilt.
5. **Four clips carried everything.** Now six topics. One plate (scissors on
   fabric) is soft; `doc` uses it wide and in black and white, never tight.

## The order of work

1. ~~Re-render everything with the current engine.~~ Done 15 Nov, all 60 files.
2. ~~Rebuild the 20 old-format topics.~~ Done 15 Nov.
3. Watch which formats earn sends and watch time once a fortnight of posts is
   in, and move topics toward the ones that do. Nothing here is measured yet.
4. **Own footage.** Ten phone clips from the SoccerTex floor (vertical, 10–20s,
   steady, no faces needed) go in `assets/footage/own/`, are used without the
   library label, and would let `doc` and `cuts` show the real factory. This
   one only Youssef can do.

## A cut is ready when

- The hook and motion are both on screen in the first frame.
- One idea, one number early, nothing on screen that is not being read.
- All text sits between 14% and 65% of the height, inside 8% side margins.
- Library footage carries the label; own footage never does.
- Every figure and claim already appears in `engine/bank.py` (or the `SCRIPTS`
  in `build_silent.py`, which were written from it). Those were checked against soccertexhq.com. Nothing
  new is added by an agent — see `EDITOR.md`.
- The render reports the same duration on disk as it planned, and frames
  pulled at 0s, the midpoint and the last second look right.
