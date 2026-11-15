#!/usr/bin/env python3
"""Render the library so that no two neighbouring reels look alike.

    python3 build_vibes.py                      every topic, both cuts
    python3 build_vibes.py --social gsm seams   named topics, Instagram cut
    python3 build_vibes.py --list               which topic uses which format

Each topic is assigned one of seven formats (engine/vibes.py). The assignment
is not random: Instagram posts topic i and topic i+15 on the same day, and
topic i+1 the next day, so a format never sits next to itself in the bank and
never shares a day with itself. `check_spread()` enforces that, so adding a
topic cannot quietly put two chats or two posters back to back.

Every line on screen comes from engine/bank.py — reworded and cut down, never
added to. Where a format needed a line the bank does not have (a buyer's
opening message in a chat), it is a question, not a claim, and the thread is
headed "Illustration".
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

from engine.render import Video
from engine.bank import BANK
from engine import vibes as V
from engine.vibes import (ChatScene, Slam, Say, Count, NotebookScene, VersusScene,
                          BlueprintScene, DocShot, CloseCard, INK, BONE, AMBER)
import build_silent
from build_silent import CLOSE, SEW_V, SEW_W, CUTF, ROLL

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out" / "video"

# format → (bed tempo, bed mood, close-card colours: bg, text, accent)
LOOK = {
    "chat":      (96,  "calm",  ((11, 15, 12), (238, 244, 240), (36, 178, 94))),
    "poster":    (134, "punch", (AMBER, INK, INK)),
    "notebook":  (100, "calm",  ((245, 240, 228), (26, 30, 28), (20, 132, 68))),
    "versus":    (118, "drive", ((15, 17, 19), (242, 242, 238), (36, 178, 94))),
    "blueprint": (108, "calm",  (V.NAVY, V.LINE, V.CYAN)),
    "doc":       (90,  "punch", ((10, 12, 11), BONE, AMBER)),
}

FORMAT = {
    "lead-time": "poster", "season-calendar": "notebook", "price-drivers": "chat",
    "europe-duty": "poster", "pem-cumulation": "blueprint", "tech-pack": "notebook",
    "wrong-supplier": "versus", "small-orders": "chat", "trading-company": "poster",
    "buyer-questions": "chat", "decoration": "blueprint", "gsm": "cuts",
    "fabric-glossary": "notebook", "cheap-vs-good": "cuts", "seams": "blueprint",
    "sublimation-limits": "chat", "white-kit": "cuts", "recovery-test": "poster",
    "factory-questions": "notebook", "shrinkage": "versus", "quality": "blueprint",
    "cutting": "doc", "sewing-line": "poster", "embroidery": "doc", "heat-press": "cuts",
    "nameset": "notebook", "kit-decisions": "blueprint", "goalkeeper": "chat",
    "reorder": "versus", "packing": "notebook",
}


def check_spread():
    ids = [t["id"] for t in BANK]
    missing = [i for i in ids if i not in FORMAT]
    if missing:
        sys.exit(f"no format chosen for: {', '.join(missing)}")
    n = len(ids)
    for i, tid in enumerate(ids):
        nxt, pair = ids[(i + 1) % n], ids[(i + n // 2) % n]
        if FORMAT[tid] == FORMAT[nxt]:
            sys.exit(f"{tid} and {nxt} post on consecutive days and are both {FORMAT[tid]}")
        if FORMAT[tid] == FORMAT[pair]:
            sys.exit(f"{tid} and {pair} post on the same day and are both {FORMAT[tid]}")


# ───────────────────────────────────────────────────────────────── chat ─────
def chat(tid):
    if tid == "small-orders":
        return [ChatScene("A big factory", [
                    ("me", "Hi — can you quote 300 custom jerseys?"),
                    ("seen", "Seen"), ("sys", "3 days later"),
                    ("me", "Hello?"), ("seen", "Seen")], tail=0.9),
                ChatScene("SoccerTex", [
                    ("them", "They stopped replying about your 300 pieces."),
                    ("them", "It wasn't your brand. It was the maths."),
                    ("them", "Big factories need big runs — setup costs them more than you pay."),
                    ("them", "A colourway is a fabric lot, a lab dip and a cut, whatever the quantity."),
                    ("them", "Short custom runs are a different cost structure, not a favour."),
                    ("them", "Send your real quantity and we'll tell you straight.")])]
    if tid == "price-drivers":
        return [ChatScene("SoccerTex", [
            ("me", "Why is my unit price what it is?"),
            ("them", "Six things move it. Quantity is only one, and rarely the biggest."),
            ("them", "1. FABRIC — composition and GSM. The largest input cost."),
            ("them", "2. COLOURWAYS — each one is its own lot, lab dip and cut."),
            ("them", "3. DECORATION — a sublimated body is nearly free; four embroidered placements are not."),
            ("them", "4. PANEL COUNT — a 12-panel jersey has more operations than a 6-panel."),
            ("them", "5. SIZE RANGE — youth XS to adult 4XL needs a wider grade."),
            ("them", "6. QUANTITY — real, but it flattens fast above 1,000.")])]
    if tid == "buyer-questions":
        return [ChatScene("A new supplier", [
            ("sys", "What I'd ask if I were buying"),
            ("me", "Which operations happen in this building, and which leave it?"),
            ("me", "Show me the floor on a live video call this week."),
            ("me", "What's your MOQ per colourway, not per style?"),
            ("me", "What certifications do you hold, and when were you last audited?"),
            ("me", "What was the last order you got wrong, and what happened next?"),
            ("typing", "2.6"),
            ("sys", "Two of them are uncomfortable. Ask anyway.")], tail=1.6)]
    if tid == "sublimation-limits":
        return [ChatScene("SoccerTex", [
            ("me", "Can you sublimate this design onto 100% cotton?"),
            ("them", "No. Sublimation needs polyester. On cotton there's nothing for the ink to bond to."),
            ("them", "SCREEN PRINT — the standard answer for cotton."),
            ("them", "EMBROIDERY — works on anything, best for small marks."),
            ("them", "HEAT TRANSFER — works on cotton, application is everything."),
            ("them", "Or change the fabric: a poly-cotton blend takes it, softer and more muted."),
            ("me", "Another supplier said they can."),
            ("them", "Anyone saying otherwise is about to disappoint you.")])]
    if tid == "goalkeeper":
        return [ChatScene("SoccerTex", [
            ("me", "Can the keeper just wear a long-sleeved outfield shirt?"),
            ("them", "It isn't the same shirt. Four things change."),
            ("them", "Elbow padding changes the sleeve construction."),
            ("them", "Heavier fabric, because it meets the ground."),
            ("them", "Looser cut through the body, for reach."),
            ("them", "Different colour rules — it has to contrast with both teams."),
            ("them", "Built for a different job.")])]
    raise KeyError(tid)


# ─────────────────────────────────────────────────────────────── poster ─────
A, B_, C = dict(bg=INK, fg=BONE, accent=AMBER), dict(bg=BONE, fg=INK, accent=(196, 70, 44)), dict(bg=AMBER, fg=INK, accent=INK)


def poster(tid):
    if tid == "lead-time":
        return [Slam(["14 WEEKS", "VS", "2 WEEKS"], "Same deadline. Two different seasons.", hi=2, **A),
                Say("At 14 weeks you approve in January, and commit before this season ends.", **B_),
                Slam(["NO WAY", "TO REACT", "IN MAY"], **C),
                Say("At 2 weeks you approve in April, and decide with better information.", **A),
                Slam(["ABSORB A", "200-PIECE", "ADD-ON"], hi=1, **A),
                Count(2, " WEEKS", "Production lead time", "Published, so you can plan around it.")]
    if tid == "europe-duty":
        return [Slam(["EGYPT", "SHIPS TO", "EUROPE", "DUTY-FREE"], "Since 2004. Most brands don't know it.", hi=3, **A),
                Count(46, "%", "Growth in Egyptian garment exports to Europe",
                      "First seven months of 2026. Spain alone was up 86%."),
                Slam(["SINCE", "JUNE 2004"], "EU–Egypt Association Agreement, in force.", **B_),
                Slam(["NO DUTY"], "Egyptian industrial goods enter the EU without duty.", **A),
                Say("PEM origin rules let EU or Turkish fabric still count as Egyptian.", **B_),
                Slam(["3 TO 7", "DAYS"], "By sea to Southern European ports.", hi=0, **A)]
    if tid == "trading-company":
        return [Slam(["THREE SIGNS", "IT'S NOT", "REALLY", "A FACTORY"], "None of them are about price.", hi=3, **A),
                Say("They can't show you this week's floor on a live video call.", n=1, **B_),
                Say("Every photo is the same corner of the same room.", n=2, **A),
                Say("They quote jerseys, shoes and backpacks from one building.", n=3, **B_),
                Slam(["ASK FOR", "THE FLOOR", "ON VIDEO"], "What a real floor can do in 90 seconds.", **C)]
    if tid == "recovery-test":
        return [Slam(["STRETCH", "ISN'T", "THE TEST."], **A),
                Slam(["RECOVERY", "IS."], "Two seconds, and it tells you more than the label.", hi=0, **A),
                Say("Stretch is how far the fabric goes. Recovery is whether it comes back.", **B_),
                Slam(["PULL", "THE CUFF."], "Then let go and watch.", **C),
                Say("Instant return means good recovery.", **A),
                Say("Stays slightly open? That's the shirt that looks tired by March.", **B_)]
    if tid == "sewing-line":
        return [Slam(["A JERSEY", "ISN'T SEWN", "BY ONE", "PERSON"], "And that's exactly why it comes out consistent.", hi=2, **A),
                Slam(["ONE", "OPERATION", "PER STATION"], "The garment moves down the line.", **B_),
                Say("Repetition is what makes it consistent, not what makes it careless.", **A),
                Say("The operations that fail have stretch or shape.", **B_),
                Slam(["COLLARS.", "PLACKETS.", "SLEEVES."], "Those get checked specifically.", **C)]
    raise KeyError(tid)


# ───────────────────────────────────────────────────────────── notebook ─────
NOTE = {
    "season-calendar": ("THE REAL CALENDAR", ["WORK BACKWARDS", "FROM JULY"],
        "Most brands get this date wrong by two months.", [
        ("1 July: kit with clubs", "[1 JULY] — kit with clubs"),
        ("less 1–2 weeks: distribution, namesets", "[MINUS 1–2 WEEKS] — your own distribution and namesets"),
        ("less 1 week: sea transit", "[MINUS 1 WEEK] — sea transit to Southern Europe"),
        ("less 2 weeks: bulk production", "[MINUS 2 WEEKS] — bulk production"),
        ("less 1–2 weeks: sample approval", "[MINUS 1–2 WEEKS] — sample approval"),
        ("less 1–2 weeks: tech pack, lab dips", "[MINUS 1–2 WEEKS] — tech pack and lab dips")],
        "Approve your sample by the first half of April."),
    "tech-pack": ("THE MINIMUM BRIEF", ["EIGHT THINGS", "AND WE CAN", "QUOTE YOU"],
        "Five of them you already know.", [
        ("Sketch or photo", "[A SKETCH OR A PHOTO] of a garment you like — front and back"),
        ("Fabric intent", "[FABRIC INTENT] — composition and GSM, or just \"like this shirt\""),
        ("Colourways", "[COLOURWAYS] — with Pantone references if you have them"),
        ("Size range", "[SIZE RANGE] and rough split"),
        ("Quantity per colourway", "[QUANTITY] per colourway, not just the total"),
        ("Decoration", "[DECORATION] — what goes where, at what size"),
        ("Trims and labels", "[TRIMS AND LABELS]"),
        ("The real deadline", "[THE REAL DEADLINE] — not the one you'd like")],
        "Enough to quote a price we'll stand behind."),
    "fabric-glossary": ("FABRIC GLOSSARY", ["THE WORDS", "ON EVERY", "TEAMWEAR", "QUOTE"],
        "Recovery is the one brands skip.", [
        ("Interlock", "[INTERLOCK] — double-knit, smooth both sides, stable"),
        ("Single jersey", "[SINGLE JERSEY] — lighter, curls at a raw edge"),
        ("Piqué", "[PIQUÉ] — textured waffle. The polo fabric"),
        ("Mesh", "[MESH] — open structure, for airflow panels"),
        ("Jacquard", "[JACQUARD] — pattern knitted in, not printed"),
        ("Recovery", "[RECOVERY] — whether it returns to shape. Separate from stretch, and more important")],
        "Save this before your next spec call."),
    "factory-questions": ("ASK THESE", ["SEVEN QUESTIONS", "BEFORE YOU SEND", "A DEPOSIT"],
        "Number 7 sorts it out on its own.", [
        ("GSM and composition", "What's the [GSM and composition] you're quoting?"),
        ("In-house or subcontracted", "Which decoration is [in-house,] which is subcontracted?"),
        ("Lead time from sample", "Lead time from [approved sample,] not from deposit?"),
        ("MOQ per colourway", "MOQ [per colourway,] not per style?"),
        ("Inspection points", "How many [inspection points,] and what does each check?"),
        ("Shade variance", "Who signs off a [shade variance?]"),
        ("This week's floor, live", "Can I see this week's floor on a [live video call?]")],
        "If they can't answer in one email, that's your answer."),
    "nameset": ("THE NAMESET", ["NAMES AND NUMBERS", "ARE WHERE KIT", "GOES WRONG"],
        "Four variables, and one wrong shows up in March.", [
        ("Film type", "[FILM TYPE] decides hand-feel and how far it reads"),
        ("Temperature and dwell time", "[TEMPERATURE AND DWELL TIME] decide whether it stays on"),
        ("Pressure", "[PRESSURE] decides the edge quality"),
        ("Five finishes", "We run [3D, reflective, fluor, matt and silicone]")],
        "Film, temperature, dwell time, pressure."),
    "packing": ("FINISHING", ["THIS IS WHAT", "A DAY", "LOOKS LIKE"],
        "Folded, bagged, cartoned, labelled.", [
        ("Trim to carton", "[Trim, measure against spec, press, fold, bag, carton]"),
        ("The last inspection point", "The last of the [five inspection points]"),
        ("Adhesion and measurements", "Checks [decoration adhesion] and final measurements"),
        ("The fold", "A well-made garment [badly folded] arrives looking cheap"),
        ("2,000 pieces a day", "[2,000 pieces a day] — then 3 to 7 days by sea to Southern Europe")],
        "The stage that decides what the buyer sees first."),
}


# ─────────────────────────────────────────────────────────────── versus ─────
VS = {
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
def blueprint(tid):
    if tid == "pem-cumulation":
        return BlueprintScene("THE ORIGIN RULE NOBODY USES", "European fabric, Egyptian make, duty-free entry.",
            "DIAGONAL CUMULATION", [
            ("THE FABRIC", "Specify a European or Turkish mill if your brand needs it"),
            ("THE MAKE", "Manufacture in Egypt at Egyptian conversion cost"),
            ("THE ORIGIN", "The garment can still qualify as Egyptian origin"),
            ("THE ENTRY", "Enters the EU duty-free under the 2004 agreement"),
            ("THE CATCH", "The paperwork changed in 2025 — check it with your broker")],
            V.flow_diagram(["EU OR TURKISH MILL", "MADE IN EGYPT", "EGYPTIAN ORIGIN",
                            "INTO THE EU, DUTY-FREE", "CHECK THE PAPERWORK"]))
    if tid == "quality":
        return BlueprintScene("MOST QUALITY PROBLEMS AREN'T SEWING PROBLEMS",
            "They're fabric problems nobody checked at intake.", "FIVE INSPECTION POINTS", [
            ("FABRIC ARRIVAL", "Shade, weight, flaws. The first one saves the most money"),
            ("PATTERN", "Grading across the size run"),
            ("BULK CUT", "Piece count against the marker, before anything moves"),
            ("SPECIAL SEWING", "Collars, plackets, sleeves"),
            ("FINISHING", "Adhesion, measurement, pack")],
            V.flow_diagram(["FABRIC ARRIVAL", "PATTERN", "BULK CUT", "SPECIAL SEWING", "FINISHING"]))
    if tid == "decoration":
        return BlueprintScene("FOUR WAYS TO PUT A BADGE ON A SHIRT", "They are not interchangeable.",
            "WHERE THE MARK ACTUALLY SITS", [
            ("SUBLIMATION", "Ink bonds inside the fibre"),
            ("EMBROIDERY", "Thread stitched in. Raised, durable, adds weight"),
            ("HEAT TRANSFER", "Film applied under heat"),
            ("SCREEN PRINT", "Ink on the surface")], V.layers_diagram())
    if tid == "seams":
        return BlueprintScene("THIS SEAM IS WHY THE SHIRT DOESN'T RUB", "And most tech packs never specify it.",
            "FLATLOCK VS OVERLOCK", [
            ("FLATLOCK", "Edges butted and stitched flat. No inside ridge"),
            ("OVERLOCK", "Faster, cheaper, leaves a raised seam"),
            ("WHERE IT MATTERS", "Fine on a leisure tee. Wrong on a match jersey"),
            ("SPECIFY IT", "Put it in the tech pack or you get whichever is cheaper")], V.seam_diagram())
    if tid == "kit-decisions":
        return BlueprintScene("ONE KIT. ELEVEN DECISIONS.", "None of them are default settings.",
            "SIX OF THEM, ON ONE SHIRT", [
            ("FABRIC", "Poly interlock, mid-weight, for print quality"),
            ("SEAMS", "Flatlock at shoulders and sides"),
            ("BODY GRAPHIC", "Sublimated before cutting"),
            ("CREST", "Embroidered, for the raised feel"),
            ("NUMBERS", "Heat transfer, matt film"),
            ("LABEL", "Heat transfer, so there's nothing to itch")],
            V.jersey_diagram([(.50, .80), (.27, .62), (.50, .50), (.63, .28), (.38, .28), (.50, .13)]))
    raise KeyError(tid)


# ────────────────────────────────────────────────────────────────── doc ─────
DOC = {
    "cutting": (["SIXTY LAYERS,", "ONE PASS"], "Everything after this depends on getting it right.", [
        (ROLL, 1.15, (.5, .45), "SPREAD", "Fabric spread in layers, pattern laid out as a marker"),
        (CUTF, 1.0, (.5, .5), "THE MARKER", "Get it wrong and you waste fabric on every garment"),
        (ROLL, 1.3, (.4, .6), "INSPECTED", "The cut is checked before anything moves to the line"),
        (CUTF, 1.05, (.6, .45), "COUNTED", "Piece count checked against the marker")]),
    "embroidery": (["FIFTEEN", "THOUSAND", "STITCHES"], "One crest. You can feel it. That's the point.", [
        (SEW_W, 1.1, (.5, .5), "NEEDLES", "Multiple needles, one colour each, swapping as the design builds"),
        (SEW_V, 1.8, (.5, .6), "ON TOP", "Thread sits on the surface — the premium feel, and the added weight"),
        (SEW_W, 1.2, (.45, .55), "CRESTS", "Best for crests and sponsor marks"),
        (SEW_V, 1.6, (.55, .45), "NOT GRAPHICS", "Not for full-garment graphics. That's sublimation")]),
}


def doc(tid):
    hook, sub, shots = DOC[tid]
    first = shots[0]
    out = [DocShot(first[0], 2.2, hook, sub, tight=first[1], focus=first[2], start=2.0)]
    for k, (clip, tight, focus, big, small) in enumerate(shots):
        out.append(DocShot(clip, V.read_secs(small) + 0.7, big, small, chip=f"{k + 1:02d} / {len(shots):02d}",
                           tight=tight, focus=focus, start=5.0 + k * 3.3, mirror=k % 2 == 1))
    return out


# ──────────────────────────────────────────────────────────────── build ─────
def build(tid: str, variant: str = "social") -> tuple[Video, dict]:
    fmt = FORMAT[tid]
    if fmt == "cuts":
        return build_silent.build(tid, variant), dict(bpm=126)
    bpm, mood, (bg, fg, accent) = LOOK[fmt]
    v = Video(OUT / f"{tid}--{variant}.mp4")
    if fmt == "chat":
        scenes = chat(tid)
    elif fmt == "poster":
        scenes = poster(tid)
    elif fmt == "notebook":
        scenes = [NotebookScene(*NOTE[tid])]
    elif fmt == "versus":
        scenes = [VersusScene(*VS[tid])]
    elif fmt == "blueprint":
        scenes = [blueprint(tid)]
    else:
        scenes = doc(tid)
    for s in scenes:
        v.add(s)
    line, sub = CLOSE[variant]
    v.add(CloseCard(line, sub, bg, fg, accent))
    return v, dict(bpm=bpm, mood=mood)


def main():
    args = sys.argv[1:]
    check_spread()
    if "--list" in args:
        for t in BANK:
            print(f"  {t['id']:20s} {FORMAT[t['id']]}")
        return
    variants = [a.lstrip("-") for a in args if a.startswith("--")] or ["social", "business"]
    which = [a for a in args if not a.startswith("--")] or [t["id"] for t in BANK]
    bad = [t for t in which if t not in FORMAT]
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
            print(f"  {tid}--{variant}: {got:.1f}s on disk, {FORMAT[tid]}  OK")


if __name__ == "__main__":
    main()
