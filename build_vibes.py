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

Every line on screen comes from engine/bank.py — reworded and cut down, never
added to.
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

from engine.render import Video
from engine.bank import BANK
from engine import vibes as V
from engine.vibes import Poster, VersusScene, BlueprintScene, CloseCard
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


# ─────────────────────────────────────────────────────────────── poster ─────
def poster(tid, P):
    s, y, c = P.slam, P.say, P.count
    if tid == "europe-duty":
        return [s(["EGYPT", "SHIPS TO", "EUROPE", "DUTY-FREE"], "Since 2004. Most brands don't know it.", hi=3, scheme=0),
                c(46, "%", "Growth in Egyptian garment exports to Europe", "First seven months of 2026. Spain alone was up 86%."),
                s(["SINCE", "JUNE 2004"], "EU–Egypt Association Agreement, in force.", scheme=1),
                s(["NO DUTY"], "Egyptian industrial goods enter the EU without duty.", scheme=0),
                y("PEM origin rules let EU or Turkish fabric still count as Egyptian.", scheme=1),
                s(["3 TO 7", "DAYS"], "By sea to Southern European ports.", hi=0, scheme=0)]
    if tid == "season-calendar":
        return [s(["WORK", "BACKWARDS", "FROM JULY"], "Most brands get this date wrong by two months.", hi=2),
                s(["1 JULY"], "Kit with clubs."),
                s(["MINUS", "1–2 WEEKS"], "Your own distribution and namesets."),
                s(["MINUS", "1 WEEK"], "Sea transit to Southern Europe."),
                s(["MINUS", "2 WEEKS"], "Bulk production."),
                s(["MINUS", "1–2 WEEKS"], "Sample approval."),
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
        return ([s(["EIGHT THINGS", "AND WE CAN", "QUOTE YOU"], "Five of them you already know.", hi=0)]
                + [y(t, n=k + 1) for k, t in enumerate(items)]
                + [y("Enough to quote a price we'll stand behind.")])
    if tid == "small-orders":
        return [s(["THEY STOPPED", "REPLYING"], "About your 300 pieces.", hi=1),
                s(["IT WASN'T", "YOUR BRAND."]), s(["IT WAS", "THE MATHS."], hi=1),
                y("Big factories need big runs — setup costs them more than you pay."),
                y("A colourway is a fabric lot, a lab dip and a cut, whatever the quantity."),
                y("Short custom runs are a different cost structure, not a favour."),
                s(["SEND YOUR", "REAL", "QUANTITY"], "We'll tell you straight.")]
    if tid == "buyer-questions":
        qs = ["Which operations happen in this building, and which leave it?",
              "Show me the floor on a live video call this week.",
              "What's your MOQ per colourway, not per style?",
              "What certifications do you hold, and when were you last audited?",
              "What was the last order you got wrong, and what happened next?"]
        return ([s(["WHAT I'D ASK", "IF I WERE", "BUYING"], "Including the two I'd least like to be asked.", hi=2)]
                + [y(q, n=k + 1) for k, q in enumerate(qs)]
                + [s(["TWO OF THEM", "ARE", "UNCOMFORTABLE."], "Ask anyway.")])
    if tid == "gsm":
        return [s(["THE ONE", "FABRIC NUMBER", "NOBODY", "EXPLAINS"], "And it's on every quote you'll ever read.", hi=1),
                y("GSM is grams per square metre. It's just fabric weight."),
                s(["130–150"], "GSM — match jersey."), s(["150–180"], "GSM — training top."),
                s(["180–220"], "GSM — polo, warm-up."), s(["240–320"], "GSM — hoodie, sweat."),
                c(150, " GSM", "Where a match jersey tops out", "Above this you're buying a training top."),
                y("Lighter isn't cheaper by accident. It's less of it.")]
    if tid == "cheap-vs-good":
        return [s(["A £15 JERSEY", "AND A", "£45 JERSEY"], "Same photo. Different garment.", hi=2),
                s(["WHAT YOU", "CAN'T SEE"], "Three things that never show in a product shot."),
                y("£15: lighter fabric, less yarn. £45: the correct GSM for the job.", n=1),
                y("£15: overlocked seams that rub. £45: flatlocked seams, no ridge.", n=2),
                y("£15: a printed vinyl badge that peels. £45: a sublimated or stitched badge.", n=3)]
    if tid == "sublimation-limits":
        return [s(["SUBLIMATION", "CANNOT", "PRINT ON", "COTTON"], "Anyone saying otherwise is about to disappoint you.", hi=3),
                y("Sublimation needs polyester. On cotton there's nothing for the ink to bond to."),
                s(["SCREEN", "PRINT"], "The standard answer for cotton."),
                s(["EMBROIDERY"], "Works on anything, best for small marks."),
                s(["HEAT", "TRANSFER"], "Works on cotton, application is everything."),
                y("Or change the fabric: a poly-cotton blend takes it, softer and more muted.")]
    if tid == "recovery-test":
        return [s(["STRETCH", "ISN'T", "THE TEST."]),
                s(["RECOVERY", "IS."], "Two seconds, and it tells you more than the label.", hi=0, scheme=0),
                y("Stretch is how far the fabric goes. Recovery is whether it comes back."),
                s(["PULL", "THE CUFF."], "Then let go and watch."),
                y("Instant return means good recovery."),
                y("Stays slightly open? That's the shirt that looks tired by March.")]
    if tid == "cutting":
        return [s(["SIXTY", "LAYERS,", "ONE PASS"], "Everything after this depends on getting it right.", hi=2),
                y("Fabric spread in layers, pattern laid out as a marker.", n=1),
                y("Get the marker wrong and you waste fabric on every garment.", n=2),
                y("The cut is inspected before anything moves to the line.", n=3),
                y("Piece count checked against the marker.", n=4),
                s(["STACKED.", "IDENTICAL."], "That is how the pieces come off.")]
    if tid == "embroidery":
        return [s(["FIFTEEN", "THOUSAND", "STITCHES,", "ONE CREST"], "You can feel it. That's the point.", hi=3),
                y("Multiple needles, one colour each, swapping as the design builds."),
                s(["ON TOP,", "NOT INSIDE"], "Thread sits on the surface — the premium feel, and the added weight."),
                s(["CRESTS.", "SPONSOR", "MARKS."], "What it is best for."),
                y("Not for full-garment graphics. That's sublimation.")]
    if tid == "nameset":
        return [s(["NAMES AND", "NUMBERS ARE", "WHERE KIT", "GOES WRONG"], "Four variables, and one wrong shows up in March.", hi=3),
                s(["FILM", "TYPE"], "Decides hand-feel and how far it reads."),
                s(["TEMPERATURE", "AND DWELL", "TIME"], "Decide whether it stays on."),
                s(["PRESSURE"], "Decides the edge quality."),
                y("We run 3D, reflective, fluor, matt and silicone.")]
    if tid == "goalkeeper":
        return [s(["A KEEPER SHIRT", "ISN'T AN", "OUTFIELD SHIRT", "WITH LONG SLEEVES"], "Four things change.", hi=0),
                y("Elbow padding changes the sleeve construction.", n=1),
                y("Heavier fabric, because it meets the ground.", n=2),
                y("Looser cut through the body, for reach.", n=3),
                y("Different colour rules — it has to contrast with both teams.", n=4),
                s(["BUILT FOR", "A DIFFERENT", "JOB."])]
    if tid == "packing":
        return [s(["THIS IS WHAT", "A DAY", "LOOKS LIKE"], "Folded, bagged, cartoned, labelled.", hi=1),
                c(2000, "", "Pieces a day", "Then 3 to 7 days by sea to Southern Europe."),
                s(["TRIM.", "MEASURE.", "PRESS."]), s(["FOLD.", "BAG.", "CARTON."]),
                y("The last of the five inspection points. It checks decoration adhesion and final measurements."),
                y("A well-made garment badly folded arrives looking cheap.")]
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
        scenes, colours = [VersusScene(*VS[tid], skin=skin, mode=kind, pace=hold)], (c["bg"], c["txt"], c["grn"])
    else:
        hook, sub, title, steps, diagram = BP[tid]
        c = V.BLUE_SKINS[skin]
        scenes = [BlueprintScene(hook, sub, title, steps, diagram(), skin=skin, pace=hold)]
        colours = (c["bg"], c["line"], c["accent"])
    for s in scenes:
        v.add(s)
    line, sub = CLOSE[variant]
    v.add(CloseCard(line, sub, *colours))
    return v, dict(bpm=bpm, mood=mood)


def main():
    args = sys.argv[1:]
    check_spread()
    if "--list" in args:
        for t in BANK:
            print(f"  {t['id']:20s} " + "  ".join(f"{x:10s}" for x in LOOK[t["id"]]))
        return
    variants = [a.lstrip("-") for a in args if a.startswith("--")] or ["social", "business"]
    which = [a for a in args if not a.startswith("--")] or [t["id"] for t in BANK]
    bad = [t for t in which if t not in LOOK]
    if bad:
        sys.exit(f"unknown topic: {', '.join(bad)}")
    OUT.mkdir(parents=True, exist_ok=True)
    for tid in which:
        for variant in variants:
            v, sound = build(tid, variant)
            v.write(music=True, quiet=False, **sound)
            # trust the file on disk, not the composer's intent
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(v.out)], capture_output=True, text=True)
            got = float(r.stdout.strip() or 0)
            if got < v.seconds * 0.9 or got < 8.0:
                v.out.unlink(missing_ok=True)
                raise RuntimeError(f"{tid}--{variant}: only {got:.1f}s on disk, "
                                   f"composer wrote {v.seconds:.1f}s — deleted")
            print(f"  {tid}--{variant}: {got:.1f}s on disk, {' / '.join(LOOK[tid])}  OK")


if __name__ == "__main__":
    main()
