"""v2 motion-graphics helpers: per-glyph kinetic type, light FX, Halloween transitions, camera."""
import json
import math
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

from gfx import (W, H, FPS, BEAT, BAR, ROOT, FONT_BOLD, CREAM, ORANGE, ORANGE_D, YELLOW, DARK, PURPLE,
                 clamp01, prog, ease_out_back, ease_in_back, ease_out_cubic, ease_in_cubic, ease_in_out,
                 place, paste, trim)

HR = os.path.join(ROOT, "work", "assets_hr")


def ease_out_bounce(x):
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


def load_hr(name):
    return Image.open(os.path.join(HR, name)).convert("RGBA")


# ---------------- kinetic type ----------------
class GlyphText:
    """Chunky cartoon text (light face, coloured extrusion, dark outline) laid out per glyph,
    so every letter can be animated on its own. Drawn in two passes (backs, then faces) so
    outlines never cover a neighbour's face."""

    def __init__(self, lines, size, fill=CREAM, outline=DARK, ext_color=ORANGE_D, max_width=None,
                 leading=1.0, shadow=True, seed=0):
        lines = [(l, fill) if isinstance(l, str) else l for l in lines]
        while True:
            font = ImageFont.truetype(FONT_BOLD, size)
            ow = max(2, round(size * 0.075))
            ex = max(2, round(size * 0.085))
            widest = max(font.getlength(t) for t, _ in lines) + 2 * ow + ex
            if max_width is None or widest <= max_width or size < 12:
                break
            size = int(size * max_width / widest) - 1
        self.size = size
        asc, desc = font.getmetrics()
        lh = int((asc + desc) * leading)
        total_h = lh * len(lines)
        self.width, self.height = widest, total_h
        rnd = np.random.default_rng(seed)
        self.glyphs = []
        idx = 0
        for li, (txt, col) in enumerate(lines):
            x_start = -font.getlength(txt) / 2
            y_top = -total_h / 2 + li * lh
            for ci, ch in enumerate(txt):
                if ch == " ":
                    continue
                adv = font.getlength(txt[:ci])
                bb = font.getbbox(ch, stroke_width=ow)
                pad = ow + ex + int(size * 0.22)
                gw = int(bb[2] - bb[0] + 2 * pad)
                gh = int(asc + desc + 2 * pad)
                ox, oy = pad - bb[0], pad
                face = Image.new("L", (gw, gh), 0)
                outl = Image.new("L", (gw, gh), 0)
                extr = Image.new("L", (gw, gh), 0)
                df, do, de = ImageDraw.Draw(face), ImageDraw.Draw(outl), ImageDraw.Draw(extr)
                for k in range(ex + 1):
                    do.text((ox + k * 0.25, oy + k), ch, font=font, fill=255, stroke_width=ow, stroke_fill=255)
                    if k:
                        de.text((ox + k * 0.25, oy + k), ch, font=font, fill=255)
                df.text((ox, oy), ch, font=font, fill=255)
                back = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
                if shadow:
                    sh = outl.filter(ImageFilter.GaussianBlur(size * 0.07)).point(lambda v: int(v * 0.5))
                    shl = Image.new("RGBA", (gw, gh), (10, 4, 8, 0))
                    shl.putalpha(sh)
                    back.alpha_composite(shl, (0, int(size * 0.03)))
                back.paste(Image.new("RGBA", (gw, gh), DARK + (255,)), (0, 0), outl)
                back.paste(Image.new("RGBA", (gw, gh), ext_color + (255,)), (0, 0), extr)
                grad = Image.linear_gradient("L").resize((gw, gh))
                top = Image.new("RGBA", (gw, gh), col + (255,))
                bot = Image.new("RGBA", (gw, gh), tuple(int(c * 0.88) for c in col) + (255,))
                fc = Image.composite(bot, top, grad)
                fl = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
                fl.paste(fc, (0, 0), face)
                # glossy highlight on the upper part of the face
                hl = face.filter(ImageFilter.GaussianBlur(1)).point(lambda v: int(v * 0.35))
                hm = Image.linear_gradient("L").resize((gw, gh)).point(lambda v: 255 if v < 110 else 0)
                hl = ImageChops.multiply(hl, hm)
                fl.paste(Image.new("RGBA", (gw, gh), (255, 255, 255, 255)), (0, 0),
                         ImageChops.multiply(hl, face))
                cx = x_start + adv - ox + gw / 2
                cy = y_top - oy + gh / 2
                self.glyphs.append(dict(back=back, face=fl, cx=cx, cy=cy, i=idx, line=li,
                                        rnd=float(rnd.uniform(-1, 1)), rnd2=float(rnd.uniform(-1, 1))))
                idx += 1
        self.n = idx

    def draw(self, c, x, y, t, t0, scale=1.0, stagger=0.03, dur=0.38, style="pop", out=1.0,
             wave=0.0, wave_t=0.0, alpha=1.0):
        items = []
        for g in self.glyphs:
            ts = t0 + g["i"] * stagger
            if t < ts:
                continue
            p = clamp01((t - ts) / dur)
            if style == "pop":
                s = ease_out_back(p, 2.6)
                dy = (1 - ease_out_cubic(p)) * 50
                rot = (1 - p) * g["rnd"] * 35
            elif style == "drop":
                s = 1 + 0.35 * (1 - ease_out_cubic(p))
                dy = -(1 - ease_out_bounce(p)) * 320
                rot = (1 - p) * g["rnd"] * 25
            else:  # "stamp"
                s = 1 + 1.4 * (1 - ease_out_back(p, 2.0))
                dy = 0
                rot = (1 - p) * g["rnd"] * 12
            wv = wave * math.sin(2 * math.pi * 1.1 * wave_t - g["i"] * 0.55) if wave else 0.0
            a = min(1.0, (t - ts) / 0.06) * alpha
            items.append((g, x + g["cx"] * scale, y + (g["cy"] + dy + wv) * scale, s * scale * out, rot, a))
        for g, gx, gy, s, rot, a in items:
            place(c, g["back"], gx, gy, scale=s, rot=rot, alpha=a)
        for g, gx, gy, s, rot, a in items:
            place(c, g["face"], gx, gy, scale=s, rot=rot, alpha=a)


