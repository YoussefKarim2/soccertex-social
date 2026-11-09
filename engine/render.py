#!/usr/bin/env python3
"""SoccerTex video engine — code-rendered motion graphics.

Why this and not an AI video model: every free AI video tier either has no API,
no renewing credits, or forbids commercial use (see AUDIT-AI-TOOLS.md). ffmpeg
plus a frame renderer has no quota, no licence ceiling and no account. It runs
the same way forever.

Frames are generated with PIL and piped straight into ffmpeg as rawvideo, so
nothing touches disk between the two.

    from engine.render import Video, Brand
    v = Video("out.mp4"); v.add(TitleScene(...)); v.write()
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import subprocess, math, random, shutil

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"

W, H, FPS = 1080, 1920, 30          # 9:16, the only aspect all three platforms want
SAFE = int(W * 0.08)                 # 8% side margin
TOP_SAFE = int(H * 0.12)             # platform UI eats top and bottom
BOT_SAFE = int(H * 0.16)


class Brand:
    PITCH = (20, 132, 68)
    PITCH_LIT = (32, 174, 90)
    DEEP = (1, 22, 1)
    MINT = (242, 255, 244)
    WHITE = (255, 255, 255)
    FLOOR = (11, 20, 16)
    AMBER = (232, 161, 58)
    SLATE = (138, 152, 144)

    @staticmethod
    def head(s): return ImageFont.truetype(str(FONTS / "SecularOne-Regular.ttf"), s)
    @staticmethod
    def num(s):  return ImageFont.truetype(str(FONTS / "RobotoCondensed-Bold.ttf"), s)
    @staticmethod
    def body(s): return ImageFont.truetype(str(FONTS / "Roboto-Regular.ttf"), s)
    @staticmethod
    def med(s):  return ImageFont.truetype(str(FONTS / "Roboto-Medium.ttf"), s)
    @staticmethod
    def bold(s): return ImageFont.truetype(str(FONTS / "Roboto-Bold.ttf"), s)


# ---------------------------------------------------------------- easing ----
def ease_out(t):   return 1 - (1 - t) ** 3
def ease_in_out(t): return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def clamp01(t):    return max(0.0, min(1.0, t))

def seg(frame, start, dur):
    """Progress 0..1 of a sub-animation starting at `start` lasting `dur`."""
    if dur <= 0: return 1.0
    return clamp01((frame - start) / dur)


# ------------------------------------------------------------- utilities ----
def wrap(draw, text, font, max_w):
    out, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur: out.append(cur)
            cur = word
    if cur: out.append(cur)
    return out


def text_block(draw, xy, lines, font, fill, lh=1.18, align="left", max_w=None):
    x, y = xy
    for ln in lines:
        w = draw.textlength(ln, font=font)
        tx = x if align == "left" else (x - w / 2 if align == "center" else x - w)
        draw.text((tx, y), ln, font=font, fill=fill)
        y += int(font.size * lh)
    return y


def grain(img, amount=5, seed=0):
    """A little noise so flat colour doesn't band on compression."""
    rnd = random.Random(seed)
    px = img.load()
    for _ in range(int(W * H * 0.0035)):
        x, y = rnd.randrange(W), rnd.randrange(H)
        r, g, b = px[x, y]
        d = rnd.randint(-amount, amount)
        px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))
    return img


def vignette(img, strength=0.45):
    v = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(v)
    d.ellipse([-W * 0.35, -H * 0.12, W * 1.35, H * 1.12], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(W * 0.16))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(img, Image.blend(img, black, strength), v)


def logo_bug(d, opacity=140):
    f = Brand.head(34)
    d.text((SAFE, H - BOT_SAFE + 42), "SOCCERTEX", font=f, fill=(255, 255, 255, opacity))


