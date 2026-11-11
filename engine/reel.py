#!/usr/bin/env python3
"""Reel format v2 — footage under everything, text on top, cut every ~2.5s.

WHY THIS REPLACES THE SLIDE FORMAT
----------------------------------
The v1 composer alternated footage scenes with flat-background text scenes.
Sampling four frames of gsm--social showed two of them were white slides
carrying a bulleted list — a deck, not a reel. Against OpusClip's analysis of
13.5M short-form clips (Jan–Mar 2026) that breaks several things at once:

  • "Close-ups outperform wide shots in the first 3 seconds."
  • "Faces get 28% more early retention than products."
  • "Use 3-5 second B-Roll clips max."
  • "Open with an object mid-flight, mid-pour, or mid-drop — unresolved
     motion hijacks attention."
  • "Cropped 16:9 footage loses ~40% of the frame's visual information."
  • "Watermarked or low-res stock footage tanks perceived production value."

So v2 holds one rule above all others: **there is never a frame without
moving footage behind it.** Text is an overlay, never the content. Shots run
2.2–2.8s, the open is a push-in on motion, and type sits in the lower half
where the eye already is, with a scrim only under the words.

The stock label stays. It is the one piece of chrome that earns its place:
these clips are not SoccerTex's floor and the video says so.
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from engine.render import (W, H, FPS, SAFE, TOP_SAFE, BOT_SAFE, Brand,
                           ease_out, seg, wrap, grain, vignette, Video)
from engine.footage import FootageScene

SHOT = 2.5                      # seconds per cut; the research says 3–5 max


class Shot(FootageScene):
    """Footage with a slow push-in and whatever type the caller draws on it.

    `overlay(d, i, n)` is called with a PIL draw context over the graded
    frame. `zoom` is the scale reached by the last frame — 1.06 is a push
    you feel without noticing, which is the point.
    """

    @staticmethod
    def _source_width(path):
        import subprocess
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width", "-of", "csv=p=0",
                            str(path)], capture_output=True, text=True)
        try:
            return int(r.stdout.strip())
        except ValueError:
            return W

    def __init__(self, path, seconds=SHOT, overlay=None, zoom=1.06,
                 start=0.0, speed=1.0, source="stock", scrim=0.0,
                 tight=1.0, focus=(0.5, 0.5), blur_edge=0.0, mirror=False, **kw):
        # SHARPNESS
        # ---------
        # The crop below samples 1/k of the frame and stretches it back to the
        # full canvas, so the shot is only as sharp as the pixels underneath
        # it. Ask the decoder for the resolution this crop needs, and cap that
        # at what the clip genuinely has: beyond its real width every extra
        # factor is invention, and it shows. A clip too small for the crop
        # requested gets the crop it can carry, not a blurred version of the
        # one it was asked for.
        # A little upscaling is invisible once the frame is moving and lightly
        # sharpened; a lot is mush. 1.25x is where the line sits by eye on a
        # phone, so clips are allowed that much headroom past their real width
        # and no more.
        MAX_UPSCALE = 1.25
        need = max(1.0, tight * zoom)
        have = self._source_width(path) / W
        self.upscaled = need > have * MAX_UPSCALE + 1e-6
        if self.upscaled:
            tight = max(1.0, have * MAX_UPSCALE / zoom)
            need = max(1.0, tight * zoom)
        # how far past the real pixels this shot ends up, for the sharpener
        self.stretch = max(1.0, need / have)
        super().__init__(path, seconds=seconds, start=start, speed=speed,
                         source=source, decode_scale=min(need, have), **kw)
        self.overlay, self.zoom, self.scrim = overlay, zoom, scrim
        # `tight` crops in before the push, to turn a wide stock plate into
        # the close-up the format needs. 1.9 keeps roughly the middle half.
        # `focus` moves that crop around the plate so two cuts off the same
        # clip don't look like the same shot.
        self.tight, self.focus, self.blur_edge = tight, focus, blur_edge
        # With four licensed clips carrying thirty videos, the same plate has
        # to come round several times inside one reel. A horizontal flip costs
        # nothing and breaks the recognition: the eye reads a mirrored machine
        # as a different angle rather than the same shot again. It is only
        # safe because none of these clips contain text or a logo.
        self.mirror = mirror

    def frame(self, i, n):
        img = self._next()
        if self.mirror:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        img = ImageEnhance.Color(img).enhance(0.9)
        img = ImageEnhance.Contrast(img).enhance(1.1)

        # crop in the decoded resolution, then resize once — cropping after a
        # downscale would throw away the pixels this scene asked for
        dw, dh = img.size
        k = self.tight * (1 + (self.zoom - 1) * (i / max(1, n - 1)))
        cw, ch = int(dw / k), int(dh / k)
        fx, fy = self.focus
        x = int((dw - cw) * min(max(fx, 0.0), 1.0))
        y = int((dh - ch) * min(max(fy, 0.0), 1.0))
        img = img.crop((x, y, x + cw, y + ch))
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        if self.stretch > 1.02:
            # recover the edge a resize costs — scaled to how far we stretched,
            # because over-sharpening a soft plate looks worse than the softness
            img = img.filter(ImageFilter.UnsharpMask(
                radius=1.6, percent=int(min(80, 60 * (self.stretch - 1) / 0.25)),
                threshold=3))

        if self.blur_edge:
            # Shallow depth of field is what makes the reference look shot on
            # a real lens rather than grabbed off a library. Approximate it:
            # blur the plate, then mask the sharp centre back in.
            blurred = img.filter(ImageFilter.GaussianBlur(self.blur_edge))
            mask = Image.new("L", (W, H), 0)
            md = ImageDraw.Draw(mask)
            md.ellipse([-int(W * .35), int(H * .18), int(W * 1.35), int(H * .86)], fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(int(W * .18)))
            img = Image.composite(img, blurred, mask)

        if self.scrim:
            band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bd = ImageDraw.Draw(band)
            top = int(H * 0.40)
            for k in range(top, H):
                t = (k - top) / (H - top)
                bd.line([0, k, W, k],
                        fill=(4, 12, 8, int(236 * self.scrim * t ** 0.85)))
            img = Image.alpha_composite(img.convert("RGBA"), band).convert("RGB")

        d = ImageDraw.Draw(img)
        if self.overlay:
            self.overlay(d, i, n)

        if self.source == "stock" and self.label_stock:
            f = Brand.body(23)
            txt = self.credit or "Library footage · not SoccerTex's floor"
            tw = d.textlength(txt, font=f)
            d.rectangle([SAFE - 9, H - BOT_SAFE + 30, SAFE + tw + 9, H - BOT_SAFE + 62],
                        fill=(0, 0, 0))
            d.text((SAFE, H - BOT_SAFE + 33), txt, font=f, fill=(150, 166, 158))

        return vignette(grain(img, 2, i), 0.30)


# ------------------------------------------------------------- overlays ----

def _fit(d, text, maker, max_size, min_size, max_lines, width):
    f = maker(max_size)
    lines = wrap(d, text, f, width)
    while len(lines) > max_lines and f.size > min_size:
        f = maker(f.size - 4)
        lines = wrap(d, text, f, width)
    return f, lines


def hook(text, sub=None):
    """Opening type. Big, bottom-weighted, in by 0.35s — the research says an
    intro over two seconds costs you the viewer, so there isn't one."""
    def draw(d, i, n):
        p = ease_out(seg(i, 0, FPS * 0.35))
        f, lines = _fit(d, text, Brand.head, 96, 58, 4, W - 2 * SAFE)
        lh = int(f.size * 1.08)
        y = H - BOT_SAFE - 150 - lh * len(lines) - (72 if sub else 0)
        for ln in lines:
            d.text((SAFE, y + int((1 - p) * 26)), ln, font=f,
                   fill=tuple(int(c * p) for c in Brand.WHITE))
            y += lh
        d.line([SAFE, y + 20, SAFE + int(200 * p), y + 27], fill=Brand.PITCH_LIT, width=8)
        if sub:
            q = ease_out(seg(i, FPS * 0.3, FPS * 0.35))
            fs = Brand.body(40)
            yy = y + 52
            for ln in wrap(d, sub, fs, W - 2 * SAFE):
                d.text((SAFE, yy), ln, font=fs,
                       fill=tuple(int(c * q) for c in (205, 218, 210)))
                yy += int(fs.size * 1.28)
    return draw


