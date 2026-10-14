#!/usr/bin/env python3
"""PIKA K-Store - banda sonora original generada por código.

Future-bass / K-pop a 120 BPM (1 beat = 15 frames a 30 fps), 15 compases = 30 s.
Lee timeline.json (la misma fuente que usa el video) para clavar cada efecto
de sonido en el frame exacto de cada corte, golpe o transición.

Uso:  python3 audio/compose.py        (requiere numpy, scipy y ffmpeg)
Sale: public/audio/pika-soundtrack.wav (48 kHz, estéreo, -14 LUFS, -1 dBTP)
"""
import json
import pathlib
import re
import subprocess
import tempfile

import numpy as np
from scipy import ndimage, signal
from scipy.io import wavfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "timeline.json").read_text())
OUT = ROOT / "public" / "audio" / "pika-soundtrack.wav"

SR = 48000
FPS = TL["fps"]
BEAT = 60.0 / TL["bpm"]
BAR = 4 * BEAT
S16 = BEAT / 4
DUR = TL["durationInFrames"] / FPS
N = int(round(DUR * SR))
rng = np.random.default_rng(1969)


# ----------------------------------------------------------------- helpers
def bt(bar, beat=0.0):
    """Tiempo en segundos de un compás (1-indexado) y beat."""
    return (bar - 1) * BAR + beat * BEAT


def ft(frame):
    return frame / FPS


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def norm(x, peak=1.0):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def filt(x, kind, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype=kind, fs=SR, output="sos"), x, axis=0)


def sweep(x, kind, fc_of_p, block=256, q=1.6):
    """Filtro variable en el tiempo (procesado por bloques con estado)."""
    out = np.zeros_like(x)
    zi = None
    n = len(x)
    for s in range(0, n, block):
        fc = float(np.clip(fc_of_p(s / n), 30, SR * 0.45))
        f = [fc / q, min(fc * q, SR * 0.47)] if kind == "band" else fc
        sos = signal.butter(2, f, btype=kind, fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2) + x.shape[1:])
        out[s:s + block], zi = signal.sosfilt(sos, x[s:s + block], axis=0, zi=zi)
    return out


def mixn(*xs):
    """Suma señales de distinto largo."""
    out = np.zeros((max(len(x) for x in xs),) + xs[0].shape[1:])
    for x in xs:
        out[: len(x)] += x
    return out


def fades(x, a=0.003, r=0.006):
    n = len(x)
    env = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        env[:na] = np.linspace(0, 1, na)
    if nr:
        env[-nr:] *= np.linspace(1, 0, nr)
    return x * (env[:, None] if x.ndim == 2 else env)


def pan_st(x, pan=0.0):
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1) * np.sqrt(2)


class Bus:
    def __init__(self):
        self.x = np.zeros((N + SR * 4, 2))

    def add(self, t, snd, gain=1.0, pan=0.0):
        if snd.ndim == 1:
            snd = pan_st(snd, pan)
        i = int(round(t * SR))
        if i < 0:
            snd, i = snd[-i:], 0
        n = min(len(snd), len(self.x) - i)
        if n > 0:
            self.x[i:i + n] += snd[:n] * gain


# ------------------------------------------------------ band-limited osc
TBL = 2048
_tables = {}


