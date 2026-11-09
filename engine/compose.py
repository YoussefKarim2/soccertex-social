#!/usr/bin/env python3
"""Turns a bank topic into a finished video.

Two cuts per topic:

  social   ~16s, hard hook, fast list   → TikTok and Instagram
  business ~21s, measured, more text    → LinkedIn

TikTok and Instagram share the social cut but carry different captions, and on
TikTok a trending sound goes over the top at upload. That is repurposing, not
duplication — the same footage, a different frame for a different audience.

The composer picks its scene sequence from the topic's `kind`, so a new topic
is a dict in bank.py and nothing else.
"""
from __future__ import annotations
from pathlib import Path

from engine.render import (Video, StatScene, ListScene, CompareScene, CTAScene)
from engine.motion import (SewingScene, CutScene, PressScene, EmbroideryScene,
                           PunchScene)
from engine.footage import FootageScene

ROOT = Path(__file__).resolve().parent.parent
PROXY = ROOT / "assets" / "footage" / "proxy"

FOOTAGE = {
    "sew":    PROXY / "sewing-machine-vertical.mp4",
    "stitch": PROXY / "sewing-machine-working.mp4",
    "cut":    PROXY / "cutting-fabric-scissors.mp4",
    "mill":   PROXY / "fabric-production-overhead.mp4",
}
MACHINE = {
    "sew":        lambda s, t, u: SewingScene(s, t, u),
    "cut":        lambda s, t, u: CutScene(s, t, u),
    "press":      lambda s, t, u: PressScene(s, t, u),
    "embroidery": lambda s, t, u: EmbroideryScene(s, t, u),
}

# variant -> (hook_s, machine_s, list_per, stat_s, compare_s, cta_line, cta_sub)
TUNE = {
    "social":   (2.4, 3.2, 1.10, 2.4, 3.6, "SEE\nTHE FLOOR.", "soccertexhq.com"),
    "business": (2.9, 3.6, 1.35, 3.0, 4.2, "SEE\nTHE FLOOR.", "Quote in 24h · soccertexhq.com"),
}


def _footage_or_machine(topic, seconds, variant):
    """Prefer real footage; fall back to the drawn machine; else nothing."""
    key = topic.get("footage")
    title, sub = topic.get("overlay", (None, None))
    if key and FOOTAGE.get(key) and FOOTAGE[key].exists():
        speed = 0.7 if variant == "social" else 0.85
        return FootageScene(FOOTAGE[key], seconds, title, sub,
                            source="stock", speed=speed)
    m = topic.get("machine")
    if m and m in MACHINE:
        return MACHINE[m](seconds, title or m.upper(), sub)
    return None


def compose(topic: dict, variant: str = "social", out_dir: Path | None = None) -> Video:
    if variant not in TUNE:
        raise ValueError(f"variant must be one of {list(TUNE)}")
    hook_s, mach_s, per, stat_s, cmp_s, cta_line, cta_sub = TUNE[variant]
    out_dir = out_dir or (ROOT / "out" / "video")
    v = Video(out_dir / f"{topic['id']}--{variant}.mp4")

    v.add(PunchScene(topic["hook"], topic.get("sub"), hook_s))

    kind = topic["kind"]
    items = topic.get("items") or []

    if kind == "process":
        sc = _footage_or_machine(topic, mach_s, variant)
        if sc: v.add(sc)
        if topic.get("machine") and topic.get("footage"):
            m = MACHINE.get(topic["machine"])
            if m:
                t, s = topic.get("overlay", (None, None))
                v.add(m(mach_s, t or topic["machine"].upper(), s))
        if items:
            v.add(ListScene(_title(topic), items, per=per))

    elif kind == "compare":
        # Footage first when we have it — it is the strongest part of the cut —
        # then the number, then the comparison that pays both off.
        sc = _footage_or_machine(topic, mach_s, variant)
        if sc: v.add(sc)
        if topic.get("stat"):
            val, suf, lab, note = topic["stat"]
            v.add(StatScene(val, suf, lab, note, stat_s))
        ctitle, left, right, winner = topic["compare"]
        v.add(CompareScene(ctitle, left, right, cmp_s, winner=winner))

    elif kind == "stat":
        val, suf, lab, note = topic["stat"]
        v.add(StatScene(val, suf, lab, note, stat_s))
        sc = _footage_or_machine(topic, mach_s, variant)
        if sc: v.add(sc)
        if items:
            v.add(ListScene(_title(topic), items, per=per))

    else:  # list
        sc = _footage_or_machine(topic, mach_s, variant)
        if sc: v.add(sc)
        v.add(ListScene(_title(topic), items, per=per))

    v.add(CTAScene(cta_line, cta_sub, 2.0 if variant == "social" else 2.4))
    return v


def _title(topic):
    """A short on-screen heading for the list scene."""
    o = topic.get("overlay")
    if o and o[0]:
        return o[0]
    return topic["hook"][:34]


def caption_for(topic: dict, platform: str) -> str:
    """Platform-adapted caption. LinkedIn gets 0-3 hashtags, the rest get the full set."""
    body = topic["caption"]
    tags = topic["li_tags"] if platform == "linkedin" else topic["tags"]
    if platform == "tiktok":
        # TikTok shows one line before the fold; lead with the hook.
        body = topic["hook"].capitalize().rstrip(".") + ".\n\n" + body
    return body + ("\n\n" + tags if tags else "")


def variant_for(platform: str) -> str:
    return "business" if platform == "linkedin" else "social"


if __name__ == "__main__":
    import sys
    from engine.bank import BANK, BY_ID
    which = sys.argv[1:] or [BANK[0]["id"]]
    for tid in which:
        t = BY_ID[tid]
        for variant in ("social", "business"):
            v = compose(t, variant)
            v.write()
            print(f"  {tid}--{variant:9s} {v.seconds:5.1f}s  "
                  f"{v.out.stat().st_size/1024/1024:.2f} MB")
