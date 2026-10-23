"""PIKA Halloween v2 — rigged Piku, living photo, kinetic type, light FX, motion blur.

Usage:
  python3 render2.py main   out.mp4 music.wav
  python3 render2.py winner out.mp4 music.wav
  python3 render2.py main   --stills 0.5,1.2 outdir
"""
import math
import os
import subprocess
import sys
import multiprocessing as mp
import numpy as np
import cv2

cv2.setNumThreads(1)  # one thread per worker process; parallelism comes from the process pool
from PIL import Image, ImageDraw, ImageFilter

from gfx import (W, H, FPS, BEAT, BAR, ROOT, CREAM, ORANGE, ORANGE_D, YELLOW, DARK, PURPLE,
                 clamp01, prog, pop_in, ease_out_back, ease_out_cubic, ease_in_cubic, ease_in_out, beat_phase,
                 place, styled_text, plain_text, pill, number_badge, panel, ghost, candy, star, emoji,
                 background, bg_frame)
from gfx2 import (GlyphText, TitleParts, BatSwarm, LightBurst, cape_wipe, add_light, radial_light, rays_light,
                  glint, camera, grade_luts, vignette, load_hr, ease_out_bounce, HR)
from rig import PikuRig, dance, blink_amount, FIST
from livephoto import LivingPhoto

S2, S3, S4 = 2 * BAR, 4 * BAR, 6 * BAR
FINAL = 7 * BAR
WORK = os.path.join(ROOT, "work")
rng = np.random.default_rng(31)

# ---------------- assets (loaded once, shared by forked workers) ----------------
store_lo = Image.open(os.path.join(WORK, "store.png")).convert("RGB")
BG = background(store_lo, darken=0.72, blur=30)
BG_COOL = background(store_lo, darken=0.5, blur=30)
RIG = PikuRig(os.path.join(HR, "piku.png"))
LIVE = LivingPhoto(os.path.join(HR, "store_2x.png"), os.path.join(WORK, "store_depth16.png"))
LOGO = load_hr("logo.png")
TITLE = TitleParts()
BAT = load_hr("bat.png")
PEPERO = load_hr("pepero.png")
SWARM = BatSwarm(BAT)
BURST = LightBurst()
GHOST = ghost(260)

# title glow (orange halo behind the letters)
_t = Image.new("L", (TITLE.width, TITLE.height), 0)
for _p in TITLE.parts:
    _t.paste(_p["im"].getchannel("A"), (int(_p["cx"] + TITLE.width / 2 - _p["im"].width / 2),
                                        int(_p["cy"] + TITLE.height / 2 - _p["im"].height / 2)))
_t = _t.resize((int(TITLE.width * 0.47), int(TITLE.height * 0.47)), Image.LANCZOS)
_tp = Image.new("L", (_t.width + 160, _t.height + 160), 0)
_tp.paste(_t, (80, 80))
_g = _tp.filter(ImageFilter.GaussianBlur(24))
TITLE_GLOW = Image.merge("RGB", [_g.point(lambda v: int(v * 1.0)), _g.point(lambda v: int(v * 0.5)), _g.point(lambda v: int(v * 0.12))])

RAYS = rays_light(1500, (130, 86, 40), n=16)
GLINT = glint(72)
LIGHTS = [radial_light(s, c) for s in (40, 80, 140) for c in ((255, 150, 60), (255, 205, 120), (170, 110, 255))]
EMBERS = [dict(x=rng.uniform(0, W), y0=rng.uniform(0, H), sp=rng.uniform(40, 130), ph=rng.uniform(0, 6.28),
               amp=rng.uniform(10, 40), spr=int(rng.integers(len(LIGHTS))), a=rng.uniform(0.25, 0.6))
          for _ in range(30)]
BOKEH = [dict(x=rng.uniform(-100, W + 100), y=rng.uniform(0, H), r=rng.uniform(0.9, 2.2), sp=rng.uniform(8, 25),
              ph=rng.uniform(0, 6.28), spr=int(rng.integers(len(LIGHTS))), a=rng.uniform(0.08, 0.18)) for _ in range(9)]

# texts
DATE_CHIP = pill(styled_text(["SÁBADO 31/10"], 58, shadow=False), padx=40, pady=14)
HEAD2 = GlyphText(["¿Encontrás las", ("3 cajas de Pepero?", YELLOW)], 92, max_width=1000, seed=2)
PAUSE = pill(styled_text(["Pausá y buscalas"], 54, shadow=False), padx=40, pady=14, extra=emoji("👀", 62))
HOWTO = GlyphText(["¿CÓMO PARTICIPAR?"], 104, max_width=990, seed=3)
STEPS = [["Buscá las 3 cajas", "de Pepero en la foto."], ["Marcalas y mandanos", "la imagen por DM."],
         ["Si acertás, te confirmamos", "tu premio y cómo retirarlo."]]
