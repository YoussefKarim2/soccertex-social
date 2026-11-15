#!/usr/bin/env python3
"""Six ways to make a reel that do not look like each other.

Youssef's note, 15 Nov: "all the videos are the same but only the words are
different." He was right, and it was structural — thirty topics went through
two templates, over four stock clips. Changing the words could never fix it.

So a topic now picks a FORMAT, and each format has its own picture, palette,
type, motion and sound:

    chat       a message thread — dark, conversational, things arrive
    poster     giant type on flat colour — loud, hard cuts, counting numbers
    notebook   a paper checklist — calm, ticks and a highlighter
    versus     red column against green column — an argument, row by row
    blueprint  line drawings on a drafting grid — technical, quiet
    doc        black-and-white footage with one amber word — slow, filmic
    (cuts      the existing fast-cut captions over footage, engine/silent.py)

Five of the six draw everything themselves, which matters for a second reason:
they do not lean on the four library clips at all, and Instagram ranks original
pictures above recycled ones.

Everything on screen sits between 15% and 66% of the height — the band Meta's
own guidance leaves clear of the Reels interface.

No format here invents content. Each is handed lines from engine/bank.py.
"""
from __future__ import annotations
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageOps

from engine.render import (W, H, FPS, SAFE, LABEL_Y, Brand, Scene,
                           ease_out, ease_in_out, clamp01, wrap)
from engine.reel import Shot

BAND_T, BAND_B = int(H * 0.15), int(H * 0.66)
INNER = W - 2 * SAFE
_M = ImageDraw.Draw(Image.new("RGB", (8, 8)))       # for measuring text


@lru_cache(maxsize=None)
def F(kind, size):
    return getattr(Brand, kind)(max(8, int(size)))


def read_secs(text, cps=22.0, lo=1.3, hi=3.8):
    """How long a line has to stay up to be read once, comfortably."""
    return max(lo, min(hi, len(text) / cps + 0.5))


def mix(a, b, t):
    t = clamp01(t)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def prog(t, start, dur):
    return clamp01((t - start) / dur) if dur > 0 else 1.0


def fit(text, kind, width, max_size, min_size, max_lines, lh=1.14, max_h=None):
    """Largest size at which `text` wraps into the box. Returns (font, lines)."""
    size = max_size
    while True:
        f = F(kind, size)
        lines = wrap(_M, text, f, width)
        ok = len(lines) <= max_lines and (max_h is None or len(lines) * size * lh <= max_h)
        if ok or size <= min_size:
            return f, lines
        size -= 4


def tick_mark(d, x, y, s, p, fill, width=7):
    """A hand-drawn tick inside a box of side s, drawn in as p goes 0→1."""
    a, b, c = (x + s * .18, y + s * .55), (x + s * .42, y + s * .80), (x + s * .86, y + s * .22)
    if p <= 0:
        return
    q = min(1.0, p * 2)
    d.line([a, (a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q)], fill=fill, width=width)
    if p > .5:
        q = (p - .5) * 2
        d.line([b, (b[0] + (c[0] - b[0]) * q, b[1] + (c[1] - b[1]) * q)], fill=fill, width=width)


def cross_mark(d, x, y, s, fill, width=7):
    d.line([x + s * .22, y + s * .22, x + s * .78, y + s * .78], fill=fill, width=width)
    d.line([x + s * .78, y + s * .22, x + s * .22, y + s * .78], fill=fill, width=width)


def wordmark(d, colour):
    """Below 66% the app draws its own caption, so nothing that matters goes
    there — but an empty third of the frame reads as unfinished. This is the
    one thing that sits in it: the name, quiet."""
    d.text((SAFE, int(H * 0.705)), "SOCCERTEX", font=F("head", 40), fill=colour)
    d.text((SAFE, int(H * 0.705) + 50), "Teamwear factory · Cairo", font=F("med", 30), fill=colour)


# ════════════════════════════════════════════════════════════ the close ═════
class CloseCard(Scene):
    """The last two seconds, in whatever colours the format used."""

    def __init__(self, line, sub, bg, fg, accent, seconds=2.0):
        super().__init__(seconds)
        self.line, self.sub, self.bg, self.fg, self.accent = line, sub, bg, fg, accent

    def frame(self, i, n):
        t = i / FPS
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        f, rows = fit(self.line, "head", INNER, 100, 60, 4, 1.1)
        y = H * 0.40 - len(rows) * f.size * 1.1 / 2
        for k, ln in enumerate(rows):
            p = ease_out(prog(t, k * 0.05, 0.2))
            d.text((SAFE + int((1 - p) * 24), y), ln, font=f, fill=mix(self.bg, self.fg, p))
            y += f.size * 1.1
        sp = ease_out(prog(t, 0.2, 0.3))
        d.line([SAFE, y + 24, SAFE + int(220 * sp), y + 30], fill=self.accent, width=7)
        d.text((SAFE, y + 58), self.sub, font=F("med", 44), fill=mix(self.bg, self.fg, 0.8 * sp))
        return img


# ═════════════════════════════════════════════════════════════════ chat ═════
class ChatScene(Scene):
    """A message thread. Script items are (who, text):

        me      a bubble on the right        them    a bubble on the left,
        sys     a centred grey note                  after typing dots
        seen    a small "Seen" under a bubble
        typing  dots that never resolve (text = seconds to hold them)

    The thread is an illustration of a conversation, and says so in its header.
    """
    BG, THEM, TXT, GREY = (11, 15, 12), (34, 42, 37), (238, 244, 240), (128, 142, 134)
    FS, LH, PX, PY = 50, 64, 32, 24
    MAXW = int(W * 0.80)

    def __init__(self, name, script, tag="Illustration", me=(27, 150, 78), lead=0.0, tail=1.2):
        self.name, self.tag, self.me = name, tag, me
        f = F("med", self.FS)

        def item(kind, text=""):
            if kind in ("me", "them"):
                lines = wrap(_M, text, f, self.MAXW - 2 * self.PX)
                w = max(_M.textlength(l, font=f) for l in lines) + 2 * self.PX
                h = len(lines) * self.LH + 2 * self.PY - 10
            elif kind == "dots":
                lines, w, h = [], 150, 86
            elif kind == "sys":
                fs = F("med", 32)
                lines = wrap(_M, text, fs, INNER - 100)
                w = max(_M.textlength(l, font=fs) for l in lines) + 60
                h = len(lines) * 44 + 26
            else:                                   # seen
                lines, w, h = [text], _M.textlength(text, font=F("body", 30)), 40
            return dict(kind=kind, lines=lines, w=int(w), h=int(h))

        # A bubble stays on screen after the next one lands, so it does not
        # need its whole reading time to itself.
        hold = lambda s: read_secs(s, cps=30, lo=1.1, hi=3.3)
        t, cur, self.states, self.marks = lead, [], [], []
        for who, text in script:
            if who == "them":
                if cur:
                    self.states.append((t, cur + [item("dots")])); t += 0.45
                cur = cur + [item("them", text)]
                self.states.append((t, cur)); self.marks.append(t); t += hold(text)
            elif who == "me":
                if cur: t += 0.2
                cur = cur + [item("me", text)]
                self.states.append((t, cur)); self.marks.append(t); t += hold(text) * 0.9
            elif who == "sys":
                if cur: t += 0.25
                cur = cur + [item("sys", text)]
                self.states.append((t, cur)); t += max(1.3, read_secs(text) * 0.85)
            elif who == "seen":
                t += 0.5
                cur = cur + [item("seen", text)]
                self.states.append((t, cur)); t += 1.1
            elif who == "typing":
                cur = cur + [item("dots")]
                self.states.append((t, cur)); t += float(text or 2.2)
        super().__init__(t + tail)

    @staticmethod
    def _gap(a, b):
        if b["kind"] == "seen": return 6
        if a["kind"] == "seen" or a["kind"] != b["kind"]: return 28
        return 14

    def _height(self, items):
        return sum(it["h"] for it in items) + sum(self._gap(items[k - 1], items[k]) for k in range(1, len(items)))

    def frame(self, i, n):
        t = i / FPS
        idx = -1
        for k, (ts, _) in enumerate(self.states):
            if ts <= t: idx = k
        items = self.states[idx][1] if idx >= 0 else []
        hc = self._height(items)
        hp = self._height(self.states[idx - 1][1]) if idx > 0 else 0
        p = ease_out(prog(t, self.states[idx][0], 0.22)) if idx >= 0 else 1.0
        if idx == 0 and self.states[0][0] <= 0.01:
            p = 1.0                    # the first message is there on frame 0
        scroll = hp + (hc - hp) * p

        img = Image.new("RGB", (W, H), self.BG)
        d = ImageDraw.Draw(img)
        yb = BAND_B - 8
        head_t = BAND_T - 36
        head_b = head_t + 124
        y = yb - scroll
        f = F("med", self.FS)
        for k, it in enumerate(items):
            if k: y += self._gap(items[k - 1], it)
            if y + it["h"] > head_b - 10 and y < yb + 40:
                kind = it["kind"]
                if kind in ("me", "them", "dots"):
                    x = W - SAFE - it["w"] if kind == "me" else SAFE
                    d.rounded_rectangle([x, y, x + it["w"], y + it["h"]], radius=34,
                                        fill=self.me if kind == "me" else self.THEM)
                    if kind == "dots":
                        for j in range(3):
                            a = 0.5 + 0.5 * math.sin(t * 7 - j * 0.9)
                            c = mix(self.THEM, self.TXT, 0.3 + 0.6 * a)
                            cx = x + 44 + j * 32
                            d.ellipse([cx - 9, y + 34, cx + 9, y + 52], fill=c)
                    else:
                        ty = y + self.PY - 6
                        for ln in it["lines"]:
                            d.text((x + self.PX, ty), ln, font=f,
                                   fill=(255, 255, 255) if kind == "me" else self.TXT)
                            ty += self.LH
                elif kind == "sys":
                    x = (W - it["w"]) // 2
                    d.rounded_rectangle([x, y, x + it["w"], y + it["h"]], radius=22, fill=(22, 28, 25))
                    ty = y + 10
                    for ln in it["lines"]:
                        lw = _M.textlength(ln, font=F("med", 32))
                        d.text(((W - lw) / 2, ty), ln, font=F("med", 32), fill=self.GREY)
                        ty += 44
                else:
                    d.text((W - SAFE - it["w"], y), it["lines"][0], font=F("body", 30), fill=self.GREY)
            y += it["h"]

        # header, drawn over anything that scrolled up behind it
        d.rectangle([0, 0, W, head_b], fill=self.BG)
        cx, cy = SAFE + 46, head_t + 60
        d.ellipse([cx - 46, cy - 46, cx + 46, cy + 46], fill=self.me if "Soccer" in self.name else (58, 70, 63))
        ini = self.name.replace("A ", "").strip()[0].upper()
        iw = _M.textlength(ini, font=F("head", 50))
        d.text((cx - iw / 2, cy - 34), ini, font=F("head", 50), fill=(255, 255, 255))
        d.text((SAFE + 114, head_t + 20), self.name, font=F("bold", 46), fill=self.TXT)
        tw_ = _M.textlength(self.tag, font=F("med", 28))
        d.rounded_rectangle([SAFE + 114, head_t + 78, SAFE + 114 + tw_ + 28, head_t + 116], radius=19,
                            outline=(70, 84, 76), width=2)
        d.text((SAFE + 128, head_t + 81), self.tag, font=F("med", 28), fill=self.GREY)
        d.line([0, head_b, W, head_b], fill=(26, 33, 29), width=3)

        # the input bar, and nothing below it — that is the app's own territory
        d.rectangle([0, yb + 12, W, H], fill=self.BG)
        d.rounded_rectangle([SAFE, yb + 34, W - SAFE, yb + 122], radius=44, fill=(22, 28, 25))
        d.text((SAFE + 36, yb + 55), "Message", font=F("body", 38), fill=(88, 100, 93))
        # a keyboard, so the bottom of the frame is a phone and not a void
        ky, kh, gap = yb + 160, 92, 12
        for r, keys in enumerate((10, 9, 7)):
            kw = (W - 2 * 30 - gap * 9) / 10
            x0 = (W - (keys * kw + (keys - 1) * gap)) / 2
            for c in range(keys):
                x = x0 + c * (kw + gap)
                d.rounded_rectangle([x, ky + r * (kh + gap), x + kw, ky + r * (kh + gap) + kh],
                                    radius=12, fill=(24, 30, 27))
        d.rounded_rectangle([W * .25, ky + 3 * (kh + gap), W * .75, ky + 3 * (kh + gap) + kh],
                            radius=12, fill=(24, 30, 27))
        return img


