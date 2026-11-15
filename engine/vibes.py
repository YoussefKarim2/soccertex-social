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


class Slam(Scene):
    """Lines of type, each set as wide as the frame, landing one at a time."""

    def __init__(self, lines, sub=None, bg=INK, fg=BONE, accent=AMBER, hi=None, seconds=None, stagger=0.10):
        self.lines, self.sub, self.bg, self.fg, self.accent, self.hi = lines, sub, bg, fg, accent, hi
        self.stagger = stagger
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
            seconds = 0.55 + 0.34 * len(lines) + (read_secs(sub) * 0.75 if sub else 0.35)
        super().__init__(max(1.3, min(3.6, seconds)))

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
                # it lands slightly small and grows to size — never past the
                # margins, which a shrink-from-large pop did on every wide line
                sc = 0.90 + 0.10 * ease_out(prog(t, tk, 0.14))
                f = F("head", self.sizes[k] * sc)
                b = d.textbbox((0, 0), ln, font=f)
                dy = (self.heights[k] - (b[3] - b[1])) / 2
                d.text((SAFE - b[0], y - b[1] + dy), ln, font=f,
                       fill=self.accent if k == self.hi else self.fg)
            y += self.heights[k] + 24
        if self.sub:
            ts = len(self.lines) * self.stagger + 0.1
            p = ease_out(prog(t, ts, 0.25))
            f, rows = fit(self.sub, "med", INNER, 50, 38, 3, 1.25)
            yy = y + 14
            for ln in rows:
                d.text((SAFE, yy + (1 - p) * 16), ln, font=f, fill=mix(self.bg, self.fg, 0.85 * p))
                yy += f.size * 1.25
        wordmark(d, mix(self.bg, self.fg, 0.30))
        return img


class Say(Scene):
    """One sentence, big, with an optional numeral. For lines too long to slam."""

    def __init__(self, text, n=None, bg=INK, fg=BONE, accent=AMBER, seconds=None):
        self.text, self.num, self.bg, self.fg, self.accent = text, n, bg, fg, accent
        self.top = BAND_T + (250 if n is not None else 40)
        self.f, self.rows = fit(text, "head", INNER, 100, 56, 6, 1.14, BAND_B - self.top - 50)
        super().__init__(seconds or read_secs(text) + 0.45)

    def frame(self, i, n):
        t = i / FPS
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        if self.num is not None:
            p = ease_out(prog(t, 0, 0.18))
            fn = F("num", 300 - 40 * (1 - p))
            d.text((SAFE - 8, BAND_T - 60), str(self.num), font=fn, fill=self.accent)
        y = self.top
        if self.num is None:
            y = BAND_T + ((BAND_B - BAND_T) - len(self.rows) * self.f.size * 1.14) / 2 - 20
        for k, ln in enumerate(self.rows):
            p = ease_out(prog(t, 0.06 + k * 0.06, 0.2))
            d.text((SAFE + (1 - p) * 30, y), ln, font=self.f, fill=mix(self.bg, self.fg, p))
            y += self.f.size * 1.14
        sp = ease_out(prog(t, 0.3, 0.3))
        d.rectangle([SAFE, y + 22, SAFE + int(200 * sp), y + 32], fill=self.accent)
        wordmark(d, mix(self.bg, self.fg, 0.30))
        return img


