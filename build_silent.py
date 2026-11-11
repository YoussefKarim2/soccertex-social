#!/usr/bin/env python3
"""Render the fast-cut, captions-only reels.

Ten topics to start, chosen for two reasons: they are the ones a buyer acts
on, and four of them had to be re-rendered anyway after the accuracy pass on
11 Nov (gsm, heat-press, europe-duty, and the corrected origin wording).

Each entry is a script written to be *read*, not spoken — short lines, one
idea each, the number early. Where the argument is really a quantity, a drawn
scene carries it instead of a caption, because four stock clips cannot carry
thirty videos and a bar that moves says more than a sentence about a bar.

    python3 build_silent.py              # all ten
    python3 build_silent.py gsm          # one
"""
from __future__ import annotations
import sys
from pathlib import Path

from engine.render import Video, Brand, FPS
from engine.silent import (beats, Captions, MeterScene, RaceScene, TypeScene,
                           footage_run, CUT)
from engine.bank import BANK

ROOT = Path(__file__).resolve().parent
CLIPS = ROOT / "assets" / "footage" / "proxy"
OUT = ROOT / "out" / "video"

SEW_V = CLIPS / "sewing-machine-vertical.mp4"       # the only 4K vertical one
SEW_W = CLIPS / "sewing-machine-working.mp4"
CUTF = CLIPS / "cutting-fabric-scissors.mp4"
ROLL = CLIPS / "fabric-production-overhead.mp4"

# (clip, tight, focus). SEW_V takes the hard close-ups because it is the only
# clip with the pixels for one; the others stay wide and earn their place by
# being different rather than tighter.
PLATES = [
    (SEW_V, 1.9, (.5, .60)), (ROLL, 1.2, (.5, .45)),
    (CUTF, 1.1, (.42, .5)), (SEW_V, 2.0, (.56, .40)),
    (SEW_W, 1.1, (.5, .5)), (ROLL, 1.15, (.38, .6)),
    (SEW_V, 1.7, (.46, .52)), (CUTF, 1.05, (.6, .42)),
]