def table(f, kind, fmax):
    key = (round(f, 1), kind, fmax)
    if key not in _tables:
        ph = np.arange(TBL) / TBL
        k = np.arange(1, max(1, int(fmax // f)) + 1)
        if kind == "square":
            k = k[k % 2 == 1]
        w = np.sin(2 * np.pi * np.outer(k, ph)) / k[:, None]
        _tables[key] = norm(w.sum(0))
    return _tables[key]


def osc(f, n, kind="saw", phase=0.0, fmax=12000, cents=0.0):
    f = f * 2 ** (cents / 1200)
    tb = table(f, kind, fmax)
    idx = ((phase + f * np.arange(n) / SR) % 1.0) * TBL
    i0 = idx.astype(int)
    fr = idx - i0
    return tb[i0] * (1 - fr) + tb[(i0 + 1) % TBL] * fr


def supersaw(midis, n, voices=7, spread=24, fmax=9000, width=0.85):
    out = np.zeros((n, 2))
    for m in midis:
        for v in range(voices):
            d = (v - (voices - 1) / 2) / ((voices - 1) / 2)
            s = osc(mtof(m), n, "saw", rng.random(), fmax, d * spread)
            out += pan_st(s, d * width) / np.sqrt(2)
    return out / (len(midis) * np.sqrt(voices))


# ------------------------------------------------------------ instruments
def kick():
    t = tt(0.55)
    f = 47 + 125 * np.exp(-t / 0.028) + 320 * np.exp(-t / 0.004)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.2) * np.minimum(1, t / 0.0008)
    knock = norm(filt(rng.standard_normal(len(t)), "band", [180, 900])) * np.exp(-t / 0.012) * 0.35
    click = filt(rng.standard_normal(len(t)), "high", 2500) * np.exp(-t / 0.0022) * 0.4
    return np.tanh(1.8 * (body + knock + click)) / np.tanh(1.8)


def clap(tone=185, tail=0.11):
    t = tt(0.5)
    nz = norm(filt(rng.standard_normal(len(t)), "band", [900, 4500]))
    env = np.zeros(len(t))
    for d in (0.0, 0.009, 0.019):
        env += np.where(t >= d, np.exp(-np.clip(t - d, 0, None) / 0.0045), 0)
    env += np.where(t >= 0.027, np.exp(-np.clip(t - 0.027, 0, None) / tail), 0) * 0.75
    body = np.sin(2 * np.pi * tone * t) * np.exp(-t / 0.045) * 0.45
    return norm(nz * env + body)


def snare(tone=200):
    t = tt(0.25)
    nz = norm(filt(rng.standard_normal(len(t)), "band", [1200, 7000]))
    s = nz * np.exp(-t / 0.06) + np.sin(2 * np.pi * tone * t) * np.exp(-t / 0.04) * 0.6
    return norm(s)


def hat(open_=False):
    t = tt(0.4 if open_ else 0.08)
    nz = filt(rng.standard_normal(len(t)), "high", 7000, 4)
    met = sum(np.sign(np.sin(2 * np.pi * f * t + rng.random() * 6)) for f in (5317, 6721, 8123, 9601))
    s = (norm(nz) + filt(met, "high", 6500) * 0.12) * np.exp(-t / (0.13 if open_ else 0.017))
    return norm(s)


def shaker():
    t = tt(0.07)
    s = filt(rng.standard_normal(len(t)), "band", [4000, 11000]) * np.sin(np.pi * t / t[-1]) ** 2
    return norm(s)


def pluck(m, dur=0.5, bright=0.6):
    t = tt(dur)
    f = mtof(m)
    a = osc(f, len(t), "saw", 0, 12000) * np.exp(-t / 0.045)
    b = (osc(f, len(t), "square", 0.25, 5000) * 0.45 + np.sin(2 * np.pi * f * t)) * np.exp(-t / 0.26)
    s = (a * bright + b) * np.minimum(1, t / 0.002)
    return fades(norm(filt(s, "low", 7500)), 0.001, 0.02)


def boom(f0=70, f1=30, dur=1.6, decay=0.55):
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t / 0.13)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decay) * np.minimum(1, t / 0.002)
    return np.tanh(1.5 * s)


def crack(dur=0.3, decay=0.035):
    t = tt(dur)
    return norm(filt(rng.standard_normal(len(t)), "high", 1400)) * np.exp(-t / decay)


def body(decay=0.14):
    """Capa de medios de los impactos (lo que se escucha en un parlante de celular)."""
    t = tt(0.6)
    nz = norm(filt(rng.standard_normal(len(t)), "band", [160, 1800]))
    tone = np.sin(2 * np.pi * np.cumsum(220 * np.exp(-t / 0.08) + 90) / SR)
    return norm((nz * 0.8 + tone * 0.6) * np.exp(-t / decay) * np.minimum(1, t / 0.001))


