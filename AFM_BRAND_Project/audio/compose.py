#!/usr/bin/env python3
"""AFM BRAND — original soundtrack + sound design, fully synthesised (no samples,
no third-party music). Deterministic: same input timeline -> same WAV.

Cinematic electronic, 120 BPM, D minor -> D major lift on the end card.
Every hit is placed from config/timeline.json, the same file the picture reads,
so sound and image cannot drift.

Usage:  python3 audio/compose.py      (needs numpy, scipy, soundfile, pyloudnorm)
Writes: public/audio/soundtrack.wav (master, 48 kHz / 24-bit stereo)
        ../output/audio/AFM_BRAND_music_stem.wav, AFM_BRAND_sfx_stem.wav
"""
import json, pathlib
import numpy as np
from scipy import signal
import soundfile as sf
import pyloudnorm as pyln

ROOT = pathlib.Path(__file__).resolve().parents[1]
T = json.loads((ROOT / "config" / "timeline.json").read_text())
C = T["cues"]
SR = 48000
DUR = float(T["duration"])
N = int(DUR * SR)
BEAT = 60.0 / T["bpm"]
rs = np.random.default_rng(20261012)

music = np.zeros((N, 2))
sfx = np.zeros((N, 2))
verb_send = np.zeros((N, 2))


# ----------------------------------------------------------------- helpers
def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def nm(name):  # "D3" / "A#2" -> MIDI note number
    return 12 * (int(name[-1]) + 1) + NOTE[name[:-1]]


def place(bus, x, t0, pan=0.0, gain=1.0, send=0.0):
    """Mix mono/stereo buffer x into bus at time t0 with equal-power pan."""
    i0 = int(round(t0 * SR))
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        x = np.stack([x * l * 1.414, x * r * 1.414], 1)
    a, b = max(i0, 0), min(i0 + len(x), N)
    if b <= a:
        return
    seg = x[a - i0:b - i0] * gain
    bus[a:b] += seg
    if send:
        verb_send[a:b] += seg * send