class Count(Scene):
    """A number that counts up to itself, with what it is underneath."""

    def __init__(self, value, suffix, label, note=None, bg=AMBER, fg=INK, accent=INK, seconds=None):
        self.value, self.suffix, self.label, self.note = value, suffix, label, note
        self.bg, self.fg, self.accent = bg, fg, accent
        final = f"{value:,}{suffix}"
        self.size = min(460, 200 * INNER / max(1, _M.textlength(final, font=F("num", 200))))
        super().__init__(seconds or 1.5 + read_secs(label + " " + (note or ""), lo=1.2) * 0.8)

    def frame(self, i, n):
        t = i / FPS
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        v = int(round(self.value * ease_out(prog(t, 0.05, 0.9))))
        f = F("num", self.size)
        b = d.textbbox((0, 0), f"{self.value:,}{self.suffix}", font=f)
        y = BAND_T + 30
        d.text((SAFE - b[0], y - b[1]), f"{v:,}{self.suffix}", font=f, fill=self.accent)
        y += (b[3] - b[1]) + 50
        p = ease_out(prog(t, 0.7, 0.3))
        fl, rows = fit(self.label, "head", INNER, 66, 46, 3, 1.12)
        for ln in rows:
            d.text((SAFE, y + (1 - p) * 20), ln, font=fl, fill=mix(self.bg, self.fg, p))
            y += fl.size * 1.12
        if self.note:
            p2 = ease_out(prog(t, 1.0, 0.3))
            fnote, rows = fit(self.note, "med", INNER, 46, 36, 3, 1.28)
            y += 22
            for ln in rows:
                d.text((SAFE, y), ln, font=fnote, fill=mix(self.bg, self.fg, 0.8 * p2))
                y += fnote.size * 1.28
        wordmark(d, mix(self.bg, self.fg, 0.30))
        return img


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
class VersusScene(Scene):
    """Two columns of an argument, revealed a row from each side at a time."""
    BG, RED, GRN = (15, 17, 19), (226, 84, 60), (36, 178, 94)
    PA, PB, TXT = (44, 24, 22), (18, 44, 30), (242, 242, 238)

    def __init__(self, hook, sub, title, a, b, final=None, hook_s=2.1):
        self.hook, self.sub, self.title, self.final, self.hook_s = hook, sub, title, final, hook_s
        (self.la, self.ra), (self.lb, self.rb) = a, b
        t, self.ta, self.tb = hook_s + 0.25, [], []
        for k in range(max(len(self.ra), len(self.rb))):
            if k < len(self.ra): self.ta.append(t); t += read_secs(self.ra[k]) * 0.75
            if k < len(self.rb): self.tb.append(t); t += read_secs(self.rb[k]) * 0.9
        self.end_t = t + 0.2
        self.marks = [hook_s] + self.ta + self.tb
        super().__init__(self.end_t + (read_secs(final) + 0.7 if final else 0.9))

    def frame(self, i, n):
        t = i / FPS
        img = Image.new("RGB", (W, H), self.BG)
        d = ImageDraw.Draw(img)
        if t < self.hook_s:
            mid = int(H * 0.47)
            d.rectangle([0, 0, W, mid], fill=self.PA)
            d.rectangle([0, mid, W, H], fill=self.PB)
            d.rectangle([0, mid - 4, W, mid + 4], fill=self.TXT)
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
                d.text((SAFE - b[0], y - b[1]), ln, font=f, fill=self.TXT)
                y += (hs[k][3] - hs[k][1]) + 26
            f, rows = fit(self.sub, "bold", INNER, 58, 40, 3, 1.22)
            y = mid + 50
            for ln in rows:
                d.text((SAFE, y), ln, font=f, fill=(214, 240, 222)); y += f.size * 1.22
            return img

        closing = self.final and t >= self.end_t
        head = self.final if closing else self.title
        f, rows = fit(head, "head" if closing else "num", INNER, 62 if closing else 56, 40, 2, 1.12)
        y = BAND_T
        for ln in rows:
            d.text((SAFE, y), ln, font=f, fill=self.GRN if closing else self.TXT); y += f.size * 1.12
        # the panels keep one position whether the heading above is the title
        # or the two-line closing statement — otherwise every row jumps and
        # shrinks at the moment it should be landing
        heights = [len(r) * ff.size * 1.12 for ff, r in (
            fit(self.title, "num", INNER, 56, 40, 2, 1.12),
            fit(self.final or self.title, "head", INNER, 62, 40, 2, 1.12))]
        top = BAND_T + max(heights) + 20
        ph = (BAND_B - top - 18) / 2
        nrow = max(len(self.ra), len(self.rb))
        rh = (ph - 78) / nrow
        size = int(min(54, rh * 0.40))
        wordmark(d, (70, 76, 80))
        for col, (label, rows_, times, panel, tone) in enumerate((
                (self.la, self.ra, self.ta, self.PA, self.RED),
                (self.lb, self.rb, self.tb, self.PB, self.GRN))):
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
                    d.text((x + s + 24, ty), ln, font=fr, fill=mix(panel, self.TXT, p)); ty += fr.size * 1.16
        return img


# ════════════════════════════════════════════════════════════ blueprint ═════
NAVY, GRIDC, LINE, CYAN, PANEL = (13, 36, 64), (26, 58, 96), (232, 244, 255), (118, 204, 255), (17, 48, 84)
HOT = (255, 190, 92)