def crash(dur=3.0):
    t = tt(dur)
    nz = filt(rng.standard_normal((len(t), 2)), "high", 3200, 4)
    met = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) for f in (3450, 4870, 6210, 7330, 8890))
    s = norm(nz) + pan_st(filt(met, "high", 3000), 0) * 0.05
    return s * (np.exp(-t / 0.9) * np.minimum(1, t / 0.003))[:, None]


def whoosh(dur=0.38, f0=500, f1=6000, p0=-0.7, p1=0.7):
    t = tt(dur)
    nz = rng.standard_normal(len(t))
    s = norm(sweep(nz, "band", lambda p: f0 * (f1 / f0) ** p, q=1.5))
    p = t / t[-1]
    s *= np.sin(np.pi * p) ** 2
    ang = (p0 + (p1 - p0) * p + 1) * np.pi / 4
    return np.stack([s * np.cos(ang), s * np.sin(ang)], 1) * np.sqrt(2)


def riser(dur=2.0, f0=250, f1=9000):
    t = tt(dur)
    p = t / t[-1]
    nz = norm(sweep(rng.standard_normal(len(t)), "band", lambda q: f0 * (f1 / f0) ** q, q=1.4))
    f = 180 * 2 ** (3 * p)
    saw = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 + np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR) * 0.2
    s = (nz * 0.8 + saw) * p ** 2.2
    return fades(s, 0.01, 0.004)


def rev_cymbal(dur=1.0):
    c = crash(dur)[::-1]
    return c * (np.linspace(0, 1, len(c)) ** 2)[:, None]


def beep(m, dur=0.11):
    t = tt(dur)
    f = mtof(m)
    s = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * 3 * f * t) + 0.08 * np.sin(2 * np.pi * 5 * f * t)
    return fades(norm(s), 0.002, 0.012)


def printer(dur=0.32):
    t = tt(dur)
    nz = norm(filt(rng.standard_normal(len(t)), "band", [1600, 6500]))
    buzz = (np.sin(2 * np.pi * 62 * t) > 0.1).astype(float)
    chunks = np.repeat(rng.random(int(dur / 0.035) + 2) > 0.25, int(0.035 * SR))[: len(t)].astype(float)
    chunks = ndimage.uniform_filter1d(chunks, 120)
    motor = np.sin(2 * np.pi * 118 * t) * 0.25 + np.sin(2 * np.pi * 236 * t) * 0.12
    s = (nz * buzz * 0.8 + motor) * chunks
    return fades(norm(s), 0.006, 0.03)


def rip(dur=0.42):
    t = tt(dur)
    nz = norm(filt(rng.standard_normal(len(t)), "band", [1100, 7500]))
    grains = ndimage.uniform_filter1d((rng.random(len(t)) > 0.985).astype(float) * rng.random(len(t)), 90)
    env = (t / t[-1]) ** 0.6 * np.minimum(1, (t[-1] - t) / 0.03)
    return norm(nz * (0.35 + grains * 6) * env)


def pop(m):
    t = tt(0.16)
    f = mtof(m) * (0.55 + 0.45 * np.minimum(1, t / 0.018))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05)
    s += crack(0.16, 0.003)[: len(t)] * 0.15
    return norm(s)


def ding(m, dur=1.8):
    t = tt(dur)
    fc = mtof(m)
    idx = 2.8 * np.exp(-t / 0.25)
    s = np.sin(2 * np.pi * fc * t + idx * np.sin(2 * np.pi * fc * 3.5 * t)) * np.exp(-t / 0.55)
    s += np.sin(2 * np.pi * fc * 2 * t) * np.exp(-t / 0.3) * 0.3
    return fades(norm(s), 0.001, 0.05)


def tick():
    t = tt(0.05)
    s = np.sin(2 * np.pi * 2900 * t) * np.exp(-t / 0.008) + crack(0.05, 0.002)[: len(t)] * 0.4
    return norm(s)


