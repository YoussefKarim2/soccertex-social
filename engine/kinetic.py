#!/usr/bin/env python3
"""Kinetic captions and chapter cards — the @kallaway mechanic.

Measured off the reference Youssef sent: something on screen changes every
1.25 seconds (median), captions hold one to three words at a time, and the
mix never drops below -16.6 dB. This module supplies the two visual halves of
that: a caption track that spans scene boundaries, and chapter cards.

Captions are drawn from a single global timeline rather than per scene, so a
word that starts before a cut finishes after it. That is what makes the cuts
feel like they are riding the voice instead of interrupting it.
"""
from __future__ import annotations
from PIL import Image, ImageDraw
from engine.render import W, H, FPS, SAFE, BOT_SAFE, Brand, ease_out, wrap

# words worth colouring — numbers and the terms a buyer is scanning for
import re
ACCENT_RE = re.compile(r"^\d|GSM|MOQ|kg|gsm$", re.I)


def _halo(d, xy, text, font, fill, strength=190):
    x, y = xy
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3), (-3, 3), (3, -3)):
        d.text((x + dx, y + dy), text, font=font, fill=(2, 10, 6, strength))
    for dx, dy in ((-5, 3), (5, 3), (0, 6)):
        d.text((x + dx, y + dy), text, font=font, fill=(2, 10, 6, strength // 2))
    d.text((x, y), text, font=font, fill=fill)


class Captions:
    """A timeline of (text, start, end), drawn by global video time."""

    def __init__(self, timeline, size=92, y_frac=0.60, accent=True):
        self.tl = timeline
        self.size, self.y_frac, self.accent = size, y_frac, accent

    def at(self, t):
        for c in self.tl:
            if c["start"] <= t < c["end"]:
                return c
        return None

    def draw(self, d, t):
        c = self.at(t)
        if not c:
            return
        age = t - c["start"]
        # snap in with a short overshoot: 0 -> 1.14 -> 1.0 in about 0.13s
        if age < 0.07:
            k = 0.6 + 0.8 * (age / 0.07)
        elif age < 0.13:
            k = 1.14 - 0.14 * ((age - 0.07) / 0.06)
        else:
            k = 1.0
        f = Brand.head(int(self.size * k))
        words = c["text"].split()
        gap = int(f.size * 0.26)
        widths = [d.textlength(w, font=f) for w in words]
        total = sum(widths) + gap * (len(words) - 1)
        # one caption never wraps: shrink until it fits the safe width
        while total > W - 2 * SAFE and f.size > 42:
            f = Brand.head(f.size - 5)
            gap = int(f.size * 0.26)
            widths = [d.textlength(w, font=f) for w in words]
            total = sum(widths) + gap * (len(words) - 1)
        x = (W - total) / 2
        y = H * self.y_frac - f.size / 2
        for w, wd in zip(words, widths):
            hit = self.accent and ACCENT_RE.search(w.strip(",.;:!?"))
            _halo(d, (x, y), w, f, Brand.AMBER if hit else Brand.WHITE)
            x += wd + gap


class Chapter:
    """'01 — CUT' style card. Flashes in, sits for the shot, snaps out."""

    def __init__(self, n, label):
        self.n, self.label = n, label

    def draw(self, d, i, n):
        p = ease_out(min(1.0, i / (FPS * 0.22)))
        fn = Brand.num(58)
        fl = Brand.med(40)
        num = f"{self.n:02d}"
        nw = d.textlength(num, font=fn)
        lw = d.textlength(self.label.upper(), font=fl)
        pad, gapx = 20, 22
        boxw = int((nw + pad * 2 + gapx + lw) * p)
        y = int(H * 0.17)
        d.rectangle([SAFE, y, SAFE + int((nw + pad * 2) * p), y + 76], fill=Brand.PITCH)
        if p > 0.4:
            d.text((SAFE + pad, y + 9), num, font=fn, fill=Brand.WHITE)
            _halo(d, (SAFE + nw + pad * 2 + gapx, y + 17), self.label.upper(), fl,
                  Brand.WHITE, 150)
        d.line([SAFE, y + 84, SAFE + boxw, y + 89], fill=Brand.PITCH_LIT, width=5)


def flash(d, strength):
    """A couple of frames of brand colour on a beat. Used sparingly — it is
    the difference between energetic and a strobe warning."""
    if strength <= 0:
        return
    ov = Image.new("RGBA", (W, H), Brand.PITCH_LIT + (int(190 * strength),))
    return ov
