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

| File | Source |
|---|---|
| `sewing-machine-vertical.mp4` | pexels.com/video/a-sewing-machine-is-shown-in-a-photo-4622443/ |
| `sewing-machine-working.mp4` | pexels.com/video/close-up-view-of-working-sewing-machine-11955972/ |
| `cutting-fabric-scissors.mp4` | pexels.com/video/precision-fabric-cutting-by-hand-with-scissors-36302125/ |
| `fabric-production-overhead.mp4` | pexels.com/video/industrial-fabric-production-process-from-above-32268481/ |

## Adding more

Pexels, **filter orientation to Vertical** — this matters, a landscape clip
centre-cropped to 9:16 usually loses the subject. Searches that work:
`sewing machine` · `embroidery machine` · `cutting fabric` · `textile factory`
· `garment factory` · `screen printing` · `fabric texture` · `heat press`

Drop the file in `stock/`, run `./make_proxies.sh`, reference it in
`engine/content.py`.