def env(n, a=0.005, d=0.1, s=0.0, r=0.05, sus_len=None):
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    sus_n = max(0, n - a_n - d_n - r_n) if sus_len is None else int(sus_len * SR)
    e = np.concatenate([np.linspace(0, 1, a_n, endpoint=False), np.linspace(1, s, d_n, endpoint=False), np.full(sus_n, s), np.linspace(s, 0, r_n)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def expdec(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def saw_blep(freq, n, phase0=0.0):
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    dt = f / SR
    ph = (phase0 + np.cumsum(dt)) % 1.0
    y = 2 * ph - 1
    m1 = ph < dt
    t1 = ph[m1] / dt[m1]
    y[m1] -= t1 + t1 - t1 * t1 - 1
    m2 = ph > 1 - dt
    t2 = (ph[m2] - 1) / dt[m2]
    y[m2] -= t2 * t2 + t2 + t2 + 1
    return y


def sine(freq, n, phase0=0.0):
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    return np.sin(2 * np.pi * (phase0 + np.cumsum(f) / SR))


def sos(kind, fc, order=2):
    fc = np.clip(fc, 20, SR / 2 * 0.95)
    return signal.butter(order, fc, btype=kind, fs=SR, output="sos")


def filt(x, kind, fc, order=2):
    return signal.sosfilt(sos(kind, fc, order), x, axis=0)


def sweep_filter(x, kind, fc_curve, block=256):
    """Time-varying Butterworth (block-wise, state carried)."""
    out = np.zeros_like(x)
    zi = None
    for i in range(0, len(x), block):
        s_ = sos(kind, float(fc_curve[min(i, len(fc_curve) - 1)]))
        if zi is None:
            zi = np.zeros((s_.shape[0], 2) + x.shape[1:])
        out[i:i + block], zi = signal.sosfilt(s_, x[i:i + block], axis=0, zi=zi)
    return out


def noise(n):
    return rs.standard_normal(n)


def tl(n, t0=0.0):
    return t0 + np.arange(n) / SR


# ----------------------------------------------------------------- harmony
# one chord per bar (2 s). D minor story, lifts to D major for the resolution.
CHORDS = [
    ["D3", "A3", "C4", "E4", "F4"],     # 0  Dm9
    ["D3", "A3", "C4", "E4", "F4"],     # 2
    ["A#2", "F3", "A3", "D4", "C5"],    # 4  Bbmaj9   (logo reveal)
    ["G2", "D3", "A#3", "F4", "A4"],    # 6  Gm9
    ["D3", "A3", "C4", "F4", "E5"],     # 8  Dm9      (drop)
    ["A#2", "F3", "A3", "D4", "F4"],    # 10 Bbmaj7
    ["F2", "C3", "A3", "E4", "G4"],     # 12 Fmaj9
    ["C3", "G3", "D4", "E4", "G4"],     # 14 Cadd9
    ["D3", "A3", "C4", "F4", "E5"],     # 16 Dm9
    ["A#2", "F3", "A3", "D4", "F4"],    # 18 Bbmaj7   (order)
    ["F2", "C3", "A3", "E4", "G4"],     # 20 Fmaj9
    ["G2", "D3", "A#3", "F4", "A4"],    # 22 Gm9      (advisor)
    ["A2", "E3", "G3", "D4", "E4"],     # 24 A7sus4   (tension into the dive)
    ["D3", "A3", "F#4", "E4", "A4"],    # 26 Dadd9 — resolution
    ["D3", "A3", "F#4", "E4", "A4"],    # 28
]


def chord_at(t):
    return CHORDS[min(int(t // 2), len(CHORDS) - 1)]


# ----------------------------------------------------------------- music: pads
def pad_layer():
    out = np.zeros((N, 2))
    for bar, ch in enumerate(CHORDS):
        t0 = bar * 2.0
        if t0 >= DUR:
            break
        length = 2.0 + (2.0 if bar >= 13 else 0.35)
        n = int(length * SR)
        for k, name in enumerate(ch):
            f = midi(nm(name))
            for d, pan in ((-7, -0.6), (0, 0.0), (7, 0.6)):  # detuned unison, cents
                v = saw_blep(f * 2 ** (d / 1200), n, rs.random())
                e = env(n, a=0.35 if bar not in (2, 13) else 0.02, d=0.2, s=0.85, r=0.6)
                place(out, v * e * 0.06, t0, pan=pan * (0.4 + 0.15 * k))
    # brightness follows the story: closed in the dark hook, opens on the reveal
    tt = tl(N)
    fc = np.interp(tt, [0, 3.9, 4.0, 7.9, 8.0, 21.9, 22.0, 25.9, 26.05, 30], [260, 1100, 2600, 1800, 3200, 3000, 1100, 2400, 5200, 2600])
    return sweep_filter(out, "lowpass", fc)


def sub_drone():
    tt = tl(N)
    # follow chord roots one octave down
    roots = np.array([midi(nm(chord_at(x)[0]) - 12) for x in tt[::SR // 100]])
    f = np.repeat(roots, SR // 100)[:N]
    v = sine(f, N) + 0.25 * sine(2 * f, N)
    amp = np.interp(tt, [0, 0.4, 3.9, 4.0, 7.9, 8.0, 22, 26.05, 28, 30], [0, 0.05, 0.12, 0.30, 0.18, 0.0, 0.0, 0.30, 0.16, 0.0])
    return np.stack([v * amp] * 2, 1)


# ----------------------------------------------------------------- music: rhythm section
kick_times, snare_times, hat_times = [], [], []
for b in np.arange(8.0, 22.0, BEAT):
    kick_times.append(b)
for b in np.arange(22.0, 25.5, BEAT * 2):
    kick_times.append(b)
for b in np.arange(8.0 + BEAT, 22.0, BEAT * 2):
    snare_times.append(b)
for b in np.arange(8.0, 25.5, BEAT / 4):
    hat_times.append(b)
# pre-drop pulse in the reveal (quarter-note heartbeat, felt more than heard)
pulse_times = list(np.arange(4.0, 8.0, BEAT))


def kick(gain=1.0):
    n = int(0.45 * SR)
    t = tl(n)
    f = 45 + 95 * np.exp(-t / 0.035)
    body = sine(f, n) * expdec(n, 0.16)
    click = filt(noise(n), "highpass", 2500) * expdec(n, 0.004) * 0.35
    return (np.tanh(1.6 * (body + click)) * 0.9) * gain


def snare():
    n = int(0.35 * SR)
    t = tl(n)
    tone = sine(185 + 40 * np.exp(-t / 0.02), n) * expdec(n, 0.06) * 0.35
    nz = filt(noise(n), "bandpass", [1200, 7500]) * expdec(n, 0.09)
    clap = np.zeros(n)
    for off in (0.0, 0.011, 0.022):  # layered clap transients
        i = int(off * SR)
        clap[i:] += filt(noise(n - i), "bandpass", [900, 3500]) * expdec(n - i, 0.012)
    return (tone + nz * 0.55 + clap * 0.5) * 0.55


def hat(open_=False, vel=1.0):
    n = int((0.22 if open_ else 0.06) * SR)
    x = filt(filt(noise(n), "highpass", 7000), "lowpass", 13500) * expdec(n, 0.07 if open_ else 0.012)
    return x * 0.15 * vel


def bassline():
    out = np.zeros((N, 2))
    for b in np.arange(8.0, 22.0, BEAT / 2):
        root = nm(chord_at(b)[0]) - 12
        step = int(round((b - 8.0) / (BEAT / 2))) % 8
        m = root + (12 if step in (3, 7) else 0)
        n = int(BEAT / 2 * SR * 0.92)
        v = saw_blep(midi(m), n) * 0.6 + sine(midi(m), n) * 0.8
        e = env(n, a=0.004, d=0.12, s=0.55, r=0.03)
        x = filt(v * e, "lowpass", 520 + 260 * (step % 2))
        place(out, x * 0.30, b)
    for b in np.arange(22.0, 25.5, BEAT):
        m = nm(chord_at(b)[0]) - 12
        n = int(BEAT * SR * 0.9)
        x = filt(sine(midi(m), n) * env(n, a=0.01, d=0.2, s=0.6, r=0.05), "lowpass", 300)
        place(out, x * 0.28, b)
    return out


def arp_layer():
    out = np.zeros((N, 2))
    pattern = [0, 2, 1, 3, 4, 3, 1, 2]
    for i, b in enumerate(np.arange(8.0, 22.0, BEAT / 4)):
        ch = chord_at(b)
        m = nm(ch[pattern[i % 8] % len(ch)]) + 12
        n = int(0.32 * SR)
        mod = sine(midi(m) * 2, n) * 1.8 * expdec(n, 0.05)  # light FM for a glassy pluck
        v = np.sin(2 * np.pi * np.cumsum(np.full(n, midi(m))) / SR + mod)
        x = v * expdec(n, 0.09) * (0.075 if i % 4 else 0.1)
        place(out, x, b, pan=0.45 if i % 2 else -0.45, send=0.45)
    # reveal: sparse glass notes
    for i, b in enumerate(np.arange(4.5, 8.0, BEAT)):
        ch = chord_at(b)
        m = nm(ch[(i * 2) % len(ch)]) + 24
        n = int(1.0 * SR)
        x = sine(midi(m), n) * expdec(n, 0.35) * 0.05
        place(out, x, b, pan=-0.5 + (i % 3) * 0.5, send=0.8)
    return out


# ----------------------------------------------------------------- sound design
def whoosh(dur, f0, f1, gain=0.3, pan0=-0.6, pan1=0.6, q=0.6):
    n = int(dur * SR)
    x = noise(n)
    fc = np.geomspace(f0, f1, n)
    y = np.zeros(n)
    zi = None
    for i in range(0, n, 256):
        lo = fc[i] * (1 - q / 2); hi = fc[i] * (1 + q / 2)
        s_ = sos("bandpass", [max(lo, 30), min(hi, SR / 2 * 0.9)])
        if zi is None:
            zi = np.zeros((s_.shape[0], 2))
        y[i:i + 256], zi = signal.sosfilt(s_, x[i:i + 256], zi=zi)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    y = y * e * gain
    pan = np.linspace(pan0, pan1, n)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([y * l * 1.414, y * r * 1.414], 1)


def riser(dur, gain=0.35):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    nz = filt(noise(n), "highpass", 400)
    nz = sweep_filter(nz, "lowpass", np.geomspace(600, 12000, n)) * t ** 2.2
    tone = sine(np.geomspace(110, 880, n), n) * t ** 3 * 0.25
    return (nz * 0.5 + tone) * gain


def impact(gain=1.0, tail=2.2, sub_f=52):
    n = int(tail * SR)
    t = tl(n)
    boom = sine(sub_f * (1 + 0.6 * np.exp(-t / 0.05)), n) * expdec(n, 0.6)
    body = filt(noise(n), "lowpass", 900) * expdec(n, 0.18) * 0.6
    air = filt(noise(n), "highpass", 4000) * expdec(n, 0.35) * 0.18
    return np.tanh((boom + body + air) * 1.2) * gain


def reverse_swell(dur, gain=0.25):
    n = int(dur * SR)
    x = filt(noise(n), "highpass", 3000) * np.linspace(0, 1, n) ** 3
    return x * gain


def tap():
    n = int(0.03 * SR)
    x = filt(noise(n), "bandpass", [1800, 6000]) * expdec(n, 0.003)
    x += sine(2400, n) * expdec(n, 0.006) * 0.3
    return x * 0.22


def chime(notes, spacing=0.11, gain=0.12, decay=0.6):
    n = int((decay * 2 + spacing * len(notes)) * SR)
    out = np.zeros(n)
    for i, m in enumerate(notes):
        k = int(i * spacing * SR)
        nn = n - k
        f = midi(m)
        mod = sine(f * 3.5, nn) * 1.2 * expdec(nn, 0.15)
        out[k:] += np.sin(2 * np.pi * f * np.arange(nn) / SR + mod) * expdec(nn, decay)
    return out * gain


def pop(f0=520, f1=980, dur=0.09, gain=0.18):
    n = int(dur * SR)
    return sine(np.geomspace(f0, f1, n), n) * env(n, a=0.002, d=dur * 0.8, s=0, r=0.01) * gain


def shimmer(dur, gain=0.08):
    n = int(dur * SR)
    out = np.zeros(n)
    for m in (nm("A5"), nm("D6"), nm("F#6"), nm("A6"), nm("E7")):
        out += sine(midi(m) * (1 + 0.0015 * rs.standard_normal()), n) * (0.6 + 0.4 * sine(5 + rs.random() * 3, n))
    return out * np.sin(np.pi * np.linspace(0, 1, n)) * gain


def build():
    # ---- music
    music[:] += pad_layer()
    music[:] += sub_drone()
    music[:] += bassline()
    music[:] += arp_layer()
    drums = np.zeros((N, 2))
    for k in kick_times:
        place(drums, kick(1.0 if k < 22 else 0.7), k)
    for s in snare_times:
        place(drums, snare(), s, send=0.25)
    for i, h in enumerate(hat_times):
        open_ = (i % 8) == 6
        place(drums, hat(open_, 1.0 if i % 4 == 2 else 0.6), h, pan=0.25 if i % 2 else -0.25)
    for p in pulse_times:
        place(drums, kick(0.35), p)
    # advisor scene: drums tuck under the chat
    tt = tl(N)
    duck = np.interp(tt, [0, 21.9, 22.2, 25.4, 25.6, 30], [1, 1, 0.55, 0.55, 0.0, 0.0])[:, None]
    drums = drums * duck
    music[:] += drums
    # contained, atmospheric opening: the music bus grows into the logo impact
    music[:] *= np.interp(tt, [0, 3.6, 3.95, 30], [0.42, 0.7, 1.0, 1.0])[:, None]
    # sidechain pump on pads/bass from the kick (subtle, -3 dB)
    sc = np.ones(N)
    for k in kick_times:
        i = int(k * SR); n = int(0.25 * SR)
        seg = 1 - 0.32 * np.exp(-np.arange(n) / (0.07 * SR))
        sc[i:i + n] = np.minimum(sc[i:i + n], seg[: max(0, min(n, N - i))])
    music[:] *= sc[:, None] * 0.85 + 0.15

    # ---- sound design (all from the shared cue sheet)
    a0, a1 = C["arcSweep"]
    place(sfx, whoosh(a1 - a0 + 0.5, 300, 6000, gain=0.26, pan0=-0.8, pan1=0.8, q=0.5), max(0, a0 - 0.05))
    place(sfx, shimmer(1.2, 0.05), 0.0, send=0.6)
    place(sfx, chime([nm("A5"), nm("E6")], 0.06, 0.07, 0.4), C["screenWake"], send=0.5)
    place(sfx, chime([nm("E6"), nm("A6")], 0.1, 0.10, 0.5), C["notification"], send=0.5)
    taps = [C["tapNotification"], C["tapExplore"], 8.82, C["tapCart"], C["tapAdvisor"]] + C["addToCart"]
    for t_ in taps:
        place(sfx, tap(), t_)
    place(sfx, whoosh(0.85, 200, 3000, gain=0.22), 2.7)
    place(sfx, riser(1.5, 0.30), 2.5)
    place(sfx, reverse_swell(0.6, 0.18), 3.4)
    place(sfx, impact(1.0, 2.6, 49), C["impactReveal"], send=0.5)
    place(sfx, shimmer(0.9, 0.06), C["impactReveal"] + 0.05, send=0.7)
    place(sfx, riser(1.1, 0.26), 6.9)
    place(sfx, impact(0.55, 1.4, 55), C["drop"], send=0.3)
    # brand beats: camera whip + product pop
    for i, b in enumerate(C["brandBeats"]):
        place(sfx, whoosh(0.5, 400, 5000, gain=0.20, pan0=0.7 if i % 2 else -0.7, pan1=-0.7 if i % 2 else 0.7), b - 0.25)
        place(sfx, pop(260, 120, 0.12, 0.25), b + 0.06)
        place(sfx, pop(700, 1400, 0.07, 0.07), b + 0.08, send=0.4)
    # add-to-cart: rising notes D-minor pentatonic, one per brand
    asc = [nm("D5"), nm("F5"), nm("A5"), nm("C6"), nm("D6"), nm("F6")]
    for m, t_ in zip(asc, C["addToCart"]):
        place(sfx, chime([m], 0, 0.085, 0.25), t_ + 0.02, pan=0.2, send=0.35)
    # order: products drop into the cart
    for i, t_ in enumerate(C["cartAdds"]):
        place(sfx, whoosh(0.4, 900, 4000, gain=0.10, pan0=-0.5 if i % 2 else 0.5, pan1=0), t_ - 0.4)
        place(sfx, pop(380 + i * 60, 760 + i * 120, 0.06, 0.12), t_, send=0.3)
    place(sfx, whoosh(0.45, 300, 3500, gain=0.18), C["tapCart"])
    place(sfx, whoosh(0.45, 300, 3500, gain=0.18), C["chatOpen"])
    # chat bubbles: sent (rising), received (warmer two-tone)
    for k, (t_, m) in enumerate(zip(C["chatMessages"], T["copy"]["chat"])):
        if m["from"] == "me":
            place(sfx, pop(520, 980, 0.08, 0.16), t_, pan=0.25)
        else:
            place(sfx, chime([nm("C6"), nm("G6")], 0.07, 0.09, 0.3), t_, pan=-0.25, send=0.3)
    # dive into the screen -> end card
    d0, d1 = C["dive"]
    place(sfx, reverse_swell(d1 - d0 + 0.5, 0.32), d0 - 0.5)
    place(sfx, whoosh(d1 - d0 + 0.25, 200, 9000, gain=0.32, pan0=0, pan1=0, q=0.8), d0 - 0.1)
    place(sfx, impact(1.05, 3.6, 46), C["impactEnd"], send=0.65)
    l0, l1 = C["logoDraw"]
    place(sfx, shimmer(l1 - l0 + 0.6, 0.07), l0, send=0.8)
    place(sfx, chime([nm("D6"), nm("F#6"), nm("A6")], 0.09, 0.06, 0.8), 27.45, send=0.7)


def reverb(x, seconds=2.6, predelay=0.022):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n + int(predelay * SR), 2))
    for ch in range(2):
        nz = rs.standard_normal(n) * np.exp(-t / (seconds / 6.9))
        nz = filt(nz, "lowpass", 6500)
        ir[int(predelay * SR):, ch] = nz
    ir /= np.sqrt((ir ** 2).sum(0, keepdims=True))
    wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    return filt(wet, "highpass", 180)


def compress(x, thresh_db=-17, ratio=2.0, attack=0.01, release=0.15):
    lvl = np.sqrt(signal.sosfilt(sos("lowpass", 30), (x ** 2).mean(1)).clip(1e-12))
    db = 20 * np.log10(lvl)
    over = np.maximum(0, db - thresh_db)
    gr = -over * (1 - 1 / ratio)
    # smooth gain reduction (attack/release one-pole)
    g = np.zeros_like(gr)
    a_a, a_r = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    prev = 0.0
    for i in range(0, len(gr), 64):
        target = gr[i]
        coef = a_a if target < prev else a_r
        prev = coef ** 64 * prev + (1 - coef ** 64) * target
        g[i:i + 64] = prev
    return x * (10 ** (g / 20))[:, None]


def true_peak_limit(x, ceiling_db=-1.2):
    """Brick-wall on a 4x oversampled envelope (approximates true peak)."""
    up = signal.resample_poly(x, 4, 1, axis=0)
    peak = np.abs(up).max(1)
    peak = peak.reshape(-1, 4).max(1)[: len(x)]
    ceil = 10 ** (ceiling_db / 20)
    need = np.minimum(1.0, ceil / np.maximum(peak, 1e-9))
    # look-ahead smoothing: min-filter then release
    w = int(0.004 * SR)
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    need = minimum_filter1d(need, size=w * 2 + 1)
    need = uniform_filter1d(need, size=w)
    return x * need[:, None]


def main():
    build()
    wet = reverb(verb_send)
    mus = music + wet * 0.5
    fx = sfx + 0.0
    mix = mus * 0.9 + fx
    mix = filt(mix, "highpass", 28, order=4)  # no DC / sub rumble
    mix = compress(mix)
    # loudness: -14 LUFS integrated (Reels/TikTok normalise around here)
    meter = pyln.Meter(SR)
    loud = meter.integrated_loudness(mix)
    gain = 10 ** ((-14.0 - loud) / 20)
    mix *= gain
    mix = true_peak_limit(mix, -1.2)
    # clean edges: 10 ms fade in, natural tail, 0.35 s fade out to digital silence
    fi, fo = int(0.01 * SR), int(0.35 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    out = ROOT / "public" / "audio" / "soundtrack.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, mix, SR, subtype="PCM_24")
    stems = ROOT.parent / "output" / "audio"
    stems.mkdir(parents=True, exist_ok=True)
    sf.write(stems / "AFM_BRAND_music_stem.wav", (mus * 0.9 * gain).clip(-1, 1), SR, subtype="PCM_24")
    sf.write(stems / "AFM_BRAND_sfx_stem.wav", (fx * gain).clip(-1, 1), SR, subtype="PCM_24")
    print(f"master: {out}  loudness before norm {loud:.1f} LUFS -> -14, gain {20*np.log10(gain):+.1f} dB, "
          f"peak {20*np.log10(np.abs(mix).max()):.2f} dBFS, samples {len(mix)} ({len(mix)/SR:.3f}s)")


if __name__ == "__main__":
    main()
