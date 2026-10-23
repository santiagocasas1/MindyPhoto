"""PIKA Halloween "Dulce o Piku" — 15 s vertical ad (1080x1920, 30 fps).

Usage:
  python3 render_main.py out.mp4 music.wav       # full render
  python3 render_main.py --stills 0.5,2,5 outdir # preview frames
"""
import math
import os
import subprocess
import sys
import numpy as np
from PIL import Image

from gfx import *  # noqa: F401,F403

DUR = 15.0
S2, S3, S4 = 2 * BAR, 4 * BAR, 6 * BAR   # scene starts: 3.75 / 7.5 / 11.25 s
rng = np.random.default_rng(31)

# ---------------- assets ----------------
store = Image.open(os.path.join(ROOT, "work", "store.png")).convert("RGB")
PIKU = load("piku.png")
LOGO = load("logo.png")
TITLE = load("title.png")
BAT = load("bat.png")
GHOST = ghost(240)
BG = background(store)
BG_DARK = background(store, darken=0.5)

CARD_SIZE = 880
CARD = rounded_card(store, CARD_SIZE)
CARD_CY = 965
CARD_PAD = 60 + 12 + 5  # shadow pad + border + outline (see rounded_card)

DATE_CHIP = pill(styled_text(["SÁBADO 31/10"], 58, shadow=False), padx=40, pady=14)
HEAD2 = styled_text(["¿Encontrás las", ("3 cajas de Pepero?", YELLOW)], 92, max_width=1000)
PAUSE = pill(styled_text(["Pausá y buscalas"], 54, shadow=False), padx=40, pady=14, extra=emoji("👀", 62))
HOWTO = styled_text(["¿CÓMO PARTICIPAR?"], 104, max_width=990)
STEPS = [
    ["Buscá las 3 cajas", "de Pepero en la foto."],
    ["Marcalas y mandanos", "la imagen por DM."],
    ["Si acertás, te confirmamos", "tu premio y cómo retirarlo."],
]
STEP_TXT = [styled_text(s, 58, align="left", shadow=False, max_width=720, ext_color=ORANGE_D) for s in STEPS]
BADGES = [number_badge(i + 1, 118) for i in range(3)]
PANEL = panel(930, 200)
WIN = pill(styled_text(["¡GANÁ UNA GOLOSINA!"], 74, shadow=False), padx=44, pady=18)
DATE_BIG = styled_text(["Sábado 31/10"], 104)
RETIRA = styled_text(["Retirá tu premio en Pika"], 62, ext_color=ORANGE_D, max_width=900)
CONDS = [plain_text("Participá con un adulto · Un premio por chico", 40, bold=True, max_width=880),
         plain_text("¡Cupos limitados!", 40, bold=True, fill=YELLOW)]
HANDLE = pill(styled_text(["@pika.kstore"], 60, shadow=False), padx=40, pady=12, color=PURPLE)

CANDY_COLORS = [(245, 122, 33), (150, 92, 230), (120, 210, 120), (255, 120, 170), (255, 200, 70)]
CANDIES = [candy(c, 46) for c in CANDY_COLORS]
STARS = [star(34), star(26, (255, 240, 200))]
DOTS = [glow_dot(s, c) for s in (40, 70, 110) for c in ((255, 170, 70), (255, 214, 120), (190, 120, 255))]

PARTICLES = [dict(x=rng.uniform(0, W), y0=rng.uniform(0, H), sp=rng.uniform(40, 120), ph=rng.uniform(0, 6.28),
                  amp=rng.uniform(10, 40), spr=rng.integers(len(DOTS)), a=rng.uniform(0.18, 0.45))
             for _ in range(26)]
CONFETTI = [dict(x=rng.uniform(40, W - 40), delay=rng.uniform(0, 1.6), sp=rng.uniform(380, 650),
                 rot0=rng.uniform(0, 360), vr=rng.uniform(-260, 260), sway=rng.uniform(10, 50),
                 kind=rng.integers(len(CANDIES) + len(STARS)), sc=rng.uniform(0.8, 1.35))
            for _ in range(34)]


# ---------------- reusable bits ----------------
def particles(c, t):
    for p in PARTICLES:
        y = (p["y0"] - p["sp"] * t) % (H + 200) - 100
        x = p["x"] + p["amp"] * math.sin(p["ph"] + t * 1.3)
        tw = 0.75 + 0.25 * math.sin(p["ph"] * 3 + t * 4)
        place(c, DOTS[p["spr"]], x, y, alpha=p["a"] * tw)