# ═══════════════════════════════════════════════════════════════ poster ═════
INK, BONE, AMBER = (12, 12, 11), (243, 238, 226), (236, 164, 52)

# Seven colourways for the poster format. Each is three schemes (background,
# type, accent) that a reel rotates through, so its own cuts contrast and no
# two poster reels share a palette.
POSTER_SKINS = {
    "ink":    [(INK, BONE, AMBER), (BONE, INK, (196, 70, 44)), (AMBER, INK, INK)],
    "pitch":  [((6, 40, 24), (236, 250, 240), (190, 240, 90)), ((236, 250, 240), (6, 40, 24), (20, 132, 68)),
               ((190, 240, 90), (6, 40, 24), (6, 40, 24))],
    "navy":   [((14, 24, 56), (246, 240, 226), (255, 112, 84)), ((246, 240, 226), (14, 24, 56), (232, 84, 58)),
               ((255, 112, 84), (14, 24, 56), (14, 24, 56))],
    "paper":  [((243, 238, 226), (18, 18, 16), (214, 64, 40)), ((18, 18, 16), (243, 238, 226), (240, 104, 76)),
               ((214, 64, 40), (250, 244, 232), (250, 244, 232))],
    "blue":   [((8, 8, 10), (250, 250, 250), (72, 150, 255)), ((250, 250, 250), (8, 8, 10), (36, 104, 232)),
               ((36, 104, 232), (250, 250, 250), (250, 250, 250))],
    "mint":   [((214, 244, 226), (8, 44, 28), (20, 132, 68)), ((8, 44, 28), (214, 244, 226), (120, 230, 160)),
               ((20, 132, 68), (240, 252, 244), (240, 252, 244))],
    "sunset": [((48, 12, 20), (250, 240, 226), (255, 140, 60)), ((250, 240, 226), (48, 12, 20), (220, 90, 40)),
               ((255, 140, 60), (48, 12, 20), (48, 12, 20))],
}


def _ax(align, b):
    """x for a line whose bbox is b, flush left or centred."""
    return SAFE - b[0] if align == "left" else (W - (b[2] - b[0])) / 2 - b[0]


def _rows(d, rows, f, y, align, fill, lh, dy=0):
    for ln in rows:
        x = SAFE if align == "left" else (W - _M.textlength(ln, font=f)) / 2
        d.text((x, y + dy), ln, font=f, fill=fill)
        y += f.size * lh
    return y


class Slam(Scene):
    """Lines of type, each set as wide as the frame, landing one at a time.
    motion: "pop" grows into place, "rise" comes up from below."""

    def __init__(self, lines, sub=None, bg=INK, fg=BONE, accent=AMBER, hi=None, seconds=None,
                 stagger=0.10, align="left", motion="pop", pace=1.0):
        self.lines, self.sub, self.bg, self.fg, self.accent, self.hi = lines, sub, bg, fg, accent, hi
        self.stagger, self.align, self.motion = stagger, align, motion
        base = F("head", 200)
        self.sizes = [min(380, 200 * INNER / max(1, _M.textlength(ln, font=base))) for ln in lines]
        room = (BAND_B - BAND_T) - (150 if sub else 0)
        k = 1.0
        for _ in range(3):
            tot = sum(self._bh(ln, s * k) for ln, s in zip(lines, self.sizes)) + 24 * (len(lines) - 1)
            if tot > room: k *= room / tot
        self.sizes = [s * k for s in self.sizes]
        self.heights = [self._bh(ln, s) for ln, s in zip(lines, self.sizes)]
        self.total = sum(self.heights) + 24 * (len(lines) - 1)
        self.y0 = BAND_T + (room - self.total) / 2
        if seconds is None:
            seconds = (0.55 + 0.34 * len(lines) + (read_secs(sub) * 0.75 if sub else 0.35)) * pace
        super().__init__(max(1.2, min(3.8, seconds)))

    @staticmethod
    def _bh(ln, size):
        b = _M.textbbox((0, 0), ln, font=F("head", size))
        return b[3] - b[1]

    def frame(self, i, n):
        t = i / FPS
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        y = self.y0
        for k, ln in enumerate(self.lines):
            tk = k * self.stagger
            if t >= tk:
                p = ease_out(prog(t, tk, 0.16))
                # it lands slightly small and grows to size — never past the margins
                sc = 0.90 + 0.10 * p if self.motion == "pop" else 1.0
                rise = (1 - p) * 46 if self.motion == "rise" else 0
                f = F("head", self.sizes[k] * sc)
                b = d.textbbox((0, 0), ln, font=f)
                dy = (self.heights[k] - (b[3] - b[1])) / 2
                d.text((_ax(self.align, b), y - b[1] + dy + rise), ln, font=f,
                       fill=self.accent if k == self.hi else self.fg)
            y += self.heights[k] + 24
        if self.sub:
            ts = len(self.lines) * self.stagger + 0.1
            p = ease_out(prog(t, ts, 0.25))
            f, rows = fit(self.sub, "med", INNER, 50, 38, 3, 1.25)
            _rows(d, rows, f, y + 14, self.align, mix(self.bg, self.fg, 0.85 * p), 1.25, (1 - p) * 16)
        wordmark(d, mix(self.bg, self.fg, 0.30))
        return img