STEP_TXT = [styled_text(s, 58, align="left", shadow=False, max_width=720) for s in STEPS]
BADGES = [number_badge(i + 1, 118) for i in range(3)]
PANEL = panel(930, 200)
WIN_TXT = GlyphText(["¡GANÁ UNA GOLOSINA!"], 74, shadow=False, max_width=900, seed=4)
WIN_PILL = pill(Image.new("RGBA", (int(WIN_TXT.width), int(WIN_TXT.height * 0.8)), (0, 0, 0, 0)), padx=40, pady=20)
DATE_BIG = GlyphText(["Sábado 31/10"], 104, seed=5)
RETIRA = styled_text(["Retirá tu premio en Pika"], 62, max_width=900)
CONDS = [plain_text("Participá con un adulto · Un premio por chico", 40, bold=True, max_width=880),
         plain_text("¡Cupos limitados!", 40, bold=True, fill=YELLOW)]
HANDLE = pill(styled_text(["@pika.kstore"], 60, shadow=False), padx=40, pady=12, color=PURPLE)
GANASTE = GlyphText(["¡GANASTE!"], 178, fill=YELLOW, max_width=1000, seed=6)
SUB = styled_text(["¡Encontraste las 3 Pepero!"], 70, max_width=990)
RET = styled_text(["Retirá tu premio el", ("sábado 31/10 en Pika", YELLOW)], 66, max_width=990)

CANDY_COLORS = [(245, 122, 33), (150, 92, 230), (120, 210, 120), (255, 120, 170), (255, 200, 70)]
CANDIES = [candy(c, 50) for c in CANDY_COLORS]
STARS = [star(36), star(28, (255, 240, 200))]
SPRINKLES = CANDIES + STARS
RAIN = [dict(x=rng.uniform(40, W - 40), delay=rng.uniform(0, 1.8), sp=rng.uniform(380, 650), rot0=rng.uniform(0, 360),
             vr=rng.uniform(-260, 260), sway=rng.uniform(10, 50), kind=int(rng.integers(len(SPRINKLES))),
             sc=rng.uniform(0.8, 1.3)) for _ in range(36)]
FORE = [dict(x=x, delay=d, sp=rng.uniform(700, 900), rot0=rng.uniform(0, 360), vr=rng.uniform(-200, 200),
             kind=int(rng.integers(len(CANDIES))), sc=rng.uniform(1.7, 2.1)) for x, d in ((30, 0.2), (1050, 0.9), (40, 1.7), (1045, 2.4))]
FORE_SPR = [c.filter(ImageFilter.GaussianBlur(3)) for c in CANDIES]
BURST_PARTS = [dict(ang=rng.uniform(0, 2 * math.pi), v=rng.uniform(500, 1100), kind=int(rng.integers(len(SPRINKLES))),
                    vr=rng.uniform(-400, 400), sc=rng.uniform(0.8, 1.4)) for _ in range(34)]

# card (living photo) frame
CARD = 880
CARD_CY = 965
BORDER, OUTLINE, SHPAD = 12, 5, 60
_tot = CARD + 2 * (BORDER + OUTLINE)
_frame = Image.new("RGBA", (_tot * 4, _tot * 4), (0, 0, 0, 0))
_d = ImageDraw.Draw(_frame)
_d.rounded_rectangle((0, 0, _tot * 4, _tot * 4), (44 + BORDER + OUTLINE) * 4, fill=DARK + (255,))
_d.rounded_rectangle((OUTLINE * 4, OUTLINE * 4, (_tot - OUTLINE) * 4, (_tot - OUTLINE) * 4), (44 + BORDER) * 4, fill=CREAM + (255,))
_frame = _frame.resize((_tot, _tot), Image.LANCZOS)
CARD_BASE = Image.new("RGBA", (_tot + 2 * SHPAD, _tot + 2 * SHPAD), (0, 0, 0, 0))
_sh = Image.new("L", CARD_BASE.size, 0)
_sh.paste(_frame.getchannel("A"), (SHPAD, SHPAD + 24))
_sh = _sh.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.6))
_shl = Image.new("RGBA", CARD_BASE.size, (8, 2, 6, 0))
_shl.putalpha(_sh)
CARD_BASE.alpha_composite(_shl)
CARD_BASE.alpha_composite(_frame, (SHPAD, SHPAD))
_m = Image.new("L", (CARD * 4, CARD * 4), 0)
ImageDraw.Draw(_m).rounded_rectangle((0, 0, CARD * 4, CARD * 4), 44 * 4, fill=255)
CARD_MASK = _m.resize((CARD, CARD), Image.LANCZOS)

