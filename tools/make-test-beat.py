#!/usr/bin/env python3
"""Synthesizes review-audio/synctake-test-beat.m4a: a two-minute, 120 BPM CC0 beat.

Every sound is generated here, so the track is free of third-party rights. A clap on
beats 2 and 4 gives reviewers an obvious sync point. Needs macOS `afconvert`.
"""

import math
import random
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

RATE = 44100
BPM = 120
BARS = 60
BEAT = 60 / BPM
OUT = Path(__file__).resolve().parent.parent / "review-audio" / "synctake-test-beat.m4a"
BASS_NOTES = [55.0, 55.0, 65.41, 49.0]  # A1, A1, C2, G1: one per bar, looping

random.seed(13)
length = int(RATE * BEAT * 4 * BARS)
mix = [0.0] * length


def add(start_s, samples):
    start = int(start_s * RATE)
    for i, value in enumerate(samples):
        if start + i < length:
            mix[start + i] += value


def kick():
    n = int(0.35 * RATE)
    out, phase = [], 0.0
    for i in range(n):
        t = i / RATE
        phase += 2 * math.pi * (45 + 110 * math.exp(-t * 28)) / RATE
        out.append(0.9 * math.sin(phase) * math.exp(-t * 9))
    return out


def clap():
    n = int(0.18 * RATE)
    return [0.45 * (random.random() * 2 - 1) * math.exp(-(i / RATE) * 30) for i in range(n)]


def hat():
    n = int(0.05 * RATE)
    return [0.12 * (random.random() * 2 - 1) * math.exp(-(i / RATE) * 90) for i in range(n)]


def bass(freq, seconds):
    n = int(seconds * RATE)
    return [
        0.22 * math.sin(2 * math.pi * freq * i / RATE) * min(1.0, i / 400) * math.exp(-(i / RATE) * 3)
        for i in range(n)
    ]


KICK, CLAP, HAT = kick(), clap(), hat()
for bar in range(BARS):
    bar_start = bar * 4 * BEAT
    for beat in range(4):
        at = bar_start + beat * BEAT
        add(at, KICK)
        if beat in (1, 3):
            add(at, CLAP)
        add(at + BEAT / 2, HAT)
        add(at + BEAT / 2, bass(BASS_NOTES[bar % 4], BEAT / 2))

fade = int(2 * RATE)
for i in range(fade):
    mix[length - fade + i] *= 1 - i / fade
peak = max(abs(v) for v in mix)
frames = b"".join(struct.pack("<h", int(v / peak * 0.89 * 32767)) for v in mix)

with tempfile.TemporaryDirectory() as tmp:
    wav = Path(tmp) / "beat.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(frames)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "128000", str(wav), str(OUT)], check=True)
print(f"wrote {OUT}")