# ------------------------------------------------------------- the scripts --
# Written for the buyer: a kit manager or distributor in the US or Europe
# deciding whether a supplier knows their trade. Every number here is either
# industry fact or a SoccerTex figure the website already publishes.
SCRIPTS = {
    "gsm": dict(
        hook=["NOBODY ASKS", "FOR GSM"],
        hook_sub="It's the one number on every quote.",
        script=[
            "GSM is grams per square metre.",
            "It's just fabric weight.",
            "And it's the number that tells you what you're actually buying.",
            "Here's the whole scale.",
            "So when a kit arrives lighter than you expected,",
            "that isn't a bargain. It's less fabric.",
            "Ask for the GSM before you ask for the price.",
        ],
        draw=(3, lambda: MeterScene(
            [(130, 150, "Match jersey"), (150, 180, "Training top"),
             (180, 220, "Polo, warm-up"), (240, 320, "Hoodie, sweat")],
            title="FABRIC WEIGHT", seconds=5.2)),
        chapters={},
    ),

    "lead-time": dict(
        hook=["TWO WEEKS", "OR FOURTEEN"],
        hook_sub="Same deadline. Two different seasons.",
        script=[
            "Every kit has one deadline that matters.",
            "In clubs' hands for pre-season.",
            "Watch what the lead time does to it.",
            "At fourteen weeks you're approving in January.",
            "Committing to next season before this one has finished.",
            "At two weeks you approve in April.",
            "Same delivery. Four months better informed.",
            "The cost of a long lead time isn't waiting.",
            "It's deciding early.",
        ],
        draw=(2, lambda: RaceScene("FROM APPROVAL TO DELIVERY",
                                   ("Typical chain", 14, False),
                                   ("SoccerTex build", 2, True), seconds=5.4)),
        chapters={},
    ),

    "cheap-vs-good": dict(
        hook=["A FIFTEEN POUND", "JERSEY"],
        hook_sub="And a forty-five pound one. Same photo.",
        script=[
            "Three things separate them.",
            "None of them show in a product shot.",
            "One. Fabric weight. Lighter isn't cheaper by accident.",
            "It's less yarn.",
            "Two. The seams. Overlocked rubs at seventy minutes.",
            "Flatlocked doesn't.",
            "Three. How the badge went on. Printed vinyl peels.",
            "Sublimated ink can't.",
            "Ask for GSM and seam type.",
            "Those two tell you more than the price does.",
        ],
        turn=(2, ["WHAT YOU", "CAN'T SEE"]),
        chapters={2: (1, "Fabric"), 4: (2, "Seams"), 6: (3, "The badge")},
    ),

    "heat-press": dict(
        hook=["NOTHING.", "THEN EVERYTHING."],
        hook_sub="Sixty seconds at 200°C.",
        script=[
            "This is a sublimation press.",
            "Blank polyester goes in with a paper transfer.",
            "The ink turns to gas and bonds inside the fibre.",
            "The paper comes out grey. The colour has left it.",
            "Nothing sits on top. Nothing can peel.",
            "The trade-off is real.",
            "Polyester only, and it can't print white onto dark.",
            "Those are limits, not fine print.",
        ],
        chapters={},
    ),

    "europe-duty": dict(
        hook=["EGYPT SHIPS", "TO EUROPE", "DUTY-FREE"],
        hook_sub="Since 2004. Most brands don't know it.",
        script=[
            "Egyptian garment exports to Europe grew forty-six percent.",
            "To 930 million dollars, in seven months.",
            "Spain alone was up eighty-six percent.",
            "There's a structural reason.",
            "The EU–Egypt agreement has been in force since 2004.",
            "Egyptian industrial goods enter the EU without duty.",
            "And European or Turkish fabric can still count towards origin.",
            "If a European fabric spec pushed you to European prices,",
            "it didn't have to.",
        ],
        turn=(3, ["46%", "TO EUROPE"], "Jan–Jul 2026, Export Council"),
        chapters={},
    ),

    "seams": dict(
        hook=["THIS SEAM IS WHY", "IT DOESN'T RUB"],
        hook_sub="And most tech packs never specify it.",
        script=[
            "A flatlock seam butts two pieces edge to edge.",
            "Stitched flat. No ridge on the inside.",
            "That's the shirt you forget you're wearing.",
            "An overlock folds the edge over itself.",
            "Faster, cheaper, and fine on a leisure tee.",
            "On a match shirt it's the wrong choice.",
            "It chafes at seventy minutes.",
            "Most tech packs don't specify the seam at all.",
            "Then wonder why the fit feels different from the sample.",
        ],
        chapters={0: (1, "Flatlock"), 3: (2, "Overlock")},
    ),

    "recovery-test": dict(
        hook=["STRETCH ISN'T", "THE TEST"],
        hook_sub="Recovery is. It takes two seconds.",
        script=[
            "Everyone tests stretch.",
            "Almost nobody tests recovery.",
            "Stretch is how far the fabric goes.",
            "Recovery is whether it comes back.",
            "Pull a cuff. Let go. Watch it.",
            "Straight back? Good recovery.",
            "Still slightly open? That's the shirt that looks tired by March.",
            "Two seconds, and it tells you more than the label does.",
        ],
        chapters={},
    ),

    "white-kit": dict(
        hook=["YOUR WHITE KIT", "WENT GREY"],
        hook_sub="Only one of three reasons is the factory's fault.",
        script=[
            "Three reasons white kit goes grey.",
            "One. Polyester picks up dye from everything else in the wash.",
            "Nothing in manufacturing fixes that.",
            "Two. Optical brighteners wash out.",
            "They were never permanent.",
            "Three. Low-grade fabric, uneven whiteness from the start.",
            "That one is on the factory.",
            "Ask for the whiteness grade on white polyester.",
            "It's a spec, and it's rarely volunteered.",
        ],
        chapters={1: (1, "The wash"), 3: (2, "Brighteners"), 5: (3, "The fabric")},
    ),

    "small-orders": dict(
        hook=["THEY STOPPED", "REPLYING"],
        hook_sub="About your 300 pieces. Here's why.",
        script=[
            "Most big factories won't take three hundred pieces.",
            "The setup costs them more than the order earns.",
            "So they go quiet rather than say no.",
            "That's a capacity mismatch.",
            "It isn't a verdict on your brand.",
            "Four lines. Two thousand pieces a day.",
            "Four decoration methods in one building.",
            "That's a structure built for short custom runs.",
            "If you've been ghosted over a small order, send the quantity.",
        ],
        chapters={},
    ),

    "sublimation-limits": dict(
        hook=["SUBLIMATION", "CAN'T PRINT", "ON COTTON"],
        hook_sub="Anyone saying otherwise will disappoint you.",
        script=[
            "Sublimation can't print on one hundred percent cotton.",
            "The chemistry doesn't work.",
            "The ink needs a polymer to bond into.",
            "A supplier who says otherwise will coat the cotton,",
            "which changes the hand-feel,",
            "or deliver something that fades fast.",
            "For a cotton range: screen print, embroidery, or heat transfer.",
            "Or change the fabric.",
            "Pick the fabric for how it should feel.",
            "Then pick decoration to suit.",
        ],
        chapters={},
    ),
}