class Say(Scene):
    """One sentence, big, with an optional numeral. For lines too long to slam."""

    def __init__(self, text, n=None, bg=INK, fg=BONE, accent=AMBER, seconds=None,
                 align="left", motion="pop", pace=1.0):
        self.text, self.num, self.bg, self.fg, self.accent = text, n, bg, fg, accent
        self.align = align
        self.top = BAND_T + (250 if n is not None else 40)
        self.f, self.rows = fit(text, "head", INNER, 100, 56, 6, 1.14, BAND_B - self.top - 50)
        super().__init__(seconds or (read_secs(text) + 0.45) * pace)

    def frame(self, i, n):
        t = i / FPS
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        if self.num is not None:
            p = ease_out(prog(t, 0, 0.18))
            fn = F("num", 300 - 40 * (1 - p))
            s = str(self.num)
            x = SAFE - 8 if self.align == "left" else (W - _M.textlength(s, font=fn)) / 2
            d.text((x, BAND_T - 60), s, font=fn, fill=self.accent)
        y = self.top
        if self.num is None:
            y = BAND_T + ((BAND_B - BAND_T) - len(self.rows) * self.f.size * 1.14) / 2 - 20
        for k, ln in enumerate(self.rows):
            p = ease_out(prog(t, 0.06 + k * 0.06, 0.2))
            x = SAFE if self.align == "left" else (W - _M.textlength(ln, font=self.f)) / 2
            d.text((x + (1 - p) * 30, y), ln, font=self.f, fill=mix(self.bg, self.fg, p))
            y += self.f.size * 1.14
        sp = ease_out(prog(t, 0.3, 0.3))
        x0 = SAFE if self.align == "left" else W / 2 - 100 * sp
        d.rectangle([x0, y + 22, x0 + int(200 * sp), y + 32], fill=self.accent)
        wordmark(d, mix(self.bg, self.fg, 0.30))
        return img


class Count(Scene):
    """A number that counts up to itself, with what it is underneath."""

    def __init__(self, value, suffix, label, note=None, bg=AMBER, fg=INK, accent=INK, seconds=None,
                 align="left", motion="pop", pace=1.0):
        self.value, self.suffix, self.label, self.note = value, suffix, label, note
        self.bg, self.fg, self.accent, self.align = bg, fg, accent, align
        final = f"{value:,}{suffix}"
        self.size = min(460, 200 * INNER / max(1, _M.textlength(final, font=F("num", 200))))
        super().__init__(seconds or (1.5 + read_secs(label + " " + (note or ""), lo=1.2) * 0.8) * pace)

    def frame(self, i, n):
        t = i / FPS
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        v = int(round(self.value * ease_out(prog(t, 0.05, 0.9))))
        f = F("num", self.size)
        b = d.textbbox((0, 0), f"{self.value:,}{self.suffix}", font=f)
        y = BAND_T + 30
        d.text((_ax(self.align, b), y - b[1]), f"{v:,}{self.suffix}", font=f, fill=self.accent)
        y += (b[3] - b[1]) + 50
        p = ease_out(prog(t, 0.7, 0.3))
        fl, rows = fit(self.label, "head", INNER, 66, 46, 3, 1.12)
        y = _rows(d, rows, fl, y, self.align, mix(self.bg, self.fg, p), 1.12, (1 - p) * 20)
        if self.note:
            p2 = ease_out(prog(t, 1.0, 0.3))
            fnote, rows = fit(self.note, "med", INNER, 46, 36, 3, 1.28)
            _rows(d, rows, fnote, y + 22, self.align, mix(self.bg, self.fg, 0.8 * p2), 1.28)
        wordmark(d, mix(self.bg, self.fg, 0.30))
        return img


class Poster:
    """Hands out slams, sentences and counters in one colourway, alignment,
    motion and pace, rotating the colourway's three schemes cut by cut."""

    def __init__(self, skin, align="left", motion="pop", pace=1.0):
        self.schemes, self.kw, self.k = POSTER_SKINS[skin], dict(align=align, motion=motion, pace=pace), 0

    def _next(self, scheme):
        if scheme is None:
            scheme, self.k = self.k % 3, self.k + 1
        bg, fg, accent = self.schemes[scheme]
        return dict(bg=bg, fg=fg, accent=accent, **self.kw)

    def slam(self, lines, sub=None, hi=None, scheme=None):
        return Slam(lines, sub, hi=hi, **self._next(scheme))

    def say(self, text, n=None, scheme=None):
        return Say(text, n, **self._next(scheme))

    def count(self, value, suffix, label, note=None):
        return Count(value, suffix, label, note, **self._next(2))

    def _plate(self, spec, scheme, **kw):
        c = self._next(scheme)
        return Plate(spec, colours=(c["bg"], c["fg"], c["accent"]), align=c["align"],
                     motion=c["motion"], pace=c["pace"], **kw)

    def fslam(self, spec, lines, sub=None, hi=None, scheme=None):
        """A slam over real footage."""
        return self._plate(spec, scheme, lines=lines, sub=sub, hi=hi)

    def fsay(self, spec, text, n=None, scheme=None):
        """A sentence over real footage."""
        return self._plate(spec, scheme, text=text, n=n)

    @property
    def close(self):
        bg, fg, accent = self.schemes[2]
        return bg, fg, accent


# ═════════════════════════════════════════════════════════════ notebook ═════
def parse_marked(text):
    """'Who signs off a [shade variance]?' → [(word, is_key), …]"""
    out, key = [], False
    for raw in text.split():
        w = raw
        if w.startswith("["): key = True; w = w[1:]
        end = "]" in w
        w = w.replace("]", "")
        out.append((w, key))
        if end: key = False
    return out


class NotebookScene(Scene):
    """A paper checklist. One item is big and in focus; the ones already
    covered sit ticked above it, so the page fills as the reel goes."""
    PAPER, INKC, RULE = (245, 240, 228), (26, 30, 28), (208, 220, 228)
    HILITE, MARGIN, TICK = (201, 236, 92), (228, 128, 116), (20, 132, 68)
    _bg = None

    def __init__(self, title, hook, sub, items, final, hook_s=2.0):
        self.title, self.hook, self.sub, self.final, self.hook_s = title, hook, sub, final, hook_s
        self.items = [(short, parse_marked(text)) for short, text in items]
        t, self.starts = hook_s, []
        for _, words in self.items:
            self.starts.append(t)
            t += read_secs(" ".join(w for w, _ in words), cps=24) + 0.25
        self.final_t = t
        self.marks = [hook_s] + self.starts[1:] + [t]
        super().__init__(t + read_secs(final) + 0.9)
        n = len(items)
        self.row_h = 66 if n <= 5 else 58
        self.stack_y = BAND_T + 100
        self.focus_y = self.stack_y + n * self.row_h + 34

    @classmethod
    def bg(cls):
        if cls._bg is None:
            img = Image.new("RGB", (W, H), cls.PAPER)
            d = ImageDraw.Draw(img)
            for y in range(40, H, 64):
                d.line([0, y, W, y], fill=cls.RULE, width=2)
            d.line([SAFE - 30, 0, SAFE - 30, H], fill=cls.MARGIN, width=3)
            cls._bg = img
        return cls._bg.copy()

    def _words(self, d, words, top, t0, t, max_size=88):
        """Draw marked words wrapped from `top`; highlighter runs behind keys."""
        room = BAND_B - top - 10
        size = max_size
        while True:
            f = F("head", size)
            sp = _M.textlength(" ", font=f)
            lines, cur, cw = [], [], 0
            for w, k in words:
                ww = _M.textlength(w, font=f)
                if cur and cw + sp + ww > INNER:
                    lines.append(cur); cur, cw = [], 0
                cur.append((w, k, cw + (sp if cur else 0), ww)); cw += (sp if len(cur) > 1 else 0) + ww
            if cur: lines.append(cur)
            if len(lines) * size * 1.18 <= room or size <= 50: break
            size -= 4
        p = ease_out(prog(t, t0, 0.22))
        hp = ease_in_out(prog(t, t0 + 0.18, 0.36))
        y = top + (1 - p) * 26
        for ln in lines:
            x = SAFE
            keys = [(x + off, x + off + ww) for (_, k, off, ww) in ln if k]
            if keys and hp > 0:
                a, b = keys[0][0] - 10, keys[-1][1] + 10
                d.rectangle([a, y + size * .20, a + (b - a) * hp, y + size * 1.10], fill=self.HILITE)
            for (w, k, off, ww) in ln:
                d.text((x + off, y), w, font=f, fill=mix(self.PAPER, self.INKC, p))
            y += size * 1.18

    def frame(self, i, n):
        t = i / FPS
        img = self.bg()
        d = ImageDraw.Draw(img)
        if t < self.hook_s:
            sizes = [min(190, 200 * INNER / _M.textlength(ln, font=F("head", 200))) for ln in self.hook]
            y = BAND_T + 60
            for k, ln in enumerate(self.hook):
                f = F("head", sizes[k])
                b = d.textbbox((0, 0), ln, font=f)
                if k == 0:
                    hp = ease_in_out(prog(t, 0.05, 0.4))
                    d.rectangle([SAFE - 12, y + (b[3] - b[1]) * .30, SAFE - 12 + (INNER + 24) * hp,
                                 y + (b[3] - b[1]) + 14], fill=self.HILITE)
                d.text((SAFE - b[0], y - b[1]), ln, font=f, fill=self.INKC)
                y += (b[3] - b[1]) + 26
            f, rows = fit(self.sub, "med", INNER, 50, 38, 3, 1.25)
            y += 20
            for ln in rows:
                d.text((SAFE, y), ln, font=f, fill=(84, 92, 88)); y += f.size * 1.25
            wordmark(d, (176, 174, 162))
            return img

        wordmark(d, (176, 174, 162))
        cur = max(k for k, s in enumerate(self.starts) if s <= t)
        done_all = t >= self.final_t
        d.text((SAFE, BAND_T), self.title, font=F("num", 54), fill=self.INKC)
        cnt = f"{len(self.items) if done_all else cur + 1} / {len(self.items)}"
        d.text((W - SAFE - _M.textlength(cnt, font=F("num", 54)), BAND_T), cnt, font=F("num", 54), fill=(120, 128, 124))
        d.line([SAFE, BAND_T + 74, W - SAFE, BAND_T + 74], fill=self.INKC, width=5)

        fs = F("med", 42)
        for k in range(cur + 1):
            y = self.stack_y + k * self.row_h
            done = k < cur or done_all
            d.rounded_rectangle([SAFE, y + 6, SAFE + 34, y + 40], radius=6, outline=self.INKC, width=3)
            if done:
                t_done = self.starts[k + 1] if k + 1 < len(self.starts) else self.final_t
                tick_mark(d, SAFE - 2, y + 2, 40, prog(t, t_done, 0.22), self.TICK, 6)
            d.text((SAFE + 54, y - 2), self.items[k][0], font=F("bold", 42) if not done else fs,
                   fill=self.INKC if not done else (96, 104, 100))
        if done_all:
            self._words(d, [(w, True) for w in self.final.split()], self.focus_y, self.final_t, t, 80)
        else:
            self._words(d, self.items[cur][1], self.focus_y, self.starts[cur], t)
        return img


