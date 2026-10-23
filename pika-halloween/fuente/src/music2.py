"""Halloween jingle with real instrument samples (FluidSynth + FluidR3 GM soundfont).

Fun, not scary: xylophone + pizzicato strings + tuba, a sneaky bassoon section, celesta/glockenspiel
sparkles, acoustic drum kit, orchestra hits and a church-organ "ta-da" ending in D major.
128 BPM, 4 beats per bar; the ad is 8 bars (15.0 s), the winner clip 4 bars (7.5 s).

Usage: python3 music2.py out.wav [--kind main|winner]
"""
import os
import subprocess
import sys
import tempfile
import numpy as np
import mido
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

import music as synth  # synthesized whooshes / ghost "woo" layered on top

SR = 48000
BPM = 128
BEAT = 60 / BPM
BAR = 4 * BEAT
TPB = 480
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
rng = np.random.default_rng(11)

# General MIDI programs (0-based)
XYLO, CELESTA, GLOCK, PIZZ, HARPSI, TUBA, BASSOON, TIMP, ORCH_HIT, CH_ORGAN, WHISTLE = 13, 8, 9, 45, 6, 58, 70, 47, 55, 19, 78
# GM percussion keys
KICK, SNARE, CLAP, HH_C, HH_O, CRASH, TAMB, WOOD_HI, WOOD_LO, TRI = 36, 38, 39, 42, 46, 49, 54, 76, 77, 81

CHORDS = ["Dm", "Bb", "Gm", "A", "Dm", "Bb", "GmA", "D"]
VOICING = {"Dm": [62, 65, 69], "Bb": [62, 65, 70], "Gm": [62, 67, 70], "A": [61, 64, 69], "D": [62, 66, 69]}
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