# ---------------------------------------------------------------- scenes ----
class Scene:
    """Base: subclasses implement frame(i, n) -> PIL.Image."""
    def __init__(self, seconds): self.n = int(seconds * FPS)
    def frame(self, i, n): raise NotImplementedError
    def close(self):
        """Release anything the scene opened. Overridden by FootageScene,
        which holds a decoder subprocess."""
        return None


class HookScene(Scene):
    """The first 2 seconds. Hard, loud, unmissable."""
    def __init__(self, line1, line2=None, seconds=2.4, bg=Brand.FLOOR, accent=Brand.PITCH_LIT):
        super().__init__(seconds)
        self.l1, self.l2, self.bg, self.accent = line1, line2, bg, accent

    def frame(self, i, n):
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        # accent slab wipes in
        p = ease_out(seg(i, 0, FPS * .35))
        d.rectangle([0, int(H * .34), int(W * p), int(H * .345)], fill=self.accent)

        f1 = Brand.head(118)
        maxw = W - 2 * SAFE
        lines = wrap(d, self.l1, f1, maxw)
        while len(lines) > 3 and f1.size > 70:
            f1 = Brand.head(f1.size - 8); lines = wrap(d, self.l1, f1, maxw)

        y0 = int(H * .36)
        for k, ln in enumerate(lines):
            lp = ease_out(seg(i, FPS * (.08 + k * .07), FPS * .3))
            dy = int((1 - lp) * 40)
            d.text((SAFE, y0 + k * int(f1.size * 1.1) + dy), ln,
                   font=f1, fill=tuple(int(c * lp) for c in Brand.WHITE))

        if self.l2:
            f2 = Brand.body(44)
            lp = ease_out(seg(i, FPS * .55, FPS * .35))
            yy = y0 + len(lines) * int(f1.size * 1.1) + 34
            for ln in wrap(d, self.l2, f2, maxw):
                d.text((SAFE, yy + int((1 - lp) * 24)), ln, font=f2,
                       fill=tuple(int(c * lp) for c in Brand.SLATE))
                yy += int(f2.size * 1.3)
        return vignette(grain(img, 4, i), .3)


class StatScene(Scene):
    """One number counting up, with its label. Numbers stop the scroll."""
    def __init__(self, value, suffix, label, note=None, seconds=2.6,
                 bg=Brand.WHITE, fg=Brand.DEEP, accent=Brand.PITCH):
        super().__init__(seconds)
        self.value, self.suffix, self.label, self.note = value, suffix, label, note
        self.bg, self.fg, self.accent = bg, fg, accent

    def frame(self, i, n):
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        p = ease_out(seg(i, 0, FPS * 1.0))
        shown = self.value * p
        txt = f"{shown:,.0f}" if self.value >= 100 else f"{shown:.0f}"

        fn = Brand.num(380)
        tw = d.textlength(txt, font=fn)
        while tw > W - 2 * SAFE and fn.size > 160:
            fn = Brand.num(fn.size - 20); tw = d.textlength(txt, font=fn)
        y = int(H * .34)
        d.text((SAFE, y), txt, font=fn, fill=self.accent)

        if self.suffix:
            fs = Brand.head(96)
            d.text((SAFE + tw + 20, y + fn.size * .42), self.suffix, font=fs, fill=self.fg)

        lp = ease_out(seg(i, FPS * .5, FPS * .4))
        fl = Brand.head(62)
        ly = y + int(fn.size * 1.02)
        for ln in wrap(d, self.label, fl, W - 2 * SAFE):
            d.text((SAFE, ly + int((1 - lp) * 22)), ln, font=fl,
                   fill=tuple(int(a + (b - a) * lp) for a, b in zip(self.bg, self.fg)))
            ly += int(fl.size * 1.14)

        if self.note:
            np_ = ease_out(seg(i, FPS * .9, FPS * .4))
            fnm = Brand.body(38)
            d.line([SAFE, ly + 26, SAFE + int(220 * np_), ly + 26], fill=self.accent, width=6)
            yy = ly + 50
            for ln in wrap(d, self.note, fnm, W - 2 * SAFE):
                d.text((SAFE, yy), ln, font=fnm,
                       fill=tuple(int(a + (b - a) * np_) for a, b in zip(self.bg, Brand.SLATE)))
                yy += int(fnm.size * 1.32)
        return grain(img, 3, i)