# ═══════════════════════════════════════════════════════════════ versus ═════
VERSUS_SKINS = {
    # bg, the losing panel, the winning panel, type, red, green, sub colour
    "dark":  dict(bg=(15, 17, 19), pa=(44, 24, 22), pb=(18, 44, 30), txt=(242, 242, 238),
                  red=(226, 84, 60), grn=(36, 178, 94), soft=(214, 240, 222), mark=(70, 76, 80)),
    "light": dict(bg=(246, 241, 230), pa=(250, 222, 214), pb=(214, 240, 222), txt=(22, 24, 22),
                  red=(196, 52, 34), grn=(14, 122, 60), soft=(30, 70, 46), mark=(170, 166, 154)),
    "court": dict(bg=(12, 18, 44), pa=(58, 24, 44), pb=(14, 58, 62), txt=(244, 244, 250),
                  red=(255, 110, 100), grn=(72, 220, 160), soft=(200, 240, 228), mark=(70, 80, 120)),
}


class VersusScene(Scene):
    """Two sides of an argument.

    mode "stack": both columns stay on screen and fill a row from each side at
    a time. mode "duel": one pair at a time, large — the losing line on top,
    its answer underneath — which is faster and louder.
    """

    def __init__(self, hook, sub, title, a, b, final=None, hook_s=2.1, skin="dark", mode="stack", pace=1.0,
                 hookclip=None):
        self.hook, self.sub, self.title, self.final, self.hook_s = hook, sub, title, final, hook_s
        self.c, self.mode = VERSUS_SKINS[skin], mode
        # the hook can play over real footage instead of the split card
        self.hookshot = None
        if hookclip:
            stock_ok(hook, sub)
            self.hookshot = open_clip(hookclip, hook_s)
            self.hookrows = type_rows(lines=hook, sub=sub, colours=(self.c["bg"], self.c["txt"], self.c["grn"]))
        (self.la, self.ra), (self.lb, self.rb) = a, b
        k_a, k_b = (0.75, 0.9) if mode == "stack" else (0.85, 1.05)
        t, self.ta, self.tb = hook_s + 0.25, [], []
        for k in range(max(len(self.ra), len(self.rb))):
            if k < len(self.ra): self.ta.append(t); t += read_secs(self.ra[k]) * k_a * pace
            if k < len(self.rb): self.tb.append(t); t += read_secs(self.rb[k]) * k_b * pace
        self.end_t = t + 0.2
        self.marks = [hook_s] + self.ta + self.tb
        heights = [len(r) * ff.size * 1.12 for ff, r in (
            fit(title, "num", INNER, 56, 40, 2, 1.12), fit(final or title, "head", INNER, 62, 40, 2, 1.12))]
        self.top = BAND_T + max(heights) + 20
        super().__init__(self.end_t + (read_secs(final) + 0.7 if final else 0.9))

    def close(self):
        if self.hookshot:
            self.hookshot.close()

    def _hook(self, d, t):
        c = self.c
        mid = int(H * 0.47)
        d.rectangle([0, 0, W, mid], fill=c["pa"])
        d.rectangle([0, mid, W, H], fill=c["pb"])
        d.rectangle([0, mid - 4, W, mid + 4], fill=c["txt"])
        sizes = [min(190, 200 * INNER / _M.textlength(ln, font=F("head", 200))) for ln in self.hook]
        room = mid - BAND_T - 60
        for _ in range(3):
            hs = [_M.textbbox((0, 0), ln, font=F("head", sz)) for ln, sz in zip(self.hook, sizes)]
            tot = sum(b[3] - b[1] for b in hs) + 26 * (len(hs) - 1)
            if tot > room: sizes = [sz * room / tot for sz in sizes]
        y = mid - 46 - tot
        for k, ln in enumerate(self.hook):
            p = ease_out(prog(t, k * 0.08, 0.16))
            f = F("head", sizes[k] * (0.9 + 0.1 * p))
            b = d.textbbox((0, 0), ln, font=f)
            d.text((SAFE - b[0], y - b[1]), ln, font=f, fill=c["txt"])
            y += (hs[k][3] - hs[k][1]) + 26
        f, rows = fit(self.sub, "bold", INNER, 58, 40, 3, 1.22)
        y = mid + 50
        for ln in rows:
            d.text((SAFE, y), ln, font=f, fill=c["soft"]); y += f.size * 1.22

    def frame(self, i, n):
        t = i / FPS
        c = self.c
        img = Image.new("RGB", (W, H), c["bg"])
        d = ImageDraw.Draw(img)
        if t < self.hook_s:
            if self.hookshot:
                img = self.hookshot.frame(i, self.hookshot.n)
                draw_rows(ImageDraw.Draw(img), self.hookrows, t)
                return img
            self._hook(d, t)
            return img
        if self.hookshot:
            self.hookshot.close()

        closing = self.final and t >= self.end_t
        head = self.final if closing else self.title
        f, rows = fit(head, "head" if closing else "num", INNER, 62 if closing else 56, 40, 2, 1.12)
        y = BAND_T
        for ln in rows:
            d.text((SAFE, y), ln, font=f, fill=c["grn"] if closing else c["txt"]); y += f.size * 1.12
        wordmark(d, c["mark"])
        top = self.top
        ph = (BAND_B - top - 18) / 2
        sides = ((self.la, self.ra, self.ta, c["pa"], c["red"]), (self.lb, self.rb, self.tb, c["pb"], c["grn"]))

        if self.mode == "duel":
            cur = max([k for k, s in enumerate(self.ta) if s <= t] or [0])
            for col, (label, rows_, times, panel, tone) in enumerate(sides):
                py = top + col * (ph + 18)
                d.rounded_rectangle([SAFE - 20, py, W - SAFE + 20, py + ph], radius=26, fill=panel,
                                    outline=tone if (col == 1 and closing) else None, width=6)
                d.text((SAFE + 6, py + 14), label, font=F("num", 50), fill=tone)
                cnt = f"{cur + 1} / {len(rows_)}"
                d.text((W - SAFE - 6 - _M.textlength(cnt, font=F("num", 44)), py + 18), cnt, font=F("num", 44),
                       fill=mix(panel, tone, 0.6))
                if cur < len(rows_) and t >= times[cur]:
                    p = ease_out(prog(t, times[cur], 0.2))
                    fr, lines = fit(rows_[cur], "head", INNER - 30, 96, 52, 3, 1.12, ph - 120)
                    ty = py + 84 + (ph - 100 - len(lines) * fr.size * 1.12) / 2
                    for ln in lines:
                        d.text((SAFE + 6 + (1 - p) * (-60 if col == 0 else 60), ty), ln, font=fr,
                               fill=mix(panel, c["txt"], p)); ty += fr.size * 1.12
            return img

        nrow = max(len(self.ra), len(self.rb))
        rh = (ph - 78) / nrow
        size = int(min(54, rh * 0.40))
        for col, (label, rows_, times, panel, tone) in enumerate(sides):
            py = top + col * (ph + 18)
            d.rounded_rectangle([SAFE - 20, py, W - SAFE + 20, py + ph], radius=26, fill=panel,
                                outline=tone if (col == 1 and closing) else None, width=6)
            d.text((SAFE + 6, py + 14), label, font=F("num", 50), fill=tone)
            for k, txt in enumerate(rows_):
                if t < times[k]: continue
                p = ease_out(prog(t, times[k], 0.22))
                ry = py + 78 + k * rh
                x = SAFE + 6 + (1 - p) * (-70 if col == 0 else 70)
                s = min(52, rh * 0.5)
                cy = ry + (rh - s) / 2
                d.ellipse([x, cy, x + s, cy + s], fill=mix(panel, tone, p))
                if col == 0: cross_mark(d, x, cy, s, panel, 6)
                else: tick_mark(d, x, cy, s, 1.0, panel, 6)
                fr, lines = fit(txt, "bold", INNER - s - 40, size, 30, 2, 1.16)
                ty = ry + (rh - len(lines) * fr.size * 1.16) / 2
                for ln in lines:
                    d.text((x + s + 24, ty), ln, font=fr, fill=mix(panel, c["txt"], p)); ty += fr.size * 1.16
        return img


