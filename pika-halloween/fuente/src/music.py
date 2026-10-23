"""Fun (not scary) Halloween jingle, 128 BPM, 8 bars = 15.0 s, plus SFX synced to the video.

Usage: python3 music.py out.wav [--sfx main|winner] [--seconds 15]
"""
import sys
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
BPM = 128
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env_exp(n, decay, attack=0.004):
    t = np.arange(n) / SR
    a = np.minimum(1, t / attack) if attack > 0 else 1
    return a * np.exp(-t / decay)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


class Track:
    def __init__(self, seconds):
        self.buf = np.zeros(int(seconds * SR) + SR * 3)

    def add(self, t, sig, gain=1.0):
        i = int(round(t * SR))
        if i < 0:
            sig = sig[-i:]
            i = 0
        j = min(len(self.buf), i + len(sig))
        self.buf[i:j] += gain * sig[: j - i]


# ---------- instruments ----------
def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * env_exp(n, 0.16, 0.001)
    s += 0.25 * hp(rng.standard_normal(n), 3000) * env_exp(n, 0.004, 0.0005)
    return s


def clap():
    n = int(0.25 * SR)
    noise = bp(rng.standard_normal(n), 900, 2600)
    e = np.zeros(n)
    for k, off in enumerate([0, 0.011, 0.022]):
        i = int(off * SR)
        e[i:] += env_exp(n - i, 0.012 if k < 2 else 0.09, 0.0005)
    return noise * e * 0.9


def snap():
    n = int(0.12 * SR)
    return bp(rng.standard_normal(n), 1800, 4200) * env_exp(n, 0.018, 0.0005) * 1.4


def hat(open_=False):
    n = int((0.2 if open_ else 0.06) * SR)
    return hp(rng.standard_normal(n), 7000) * env_exp(n, 0.07 if open_ else 0.014, 0.0005) * 0.5


def pluck_bass(note, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(note)
    saw = 2 * ((t * f) % 1) - 1
    sq = np.sign(np.sin(2 * np.pi * f * t))
    s = 0.6 * saw + 0.4 * sq
    # filter sweep for a "pizzicato" pluck
    s = lp(s, 900) * 0.6 + lp(s, 300) * 0.6
    s += 0.5 * np.sin(2 * np.pi * f * t)
    return s * env_exp(n, 0.22, 0.003)


def music_box(note, dur=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(note)
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.003 * np.sin(2 * np.pi * 5.5 * t))) / SR
    s = (np.sin(ph) * env_exp(n, 0.45, 0.002)
         + 0.35 * np.sin(2 * np.pi * 2 * f * t) * env_exp(n, 0.18, 0.002)
         + 0.22 * np.sin(2 * np.pi * 3.01 * f * t) * env_exp(n, 0.08, 0.001)
         + 0.12 * np.sin(2 * np.pi * 5.4 * f * t) * env_exp(n, 0.03, 0.001))
    return s


def organ(notes, dur, decay=0.09):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for nt in notes:
        f = midi(nt)
        for h, a in [(1, 1), (2, 0.5), (3, 0.3), (4, 0.15), (6, 0.08)]:
            s += a * np.sin(2 * np.pi * f * h * t + 0.3 * h)
    e = np.minimum(1, t / 0.006) * np.exp(-t / decay)
    return s * e / len(notes)


