#!/usr/bin/env python3
"""The fast-cut format, without a voice.

Youssef chose captions over an AI voice, which changes the problem. In the
narrated cut the voice carried the argument and the pictures decorated it.
With no voice the type *is* the performance, and two things follow:

  1. Timing has to come from reading speed rather than from a waveform. A
     caption has to sit long enough to be read once and not a frame longer,
     or the reel feels slow. `beats()` below does that arithmetic.

  2. The pictures can no longer be wallpaper. There are four licensed clips
     carrying thirty videos — roughly seventy seconds of distinct material —
     so leaning on b-roll means every video looks like every other one. The
     answer is to make the information itself the visual: a weight scale that
     fills, two lead times racing each other, a counter that climbs. Those
     are drawn from the brand, they cost no footage, and no competitor has
     them because nobody else publishes the numbers.

So a reel here is: a hook you can read in one glance, a short run of beats
over footage, one drawn scene that carries the actual argument, and a close.
"""
from __future__ import annotations
import re
from PIL import Image, ImageDraw

from engine.render import (W, H, FPS, SAFE, BOT_SAFE, Brand, Scene, Video,
                           ease_out, ease_in_out, clamp01, seg, wrap)
from engine.kinetic import Captions, Chapter, _halo
from engine.reel import Shot

# Reading speed for one- to three-word captions on a phone, in characters per
# second. Measured against the reference reels rather than typical prose rates:
# short centred lines in a big face read far faster than a paragraph, and the
# usual 15-18 cps prose figure leaves the cut feeling sluggish.
CPS = 23.0
MIN_HOLD = 0.42         # no beat is readable in less
MAX_HOLD = 1.30         # past this the reel stalls
BEAT_GAP = 0.05         # a hair of black between beats, so they snap


def chunk(line: str, max_words: int = 3) -> list[str]:
    """Split a sentence into caption beats of one to three words.

    Breaks are chosen so a beat never ends on a word that needs the next one
    to make sense — articles, prepositions and conjunctions pull the following
    word along with them.
    """
    glue = {"a", "an", "the", "of", "to", "in", "on", "at", "for", "and",
            "or", "but", "is", "it", "its", "that", "this", "your", "you",
            "we", "our", "not", "no", "so", "if", "than", "with", "from"}
    words, out, cur = line.split(), [], []
    for w in words:
        cur.append(w)
        bare = w.lower().strip(",.;:!?—-")
        if len(cur) >= max_words and bare not in glue:
            out.append(" ".join(cur)); cur = []
    if cur:
        if out and len(cur) == 1 and cur[0].lower().strip(",.") in glue:
            out[-1] += " " + cur[0]          # never strand a lone glue word
        else:
            out.append(" ".join(cur))
    return out


def beats(lines, start=0.0, line_gap=0.20):
    """Turn script lines into a caption timeline, timed by reading speed."""
    tl, t = [], start
    for li, line in enumerate(lines):
        for c in chunk(line):
            hold = min(MAX_HOLD, max(MIN_HOLD, len(c) / CPS))
            tl.append({"text": c, "start": t, "end": t + hold, "line": li})
            t += hold + BEAT_GAP
        t += line_gap
    return tl, t