class TitleParts:
    """The original 'DULCE O PIKU' art, split per letter (see split_title.py)."""

    def __init__(self):
        meta = json.load(open(os.path.join(HR, "title_parts", "parts.json")))
        tw, th = meta["size"]
        self.width, self.height = tw, th
        self.parts = []
        rnd = np.random.default_rng(5)
        for p in meta["parts"]:
            im = Image.open(os.path.join(HR, "title_parts", p["name"] + ".png")).convert("RGBA")
            cx = p["x"] + p["w"] / 2 - tw / 2
            cy = p["y"] + p["h"] / 2 - th / 2
            self.parts.append(dict(name=p["name"], im=im, cx=cx, cy=cy, rnd=float(rnd.uniform(-1, 1))))
        letters = [p for p in self.parts if not p["name"].startswith("dash")]
        letters.sort(key=lambda p: p["cx"])
        for i, p in enumerate(letters):
            p["i"] = i
        for p in self.parts:
            if p["name"].startswith("dash"):
                p["i"] = None

    def draw(self, c, x, y, t, t0, scale, stagger=0.04, dur=0.32, out=1.0, wave=0.0, pulse=1.0):
        n_letters = sum(1 for p in self.parts if p["i"] is not None)
        for p in self.parts:
            if p["i"] is None:
                ts = t0 + n_letters * stagger
                if t < ts:
                    continue
                s = ease_out_back(prog(t, ts, 0.3), 3.0)
                side = -1 if p["name"] == "dashL" else 1
                dx = side * 30 * (1 - s)
                place(c, p["im"], x + (p["cx"] * pulse + dx) * scale, y + p["cy"] * scale, scale=scale * s * out * pulse)
                continue
            ts = t0 + p["i"] * stagger
            if t < ts:
                continue
            q = clamp01((t - ts) / dur)
            dy = -(1 - ease_out_bounce(q)) * 420
            sq = 1.0
            if q >= 1:
                land = clamp01((t - ts - dur) / 0.18)
                sq = 1 - 0.12 * math.sin(math.pi * land) if land < 1 else 1.0
            wv = wave * math.sin(2 * math.pi * 1.1 * t - p["i"] * 0.6) if wave else 0.0
            rot = (1 - q) * p["rnd"] * 30
            place(c, p["im"], x + p["cx"] * scale * pulse, y + (p["cy"] + dy + wv) * scale,
                  scale=scale * out * pulse, sx=2 - sq, sy=sq, rot=rot, anchor=(0.5, 0.5))