class Stem:
    """Collects MIDI events (absolute ticks) for one stem and renders it with FluidSynth."""

    def __init__(self, name):
        self.name = name
        self.ev = []  # (tick, order, mido.Message)
        self.programs = {}

    def program(self, ch, prog, pan=64, vol=110):
        self.programs[ch] = (prog, pan, vol)

    def note(self, beat, dur, pitch, vel, ch, jitter=True):
        t = int(round(beat * TPB)) + (int(rng.integers(-6, 7)) if jitter and ch != 9 else 0)
        t = max(0, t)
        v = int(np.clip(vel + (rng.integers(-6, 7) if jitter else 0), 1, 127))
        self.ev.append((t, 1, mido.Message("note_on", channel=ch, note=pitch, velocity=v)))
        self.ev.append((t + max(1, int(dur * TPB)), 0, mido.Message("note_off", channel=ch, note=pitch, velocity=0)))

    def bend(self, beat, value, ch):
        self.ev.append((max(0, int(round(beat * TPB))), 0, mido.Message("pitchwheel", channel=ch, pitch=int(np.clip(value, -8192, 8191)))))

    def cc(self, beat, ctrl, value, ch):
        self.ev.append((max(0, int(round(beat * TPB))), 0, mido.Message("control_change", channel=ch, control=ctrl, value=int(value))))

    def render(self, seconds, workdir):
        mid = mido.MidiFile(type=1, ticks_per_beat=TPB)
        meta = mido.MidiTrack()
        meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
        mid.tracks.append(meta)
        tr = mido.MidiTrack()
        for ch, (prog, pan, vol) in self.programs.items():
            if ch != 9:
                tr.append(mido.Message("program_change", channel=ch, program=prog, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=10, value=pan, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=7, value=vol, time=0))
            # pitch-bend range +-12 semitones (for the slide whistle)
            for c, v in ((101, 0), (100, 0), (6, 12), (38, 0)):
                tr.append(mido.Message("control_change", channel=ch, control=c, value=v, time=0))
        last = 0
        for t, _, msg in sorted(self.ev, key=lambda e: (e[0], e[1])):
            tr.append(msg.copy(time=t - last))
            last = t
        mid.tracks.append(tr)
        mpath = os.path.join(workdir, f"{self.name}.mid")
        wpath = os.path.join(workdir, f"{self.name}.wav")
        mid.save(mpath)
        subprocess.run(["fluidsynth", "-ni", "-q", "-R", "0", "-C", "0", "-g", "0.5", "-r", str(SR),
                        "-F", wpath, SF2, mpath], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sr, x = wavfile.read(wpath)
        x = x.astype(np.float32) / 32768.0
        n = int(seconds * SR)
        out = np.zeros((n, 2), np.float32)
        out[: min(n, len(x))] = x[:n]
        return out


# ---------------- arrangement ----------------
def arrange(order, sfx_cues):
    """order: which of the 8 composed bars to play; sfx_cues: dict of named cues -> beat positions."""
    drums, bass, melody, harmony, fx = (Stem(n) for n in ("drums", "bass", "melody", "harmony", "fx"))
    drums.program(9, 0, 64, 112)
    bass.program(0, TUBA, 64, 118)
    melody.program(0, XYLO, 64, 120)
    melody.program(1, CELESTA, 84, 100)
    melody.program(2, BASSOON, 76, 112)
    harmony.program(0, PIZZ, 44, 104)
    harmony.program(1, HARPSI, 88, 84)
    fx.program(0, ORCH_HIT, 64, 104)
    fx.program(1, CH_ORGAN, 64, 100)
    fx.program(2, GLOCK, 40, 100)
    fx.program(3, TIMP, 64, 120)
    fx.program(4, WHISTLE, 70, 96)

    nb = len(order)
    for b, src in enumerate(order):
        b0 = b * 4
        final = src == 7
        section = "sneaky" if src in (2, 3) else "main"
        # ---- drums ----
        if not final:
            for q in range(4):
                if b > 0 or q in (0, 2):
                    drums.note(b0 + q, 0.25, KICK, 112 if q == 0 else 100, 9)
                if q in (1, 3):
                    drums.note(b0 + q, 0.25, CLAP, 92, 9)
                    if section == "sneaky":
                        drums.note(b0 + q, 0.2, SNARE, 50, 9)
                if b > 0 or section == "sneaky":
                    drums.note(b0 + q + 0.5, 0.2, HH_O if q == 3 else HH_C, 70 if q == 3 else 62, 9)
                    drums.note(b0 + q, 0.2, HH_C, 38, 9)
                if src in (4, 5):
                    for s16 in (0.25, 0.75):
                        drums.note(b0 + q + s16, 0.1, TAMB, 46, 9)
            if src == 6:  # build: snare roll into the final bar
                for k in range(16):
                    drums.note(b0 + 2 + k / 8, 0.1, SNARE, 40 + k * 5, 9)
        if b0 % 8 == 0 and b > 0 or final:
            drums.note(b0, 1.5, CRASH, 100 if final else 80, 9)
        # ---- bass (tuba, staccato) ----
        for q in range(4):
            nt = BASS[src][q]
            if nt is not None:
                bass.note(b0 + q, 0.42, nt, 100 if q in (0, 2) else 86, 0)
        if final:
            bass.note(b0, 3.0, 38, 112, 0)
            bass.note(b0, 3.0, 26 + 12, 90, 0)
        # ---- melody ----
        for e, nt in enumerate(LEAD[src]):
            if nt is None:
                continue
            beat = b0 + e * 0.5
            if section == "sneaky":
                melody.note(beat, 0.32, nt - 12, 96, 2)        # sneaky bassoon
                melody.note(beat, 0.25, nt, 58, 0)             # soft xylophone echo
            else:
                melody.note(beat, 0.45 if not final else 2.5, nt, 104, 0)
                if src >= 4:
                    melody.note(beat, 0.45 if not final else 2.5, nt + 12, 60, 1)  # celesta sparkle
        # ---- harmony ----
        ch = CHORDS[src]
        for q in range(4):
            c = ch if ch != "GmA" else ("Gm" if q < 2 else "A")
            if not final:
                for p in VOICING[c]:
                    harmony.note(b0 + q + 0.5, 0.2, p, 78, 0)
        if section == "sneaky":
            for k in range(16):
                c = VOICING[ch]
                arp = [c[0], c[1], c[2], c[0] + 12]
                harmony.note(b0 + k * 0.25, 0.22, arp[k % 4] + (12 if k % 8 >= 4 else 0), 54, 1)
        if final:
            for p in [50, 54, 57, 62, 66, 69, 74]:
                fx.note(b0, 3.2, p, 92, 1)          # church organ D major "ta-da"
            for p in (62, 69, 74):
                fx.note(b0, 0.5, p, 112, 0)         # orchestra hit
            fx.note(b0, 1.5, 38, 120, 3)            # timpani hit
        if src == 6:
            for k in range(16):                     # timpani roll crescendo
                fx.note(b0 + 2 + k / 8, 0.12, 38, 50 + k * 4, 3)

    # ---- cues ----
    for beat in sfx_cues.get("stamp", []):
        for p in (62, 69, 74):
            fx.note(beat, 0.5, p, 104, 0)
    for beat in sfx_cues.get("sparkle", []):
        for k, p in enumerate([86, 90, 93, 98, 102, 105]):
            fx.note(beat + k * 0.09, 0.6, p, 84 - k * 4, 2)
    for beat, hi in sfx_cues.get("wood", []):
        drums.note(beat, 0.2, WOOD_HI if hi else WOOD_LO, 108, 9, jitter=False)
    for beat, pitch in sfx_cues.get("ping", []):
        fx.note(beat, 0.8, pitch, 92, 2)
    for beat, dur, up in sfx_cues.get("slide", []):
        # slide whistle: one long note with a pitch-bend sweep
        fx.bend(beat - 0.01, -8192 if up else 8191, 4)
        fx.note(beat, dur, 84, 100, 4, jitter=False)
        steps = 24
        for k in range(steps + 1):
            u = k / steps
            v = -8192 + 16383 * u if up else 8191 - 16383 * u
            fx.bend(beat + dur * u, v, 4)
        fx.bend(beat + dur + 0.05, 0, 4)
    return [drums, bass, melody, harmony, fx]


# ---------------- mixing ----------------
def hp(x, f):
    return sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), x, axis=0)