def stamp():
    t = tt(0.4)
    thud = boom(150, 60, 0.4, 0.06)
    body = norm(filt(rng.standard_normal(len(t)), "band", [180, 1400])) * np.exp(-t / 0.025)
    return norm(thud + body * 0.7)


def neon_buzz(dur):
    t = tt(dur)
    hum = osc(100, len(t), "saw", 0, 3000) * 0.6 + osc(50, len(t), "square", 0, 1500) * 0.4
    zap = filt(rng.standard_normal(len(t)), "band", [2000, 8000]) * 0.25
    return filt(hum, "low", 1800) + zap


# ------------------------------------------------------------- harmony
CH = {  # voicings (MIDI) + bajo
    "F": ([53, 57, 60, 64], 29),   # Fmaj7
    "G": ([55, 59, 62, 64], 31),   # G6
    "Em": ([52, 55, 59, 62], 28),  # Em7
    "Am": ([57, 60, 64, 67], 33),  # Am7
    "C": ([60, 64, 67, 74], 36),   # Cadd9
}
# (compás, beat inicio, beat fin, acorde)
HARM = [(1, 0, 4, "F"), (2, 0, 4, "F"), (3, 0, 4, "G"), (4, 0, 4, "Em"), (5, 0, 4, "Am"),
        (6, 0, 4, "F"), (7, 0, 4, "G"), (8, 0, 4, "Em"), (9, 0, 4, "Am"),
        (10, 0, 2, "F"), (10, 2, 4, "G"), (11, 0, 4, "F"), (12, 0, 4, "G"), (13, 0, 4, "Em"),
        (14, 0, 2, "F"), (14, 2, 4, "G"), (15, 0, 4, "C")]

HOOK = {  # melodía principal en semicorcheas: (pos, nota, largo)
    "F": [(0, 81, 2), (3, 79, 2), (6, 76, 2), (8, 79, 2), (10, 81, 2), (12, 84, 4)],
    "G": [(0, 83, 2), (3, 81, 2), (6, 79, 2), (8, 74, 2), (10, 76, 2), (12, 79, 4)],
    "Em": [(0, 79, 2), (3, 76, 2), (6, 74, 2), (8, 76, 2), (10, 79, 2), (12, 83, 4)],
    "Am": [(0, 81, 2), (3, 79, 2), (6, 76, 2), (8, 72, 2), (10, 74, 2), (12, 76, 4)],
}
STAB = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0]  # ritmo future-bass

SECTION = {1: "intro", 2: "dropA", 3: "dropA", 4: "dropA", 5: "groove", 6: "groove", 7: "groove",
           8: "groove", 9: "groove", 10: "break", 11: "dropB", 12: "dropB", 13: "dropB",
           14: "outro", 15: "final"}

drums, bass, music, lead, sfx, send = (Bus() for _ in range(6))

# ------------------------------------------------------------ drums
kicks = []
K = kick()
for bar in range(2, 15):
    sec = SECTION[bar]
    if sec == "break":
        continue
    for b in range(4):
        t = bt(bar, b)
        drums.add(t, K, 0.62)
        kicks.append(t)
    for b in (1, 3):
        drums.add(bt(bar, b), clap(), 0.8, 0.0)
        send.add(bt(bar, b), clap(), 0.12)
    for s in range(16):
        t = bt(bar, s / 4)
        if s % 4 == 2:
            drums.add(t, hat(True), 0.24, 0.25)
        elif sec != "outro" or s % 2 == 0:
            acc = 0.26 if s % 2 == 0 else 0.16
            drums.add(t + (0.012 if s % 2 else 0), hat(), acc, -0.2)
        if sec == "groove" and s % 2 == 1:
            drums.add(t, shaker(), 0.12, 0.4)
    if sec in ("dropA", "dropB") and bar in (2, 11):
        drums.add(bt(bar), crash(), 0.33)