class BlueprintScene(Scene):
    """A drafting sheet: a drawing in the upper box, the note for the current
    step underneath. `diagram(d, w, h, k, p)` draws the state for step k."""
    _bg = None
    BOX_H = 590

    def __init__(self, hook, sub, title, steps, diagram, hook_s=2.1):
        self.hook, self.sub, self.title, self.steps, self.diagram, self.hook_s = hook, sub, title, steps, diagram, hook_s
        t, self.starts = hook_s, []
        for key, detail in steps:
            self.starts.append(t); t += read_secs(key + " " + detail) + 0.45
        self.marks = list(self.starts)
        super().__init__(t + 0.5)

    @classmethod
    def bg(cls):
        if cls._bg is None:
            img = Image.new("RGB", (W, H), NAVY)
            d = ImageDraw.Draw(img)
            for x in range(0, W, 60):
                d.line([x, 0, x, H], fill=GRIDC, width=3 if x % 300 == 0 else 1)
            for y in range(0, H, 60):
                d.line([0, y, W, y], fill=GRIDC, width=3 if y % 300 == 0 else 1)
            cls._bg = img
        return cls._bg.copy()

    def frame(self, i, n):
        t = i / FPS
        img = self.bg()
        d = ImageDraw.Draw(img)
        if t < self.hook_s:
            f, rows = fit(self.hook, "num", INNER, 170, 90, 5, 1.02)
            y = BAND_T + 70
            p0 = ease_out(prog(t, 0, 0.3))
            d.line([SAFE, y - 34, SAFE + INNER * p0, y - 34], fill=CYAN, width=4)
            d.line([SAFE, y - 50, SAFE, y - 18], fill=CYAN, width=4)
            if p0 >= 1: d.line([W - SAFE, y - 50, W - SAFE, y - 18], fill=CYAN, width=4)
            for k, ln in enumerate(rows):
                p = ease_out(prog(t, k * 0.07, 0.18))
                d.text((SAFE + (1 - p) * 30, y), ln, font=f, fill=LINE); y += f.size * 1.02
            fs, srows = fit(self.sub, "med", INNER, 50, 38, 3, 1.25)
            y += 64
            for ln in srows:
                d.text((SAFE, y), ln, font=fs, fill=CYAN); y += fs.size * 1.25
            wordmark(d, (74, 112, 152))
            return img

        wordmark(d, (74, 112, 152))
        cur = max(k for k, s in enumerate(self.starts) if s <= t)
        p = prog(t, self.starts[cur], 0.6)
        d.text((SAFE, BAND_T), self.title, font=F("num", 46), fill=CYAN)
        cnt = f"{cur + 1} / {len(self.steps)}"
        d.text((W - SAFE - _M.textlength(cnt, font=F("num", 46)), BAND_T), cnt, font=F("num", 46), fill=(150, 176, 204))
        d.line([SAFE, BAND_T + 64, W - SAFE, BAND_T + 64], fill=CYAN, width=3)

        # the drawing, at twice the size and scaled down, so its lines are clean
        bx, by, bw, bh = SAFE - 20, BAND_T + 86, INNER + 40, self.BOX_H
        sub = Image.new("RGB", (bw * 2, bh * 2), PANEL)
        self.diagram(ImageDraw.Draw(sub), bw * 2, bh * 2, cur, ease_out(p))
        img.paste(sub.resize((bw, bh), Image.LANCZOS), (bx, by))
        d.rectangle([bx, by, bx + bw, by + bh], outline=(60, 104, 150), width=3)

        key, detail = self.steps[cur]
        q = ease_out(prog(t, self.starts[cur], 0.22))
        y = by + bh + 26 + (1 - q) * 20
        d.ellipse([SAFE, y + 4, SAFE + 72, y + 76], fill=CYAN)
        num = str(cur + 1)
        d.text((SAFE + 36 - _M.textlength(num, font=F("num", 50)) / 2, y + 11), num, font=F("num", 50), fill=NAVY)
        fk, _ = fit(key, "head", INNER - 100, 72, 44, 1)
        d.text((SAFE + 96, y + (76 - fk.size) / 2 - 4), key, font=fk, fill=CYAN)
        fd, rows = fit(detail, "med", INNER, 56, 38, 3, 1.22, BAND_B + 30 - (y + 98))
        yy = y + 98
        for ln in rows:
            d.text((SAFE, yy), ln, font=fd, fill=LINE); yy += fd.size * 1.22
        return img