def lp(x, f):
    return sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), x, axis=0)


def reverb(x, seconds=1.6, mix=0.2, predelay=0.012):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for c in range(2):
        ir = np.random.default_rng(100 + c).standard_normal(n) * np.exp(-t / (seconds / 6.5))
        ir = lp(hp(ir, 200), 6500)
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, c] = fftconvolve(x[:, c], ir)[: len(x)]
    return x * (1 - mix) + out * mix * 1.4


def compress(x, thresh_db=-16, ratio=2.5, attack=0.008, release=0.14, makeup_db=2.0):
    level = np.max(np.abs(x), axis=1)
    env = np.zeros_like(level)
    a_att, a_rel = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    e = 0.0
    for i, v in enumerate(level):
        a = a_att if v > e else a_rel
        e = a * e + (1 - a) * v
        env[i] = e
    db = 20 * np.log10(np.maximum(env, 1e-6))
    gain_db = np.minimum(0, (thresh_db - db) * (1 - 1 / ratio)) + makeup_db
    return x * (10 ** (gain_db / 20))[:, None]


def limiter(x, ceiling=0.89, lookahead=0.004, release=0.06):
    n_la = int(lookahead * SR)
    peak = np.max(np.abs(x), axis=1)
    # running max over the look-ahead window
    pk = np.copy(peak)
    for k in range(1, n_la):
        pk[:-k] = np.maximum(pk[:-k], peak[k:])
    g = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    a = np.exp(-1 / (release * SR))
    out_g = np.empty_like(g)
    cur = 1.0
    for i, v in enumerate(g):
        cur = v if v < cur else a * cur + (1 - a) * v
        out_g[i] = cur
    return x * out_g[:, None]