# ════════════════════════════════════════════════════════════ blueprint ═════
def _skin(bg, grid, line, accent, panel, hot):
    return dict(bg=bg, grid=grid, line=line, accent=accent, panel=panel, hot=hot,
                fab=mix(panel, line, .24), knit=mix(panel, line, .45), dim=mix(panel, line, .62),
                mute=mix(panel, line, .38), edge=mix(bg, line, .35), mark=mix(bg, line, .30))


# Four drafting sheets. Same drawings, different room: a blueprint, a night
# desk, a white technical sheet and a chalkboard.
BLUE_SKINS = {
    "blueprint": _skin((13, 36, 64), (26, 58, 96), (232, 244, 255), (118, 204, 255), (17, 48, 84), (255, 190, 92)),
    "night":     _skin((16, 16, 18), (34, 34, 38), (240, 236, 226), (236, 164, 52), (26, 26, 30), (120, 226, 150)),
    "sheet":     _skin((244, 241, 232), (218, 226, 234), (22, 40, 84), (28, 92, 204), (252, 250, 244), (226, 84, 60)),
    "chalk":     _skin((18, 54, 42), (30, 74, 58), (238, 246, 238), (255, 214, 110), (24, 66, 52), (255, 150, 120)),
}
K = BLUE_SKINS["blueprint"]            # the sheet being drawn on right now
NAVY, LINE, CYAN = K["bg"], K["line"], K["accent"]      # kept for the close card


class BlueprintScene(Scene):
    """A drafting sheet: a drawing in the upper box, the note for the current
    step underneath. `diagram(d, w, h, k, p)` draws the state for step k."""
    _bgs = {}
    BOX_H = 590

    def __init__(self, hook, sub, title, steps, diagram, hook_s=2.1, skin="blueprint", pace=1.0,
                 hookclip=None, footage=None):
        self.hook, self.sub, self.title, self.steps, self.diagram, self.hook_s = hook, sub, title, steps, diagram, hook_s
        self.skin = skin
        t, self.starts = hook_s, []
        for key, detail in steps:
            self.starts.append(t); t += (read_secs(key + " " + detail) + 0.45) * pace
        self.marks = list(self.starts)
        super().__init__(t + 0.5)
        # Real footage: the hook, and any step listed in `footage`, play over a
        # library clip instead of the sheet. The drawing keeps the other steps.
        c = BLUE_SKINS[skin]
        cols = (c["bg"], c["line"], c["accent"])
        ends = self.starts[1:] + [t + 0.5]
        self.shots, self.rows = {}, {}
        if hookclip:
            stock_ok(hook, sub)
            self.shots[-1] = open_clip(hookclip, hook_s)
            self.rows[-1] = type_rows(text=hook, sub=sub, colours=cols, kind="num", room=640, tmax=128)
        for k, spec in (footage or {}).items():
            key, detail = steps[k]
            stock_ok(key, detail, title)
            self.shots[k] = open_clip(spec, ends[k] - self.starts[k])
            fk, _ = fit(f"{k + 1}  {key}", "head", TEXT_W, 78, 44, 1)
            fd, drows = fit(detail, "med", TEXT_W, 56, 38, 4, 1.3, 330)
            self.rows[k] = ([(f"{k + 1}  {key}", fk, c["accent"], c["bg"], 8)]
                            + [(ln, fd, c["bg"], c["line"], 0) for ln in drows])

    def close(self):
        for s in self.shots.values():
            s.close()

    def _plate(self, k, i, t):
        """Step k (or the hook, k = -1) over its clip."""
        c = BLUE_SKINS[self.skin]
        shot = self.shots[k]
        t0 = 0.0 if k < 0 else self.starts[k]
        li = max(0, min(shot.n - 1, i - math.ceil(t0 * FPS - 1e-6)))
        img = shot.frame(li, shot.n)
        d = ImageDraw.Draw(img)
        if k >= 0:
            # the sheet's header rides along, so the step still reads as one of a set
            f, _ = fit(self.title, "num", TEXT_W - 150, 40, 26, 1)
            h = int(40 * 1.4)
            a, b = f.getmetrics()
            d.rectangle([BOX_X, PLATE_TOP, BOX_X + _M.textlength(self.title, font=f) + 2 * PX, PLATE_TOP + h], fill=c["bg"])
            d.text((BOX_X + PX, PLATE_TOP + (h - (a + b)) / 2), self.title, font=f, fill=c["accent"])
            cnt = f"{k + 1} / {len(self.steps)}"
            fc = F("num", 40)
            wc = _M.textlength(cnt, font=fc) + 2 * PX
            a, b = fc.getmetrics()
            d.rectangle([W - BOX_X - wc, PLATE_TOP, W - BOX_X, PLATE_TOP + h], fill=c["bg"])
            d.text((W - BOX_X - wc + PX, PLATE_TOP + (h - (a + b)) / 2), cnt, font=fc, fill=c["line"])
        draw_rows(d, self.rows[k], t, t0=t0)
        if li == shot.n - 1:
            shot.close()
        return img

    def bg(self):
        if self.skin not in self._bgs:
            c = BLUE_SKINS[self.skin]
            img = Image.new("RGB", (W, H), c["bg"])
            d = ImageDraw.Draw(img)
            for x in range(0, W, 60):
                d.line([x, 0, x, H], fill=c["grid"], width=3 if x % 300 == 0 else 1)
            for y in range(0, H, 60):
                d.line([0, y, W, y], fill=c["grid"], width=3 if y % 300 == 0 else 1)
            self._bgs[self.skin] = img
        return self._bgs[self.skin].copy()

    def frame(self, i, n):
        global K
        K = c = BLUE_SKINS[self.skin]
        t = i / FPS
        if t < self.hook_s and -1 in self.shots:
            return self._plate(-1, i, t)
        if t >= self.hook_s:
            now = max(k for k, s in enumerate(self.starts) if s <= t)
            if now in self.shots:
                return self._plate(now, i, t)
        img = self.bg()
        d = ImageDraw.Draw(img)
        wordmark(d, c["mark"])
        if t < self.hook_s:
            f, rows = fit(self.hook, "num", INNER, 170, 90, 5, 1.02)
            y = BAND_T + 70
            p0 = ease_out(prog(t, 0, 0.3))
            d.line([SAFE, y - 34, SAFE + INNER * p0, y - 34], fill=c["accent"], width=4)
            d.line([SAFE, y - 50, SAFE, y - 18], fill=c["accent"], width=4)
            if p0 >= 1: d.line([W - SAFE, y - 50, W - SAFE, y - 18], fill=c["accent"], width=4)
            for k, ln in enumerate(rows):
                p = ease_out(prog(t, k * 0.07, 0.18))
                d.text((SAFE + (1 - p) * 30, y), ln, font=f, fill=c["line"]); y += f.size * 1.02
            fs, srows = fit(self.sub, "med", INNER, 50, 38, 3, 1.25)
            y += 64
            for ln in srows:
                d.text((SAFE, y), ln, font=fs, fill=c["accent"]); y += fs.size * 1.25
            return img

        cur = max(k for k, s in enumerate(self.starts) if s <= t)
        p = prog(t, self.starts[cur], 0.6)
        ft, _ = fit(self.title, "num", INNER - 130, 46, 30, 1)
        d.text((SAFE, BAND_T + (46 - ft.size) / 2), self.title, font=ft, fill=c["accent"])
        cnt = f"{cur + 1} / {len(self.steps)}"
        d.text((W - SAFE - _M.textlength(cnt, font=F("num", 46)), BAND_T), cnt, font=F("num", 46), fill=mix(c["bg"], c["line"], .6))
        d.line([SAFE, BAND_T + 64, W - SAFE, BAND_T + 64], fill=c["accent"], width=3)

        # the drawing, at twice the size and scaled down, so its lines are clean
        bx, by, bw, bh = SAFE - 20, BAND_T + 86, INNER + 40, self.BOX_H
        sub = Image.new("RGB", (bw * 2, bh * 2), c["panel"])
        self.diagram(ImageDraw.Draw(sub), bw * 2, bh * 2, cur, ease_out(p))
        img.paste(sub.resize((bw, bh), Image.LANCZOS), (bx, by))
        d.rectangle([bx, by, bx + bw, by + bh], outline=c["edge"], width=3)

        key, detail = self.steps[cur]
        q = ease_out(prog(t, self.starts[cur], 0.22))
        y = by + bh + 26 + (1 - q) * 20
        d.ellipse([SAFE, y + 4, SAFE + 72, y + 76], fill=c["accent"])
        num = str(cur + 1)
        d.text((SAFE + 36 - _M.textlength(num, font=F("num", 50)) / 2, y + 11), num, font=F("num", 50), fill=c["bg"])
        fk, _ = fit(key, "head", INNER - 100, 72, 44, 1)
        d.text((SAFE + 96, y + (76 - fk.size) / 2 - 4), key, font=fk, fill=c["accent"])
        fd, rows = fit(detail, "med", INNER, 56, 38, 3, 1.22, BAND_B + 30 - (y + 98))
        yy = y + 98
        for ln in rows:
            d.text((SAFE, yy), ln, font=fd, fill=c["line"]); yy += fd.size * 1.22
        return img