def _dot(d, cx, cy, n, active, p, t_pulse=0.0):
    r = 40
    if active:
        rr = r + 14 + 26 * p
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=HOT, width=6)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=HOT if active else (86, 132, 176))
    s = str(n)
    f = F("num", 54)
    d.text((cx - _M.textlength(s, font=f) / 2, cy - 33), s, font=f, fill=NAVY)


def jersey_outline(long=False):
    if long:
        return [(.40, .04), (.24, .09), (.01, .70), (.11, .74), (.27, .33), (.27, .97), (.73, .97),
                (.73, .33), (.89, .74), (.99, .70), (.76, .09), (.60, .04), (.50, .13)]
    return [(.40, .04), (.24, .09), (.03, .27), (.12, .41), (.27, .31), (.27, .97), (.73, .97),
            (.73, .31), (.88, .41), (.97, .27), (.76, .09), (.60, .04), (.50, .13)]


def jersey_diagram(anchors, long=False, highlight=None):
    """A shirt with numbered points lighting up one step at a time.
    `highlight(d, P, k)` may draw extra marks for step k."""
    def fn(d, w, h, k, p):
        jh = h * 0.88
        jw = jh * (1.0 if long else 0.94)
        x0, y0 = (w - jw) / 2, h * 0.06
        P = lambda u, v: (x0 + u * jw, y0 + v * jh)
        pts = [P(u, v) for u, v in jersey_outline(long)]
        d.line(pts + [pts[0]], fill=LINE, width=9, joint="curve")
        d.line([P(.27, .92), P(.73, .92)], fill=(120, 160, 200), width=4)       # hem stitch
        if highlight: highlight(d, P, k, p)
        for j, (u, v) in enumerate(anchors[:k + 1]):
            cx, cy = P(u, v)
            _dot(d, cx, cy, j + 1, j == k, p)
    return fn


def layers_diagram():
    """Fabric in cross-section, and where each decoration method puts its mark."""
    def fn(d, w, h, k, p):
        fx0, fx1, fy0, fy1 = w * .10, w * .90, h * .50, h * .74
        d.rounded_rectangle([fx0, fy0, fx1, fy1], radius=18, fill=(46, 88, 132), outline=LINE, width=6)
        for x in range(int(fx0) + 40, int(fx1) - 20, 46):                      # the knit
            d.line([x, fy0 + 22, x, fy1 - 22], fill=(84, 128, 172), width=5)
        d.text((fx0, fy1 + 26), "FABRIC, IN CROSS-SECTION", font=F("num", 52), fill=(150, 176, 204))
        a, b = w * .28, w * .28 + (w * .44) * p
        if k == 0:        # ink inside the fibre
            d.rectangle([a, fy0 + 10, b, fy1 - 10], fill=HOT)
            for x in range(int(a) + 22, int(b), 46):
                d.line([x, fy0 + 22, x, fy1 - 22], fill=(196, 132, 40), width=5)
        elif k == 1:      # thread on top, stitched through
            x = a
            while x < b - 20:
                d.ellipse([x, fy0 - 62, x + 64, fy0 + 30], fill=HOT, outline=NAVY, width=4)
                d.line([x + 32, fy0, x + 32, fy1 - 14], fill=HOT, width=7)
                x += 66
        elif k == 2:      # a thin film, bonded on
            d.rectangle([a, fy0 - 26, b, fy0], fill=HOT)
        else:             # ink sitting on the surface
            d.rounded_rectangle([a, fy0 - 54, max(a + 40, b), fy0], radius=26, fill=HOT)
        names = ["INSIDE THE FIBRE", "RAISED, ON TOP", "A FILM ON TOP", "ON THE SURFACE"]
        d.line([w * .50, fy0 - 96, w * .50, h * .22], fill=HOT, width=5)
        tw_ = _M.textlength(names[k], font=F("num", 64))
        d.text((w * .50 - tw_ / 2, h * .09), names[k], font=F("num", 64), fill=HOT)
    return fn