# --------------------------------------------------------------- scenes ----
class MeterScene(Scene):
    """A weight scale that fills, with the bands labelled as it passes them.

    Built for GSM, and it is the clearest thing in the whole library: the
    number a buyer is told to ask for, drawn as the thing it measures.
    """

    def __init__(self, bands, unit="GSM", seconds=4.6, title=None,
                 lo=100, hi=340):
        super().__init__(seconds)
        self.bands, self.unit, self.title = bands, unit, title
        self.lo, self.hi = lo, hi

    def frame(self, i, n):
        img = Image.new("RGB", (W, H), Brand.FLOOR)
        d = ImageDraw.Draw(img)
        # The bars used to fill across three quarters of the scene, which left
        # the first two seconds showing four empty troughs — dead air in the
        # middle of a reel. They now land inside the first 40% and the rest of
        # the scene is a hold on the finished chart, which is the bit worth
        # looking at.
        p = ease_in_out(clamp01(i / (n * 0.40)))

        if self.title:
            d.text((SAFE, int(H * 0.21)), self.title, font=Brand.head(62),
                   fill=Brand.WHITE)

        x0, x1 = SAFE, W - SAFE
        top = int(H * 0.34)
        row = int(H * 0.095)
        span = self.hi - self.lo

        for k, (a, b, label) in enumerate(self.bands):
            y = top + k * row
            ax = x0 + (x1 - x0) * (a - self.lo) / span
            bx = x0 + (x1 - x0) * (b - self.lo) / span
            # each band grows in turn, so the eye walks up the scale
            kp = ease_out(clamp01((p * len(self.bands)) - k))
            d.rounded_rectangle([x0, y, x1, y + row - 14], 8,
                                fill=(18, 30, 24))
            if kp > 0:
                d.rounded_rectangle([ax, y, ax + (bx - ax) * kp, y + row - 14],
                                    8, fill=Brand.PITCH if k % 2 else Brand.PITCH_LIT)
            if kp > 0.55:
                f = Brand.med(34)
                d.text((x0 + 18, y + 12), label.upper(), font=f, fill=Brand.WHITE)
                fr = Brand.num(34)
                txt = f"{a}–{b}"
                d.text((x1 - 18 - d.textlength(txt, font=fr), y + 12), txt,
                       font=fr, fill=Brand.AMBER)

        # the axis, so the bars mean something
        ay = top + len(self.bands) * row + 10
        d.line([x0, ay, x1, ay], fill=Brand.SLATE, width=3)
        fa = Brand.body(30)
        for v in range(self.lo, self.hi + 1, 60):
            vx = x0 + (x1 - x0) * (v - self.lo) / span
            d.line([vx, ay, vx, ay + 12], fill=Brand.SLATE, width=3)
            d.text((vx - d.textlength(str(v), font=fa) / 2, ay + 20), str(v),
                   font=fa, fill=Brand.SLATE)
        d.text((x1 - d.textlength(self.unit, font=Brand.head(40)), ay + 62),
               self.unit, font=Brand.head(40), fill=Brand.WHITE)
        return img


class RaceScene(Scene):
    """Two durations racing left to right. The short one lands and waits.

    This is the two-week argument as a picture. A list saying "2 weeks vs 14"
    is a claim; watching one bar finish and the other still crawling is the
    reason the claim matters.
    """

    def __init__(self, title, slow, fast, seconds=5.0, unit="weeks"):
        super().__init__(seconds)
        self.title, self.slow, self.fast, self.unit = title, slow, fast, unit

    def frame(self, i, n):
        img = Image.new("RGB", (W, H), Brand.FLOOR)
        d = ImageDraw.Draw(img)
        hold = int(n * 0.16)
        p = clamp01((i - hold) / max(1, n - hold * 2))

        d.text((SAFE, int(H * 0.16)), self.title, font=Brand.head(60),
               fill=Brand.WHITE)

        x0, x1 = SAFE, W - SAFE
        worst = max(self.slow[1], self.fast[1])
        # The label used to sit inside the bar and the value just past its
        # end. On the fast bar — two weeks against fourteen — the bar is a
        # seventh of the width, so the two collided into unreadable mush.
        # Label goes above the track, value goes inside the bar when it fits
        # and outside when it doesn't. Neither can ever overlap the other.
        for k, (label, weeks, good) in enumerate(
                ((self.slow[0], self.slow[1], False),
                 (self.fast[0], self.fast[1], True))):
            y = int(H * (0.36 + k * 0.22))
            bar_h = int(H * 0.095)
            d.text((x0, y - 46), label.upper(), font=Brand.med(36),
                   fill=Brand.SLATE)
            d.rounded_rectangle([x0, y, x1, y + bar_h], 12, fill=(18, 30, 24))
            # each bar advances at its own real pace, so the fast one arrives
            # first and then sits there while the slow one is still going
            prog = clamp01(p * worst / weeks)
            wpx = (x1 - x0) * (weeks / worst) * prog
            col = Brand.PITCH_LIT if good else (150, 62, 48)
            d.rounded_rectangle([x0, y, x0 + max(14, wpx), y + bar_h], 12, fill=col)

            done = prog >= 0.999
            fn = Brand.num(56)
            txt = f"{weeks} {self.unit}"
            tw = d.textlength(txt, font=fn)
            ty = y + (bar_h - fn.size) / 2 - 4
            if wpx > tw + 48:                       # room inside the bar
                d.text((x0 + 24, ty), txt, font=fn, fill=Brand.WHITE)
            else:                                   # park it clear of the bar
                d.text((min(x0 + max(14, wpx) + 24, x1 - tw), ty), txt,
                       font=fn, fill=Brand.AMBER if done else Brand.SLATE)
            if done and good:
                d.text((x0, y + bar_h + 14), "DELIVERED — STILL IN SEASON",
                       font=Brand.med(32), fill=Brand.PITCH_LIT)
        return img