def _centre(d, text, y, w, size, fill):
    f = F("num", size)
    d.text((w / 2 - _M.textlength(text, font=f) / 2, y), text, font=f, fill=fill)


def _dot(d, cx, cy, n, active, p):
    r = 40
    if active:
        rr = r + 14 + 26 * p
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=K["hot"], width=6)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=K["hot"] if active else K["mute"])
    s, f = str(n), F("num", 54)
    d.text((cx - _M.textlength(s, font=f) / 2, cy - 33), s, font=f, fill=K["panel"])


def jersey_outline(long=False):
    if long:
        return [(.40, .04), (.24, .09), (.01, .70), (.11, .74), (.27, .33), (.27, .97), (.73, .97),
                (.73, .33), (.89, .74), (.99, .70), (.76, .09), (.60, .04), (.50, .13)]
    return [(.40, .04), (.24, .09), (.03, .27), (.12, .41), (.27, .31), (.27, .97), (.73, .97),
            (.73, .31), (.88, .41), (.97, .27), (.76, .09), (.60, .04), (.50, .13)]


def jersey_diagram(anchors, long=False):
    """A shirt with numbered points lighting up one step at a time."""
    def fn(d, w, h, k, p):
        jh = h * 0.88
        jw = jh * (1.0 if long else 0.94)
        x0, y0 = (w - jw) / 2, h * 0.06
        P = lambda u, v: (x0 + u * jw, y0 + v * jh)
        pts = [P(u, v) for u, v in jersey_outline(long)]
        d.line(pts + [pts[0]], fill=K["line"], width=9, joint="curve")
        d.line([P(.27, .92), P(.73, .92)], fill=K["dim"], width=4)             # hem stitch
        for j, (u, v) in enumerate(anchors[:k + 1]):
            cx, cy = P(u, v)
            _dot(d, cx, cy, j + 1, j == k, p)
    return fn


def layers_diagram():
    """Fabric in cross-section, and where each decoration method puts its mark."""
    def fn(d, w, h, k, p):
        fx0, fx1, fy0, fy1 = w * .10, w * .90, h * .50, h * .74
        d.rounded_rectangle([fx0, fy0, fx1, fy1], radius=18, fill=K["fab"], outline=K["line"], width=6)
        for x in range(int(fx0) + 40, int(fx1) - 20, 46):                      # the knit
            d.line([x, fy0 + 22, x, fy1 - 22], fill=K["knit"], width=5)
        d.text((fx0, fy1 + 26), "FABRIC, IN CROSS-SECTION", font=F("num", 52), fill=K["dim"])
        a, b = w * .28, w * .28 + (w * .44) * p
        hot = K["hot"]
        if k == 0:        # ink inside the fibre
            d.rectangle([a, fy0 + 10, b, fy1 - 10], fill=hot)
            for x in range(int(a) + 22, int(b), 46):
                d.line([x, fy0 + 22, x, fy1 - 22], fill=mix(hot, (0, 0, 0), .25), width=5)
        elif k == 1:      # thread on top, stitched through
            x = a
            while x < b - 20:
                d.ellipse([x, fy0 - 62, x + 64, fy0 + 30], fill=hot, outline=K["panel"], width=4)
                d.line([x + 32, fy0, x + 32, fy1 - 14], fill=hot, width=7)
                x += 66
        elif k == 2:      # a thin film, bonded on
            d.rectangle([a, fy0 - 26, b, fy0], fill=hot)
        else:             # ink sitting on the surface
            d.rounded_rectangle([a, fy0 - 54, max(a + 40, b), fy0], radius=26, fill=hot)
        names = ["INSIDE THE FIBRE", "RAISED, ON TOP", "A FILM ON TOP", "ON THE SURFACE"]
        d.line([w * .50, fy0 - 96, w * .50, h * .22], fill=hot, width=5)
        _centre(d, names[k], h * .09, w, 64, hot)
    return fn


def seam_diagram():
    def fn(d, w, h, k, p):
        fab, cy, hot, line = K["fab"], h * .52, K["hot"], K["line"]
        if k == 0:        # flatlock: two edges butted, stitched flat
            d.rectangle([w * .08, cy - 80, w * .497, cy + 80], fill=fab, outline=line, width=8)
            d.rectangle([w * .503, cy - 80, w * .92, cy + 80], fill=fab, outline=line, width=8)
            xs = [w * .36 + j * (w * .28 / 10) for j in range(int(11 * p) + 1)]
            zz = [(x, cy - 66 if j % 2 == 0 else cy + 66) for j, x in enumerate(xs)]
            if len(zz) > 1: d.line(zz, fill=hot, width=14, joint="curve")
            d.line([w * .08, cy + 150, w * .92, cy + 150], fill=K["dim"], width=6)
            lab, sub_ = "FLATLOCK", "FLAT AGAINST THE SKIN"
        elif k == 1:      # overlock: both layers turned in, a ridge inside
            ridge = 230 * p
            cy -= 110
            d.rectangle([w * .08, cy - 80, w * .44, cy + 80], fill=fab, outline=line, width=8)
            d.rectangle([w * .56, cy - 80, w * .92, cy + 80], fill=fab, outline=line, width=8)
            d.rectangle([w * .44 - 4, cy - 80, w * .497, cy + 80 + ridge], fill=fab, outline=line, width=8)
            d.rectangle([w * .503, cy - 80, w * .56 + 4, cy + 80 + ridge], fill=fab, outline=line, width=8)
            for j in range(int(5 * p) + 1):
                yy = cy + 96 + j * (ridge / 6)
                d.arc([w * .41, yy, w * .59, yy + 70], 0, 180, fill=hot, width=14)
            lab, sub_ = "OVERLOCK", "A RIDGE ON THE INSIDE"
        else:             # where it sits on the shirt
            jh = h * 0.80; jw = jh * 0.94; x0, y0 = (w - jw) / 2, h * 0.16
            P = lambda u, v: (x0 + u * jw, y0 + v * jh)
            pts = [P(u, v) for u, v in jersey_outline()]
            d.line(pts + [pts[0]], fill=line, width=9, joint="curve")
            for (a, b) in (((.24, .09), (.40, .04)), ((.76, .09), (.60, .04)),
                           ((.27, .31), (.27, .97)), ((.73, .31), (.73, .97))):
                A, B = P(*a), P(*b)
                d.line([A, (A[0] + (B[0] - A[0]) * p, A[1] + (B[1] - A[1]) * p)], fill=hot, width=16)
            lab, sub_ = ("SHOULDERS AND SIDES", "") if k == 2 else ("WRITE IT DOWN", "")
        _centre(d, lab, h * .06, w, 70, hot)
        if sub_:
            _centre(d, sub_, h * .86, w, 50, K["dim"])
    return fn


def flow_diagram(nodes):
    """A chain of stages, top to bottom; the current one is lit."""
    def fn(d, w, h, k, p):
        n, gap = len(nodes), 34
        nh = (h * .90 - gap * (n - 1)) / n
        y = h * .05
        for j, name in enumerate(nodes):
            x0, x1 = w * .10, w * .90
            if j == k:
                d.rounded_rectangle([x0, y, x1, y + nh], radius=22, fill=mix(K["panel"], K["hot"], p), outline=K["hot"], width=6)
                col = K["panel"]
            elif j < k:
                d.rounded_rectangle([x0, y, x1, y + nh], radius=22, fill=K["fab"], outline=K["line"], width=5)
                col = K["line"]
            else:
                d.rounded_rectangle([x0, y, x1, y + nh], radius=22, outline=K["mute"], width=4)
                col = K["mute"]
            f = F("num", min(70, nh * .50))
            d.text((x0 + 44, y + (nh - f.size) / 2 - 6), f"{j + 1}   {name}", font=f, fill=col)
            if j < n - 1:
                d.line([w * .5, y + nh + 4, w * .5, y + nh + gap - 4], fill=K["line"] if j < k else K["mute"], width=6)
            y += nh + gap
    return fn


def bars_diagram(labels, note="ORDER, NOT SCALE"):
    """A ranking: the longest bar first. The lengths show order only, and the
    drawing says so — there is no measured number behind them."""
    def fn(d, w, h, k, p):
        n, gap = len(labels), 26
        bh = (h * .82 - gap * (n - 1)) / n
        y = h * .05
        for j, name in enumerate(labels):
            full = w * (.80 - .085 * j)
            if j <= k:
                wd = full * (p if j == k else 1.0)
                d.rounded_rectangle([w * .08, y, w * .08 + max(wd, 30), y + bh], radius=14,
                                    fill=K["hot"] if j == k else K["fab"], outline=None if j == k else K["line"], width=4)
                f = F("num", min(64, bh * .52))
                d.text((w * .08 + 30, y + (bh - f.size) / 2 - 6), f"{j + 1}  {name}", font=f,
                       fill=K["panel"] if j == k else K["line"])
            else:
                d.rounded_rectangle([w * .08, y, w * .08 + full, y + bh], radius=14, outline=K["mute"], width=3)
            y += bh + gap
        d.text((w * .08, h * .91), note, font=F("num", 44), fill=K["dim"])
    return fn