# ---------------- light ----------------
def add_light(c, light, x, y, intensity=1.0, scale=1.0, rot=0.0):
    """Additive blend of an RGB 'light' image (black = nothing) centred at (x, y)."""
    if intensity <= 0.01:
        return
    im = light
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05:
        im = im.rotate(rot, resample=Image.BILINEAR, expand=True)
    if intensity < 0.99:
        lut = [int(v * intensity) for v in range(256)] * 3
        im = im.point(lut)
    x0, y0 = int(x - im.width / 2), int(y - im.height / 2)
    bx0, by0 = max(0, x0), max(0, y0)
    bx1, by1 = min(c.width, x0 + im.width), min(c.height, y0 + im.height)
    if bx1 <= bx0 or by1 <= by0:
        return
    region = c.crop((bx0, by0, bx1, by1))
    lit = im.crop((bx0 - x0, by0 - y0, bx1 - x0, by1 - y0))
    rgb = ImageChops.add(region.convert("RGB"), lit)
    rgb.putalpha(region.getchannel("A"))
    c.paste(rgb, (bx0, by0))


def radial_light(size, color, falloff=1.6):
    r = size / 2
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** falloff
    return Image.fromarray((a[..., None] * np.array(color, np.float32)).astype(np.uint8), "RGB")


def rays_light(size, color, n=16, softness=6):
    big = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(big)
    c = size / 2
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n * 0.8
        d.polygon([(c, c), (c + c * 1.5 * math.cos(a0), c + c * 1.5 * math.sin(a0)),
                   (c + c * 1.5 * math.cos(a1), c + c * 1.5 * math.sin(a1))], fill=255)
    big = big.filter(ImageFilter.GaussianBlur(softness))
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    fade = np.clip(1 - np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c, 0, 1) ** 1.3
    a = np.asarray(big).astype(np.float32) / 255 * fade
    return Image.fromarray((a[..., None] * np.array(color, np.float32)).astype(np.uint8), "RGB")