def stat(value, suffix, label, note=None):
    """One number, enormous, over moving footage. The number counts in — the
    eye follows a changing digit."""
    def draw(d, i, n):
        p = ease_out(seg(i, 0, FPS * 0.5))
        shown = int(value * p) if isinstance(value, int) else value
        fn = Brand.num(250)
        txt = f"{shown}{suffix}"
        # Lay the block out from the bottom up, so the note can never run
        # into the footage credit the way the first cut of this did.
        fl, fnm = Brand.med(44), Brand.body(38)
        note_lines = wrap(d, note, fnm, W - 2 * SAFE) if note else []
        note_h = len(note_lines) * int(fnm.size * 1.3)
        bottom = H - BOT_SAFE - 40
        y = bottom - note_h - 70 - 250
        d.text((SAFE, y), txt, font=fn, fill=Brand.WHITE)
        d.text((SAFE + 5, y + 258), label, font=fl, fill=Brand.PITCH_LIT)
        yy = y + 258 + 64
        for ln in note_lines:
            d.text((SAFE, yy), ln, font=fnm, fill=(200, 212, 204))
            yy += int(fnm.size * 1.3)
    return draw


def rows(items, start_index=1):
    """Two or three rows at a time, over footage. v1 put six on a white card;
    nobody reads six lines on a phone in two seconds."""
    def draw(d, i, n):
        f = Brand.med(50)
        fi = Brand.num(40)
        y = H - BOT_SAFE - 110 - len(items) * 112
        for k, it in enumerate(items):
            p = ease_out(seg(i, FPS * (0.12 + k * 0.16), FPS * 0.3))
            if p <= 0:
                continue
            dx = int((1 - p) * 34)
            d.rounded_rectangle([SAFE - dx, y - 8, SAFE + 62 - dx, y + 54],
                                radius=10, fill=Brand.PITCH)
            num = str(start_index + k)
            nw = d.textlength(num, font=fi)
            d.text((SAFE + 31 - nw / 2 - dx, y + 6), num, font=fi, fill=Brand.WHITE)
            lines = wrap(d, it, f, W - 2 * SAFE - 86)
            yy = y - 4
            for ln in lines[:2]:
                d.text((SAFE + 86 - dx, yy), ln, font=f,
                       fill=tuple(int(c * p) for c in Brand.WHITE))
                yy += int(f.size * 1.12)
            y += 112
    return draw