def checklist_diagram(labels):
    """Rows that get ticked as the reel goes."""
    def fn(d, w, h, k, p):
        n, gap = len(labels), 18
        rh = (h * .92 - gap * (n - 1)) / n
        y = h * .04
        for j, name in enumerate(labels):
            s = rh * .62
            bx, bycc = w * .08, y + (rh - s) / 2
            col = K["hot"] if j == k else K["line"] if j < k else K["mute"]
            d.rounded_rectangle([bx, bycc, bx + s, bycc + s], radius=10, outline=col, width=6)
            if j < k: tick_mark(d, bx, bycc, s, 1.0, K["hot"], 10)
            elif j == k: tick_mark(d, bx, bycc, s, p, K["hot"], 10)
            f = F("num", min(66, rh * .56))
            d.text((bx + s + 36, y + (rh - f.size) / 2 - 6), name, font=f, fill=col)
            y += rh + gap
    return fn


def flags_diagram(labels):
    """Warning signs, lit one at a time."""
    def fn(d, w, h, k, p):
        n = len(labels)
        cw = w * .84 / n
        for j, name in enumerate(labels):
            cx, top, s = w * .08 + cw * (j + .5), h * .16, min(cw * .78, h * .52)
            lit = j <= k
            col = K["hot"] if j == k else K["line"] if j < k else K["mute"]
            tri = [(cx, top), (cx - s / 2, top + s * .9), (cx + s / 2, top + s * .9)]
            if j == k:
                d.polygon(tri, fill=mix(K["panel"], K["hot"], p))
            d.line(tri + [tri[0]], fill=col, width=10, joint="curve")
            f = F("num", s * .46)
            mk = "!" if lit else str(j + 1)
            d.text((cx - _M.textlength(mk, font=f) / 2, top + s * .30), mk, font=f,
                   fill=K["panel"] if j == k else col)
            fl = F("num", min(54, cw * .19))
            d.text((cx - _M.textlength(name, font=fl) / 2, top + s * .9 + 40), name, font=fl, fill=col)
    return fn


def swatch_diagram(kinds):
    """A square of each fabric, drawn as its structure."""
    def fn(d, w, h, k, p):
        kind = kinds[k]
        s = h * .74
        x0, y0 = (w - s) / 2, h * .06
        line, hot = K["line"], K["hot"]
        d.rectangle([x0, y0, x0 + s, y0 + s], fill=K["fab"], outline=line, width=8)
        step = s / 12
        if kind == "interlock":            # dense, both directions
            for j in range(-11, 12):
                o = j * step
                d.line([x0 + max(0, o), y0 + max(0, -o), x0 + min(s, s + o), y0 + min(s, s - o)], fill=K["knit"], width=5)
                d.line([x0 + min(s, s + o), y0 + max(0, o), x0 + max(0, o), y0 + min(s, s + o)], fill=K["knit"], width=5)
        elif kind == "jersey":             # columns of V stitches
            for cx in range(12):
                for cy in range(12):
                    ax, ay = x0 + cx * step, y0 + cy * step
                    d.line([ax + step * .15, ay + step * .1, ax + step * .5, ay + step * .85, ax + step * .85, ay + step * .1], fill=K["knit"], width=5)
        elif kind == "pique":              # waffle
            for cx in range(8):
                for cy in range(8):
                    ax = x0 + cx * s / 8 + (s / 16 if cy % 2 else 0)
                    ay = y0 + cy * s / 8
                    if ax + s / 10 <= x0 + s:
                        d.rectangle([ax + 8, ay + 8, ax + s / 10, ay + s / 10], outline=K["knit"], width=6)
        elif kind == "mesh":               # holes
            for cx in range(9):
                for cy in range(9):
                    ax, ay = x0 + (cx + .5) * s / 9, y0 + (cy + .5) * s / 9
                    r = s / 34
                    d.ellipse([ax - r, ay - r, ax + r, ay + r], fill=K["panel"], outline=K["knit"], width=4)
        elif kind == "jacquard":           # a motif knitted in
            for cx in range(5):
                for cy in range(5):
                    ax, ay, r = x0 + (cx + .5) * s / 5, y0 + (cy + .5) * s / 5, s / 14
                    d.polygon([(ax, ay - r), (ax + r, ay), (ax, ay + r), (ax - r, ay)],
                              fill=hot if (cx + cy) % 2 == 0 else K["knit"])
        else:                              # recovery: pulled out, and back
            d.rectangle([x0, y0, x0 + s, y0 + s], fill=K["panel"])
            pull = math.sin(min(1.0, p * 1.6) * math.pi) * s * .16
            d.rectangle([x0 - pull, y0 + s * .3, x0 + s + pull, y0 + s * .7], fill=K["fab"], outline=line, width=8)
            for sx in (-1, 1):
                ax = w / 2 + sx * (s / 2 + pull + 50)
                d.line([ax, y0 + s * .5, ax + sx * 90, y0 + s * .5], fill=hot, width=10)
                d.polygon([(ax + sx * 120, y0 + s * .5), (ax + sx * 84, y0 + s * .5 - 26), (ax + sx * 84, y0 + s * .5 + 26)], fill=hot)
        if kind != "recovery":
            d.rectangle([x0, y0, x0 + s, y0 + s], outline=line, width=8)
        _centre(d, f"{k + 1} OF {len(kinds)}", h * .88, w, 48, K["dim"])
    return fn


def press_diagram():
    """Sublimation: a printed paper on blank polyester, heat, and the ink
    moving from one into the other."""
    def fn(d, w, h, k, p):
        line, hot = K["line"], K["hot"]
        fx0, fx1 = w * .12, w * .88
        fab_t, fab_b = h * .56, h * .80
        grey = mix(K["panel"], line, .5)
        # the fabric
        inked = 0.0 if k == 0 else p if k == 1 else 1.0
        d.rounded_rectangle([fx0, fab_t, fx1, fab_b], radius=14, fill=K["fab"], outline=line, width=6)
        if inked > 0:
            d.rectangle([fx0 + 30, fab_t + 12, fx1 - 30, fab_t + 12 + (fab_b - fab_t - 24) * inked], fill=hot)
        for x in range(int(fx0) + 40, int(fx1) - 20, 46):
            d.line([x, fab_t + 22, x, fab_b - 22], fill=K["knit"] if inked < .5 else mix(hot, (0, 0, 0), .25), width=5)
        # the paper
        lift = 0 if k < 2 else (h * .26 * p if k == 2 else h * .9)
        py1 = fab_t - 14 - lift
        py0 = py1 - h * .10
        if py1 > 0:
            col = hot if k == 0 else mix(hot, grey, p) if k == 1 else grey
            d.rectangle([fx0 + 30, py0, fx1 - 30, py1], fill=col, outline=line, width=6)
        # the heat
        if k == 1:
            for j in range(7):
                x = fx0 + 80 + j * (fx1 - fx0 - 160) / 6
                d.line([x, h * .16, x, h * .16 + h * .16 * p], fill=hot, width=10)
                d.polygon([(x, h * .16 + h * .16 * p + 34), (x - 24, h * .16 + h * .16 * p), (x + 24, h * .16 + h * .16 * p)], fill=hot)
        lab = ["PAPER ON POLYESTER", "200°C · 60 SECONDS", "THE PAPER COMES OFF GREY", "THE COLOUR IS IN THE FIBRE"][k]
        _centre(d, lab, h * .04, w, 62, hot)
        d.text((fx0, fab_b + 22), "POLYESTER, IN CROSS-SECTION", font=F("num", 46), fill=K["dim"])
    return fn


# ══════════════════════════════════════════════════════════════════ doc ═════
class DocShot(Shot):
    """Library footage in black and white, one word in amber over it.

    The colour is taken out on purpose: four clips in their own colours look
    like the same four clips; graded to one tone with a slow push they read as
    a single film. The library-footage label is drawn before the grade, so it
    stays on the frame.
    """

    def __init__(self, path, seconds, big, small=None, chip=None, **kw):
        kw.setdefault("zoom", 1.12); kw.setdefault("blur_edge", 0); kw.setdefault("scrim", 0.0)
        super().__init__(path, seconds, overlay=None, **kw)
        self.big = big if isinstance(big, (list, tuple)) else [big]
        self.small, self.chip = small, chip

    def frame(self, i, n):
        img = super().frame(i, n)
        img = ImageOps.colorize(ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1),
                                (6, 9, 8), (240, 235, 224))
        d = ImageDraw.Draw(img)
        t = i / FPS
        if self.chip:
            d.text((SAFE, LABEL_Y + 64), self.chip, font=F("num", 50), fill=AMBER,
                   stroke_width=5, stroke_fill=(0, 0, 0))
        sizes = [min(250, 200 * INNER / _M.textlength(ln, font=F("head", 200))) for ln in self.big]
        y = H * 0.33 if self.small else H * 0.36
        for k, ln in enumerate(self.big):
            p = ease_out(prog(t, k * 0.08, 0.2))
            f = F("head", sizes[k] * (1.08 - 0.08 * p))
            b = d.textbbox((0, 0), ln, font=f)
            d.text((SAFE - b[0], y - b[1]), ln, font=f, fill=AMBER, stroke_width=8, stroke_fill=(0, 0, 0))
            y += (b[3] - b[1]) + 30
        if self.small:
            p = ease_out(prog(t, 0.25, 0.25))
            f, rows = fit(self.small, "bold", INNER, 54, 40, 4, 1.22)
            y += 14 + (1 - p) * 16
            for ln in rows:
                if p > 0.05:
                    d.text((SAFE, y), ln, font=f, fill=(250, 248, 240), stroke_width=4, stroke_fill=(0, 0, 0))
                y += f.size * 1.22
        return img