def mono_to_stereo(m, pan=0.0):
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([m * l, m * r], axis=1).astype(np.float32)


def build(kind):
    if kind == "main":
        order = list(range(8))
        cues = {
            "slide": [(0.0, 0.85, True)],
            "stamp": [2.0, 24.5],
            "sparkle": [24.0],
            "wood": [(5.0, True), (8.5, False), (12.5, True), (17.0, True), (19.0, True), (21.0, True),
                     (25.5, False), (26.5, True), (27.5, False)],
            "ping": [(5.0, 93), (17.0, 86), (19.0, 89), (21.0, 93), (28.0, 98)],
        }
        whooshes = [2 * BAR - 0.42, 4 * BAR - 0.42, 6 * BAR - 0.42]
    else:
        order = [0, 1, 6, 7]
        cues = {
            "slide": [(0.0, 0.85, True), (2.0, 0.95, False)],
            "stamp": [1.0],
            "sparkle": [1.0, 3.0],
            "wood": [(3.0, False), (4.0, True), (6.0, True), (8.0, False)],
            "ping": [(3.0, 98), (4.0, 93)],
        }
        whooshes = [2.0 * BEAT]
    seconds = len(order) * BAR
    stems = arrange(order, cues)
    with tempfile.TemporaryDirectory() as td:
        audio = {s.name: s.render(seconds, td) for s in stems}
    gains = {"drums": 1.0, "bass": 0.7, "melody": 2.0, "harmony": 0.6, "fx": 0.7}
    wet = {"drums": 0.08, "bass": 0.05, "melody": 0.22, "harmony": 0.2, "fx": 0.25}
    mix = np.zeros((int(seconds * SR), 2), np.float32)
    for name, x in audio.items():
        mix += reverb(x, mix=wet[name]) * gains[name]
    # synthesized layers: whooshes and a friendly ghost "woo" at the start
    n = len(mix)
    sfx = np.zeros(n, np.float32)

    def add(t, sig, g):
        # music.py synthesizes at 44.1 kHz
        sig = np.interp(np.arange(int(len(sig) * SR / synth.SR)) * synth.SR / SR, np.arange(len(sig)), sig)
        i = int(t * SR)
        j = min(n, i + len(sig))
        if i < n:
            sfx[i:j] += g * sig[: j - i]

    for t in whooshes:
        add(t, synth.whoosh(0.45, up=kind == "main"), 0.22)
    if kind == "main":
        add(0.25, synth.theremin(520, 880, 1.4), 0.05)
    mix += reverb(mono_to_stereo(sfx), mix=0.15)
    mix = hp(mix, 35)
    mix = compress(mix)
    # 6 ms fade-in, gentle fade-out over the last 0.4 s
    mix[: int(0.006 * SR)] *= np.linspace(0, 1, int(0.006 * SR))[:, None]
    fo = int(0.4 * SR)
    mix[-fo:] *= (np.linspace(1, 0, fo) ** 2)[:, None]
    return mix / np.max(np.abs(mix)) * 0.7, seconds


def main():
    out = sys.argv[1]
    kind = sys.argv[sys.argv.index("--kind") + 1] if "--kind" in sys.argv else "main"
    mix, seconds = build(kind)
    # loudness to -14 LUFS (BS.1770), then a look-ahead limiter keeps peaks under -1.2 dBFS
    import pyloudnorm
    meter = pyloudnorm.Meter(SR)
    for _ in range(3):
        mix = mix * 10 ** ((-14.0 - meter.integrated_loudness(mix)) / 20)
        mix = limiter(mix, ceiling=0.87)
    wavfile.write(out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print("wrote", out, f"{seconds:.3f}s")


if __name__ == "__main__":
    main()