def bat(c, t, t0, t1, y, direction=1, scale=1.4, wobble=60):
    if not (t0 <= t <= t1):
        return
    u = (t - t0) / (t1 - t0)
    x = -140 + (W + 280) * u if direction > 0 else W + 140 - (W + 280) * u
    yy = y + wobble * math.sin(u * 2 * math.pi * 1.5)
    flap = 0.55 + 0.45 * abs(math.sin(t * 2 * math.pi * 3.2))
    spr = BAT if direction > 0 else BAT.transpose(Image.FLIP_LEFT_RIGHT)
    rot = -8 * math.cos(u * 2 * math.pi * 1.5) * direction
    place(c, spr, x, yy, scale=scale, sy=flap, rot=rot)


def piku_dance(t, amp=26, sway=4.0):
    """y offset (up is negative), squash/stretch and rotation, bouncing on every beat."""
    ph = beat_phase(t)
    hop = -amp * math.sin(math.pi * ph)
    squash = max(0.0, 1 - ph / 0.16) if ph < 0.16 else 0.0
    sx = 1 + 0.05 * squash - 0.02 * math.sin(math.pi * ph)
    sy = 1 - 0.07 * squash + 0.03 * math.sin(math.pi * ph)
    rot = sway * math.sin(2 * math.pi * t / (2 * BEAT))
    return hop, sx, sy, rot


def stamp(t, t0, dur=0.28, start=2.0):
    """Scale for a 'stamp' entrance: big -> 1 with a bounce."""
    if t < t0:
        return 0.0, 0.0
    p = prog(t, t0, dur)
    s = start + (1 - start) * ease_out_back(p, 2.5)
    return s, min(1.0, (t - t0) / 0.07)


def bar_pulse(t, start, amount=0.035):
    """Small pulse on beat 1 of every bar after `start`."""
    if t < start:
        return 1.0
    ph = ((t - start) / BAR) % 1.0
    return 1 + amount * max(0.0, 1 - ph * BAR / 0.25)


# ---------------- scenes ----------------
def scene1(c, t):
    out = pop_out(t, S2 - 0.22, 0.22) if t > S2 - 0.22 else 1.0
    # friendly ghost peeking from the left
    if 1.6 < t:
        g = ease_out_back(prog(t, 1.6, 0.5))
        gx = -160 + 290 * g - (300 * (1 - out))
        place(c, GHOST, gx, 1180 + 18 * math.sin(t * 3.2), scale=0.85, rot=12 + 5 * math.sin(t * 2.5))
    bat(c, t, 0.5, 2.9, 780, 1, 1.35)
    bat(c, t, 1.3, 3.7, 300, -1, 1.1, 40)
    # Piku jumps in, then dances
    feet = 1600
    if t < 0.45:
        p = ease_out_back(prog(t, 0.0, 0.45), 1.4)
        y = 2500 + (feet - 2500) * p
        place(c, PIKU, 540, y, scale=1.3, rot=-14 * (1 - p), anchor=(0.5, 1.0))
    else:
        hop, sx, sy, rot = piku_dance(t)
        land = max(0.0, 1 - (t - 0.45) / 0.18)
        sx += 0.10 * land
        sy -= 0.14 * land
        s = 1.3 * (0.4 + 0.6 * out)
        place(c, PIKU, 540, feet + hop + 500 * (1 - out), scale=s, sx=sx, sy=sy, rot=rot, anchor=(0.5, 1.0))
    # logo drops in
    if t > 0.12:
        p = ease_out_back(prog(t, 0.12, 0.45), 2.0)
        y = -150 + (330 + 150) * p - 400 * (1 - out)
        place(c, LOGO, 540, y + 6 * math.sin(t * 2.4), scale=1.12 * bar_pulse(t, BAR))
    # title stamp on beat 2
    s, a = stamp(t, 2 * BEAT)
    if s:
        place(c, TITLE, 540, 545, scale=0.93 * s * bar_pulse(t, BAR) * out, rot=-2, alpha=a)
    # date chip
    s = pop_in(t, 5 * BEAT, 0.35)
    if s:
        place(c, DATE_CHIP, 540, 690, scale=s * out, rot=3 + 2 * math.sin(t * 3))