def seam_diagram():
    def fn(d, w, h, k, p):
        fab, cy = (46, 88, 132), h * .52
        if k == 0:        # flatlock: two edges butted, stitched flat
            d.rectangle([w * .08, cy - 80, w * .497, cy + 80], fill=fab, outline=LINE, width=8)
            d.rectangle([w * .503, cy - 80, w * .92, cy + 80], fill=fab, outline=LINE, width=8)
            xs = [w * .36 + j * (w * .28 / 10) for j in range(int(11 * p) + 1)]
            zz = [(x, cy - 66 if j % 2 == 0 else cy + 66) for j, x in enumerate(xs)]
            if len(zz) > 1: d.line(zz, fill=HOT, width=14, joint="curve")
            d.line([w * .08, cy + 150, w * .92, cy + 150], fill=(150, 176, 204), width=6)
            lab, sub_ = "FLATLOCK", "FLAT AGAINST THE SKIN"
        elif k == 1:      # overlock: both layers turned in, a ridge inside
            ridge = 230 * p
            cy -= 110
            d.rectangle([w * .08, cy - 80, w * .44, cy + 80], fill=fab, outline=LINE, width=8)
            d.rectangle([w * .56, cy - 80, w * .92, cy + 80], fill=fab, outline=LINE, width=8)
            d.rectangle([w * .44 - 4, cy - 80, w * .497, cy + 80 + ridge], fill=fab, outline=LINE, width=8)
            d.rectangle([w * .503, cy - 80, w * .56 + 4, cy + 80 + ridge], fill=fab, outline=LINE, width=8)
            for j in range(int(5 * p) + 1):
                yy = cy + 96 + j * (ridge / 6)
                d.arc([w * .41, yy, w * .59, yy + 70], 0, 180, fill=HOT, width=14)
            lab, sub_ = "OVERLOCK", "A RIDGE ON THE INSIDE"
        else:             # where it sits on the shirt
            jh = h * 0.80; jw = jh * 0.94; x0, y0 = (w - jw) / 2, h * 0.16
            P = lambda u, v: (x0 + u * jw, y0 + v * jh)
            pts = [P(u, v) for u, v in jersey_outline()]
            d.line(pts + [pts[0]], fill=LINE, width=9, joint="curve")
            for (a, b) in (((.24, .09), (.40, .04)), ((.76, .09), (.60, .04)),
                           ((.27, .31), (.27, .97)), ((.73, .31), (.73, .97))):
                A, B = P(*a), P(*b)
                d.line([A, (A[0] + (B[0] - A[0]) * p, A[1] + (B[1] - A[1]) * p)], fill=HOT, width=16)
            lab, sub_ = ("SHOULDERS AND SIDES", "") if k == 2 else ("WRITE IT DOWN", "")
        f = F("num", 70)
        d.text((w / 2 - _M.textlength(lab, font=f) / 2, h * .06), lab, font=f, fill=HOT)
        if sub_:
            f2 = F("num", 50)
            d.text((w / 2 - _M.textlength(sub_, font=f2) / 2, h * .86), sub_, font=f2, fill=(150, 176, 204))
    return fn


def flow_diagram(nodes):
    """A chain of stages, top to bottom; the current one is lit."""
    def fn(d, w, h, k, p):
        n = len(nodes)
        gap = 34
        nh = (h * .90 - gap * (n - 1)) / n
        y = h * .05
        for j, name in enumerate(nodes):
            x0, x1 = w * .10, w * .90
            if j == k:
                d.rounded_rectangle([x0, y, x1, y + nh], radius=22, fill=mix(PANEL, HOT, p), outline=HOT, width=6)
                col = NAVY
            elif j < k:
                d.rounded_rectangle([x0, y, x1, y + nh], radius=22, fill=(40, 82, 126), outline=LINE, width=5)
                col = LINE
            else:
                d.rounded_rectangle([x0, y, x1, y + nh], radius=22, outline=(66, 108, 152), width=4)
                col = (96, 136, 178)
            f = F("num", min(70, nh * .50))
            lab = f"{j + 1}   {name}"
            d.text((x0 + 44, y + (nh - f.size) / 2 - 6), lab, font=f, fill=col)
            if j < n - 1:
                ax = w * .5
                d.line([ax, y + nh + 4, ax, y + nh + gap - 4], fill=LINE if j < k else (66, 108, 152), width=6)
            y += nh + gap
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