LUTS = grade_luts()
VIG = vignette()


# ---------------- shared pieces ----------------
def embers(c, t):
    for b in BOKEH:
        add_light(c, LIGHTS[b["spr"]], b["x"] + 30 * math.sin(t * 0.3 + b["ph"]), (b["y"] - b["sp"] * t) % (H + 300) - 150,
                  intensity=b["a"], scale=b["r"] * 2.2)
    for p in EMBERS:
        y = (p["y0"] - p["sp"] * t) % (H + 200) - 100
        x = p["x"] + p["amp"] * math.sin(p["ph"] + t * 1.3)
        tw = 0.7 + 0.3 * math.sin(p["ph"] * 3 + t * 5)
        add_light(c, LIGHTS[p["spr"]], x, y, intensity=p["a"] * tw, scale=0.6)


def twinkles(c, t, spots, t_from):
    for k, (x, y, t0) in enumerate(spots):
        u = (t - t_from - t0) % 1.6
        if u < 0.45:
            add_light(c, GLINT, x, y, intensity=math.sin(math.pi * u / 0.45), scale=0.7 + 0.5 * math.sin(math.pi * u / 0.45), rot=u * 90)


def bat(c, t, t0, t1, y, direction=1, scale=0.65, wobble=60):
    if not (t0 <= t <= t1):
        return
    u = (t - t0) / (t1 - t0)
    x = -140 + (W + 280) * u if direction > 0 else W + 140 - (W + 280) * u
    yy = y + wobble * math.sin(u * 2 * math.pi * 1.5)
    flap = 0.5 + 0.5 * abs(math.sin(t * 2 * math.pi * 3.2))
    spr = BAT if direction > 0 else BAT.transpose(Image.FLIP_LEFT_RIGHT)
    place(c, spr, x, yy, scale=scale, sy=flap, rot=-8 * math.cos(u * 2 * math.pi * 1.5) * direction)


def bounce(t, amp):
    ph = beat_phase(t)
    hop = -amp * math.sin(math.pi * ph)
    squash = max(0.0, 1 - ph / 0.16) if ph < 0.16 else 0.0
    sx = 1 + 0.05 * squash - 0.02 * math.sin(math.pi * ph)
    sy = 1 - 0.07 * squash + 0.03 * math.sin(math.pi * ph)
    return hop, sx, sy


def piku(c, t, x, feet, height, t_in, energy=1.0, amp=26, enter_from=2500, hit=1.0, before=None):
    """Draw the rigged Piku. `before(fist_xy, pose)` is called right before Piku is placed
    (used to draw the Pepero box behind his fist)."""
    if t < t_in:
        return
    scale = height / RIG.h * hit
    p = prog(t, t_in, 0.45)
    if p < 1:
        e = ease_out_back(p, 1.4)
        y = enter_from + (feet - enter_from) * e
        st = 1 + 0.14 * (1 - p)
        params = dance(t, BEAT, energy=0.4)
        sx, sy, rot = 1 / st ** 0.5, st, -10 * (1 - e)
    else:
        hop, sx, sy = bounce(t, amp)
        land = max(0.0, 1 - (t - t_in - 0.45) / 0.18)
        sx += 0.10 * land
        sy -= 0.14 * land
        y, rot = feet + hop, 0.0
        params = dance(t, BEAT, energy=energy)
        params["blink"] = blink_amount(t)
    img = RIG.pose(**params)
    if before is not None:
        fx, fy = RIG.forward(FIST, params["arm"], params["lean"])
        th = math.radians(rot)
        lx, ly = (fx - RIG.w / 2) * scale * sx, (fy - RIG.h) * scale * sy
        before((x + lx * math.cos(th) + ly * math.sin(th), y - lx * math.sin(th) + ly * math.cos(th)), params, scale)
    place(c, img, x, y, scale=scale, sx=sx, sy=sy, rot=rot, anchor=(0.5, 1.0))