def glint(size=64, color=(255, 240, 210)):
    """4-point star twinkle (RGB, for add_light)."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    c = (size - 1) / 2
    dx, dy = np.abs(xx - c) / c, np.abs(yy - c) / c
    star = np.exp(-dx * 14) * np.exp(-dy * 2.2) + np.exp(-dy * 14) * np.exp(-dx * 2.2)
    core = np.exp(-((dx ** 2 + dy ** 2) * 30))
    a = np.clip(star * 0.9 + core, 0, 1)
    return Image.fromarray((a[..., None] * np.array(color, np.float32)).astype(np.uint8), "RGB")


# ---------------- transitions ----------------
class BatSwarm:
    """A flock of bats sweeping diagonally across the screen; densest at t_mid (hides a cut)."""

    def __init__(self, bat, n=44, seed=3):
        rnd = np.random.default_rng(seed)
        dark = bat.copy()
        arr = np.asarray(dark).astype(np.float32)
        arr[..., :3] = arr[..., :3] * 0.35 + np.array([25, 8, 40]) * 0.65
        self.variants = [bat, Image.fromarray(arr.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(2))]
        self.bats = []
        for k in range(n):
            near = k < 9
            self.bats.append(dict(
                delay=float(rnd.uniform(-0.18, 0.18) if near else rnd.uniform(-0.35, 0.35)),
                y0=float(rnd.uniform(200, H + 500)),
                size=float(rnd.uniform(3.4, 5.6) if near else rnd.uniform(0.6, 1.8)),
                ph=float(rnd.uniform(0, 6.28)), var=1 if near else 0,
                dur=float(rnd.uniform(0.55, 0.7) if near else rnd.uniform(0.75, 1.0))))
        self.bats.sort(key=lambda b: b["size"])

    def draw(self, c, t, t_mid):
        for b in self.bats:
            u = (t - (t_mid + b["delay"] - b["dur"] / 2)) / b["dur"]
            if not 0 <= u <= 1:
                continue
            x = -500 + (W + 1000) * u
            y = b["y0"] - 900 * u + 40 * math.sin(u * 9 + b["ph"])
            flap = 0.5 + 0.5 * abs(math.sin(2 * math.pi * 5.5 * t + b["ph"]))
            place(c, self.variants[b["var"]], x, y, scale=b["size"], sy=flap, rot=22)


def cape_wipe(c, t, t_mid, dur=0.55, color_top=(122, 64, 196), color_bot=(58, 22, 98)):
    """A purple cape sweeping right-to-left with a wavy hem and an orange trim."""
    u = (t - (t_mid - dur / 2)) / dur
    if not 0 <= u <= 1:
        return
    e = ease_in_out(u)
    width = W + 900
    lead = W + 250 - (W + width + 500) * e
    trail = lead + width
    slope = 0.35
    pts_lead, pts_trail = [], []
    for k in range(0, 41):
        yy = -100 + (H + 200) * k / 40
        wv = 38 * math.sin(yy * 0.012 + t * 9)
        pts_lead.append((lead + wv + (yy - H / 2) * slope, yy))
        pts_trail.append((trail + 0.6 * wv + (yy - H / 2) * slope, yy))
    poly = pts_lead + pts_trail[::-1]
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    grad = Image.linear_gradient("L").resize((W, H))
    layer = Image.composite(Image.new("RGBA", (W, H), color_bot + (255,)), Image.new("RGBA", (W, H), color_top + (255,)), grad)
    layer.putalpha(mask)
    c.alpha_composite(layer)
    d = ImageDraw.Draw(c)
    d.line(pts_lead, fill=ORANGE + (255,), width=16)
    d.line([(x - 12, y) for x, y in pts_lead], fill=DARK + (255,), width=6)
    d.line([(x + 14, y) for x, y in pts_lead], fill=(255, 190, 120, 255), width=4)


class LightBurst:
    def __init__(self):
        self.glow = radial_light(1400, (255, 196, 120), 1.4)
        self.rays = rays_light(1600, (255, 220, 160), n=18)

    def draw(self, c, t, t_mid):
        u = (t - (t_mid - 0.22)) / 0.7
        if not 0 <= u <= 1:
            return
        grow = ease_out_cubic(u)
        inten = math.sin(math.pi * min(1, u * 1.4)) if u < 0.72 else max(0.0, 1 - (u - 0.72) / 0.28) * 0.6
        add_light(c, self.glow, W / 2, H * 0.45, intensity=inten, scale=0.4 + 1.6 * grow)
        add_light(c, self.rays, W / 2, H * 0.45, intensity=inten * 0.8, scale=0.6 + 1.2 * grow, rot=u * 40)
        flash = max(0.0, 1 - abs(t - t_mid) / 0.16)
        if flash > 0:
            c.alpha_composite(Image.new("RGBA", (W, H), (255, 240, 220, int(200 * flash))))


# ---------------- camera & grade ----------------
def camera(img_rgb, zoom=1.0, dx=0.0, dy=0.0, rot=0.0):
    if abs(zoom - 1) < 1e-4 and abs(dx) < 0.05 and abs(dy) < 0.05 and abs(rot) < 0.01:
        return img_rgb
    M = cv2.getRotationMatrix2D((W / 2, H / 2), rot, zoom)
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(img_rgb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def grade_luts():
    x = np.arange(256) / 255.0
    s = x + 0.07 * np.sin(2 * np.pi * (x - 0.5)) * (x * (1 - x)) * 4 / 4  # gentle S-curve
    s = np.clip(0.5 + (s - 0.5) * 1.05, 0, 1)
    r = np.clip(s * 1.02 + 0.004, 0, 1)
    g = s
    b = np.clip(s * 0.97 + 0.012, 0, 1)
    return [(v * 255 + 0.5).astype(np.uint8) for v in (r, g, b)]


def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    return np.clip(1.08 - 0.42 * d ** 2, 0.55, 1.0).astype(np.float32)[..., None]