# ═════════════════════════════════════════════════════════ real footage ═════
# 15 Nov, night: "i like the videos vibe ... but i want more real life videos of
# factory videos, such as cutting, stitching." So the three families keep their
# look and real footage is cut into them: the hook plays over a moving plate,
# and lines that describe a process play over that process.
#
# The footage is licensed library footage, not SoccerTex's floor, and three
# rules keep it honest:
#   1. every plate carries the "Library footage" stamp (engine/reel.py);
#   2. nothing in SoccerTex's own voice — we, our, us, the name — is ever set
#      over it (`stock_ok` raises before a frame is drawn);
#   3. a line only goes over a clip that shows what the line is about, or over
#      a neutral close-up. That one is editorial, and lives in build_vibes.py.
import re
from pathlib import Path
from engine.footage import guard, StockMisuse

PROXY = Path(__file__).resolve().parent.parent / "assets" / "footage" / "proxy"
OWN_VOICE = re.compile(r"\b(we|we're|we'll|we've|we'd|our|ours|us)\b|soccertex", re.I)
PX = 22                                  # padding inside a type box
BOX_X = SAFE - 12                        # lines up with the library stamp
TEXT_W = W - 2 * BOX_X - 2 * PX
PLATE_TOP = LABEL_Y + 46 + 22            # nothing rides over the stamp


def stock_ok(*texts):
    """Refuse SoccerTex's own voice over somebody else's factory."""
    for t in texts:
        if not t:
            continue
        s = " ".join(t) if isinstance(t, (list, tuple)) else str(t)
        guard(s, "stock")
        m = OWN_VOICE.search(s)
        if m:
            raise StockMisuse(f"{m.group(0)!r} in {s!r}: SoccerTex's own voice cannot sit over "
                              f"library footage. Keep that line on a drawn card.")


def clip(name, start=0.0, tight=1.0, focus=(0.5, 0.5), mirror=False, zoom=1.07):
    """A piece of a library clip: which one, from when, and how it is framed."""
    p = PROXY / f"{name}.mp4"
    if not p.exists():
        raise FileNotFoundError(f"{p} — see assets/footage/README.md")
    return dict(path=p, start=start, tight=tight, focus=focus, mirror=mirror, zoom=zoom)


def _easy(shot):
    """A push of a few percent needs no sharpening pass — it is invisible, and
    the pass is the slowest thing in the frame."""
    if shot.stretch <= 1.10:
        shot.stretch = 1.0
    return shot


def open_clip(spec, seconds):
    """The clip as a bare moving picture, stamp included, no type."""
    return _easy(Shot(spec["path"], seconds, overlay=None, blur_edge=0, scrim=0.0,
                      **{k: spec[k] for k in ("start", "tight", "focus", "mirror", "zoom")}))


def type_rows(lines=None, text=None, sub=None, n=None, chip=None, colours=(INK, BONE, AMBER),
              hi=None, kind="head", big=150, room=600, tmax=84):
    """Type for a plate, as rows of (string, font, box, ink). Slam lines share
    one size so the right edge stays ragged and the footage shows past it."""
    bg, fg, accent = colours
    pop = accent if accent != bg else fg
    rows = []
    if chip:
        f, wrapped = fit(chip, "num", TEXT_W, 46, 30, 2, 1.0)
        rows += [(ln, f, bg, pop, 8 if k == len(wrapped) - 1 else 0) for k, ln in enumerate(wrapped)]
    if n is not None:
        rows.append((str(n), F("num", 130), pop, bg, 0))
    sub_rows = []
    if sub:
        f, wrapped = fit(sub, "med", TEXT_W, 46, 34, 3, 1.0)
        sub_rows = [(ln, f, pop, bg, 0) for ln in wrapped]
    left = room - sum(r[1].size * 1.3 + r[4] for r in rows + sub_rows)
    if lines:
        size = min([big] + [200 * TEXT_W / max(1, _M.textlength(ln, font=F(kind, 200))) for ln in lines])
        size = min(size, left / (len(lines) * 1.3))
        rows += [(ln, F(kind, size), bg, accent if (k == hi and accent != bg) else fg,
                  10 if (k == len(lines) - 1 and sub_rows) else 0) for k, ln in enumerate(lines)]
    if text:
        f, wrapped = fit(text, kind, TEXT_W, tmax, 46, 6, 1.3, left)
        rows += [(ln, f, bg, fg, 10 if (k == len(wrapped) - 1 and sub_rows) else 0)
                 for k, ln in enumerate(wrapped)]
    return rows + sub_rows


def draw_rows(d, rows, t, bottom=BAND_B - 6, align="left", motion="pop", stagger=0.07, t0=0.0):
    """Stack the rows upward from `bottom`, each in its own tight box."""
    hs = [int(r[1].size * 1.3) for r in rows]
    y = bottom - sum(hs) - sum(r[4] for r in rows)
    if y < PLATE_TOP:
        raise ValueError(f"type runs {PLATE_TOP - y:.0f}px over the library stamp: {[r[0] for r in rows]}")
    for k, ((s, f, box, ink, gap), h) in enumerate(zip(rows, hs)):
        tk = t0 + k * stagger
        if t >= tk:
            p = ease_out(prog(t, tk, 0.18))
            w = _M.textlength(s, font=f) + 2 * PX
            x = BOX_X if align == "left" else (W - w) / 2
            dx = -(1 - p) * 60 if motion == "pop" else 0
            dy = (1 - p) * 44 if motion == "rise" else 0
            d.rectangle([x + dx, y + dy, x + dx + w, y + dy + h + 1], fill=box)
            a, b = f.getmetrics()
            d.text((x + dx + PX, y + dy + (h - (a + b)) / 2), s, font=f, fill=ink)
        y += h + gap


class Plate(Shot):
    """Real footage, full frame and in its own colours, with the reel's type
    set over it in tight boxes of the reel's colourway."""

    def __init__(self, spec, lines=None, text=None, sub=None, n=None, chip=None,
                 colours=(INK, BONE, AMBER), hi=None, kind="head", align="left", motion="pop",
                 seconds=None, pace=1.0, big=150):
        stock_ok(lines, text, sub, chip)
        if seconds is None:
            if lines:
                seconds = (0.6 + 0.34 * len(lines) + (read_secs(sub) * 0.75 if sub else 0.35)) * pace
            elif text:
                seconds = (read_secs(text) + 0.45) * pace
            else:
                seconds = 1.1 * pace
        seconds = max(1.0, min(3.8, seconds))
        super().__init__(spec["path"], seconds, overlay=None, blur_edge=0, scrim=0.0,
                         **{k: spec[k] for k in ("start", "tight", "focus", "mirror", "zoom")})
        self.rows = type_rows(lines, text, sub, n, chip, colours, hi, kind, big)
        self.align, self.motion = align, motion
        _easy(self)

    def frame(self, i, n):
        img = super().frame(i, n)
        draw_rows(ImageDraw.Draw(img), self.rows, i / FPS, align=self.align, motion=self.motion)
        return img


class Breaks(Scene):
    """Lets real footage interrupt a drawn scene. At each `(when, plate)` the
    drawn scene holds exactly where it is, the plate plays, and it carries on."""

    def __init__(self, inner, breaks):
        self.inner, self.parts, at, out = inner, [], 0, 0
        self.marks = []
        shift = 0.0
        pending = sorted(getattr(inner, "marks", ()))
        for when, plate in sorted(breaks, key=lambda b: b[0]):
            f = min(inner.n, int(when * FPS))
            if f > at:
                self.parts.append((out, f - at, None, at)); out += f - at
            self.marks += [m + shift for m in pending if m < when]
            pending = [m for m in pending if m >= when]
            self.marks += [out / FPS, (out + plate.n) / FPS]
            self.parts.append((out, plate.n, plate, 0)); out += plate.n
            shift += plate.n / FPS
            at = f
        if inner.n > at:
            self.parts.append((out, inner.n - at, None, at)); out += inner.n - at
        self.marks += [m + shift for m in pending]
        self.n = out

    def frame(self, i, n):
        for start, length, plate, base in self.parts:
            if start <= i < start + length:
                if plate is None:
                    return self.inner.frame(base + i - start, self.inner.n)
                img = plate.frame(i - start, plate.n)
                if i - start == length - 1:
                    plate.close()
                return img
        raise IndexError(i)

    def close(self):
        self.inner.close()
        for _, _, plate, _ in self.parts:
            if plate is not None:
                plate.close()