def rain(c, t, t0, items=RAIN, sprites=SPRINKLES):
    for q in items:
        tt = t - t0 - q["delay"] * 0.6
        if tt < 0:
            continue
        y = -80 + q["sp"] * tt
        if y > H + 120:
            continue
        x = q["x"] + q.get("sway", 0) * math.sin(tt * 3 + q["rot0"])
        place(c, sprites[q["kind"]], x, y, scale=q["sc"], rot=q["rot0"] + q["vr"] * tt)


def confetti_burst(c, t, t0, x, y):
    tt = t - t0
    if tt < 0 or tt > 2.2:
        return
    for q in BURST_PARTS:
        px = x + math.cos(q["ang"]) * q["v"] * tt
        py = y + math.sin(q["ang"]) * q["v"] * tt + 900 * tt * tt
        place(c, SPRINKLES[q["kind"]], px, py, scale=q["sc"], rot=q["vr"] * tt, alpha=max(0.0, 1 - tt / 2.2))


def sparkle_ring(c, t, t0, x, y, n=12, radius=320):
    u = (t - t0) / 0.6
    if not 0 <= u <= 1:
        return
    for k in range(n):
        a = 2 * math.pi * k / n + 0.3
        r = radius * ease_out_cubic(u)
        add_light(c, GLINT, x + math.cos(a) * r, y + math.sin(a) * r * 0.6, intensity=1 - u, scale=0.8, rot=u * 60)


def make_card(content):
    """content: float RGB (CARD x CARD) -> RGBA card sprite with frame and shadow."""
    im = Image.fromarray((content * 255 + 0.5).astype(np.uint8), "RGB").convert("RGBA")
    im.putalpha(CARD_MASK)
    card = CARD_BASE.copy()
    card.alpha_composite(im, (SHPAD + BORDER + OUTLINE, SHPAD + BORDER + OUTLINE))
    return card


