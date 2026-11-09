#!/usr/bin/env python3
"""Soundtrack generator — synthesised from scratch with numpy.

Why synthesised rather than licensed: every free music API is unreachable from
this environment, and more importantly, TikTok and Instagram trending audio can
only be attached inside their apps. Downloading a chart track and muxing it into
an MP4 is copyright infringement and gets the audio muted or the account struck.

So the tracks here are generated, which makes them royalty-free by construction —
nobody else owns them. They are built to sit UNDER a voice or to be replaced:
when you post to TikTok by hand you can swap in a trending sound in the app,
which is the only legal way to use one.

    from engine.audio import Track
    Track(seconds=20, bpm=124).build().save("bed.wav")
"""
from __future__ import annotations
import numpy as np
from pathlib import Path
import struct, wave

SR = 44100


# ------------------------------------------------------------- primitives --
def _env(n, attack=0.002, decay=0.1, sustain=0.0, release=0.05, curve=3.0):
    a = int(attack * SR); d = int(decay * SR); r = int(release * SR)
    s = max(0, n - a - d - r)
    out = np.concatenate([
        np.linspace(0, 1, a, endpoint=False) if a else np.array([]),
        (1 - np.linspace(0, 1, d, endpoint=False) ** (1 / curve)) * (1 - sustain) + sustain if d else np.array([]),
        np.full(s, sustain),
        np.linspace(sustain, 0, r) if r else np.array([]),
    ])
    return np.pad(out, (0, max(0, n - len(out))))[:n]


def kick(dur=0.32, f0=110, f1=42):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    click = np.random.RandomState(1).randn(n) * np.exp(-t * 420) * 0.35
    return (body * _env(n, .001, dur * .9, 0, .01, 2.2) + click) * 0.95


def snare(dur=0.22):
    n = int(dur * SR); t = np.arange(n) / SR
    rs = np.random.RandomState(7)
    noise = rs.randn(n)
    # crude band-pass: difference of two smoothed copies
    k = np.ones(14) / 14
    noise = noise - np.convolve(noise, k, mode="same")
    tone = np.sin(2 * np.pi * 185 * t) * 0.35
    return (noise * 0.8 + tone) * _env(n, .001, dur * .8, 0, .02, 2.5) * 0.55


def hat(dur=0.055, open_=False):
    n = int(dur * SR)
    rs = np.random.RandomState(13)
    x = rs.randn(n)
    x = x - np.convolve(x, np.ones(4) / 4, mode="same")      # high-pass-ish
    return x * _env(n, .0005, dur * (.9 if open_ else .5), 0, .005, 3) * 0.26


def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    f = freq * (1 + detune)
    ph = (t * f) % 1.0
    return 2 * ph - 1


def pluck(freq, dur, amp=0.3):
    n = int(dur * SR)
    x = (saw(freq, n) * .5 + saw(freq, n, .004) * .5)
    # one-pole lowpass that opens then closes
    env = _env(n, .003, dur * .75, .0, .06, 2.0)
    cut = np.clip(env, 0, 1)
    y = np.zeros(n); z = 0.0
    for i in range(n):
        a = 0.06 + 0.5 * cut[i]
        z += a * (x[i] - z)
        y[i] = z
    return y * env * amp


def sub(freq, dur, amp=0.34):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return x * _env(n, .006, dur * .6, .55, .08, 1.6) * amp


def whoosh(dur=0.55, amp=0.5):
    """Transition sweep — noise through a rising then falling filter."""
    n = int(dur * SR); t = np.arange(n) / SR
    rs = np.random.RandomState(29)
    x = rs.randn(n)
    sweep = np.sin(np.pi * t / dur) ** 2
    y = np.zeros(n); z = 0.0
    for i in range(n):
        a = 0.004 + 0.30 * sweep[i]
        z += a * (x[i] - z)
        y[i] = x[i] - z            # high-pass: what the lowpass didn't keep
    return y * sweep * amp


def impact(dur=0.5, amp=0.7):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 160 * np.exp(-t * 16) + 38
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    rs = np.random.RandomState(31)
    nz = rs.randn(n) * np.exp(-t * 60) * .4
    return (body + nz) * _env(n, .001, dur * .85, 0, .04, 2.0) * amp


# ------------------------------------------------------------------ track --
NOTES = {"A1": 55.00, "C2": 65.41, "D2": 73.42, "E2": 82.41, "F2": 87.31, "G2": 98.00,
         "A2": 110.0, "C3": 130.8, "D3": 146.8, "E3": 164.8, "F3": 174.6, "G3": 196.0,
         "A3": 220.0, "C4": 261.6, "D4": 293.7, "E4": 329.6}


