#!/usr/bin/env python3
"""Real video footage as a scene — your own clips, or licensed stock.

Any clip, any aspect ratio, gets scaled to cover 1080x1920 and centre-cropped,
optionally slowed, graded toward the brand, and overlaid with brand type.

THE RULE THIS MODULE ENFORCES
-----------------------------
Clips live in two pools and they never mix:

    assets/footage/own/     filmed at SoccerTex. May be called "our floor".
    assets/footage/stock/   licensed from Pexels/Pixabay. May NOT.

Pexels' licence prohibits implying endorsement; Pixabay's prohibits misleading
use. Beyond the licences, presenting someone else's sewing floor as SoccerTex's
would be a lie to buyers who are specifically checking whether a supplier is
real. So `source="stock"` refuses first-person factory language in the overlay
and raises before anything renders.
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageEnhance
from pathlib import Path
import subprocess, re, shutil

from engine.render import (Scene, Brand, W, H, FPS, SAFE, TOP_SAFE, BOT_SAFE,
                           ease_out, seg, wrap, grain, vignette)

ROOT = Path(__file__).resolve().parent.parent
OWN = ROOT / "assets" / "footage" / "own"
STOCK = ROOT / "assets" / "footage" / "stock"

# Language that asserts this is SoccerTex's own operation.
FIRST_PERSON = re.compile(
    r"\b(our|we|us|my)\b.{0,30}\b(floor|factory|line|lines|team|machine|machines|"
    r"workshop|facility|plant|operators?|staff)\b"
    r"|\b(this|here)\s+(is|in)\s+(our|the)\s+(floor|factory|line|workshop)\b"
    r"|\bsoccertex['’]s?\s+(floor|factory|line|workshop|machines?)\b"
    r"|\b(inside|at)\s+soccertex\b", re.I)


class StockMisuse(RuntimeError):
    pass


def guard(text: str | None, source: str):
    if not text or source == "own":
        return
    m = FIRST_PERSON.search(text)
    if m:
        raise StockMisuse(
            f"Stock footage cannot carry first-person factory language: "
            f"{m.group(0)!r}. Either film it yourself and put the clip in "
            f"assets/footage/own/, or reword the overlay so it describes the "
            f"process generally rather than claiming it is SoccerTex's floor."
        )


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,duration,nb_frames,r_frame_rate",
         "-show_entries", "format=duration", "-of", "default=nw=1", str(path)],
        capture_output=True, text=True)
    out = {}
    for line in r.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out


class FootageScene(Scene):
    """One clip, cropped to 9:16, with optional overlay.

    source:  "own"   — filmed at SoccerTex; may use first-person language
             "stock" — licensed; must describe the process generally
    """

    def __init__(self, path, seconds=4.0, title=None, sub=None, credit=None,
                 start=0.0, speed=1.0, source="stock", grade=True,
                 darken=0.55, label_stock=True, decode_scale=1.0):
        super().__init__(seconds)
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(
                f"{self.path} is missing. Drop clips into "
                f"{'assets/footage/own/' if source == 'own' else 'assets/footage/stock/'} "
                f"— see assets/footage/README.md")
        if source not in ("own", "stock"):
            raise ValueError("source must be 'own' or 'stock'")
        guard(title, source); guard(sub, source)
        self.title, self.sub, self.credit = title, sub, credit
        self.start, self.speed, self.source = start, speed, source
        self.grade, self.darken, self.label_stock = grade, darken, label_stock
        self._proc = None
        # DECODE RESOLUTION
        # -----------------
        # Decoding straight to the 1080x1920 canvas throws the proxy's extra
        # pixels away before anything can crop into them, so a close-up was
        # always an upscale of the delivery frame — the reason every tight
        # shot in the first narrated cut looked soft. A scene that intends to
        # crop in asks for a bigger decode and does its own resize at the end.
        s = max(1.0, float(decode_scale))
        self.dw = int(W * s) // 2 * 2
        self.dh = int(H * s) // 2 * 2
        self.decode_scale = self.dw / W
        self._bytes = self.dw * self.dh * 3

    # -- frame source ------------------------------------------------------
    def _open(self):
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg not installed")
        vf = (f"scale={self.dw}:{self.dh}:force_original_aspect_ratio=increase,"
              f"crop={self.dw}:{self.dh},fps={FPS}")
        if self.speed != 1.0:
            vf = f"setpts={1/self.speed:.4f}*PTS," + vf
        self._proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-stream_loop", "-1",
             "-ss", str(self.start), "-i", str(self.path),
             "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            bufsize=self._bytes * 2)

    def _read_exact(self):
        """A pipe read can come back short. Loop until the frame is whole."""
        parts, got = [], 0
        while got < self._bytes:
            chunk = self._proc.stdout.read(self._bytes - got)
            if not chunk:
                return None                      # EOF
            parts.append(chunk); got += len(chunk)
        return b"".join(parts)

    def _next(self):
        if self._proc is None:
            self._open()
        buf = self._read_exact()
        if buf is None:
            self.close()                         # clip ended; start it again
            self._open()
            buf = self._read_exact()
        if buf is None:
            # the clip cannot be decoded at all — fail loudly rather than
            # writing a short frame and corrupting the encoder's stream
            raise RuntimeError(f"no frames decoded from {self.path}")
        return Image.frombytes("RGB", (self.dw, self.dh), buf)

    def close(self):
        """Stop the decoder. Video.write calls this when the scene is done —
        without it every FootageScene leaves an ffmpeg running until the
        process exits, which is what broke the first full-library render."""
        p, self._proc = self._proc, None
        if p is None:
            return
        for step in (p.stdout.close, p.terminate, p.kill):
            try:
                step()
            except Exception:
                pass
        try:
            p.wait(timeout=5)
        except Exception:
            pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # -- rendering ---------------------------------------------------------
    def frame(self, i, n):
        img = self._next()
        if img.size != (W, H):          # a plain footage scene never crops in
            img = img.resize((W, H), Image.LANCZOS)

        if self.grade:
            img = ImageEnhance.Color(img).enhance(0.88)
            img = ImageEnhance.Contrast(img).enhance(1.08)

        # darken the top band so type stays readable over any footage
        if self.title:
            band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bd = ImageDraw.Draw(band)
            for k in range(int(H * .42)):
                a = int(235 * self.darken * (1 - k / (H * .42)) ** 1.3)
                bd.line([0, k, W, k], fill=Brand.FLOOR + (a,))
            img = Image.alpha_composite(img.convert("RGBA"), band).convert("RGB")

        d = ImageDraw.Draw(img)
        if self.title:
            p = ease_out(seg(i, 0, FPS * .4))
            f = Brand.head(74)
            lines = wrap(d, self.title, f, W - 2 * SAFE)
            while len(lines) > 2 and f.size > 46:
                f = Brand.head(f.size - 6); lines = wrap(d, self.title, f, W - 2 * SAFE)
            y = TOP_SAFE + 6
            for ln in lines:
                d.text((SAFE, y + int((1 - p) * 22)), ln, font=f,
                       fill=tuple(int(c * p) for c in Brand.WHITE))
                y += int(f.size * 1.1)
            d.line([SAFE, y + 16, SAFE + int(240 * p), y + 22],
                   fill=Brand.PITCH_LIT, width=7)
            if self.sub:
                sp = ease_out(seg(i, FPS * .35, FPS * .4))
                fs = Brand.body(38)
                yy = y + 46
                for ln in wrap(d, self.sub, fs, W - 2 * SAFE):
                    d.text((SAFE, yy), ln, font=fs,
                           fill=tuple(int(c * sp) for c in (200, 212, 204)))
                    yy += int(fs.size * 1.3)

        # stock has to say so, on the frame
        if self.source == "stock" and self.label_stock:
            fl = Brand.body(24)
            txt = self.credit or "Library footage · not SoccerTex's floor"
            tw = d.textlength(txt, font=fl)
            d.rectangle([SAFE - 10, H - BOT_SAFE + 28, SAFE + tw + 10,
                         H - BOT_SAFE + 62], fill=(0, 0, 0))
            d.text((SAFE, H - BOT_SAFE + 32), txt, font=fl, fill=(168, 182, 174))

        return vignette(grain(img, 3, i), .28)


def available(pool="own"):
    """What clips are on hand."""
    d = OWN if pool == "own" else STOCK
    d.mkdir(parents=True, exist_ok=True)
    return sorted(p for p in d.iterdir()
                  if p.suffix.lower() in (".mp4", ".mov", ".m4v", ".webm"))


def report():
    for pool in ("own", "stock"):
        clips = available(pool)
        print(f"{pool:6s} {len(clips)} clip(s)")
        for c in clips:
            m = probe(c)
            dur = m.get("duration") or m.get("format.duration") or "?"
            print(f"   {c.name:44s} {m.get('width','?')}x{m.get('height','?')}  {dur}s")


if __name__ == "__main__":
    report()
