#!/usr/bin/env python3
"""Animated machine scenes, drawn frame by frame.

These are deliberately illustrations, not footage. We have no video of the
SoccerTex floor and no licensed stock is reachable, so rather than fake a
factory we draw the mechanism: a needle that actually punches, a blade that
actually tracks, a press that actually closes. It reads as a diagram in motion,
which is honest and holds attention far better than static type.

Every scene loops cleanly so it can be cut to any length.
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFilter
import math, random

from engine.render import (Scene, Brand, W, H, FPS, SAFE, TOP_SAFE, BOT_SAFE,
                           ease_out, ease_in_out, seg, clamp01, wrap, grain, vignette)

STROKE = 9
METAL = (120, 134, 126)
METAL_D = (74, 84, 78)
THREAD = (232, 161, 58)


def _rgba():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _ghost(base, draw_fn, offsets, alpha=70):
    """Cheap motion blur: the same shape drawn behind itself, fading."""
    for i, off in enumerate(offsets):
        layer = _rgba()
        d = ImageDraw.Draw(layer)
        draw_fn(d, off, int(alpha * (1 - i / max(1, len(offsets)))))
        base.alpha_composite(layer)


def _caption(img, text, sub=None, accent=Brand.PITCH_LIT):
    d = ImageDraw.Draw(img)
    f = Brand.head(72)
    lines = wrap(d, text, f, W - 2 * SAFE)
    while len(lines) > 2 and f.size > 46:
        f = Brand.head(f.size - 6); lines = wrap(d, text, f, W - 2 * SAFE)
    y = TOP_SAFE + 10
    for ln in lines:
        d.text((SAFE, y), ln, font=f, fill=Brand.WHITE)
        y += int(f.size * 1.1)
    d.line([SAFE, y + 16, SAFE + 240, y + 22], fill=accent, width=7)
    if sub:
        fs = Brand.body(38)
        yy = y + 48
        for ln in wrap(d, sub, fs, W - 2 * SAFE):
            d.text((SAFE, yy), ln, font=fs, fill=Brand.SLATE)
            yy += int(fs.size * 1.3)
    return img


# =========================================================== sewing machine =
class SewingScene(Scene):
    """Needle bar punching, fabric feeding, stitches accumulating behind."""

    def __init__(self, seconds=4.0, title="SEWN HERE", sub=None, spm=7.0):
        super().__init__(seconds)
        self.title, self.sub, self.spm = title, sub, spm

    def frame(self, i, n):
        t = i / FPS
        img = Image.new("RGBA", (W, H), Brand.FLOOR + (255,))
        d = ImageDraw.Draw(img)

        cx, bed_y = W // 2, int(H * .76)
        phase = (t * self.spm) % 1.0
        # needle: fast down, slower up — a real machine's motion
        drop = math.sin(phase * math.pi) ** 0.6
        needle_y = int(H * .50 + drop * 170)
        velocity = abs(math.cos(phase * math.pi))

        # --- fabric, scrolling right to left
        fab_h = 68
        fy = bed_y - fab_h
        d.rectangle([0, fy, W, bed_y], fill=(28, 46, 36))
        scroll = (t * 150) % 60
        for x in range(-60, W + 60, 60):
            d.line([x - scroll, fy, x - scroll, bed_y], fill=(22, 38, 29), width=2)

        # --- stitches already made (to the left of the needle)
        pitch = 48
        off = (t * 150) % pitch
        x = cx - off
        while x > -pitch:
            d.line([x - 13, fy + fab_h // 2, x + 13, fy + fab_h // 2],
                   fill=THREAD, width=7)
            x -= pitch

        # --- machine bed
        d.rounded_rectangle([0, bed_y, W, bed_y + 190], 0, fill=METAL_D)
        d.rectangle([0, bed_y, W, bed_y + 8], fill=METAL)

        # --- arm overhead
        arm_y = int(H * .34)
        d.rounded_rectangle([SAFE - 46, arm_y, W - SAFE + 46, arm_y + 110], 28, fill=METAL_D)
        d.rounded_rectangle([W - SAFE - 130, arm_y, W - SAFE + 46, bed_y - 40], 28, fill=METAL_D)
        d.rounded_rectangle([SAFE - 46, arm_y, W - SAFE + 46, arm_y + 18], 8, fill=METAL)

        # --- thread path from spool to needle
        spool_x, spool_y = W - SAFE - 52, arm_y - 62
        d.ellipse([spool_x - 34, spool_y - 26, spool_x + 34, spool_y + 26], fill=THREAD)
        d.ellipse([spool_x - 12, spool_y - 26, spool_x + 12, spool_y + 26], fill=(150, 100, 30))
        slack = 18 * math.sin(phase * 2 * math.pi)
        d.line([spool_x, spool_y, cx + 130, arm_y + 56 + slack], fill=THREAD, width=5)
        d.line([cx + 130, arm_y + 56 + slack, cx, needle_y - 130], fill=THREAD, width=5)

        # --- needle bar with ghosting while it moves fast
        def bar(dd, dy, a):
            dd.rounded_rectangle([cx - 18, arm_y + 86 + dy, cx + 18, needle_y - 60 + dy],
                                 7, fill=METAL + (a,))
            dd.polygon([(cx - 5, needle_y - 56 + dy), (cx + 5, needle_y - 56 + dy),
                        (cx + 2, needle_y + dy), (cx - 2, needle_y + dy)],
                       fill=(235, 240, 236, a))
        if velocity > .35:
            _ghost(img, bar, [int(28 * velocity), int(14 * velocity)], alpha=90)
        bar(d, 0, 255)

        # --- presser foot
        d.rounded_rectangle([cx - 64, fy - 34, cx + 64, fy - 6], 7, fill=METAL)
        d.rectangle([cx - 12, fy - 80, cx + 12, fy - 28], fill=METAL)

        # --- impact flash at the bottom of the stroke
        if drop > .93:
            fl = _rgba(); fd = ImageDraw.Draw(fl)
            r = int(46 * (drop - .93) / .07)
            fd.ellipse([cx - r, fy + fab_h // 2 - r, cx + r, fy + fab_h // 2 + r],
                       fill=(255, 255, 255, 120))
            img.alpha_composite(fl.filter(ImageFilter.GaussianBlur(10)))

        out = img.convert("RGB")
        _caption(out, self.title, self.sub)
        return vignette(grain(out, 4, i), .3)


# ============================================================ rotary cutter =
class CutScene(Scene):
    """Blade tracking left to right, layers separating behind it."""

    def __init__(self, seconds=4.0, title="CUT HERE", sub=None, layers=5):
        super().__init__(seconds)
        self.title, self.sub, self.layers = title, sub, layers

    def frame(self, i, n):
        p = i / max(1, n - 1)
        img = Image.new("RGB", (W, H), Brand.FLOOR)
        d = ImageDraw.Draw(img)

        top = int(H * .50)
        lh = 44
        travel = ease_in_out(clamp01(p * 1.15))
        bx = int(SAFE + travel * (W - 2 * SAFE))

        # stacked fabric layers, splitting open behind the blade
        for k in range(self.layers):
            y = top + k * lh
            shade = 30 + k * 7
            col = (shade, 54 + k * 5, shade + 10)
            d.rectangle([SAFE, y, W - SAFE, y + lh - 5], fill=col)
            if bx > SAFE:
                gap = int(min(16, (bx - SAFE) / 26)) + k
                d.rectangle([SAFE, y + lh // 2 - 2, bx, y + lh // 2 + 2], fill=Brand.FLOOR)
                d.rectangle([SAFE, y, bx, y + lh // 2 - gap // 2], fill=col)
                d.rectangle([SAFE, y + lh // 2 + gap // 2, bx, y + lh - 5], fill=col)

        # cut line glow
        if bx > SAFE:
            gl = _rgba(); gd = ImageDraw.Draw(gl)
            gd.line([SAFE, top + self.layers * lh // 2, bx, top + self.layers * lh // 2],
                    fill=Brand.PITCH_LIT + (160,), width=5)
            img.paste(Image.alpha_composite(
                Image.new("RGBA", (W, H), (0, 0, 0, 0)),
                gl.filter(ImageFilter.GaussianBlur(9))).convert("RGB"),
                (0, 0), gl.filter(ImageFilter.GaussianBlur(9)).split()[3])

        # blade
        by = top + self.layers * lh // 2
        r = 100
        rot = p * 26
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=METAL, outline=(210, 220, 212), width=5)
        d.ellipse([bx - 22, by - 22, bx + 22, by + 22], fill=METAL_D)
        for k in range(8):
            a = rot + k * math.pi / 4
            d.line([bx + 26 * math.cos(a), by + 26 * math.sin(a),
                    bx + (r - 12) * math.cos(a), by + (r - 12) * math.sin(a)],
                   fill=(176, 188, 179), width=4)
        # handle
        d.rounded_rectangle([bx - 18, by - r - 150, bx + 18, by - r + 8], 16, fill=(40, 48, 43))

        _caption(img, self.title, self.sub)
        return vignette(grain(img, 4, i), .3)


# =============================================================== heat press =
class PressScene(Scene):
    """Platen descends, steam escapes, the print is revealed on lift."""

    def __init__(self, seconds=5.0, title="PRESSED HERE", sub=None):
        super().__init__(seconds)
        self.title, self.sub = title, sub
        self._puffs = [(random.Random(k).uniform(-240, 240),
                        random.Random(k + 99).uniform(.0, .5),
                        random.Random(k + 7).uniform(26, 56)) for k in range(16)]

    def frame(self, i, n):
        p = i / max(1, n - 1)
        img = Image.new("RGB", (W, H), Brand.FLOOR)
        d = ImageDraw.Draw(img)
        cx = W // 2
        bed_y = int(H * .76)

        # phases: close 0-.3, hold .3-.6, lift .6-.85, reveal .85-1
        if p < .30:   close = ease_in_out(p / .30)
        elif p < .60: close = 1.0
        elif p < .85: close = 1 - ease_out((p - .60) / .25)
        else:         close = 0.0
        pressed = p > .32

        # bed
        d.rounded_rectangle([SAFE - 20, bed_y, W - SAFE + 20, bed_y + 150], 14, fill=METAL_D)
        d.rectangle([SAFE - 20, bed_y, W - SAFE + 20, bed_y + 10], fill=METAL)

        # garment
        gy = bed_y - 70
        d.rounded_rectangle([SAFE + 20, gy, W - SAFE - 20, bed_y - 4], 8, fill=(236, 240, 237))

        # the printed graphic, only after the press has closed
        if pressed:
            rev = clamp01((p - .32) / .25) if p < .85 else 1.0
            gw = int((W - 2 * SAFE - 240) * rev)
            if gw > 4:
                d.rounded_rectangle([cx - gw // 2, gy + 12, cx + gw // 2, bed_y - 18],
                                    6, fill=Brand.PITCH)
                if gw > 160:
                    f = Brand.head(44)
                    tw = d.textlength("SOCCERTEX", font=f)
                    if tw < gw - 20:
                        d.text((cx - tw / 2, gy + 18), "SOCCERTEX", font=f, fill=Brand.WHITE)

        # platen
        plat_rest = int(H * .34)
        plat_y = int(plat_rest + close * (gy - plat_rest - 96))
        d.rounded_rectangle([SAFE - 20, plat_y, W - SAFE + 20, plat_y + 96], 14, fill=METAL_D)
        d.rectangle([SAFE - 20, plat_y + 86, W - SAFE + 20, plat_y + 96], fill=(196, 92, 60))
        d.rounded_rectangle([cx - 24, plat_y - 150, cx + 24, plat_y + 10], 18, fill=(40, 48, 43))
        d.rounded_rectangle([cx - 110, plat_y - 190, cx + 110, plat_y - 146], 20, fill=(54, 62, 56))

        # steam on lift
        if .60 < p < .92:
            s = (p - .60) / .32
            layer = _rgba(); ld = ImageDraw.Draw(layer)
            for dx, delay, size in self._puffs:
                local = clamp01((s - delay) / .6)
                if local <= 0: continue
                yy = gy - 20 - local * 300
                rr = size * (0.5 + local)
                a = int(130 * (1 - local))
                ld.ellipse([cx + dx - rr, yy - rr, cx + dx + rr, yy + rr],
                           fill=(230, 240, 234, a))
            img.paste(layer.filter(ImageFilter.GaussianBlur(14)).convert("RGB"),
                      (0, 0), layer.filter(ImageFilter.GaussianBlur(14)).split()[3])

        _caption(img, self.title, self.sub)
        return vignette(grain(img, 4, i), .3)


# =============================================================== embroidery =
class EmbroideryScene(Scene):
    """Needle punching while a stitched path builds along a crest outline."""

    def __init__(self, seconds=4.5, title="EMBROIDERED HERE", sub=None):
        super().__init__(seconds)
        self.title, self.sub = title, sub

    @staticmethod
    def _crest(cx, cy, s):
        """A shield outline: flat top, straight shoulders, curved point.
        Built as key vertices then resampled at even spacing so the stitch
        rate stays constant all the way round."""
        w, h = s, s * 1.22
        top = cy - h * .72

        def bez(p0, p1, p2, steps):
            return [(
                (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1],
            ) for t in (k / steps for k in range(steps + 1))]

        shoulder_l = (cx - w, top)
        shoulder_r = (cx + w, top)
        waist_l = (cx - w, cy + h * .06)
        waist_r = (cx + w, cy + h * .06)
        point = (cx, cy + h * .78)

        path = [shoulder_l, shoulder_r, waist_r]
        path += bez(waist_r, (cx + w * .72, cy + h * .62), point, 14)[1:]
        path += bez(point, (cx - w * .72, cy + h * .62), waist_l, 14)[1:]
        path += [shoulder_l]

        # resample to even arc length
        segs, total = [], 0.0
        for a, b in zip(path, path[1:]):
            d_ = math.hypot(b[0] - a[0], b[1] - a[1])
            segs.append((a, b, d_)); total += d_
        out, N = [], 72
        for k in range(N + 1):
            want = total * k / N
            acc = 0.0
            for a, b, d_ in segs:
                if acc + d_ >= want or (a, b, d_) is segs[-1]:
                    u = 0 if d_ == 0 else (want - acc) / d_
                    out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
                    break
                acc += d_
        return out

    def frame(self, i, n):
        p = i / max(1, n - 1)
        t = i / FPS
        img = Image.new("RGBA", (W, H), Brand.FLOOR + (255,))
        d = ImageDraw.Draw(img)
        cx, cy = W // 2, int(H * .60)

        # hoop
        R = 345
        d.ellipse([cx - R - 22, cy - R - 22, cx + R + 22, cy + R + 22],
                  outline=(150, 120, 70), width=20)
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(236, 240, 237))

        pts = self._crest(cx, cy, 215)
        done = int(len(pts) * ease_in_out(clamp01(p * 1.1)))

        # stitched path
        for k in range(1, max(1, done)):
            d.line([pts[k - 1], pts[k]], fill=Brand.PITCH, width=13)
        for k in range(0, max(1, done), 2):
            x, y = pts[k]
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(10, 90, 46))

        # needle hammering at the live end
        if done < len(pts):
            nx, ny = pts[min(done, len(pts) - 1)]
            phase = (t * 9) % 1.0
            drop = math.sin(phase * math.pi) ** .6
            tip = ny - 150 + drop * 150
            velocity = abs(math.cos(phase * math.pi))

            def needle(dd, dy, a):
                dd.rounded_rectangle([nx - 11, ny - 420 + dy, nx + 11, tip - 40 + dy],
                                     6, fill=METAL + (a,))
                dd.polygon([(nx - 4, tip - 40 + dy), (nx + 4, tip - 40 + dy),
                            (nx + 1, tip + dy), (nx - 1, tip + dy)],
                           fill=(240, 244, 241, a))
            if velocity > .35:
                _ghost(img, needle, [int(26 * velocity), int(13 * velocity)], alpha=90)
            needle(d, 0, 255)

            # thread feeding in
            d.line([nx + 150, ny - 430, nx, tip - 60], fill=THREAD, width=4)
            if drop > .9:
                fl = _rgba(); fd = ImageDraw.Draw(fl)
                fd.ellipse([nx - 26, ny - 26, nx + 26, ny + 26], fill=(255, 255, 255, 110))
                img.alpha_composite(fl.filter(ImageFilter.GaussianBlur(8)))

        out = img.convert("RGB")
        _caption(out, self.title, self.sub)
        return vignette(grain(out, 4, i), .3)


# ==================================================== high-energy title card =
class PunchScene(Scene):
    """Word-by-word type that lands hard, with a shake on each hit.
    Replaces the old static hook."""

    def __init__(self, text, sub=None, seconds=2.6, bg=Brand.FLOOR,
                 accent=Brand.PITCH_LIT, shake=True):
        super().__init__(seconds)
        self.words = text.split()
        self.sub, self.bg, self.accent, self.shake = sub, bg, accent, shake

    def frame(self, i, n):
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)

        per = max(2, int(n * .55 / max(1, len(self.words))))
        f = Brand.head(126)
        maxw = W - 2 * SAFE

        # lay the words out once
        lines, cur = [], []
        for wd in self.words:
            trial = " ".join(cur + [wd])
            if d.textlength(trial, font=f) <= maxw or not cur:
                cur.append(wd)
            else:
                lines.append(cur); cur = [wd]
        if cur: lines.append(cur)
        while len(lines) > 3 and f.size > 72:
            f = Brand.head(f.size - 8)
            lines, cur = [], []
            for wd in self.words:
                trial = " ".join(cur + [wd])
                if d.textlength(trial, font=f) <= maxw or not cur:
                    cur.append(wd)
                else:
                    lines.append(cur); cur = [wd]
            if cur: lines.append(cur)

        # shake when a word has just landed
        sx = sy = 0
        idx = 0
        total_words = sum(len(l) for l in lines)
        for k in range(total_words):
            age = i - k * per
            if 0 <= age < 3 and self.shake:
                mag = 9 - age * 3
                rnd = random.Random(k * 31 + age)
                sx += rnd.randint(-mag, mag); sy += rnd.randint(-mag, mag)

        y = int(H * .36) + sy
        for line in lines:
            x = SAFE + sx
            for wd in line:
                p = clamp01((i - idx * per) / max(1, per * .8))
                idx += 1
                if p <= 0:
                    x += d.textlength(wd + " ", font=f); continue
                e = ease_out(p)
                # scale punch: overshoot then settle
                k = 1.25 - .25 * e if p < 1 else 1.0
                fw = Brand.head(max(10, int(f.size * k)))
                col = tuple(int(c * min(1, e * 1.4)) for c in Brand.WHITE)
                d.text((x, y + (f.size - fw.size) * .55), wd, font=fw, fill=col)
                x += d.textlength(wd + " ", font=f)
            y += int(f.size * 1.1)

        bar = ease_out(seg(i, 0, FPS * .35))
        d.rectangle([0, int(H * .33), int(W * bar), int(H * .335)], fill=self.accent)

        if self.sub:
            sp = ease_out(seg(i, int(n * .62), FPS * .35))
            fs = Brand.body(42)
            yy = y + 26
            for ln in wrap(d, self.sub, fs, maxw):
                d.text((SAFE + sx, yy), ln, font=fs,
                       fill=tuple(int(c * sp) for c in Brand.SLATE))
                yy += int(fs.size * 1.3)
        return vignette(grain(img, 4, i), .3)