# break (compás 10): redoble que acelera hacia el drop B
for i, (beat, step) in enumerate([(2.0, 0.5), (3.0, 0.25), (3.75, 0.125)]):
    b = beat
    end = [3.0, 3.75, 3.875][i]
    while b < end - 1e-6:
        prog = (b - 2.0) / 1.875
        drums.add(bt(10, b), snare(190 + 180 * prog), 0.3 + 0.7 * prog)
        b += step
for b in (0.5, 1.5):
    drums.add(bt(10, b), hat(True), 0.18)

# ------------------------------------------------------ sidechain pump
side = np.ones(len(music.x))
for k in kicks:
    i = int(k * SR)
    n = min(int(0.5 * SR), len(side) - i)
    t = np.arange(n) / SR
    dip = 1 - 0.78 * np.minimum(1, t / 0.003) * np.exp(-t / 0.13)
    side[i:i + n] = np.minimum(side[i:i + n], dip)

# ------------------------------------------------- bajo, acordes, lead
for bar, b0, b1, name in HARM:
    voic, root = CH[name]
    sec = SECTION[bar]
    t0, t1 = bt(bar, b0), bt(bar, b1)
    n = int((t1 - t0) * SR)
    tl = np.arange(n) / SR

    # bajo: sub sinusoidal + saw filtrado
    if sec not in ("intro", "final", "break"):
        sub = np.sin(2 * np.pi * mtof(root + 12) * tl)
        mid = np.tanh(2.2 * filt(osc(mtof(root + 24), n, "saw", 0, 5000), "low", 1100))
        bass.add(t0, fades(pan_st(sub * 0.5 + mid * 0.5), 0.004, 0.01), 0.42)

    # acordes
    saw = supersaw(voic, n)
    if sec == "intro":
        pad = sweep(saw, "low", lambda p: 300 * (3200 / 300) ** p)
        music.add(t0, fades(pad * np.minimum(1, tl / 0.4)[:, None], 0.01, 0.01), 1.1)
        continue
    if sec == "final":
        n2 = int(3.0 * SR)
        big = supersaw(voic + [voic[0] - 12], n2, spread=30)
        tf = np.arange(n2) / SR
        big = sweep(big, "low", lambda p: 9000 * (600 / 9000) ** p)
        music.add(t0, fades(big * np.exp(-tf / 0.9)[:, None], 0.002, 0.05), 0.9)
        send.add(t0, big * np.exp(-tf / 0.9)[:, None], 0.45)
        bass.add(t0, pan_st(np.sin(2 * np.pi * mtof(root + 12) * tf) * np.exp(-tf / 0.8)), 0.35)
        continue
    if sec == "break":
        pad = sweep(saw, "low", (lambda p: 2600 * (380 / 2600) ** p) if b0 == 0 else (lambda p: 380 * (5000 / 380) ** (p ** 1.5)))
        music.add(t0, fades(pad, 0.01, 0.01), 1.3)
        send.add(t0, pad, 0.18)
        continue

    lp = {"dropA": 6000, "dropB": 7500, "groove": 3400, "outro": 5000}[sec]
    sawf = filt(saw, "low", lp)
    pad = filt(saw, "low", 2000)
    music.add(t0, fades(pad, 0.01, 0.01), 0.55 if sec == "groove" else 0.38)
    send.add(t0, pad, 0.1)
    if sec in ("dropA", "dropB", "outro"):
        gate = np.zeros(n)
        steps = int(round((b1 - b0) * 4))
        for s in range(steps):
            if STAB[(int(b0 * 4) + s) % 16]:
                i = int(s * S16 * SR)
                m = min(n - i, int(0.3 * SR))
                ts = np.arange(m) / SR
                gate[i:i + m] = np.maximum(gate[i:i + m], np.minimum(1, ts / 0.004) * np.exp(-ts / 0.16))
        stab = sawf * gate[:, None]
        music.add(t0, stab, 1.35 if sec == "dropB" else 1.1)
        send.add(t0, stab, 0.16)

    # lead hook
    if sec == "dropB" or (sec == "dropA" and bar >= 3) or sec == "outro":
        notes = HOOK[name]
        for pos, m, ln in notes:
            if pos < b0 * 4 or pos >= b1 * 4:
                continue
            tn = bt(bar, pos / 4)
            p = pluck(m, ln * S16 + 0.35)
            g = 0.62 if sec == "dropB" else 0.48
            lead.add(tn, p, g, 0.0)
            send.add(tn, pan_st(p), g * 0.5)
    # arpegio suave en la sección del escáner
    if sec == "groove":
        arp = voic + [voic[1] + 12]
        for s in range(8):
            m = arp[s % len(arp)] + 12
            p = pluck(m, 0.3, 0.3)
            lead.add(t0 + s * 2 * S16, p, 0.17, -0.4 if s % 2 else 0.4)
            send.add(t0 + s * 2 * S16, pan_st(p), 0.05)