def magnifier(c, t, card_scale):
    """A magnifying glass wandering over the photo (keeps away from the band where the Pepero are)."""
    t0, t1 = S2 + 0.9, S3 - 0.35
    if not (t0 < t < t1):
        return
    u = (t - t0) / (t1 - t0)
    # waypoints in card-pixel coordinates (0..CARD_SIZE)
    pts = [(-120, 160), (230, 150), (560, 170), (330, 200), (310, 720), (600, 730), (1000, 740)]
    seg = u * (len(pts) - 1)
    i = min(int(seg), len(pts) - 2)
    f = ease_in_out(seg - i)
    px = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
    py = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
    cx = 540 + (px - CARD_SIZE / 2) * card_scale
    cy = CARD_CY + (py - CARD_SIZE / 2) * card_scale
    r = 92
    mag = 1.7
    # lens content
    k = store.width / CARD_SIZE
    sx, sy = px * k, py * k
    half = r / mag * k / card_scale
    crop = store.crop((int(sx - half), int(sy - half), int(sx + half), int(sy + half))).resize((2 * r, 2 * r), Image.BICUBIC)
    lens = crop.convert("RGBA")
    m = Image.new("L", (8 * r, 8 * r), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 8 * r, 8 * r), fill=255)
    lens.putalpha(m.resize((2 * r, 2 * r), Image.LANCZOS))
    frame = Image.new("RGBA", (2 * r + 200, 2 * r + 200), (0, 0, 0, 0))
    big = Image.new("RGBA", (frame.width * 3, frame.height * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    o = 100
    S = lambda *v: tuple(int(a * 3) for a in v)
    # handle
    d.line(S(o + r * 1.6, o + r * 1.6, o + r * 2.45, o + r * 2.45), fill=DARK + (255,), width=3 * 36)
    d.ellipse(S(o + r * 2.45 - 18, o + r * 2.45 - 18, o + r * 2.45 + 18, o + r * 2.45 + 18), fill=DARK + (255,))
    d.line(S(o + r * 1.65, o + r * 1.65, o + r * 2.42, o + r * 2.42), fill=ORANGE + (255,), width=3 * 24)
    d.ellipse(S(o + r * 2.42 - 12, o + r * 2.42 - 12, o + r * 2.42 + 12, o + r * 2.42 + 12), fill=ORANGE + (255,))
    frame_ring = big.resize(frame.size, Image.LANCZOS)
    frame.alpha_composite(frame_ring)
    frame.alpha_composite(lens, (o, o))
    ring = Image.new("RGBA", (frame.width * 3, frame.height * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(ring)
    d.ellipse(S(o - 18, o - 18, o + 2 * r + 18, o + 2 * r + 18), outline=DARK + (255,), width=3 * 24)
    d.ellipse(S(o - 13, o - 13, o + 2 * r + 13, o + 2 * r + 13), outline=CREAM + (255,), width=3 * 15)
    d.arc(S(o + 20, o + 20, o + 2 * r - 20, o + 2 * r - 20), 200, 250, fill=(255, 255, 255, 170), width=3 * 8)
    frame.alpha_composite(ring.resize(frame.size, Image.LANCZOS))
    a = min(1.0, (t - t0) / 0.15, (t1 - t) / 0.15)
    place(c, frame, cx + 0, cy + 0, alpha=a, anchor=((o + r) / frame.width, (o + r) / frame.height))


def scene2(c, t):
    out = pop_out(t, S3 - 0.22, 0.22) if t > S3 - 0.22 else 1.0
    s = pop_in(t, S2, 0.4)
    if s:
        place(c, HEAD2, 540, 300 - 60 * (1 - s), scale=(0.6 + 0.4 * s) * out, alpha=min(1, s * 1.5))
    s = pop_in(t, S2 + BEAT * 0.5, 0.5)
    card_scale = 1.0
    if s:
        card_scale = s * out * (1 + 0.015 * (t - S2) / BAR)
        place(c, CARD, 540, CARD_CY, scale=card_scale, rot=6 * (1 - min(1, s)))
        magnifier(c, t, card_scale)
    s = pop_in(t, S2 + BAR + BEAT * 0.5, 0.35)
    if s:
        bob = 1 + 0.04 * max(0.0, 1 - beat_phase(t) / 0.2)
        place(c, PAUSE, 540, 1500, scale=s * out * bob, rot=-2)


def scene3(c, t):
    out = pop_out(t, S4 - 0.22, 0.22) if t > S4 - 0.22 else 1.0
    s, a = stamp(t, S3, 0.3, 1.8)
    if s:
        place(c, HOWTO, 540, 330, scale=s * out * bar_pulse(t, S3 + BAR), alpha=a)
    for i in range(3):
        t0 = S3 + BEAT * (1 + 2 * i)
        if t < t0:
            continue
        p = ease_out_back(prog(t, t0, 0.42), 1.8)
        y = 575 + i * 240
        dx = 700 * (1 - p) + 900 * (1 - out)
        place(c, PANEL, 540 + 25 + dx, y, alpha=min(1, p * 2))
        place(c, STEP_TXT[i], 238 + dx, y, anchor=(0, 0.5))
        bs = pop_in(t, t0 + 0.08, 0.35)
        bob = 1 + 0.06 * max(0.0, 1 - beat_phase(t) / 0.2) if t > t0 + 0.5 else 1
        place(c, BADGES[i], 130 + dx * 1.2, y, scale=bs * bob, rot=-8 + 8 * bs)
    # Piku peeks from the bottom
    if t > S3 + 0.2:
        p = ease_out_back(prog(t, S3 + 0.2, 0.5), 1.6)
        hop, sx, sy, rot = piku_dance(t, amp=18, sway=6)
        y = 2400 + (1790 - 2400) * p + 500 * (1 - out)
        place(c, PIKU, 540, y + hop, scale=0.92, sx=sx, sy=sy, rot=rot, anchor=(0.5, 1.0))


def scene4(c, t):
    # candy rain
    for q in CONFETTI:
        tt = t - S4 - q["delay"] * 0.6
        if tt < 0:
            continue
        y = -60 + q["sp"] * tt
        if y > H + 80:
            continue
        x = q["x"] + q["sway"] * math.sin(tt * 3 + q["rot0"])
        k = q["kind"]
        spr = CANDIES[k] if k < len(CANDIES) else STARS[k - len(CANDIES)]
        place(c, spr, x, y, scale=q["sc"], rot=q["rot0"] + q["vr"] * tt)
    # ghost on the right
    g = ease_out_back(prog(t, S4 + 0.6, 0.5))
    if g:
        place(c, GHOST, W + 150 - 300 * g, 760 + 16 * math.sin(t * 3), scale=0.62, rot=-12 + 4 * math.sin(t * 2.2))
    bat(c, t, S4 + 0.3, DUR, 620, -1, 1.1, 50)
    final = 7 * BAR
    hit = 1 + 0.07 * max(0.0, 1 - (t - final) / 0.3) if t >= final else 1.0
    # Piku jumps in big and dances
    feet = 1110
    if t > S4:
        p = ease_out_back(prog(t, S4, 0.45), 1.5)
        hop, sx, sy, rot = piku_dance(t, amp=34 if t < final else 46, sway=5)
        y = 2400 + (feet - 2400) * p
        place(c, PIKU, 540, y + hop, scale=0.98 * hit, sx=sx, sy=sy, rot=rot, anchor=(0.5, 1.0))
    s = pop_in(t, S4 + 0.05, 0.45)
    if s:
        place(c, LOGO, 540, 250 - 200 * (1 - s), scale=0.95 * hit)
    s, a = stamp(t, S4 + BEAT * 0.5, 0.3, 1.9)
    if s:
        place(c, WIN, 540, 440, scale=s * hit * bar_pulse(t, S4 + BAR, 0.04), rot=-2, alpha=a)
    s = pop_in(t, S4 + BEAT * 1.5, 0.4)
    if s:
        place(c, DATE_BIG, 540, 1195, scale=s * hit)
    s = pop_in(t, S4 + BEAT * 2.5, 0.4)
    if s:
        place(c, RETIRA, 540, 1296, scale=s)
    s = pop_in(t, S4 + BEAT * 3.5, 0.4)
    if s:
        place(c, CONDS[0], 540, 1366, scale=s)
        place(c, CONDS[1], 540, 1414, scale=s)
    s = pop_in(t, final, 0.4)
    if s:
        place(c, HANDLE, 540, 1500, scale=s * (1 + 0.04 * math.sin(t * 6)))


def frame(t):
    if t < S2:
        bg = bg_frame(BG, t)
    elif t < S3:
        bg = bg_frame(BG_DARK, t)
    else:
        bg = bg_frame(BG, t)
    c = bg.copy()
    particles(c, t)
    if t < S2:
        scene1(c, t)
    elif t < S3:
        scene2(c, t)
    elif t < S4:
        scene3(c, t)
    else:
        scene4(c, t)
    # quick flash on scene cuts
    for cut in (S2, S3, S4):
        if 0 <= t - cut < 0.12:
            a = 1 - (t - cut) / 0.12
            fl = Image.new("RGBA", (W, H), (255, 236, 210, int(110 * a)))
            c.alpha_composite(fl)
    # fade in from black (very short) and out at the end
    return c.convert("RGB")


def main():
    if sys.argv[1] == "--stills":
        ts = [float(x) for x in sys.argv[2].split(",")]
        os.makedirs(sys.argv[3], exist_ok=True)
        for t in ts:
            frame(t).save(os.path.join(sys.argv[3], f"f_{t:05.2f}.png"))
        return
    out, wav = sys.argv[1], sys.argv[2]
    n = int(round(DUR * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-level", "4.2", "-r", str(FPS), "-g", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-t", str(DUR), "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print("done", out)


if __name__ == "__main__":
    main()