def magnifier(c, t, full, card_scale):
    """Glass lens with barrel distortion, wandering away from the band where the Pepero are."""
    t0, t1 = S2 + 0.9, S3 - 0.4
    if not (t0 < t < t1):
        return
    u = (t - t0) / (t1 - t0)
    pts = [(-120, 160), (230, 150), (560, 170), (330, 200), (310, 720), (600, 730), (1000, 740)]
    seg = u * (len(pts) - 1)
    i = min(int(seg), len(pts) - 2)
    f = ease_in_out(seg - i)
    px = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
    py = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
    cx = 540 + (px - CARD / 2) * card_scale
    cy = CARD_CY + (py - CARD / 2) * card_scale
    r = 96
    k = full.shape[0] / CARD
    yy, xx = np.mgrid[-r:r, -r:r].astype(np.float32)
    rn2 = (xx ** 2 + yy ** 2) / (r * r)
    barrel = 0.8 + 0.2 * rn2
    mag = 1.75
    mx = (px * k + xx * k / mag / card_scale * barrel).astype(np.float32)
    my = (py * k + yy * k / mag / card_scale * barrel).astype(np.float32)
    lens = cv2.remap(full, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    # glass shading: slight darkening at the rim, bright reflection arc
    lens = lens * (1 - 0.18 * np.clip(rn2 - 0.6, 0, 1)[..., None] * 2.5)
    a = np.clip((1 - np.sqrt(rn2)) * r, 0, 1)
    rgba = np.dstack([np.clip(lens, 0, 1) * 255, a * 255]).astype(np.uint8)
    lens_im = Image.fromarray(rgba, "RGBA")
    S = 3
    pad = 110
    size = 2 * r + 2 * pad
    big = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    o = pad
    Sx = lambda *v: tuple(int(q * S) for q in v)
    # shadow, handle
    d.ellipse(Sx(o - 16 + 10, o - 16 + 16, o + 2 * r + 16 + 10, o + 2 * r + 16 + 16), fill=(0, 0, 0, 70))
    hx0, hy0, hx1, hy1 = o + r * 1.62, o + r * 1.62, o + r * 2.5, o + r * 2.5
    d.line(Sx(hx0, hy0, hx1, hy1), fill=DARK + (255,), width=36 * S)
    d.ellipse(Sx(hx1 - 18, hy1 - 18, hx1 + 18, hy1 + 18), fill=DARK + (255,))
    d.line(Sx(hx0 + 3, hy0 + 3, hx1 - 2, hy1 - 2), fill=ORANGE + (255,), width=24 * S)
    d.ellipse(Sx(hx1 - 13, hy1 - 13, hx1 + 11, hy1 + 11), fill=ORANGE + (255,))
    d.line(Sx(hx0 + 8, hy0 - 2, hx1 - 8, hy1 - 12), fill=(255, 200, 150, 160), width=5 * S)
    frame = big.resize((size, size), Image.LANCZOS)
    frame.alpha_composite(lens_im, (o, o))
    ring = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(ring)
    d.ellipse(Sx(o - 18, o - 18, o + 2 * r + 18, o + 2 * r + 18), outline=DARK + (255,), width=24 * S)
    d.ellipse(Sx(o - 13, o - 13, o + 2 * r + 13, o + 2 * r + 13), outline=CREAM + (255,), width=15 * S)
    d.arc(Sx(o + 16, o + 16, o + 2 * r - 16, o + 2 * r - 16), 195, 255, fill=(255, 255, 255, 190), width=9 * S)
    d.arc(Sx(o + 30, o + 30, o + 2 * r - 30, o + 2 * r - 30), 20, 45, fill=(255, 255, 255, 110), width=5 * S)
    frame.alpha_composite(ring.resize((size, size), Image.LANCZOS))
    alpha = min(1.0, (t - t0) / 0.15, (t1 - t) / 0.15)
    place(c, frame, cx, cy, alpha=alpha, scale=0.94 + 0.06 * min(1.0, (t - t0) / 0.2),
          anchor=((o + r) / size, (o + r) / size))


def shine(c, im, x, y, t, t0, dur=0.45):
    """A glossy light band sweeping across a sprite (clipped to it)."""
    u = (t - t0) / dur
    if not 0 <= u <= 1:
        return
    w, h = im.size
    band = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(band)
    bx = -200 + (w + 400) * ease_in_out(u)
    d.polygon([(bx, 0), (bx + 70, 0), (bx + 10, h), (bx - 60, h)], fill=110)
    band = band.filter(ImageFilter.GaussianBlur(12))
    from PIL import ImageChops
    band = ImageChops.multiply(band, im.getchannel("A"))
    layer = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    layer.putalpha(band)
    place(c, layer, x, y)


# ---------------- main ad ----------------
def scene1(c, t):
    ra = ease_out_cubic(prog(t, 0.3, 0.7))
    add_light(c, RAYS, 540, 1180, intensity=0.38 * ra, rot=t * 10)
    if t > 1.6:
        g = ease_out_back(prog(t, 1.6, 0.5))
        place(c, GHOST, -160 + 290 * g, 1180 + 18 * math.sin(t * 3.2), scale=0.8, rot=12 + 5 * math.sin(t * 2.5))
    bat(c, t, 0.5, 2.9, 780, 1, 0.7)
    bat(c, t, 1.3, 3.7, 300, -1, 0.55, 40)
    piku(c, t, 540, 1600, 800, 0.0, energy=1.0)
    if t > 0.12:
        p = prog(t, 0.12, 0.55)
        y = -220 + (300 + 220) * ease_out_bounce(p)
        sq = 1 - 0.1 * math.sin(math.pi * clamp01((t - 0.67) / 0.2)) if t > 0.67 else 1.0
        place(c, LOGO, 540, y + 6 * math.sin(t * 2.4), scale=0.563, sx=2 - sq, sy=sq)
    if t > 0.6:
        pulse = 1 + 0.025 * max(0.0, 1 - beat_phase(t) / 0.25) if t > 1.5 else 1.0
        add_light(c, TITLE_GLOW, 540, 530, intensity=0.32 + 4.0 * (pulse - 1))
        TITLE.draw(c, 540, 530, t, t0=0.62, scale=0.47, wave=5 if t > 1.5 else 0, pulse=pulse)
    s = pop_in(t, 5 * BEAT, 0.35)
    if s:
        place(c, DATE_CHIP, 540, 690, scale=s, rot=3 + 2 * math.sin(t * 3))
        shine(c, DATE_CHIP, 540, 690, t, 5 * BEAT + 0.3)
    twinkles(c, t, [(150, 470, 0.0), (930, 600, 0.5), (880, 240, 1.0), (200, 760, 1.3)], 1.4)


def scene2(c, t):
    HEAD2.draw(c, 540, 300, t, t0=S2 + 0.02, stagger=0.022, style="pop", wave=3, wave_t=t)
    s = pop_in(t, S2 + 0.5 * BEAT, 0.5)
    if s:
        u = clamp01((t - S2) / (2 * BAR))
        content, full = LIVE.render(t, CARD, cam=(math.sin(1.1 * (t - S2) - 0.8), 0.6 * math.cos(0.8 * (t - S2))),
                                    zoom=1.0 + 0.035 * ease_in_out(u), return_full=True)
        card_scale = s * (1 + 0.012 * (t - S2) / BAR)
        place(c, make_card(content), 540, CARD_CY, scale=card_scale, rot=6 * (1 - min(1, s)))
        magnifier(c, t, full, card_scale)
    s = pop_in(t, S2 + BAR + 0.5 * BEAT, 0.35)
    if s:
        bob = 1 + 0.04 * max(0.0, 1 - beat_phase(t) / 0.2)
        place(c, PAUSE, 540, 1500, scale=s * bob, rot=-2)
        shine(c, PAUSE, 540, 1500, t, S2 + BAR + 0.5 * BEAT + 0.3)


def scene3(c, t):
    HOWTO.draw(c, 540, 330, t, t0=S3, stagger=0.028, style="drop", dur=0.45, wave=3, wave_t=t)
    for i in range(3):
        t0 = S3 + BEAT * (1 + 2 * i)
        if t < t0:
            continue
        p = ease_out_back(prog(t, t0, 0.42), 1.8)
        y = 575 + i * 240
        dx = 700 * (1 - p)
        place(c, PANEL, 565 + dx, y, alpha=min(1, p * 2))
        shine(c, PANEL, 565 + dx, y, t, t0 + 0.25, 0.5)
        place(c, STEP_TXT[i], 238 + dx, y, anchor=(0, 0.5))
        bs = pop_in(t, t0 + 0.08, 0.35)
        bob = 1 + 0.06 * max(0.0, 1 - beat_phase(t) / 0.2) if t > t0 + 0.5 else 1
        place(c, BADGES[i], 130 + dx * 1.2, y, scale=bs * bob, rot=-360 * (1 - bs) if bs < 1 else 0)
    piku(c, t, 540, 1790, 560, S3 + 0.2, energy=1.25, amp=18, enter_from=2400)


def scene4(c, t):
    hit = 1 + 0.07 * max(0.0, 1 - (t - FINAL) / 0.3) if t >= FINAL else 1.0
    ra = ease_out_cubic(prog(t, S4, 0.6))
    add_light(c, RAYS, 540, 820, intensity=0.55 * ra * hit, scale=1.1, rot=-t * 14)
    rain(c, t, S4)
    g = ease_out_back(prog(t, S4 + 0.6, 0.5))
    if g:
        place(c, GHOST, W + 150 - 300 * g, 760 + 16 * math.sin(t * 3), scale=0.6, rot=-12 + 4 * math.sin(t * 2.2))
    bat(c, t, S4 + 0.3, 15.0, 620, -1, 0.55, 50)
    confetti_burst(c, t, FINAL, 540, 820)
    piku(c, t, 540, 1110, 640, S4, energy=1.3 if t < FINAL else 1.7, amp=34 if t < FINAL else 46, enter_from=2400, hit=hit)
    # a few big, out-of-focus candies drifting down the edges (depth of field), behind the texts
    rain(c, t, S4, items=FORE, sprites=FORE_SPR)
    s = pop_in(t, S4 + 0.05, 0.45)
    if s:
        place(c, LOGO, 540, 250 - 200 * (1 - s), scale=0.477 * hit)
    t_win = S4 + 0.5 * BEAT
    if t >= t_win:
        ps = 1 + 0.9 * (1 - ease_out_back(prog(t, t_win, 0.3), 2.2))
        pulse = 1 + 0.04 * max(0.0, 1 - ((t - S4 - BAR) / BAR % 1) * BAR / 0.25) if t > S4 + BAR else 1.0
        place(c, WIN_PILL, 540, 440, scale=ps * hit * pulse, rot=-2, alpha=min(1.0, (t - t_win) / 0.06))
        WIN_TXT.draw(c, 540, 434, t, t_win + 0.08, scale=hit * pulse, stagger=0.018, style="pop", dur=0.3)
        sparkle_ring(c, t, t_win, 540, 440)
    DATE_BIG.draw(c, 540, 1195, t, S4 + 1.5 * BEAT, scale=hit, stagger=0.03, style="pop", wave=3, wave_t=t)
    s = pop_in(t, S4 + 2.5 * BEAT, 0.4)
    if s:
        place(c, RETIRA, 540, 1296, scale=s)
    s = pop_in(t, S4 + 3.5 * BEAT, 0.4)
    if s:
        place(c, CONDS[0], 540, 1366, scale=s)
        place(c, CONDS[1], 540, 1414, scale=s)
    s = pop_in(t, FINAL, 0.4)
    if s:
        place(c, HANDLE, 540, 1500, scale=s * (1 + 0.04 * math.sin(t * 6)))
        shine(c, HANDLE, 540, 1500, t, FINAL + 0.35)
    twinkles(c, t, [(160, 330, 0.0), (930, 300, 0.4), (110, 980, 0.9), (960, 1050, 1.2)], S4 + 0.5)


def frame_main(t):
    c = (bg_frame(BG_COOL, t) if S2 <= t < S3 else bg_frame(BG, t)).copy()
    embers(c, t)
    if t < S2:
        scene1(c, t)
    elif t < S3:
        scene2(c, t)
    elif t < S4:
        scene3(c, t)
    else:
        scene4(c, t)
    SWARM.draw(c, t, S2)
    if abs(t - S2) < 0.6:
        c.alpha_composite(Image.new("RGBA", (W, H), (30, 8, 45, int(150 * max(0.0, 1 - abs(t - S2) / 0.22)))))
    cape_wipe(c, t, S3)
    BURST.draw(c, t, S4)
    return c


def cam_main(t):
    z, dx, dy = 1.012 + 0.006 * math.sin(t * 0.7), 0.0, 0.0
    for cut in (S2, S3, S4):
        if cut - 0.3 <= t < cut:
            z *= 1 + 0.10 * ease_in_cubic(prog(t, cut - 0.3, 0.3))
        elif cut <= t < cut + 0.45:
            z *= 1 + 0.06 * (1 - ease_out_cubic(prog(t, cut, 0.45)))
    for te, k in ((0.94, 1.0), (S4 + 0.5 * BEAT, 0.8), (FINAL, 1.2)):
        if 0 <= t - te < 0.5:
            e = math.exp(-(t - te) / 0.11)
            z *= 1 + 0.035 * k * e
            dx += 7 * k * e * math.sin(2 * math.pi * 23 * (t - te))
            dy += 6 * k * e * math.sin(2 * math.pi * 19 * (t - te) + 1.1)
    return z, dx, dy


MB_MAIN = [(0.0, 0.62, 5), (0.62, 1.4, 4), (2.3, 2.62, 4), (3.2, 4.45, 6), (5.82, 6.15, 4), (7.15, 7.8, 10),
           (7.8, 7.97, 5), (7.97, 8.27, 8), (8.27, 8.91, 3), (8.91, 9.21, 8), (9.21, 9.84, 3), (9.84, 10.14, 8),
           (10.14, 10.9, 3), (10.9, 12.0, 6), (12.0, 15.0, 3)]


# ---------------- winner clip ----------------
CATCH = 3 * BEAT
FINAL_W = 3 * BAR


def frame_winner(t):
    c = bg_frame(BG, t).copy()
    embers(c, t)
    hit = 1 + 0.07 * max(0.0, 1 - (t - FINAL_W) / 0.3) if t >= FINAL_W else 1.0
    ra = ease_out_cubic(prog(t, CATCH, 0.4))
    add_light(c, RAYS, 540, 1000, intensity=0.6 * ra * hit, scale=1.15, rot=-t * 22)
    rain(c, t, CATCH)
    bat(c, t, 0.3, 3.4, 560, 1, 0.65)
    bat(c, t, 3.2, 7.2, 820, -1, 0.5, 40)

    def box(fist, params, scale):
        fx, fy = fist
        bs = 0.5 * hit
        if t >= CATCH:
            pop = 1 + 0.12 * max(0.0, 1 - (t - CATCH) / 0.25)
            tilt = -14 + params["arm"] * 0.8 + params["lean"] + 4 * math.sin(t * 5)
            place(c, PEPERO, fx + 10 * scale / 0.57, fy + 36 * scale / 0.57, scale=bs * pop, rot=tilt, anchor=(0.5, 1.0))
        elif t >= 2 * BEAT:
            p = prog(t, 2 * BEAT, CATCH - 2 * BEAT)
            by = -320 + (fy + 36 + 320) * p * p
            bx = 760 + (fx + 10 - 760) * p
            place(c, PEPERO, bx, by, scale=bs, rot=-14 + 540 * (1 - p), anchor=(0.5, 1.0))

    catch_sq = max(0.0, 1 - (t - CATCH) / 0.2) if t >= CATCH else 0.0
    piku(c, t, 540, 1330, 700, 0.0, energy=1.1 if t < FINAL_W else 1.6, amp=30 if t < FINAL_W else 44,
         hit=hit * (1 - 0.04 * catch_sq), before=lambda f, pr, sc: (confetti_burst(c, t, FINAL_W, 540, 980), box(f, pr, sc)))
    if t >= BEAT:
        GANASTE.draw(c, 540, 300, t, BEAT, scale=hit * (1 + 0.03 * max(0.0, 1 - beat_phase(t) / 0.25) if t > BAR else 1),
                     stagger=0.035, style="stamp", dur=0.3, wave=4 if t > BAR else 0, wave_t=t)
        sparkle_ring(c, t, BEAT + 0.1, 540, 300, radius=420)
    s = pop_in(t, BAR, 0.4)
    if s:
        place(c, SUB, 540, 470, scale=s)
        shine(c, SUB, 540, 470, t, BAR + 0.3)
    s = pop_in(t, BAR + 2 * BEAT, 0.4)
    if s:
        place(c, RET, 540, 1470, scale=s * hit)
    s = pop_in(t, 2 * BAR, 0.4)
    if s:
        place(c, HANDLE, 540, 1650, scale=s * (1 + 0.04 * math.sin(t * 6)))
        shine(c, HANDLE, 540, 1650, t, 2 * BAR + 0.3)
    twinkles(c, t, [(150, 700, 0.0), (930, 640, 0.6), (180, 1250, 1.1), (900, 1300, 0.3)], CATCH)
    if 0 <= t - CATCH < 0.12:
        c.alpha_composite(Image.new("RGBA", (W, H), (255, 236, 210, int(110 * (1 - (t - CATCH) / 0.12)))))
    return c


def cam_winner(t):
    z, dx, dy = 1.012 + 0.006 * math.sin(t * 0.7), 0.0, 0.0
    for te, k in ((BEAT + 0.05, 1.0), (CATCH, 0.8), (FINAL_W, 1.2)):
        if 0 <= t - te < 0.5:
            e = math.exp(-(t - te) / 0.11)
            z *= 1 + 0.035 * k * e
            dx += 7 * k * e * math.sin(2 * math.pi * 23 * (t - te))
            dy += 6 * k * e * math.sin(2 * math.pi * 19 * (t - te) + 1.1)
    return z, dx, dy


MB_WINNER = [(0.0, 0.62, 5), (0.62, 1.0, 4), (0.9, 1.75, 5), (1.8, 2.2, 3), (2.75, 3.1, 3), (3.7, 4.1, 3), (5.55, 7.5, 3)]

KINDS = {"main": (frame_main, cam_main, MB_MAIN, 8 * BAR), "winner": (frame_winner, cam_winner, MB_WINNER, 4 * BAR)}


# ---------------- frame assembly ----------------
def subframes(t, windows):
    for a, b, n in windows:
        if a <= t < b:
            return n
    return 1


def render(kind, t):
    fr, cam, mb, dur = KINDS[kind]
    n = subframes(t, mb)
    shutter = 0.5 / FPS
    acc = None
    for k in range(n):
        ts = t + (k / n - 0.5) * shutter if n > 1 else t
        ts = min(max(ts, 0.0), dur - 1e-3)
        img = np.asarray(fr(ts).convert("RGB")).astype(np.float32)
        acc = img if acc is None else acc + img
    img = acc / n
    z, dx, dy = cam(t)
    img = camera(img, z, dx, dy)
    img = img * VIG
    img = np.clip(img, 0, 255).astype(np.uint8)
    for ch in range(3):
        img[..., ch] = cv2.LUT(img[..., ch], LUTS[ch])
    return img


def _work(args):
    kind, t = args
    cv2.setNumThreads(1)
    return render(kind, t).tobytes()


def main():
    kind = sys.argv[1]
    dur = KINDS[kind][3]
    if sys.argv[2] == "--stills":
        os.makedirs(sys.argv[4], exist_ok=True)
        for t in [float(x) for x in sys.argv[3].split(",")]:
            Image.fromarray(render(kind, t)).save(os.path.join(sys.argv[4], f"{kind}_{t:05.2f}.png"))
        return
    out, wav = sys.argv[2], sys.argv[3]
    n = int(round(dur * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-level", "4.2", "-g", str(FPS), "-bf", "2", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-t", f"{dur:.3f}", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with mp.get_context("spawn").Pool(4) as pool:
        for i, buf in enumerate(pool.imap(_work, [(kind, i / FPS) for i in range(n)], chunksize=2)):
            p.stdin.write(buf)
            if i % 30 == 0:
                print(f"{kind}: frame {i}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print("done", out)


if __name__ == "__main__":
    main()