# --------------------------------------------- intro: zumbido de neón
flick = TL["neonFlicker"]
buzz = neon_buzz(len(flick) / FPS + 0.2)
g = np.repeat(np.array(flick + [1] * 6, float), int(SR / FPS))[: len(buzz)]
g = ndimage.uniform_filter1d(g, 60) * np.exp(-np.arange(len(buzz)) / SR / 0.5)
sfx.add(0, buzz * g, 0.06)
sfx.add(bt(1), riser(BAR - 0.25), 0.4)
sfx.add(bt(2) - 0.9, rev_cymbal(0.9), 0.28)
sfx.add(bt(10, 2), riser(BAR / 2 - 0.12, 300, 11000), 0.55)
sfx.add(bt(11) - 1.0, rev_cymbal(1.0), 0.3)

# -------------------------------------------- efectos desde timeline.json
for cue in TL["cues"]:
    t = ft(cue["f"])
    ty = cue["type"]
    note = cue.get("note", 60)
    if ty == "slam":
        s = mixn(boom(95, 42, 0.9, 0.22), crack(0.3, 0.03) * 0.45)
        st = supersaw([note, note + 12], int(0.5 * SR), spread=18)
        st = filt(st, "low", 3000) * np.exp(-tt(0.5) / 0.12)[:, None]
        sfx.add(t, s, 0.45)
        sfx.add(t, body(), 0.5)
        sfx.add(t, st, 0.8)
        send.add(t, mixn(pan_st(s * 0.5), st), 0.3)
    elif ty == "drop":
        s = mixn(boom(68, 27, 2.2, 0.75), crack(0.5, 0.05) * 0.5)
        sfx.add(t, s, 0.6)
        sfx.add(t, body(0.25), 0.7)
        sfx.add(t, crash(3.0), 0.45)
        send.add(t, pan_st(crack(0.5, 0.06)), 0.4)
    elif ty == "hit":
        s = mixn(boom(85, 40, 0.7, 0.18), crack(0.25, 0.025) * 0.5)
        sfx.add(t, s, 0.36)
        sfx.add(t, body(), 0.45)
        send.add(t, pan_st(crack(0.25, 0.03)), 0.25)
    elif ty == "tick":
        sfx.add(t, tick(), 0.25, 0.3)
    elif ty == "flip":
        sfx.add(t - 0.02, tick(), 0.22, -0.3)
        sfx.add(t - 0.06, whoosh(0.16, 1500, 7000, 0.6, -0.6), 0.1)
    elif ty == "whoosh":
        sfx.add(t - 0.05, whoosh(0.45, 400, 7000), 0.3)
    elif ty == "scan":
        sfx.add(t - 0.2, whoosh(0.24, 2500, 600, 0.8, 0.0), 0.2)
        sfx.add(t, beep(note), 0.3)
        send.add(t, pan_st(beep(note)), 0.12)
        sfx.add(t + 0.12, printer(0.3), 0.13, 0.35)
    elif ty == "printlong":
        sfx.add(t, printer(1.1), 0.18, 0.0)
    elif ty == "rip":
        sfx.add(t, rip(0.42), 0.32)
    elif ty == "stamp":
        sfx.add(t, stamp(), 0.55)
        send.add(t, pan_st(stamp()), 0.15)
    elif ty == "pop":
        sfx.add(t, pop(note), 0.3)
        send.add(t, pan_st(pop(note)), 0.12)
    elif ty == "ding":
        sfx.add(t, ding(note), 0.18)
        send.add(t, pan_st(ding(note)), 0.2)
    elif ty == "final":
        s = mixn(boom(70, 28, 2.6, 0.9), crack(0.6, 0.06) * 0.5)
        sfx.add(t, s, 0.4)
        sfx.add(t, body(0.3), 0.7)
        sfx.add(t, crash(3.5), 0.45)
        sfx.add(t, ding(96, 2.2), 0.12)
        send.add(t, pan_st(crack(0.5, 0.06)), 0.4)