class Track:
    """A driving, slightly industrial bed in A minor. Mix sits low so it
    supports the cut instead of fighting it."""

    def __init__(self, seconds, bpm=124, seed=0):
        self.seconds = seconds
        self.bpm = bpm
        self.n = int(seconds * SR)
        self.buf = np.zeros(self.n + SR)
        self.rs = np.random.RandomState(seed)

    def _at(self, beat):
        return int(beat * 60.0 / self.bpm * SR)

    def _add(self, sig, at, gain=1.0):
        a = max(0, at); b = min(len(self.buf), at + len(sig))
        if b <= a: return
        self.buf[a:b] += sig[: b - a] * gain

    def build(self):
        beats = self.seconds * self.bpm / 60.0
        bars = int(beats / 4) + 1

        # progression: Am — F — C — G, one bar each
        prog = [("A2", [220.0, 261.6, 329.6]),
                ("F2", [174.6, 220.0, 261.6]),
                ("C3", [130.8, 164.8, 196.0]),
                ("G2", [196.0, 246.9, 293.7])]

        for bar in range(bars):
            b0 = bar * 4
            root, chord = prog[bar % 4]

            # drums
            for i, beat in enumerate([0, 1, 2, 3]):
                self._add(kick(), self._at(b0 + beat), 1.0 if i % 2 == 0 else .8)
            self._add(snare(), self._at(b0 + 1), .9)
            self._add(snare(), self._at(b0 + 3), .9)
            for eighth in range(8):
                op = eighth == 7
                self._add(hat(open_=op), self._at(b0 + eighth * .5),
                          .8 if eighth % 2 == 0 else .5)
            # a 16th roll into each new 4-bar phrase
            if bar % 4 == 3:
                for k in range(4):
                    self._add(snare(.1), self._at(b0 + 3 + k * .25), .35 + k * .12)

            # bass on root
            self._add(sub(NOTES[root], 60.0 / self.bpm * 2.0), self._at(b0), .9)
            self._add(sub(NOTES[root], 60.0 / self.bpm * 1.0), self._at(b0 + 2.5), .7)

            # sparse pluck motif, only after the first bar so the open is clean
            if bar >= 1:
                for j, beat in enumerate([0.5, 1.5, 2.25, 3.5]):
                    self._add(pluck(chord[j % len(chord)] * 2, .34),
                              self._at(b0 + beat), .22)

        out = self.buf[: self.n]

        # gentle sidechain feel: duck everything slightly on each beat
        duck = np.ones(self.n)
        for beat in range(int(beats) + 1):
            a = self._at(beat)
            if a >= self.n: break
            ln = min(int(.18 * SR), self.n - a)
            duck[a:a + ln] *= np.linspace(.62, 1.0, ln)
        out = out * duck

        # soft-clip and normalise with headroom for a voice later
        out = np.tanh(out * 1.15)
        peak = np.max(np.abs(out)) or 1.0
        self.out = out / peak * 0.62
        return self

    def accent(self, seconds, kind="whoosh", gain=1.0):
        """Place a transition sound at a timestamp."""
        sig = whoosh() if kind == "whoosh" else impact()
        self._add_out(sig, int(seconds * SR), gain)
        return self

    def _add_out(self, sig, at, gain):
        a = max(0, at); b = min(len(self.out), at + len(sig))
        if b <= a: return
        self.out[a:b] = np.tanh(self.out[a:b] + sig[: b - a] * gain)

    def fade(self, ms=450):
        k = int(ms / 1000 * SR)
        if k * 2 < len(self.out):
            self.out[:k] *= np.linspace(0, 1, k)
            self.out[-k:] *= np.linspace(1, 0, k)
        return self

    def save(self, path):
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        data = np.clip(self.out, -1, 1)
        stereo = np.stack([data, data], axis=1)
        pcm = (stereo * 32767).astype("<i2").tobytes()
        with wave.open(str(p), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(pcm)
        return p


def soundtrack(seconds, cuts=(), path="out/audio/bed.wav", bpm=124, seed=0):
    """Build a bed of `seconds` with a whoosh at each cut timestamp."""
    t = Track(seconds, bpm, seed).build()
    for i, c in enumerate(cuts):
        if 0 < c < seconds - .3:
            t.accent(c - .28, "whoosh", .45)
            t.accent(c, "impact", .30)
    return t.fade().save(path)


if __name__ == "__main__":
    p = soundtrack(18.0, cuts=(2.4, 5.0, 9.2, 14.0), path="out/audio/demo.wav")
    print("wrote", p, p.stat().st_size // 1024, "KB")