def build(tid: str) -> Video:
    spec = SCRIPTS[tid]
    topic = next(t for t in BANK if t["id"] == tid)
    out = OUT / f"{tid}--social.mp4"
    v = Video(out)

    # 1. the hook — flat colour, no footage, readable in one glance
    v.add(TypeScene(spec["hook"], seconds=1.9, sub=spec.get("hook_sub"),
                    bg=Brand.DEEP, size=104))

    # 2. the body, as caption beats over cuts, with a drawn scene or a hard
    #    turn spliced in at the line the script reaches it
    tl, total = beats(spec["script"], start=0.0)
    caps = Captions(tl, size=94, y_frac=0.60)

    split_at = None
    if spec.get("draw"):
        split_at = spec["draw"][0]
    elif spec.get("turn"):
        split_at = spec["turn"][0]

    def line_time(li):
        return next((c["start"] for c in tl if c["line"] == li), total)

    shown = set()
    if split_at is None:
        footage_run(v, PLATES, caps, 0.0, total, spec.get("chapters"), shown)
    else:
        cut_t = line_time(split_at)
        footage_run(v, PLATES, caps, 0.0, cut_t, spec.get("chapters"), shown)
        if spec.get("draw"):
            v.add(spec["draw"][1]())
        else:
            t = spec["turn"]
            v.add(TypeScene(t[1], seconds=2.0, bg=Brand.PITCH,
                            accent=Brand.AMBER,
                            sub=(t[2] if len(t) > 2 else None), size=112))
        # the caption track resumes where it left off, so the drawn scene is
        # a pause in the reading rather than a hole in it
        rest = [dict(c, start=c["start"] - cut_t, end=c["end"] - cut_t)
                for c in tl if c["start"] >= cut_t]
        if rest:
            caps2 = Captions(rest, size=94, y_frac=0.60)
            footage_run(v, PLATES[3:] + PLATES[:3], caps2, 0.0,
                        rest[-1]["end"], spec.get("chapters"), shown)

    # 3. the close
    v.add(TypeScene(["SEE THE FLOOR."], seconds=1.8, bg=Brand.PITCH,
                    accent=Brand.MINT, sub="soccertexhq.com · Cairo, Egypt",
                    size=96))
    return v


def main():
    which = sys.argv[1:] or list(SCRIPTS)
    bad = [t for t in which if t not in SCRIPTS]
    if bad:
        sys.exit(f"no script for: {', '.join(bad)}")
    OUT.mkdir(parents=True, exist_ok=True)
    import subprocess
    for tid in which:
        v = build(tid)
        v.write(music=True, bpm=126, quiet=False)
        # Same guard build_all.py got after a 1.8s render came within two days
        # of publishing: trust the file on disk, not the composer's intent.
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", str(v.out)],
                           capture_output=True, text=True)
        got = float(r.stdout.strip() or 0)
        if got < v.seconds * 0.9 or got < 8.0:
            v.out.unlink(missing_ok=True)
            raise RuntimeError(f"{tid}: only {got:.1f}s on disk, "
                               f"composer wrote {v.seconds:.1f}s — deleted")
        print(f"  {tid}: {got:.1f}s on disk, {len(v.scenes)} cuts  OK")


if __name__ == "__main__":
    main()
