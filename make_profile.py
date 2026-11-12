#!/usr/bin/env python3
"""Instagram profile assets, built from the same brand system as the reels.

The colours and fonts here are not a guess. Scraping soccertexhq.com returns
primary #148444, Secular One for headings and Roboto for body, which is
exactly what engine/render.py already uses — so the avatar, the videos and the
website are one system rather than three near-misses.

The real logo mark is not usable: the only copy on the Mac is a screenshot of
a browser window with the app chrome still in it, and neither the container
nor the Mac's shell can reach soccertexhq.com to pull a clean one. So this
draws a wordmark avatar that works at the size an avatar is actually seen —
32 pixels in a feed, where a detailed emblem turns to soup anyway.

    python3 make_profile.py
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine.render import Brand

OUT = Path(__file__).resolve().parent / "out" / "profile"
S = 1080


def avatar_wordmark(path: Path):
    """Green field, white wordmark, a pitch line. Legible at 32px."""
    img = Image.new("RGB", (S, S), Brand.PITCH)
    d = ImageDraw.Draw(img)

    # a faint off-centre circle so the mark has some depth inside the crop
    d.ellipse([-S * 0.30, S * 0.18, S * 0.72, S * 1.20],
              fill=(17, 118, 62))

    f = Brand.head(196)
    txt = "SOCCER"
    w = d.textlength(txt, font=f)
    while w > S * 0.78:
        f = Brand.head(f.size - 6); w = d.textlength(txt, font=f)
    d.text(((S - w) / 2, S * 0.285), txt, font=f, fill=Brand.WHITE)

    f2 = Brand.head(196)
    t2 = "TEX"
    w2 = d.textlength(t2, font=f2)
    d.text(((S - w2) / 2, S * 0.285 + f.size * 1.02), t2, font=f2,
           fill=Brand.MINT)

    # the pitch line — the one graphic element the reels also use
    y = int(S * 0.285 + f.size * 1.02 + f2.size * 1.18)
    d.rounded_rectangle([S * 0.32, y, S * 0.68, y + 16], 8, fill=Brand.AMBER)
    img.save(path, quality=95)
    return path


def avatar_monogram(path: Path):
    """The alternative: a single ST monogram, which survives being tiny."""
    # Full-bleed green, no inset circle: Instagram crops an avatar to a circle
    # itself, and an inset one leaves a dark ring around the edge of the crop.
    img = Image.new("RGB", (S, S), Brand.PITCH)
    d = ImageDraw.Draw(img)
    d.ellipse([-S * 0.34, S * 0.10, S * 0.66, S * 1.10], fill=(17, 118, 62))
    f = Brand.head(430)
    txt = "ST"
    w = d.textlength(txt, font=f)
    d.text(((S - w) / 2, S * 0.255), txt, font=f, fill=Brand.WHITE)
    d.rounded_rectangle([S * 0.36, S * 0.70, S * 0.64, S * 0.715], 8,
                        fill=Brand.AMBER)
    img.save(path, quality=95)
    return path


# ------------------------------------------------------------------ copy ----
# Instagram's real limits: name 30 characters, bio 150. The bio Youssef chose
# put the name line inside the bio; it belongs in the name field, which is
# also what gets searched.
NAME = "SoccerTex · Teamwear Factory"

BIO = ("700+ customers in 40 countries\n"
       "2-week production · duty-free into the EU\n"
       "Cairo, Egypt ↓")

LINK = "https://soccertexhq.com/get-your-quote"

# Everything below is on soccertexhq.com already, so none of it is a new claim.
NOTES = """\
Category      Clothing (Brand)  — or "Product/Service" if Clothing isn't offered
Contact       Email button on; phone only if you want it public
Link          %s
              (the quote page, not the home page — it is the one page with an
               action on it, and the bio arrow points at it)
City          Cairo  — currently typed "Cario" in the business address
""" % LINK


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    a = avatar_wordmark(OUT / "avatar-wordmark.jpg")
    b = avatar_monogram(OUT / "avatar-monogram.jpg")

    # a side-by-side at the size an avatar is actually seen, because that is
    # the only test that matters
    sheet = Image.new("RGB", (1080, 560), (16, 16, 16))
    for i, p in enumerate((a, b)):
        im = Image.open(p)
        sheet.paste(im.resize((380, 380)), (60 + i * 520, 40))
        for j, size in enumerate((110, 56, 32)):
            sheet.paste(im.resize((size, size)),
                        (60 + i * 520 + j * 130, 450))
    sheet.save(OUT / "avatar-options.jpg", quality=92)

    print(f"name  ({len(NAME):>3}/30)  {NAME}")
    print(f"bio   ({len(BIO):>3}/150)")
    for line in BIO.split("\n"):
        print(f"               {line}")
    print()
    print(NOTES)
    print(f"written to {OUT}")


if __name__ == "__main__":
    main()