def theremin(f0, f1, dur, vib=6.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    f = f * (1 + 0.025 * np.sin(2 * np.pi * vib * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return (np.sin(ph) + 0.15 * np.sin(2 * ph)) * e


# ---------- sfx ----------
def whoosh(dur=0.45, up=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    # state-variable band-pass with a swept cutoff
    low = band = 0.0
    q = 0.5
    for i in range(n):
        x = i / n
        fc = 300 + (4500 if up else 2500) * (x ** 1.5 if up else 1 - x)
        f = 2 * np.sin(np.pi * fc / SR)
        high = noise[i] - low - q * band
        band += f * high
        low += f * band
        out[i] = band
    e = np.sin(np.pi * t / dur) ** 2
    return out * e * 0.9


def pop(f0=380, f1=1100, dur=0.09):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.035, 0.001)


def boing(dur=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 160 + 260 * np.exp(-t / 0.12) * (1 + 0.5 * np.sin(2 * np.pi * 14 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.18, 0.002)


def sparkle(start_note=86, n_notes=6, step=0.045):
    out = np.zeros(int((n_notes * step + 0.8) * SR))
    for k, iv in enumerate([0, 4, 7, 12, 16, 19][:n_notes]):
        s = music_box(start_note + iv, 0.6) * 0.6
        i = int(k * step * SR)
        out[i:i + len(s)] += s
    return out


def crash(dur=1.6):
    n = int(dur * SR)
    return hp(rng.standard_normal(n), 5000) * env_exp(n, 0.5, 0.001) * 0.35


def reverb(x, seconds=1.4, mix=0.18):
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (seconds / 5))
    ir = lp(ir, 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = fftconvolve(x, ir)[: len(x)]
    return x * (1 - mix) + wet * mix * 1.6


# ---------- composition ----------
CHORDS = ["Dm", "Bb", "Gm", "A", "Dm", "Bb", "GmA", "Dm"]
VOICING = {"Dm": [62, 65, 69], "Bb": [62, 65, 70], "Gm": [62, 67, 70], "A": [61, 64, 69]}
BASS = [
    [38, 45, 50, 45], [34, 41, 46, 41], [43, 50, 46, 50], [33, 40, 45, 49],
    [38, 45, 50, 45], [34, 41, 46, 41], [43, 50, 45, 49], [38, None, None, None],
]
LEAD = [
    [74, None, 77, 74, 81, None, 77, None],
    [70, None, 74, 70, 77, None, 74, None],
    [79, None, 77, None, 74, None, 70, 74],
    [73, None, 76, None, 79, 77, 76, 73],
    [74, None, 77, 74, 81, None, 77, None],
    [70, None, 74, 70, 77, None, 82, None],
    [79, 77, 74, 70, 73, 76, 79, 81],
    [86, None, None, None, None, None, None, None],
]


def compose(seconds, bars=8, end_hit=True, order=None):
    order = order or list(range(bars))
    drums, bass, lead, keys = Track(seconds), Track(seconds), Track(seconds), Track(seconds)
    for b in range(bars):
        t0 = b * BAR
        last = end_hit and b == bars - 1
        for q in range(4):
            tq = t0 + q * BEAT
            # bass
            nt = BASS[order[b]][q]
            if nt is not None and not last:
                bass.add(tq, pluck_bass(nt, BEAT * 0.95))
            # drums
            if last:
                continue
            if b == 0:
                if q in (0, 2):
                    drums.add(tq, kick(), 0.9)
                if q in (1, 3):
                    drums.add(tq, snap(), 0.8)
            else:
                drums.add(tq, kick(), 1.0)
                if q in (1, 3):
                    drums.add(tq, clap(), 0.75)
                    drums.add(tq, snap(), 0.35)
                drums.add(tq + BEAT / 2, hat(open_=(q == 3)), 0.9)
                drums.add(tq, hat(), 0.35)
            # organ stabs on the offbeats
            ch = CHORDS[order[b]]
            if ch == "GmA":
                ch = "Gm" if q < 2 else "A"
            keys.add(tq + BEAT / 2, organ(VOICING[ch], 0.16), 0.33 if b else 0.22)
        for e in range(8):
            nt = LEAD[order[b]][e]
            if nt is not None:
                lead.add(t0 + e * BEAT / 2, music_box(nt), 0.42 if not last else 0.6)
        if last:
            bass.add(t0, pluck_bass(38, 1.2) * 1.2 + pluck_bass(26 + 12, 1.2) * 0.4)
            keys.add(t0, organ([62, 65, 69, 74], 1.8, decay=0.55), 0.5)
            drums.add(t0, kick(), 1.1)
            drums.add(t0, crash(), 1.0)
    mix = drums.buf * 0.55 + bass.buf * 0.6 + reverb(lead.buf, mix=0.25) * 0.9 + reverb(keys.buf, mix=0.2) * 1.6
    return mix


def sfx_main(seconds):
    s = Track(seconds)
    s.add(0.0, boing(), 0.35)                    # Piku jumps in
    s.add(0.15, theremin(500, 900, 1.6), 0.10)   # friendly ghost "woo"
    s.add(0.94, pop(300, 900, 0.1), 0.5)         # title stamp
    s.add(2.34, pop(500, 1300), 0.4)             # date chip
    s.add(BAR * 2 - 0.42, whoosh(0.45), 0.45)    # -> game scene
    s.add(BAR * 2 + BEAT * 0.5, pop(350, 1000), 0.4)   # card pop
    s.add(BAR * 3 + BEAT * 0.5, pop(500, 1300), 0.35)  # "pausá" pill
    s.add(BAR * 4 - 0.42, whoosh(0.45), 0.45)    # -> steps
    for k in range(3):
        s.add(BAR * 4 + BEAT * (1 + 2 * k), pop(450 + 120 * k, 1200 + 200 * k), 0.45)
    s.add(BAR * 6 - 0.42, whoosh(0.45), 0.45)    # -> end card
    s.add(BAR * 6, sparkle(), 0.35)
    return s.buf


def sfx_winner(seconds):
    s = Track(seconds)
    s.add(0.0, boing(), 0.35)                       # Piku jumps in
    s.add(BEAT, pop(300, 900, 0.1), 0.5)            # ¡GANASTE! stamp
    s.add(BEAT, sparkle(), 0.35)
    s.add(2 * BEAT, whoosh(0.45, up=False), 0.35)   # box falling
    s.add(3 * BEAT, pop(250, 700, 0.12), 0.55)      # catch!
    s.add(3 * BEAT, sparkle(81), 0.3)
    s.add(BAR, pop(450, 1200), 0.35)
    s.add(BAR + 2 * BEAT, pop(500, 1300), 0.35)
    s.add(2 * BAR, pop(550, 1400), 0.35)
    return s.buf


def main():
    out = sys.argv[1]
    kind = "main"
    seconds = 15.0
    if "--sfx" in sys.argv:
        kind = sys.argv[sys.argv.index("--sfx") + 1]
    if "--seconds" in sys.argv:
        seconds = float(sys.argv[sys.argv.index("--seconds") + 1])
    bars = int(round(seconds / BAR))
    mix = compose(seconds, bars=bars, order=[0, 1, 6, 7] if kind == "winner" else None)
    fx = sfx_main(seconds) if kind == "main" else sfx_winner(seconds)
    n = int(seconds * SR)
    mix = mix[:n] + fx[:n]
    # gentle glue + limiter
    mix = mix / np.max(np.abs(mix))
    mix = np.tanh(mix * 1.3) / np.tanh(1.3)
    fade = int(0.35 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade) ** 2
    mix[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    mix = mix / np.max(np.abs(mix)) * 0.89
    stereo = np.stack([mix, mix], axis=1)
    # tiny stereo width: delay right channel's lead-ish highs slightly
    stereo[:, 1] = np.roll(mix, int(0.0007 * SR))
    wavfile.write(out, SR, (stereo * 32767).astype(np.int16))
    print("wrote", out, seconds, "s")


if __name__ == "__main__":
    main()
