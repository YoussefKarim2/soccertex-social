#!/usr/bin/env python3
"""Render the library so that no two reels look, move or sound alike.

    python3 build_vibes.py                      every topic, both cuts
    python3 build_vibes.py --social gsm seams   named topics, Instagram cut
    python3 build_vibes.py --list               which topic gets which look

HOW IT GOT HERE
15 Nov, morning: "all the videos are the same but only the words are
different." Seven formats were built. 15 Nov, evening: Youssef picked the four
he liked — europe-duty (poster), kit-decisions and seams (blueprint) and
wrong-supplier (versus) — and asked for those on everything, with every upload
different in pace and feel from the next.

So the library is three families, the ones he chose, and the variety now
comes from inside them: seven poster colourways in two alignments and two
motions, four drafting sheets with nine kinds of drawing, three versus
palettes in two modes, and three paces with a soundtrack to match. The chat,
notebook and documentary formats are still in engine/vibes.py, unused; a topic
can be moved back to one by giving it a spec here.

`check_spread()` holds the two promises: no family next to itself (the same
day, or consecutive days), and no two reels in the whole library with the
same look.

15 Nov, night: "i like the videos vibe ... but i want more real life videos of
factory videos, such as cutting, stitching." So the look stays and real footage
is cut into it — eighteen library clips of cutting, sewing, embroidery,
printing, pressing and mills. A reel opens on one, and lines about a process
play over that process. It is library footage, stamped as such on every frame,
and never carries SoccerTex's own voice; `check_footage()` keeps two reels that
post back to back from opening on the same clip.

Every line on screen comes from engine/bank.py — reworded and cut down, never
added to.
"""
from __future__ import annotations
import subprocess, sys, zlib
from pathlib import Path

from engine.render import Video
from engine.bank import BANK
from engine import vibes as V
from engine.vibes import Poster, VersusScene, BlueprintScene, CloseCard, Plate, Breaks, clip
from build_silent import CLOSE

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out" / "video"

# pace → (how long things hold, tempo and mood by family)
PACE = {
    "fast":   dict(hold=0.88, poster=(140, "punch"), blueprint=(122, "drive"), versus=(132, "punch")),
    "steady": dict(hold=1.00, poster=(124, "drive"), blueprint=(108, "calm"),  versus=(118, "drive")),
    "slow":   dict(hold=1.12, poster=(104, "calm"),  blueprint=(94,  "calm"),  versus=(100, "calm")),
}

# topic → (family, colourway, variant, pace).
# variant is "<alignment>/<motion>" for a poster, the drawing for a blueprint,
# and the mode for a versus.
LOOK = {
    "lead-time":          ("versus",    "dark",      "duel",        "fast"),
    "season-calendar":    ("poster",    "paper",     "left/pop",    "steady"),
    "price-drivers":      ("blueprint", "sheet",     "bars",        "steady"),
    "europe-duty":        ("poster",    "ink",       "left/pop",    "steady"),     # as he liked it
    "pem-cumulation":     ("blueprint", "blueprint", "chain",       "slow"),
    "tech-pack":          ("poster",    "pitch",     "left/rise",   "fast"),
    "wrong-supplier":     ("versus",    "dark",      "stack",       "steady"),     # as he liked it
    "small-orders":       ("poster",    "navy",      "center/pop",  "steady"),
    "trading-company":    ("blueprint", "night",     "flags",       "fast"),
    "buyer-questions":    ("poster",    "blue",      "left/rise",   "slow"),
    "decoration":         ("blueprint", "chalk",     "layers",      "steady"),
    "gsm":                ("poster",    "mint",      "center/pop",  "steady"),
    "fabric-glossary":    ("blueprint", "sheet",     "swatch",      "fast"),
    "cheap-vs-good":      ("poster",    "sunset",    "left/pop",    "fast"),
    "seams":              ("blueprint", "blueprint", "seam",        "steady"),     # as he liked it
    "sublimation-limits": ("poster",    "ink",       "center/rise", "steady"),
    "white-kit":          ("blueprint", "night",     "chain",       "slow"),
    "recovery-test":      ("poster",    "paper",     "center/pop",  "slow"),
    "factory-questions":  ("blueprint", "chalk",     "checklist",   "fast"),
    "shrinkage":          ("versus",    "light",     "stack",       "steady"),
    "quality":            ("blueprint", "sheet",     "chain",       "steady"),
    "cutting":            ("poster",    "pitch",     "center/pop",  "steady"),
    "sewing-line":        ("blueprint", "night",     "jersey",      "steady"),
    "embroidery":         ("poster",    "navy",      "left/rise",   "fast"),
    "heat-press":         ("blueprint", "chalk",     "press",       "slow"),
    "nameset":            ("poster",    "blue",      "center/pop",  "steady"),
    "kit-decisions":      ("blueprint", "blueprint", "jersey",      "steady"),     # as he liked it
    "goalkeeper":         ("poster",    "mint",      "left/rise",   "slow"),
    "reorder":            ("versus",    "court",     "duel",        "steady"),
    "packing":            ("poster",    "sunset",    "center/rise", "fast"),
}


