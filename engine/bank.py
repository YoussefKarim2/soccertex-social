#!/usr/bin/env python3
"""The content bank.

Every topic SoccerTex posts about, as data rather than code. `compose.py` turns
each entry into a finished video; `queue_build.py` rolls them onto a schedule.
Adding a topic means adding a dict — no code changes, which is what lets the
GitHub workflow keep producing content without anyone touching the repo.

Each topic is published to all three platforms with a platform-specific cut and
caption, so 30 topics covers a 90-post month without repeating a video.

EVERY CLAIM HERE TRACES TO THE VERIFIED FACTS REGISTER. No certification claim,
no MOQ figure, no US duty claim, no named customer.
"""

# footage keys resolve in compose.py against assets/footage/proxy/
SEW, STITCH, CUT, MILL = "sew", "stitch", "cut", "mill"

T = dict  # readability

BANK = [
# ─────────────────────────────── SOURCING MATH ───────────────────────────────
T(id="lead-time", pillar="3 Sourcing Math", kind="compare", footage=SEW,
  hook="14 WEEKS VS 2 WEEKS", sub="Same deadline. Two different seasons.",
  overlay=("TWO WEEKS OF PRODUCTION", "Cut, sewn, decorated and packed."),
  stat=(2, " WEEKS", "Production lead time", "Published, so you can plan around it."),
  compare=("APPROVE YOUR DESIGN",
           ("14-WEEK CHAIN", ["Approve in January", "Commit before this season ends",
                              "No way to react in May"]),
           ("2-WEEK BUILD", ["Approve in April", "Decide with better information",
                             "Absorb a 200-piece add-on"]), "right"),
  caption="A kit programme that ships in 2 weeks of production instead of 10 changes your whole "
          "season calendar.\n\nAt 2 weeks you approve in April for a July delivery. At 14 weeks "
          "end to end, the same deadline means approving in January — committing to next season's "
          "kit before this season has finished.\n\nThe real cost of a long lead time isn't the "
          "waiting. It's deciding early, with worse information, and having no way to react when a "
          "club adds 200 pieces in May.\n\nWhat's your drop-dead approval date?",
  tags="#teamwear #footballkit #cutandsew #clothingmanufacturer #sourcing #customkits",
  li_tags="#sourcing #manufacturing"),

T(id="season-calendar", pillar="3 Sourcing Math", kind="list", footage=MILL,
  hook="WORK BACKWARDS FROM JULY", sub="Most brands get this date wrong by two months.",
  overlay=("THE REAL CALENDAR", "Counted backwards from kit in hand."),
  items=["1 JULY — kit with clubs", "minus 1–2 weeks — your own distribution and namesets",
         "minus 1 week — sea transit to Southern Europe", "minus 2 weeks — bulk production",
         "minus 1–2 weeks — sample approval", "minus 1–2 weeks — tech pack and lab dips"],
  caption="If your kit has to be in clubs' hands for July pre-season, when is the last safe date "
          "to approve your sample?\n\nMost brands answer March. Counted backwards honestly it's "
          "the first half of April — and that's on a 2-week production window. On a 10-week lead "
          "time the same deadline moves to January.\n\nThat's the actual argument for a shorter "
          "lead time. Not that kit arrives sooner. That you decide later, with better information.",
  tags="#sourcing #teamwear #footballkit #clothingbrandowner #customkits #cutandsew",
  li_tags="#sourcing #teamwear"),

T(id="price-drivers", pillar="3 Sourcing Math", kind="list", footage=MILL,
  hook="SIX THINGS MOVE YOUR UNIT PRICE", sub="Quantity is only one, and rarely the biggest.",
  overlay=("WHAT YOU'RE ACTUALLY PAYING FOR", "Ranked by how much it moves the number."),
  items=["FABRIC — composition and GSM. The largest input cost",
         "COLOURWAYS — each one is its own lot, lab dip and cut",
         "DECORATION — a sublimated body is nearly free; four embroidered placements are not",
         "PANEL COUNT — a 12-panel jersey has more operations than a 6-panel",
         "SIZE RANGE — youth XS to adult 4XL needs a wider grade",
         "QUANTITY — real, but it flattens fast above 1,000"],
  caption="Six things move the unit price of a custom jersey. Quantity is only one, and it's "
          "rarely the biggest lever you have.\n\nIf a quote comes back higher than you budgeted, "
          "the fastest fix is usually consolidating colourways or dropping a panel — not adding "
          "units you can't sell.\n\nI'd rather you knew that before asking us for a number.",
  tags="#sourcing #teamwear #clothingbrandowner #cutandsew #apparelmanufacturing #customkits",
  li_tags="#sourcing #pricing"),

T(id="europe-duty", pillar="3 Sourcing Math", kind="stat", footage=MILL,
  hook="EGYPT SHIPS TO EUROPE DUTY-FREE", sub="Since 2004. Most brands don't know it.",
  overlay=("DUTY-FREE INTO THE EU", "No EU duty on Egyptian industrial goods."),
  stat=(46, "%", "Growth in Egyptian garment exports to Europe",
        "First seven months of 2026. Spain alone was up 86%."),
  items=["EU–Egypt Association Agreement in force since June 2004",
         "Egyptian industrial goods enter the EU without duty",
         "PEM origin rules let EU or Turkish fabric still count as Egyptian",
         "3 to 7 days by sea to Southern European ports"],
  # The direction matters and the first draft blurred it. The agreement entered
  # into force on 1 June 2004 and its implementation ran to 2019 — but the
  # phase-out was on Egypt's side, for EU goods entering Egypt. For a European
  # buyer importing Egyptian garments, duty-free is the position from 2004.
  # Figures: Ready-Made Garments Export Council, via Egypt Today, 1 Sept 2026.
  caption="Egyptian garment exports to Europe grew 46% in the first seven months of 2026, to "
          "$930m. Spain alone was up 86%.\n\nThere's a structural reason most brands sourcing in "
          "Asia don't know about.\n\n1. The EU–Egypt Association Agreement has been in force since "
          "June 2004. Egyptian industrial goods — garments included — enter the EU without duty."
          "\n2. Egypt is in the pan-Euro-Mediterranean origin zone, so Turkish or European fabric "
          "can still count towards Egyptian origin.\n\nIf your fabric spec is European and you "
          "assumed that forced you into European manufacturing prices, it doesn't.\n\nFigures: "
          "Egypt's Ready-Made Garments Export Council, September 2026. Confirm your own HS code "
          "with your customs broker — origin rules changed in 2025 and I'd rather you checked.",
  tags="#sourcing #nearshoring #teamwear #apparelmanufacturing #madeinegypt",
  li_tags="#sourcing #nearshoring"),

T(id="pem-cumulation", pillar="3 Sourcing Math", kind="list", footage=MILL,
  hook="THE ORIGIN RULE NOBODY USES", sub="European fabric, Egyptian make, duty-free entry.",
  overlay=("DIAGONAL CUMULATION", "Revised PEM rules, EU–Egypt, since March 2025."),
  items=["Specify a European or Turkish mill if your brand needs it",
         "Manufacture in Egypt at Egyptian conversion cost",
         "The garment can still qualify as Egyptian origin",
         "Enters the EU duty-free under the 2004 agreement",
         "The paperwork changed in 2025 — check it with your broker"],
  # CORRECTED 11 Nov 2026. The first version told buyers to "get the EUR-MED
  # paperwork right". EUR-MED certificates and EUR-MED invoice declarations are
  # withdrawn under the revised PEM rules, which the European Commission says
  # have applied between the EU and Egypt since 11 March 2025, and which have
  # been the only rules in force since 1 January 2026. Telling a procurement
  # buyer to file a document that no longer exists is the kind of error this
  # whole account is positioned against.
  # Source: taxation-customs.ec.europa.eu, Pan-Euro-Mediterranean cumulation.
  caption="Egypt signed the PEM Convention — the pan-Euro-Mediterranean rules of origin — on 9 "
          "October 2013, and the revised version of those rules has applied between the EU and "
          "Egypt since March 2025.\n\nPEM allows diagonal cumulation. In plain terms: materials "
          "from another country in the zone can count towards local content. The zone covers the "
          "EU, EFTA, Türkiye, the Western Balkans and the Mediterranean partners.\n\nSo a garment "
          "cut and sewn in Egypt from Italian fabric can still qualify as Egyptian origin and "
          "enter the EU duty-free.\n\nTwo caveats, because origin rules punish the careless. "
          "Processing requirements vary by category. And the paperwork has changed — the EUR-MED "
          "certificate is gone, and since January 2026 only the revised rules apply. If you last "
          "looked at this before 2025, look again.\n\nConfirm your category with your customs "
          "broker before building a cost model on it.",
  tags="#sourcing #customs #nearshoring #apparelmanufacturing #teamwear",
  li_tags="#sourcing #customs"),

T(id="tech-pack", pillar="3 Sourcing Math", kind="list", footage=CUT,
  hook="EIGHT THINGS AND WE CAN QUOTE YOU", sub="Five of them you already know.",
  overlay=("THE MINIMUM BRIEF", "Enough to quote a price we'll stand behind."),
  items=["A sketch or a photo of a garment you like — front and back",
         "Fabric intent — composition and GSM, or just \"like this shirt\"",
         "Colourways, with Pantone references if you have them",
         "Size range and rough split",
         "Quantity per colourway, not just the total",
         "Decoration — what goes where, at what size",
         "Trims and labels", "The real deadline, not the one you'd like"],
  caption="About half the brands who contact us don't have a tech pack, and ask whether that's a "
          "problem.\n\nIt isn't. But it changes what we can tell you. Without one we give a "
          "budgetary range; with one we give a price we'll stand behind.\n\nThe genuine minimum is "
          "eight items, and five of them you already know.\n\nNumber 8 is the one people soften, "
          "and it decides everything. Tell us the real date.\n\nGot items 1 and 8 only? Send those. "
          "We'll tell you what's missing and quote a range in 24 hours.",
  tags="#sourcing #productdevelopment #clothingbrandowner #techpack #cutandsew #teamwear",
  li_tags="#sourcing #productdevelopment"),

T(id="wrong-supplier", pillar="3 Sourcing Math", kind="compare", footage=SEW,
  hook="WE'RE THE WRONG FACTORY FOR PLENTY OF BRIEFS", sub="Here's how to tell in ten seconds.",
  overlay=("CAPACITY, HONESTLY", "2,000 pieces a day across 4 lines."),
  stat=(2000, "", "Pieces a day", "Not an Asian mega-factory. Built for custom runs that move."),
  compare=("IS THIS YOU?",
           ("WRONG FIT", ["100,000 pieces in 30 days", "Commodity blanks at lowest cost",
                          "Certified supplier required today", "Footwear, bags, hard goods"]),
           ("RIGHT FIT", ["Custom teamwear or kit", "Several decoration methods on one garment",
                          "A deadline that needs 2 weeks", "Europe or the USA"]), "right"),
  caption="We're the wrong factory for plenty of briefs, and I'd rather say so in a post than in "
          "week three of a conversation.\n\nWRONG: 100,000 pieces in 30 days — our capacity is "
          "2,000 a day. Commodity blanks at the lowest possible price. A certified supplier today "
          "— we don't currently publish BSCI, WRAP, SEDEX or OEKO-TEX certification and I'm not "
          "going to imply otherwise. Footwear or hard goods.\n\nRIGHT: custom teamwear, several "
          "decoration methods on one garment, a deadline that needs 2 weeks not 10, Europe or the "
          "US, and you want to see the floor before you commit.\n\nListing the third item costs us "
          "enquiries. It also means nobody discovers a dealbreaker after sending artwork.",
  tags="#sourcing #manufacturing #teamwear #clothingbrandowner #cutandsew #honesty",
  li_tags="#sourcing #manufacturing"),

T(id="small-orders", pillar="3 Sourcing Math", kind="list", footage=SEW,
  hook="THEY STOPPED REPLYING ABOUT YOUR 300 PIECES", sub="It wasn't your brand. It was the maths.",
  overlay=("SHORT RUNS", "What four lines are set up for."),
  items=["Big factories need big runs — setup costs them more than you pay",
         "A colourway is a fabric lot, a lab dip and a cut, whatever the quantity",
         "Short custom runs are a different cost structure, not a favour",
         "Send your real quantity and we'll tell you straight"],
  caption="Most big factories won't take 300 pieces. The setup time costs them more than the "
          "order earns, so they go quiet rather than say no.\n\nThat's a capacity mismatch, not a "
          "reflection on your brand.\n\nFour lines, 2,000 pieces a day, four decoration methods in "
          "one building — that's a structure built for short custom runs.\n\nIf you've been "
          "ghosted over a small order, send us the quantity.",
  tags="#clothingbrandowner #cutandsew #clothingmanufacturer #teamwear #smallbusiness #startup",
  li_tags="#sourcing #manufacturing"),

T(id="trading-company", pillar="3 Sourcing Math", kind="list", footage=STITCH,
  hook="THREE SIGNS IT'S NOT REALLY A FACTORY", sub="None of them are about price.",
  overlay=("HOW TO TELL", "What a real floor can do in 90 seconds."),
  items=["They can't show you this week's floor on a live video call",
         "Every photo is the same corner of the same room",
         "They quote jerseys, shoes and backpacks from one building"],
  caption="Three signs you're talking to a middleman rather than a manufacturer:\n\n1. They can't "
          "show you this week's floor on a live video call. Anyone with a factory can — it takes "
          "90 seconds.\n2. Every photo shows the same corner of the same room. Real floors look "
          "different on different days.\n3. They quote every product category. Nobody makes "
          "jerseys, shoes and backpacks in one building.\n\nNone of this makes a trading company a "
          "bad partner. But you should know which you're buying from, because it changes who "
          "controls your lead time.\n\nAsk for a live walkthrough. We'll do one this week.",
  tags="#sourcing #cutandsew #clothingbrandowner #clothingmanufacturer #manufacturing #teamwear",
  li_tags="#sourcing #manufacturing"),

T(id="buyer-questions", pillar="3 Sourcing Math", kind="list", footage=CUT,
  hook="WHAT I'D ASK IF I WERE BUYING", sub="Including the two I'd least like to be asked.",
  overlay=("FIVE QUESTIONS", "Two of them are uncomfortable."),
  items=["Which operations happen in this building, and which leave it?",
         "Show me the floor on a live video call this week",
         "What's your MOQ per colourway, not per style?",
         "What certifications do you hold, and when were you last audited?",
         "What was the last order you got wrong, and what happened next?"],
  caption="If I were buying teamwear instead of making it, here's what I'd ask.\n\n1. Which "
          "operations happen in this building, and which leave it? The answer tells you who "
          "controls your lead time.\n2. Show me the floor, live, this week.\n3. MOQ per colourway "
          "— not per style. That's where quotes go wrong.\n4. What certifications, and when were "
          "you last audited? One of the two I'd rather not be asked — we don't publish any, and if "
          "your procurement requires an audited supplier you need that answer early.\n5. What was "
          "the last order you got wrong? Every factory has one. How they answer tells you how "
          "they'll behave when it's yours.\n\nBuyers under-ask 1 and 5 and over-weight price.",
  tags="#sourcing #manufacturing #cutandsew #teamwear #procurement #clothingbrandowner",
  li_tags="#sourcing #procurement"),

# ──────────────────────────────── KIT SCHOOL ─────────────────────────────────
T(id="decoration", pillar="2 Kit School", kind="process", footage=STITCH,
  hook="FOUR WAYS TO PUT A BADGE ON A SHIRT", sub="They are not interchangeable.",
  overlay=("EMBROIDERY", "Thread stitched in. Raised, durable, adds weight."),
  machine="press",
  items=["SUBLIMATION — ink bonds inside the fibre", "EMBROIDERY — thread stitched in",
         "HEAT TRANSFER — film applied under heat", "SCREEN PRINT — ink on the surface"],
  caption="Four ways to decorate a kit, and the honest trade-offs.\n\nSUBLIMATION — ink becomes "
          "part of the fabric. Zero hand-feel, nothing to peel, unlimited colour. Polyester only, "
          "and it can't print white onto dark.\n\nEMBROIDERY — thread stitched in. The most "
          "premium feel, best for crests. Adds weight and cost.\n\nHEAT TRANSFER — applied film. "
          "3D, reflective, fluor, matt and silicone. Works on any fabric; application is "
          "everything.\n\nSCREEN PRINT — ink on the surface. Cheapest at volume, one screen per "
          "colour.\n\nThe real answer is usually a mix. All four run in our building, so a garment "
          "using three of them doesn't leave and doesn't add a week.",
  tags="#sublimation #embroidery #teamwear #footballkit #customkits #cutandsew",
  li_tags="#manufacturing"),

T(id="gsm", pillar="2 Kit School", kind="stat", footage=MILL,
  # "THE ONLY number that matters" was an overclaim, and the bank contradicted
  # it twice over: fabric-glossary says recovery is the one brands skip, and
  # cheap-vs-good tells buyers to ask for GSM *and* seam type. The stat card
  # also read "150 GSM — Match jersey" while the list underneath put 150 at the
  # bottom of the training-top band. Same screen, two different claims.
  hook="THE ONE FABRIC NUMBER NOBODY EXPLAINS", sub="And it's on every quote you'll ever read.",
  overlay=("IT'S JUST YARN", "Lighter isn't cheaper by accident. It's less of it."),
  stat=(150, " GSM", "Where a match jersey tops out",
        "Grams per square metre. Above this you're buying a training top."),
  items=["130–150 GSM — match jersey", "150–180 GSM — training top",
         "180–220 GSM — polo, warm-up", "240–320 GSM — hoodie, sweat"],
  caption="GSM = grams per square metre. It's fabric weight, and it's the number that matters "
          "most.\n\n130–150 — match jersey. Light, fast-drying.\n150–180 — training top. The "
          "everyday workhorse.\n180–220 — polo, warm-up.\n240–320 — hoodie, sweat.\n\nLighter "
          "isn't cheaper by accident — it's less yarn. If a factory quotes you without a GSM, you "
          "don't know what you're buying.\n\nAsk for GSM and seam type before you ask for a price.",
  tags="#fabric #gsm #teamwear #cutandsew #clothingmanufacturer #footballkit",
  li_tags="#sourcing"),

T(id="fabric-glossary", pillar="2 Kit School", kind="list", footage=MILL,
  hook="NINE WORDS ON EVERY TEAMWEAR QUOTE", sub="Recovery is the one brands skip.",
  overlay=("FABRIC GLOSSARY", "Save this before your next spec call."),
  items=["INTERLOCK — double-knit, smooth both sides, stable",
         "SINGLE JERSEY — lighter, curls at a raw edge", "PIQUÉ — textured waffle. The polo fabric",
         "MESH — open structure, for airflow panels", "JACQUARD — pattern knitted in, not printed",
         "RECOVERY — whether it returns to shape. Separate from stretch, and more important"],
  caption="Nine fabric words that appear on every teamwear quote.\n\nINTERLOCK — double-knit, "
          "smooth both sides, more stable. Classic jersey body.\nSINGLE JERSEY — lighter, one "
          "smooth face, curls at a raw edge.\nPIQUÉ — textured waffle. The polo fabric.\nMESH — "
          "open structure for airflow.\nJACQUARD — pattern knitted into the fabric, not printed "
          "on.\nMOISTURE WICKING — ask whether it's a finish or the fibre. A finish washes out."
          "\nSPANDEX — stretch content, 5–10% in a fitted kit.\nRECOVERY — whether it returns to "
          "shape after stretching.\n\nRecovery is the one brands skip, and it's why some kit looks "
          "baggy at the knees by March.",
  tags="#fabric #teamwear #cutandsew #apparelmanufacturing #kitdesign #footballkit #textiles",
  li_tags="#sourcing #textiles"),

T(id="cheap-vs-good", pillar="2 Kit School", kind="compare", footage=STITCH,
  hook="A £15 JERSEY AND A £45 JERSEY", sub="Same photo. Different garment.",
  overlay=("WHAT YOU CAN'T SEE", "Three things that never show in a product shot."),
  compare=("THE DIFFERENCE",
           ("£15", ["Lighter fabric, less yarn", "Overlocked seams that rub",
                    "Printed vinyl badge that peels"]),
           ("£45", ["Correct GSM for the job", "Flatlocked seams, no ridge",
                    "Sublimated or stitched badge"]), "right"),
  caption="Three things separate a £15 jersey from a £45 one, and none of them show in a product "
          "photo.\n\n1. Fabric weight. Lighter isn't cheaper by accident — it's less yarn.\n2. Seam "
          "construction. Overlocked vs flatlocked. One rubs at 70 minutes, one doesn't.\n3. How "
          "the badge is applied. Printed vinyl peels. Sublimated ink doesn't.\n\nNext time a "
          "factory quotes you, ask for GSM and seam type. Those two numbers tell you more than the "
          "price does.",
  tags="#footballkit #teamwear #cutandsew #clothingmanufacturer #jerseycheck #kitdesign",
  li_tags="#sourcing"),

T(id="seams", pillar="2 Kit School", kind="list", footage=STITCH,
  hook="THIS SEAM IS WHY THE SHIRT DOESN'T RUB", sub="And most tech packs never specify it.",
  overlay=("FLATLOCK VS OVERLOCK", "One sits flat. One leaves a ridge."),
  items=["FLATLOCK — edges butted and stitched flat. No inside ridge",
         "OVERLOCK — faster, cheaper, leaves a raised seam",
         "Fine on a leisure tee. Wrong on a match jersey",
         "Specify it in the tech pack or you get whichever is cheaper"],
  caption="A flatlock seam has two pieces of fabric butted edge to edge and stitched flat, so "
          "there's no ridge on the inside. That's the difference between a shirt you forget you're "
          "wearing and one that chafes at 70 minutes.\n\nAn overlocked seam is faster and cheaper "
          "and perfectly fine on a leisure tee. On a match jersey it's the wrong choice.\n\nMost "
          "brands don't specify seams, then wonder why the fit feels different from the sample "
          "they liked.",
  tags="#cutandsew #teamwear #footballkit #apparelmanufacturing #sewing #kitdesign",
  li_tags="#manufacturing"),

T(id="sublimation-limits", pillar="2 Kit School", kind="list", footage=MILL,
  hook="SUBLIMATION CANNOT PRINT ON COTTON", sub="Anyone saying otherwise is about to disappoint you.",
  overlay=("THE CHEMISTRY", "Ink needs a polymer to bond into."),
  items=["Sublimation needs polyester. On cotton there's nothing for the ink to bond to",
         "SCREEN PRINT — the standard answer for cotton",
         "EMBROIDERY — works on anything, best for small marks",
         "HEAT TRANSFER — works on cotton, application is everything",
         "Or change the fabric: a poly-cotton blend takes it, softer and more muted"],
  caption="Sublimation cannot print on 100% cotton. The chemistry doesn't work — the ink needs a "
          "polymer to bond into.\n\nAny supplier telling you otherwise is going to coat the "
          "cotton, which changes the hand-feel, or deliver something that fades fast.\n\nFor a "
          "cotton range: screen print, embroidery, or heat transfer. Or change the fabric — a "
          "poly-cotton blend takes sublimation on the polyester fraction, softer and more muted. "
          "Sometimes that's the look you wanted anyway.\n\nPick the fabric for how the garment "
          "should feel, then pick decoration to suit. Doing it the other way round is how brands "
          "end up with a kit they don't like the feel of.",
  tags="#sublimation #cutandsew #apparelmanufacturing #teamwear #fabric #customkits",
  li_tags="#manufacturing #sourcing"),

T(id="white-kit", pillar="2 Kit School", kind="list", footage=MILL,
  hook="YOUR WHITE KIT WENT GREY", sub="Only one of the three reasons is the factory's fault.",
  overlay=("WHY WHITE FAILS", "Three causes. One is a spec you can demand."),
  items=["Polyester picks up dye from other garments in the wash",
         "Optical brighteners wash out — they were never permanent",
         "Low-grade fabric with uneven whiteness to begin with",
         "Ask for the whiteness grade. It's a spec, and it's rarely volunteered"],
  caption="White kit goes grey for three reasons, and only one of them is the factory's fault."
          "\n\n1. Polyester picks up dye from other garments in the wash. Not fixable in "
          "manufacturing.\n2. Optical brighteners wash out. They were never permanent.\n3. "
          "Low-grade fabric with uneven whiteness to begin with. That one IS on the factory."
          "\n\nAsk for the whiteness grade on white polyester. It's a spec, and it's rarely "
          "volunteered.",
  tags="#footballkit #teamwear #cutandsew #fabric #kitcare #clothingmanufacturer",
  li_tags="#sourcing"),

T(id="recovery-test", pillar="2 Kit School", kind="list", footage=STITCH,
  hook="STRETCH ISN'T THE TEST. RECOVERY IS.", sub="Two seconds, and it tells you more than the label.",
  overlay=("PULL THE CUFF", "Then let go and watch."),
  items=["Stretch is how far the fabric goes", "Recovery is whether it comes back",
         "Pull a cuff and release. Instant return means good recovery",
         "Stays slightly open? That's the shirt that looks tired by March"],
  caption="Everyone tests stretch. Almost nobody tests recovery.\n\nStretch is how far the fabric "
          "goes. Recovery is whether it comes back.\n\nPull a cuff and let go. If it returns "
          "instantly, good recovery. If it stays slightly open, that's the shirt that'll look "
          "tired by March.\n\nIt's a two-second test and it tells you more than the composition "
          "label does.",
  tags="#fabric #cutandsew #teamwear #clothingmanufacturer #footballkit #fabrictest",
  li_tags="#sourcing"),

T(id="factory-questions", pillar="2 Kit School", kind="list", footage=CUT,
  hook="SEVEN QUESTIONS BEFORE YOU SEND A DEPOSIT", sub="Number 7 sorts it out on its own.",
  overlay=("ASK THESE", "If they can't answer in one email, that's your answer."),
  items=["What's the GSM and composition you're quoting?",
         "Which decoration is in-house, which is subcontracted?",
         "Lead time from approved sample, not from deposit?",
         "MOQ per colourway, not per style?",
         "How many inspection points, and what does each check?",
         "Who signs off a shade variance?",
         "Can I see this week's floor on a live video call?"],
  caption="Seven questions. If a factory can't answer all of them in one email, that's your "
          "answer.\n\nNumber 7 is the one that sorts it out. A factory that makes your garments "
          "can show you the line this week. A trading company can't.\n\nWe'd answer all seven in "
          "writing. Ask us.",
  tags="#teamwear #cutandsew #clothingbrandowner #apparelmanufacturing #customkits #sourcing",
  li_tags="#sourcing #procurement"),

T(id="shrinkage", pillar="2 Kit School", kind="list", footage=MILL,
  hook="IT SHRANK BECAUSE NOBODY ASKED", sub="Shrinkage is a test, and it's free to demand.",
  overlay=("SPECIFY IT", "Or inherit whatever the fabric does."),
  items=["Every knit fabric moves in the first wash",
         "A shrinkage test tells you how much, before bulk is cut",
         "Patterns are graded to compensate — if someone asks for it",
         "Put a tolerance in the tech pack: ±3% is normal, ±5% is not"],
  caption="Garments shrink because knit fabric relaxes in the first wash. That's physics, not "
          "a defect.\n\nWhat separates a good supplier from a bad one is whether anyone measured "
          "it before cutting 2,000 pieces. A shrinkage test tells you the number, and the pattern "
          "gets graded to compensate.\n\nPut a tolerance in your tech pack. ±3% is normal. ±5% "
          "means somebody skipped the test.",
  tags="#cutandsew #fabric #teamwear #apparelmanufacturing #techpack #kitdesign",
  li_tags="#manufacturing #sourcing"),

# ─────────────────────────── INSIDE THE FLOOR / CLUBS ────────────────────────
T(id="quality", pillar="3 Sourcing Math", kind="stat", footage=CUT,
  hook="MOST QUALITY PROBLEMS AREN'T SEWING PROBLEMS",
  sub="They're fabric problems nobody checked at intake.",
  overlay=("THE CUT GETS CHECKED", "Piece count against the marker, before anything moves."),
  stat=(5, "", "Inspection points", "The first one saves the most money."),
  items=["FABRIC ARRIVAL — shade, weight, flaws", "PATTERN — grading across the size run",
         "BULK CUT — piece count vs the marker", "SPECIAL SEWING — collars, plackets, sleeves",
         "FINISHING — adhesion, measurement, pack"],
  caption="Most quality problems in teamwear aren't sewing problems. They're fabric problems "
          "nobody checked at intake, and they only surface after 2,000 garments are cut.\n\nWe "
          "inspect at 5 points: fabric arrival, pattern, bulk cut, special sewing, finishing."
          "\n\nThe first one saves the most. Shade variance caught on an incoming roll costs a "
          "roll. Caught after cutting, it costs the order.\n\nNone of this is unusual. What's "
          "unusual is publishing it, so you can ask about a specific stage instead of asking "
          "\"do you do QC?\" — which every factory answers yes to.\n\nAsk which stage catches "
          "shade variance, and who signs it off.",
  tags="#qualitycontrol #teamwear #cutandsew #apparelmanufacturing #sourcing #manufacturing",
  li_tags="#sourcing #qualitycontrol"),

T(id="cutting", pillar="1 Inside the Floor", kind="process", footage=CUT,
  hook="SIXTY LAYERS, ONE PASS", sub="Everything after this depends on getting it right.",
  overlay=("THE CUT", "Pieces come off stacked and identical."),
  machine="cut",
  items=["Fabric spread in layers, pattern laid out as a marker",
         "Get the marker wrong and you waste fabric on every garment",
         "The cut is inspected before anything moves to the line",
         "Piece count checked against the marker"],
  caption="Before a single stitch, fabric gets spread in layers and the pattern laid out as a "
          "marker. Get the marker wrong and you waste fabric on every garment in the run.\n\nThe "
          "pieces come off stacked and identical — that's the whole point. Every garment starts "
          "from the same shape.\n\nIt's one of our five inspection points: piece count and "
          "placement checked against the marker before anything reaches a sewing line.",
  tags="#cutandsew #patternmaking #teamwear #apparelmanufacturing #clothingmanufacturer #howitsmade",
  li_tags="#manufacturing"),

T(id="sewing-line", pillar="1 Inside the Floor", kind="process", footage=SEW,
  hook="A JERSEY ISN'T SEWN BY ONE PERSON", sub="And that's exactly why it comes out consistent.",
  overlay=("THE LINE", "Each operator does one operation, hundreds of times a day."),
  machine="sew",
  items=["The garment moves down the line, one operation per station",
         "Repetition is what makes it consistent, not what makes it careless",
         "The operations that fail have stretch or shape",
         "Collars, plackets and sleeve insertions get checked specifically"],
  caption="A jersey isn't sewn by one person start to finish. It moves down the line, and each "
          "operator does one operation hundreds of times a day — which is exactly why it comes out "
          "consistent.\n\nFour lines here.\n\nThe operations that fail are the ones with stretch "
          "or shape: collars, plackets, sleeve insertions. Those get checked specifically at the "
          "special-sewing stage.",
  tags="#cutandsew #sewing #teamwear #apparelmanufacturing #clothingmanufacturer #madeinegypt",
  li_tags="#manufacturing"),

T(id="embroidery", pillar="1 Inside the Floor", kind="process", footage=STITCH,
  hook="FIFTEEN THOUSAND STITCHES, ONE CREST", sub="You can feel it. That's the point.",
  overlay=("EMBROIDERY", "Thread sits on top of the fabric, not inside it."),
  machine="embroidery",
  items=["Multiple needles, one colour each, swapping as the design builds",
         "Thread sits on the surface — that's the premium feel and the added weight",
         "Best for crests and sponsor marks", "Not for full-garment graphics. That's sublimation"],
  caption="An embroidered crest, close up.\n\nMultiple needles, one colour each, the machine "
          "swapping between them as the design builds. Thread sits on top of the fabric, which is "
          "why it feels the way it does and why it adds weight.\n\nBest for crests and sponsor "
          "marks. Not for full-garment graphics — that's what sublimation is for.",
  tags="#embroidery #satisfying #cutandsew #teamwear #clothingmanufacturer #howitsmade",
  li_tags="#manufacturing"),

T(id="heat-press", pillar="1 Inside the Floor", kind="process", footage=None,
  hook="NOTHING. THEN EVERYTHING.", sub="Sixty seconds at 200°C.",
  # The overlay said HEAT TRANSFER while the items and caption described
  # SUBLIMATION — two different processes, and the decoration post teaches the
  # difference. Heat transfer lays a film on the surface; sublimation turns ink
  # to gas that bonds inside the fibre. Getting that wrong in our own video
  # undoes the post that explains it.
  overlay=("SUBLIMATION", "Ink turns to gas and bonds inside the fibre."),
  machine="press",
  items=["Blank polyester goes in with a paper transfer",
         "The ink turns to gas and bonds inside the fibre",
         "The paper comes off grey — the colour has left it",
         "Nothing to feel, nothing to peel"],
  caption="Sublimation press, 60 seconds at 200°C.\n\nBlank polyester goes in with a paper "
          "transfer. The ink turns to gas, bonds inside the fibre, and the paper comes off grey."
          "\n\nFull-garment graphics, no hand-feel, nothing to peel.\n\nThe trade-off: polyester "
          "only, and it can't print white onto a dark base. Those are real limits, not fine print.",
  tags="#sublimation #satisfying #cutandsew #clothingmanufacturer #teamwear #howitsmade",
  li_tags="#manufacturing"),

T(id="nameset", pillar="4 Built for Clubs", kind="list", footage=STITCH,
  hook="NAMES AND NUMBERS ARE WHERE KIT GOES WRONG", sub="Four variables, and one wrong shows up in March.",
  overlay=("THE NAMESET", "Film, temperature, dwell time, pressure."),
  items=["Film type decides hand-feel and how far it reads",
         "Temperature and dwell time decide whether it stays on",
         "Pressure decides the edge quality",
         "We run 3D, reflective, fluor, matt and silicone"],
  caption="Names and numbers are where kit becomes a specific player's shirt, and where most "
          "complaints come from. Film that lifts at the corner after a season. Numbers that crack. "
          "Letters that bleed.\n\nIt comes down to four variables: the film, the temperature, the "
          "dwell time and the pressure. Get one wrong and it shows up three months later.\n\nWe "
          "run 3D, reflective, fluor, matt and silicone. The choice is usually about hand-feel and "
          "how far away it needs to read.",
  tags="#teamwear #footballkit #heattransfer #customkits #nameset #apparelmanufacturing",
  li_tags="#manufacturing"),

T(id="kit-decisions", pillar="4 Built for Clubs", kind="list", footage=STITCH,
  hook="ONE KIT. ELEVEN DECISIONS.", sub="None of them are default settings.",
  overlay=("WHAT WAS CHOSEN", "Every one has a cheaper and a dearer version."),
  items=["Fabric — poly interlock, mid-weight, for print quality",
         "Seams — flatlock at shoulders and sides", "Body graphic — sublimated before cutting",
         "Crest — embroidered, for the raised feel", "Numbers — heat transfer, matt film",
         "Label — heat transfer, so there's nothing to itch"],
  caption="A finished kit, and the decisions inside it.\n\nFabric: poly interlock, mid-weight, for "
          "stability and print quality.\nSeams: flatlock at the shoulders and sides.\nBody "
          "graphic: sublimated — printed before the panels were cut, so it runs edge to edge with "
          "no break.\nCrest: embroidered.\nNumbers: heat transfer, matt film.\nCollar and cuffs: "
          "ribbed, with recovery that holds.\nLabel: heat transfer, nothing to itch.\n\nNone of "
          "these are default settings. Every one was chosen, and every one has a cheaper and a "
          "more expensive version.\n\nThat's what a tech pack conversation actually is.",
  tags="#teamwear #footballkit #kitdesign #customkits #apparelmanufacturing #sublimation",
  li_tags="#manufacturing #productdevelopment"),

T(id="goalkeeper", pillar="4 Built for Clubs", kind="list", footage=STITCH,
  hook="A KEEPER SHIRT ISN'T A LONGER-SLEEVED OUTFIELD SHIRT", sub="Four things change.",
  overlay=("GOALKEEPER KIT", "Built for a different job."),
  items=["Elbow padding changes the sleeve construction",
         "Heavier fabric, because it meets the ground",
         "Looser cut through the body for reach",
         "Different colour rules — it has to contrast with both teams"],
  caption="A goalkeeper shirt isn't an outfield shirt with longer sleeves.\n\nElbow padding "
          "changes the sleeve construction. The fabric is heavier because it meets the ground "
          "repeatedly. The body is cut looser for reach. And the colour has to contrast with both "
          "teams and both other keepers, which is a rule, not a preference.\n\nIf your kit "
          "supplier quotes a keeper shirt at the same price as an outfield one, they haven't read "
          "the brief.",
  tags="#goalkeeper #footballkit #teamwear #kitdesign #customkits #cutandsew",
  li_tags="#manufacturing"),

T(id="reorder", pillar="4 Built for Clubs", kind="compare", footage=SEW,
  hook="THE MID-SEASON REORDER", sub="Where teamwear margins quietly die.",
  overlay=("REORDERS", "The order nobody plans for."),
  compare=("WHEN A CLUB ADDS 200 PIECES IN MARCH",
           ("10-WEEK CHAIN", ["Arrives in June", "Season is over",
                              "You eat it or you lose the club"]),
           ("2-WEEK BUILD", ["Arrives in April", "Still in season",
                             "Same fabric lot if you planned it"]), "right"),
  caption="The mid-season reorder is where teamwear margins die.\n\nA club adds 200 pieces in "
          "March. On a 10-week chain it arrives in June, the season is over, and you either eat "
          "the cost or lose the club.\n\nOn a 2-week build it arrives in April, still in season."
          "\n\nThe thing that makes reorders work isn't speed alone — it's whether your supplier "
          "held the fabric lot. Ask about that before the season starts, not during it.",
  tags="#teamwear #footballkit #reorder #clubkit #customkits #sourcing",
  li_tags="#sourcing #teamwear"),

T(id="packing", pillar="1 Inside the Floor", kind="stat", footage=MILL,
  hook="THIS IS WHAT A DAY LOOKS LIKE", sub="Folded, bagged, cartoned, labelled.",
  overlay=("FINISHING", "The stage that decides what the buyer sees first."),
  stat=(2000, "", "Pieces a day", "Then 3 to 7 days by sea to Southern Europe."),
  items=["Trim, measure against spec, press, fold, bag, carton",
         "The last of the five inspection points",
         "Checks decoration adhesion and final measurements",
         "A well-made garment badly folded arrives looking cheap"],
  caption="Trim, measure, press, fold, bag, carton.\n\nThis is the last of the five inspection "
          "points, and it checks things the earlier stages can't: decoration adhesion, final "
          "measurements against spec, and whether the pack matches the order.\n\nIt's also the "
          "stage that decides what your customer sees in the first three seconds of opening the "
          "box. A well-made garment, badly folded, arrives looking cheap.",
  tags="#cutandsew #teamwear #apparelmanufacturing #qualitycontrol #logistics #madeinegypt",
  li_tags="#manufacturing #logistics"),
]

BY_ID = {t["id"]: t for t in BANK}

if __name__ == "__main__":
    from collections import Counter
    print(f"{len(BANK)} topics")
    for k, v in sorted(Counter(t["pillar"] for t in BANK).items()):
        print(f"  {k:24s} {v}")
    for k, v in sorted(Counter(t["kind"] for t in BANK).items()):
        print(f"  kind {k:20s} {v}")
    ids = [t["id"] for t in BANK]
    assert len(ids) == len(set(ids)), "duplicate id"
    print("ids unique ✓")