# --------------------------------------- silencio pre-drop (antes del 2 y el 11)
gate = np.ones(len(music.x))
for bar in (2, 11):
    i1 = int(bt(bar) * SR)
    i0 = i1 - int(BEAT / 2 * SR)
    gate[i0:i1] = 0.0
gate = ndimage.uniform_filter1d(gate, 240)

# ----------------------------------------------------------------- reverb
def make_ir(rt=1.9, pre=0.018):
    t = np.arange(int((rt * 1.1 + pre) * SR)) / SR
    ir = rng.standard_normal((len(t), 2)) * np.exp(-6.9 * t / rt)[:, None]
    ir[: int(pre * SR)] = 0
    ir = filt(filt(ir, "low", 6000), "high", 220)
    return ir / np.sqrt(np.sum(ir ** 2, axis=0))


ir = make_ir()
wet = np.stack([signal.fftconvolve(send.x[:, c], ir[:, c])[: len(send.x)] for c in range(2)], 1)

# ----------------------------------------------------------------- mezcla
mix = (drums.x * 0.95 * gate[:, None]
       + bass.x * side[:, None] * gate[:, None]
       + music.x * side[:, None] * gate[:, None]
       + lead.x * (0.55 + 0.45 * side)[:, None] * gate[:, None]
       + sfx.x
       + wet * 0.55)
mix = mix[:N]
# fade final (los últimos 0.35 s) para que el loop/cierre quede limpio
mix[-int(0.35 * SR):] *= np.linspace(1, 0, int(0.35 * SR))[:, None] ** 2
mix = filt(mix, "high", 38, 2)
mix = mix + filt(mix, "high", 4500, 2) * 0.4  # brillo (high-shelf suave)


def limiter(x, ceil_db=-1.2, look=0.004, rel=0.08):
    ceil = 10 ** (ceil_db / 20)
    peak = np.max(np.abs(x), axis=1)
    g_req = np.minimum(1.0, ceil / np.maximum(peak, 1e-9))
    L = int(look * SR)
    g = ndimage.minimum_filter1d(g_req, 2 * L + 1)
    a = np.exp(-1 / (rel * SR))
    g = signal.lfilter([1 - a], [1, -a], g - 1) + 1  # suavizado de liberación
    g = np.minimum(g, ndimage.minimum_filter1d(g_req, 2 * L + 1))
    return np.clip(x * g[:, None], -ceil, ceil)


def lufs(x):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        wavfile.write(f.name, SR, (x * 32767).astype(np.int16))
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f.name, "-af", "ebur128=peak=true",
                            "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])


mix = norm(mix, 0.9)
for _ in range(3):
    out = limiter(mix)
    gain = 10 ** ((-14.0 - lufs(out)) / 20)
    mix = mix * gain
out = limiter(mix)
OUT.parent.mkdir(parents=True, exist_ok=True)
wavfile.write(OUT, SR, (out * 32767).astype(np.int16))
print(f"{OUT.relative_to(ROOT)}  {len(out) / SR:.2f}s  {lufs(out):.1f} LUFS  peak {20 * np.log10(np.max(np.abs(out))):.1f} dBFS")