def check_spread():
    ids = [t["id"] for t in BANK]
    missing = [i for i in ids if i not in LOOK]
    if missing:
        sys.exit(f"no look chosen for: {', '.join(missing)}")
    n = len(ids)
    for i, tid in enumerate(ids):
        nxt, pair = ids[(i + 1) % n], ids[(i + n // 2) % n]
        if LOOK[tid][0] == LOOK[nxt][0]:
            sys.exit(f"{tid} and {nxt} post on consecutive days and are both {LOOK[tid][0]}")
        if LOOK[tid][0] == LOOK[pair][0]:
            sys.exit(f"{tid} and {pair} post on the same day and are both {LOOK[tid][0]}")
    seen = {}
    for tid in ids:
        key = LOOK[tid][:3]
        if key in seen:
            sys.exit(f"{tid} and {seen[key]} would look the same: {' / '.join(key)}")
        seen[key] = tid


def opening_clip(tid):
    """The library clip a reel opens on, or None if it opens on a drawn card."""
    v, _ = build(tid, "social")
    first = v.scenes[0]
    shot = (first if isinstance(first, Plate)
            else first.shots.get(-1) if isinstance(first, BlueprintScene)
            else first.inner.hookshot if isinstance(first, Breaks) else None)
    for s in v.scenes:
        s.close()
    return shot.path.stem if shot else None


def check_footage():
    """Two reels a viewer sees back to back must not open on the same clip."""
    ids = [t["id"] for t in BANK]
    first = {tid: opening_clip(tid) for tid in ids}
    n = len(ids)
    for i, tid in enumerate(ids):
        for other in (ids[(i + 1) % n], ids[(i + n // 2) % n]):
            if first[tid] and first[tid] == first[other]:
                sys.exit(f"{tid} and {other} post back to back and both open on {first[tid]}")
    return first


# ─────────────────────────────────────────────────────────────── poster ─────
def poster(tid, P):
    s, y, c, fs, fy = P.slam, P.say, P.count, P.fslam, P.fsay
    if tid == "europe-duty":
        return [fs(clip("sewing-machine-vertical", 4), ["EGYPT", "SHIPS TO", "EUROPE", "DUTY-FREE"],
                   "Since 2004. Most brands don't know it.", hi=3, scheme=0),
                c(46, "%", "Growth in Egyptian garment exports to Europe", "First seven months of 2026. Spain alone was up 86%."),
                s(["SINCE", "JUNE 2004"], "EU–Egypt Association Agreement, in force.", scheme=1),
                s(["NO DUTY"], "Egyptian industrial goods enter the EU without duty.", scheme=0),
                fy(clip("fabric-production-overhead", 2), "PEM origin rules let EU or Turkish fabric still count as Egyptian.", scheme=1),
                s(["3 TO 7", "DAYS"], "By sea to Southern European ports.", hi=0, scheme=0)]
    if tid == "season-calendar":
        return [fs(clip("sewing-factory", 1), ["WORK", "BACKWARDS", "FROM JULY"], "Most brands get this date wrong by two months.", hi=2),
                s(["1 JULY"], "Kit with clubs."),
                s(["MINUS", "1–2 WEEKS"], "Your own distribution and namesets."),
                s(["MINUS", "1 WEEK"], "Sea transit to Southern Europe."),
                fs(clip("sewing-floor", 3), ["MINUS", "2 WEEKS"], "Bulk production."),
                fs(clip("fabric-check", 5), ["MINUS", "1–2 WEEKS"], "Sample approval."),
                s(["MINUS", "1–2 WEEKS"], "Tech pack and lab dips."),
                y("Approve your sample by the first half of April.")]
    if tid == "tech-pack":
        items = ["A sketch or a photo of a garment you like — front and back.",
                 "Fabric intent — composition and GSM, or just “like this shirt”.",
                 "Colourways, with Pantone references if you have them.",
                 "Size range and rough split.",
                 "Quantity per colourway, not just the total.",
                 "Decoration — what goes where, at what size.",
                 "Trims and labels.",
                 "The real deadline, not the one you'd like."]
        over = {1: clip("pressing", 6), 2: clip("thread-spools", 2), 5: clip("sewing-machine-working", 3),
                6: clip("sewing-threading", 1)}
        return ([s(["EIGHT THINGS", "AND WE CAN", "QUOTE YOU"], "Five of them you already know.", hi=0)]
                + [fy(over[k], t, n=k + 1) if k in over else y(t, n=k + 1) for k, t in enumerate(items)]
                + [y("Enough to quote a price we'll stand behind.")])
    if tid == "small-orders":
        return [fs(clip("embroidery-line", 0), ["THEY STOPPED", "REPLYING"], "About your 300 pieces.", hi=1),
                s(["IT WASN'T", "YOUR BRAND."]), s(["IT WAS", "THE MATHS."], hi=1),
                fy(clip("fabric-production-overhead", 8), "Big factories need big runs — setup costs them more than you pay."),
                fy(clip("cutting-knife", 2), "A colourway is a fabric lot, a lab dip and a cut, whatever the quantity."),
                y("Short custom runs are a different cost structure, not a favour."),
                s(["SEND YOUR", "REAL", "QUANTITY"], "We'll tell you straight.")]
    if tid == "buyer-questions":
        qs = ["Which operations happen in this building, and which leave it?",
              "Show me the floor on a live video call this week.",
              "What's your MOQ per colourway, not per style?",
              "What certifications do you hold, and when were you last audited?",
              "What was the last order you got wrong, and what happened next?"]
        over = {0: clip("sewing-factory", 6), 2: clip("thread-spools", 6)}
        return ([fs(clip("sewing-threading", 4), ["WHAT I'D ASK", "IF I WERE", "BUYING"],
                    "Including the two I'd least like to be asked.", hi=2)]
                + [fy(over[k], q, n=k + 1) if k in over else y(q, n=k + 1) for k, q in enumerate(qs)]
                + [s(["TWO OF THEM", "ARE", "UNCOMFORTABLE."], "Ask anyway.")])
    if tid == "gsm":
        return [fs(clip("fabric-production-overhead", 12), ["THE ONE", "FABRIC NUMBER", "NOBODY", "EXPLAINS"],
                   "And it's on every quote you'll ever read.", hi=1),
                fy(clip("pressing", 6), "GSM is grams per square metre. It's just fabric weight."),
                s(["130–150"], "GSM — match jersey."), s(["150–180"], "GSM — training top."),
                s(["180–220"], "GSM — polo, warm-up."), s(["240–320"], "GSM — hoodie, sweat."),
                c(150, " GSM", "Where a match jersey tops out", "Above this you're buying a training top."),
                fy(clip("mill-process", 3), "Lighter isn't cheaper by accident. It's less of it.")]
    if tid == "cheap-vs-good":
        return [fs(clip("cutting-fabric-scissors", 0), ["A £15 JERSEY", "AND A", "£45 JERSEY"], "Same photo. Different garment.", hi=2),
                s(["WHAT YOU", "CAN'T SEE"], "Three things that never show in a product shot."),
                fy(clip("mill-worker", 2), "£15: lighter fabric, less yarn. £45: the correct GSM for the job.", n=1),
                fy(clip("sewing-closeup", 1), "£15: overlocked seams that rub. £45: flatlocked seams, no ridge.", n=2),
                y("£15: a printed vinyl badge that peels. £45: a sublimated or stitched badge.", n=3)]
    if tid == "sublimation-limits":
        return [fs(clip("wide-printer", 5), ["SUBLIMATION", "CANNOT", "PRINT ON", "COTTON"],
                   "Anyone saying otherwise is about to disappoint you.", hi=3),
                y("Sublimation needs polyester. On cotton there's nothing for the ink to bond to."),
                fs(clip("screen-printing", 3), ["SCREEN", "PRINT"], "The standard answer for cotton."),
                fs(clip("embroidery-line", 4), ["EMBROIDERY"], "Works on anything, best for small marks."),
                s(["HEAT", "TRANSFER"], "Works on cotton, application is everything."),
                y("Or change the fabric: a poly-cotton blend takes it, softer and more muted.")]
    if tid == "recovery-test":
        return [fs(clip("pressing", 9), ["STRETCH", "ISN'T", "THE TEST."]),
                s(["RECOVERY", "IS."], "Two seconds, and it tells you more than the label.", hi=0, scheme=0),
                fy(clip("mill-process", 7), "Stretch is how far the fabric goes. Recovery is whether it comes back."),
                s(["PULL", "THE CUFF."], "Then let go and watch."),
                y("Instant return means good recovery."),
                y("Stays slightly open? That's the shirt that looks tired by March.")]
    if tid == "cutting":
        return [fs(clip("cutting-machine", 0), ["SIXTY", "LAYERS,", "ONE PASS"], "Everything after this depends on getting it right.", hi=2),
                fy(clip("cutting-knife", 5), "Fabric spread in layers, pattern laid out as a marker.", n=1),
                fy(clip("cutting-fabric-scissors", 1), "Get the marker wrong and you waste fabric on every garment.", n=2),
                y("The cut is inspected before anything moves to the line.", n=3),
                y("Piece count checked against the marker.", n=4),
                s(["STACKED.", "IDENTICAL."], "That is how the pieces come off.")]
    if tid == "embroidery":
        return [fs(clip("sewing-machine-working", 0), ["FIFTEEN", "THOUSAND", "STITCHES,", "ONE CREST"], "You can feel it. That's the point.", hi=3),
                fy(clip("embroidery-line", 2), "Multiple needles, one colour each, swapping as the design builds."),
                fs(clip("sewing-machine-working", 9, tight=1.15, focus=(.5, .7)), ["ON TOP,", "NOT INSIDE"],
                   "Thread sits on the surface — the premium feel, and the added weight."),
                s(["CRESTS.", "SPONSOR", "MARKS."], "What it is best for."),
                y("Not for full-garment graphics. That's sublimation.")]
    if tid == "nameset":
        return [fs(clip("fabric-check", 0), ["NAMES AND", "NUMBERS ARE", "WHERE KIT", "GOES WRONG"],
                   "Four variables, and one wrong shows up in March.", hi=3),
                s(["FILM", "TYPE"], "Decides hand-feel and how far it reads."),
                s(["TEMPERATURE", "AND DWELL", "TIME"], "Decide whether it stays on."),
                fs(clip("pressing", 9), ["PRESSURE"], "Decides the edge quality."),
                y("We run 3D, reflective, fluor, matt and silicone.")]
    if tid == "goalkeeper":
        return [fs(clip("sewing-machine-vertical", 16), ["A KEEPER SHIRT", "ISN'T AN", "OUTFIELD SHIRT", "WITH LONG SLEEVES"], "Four things change.", hi=0),
                fy(clip("sewing-closeup", 3), "Elbow padding changes the sleeve construction.", n=1),
                fy(clip("mill-process", 0), "Heavier fabric, because it meets the ground.", n=2),
                y("Looser cut through the body, for reach.", n=3),
                y("Different colour rules — it has to contrast with both teams.", n=4),
                s(["BUILT FOR", "A DIFFERENT", "JOB."])]
    if tid == "packing":
        return [s(["THIS IS WHAT", "A DAY", "LOOKS LIKE"], "Folded, bagged, cartoned, labelled.", hi=1),
                c(2000, "", "Pieces a day", "Then 3 to 7 days by sea to Southern Europe."),
                s(["TRIM.", "MEASURE.", "PRESS."]), s(["FOLD.", "BAG.", "CARTON."]),
                y("The last of the five inspection points. It checks decoration adhesion and final measurements."),
                fy(clip("pressing", 8), "A well-made garment badly folded arrives looking cheap.")]
    raise KeyError(tid)


# ─────────────────────────────────────────────────────────────── versus ─────
VS = {
    "lead-time": (["14 WEEKS", "VS", "2 WEEKS"], "Same deadline. Two different seasons.",
        "APPROVE YOUR DESIGN",
        ("14-WEEK CHAIN", ["Approve in January", "Commit before this season ends", "No way to react in May"]),
        ("2-WEEK BUILD", ["Approve in April", "Decide with better information", "Absorb a 200-piece add-on"]),
        "Two weeks of production. Published, so you can plan around it."),
    "wrong-supplier": (["WE'RE THE", "WRONG FACTORY", "FOR PLENTY", "OF BRIEFS"], "Here's how to tell in ten seconds.",
        "IS THIS YOU?",
        ("WRONG FIT", ["100,000 pieces in 30 days", "Commodity blanks at lowest cost",
                       "Certified supplier required today", "Footwear, bags, hard goods"]),
        ("RIGHT FIT", ["Custom teamwear or kit", "Several decoration methods on one garment",
                       "A deadline that needs 2 weeks", "Europe or the USA"]),
        "2,000 pieces a day across 4 lines. Built for custom runs that move."),
    "reorder": (["THE", "MID-SEASON", "REORDER"], "Where teamwear margins quietly die.",
        "A CLUB ADDS 200 PIECES IN MARCH",
        ("10-WEEK CHAIN", ["Arrives in June", "Season is over", "You eat it or you lose the club"]),
        ("2-WEEK BUILD", ["Arrives in April", "Still in season", "Same fabric lot if you planned it"]),
        "The order nobody plans for."),
    "shrinkage": (["IT SHRANK", "BECAUSE", "NOBODY ASKED"], "Shrinkage is a test, and it's free to demand.",
        "SAME FABRIC. TWO ORDERS.",
        ("NOBODY ASKED", ["Every knit fabric moves in the first wash", "No test, so nobody knows how much",
                          "You inherit whatever the fabric does"]),
        ("YOU SPECIFIED IT", ["A shrinkage test, before bulk is cut", "Patterns graded to compensate",
                              "A tolerance in the tech pack"]),
        "±3% is normal. ±5% is not."),
}


# ──────────────────────────────────────────────────────────── blueprint ─────
BP = {
    "price-drivers": ("SIX THINGS MOVE YOUR UNIT PRICE", "Quantity is only one, and rarely the biggest.",
        "RANKED BY HOW MUCH IT MOVES THE PRICE", [
        ("FABRIC", "Composition and GSM. The largest input cost"),
        ("COLOURWAYS", "Each one is its own lot, lab dip and cut"),
        ("DECORATION", "A sublimated body is nearly free; four embroidered placements are not"),
        ("PANEL COUNT", "A 12-panel jersey has more operations than a 6-panel"),
        ("SIZE RANGE", "Youth XS to adult 4XL needs a wider grade"),
        ("QUANTITY", "Real, but it flattens fast above 1,000")],
        lambda: V.bars_diagram(["FABRIC", "COLOURWAYS", "DECORATION", "PANEL COUNT", "SIZE RANGE", "QUANTITY"])),
    "pem-cumulation": ("THE ORIGIN RULE NOBODY USES", "European fabric, Egyptian make, duty-free entry.",
        "DIAGONAL CUMULATION", [
        ("THE FABRIC", "Specify a European or Turkish mill if your brand needs it"),
        ("THE MAKE", "Manufacture in Egypt at Egyptian conversion cost"),
        ("THE ORIGIN", "The garment can still qualify as Egyptian origin"),
        ("THE ENTRY", "Enters the EU duty-free under the 2004 agreement"),
        ("THE CATCH", "The paperwork changed in 2025 — check it with your broker")],
        lambda: V.flow_diagram(["EU OR TURKISH MILL", "MADE IN EGYPT", "EGYPTIAN ORIGIN",
                                "INTO THE EU, DUTY-FREE", "CHECK THE PAPERWORK"])),
    "trading-company": ("THREE SIGNS IT'S NOT REALLY A FACTORY", "None of them are about price.",
        "HOW TO TELL", [
        ("NO LIVE FLOOR", "They can't show you this week's floor on a live video call"),
        ("ONE CORNER", "Every photo is the same corner of the same room"),
        ("EVERYTHING", "They quote jerseys, shoes and backpacks from one building")],
        lambda: V.flags_diagram(["LIVE VIDEO", "PHOTOS", "PRODUCT LIST"])),
    "decoration": ("FOUR WAYS TO PUT A BADGE ON A SHIRT", "They are not interchangeable.",
        "WHERE THE MARK ACTUALLY SITS", [
        ("SUBLIMATION", "Ink bonds inside the fibre"),
        ("EMBROIDERY", "Thread stitched in. Raised, durable, adds weight"),
        ("HEAT TRANSFER", "Film applied under heat"),
        ("SCREEN PRINT", "Ink on the surface")], lambda: V.layers_diagram()),
    "fabric-glossary": ("THE WORDS ON EVERY TEAMWEAR QUOTE", "Recovery is the one brands skip.",
        "FABRIC GLOSSARY", [
        ("INTERLOCK", "Double-knit, smooth both sides, stable"),
        ("SINGLE JERSEY", "Lighter, curls at a raw edge"),
        ("PIQUÉ", "Textured waffle. The polo fabric"),
        ("MESH", "Open structure, for airflow panels"),
        ("JACQUARD", "Pattern knitted in, not printed"),
        ("RECOVERY", "Whether it returns to shape. Separate from stretch, and more important")],
        lambda: V.swatch_diagram(["interlock", "jersey", "pique", "mesh", "jacquard", "recovery"])),
    "seams": ("THIS SEAM IS WHY THE SHIRT DOESN'T RUB", "And most tech packs never specify it.",
        "FLATLOCK VS OVERLOCK", [
        ("FLATLOCK", "Edges butted and stitched flat. No inside ridge"),
        ("OVERLOCK", "Faster, cheaper, leaves a raised seam"),
        ("WHERE IT MATTERS", "Fine on a leisure tee. Wrong on a match jersey"),
        ("SPECIFY IT", "Put it in the tech pack or you get whichever is cheaper")], lambda: V.seam_diagram()),
    "white-kit": ("YOUR WHITE KIT WENT GREY", "Only one of the three reasons is the factory's fault.",
        "WHY WHITE FAILS", [
        ("THE WASH", "Polyester picks up dye from other garments in the wash"),
        ("BRIGHTENERS", "Optical brighteners wash out — they were never permanent"),
        ("THE FABRIC", "Low-grade fabric with uneven whiteness to begin with"),
        ("THE SPEC", "Ask for the whiteness grade. It's a spec, and it's rarely volunteered")],
        lambda: V.flow_diagram(["THE WASH", "BRIGHTENERS", "THE FABRIC", "THE SPEC"])),
    "factory-questions": ("SEVEN QUESTIONS BEFORE YOU SEND A DEPOSIT", "Number 7 sorts it out on its own.",
        "ASK THESE", [
        ("THE FABRIC", "What's the GSM and composition you're quoting?"),
        ("DECORATION", "Which decoration is in-house, which is subcontracted?"),
        ("LEAD TIME", "Lead time from approved sample, not from deposit?"),
        ("MOQ", "MOQ per colourway, not per style?"),
        ("INSPECTION", "How many inspection points, and what does each check?"),
        ("SHADE", "Who signs off a shade variance?"),
        ("THE FLOOR", "Can I see this week's floor on a live video call?")],
        lambda: V.checklist_diagram(["GSM AND COMPOSITION", "IN-HOUSE OR SUBCONTRACTED", "LEAD TIME FROM SAMPLE",
                                     "MOQ PER COLOURWAY", "INSPECTION POINTS", "SHADE VARIANCE", "THIS WEEK'S FLOOR, LIVE"])),
    "quality": ("MOST QUALITY PROBLEMS AREN'T SEWING PROBLEMS", "They're fabric problems nobody checked at intake.",
        "FIVE INSPECTION POINTS", [
        ("FABRIC ARRIVAL", "Shade, weight, flaws. The first one saves the most money"),
        ("PATTERN", "Grading across the size run"),
        ("BULK CUT", "Piece count against the marker, before anything moves"),
        ("SPECIAL SEWING", "Collars, plackets, sleeves"),
        ("FINISHING", "Adhesion, measurement, pack")],
        lambda: V.flow_diagram(["FABRIC ARRIVAL", "PATTERN", "BULK CUT", "SPECIAL SEWING", "FINISHING"])),
    "sewing-line": ("A JERSEY ISN'T SEWN BY ONE PERSON", "And that's exactly why it comes out consistent.",
        "THE LINE", [
        ("ONE OPERATION", "The garment moves down the line, one operation per station"),
        ("REPETITION", "It's what makes it consistent, not what makes it careless"),
        ("WHAT FAILS", "The operations that fail have stretch or shape"),
        ("WHAT GETS CHECKED", "Collars, plackets and sleeve insertions, specifically")],
        lambda: V.jersey_diagram([(.50, .66), (.50, .90), (.16, .30), (.50, .13)])),
    "heat-press": ("NOTHING. THEN EVERYTHING.", "Sixty seconds at 200°C.",
        "SUBLIMATION", [
        ("IN", "Blank polyester goes in with a paper transfer"),
        ("HEAT", "The ink turns to gas and bonds inside the fibre"),
        ("OUT", "The paper comes off grey — the colour has left it"),
        ("RESULT", "Nothing to feel, nothing to peel")], lambda: V.press_diagram()),
    "kit-decisions": ("ONE KIT. ELEVEN DECISIONS.", "None of them are default settings.",
        "SIX OF THEM, ON ONE SHIRT", [
        ("FABRIC", "Poly interlock, mid-weight, for print quality"),
        ("SEAMS", "Flatlock at shoulders and sides"),
        ("BODY GRAPHIC", "Sublimated before cutting"),
        ("CREST", "Embroidered, for the raised feel"),
        ("NUMBERS", "Heat transfer, matt film"),
        ("LABEL", "Heat transfer, so there's nothing to itch")],
        lambda: V.jersey_diagram([(.50, .80), (.27, .62), (.50, .50), (.63, .28), (.38, .28), (.50, .13)])),
}


# ────────────────────────────────────────────────────────── real footage ─────
# What each versus and blueprint reel cuts to. (The poster reels name their
# clips line by line, above.) The rule for all of them: a line only goes over
# a clip that shows what the line is about, or over a neutral close-up — and
# nothing in SoccerTex's own voice goes over library footage at all, which
# engine/vibes.py enforces. A hook that speaks as "we" stays a drawn card.
#
# versus:    (clip under the hook or None, [clips that break into the argument])
# blueprint: (clip under the hook, {step: clip it plays over})
CUTS = {
    "lead-time":         (clip("sewing-floor", 0), [clip("cutting-knife", 8), clip("sewing-machine-vertical", 0)]),
    "wrong-supplier":    (None, [clip("sewing-factory", 3), clip("cutting-machine", 2), clip("thread-spools", 3)]),
    "reorder":           (clip("embroidery-line", 6), [clip("thread-spools", 0), clip("cutting-knife", 0)]),
    "shrinkage":         (clip("pressing", 8.5), [clip("fabric-check", 8), clip("cutting-fabric-scissors", 2)]),

    "price-drivers":     (clip("thread-spools", 4), {1: clip("thread-spools", 9), 3: clip("sewing-closeup", 0)}),
    "pem-cumulation":    (clip("mill-process", 5), {0: clip("mill-worker", 0), 1: clip("sewing-threading", 6)}),
    "trading-company":   (clip("sewing-closeup", 4), {}),
    "decoration":        (clip("sewing-machine-working", 5), {1: clip("embroidery-line", 0), 3: clip("screen-printing", 6)}),
    "fabric-glossary":   (clip("mill-process", 9), {5: clip("pressing", 9)}),
    "seams":             (clip("sewing-closeup", 0), {2: clip("sewing-machine-vertical", 5), 3: clip("sewing-threading", 0)}),
    "white-kit":         (clip("fabric-production-overhead", 0), {2: clip("cutting-knife", 3), 3: clip("fabric-production-overhead", 11)}),
    "factory-questions": (clip("cutting-knife", 6), {0: clip("fabric-production-overhead", 5), 4: clip("fabric-check", 6)}),
    "quality":           (clip("sewing-machine-vertical", 20), {0: clip("fabric-production-overhead", 14), 2: clip("cutting-machine", 1)}),
    "sewing-line":       (clip("sewing-factory", 0), {0: clip("sewing-floor", 6), 2: clip("sewing-closeup", 2)}),
    "heat-press":        (clip("pressing", 5.5), {3: clip("pressing", 8)}),
    "kit-decisions":     (clip("thread-spools", 7), {1: clip("sewing-closeup", 4), 3: clip("sewing-machine-working", 2)}),
}


# ──────────────────────────────────────────────────────────────── build ─────
def build(tid: str, variant: str = "social") -> tuple[Video, dict]:
    family, skin, kind, pace = LOOK[tid]
    hold = PACE[pace]["hold"]
    bpm, mood = PACE[pace][family]
    v = Video(OUT / f"{tid}--{variant}.mp4")
    if family == "poster":
        align, motion = kind.split("/")
        kit = Poster(skin, align, motion, hold)
        scenes, colours = poster(tid, kit), kit.close
    elif family == "versus":
        c = V.VERSUS_SKINS[skin]
        colours = (c["bg"], c["txt"], c["grn"])
        opener, rolls = CUTS[tid]
        vs = VersusScene(*VS[tid], skin=skin, mode=kind, pace=hold, hookclip=opener)
        # footage breaks in just before the second and the last pair of rows
        whens = sorted(set(vs.ta[1:]))[:len(rolls)]
        scenes = [Breaks(vs, [(w, Plate(r, chip=vs.title, colours=colours, seconds=1.25 * hold))
                              for w, r in zip(whens, rolls)])]
    else:
        hook, sub, title, steps, diagram = BP[tid]
        c = V.BLUE_SKINS[skin]
        opener, over = CUTS[tid]
        scenes = [BlueprintScene(hook, sub, title, steps, diagram(), skin=skin, pace=hold,
                                 hookclip=opener, footage=over)]
        colours = (c["bg"], c["line"], c["accent"])
    for s in scenes:
        v.add(s)
    line, sub = CLOSE[variant]
    v.add(CloseCard(line, sub, *colours))
    return v, dict(bpm=bpm, mood=mood)


def write_cuts(tid, variants):
    """Render a topic's cuts together. They differ only in the closing card, so
    the body is drawn once and sent to every encoder — footage frames are the
    slow part, and drawing them twice doubled the render for nothing."""
    from engine.render import W, H
    from engine.audio import soundtrack
    built = [build(tid, variant) for variant in variants]
    encoders = []
    for v, sound in built:
        audio = soundtrack(v.seconds, v.cut_times, path=v.out.parent.parent / "audio" / f"{v.out.stem}.wav",
                           seed=zlib.crc32(v.out.stem.encode()) % 1000, marks=v.mark_times, **sound)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(v.fps), "-i", "-"]
        if audio and Path(audio).exists():
            cmd += ["-i", str(audio), "-c:a", "aac", "-b:a", "128k", "-shortest"]
        # crf 24, not 20: moving footage costs six times the bits of flat colour,
        # and sixty files at 20 came to 287 MB in a repository that keeps every
        # version. Instagram re-encodes to less than either.
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", "-profile:v", "high", "-level", "4.0", str(v.out)]
        encoders.append(subprocess.Popen(cmd, stdin=subprocess.PIPE))

    def send(scene, targets):
        try:
            for i in range(scene.n):
                buf = scene.frame(i, scene.n).tobytes()
                if len(buf) != W * H * 3:
                    raise RuntimeError(f"{type(scene).__name__} produced {len(buf)} bytes")
                for e in targets:
                    e.stdin.write(buf)
        finally:
            scene.close()

    err = None
    try:
        for scene in built[0][0].scenes[:-1]:
            send(scene, encoders)
        for (v, _), e in zip(built, encoders):
            send(v.scenes[-1], [e])
    except Exception as e:
        err = e
    finally:
        codes = []
        for e in encoders:
            try:
                e.stdin.close()
            except BrokenPipeError:
                pass
            codes.append(e.wait())
        for v, _ in built[1:]:
            for scene in v.scenes:
                scene.close()
    if err is not None:
        raise err
    if any(codes):
        raise RuntimeError(f"ffmpeg exited {codes} for {tid}")
    return [v for v, _ in built]


def main():
    args = sys.argv[1:]
    check_spread()
    first = check_footage()
    if "--list" in args:
        for t in BANK:
            print(f"  {t['id']:20s} " + "  ".join(f"{x:10s}" for x in LOOK[t["id"]])
                  + f"  opens on {first[t['id']] or 'a drawn card'}")
        return
    variants = [a.lstrip("-") for a in args if a.startswith("--")] or ["social", "business"]
    which = [a for a in args if not a.startswith("--")] or [t["id"] for t in BANK]
    bad = [t for t in which if t not in LOOK]
    if bad:
        sys.exit(f"unknown topic: {', '.join(bad)}")
    OUT.mkdir(parents=True, exist_ok=True)
    for tid in which:
        for v in write_cuts(tid, variants):
            # trust the file on disk, not the composer's intent
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(v.out)], capture_output=True, text=True)
            got = float(r.stdout.strip() or 0)
            if got < v.seconds * 0.9 or got < 8.0:
                v.out.unlink(missing_ok=True)
                raise RuntimeError(f"{v.out.stem}: only {got:.1f}s on disk, "
                                   f"composer wrote {v.seconds:.1f}s — deleted")
            print(f"  {v.out.stem}: {got:.1f}s on disk, {' / '.join(LOOK[tid])}  OK", flush=True)


if __name__ == "__main__":
    main()