class TypeScene(Scene):
    """Full-bleed type on brand colour. For the hook and for a hard turn.

    No footage behind it on purpose: after two seconds of moving pictures a
    flat colour with one sentence on it is the loudest thing you can cut to.
    """

    def __init__(self, lines, seconds=1.9, bg=None, accent=None, sub=None,
                 size=96):
        super().__init__(seconds)
        self.lines = lines if isinstance(lines, (list, tuple)) else [lines]
        self.bg = bg or Brand.DEEP
        self.accent = accent or Brand.PITCH_LIT
        self.sub, self.size = sub, size

    def frame(self, i, n):
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        f = Brand.head(self.size)
        rows = []
        for ln in self.lines:
            rows += wrap(d, ln, f, W - 2 * SAFE)
        while len(rows) * f.size * 1.1 > H * 0.42 and f.size > 54:
            f = Brand.head(f.size - 6)
            rows = []
            for ln in self.lines:
                rows += wrap(d, ln, f, W - 2 * SAFE)
        y = (H - len(rows) * f.size * 1.1) / 2 - (40 if self.sub else 0)
        for k, ln in enumerate(rows):
            p = ease_out(seg(i, FPS * (0.02 + k * 0.07), FPS * 0.26))
            d.text((SAFE + int((1 - p) * 26), y), ln, font=f,
                   fill=tuple(int(self.bg[j] + (255 - self.bg[j]) * p)
                              for j in range(3)))
            y += f.size * 1.1
        sp = ease_out(seg(i, FPS * 0.28, FPS * 0.3))
        d.line([SAFE, y + 26, SAFE + int(220 * sp), y + 32],
               fill=self.accent, width=7)
        if self.sub:
            d.text((SAFE, y + 62), self.sub, font=Brand.body(42),
                   fill=tuple(int(self.bg[j] + (Brand.SLATE[j] - self.bg[j]) * sp)
                              for j in range(3)))
        return img


# ----------------------------------------------------------------- build ----
# Cut rhythm. The reference sits at 1.25s; without a voice the eye needs a
# fraction longer on each picture, because it is also reading.
CUT = 1.35


def _vary(clips, n):
    """Order n shots so the same clip never lands twice in a row.

    There are four licensed clips behind thirty videos, so a plate has to
    repeat inside a single reel. Repeating is survivable; repeating back to
    back is what makes a reel look like a screensaver. This walks the list
    and, whenever the next shot would reuse the clip just seen, pulls the
    soonest different one forward instead. Every other appearance is also
    mirrored, so a returning plate reads as a new angle.
    """
    order, seen_last, pool = [], None, list(clips)
    counts = {}
    for i in range(n):
        pick = None
        for j in range(len(pool)):
            cand = pool[(i + j) % len(pool)]
            if cand[0] != seen_last:
                pick = cand
                break
        pick = pick or pool[i % len(pool)]
        counts[pick[0]] = counts.get(pick[0], 0) + 1
        order.append(pick + (counts[pick[0]] % 2 == 0,))   # mirror alternate
        seen_last = pick[0]
    return order


def footage_run(video, clips, caps, t0, seconds, chapters=None, shown=None):
    """Fill `seconds` with cuts, carrying the caption timeline across them."""
    t, k = t0, 0
    shown = shown if shown is not None else set()
    plan = _vary(clips, int(seconds / CUT) + 2)
    while t < t0 + seconds - 0.05:
        dur = min(CUT, t0 + seconds - t)
        clip, tight, focus, mirror = plan[k]
        start_t = t
        chap = None
        if chapters:
            for li, (num, label) in chapters.items():
                s = next((c["start"] for c in caps.tl if c["line"] == li), None)
                if s is not None and li not in shown and start_t <= s < start_t + dur:
                    chap = Chapter(num, label); shown.add(li); break

        def overlay(d, i, n, _t0=start_t, _chap=chap):
            caps.draw(d, _t0 + i / FPS)
            if _chap:
                _chap.draw(d, i, n)

        # blur_edge was 9, which stopped reading as shallow depth of field
        # and started reading as a clip that is simply out of focus — the
        # worst impression a factory video can give. 4 is enough to separate
        # the caption from the plate behind it.
        video.add(Shot(clip, dur, overlay=overlay, tight=tight, focus=focus,
                       zoom=1.06, blur_edge=4, scrim=0.46, mirror=mirror,
                       start=1.0 + (k * 3.7) % 11.0))
        t += dur
        k += 1
    return t