class ListScene(Scene):
    """Numbered points landing one at a time. The workhorse."""
    def __init__(self, title, items, seconds=None, bg=Brand.WHITE,
                 fg=Brand.DEEP, accent=Brand.PITCH, per=1.35):
        self.items = items
        secs = seconds if seconds else 1.0 + per * len(items) + .8
        super().__init__(secs)
        self.title, self.bg, self.fg, self.accent, self.per = title, bg, fg, accent, per

    # Layout is measured before anything is drawn, so wrapped items can never
    # collide and the block sits optically centred instead of hugging the top.
    def _layout(self, d):
        BOX, GAP = 76, 34
        fi = Brand.med(50)
        tx_off = BOX + 30
        rows = []
        for item in self.items:
            lines = wrap(d, item, fi, W - SAFE - (SAFE + tx_off))
            h = max(BOX, len(lines) * int(fi.size * 1.16))
            rows.append((lines, h))
        total = sum(h for _, h in rows) + GAP * (len(rows) - 1)
        # shrink if it would overflow the safe area
        while total > (H - TOP_SAFE - BOT_SAFE - 320) and fi.size > 32:
            fi = Brand.med(fi.size - 3)
            rows = []
            for item in self.items:
                lines = wrap(d, item, fi, W - SAFE - (SAFE + tx_off))
                rows.append((lines, max(BOX, len(lines) * int(fi.size * 1.16))))
            total = sum(h for _, h in rows) + GAP * (len(rows) - 1)
        return fi, rows, total, BOX, GAP, tx_off

    def frame(self, i, n):
        img = Image.new("RGB", (W, H), self.bg)
        d = ImageDraw.Draw(img)
        ft = Brand.head(72)
        tp = ease_out(seg(i, 0, FPS * .4))
        y = TOP_SAFE + 20
        for ln in wrap(d, self.title, ft, W - 2 * SAFE):
            d.text((SAFE, y + int((1 - tp) * 26)), ln, font=ft,
                   fill=tuple(int(a + (b - a) * tp) for a, b in zip(self.bg, self.fg)))
            y += int(ft.size * 1.1)
        d.line([SAFE, y + 18, SAFE + int((W - 2 * SAFE) * tp), y + 22], fill=self.accent, width=5)
        title_bottom = y + 40

        fi, rows, total, BOX, GAP, tx_off = self._layout(d)
        fnum = Brand.num(54)
        avail = (H - BOT_SAFE) - title_bottom
        y = title_bottom + max(30, int((avail - total) * 0.42))

        for k, (lines, h) in enumerate(rows):
            p = ease_out(seg(i, FPS * (.7 + k * self.per), FPS * .42))
            if p <= 0: break
            dx = int((1 - p) * 56)
            bt = y + (h - BOX) // 2
            d.rounded_rectangle([SAFE - dx, bt, SAFE + BOX - dx, bt + BOX], 12,
                                fill=tuple(int(a + (b - a) * p) for a, b in zip(self.bg, self.accent)))
            ntxt = str(k + 1)
            d.text((SAFE + BOX / 2 - d.textlength(ntxt, font=fnum) / 2 - dx, bt + 8), ntxt,
                   font=fnum, fill=tuple(int(a + (b - a) * p) for a, b in zip(self.bg, Brand.WHITE)))
            tx = SAFE + tx_off - dx
            ty = y + (h - len(lines) * int(fi.size * 1.16)) // 2
            for ln in lines:
                d.text((tx, ty), ln, font=fi,
                       fill=tuple(int(a + (b - a) * p) for a, b in zip(self.bg, self.fg)))
                ty += int(fi.size * 1.16)
            y += h + GAP
        return grain(img, 3, i)


