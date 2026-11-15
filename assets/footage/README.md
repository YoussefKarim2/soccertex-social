# Footage pools

Two directories, and they never mix.

## `own/`  — filmed at SoccerTex
Clips of the real floor. These MAY carry first-person language: "our line",
"this is our cutting table", "inside SoccerTex".

## `stock/` — licensed from Pexels
Free for commercial use under the Pexels licence. These MAY NOT claim to be
SoccerTex's floor. `engine/footage.py` enforces this: a `FootageScene` with
`source="stock"` raises `StockMisuse` before rendering if the overlay contains
first-person factory language, and stamps "Library footage · not SoccerTex's
floor" on the frame.

Two reasons, and the second matters more than the first:
1. Pexels' licence prohibits implying endorsement; Pixabay's prohibits
   misleading use.
2. Buyers vetting a supplier specifically check whether factory video is real.
   Generic stock passed off as your own floor is the exact red flag they look
   for — it would cost more trust than it buys attention.

## `proxy/` — generated
9:16, 1080x1920, 30fps versions the renderer actually reads. Rebuilt by
`make_proxies.sh`. Don't edit by hand.

## Current stock clips (Pexels, free licence)

All eighteen are real footage of real workshops and mills — none of them
SoccerTex's. Every one is stamped on screen, and `engine/vibes.py` refuses to
set SoccerTex's own voice (we, our, us, the name) over any of them.

| Proxy | What it shows | Pexels id | By |
|---|---|---|---|
| `cutting-machine` | band knife through a stack of cut parts | 32071139 | Dmitriy |
| `cutting-knife` | round-knife cutter on white fabric | 4622040 | cottonbro |
| `cutting-fabric-scissors` | shears through fabric, close | 36302125 | — |
| `sewing-factory` | sewing room, one operator, many machines | 4622428 | cottonbro |
| `sewing-floor` | sewing room against a brick wall | 4622334 | cottonbro |
| `sewing-closeup` | industrial needle and foot, close | 39984010 | Dmitriy |
| `sewing-threading` | hands threading an industrial machine | 5758549 | ShvetsA |
| `sewing-machine-vertical` | white machine, hands feeding fabric | 4622443 | cottonbro |
| `sewing-machine-working` | embroidery head stitching a white motif | 11955972 | — |
| `embroidery-line` | a row of multi-head embroidery machines | 38852130 | Dmitriy |
| `thread-spools` | wall of coloured thread cones, a hand choosing | 4622435 | cottonbro |
| `mill-worker` | operator at a spinning frame | 40381989 | Cruz in Portugal |
| `mill-process` | operator at a loom, dark cloth | 40382001 | Cruz in Portugal |
| `fabric-production-overhead` | white fabric on frames, from above | 32268481 | — |
| `fabric-check` | man with a tape measure checking cloth on a table | 6766759 | Tima Miroshnichenko |
| `pressing` | hands pressing navy cloth on a board | 37361951 | Photos by Collis |
| `screen-printing` | screen-print carousel from above | 34692310 | Alexandre |
| `wide-printer` | wide-format printer laying down colour | 36570941 | aerodronmx |

Source page for any of them: `pexels.com/video/<id>/`. Fourteen were added on
15 Nov 2026, after "i want more real life videos of factory videos, such as
cutting, stitching". The raw downloads are not kept — only the proxies are —
so `make_proxies.sh` will not rebuild these; download again by id if needed.

Three things to know before using one:

- `wide-printer` prints a banner with Spanish words on it and `embroidery-line`
  shows the machine maker's badge. Neither may be mirrored.
- `sewing-machine-vertical` goes dark between 11s and 14s (someone walks past).
- `fabric-check`, `mill-worker`, `mill-process`, `sewing-factory` and
  `sewing-floor` show identifiable people. Pexels' licence forbids showing
  them in a bad light, so no line about a bad supplier or a mistake goes over
  them — use a close-up of a machine for those.

Looked at and rejected: a fashion studio chalking a pattern, two domestic
packing clips, and two clips of players in other brands' kit.

## Adding more

Pexels, **filter orientation to Vertical** — this matters, a landscape clip
centre-cropped to 9:16 usually loses the subject. Searches that worked:
`garment factory` · `sewing machine` · `embroidery machine` · `cutting fabric`
· `textile factory` · `screen printing` · `fabric roll` · `ironing fabric`.
Still missing, and worth another look: a heat press, a sublimation printer on
paper, folding and packing on a factory table, a flatlock machine.

Put the 9:16 file in `proxy/`, add it to the table above, and name it in
`build_vibes.py` with `clip("name", start_seconds)`.