def punchline(text):
    """The line the whole clip existed to deliver."""
    def draw(d, i, n):
        p = ease_out(seg(i, 0, FPS * 0.3))
        f, lines = _fit(d, text, Brand.head, 84, 52, 4, W - 2 * SAFE)
        lh = int(f.size * 1.1)
        y = H - BOT_SAFE - 130 - lh * len(lines)
        for ln in lines:
            d.text((SAFE, y + int((1 - p) * 20)), ln, font=f,
                   fill=tuple(int(c * p) for c in Brand.MINT))
            y += lh
    return draw


def sign_off(line="SoccerTex · Cairo", sub="Teamwear, made to your tech pack"):
    def draw(d, i, n):
        p = ease_out(seg(i, 0, FPS * 0.3))
        f = Brand.head(62)
        y = H - BOT_SAFE - 190
        d.text((SAFE, y), line, font=f, fill=tuple(int(c * p) for c in Brand.WHITE))
        d.line([SAFE, y + 82, SAFE + int(170 * p), y + 89], fill=Brand.PITCH_LIT, width=7)
        fs = Brand.body(38)
        d.text((SAFE, y + 110), sub, font=fs,
               fill=tuple(int(c * p) for c in (200, 212, 204)))
    return draw


def _shadow_text(d, xy, text, font, fill, strength=150):
    """Type has to survive a near-white plate as well as a dark one. A soft
    dark halo costs nothing and removes the whole class of bug where a line
    disappears into the fabric behind it."""
    x, y = xy
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        d.text((x + dx, y + dy), text, font=font, fill=(2, 10, 6, strength))
    for dx, dy in ((-4, 2), (4, 2), (0, 4)):
        d.text((x + dx, y + dy), text, font=font, fill=(2, 10, 6, strength // 2))
    d.text((x, y), text, font=font, fill=fill)


def center_line(text, sub=None, caps=True):
    """Centred type, held in the middle of frame — the reference's only
    chrome. No rules, no chips, no numbers: just one sentence over a machine.
    """
    def draw(d, i, n):
        p = ease_out(seg(i, 0, FPS * 0.45))
        q = 1.0 if i < n - FPS * 0.4 else max(0.0, (n - i) / (FPS * 0.4))
        a = p * q
        body = text.upper() if caps else text
        f, lines = _fit(d, body, Brand.head, 72, 44, 3, W - 2 * SAFE - 60)
        lh = int(f.size * 1.18)
        total = lh * len(lines) + (58 if sub else 0)
        y = (H - total) // 2
        for ln in lines:
            tw = d.textlength(ln, font=f)
            _shadow_text(d, ((W - tw) / 2, y + int((1 - p) * 14)), ln, f,
                         tuple(int(c * a) for c in Brand.WHITE), int(170 * a))
            y += lh
        if sub:
            fs = Brand.body(36)
            r = ease_out(seg(i, FPS * 0.35, FPS * 0.4)) * q
            tw = d.textlength(sub, font=fs)
            _shadow_text(d, ((W - tw) / 2, y + 14), sub, fs,
                         tuple(int(c * r) for c in (214, 226, 218)), int(150 * r))
    return draw


def end_card(name="SOCCERTEX", sub="TEAMWEAR · CAIRO", tag="Made to your tech pack"):
    """Closing bug. The reference ends on its logo over black; this is the
    typographic stand-in until a clean logo file exists — the one on the Mac
    is a cropped screenshot with app chrome in it, not an asset."""
    def draw(d, i, n):
        p = ease_out(seg(i, 0, FPS * 0.4))
        f = Brand.head(86)
        tw = d.textlength(name, font=f)
        y = H // 2 - 120
        _shadow_text(d, ((W - tw) / 2, y), name, f,
                     tuple(int(c * p) for c in Brand.WHITE), int(190 * p))
        wline = int(190 * p)
        d.line([(W - wline) / 2, y + 112, (W + wline) / 2, y + 118],
               fill=Brand.PITCH_LIT, width=7)
        fs = Brand.med(34)
        tw = d.textlength(sub, font=fs)
        _shadow_text(d, ((W - tw) / 2, y + 148), sub, fs,
                     tuple(int(c * p) for c in (206, 218, 208)), int(160 * p))
        ft = Brand.body(32)
        tw = d.textlength(tag, font=ft)
        d.text(((W - tw) / 2, y + 200), tag, font=ft,
               fill=tuple(int(c * p * 0.8) for c in (170, 186, 176)))
    return draw