class CompareScene(Scene):
    """A vs B. The highest-performing teamwear format in the benchmark set."""
    def __init__(self, title, left, right, seconds=3.4, winner="right"):
        super().__init__(seconds)
        self.title, self.left, self.right, self.winner = title, left, right, winner

    def _col(self, d, x, w, label, rows, p, good):
        top = int(H * .30)
        col = Brand.PITCH if good else (90, 98, 93)
        d.rounded_rectangle([x, top, x + w, top + int(H * .40 * 1)], 18, fill=col)
        fh = Brand.head(54)
        d.text((x + w / 2 - d.textlength(label, font=fh) / 2, top + 26), label,
               font=fh, fill=Brand.WHITE)
        fr = Brand.body(36)
        yy = top + 120
        for k, r in enumerate(rows):
            rp = ease_out(seg_frame(p, k))
            if rp <= 0: break
            for ln in wrap(d, r, fr, w - 46):
                d.text((x + 24, yy), ln, font=fr,
                       fill=tuple(int(col[j] + (255 - col[j]) * rp) for j in range(3)))
                yy += int(fr.size * 1.3)
            yy += 12

    def frame(self, i, n):
        img = Image.new("RGB", (W, H), Brand.FLOOR)
        d = ImageDraw.Draw(img)
        ft = Brand.head(76)
        tp = ease_out(seg(i, 0, FPS * .4))
        y = TOP_SAFE
        for ln in wrap(d, self.title, ft, W - 2 * SAFE):
            d.text((SAFE, y + int((1 - tp) * 24)), ln, font=ft,
                   fill=tuple(int(Brand.FLOOR[j] + (255 - Brand.FLOOR[j]) * tp) for j in range(3)))
            y += int(ft.size * 1.08)

        gap, w = 26, (W - 2 * SAFE - 26) // 2
        fh, fr = Brand.head(50), Brand.body(36)
        pad_top, pad_bot = 120, 34

        # Measure both columns first and give them one shared height.
        wrapped = []
        col_h = 0
        for lab, rows in (self.left, self.right):
            lw = [wrap(d, r, fr, w - 48) for r in rows]
            h = pad_top + sum(len(l) * int(fr.size * 1.28) + 10 for l in lw) + pad_bot
            wrapped.append(lw); col_h = max(col_h, h)

        body_top = y + 50
        avail = (H - BOT_SAFE) - body_top
        top0 = body_top + max(0, (avail - col_h) // 2)

        for side, ((lab, rows), lw) in enumerate(zip([self.left, self.right], wrapped)):
            x = SAFE + side * (w + gap)
            good = (self.winner == "right" and side == 1) or (self.winner == "left" and side == 0)
            col = Brand.PITCH if good else (46, 54, 49)
            sp = ease_out(seg(i, FPS * (.3 + side * .2), FPS * .4))
            top = top0 + int((1 - sp) * 50)
            d.rounded_rectangle([x, top, x + w, top + col_h], 20, fill=col)
            d.text((x + w / 2 - d.textlength(lab, font=fh) / 2, top + 30), lab,
                   font=fh, fill=Brand.WHITE)
            yy = top + pad_top
            for k, lines in enumerate(lw):
                rp = ease_out(seg(i, FPS * (.75 + side * .15 + k * .3), FPS * .35))
                if rp <= 0: break
                for ln in lines:
                    d.text((x + 24, yy), ln, font=fr,
                           fill=tuple(int(col[j] + (235 - col[j]) * rp) for j in range(3)))
                    yy += int(fr.size * 1.28)
                yy += 10
        return vignette(grain(img, 4, i), .25)


class CTAScene(Scene):
    """Brand close. Same every time, which is the point."""
    def __init__(self, line="SEE THE FLOOR.", sub="soccertexhq.com", seconds=2.0):
        super().__init__(seconds)
        self.line, self.sub = line, sub

    def frame(self, i, n):
        img = Image.new("RGB", (W, H), Brand.PITCH)
        d = ImageDraw.Draw(img)
        p = ease_out(seg(i, 0, FPS * .5))
        f = Brand.head(140)
        lines = self.line.split("\n")
        y = int(H * .40)
        for k, ln in enumerate(lines):
            lp = ease_out(seg(i, FPS * (.05 + k * .12), FPS * .4))
            d.text((SAFE + int((1 - lp) * 30), y), ln, font=f,
                   fill=tuple(int(Brand.PITCH[j] + (255 - Brand.PITCH[j]) * lp) for j in range(3)))
            y += int(f.size * 1.08)
        sp = ease_out(seg(i, FPS * .6, FPS * .4))
        d.line([SAFE, y + 36, SAFE + int(260 * sp), y + 42], fill=Brand.MINT, width=7)
        fs = Brand.body(44)
        d.text((SAFE, y + 76), self.sub, font=fs,
               fill=tuple(int(Brand.PITCH[j] + (Brand.MINT[j] - Brand.PITCH[j]) * sp) for j in range(3)))
        fb = Brand.head(38)
        d.text((SAFE, H - BOT_SAFE + 30), "SOCCERTEX · CAIRO, EGYPT", font=fb,
               fill=tuple(int(Brand.PITCH[j] + (Brand.MINT[j] - Brand.PITCH[j]) * sp) for j in range(3)))
        return grain(img, 3, i)


def seg_frame(p, k):   # kept for CompareScene._col compatibility
    return clamp01(p - k * .2)


# ----------------------------------------------------------------- video ----
class Video:
    def __init__(self, out_path, fps=FPS):
        self.out = Path(out_path); self.fps = fps; self.scenes = []
        self.out.parent.mkdir(parents=True, exist_ok=True)

    def add(self, scene):
        self.scenes.append(scene); return self

    @property
    def seconds(self):
        return sum(s.n for s in self.scenes) / self.fps

    @property
    def cut_times(self):
        """Seconds at which one scene hands over to the next — the soundtrack
        puts a whoosh and an impact on each."""
        out, acc = [], 0
        for s in self.scenes[:-1]:
            acc += s.n
            out.append(acc / self.fps)
        return out

    def write(self, crf=20, audio=None, quiet=True, music=True, bpm=124):
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg not installed")
        if audio is None and music:
            from engine.audio import soundtrack
            audio = soundtrack(self.seconds, self.cut_times,
                               path=self.out.parent.parent / "audio" / f"{self.out.stem}.wav",
                               bpm=bpm, seed=abs(hash(self.out.stem)) % 1000)
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(self.fps), "-i", "-"]
        if audio and Path(audio).exists():
            cmd += ["-i", str(audio), "-c:a", "aac", "-b:a", "128k", "-shortest"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-profile:v", "high", "-level", "4.0", str(self.out)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        total, err = 0, None
        try:
            for sc in self.scenes:
                try:
                    for i in range(sc.n):
                        buf = sc.frame(i, sc.n).tobytes()
                        if len(buf) != W * H * 3:
                            raise RuntimeError(
                                f"{type(sc).__name__} produced {len(buf)} bytes, "
                                f"expected {W * H * 3}")
                        proc.stdin.write(buf)
                        total += 1
                finally:
                    sc.close()
        except Exception as e:
            err = e
        finally:
            try:
                proc.stdin.close()
            except BrokenPipeError:
                pass
            rc = proc.wait()
        if err is not None:
            raise err
        if rc != 0:
            raise RuntimeError(f"ffmpeg exited {rc}")
        if not quiet:
            print(f"  {self.out.name}  {total} frames  {total/self.fps:.1f}s  "
                  f"{self.out.stat().st_size/1024/1024:.1f} MB")
        return self.out
