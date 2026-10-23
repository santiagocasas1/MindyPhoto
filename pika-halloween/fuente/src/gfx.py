"""Shared drawing helpers: styled text, pills, badges, ghosts, candies, compositing."""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FPS = 30
BPM = 128
BEAT = 60 / BPM
BAR = 4 * BEAT

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "work", "assets")
FONT_BOLD = os.path.join(ROOT, "fonts", "Fredoka-Bold.ttf")
FONT_SEMI = os.path.join(ROOT, "fonts", "Fredoka-SemiBold.ttf")
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

CREAM = (255, 244, 228)
ORANGE = (245, 122, 33)
ORANGE_D = (205, 70, 20)
YELLOW = (255, 196, 76)
DARK = (40, 20, 18)
PURPLE = (128, 82, 214)


# ---------------- easing ----------------
def clamp01(x):
    return max(0.0, min(1.0, x))


def prog(t, t0, dur):
    return clamp01((t - t0) / dur)


def ease_out_back(x, s=1.70158):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def ease_in_back(x, s=1.70158):
    return x * x * ((s + 1) * x - s)


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    return x ** 3


def ease_in_out(x):
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out_elastic(x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1


def pop_in(t, t0, dur=0.35):
    """0 -> 1 with overshoot."""
    return ease_out_back(prog(t, t0, dur), 2.2) if t >= t0 else 0.0


def pop_out(t, t0, dur=0.2):
    """1 -> 0 accelerating."""
    p = prog(t, t0, dur)
    return 1 - ease_in_back(p, 1.5) if p < 1 else 0.0


def beat_phase(t):
    return (t / BEAT) % 1.0


# ---------------- compositing ----------------
def _alpha_lut(a):
    return [int(i * a) for i in range(256)]


def paste(canvas, im, x, y):
    """alpha_composite that tolerates sprites partly (or fully) outside the canvas."""
    x, y = int(round(x)), int(round(y))
    cw, ch = canvas.size
    if x >= cw or y >= ch or x + im.width <= 0 or y + im.height <= 0:
        return
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(im.width, cw - x), min(im.height, ch - y)
    if sx0 or sy0 or sx1 < im.width or sy1 < im.height:
        im = im.crop((sx0, sy0, sx1, sy1))
    canvas.alpha_composite(im, (x + sx0, y + sy0))


def place(canvas, spr, x, y, scale=1.0, rot=0.0, alpha=1.0, sx=1.0, sy=1.0, anchor=(0.5, 0.5)):
    """Draw spr so that its anchor point lands on (x, y)."""
    if alpha <= 0.01 or scale <= 0.01:
        return
    w = max(1, int(round(spr.width * scale * sx)))
    h = max(1, int(round(spr.height * scale * sy)))
    im = spr if (w, h) == spr.size else spr.resize((w, h), Image.BICUBIC)
    ax, ay = anchor[0] * w, anchor[1] * h
    if abs(rot) > 0.05:
        cx, cy = w / 2, h / 2
        dx, dy = ax - cx, ay - cy
        th = math.radians(rot)
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
        ax = im.width / 2 + dx * math.cos(th) + dy * math.sin(th)
        ay = im.height / 2 - dx * math.sin(th) + dy * math.cos(th)
    if alpha < 0.99:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(_alpha_lut(alpha)))
    paste(canvas, im, x - ax, y - ay)


def load(name):
    return Image.open(os.path.join(ASSETS, name)).convert("RGBA")


# ---------------- text ----------------
def _font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_SEMI, size)


def styled_text(lines, size, fill=CREAM, outline=DARK, ext_color=ORANGE_D, ow=None, extrude=None,
                align="center", leading=1.0, shadow=True, max_width=None, bold=True):
    """Chunky cartoon text like the post: light face, coloured extrusion, dark outline.

    lines: list of str or (str, fill_rgb) tuples.
    """
    lines = [(l, fill) if isinstance(l, str) else l for l in lines]
    while True:
        font = _font(size, bold)
        ow_ = ow if ow is not None else max(2, round(size * 0.075))
        ex = extrude if extrude is not None else max(2, round(size * 0.085))
        widths = [font.getbbox(t, stroke_width=ow_)[2] - font.getbbox(t, stroke_width=ow_)[0] for t, _ in lines]
        if max_width is None or max(widths) + ex <= max_width or size < 12:
            break
        size = int(size * max_width / (max(widths) + ex)) - 1
    asc, desc = font.getmetrics()
    lh = int((asc + desc) * leading)
    pad = ow_ + ex + int(size * 0.25)
    cw = max(widths) + 2 * pad
    chh = lh * len(lines) + 2 * pad
    face = Image.new("L", (cw, chh), 0)
    outl = Image.new("L", (cw, chh), 0)
    extr = Image.new("L", (cw, chh), 0)
    color_layers = []
    df, do, de = ImageDraw.Draw(face), ImageDraw.Draw(outl), ImageDraw.Draw(extr)
    for i, ((txt, col), w) in enumerate(zip(lines, widths)):
        bx = font.getbbox(txt, stroke_width=ow_)[0]
        if align == "center":
            x = (cw - w) / 2 - bx
        elif align == "left":
            x = pad - bx
        else:
            x = cw - pad - w - bx
        y = pad + i * lh
        for k in range(ex + 1):
            do.text((x + k * 0.25, y + k), txt, font=font, fill=255, stroke_width=ow_, stroke_fill=255)
            if k:
                de.text((x + k * 0.25, y + k), txt, font=font, fill=255)
        lf = Image.new("L", (cw, chh), 0)
        ImageDraw.Draw(lf).text((x, y), txt, font=font, fill=255)
        df.text((x, y), txt, font=font, fill=255)
        color_layers.append((lf, col))
    out = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
    if shadow:
        sh = outl.filter(ImageFilter.GaussianBlur(size * 0.08))
        sh_im = Image.new("RGBA", (cw, chh), (10, 4, 8, 0))
        sh_im.putalpha(sh.point(lambda v: int(v * 0.55)))
        out.alpha_composite(sh_im, (0, 0))
    out.paste(Image.new("RGBA", (cw, chh), DARK + (255,)), (0, 0), outl)
    out.paste(Image.new("RGBA", (cw, chh), ext_color + (255,)), (0, 0), extr)
    for lf, col in color_layers:
        # subtle vertical gradient on the face: a touch darker at the bottom
        grad = Image.linear_gradient("L").resize((cw, chh))
        top = Image.new("RGBA", (cw, chh), col + (255,))
        bot = Image.new("RGBA", (cw, chh), tuple(int(c * 0.9) for c in col) + (255,))
        face_col = Image.composite(bot, top, grad)
        out.paste(face_col, (0, 0), lf)
    return trim(out)


def plain_text(text, size, fill=CREAM, ow=None, outline=DARK, bold=False, max_width=None):
    while True:
        font = _font(size, bold)
        ow_ = ow if ow is not None else max(2, round(size * 0.12))
        bb = font.getbbox(text, stroke_width=ow_)
        if max_width is None or bb[2] - bb[0] <= max_width or size < 10:
            break
        size -= 1
    im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), text, font=font, fill=fill, stroke_width=ow_, stroke_fill=outline)
    return trim(im)


def emoji(ch, height):
    f = ImageFont.truetype(FONT_EMOJI, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = trim(im)
    s = height / im.height
    return im.resize((max(1, int(im.width * s)), height), Image.LANCZOS)


def trim(im, pad=2):
    bb = im.getchannel("A").getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


# ---------------- shapes ----------------
def ss_canvas(w, h, s=4):
    return Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0)), s


def pill(text_sprite, padx=46, pady=22, color=ORANGE, dark=DARK, depth=10, outline=6, extra=None, gap=14):
    """Orange rounded pill with a 3D lip, holding a text sprite (and optional emoji sprite)."""
    cw = text_sprite.width + (extra.width + gap if extra is not None else 0)
    ch = max(text_sprite.height, extra.height if extra is not None else 0)
    w, h = cw + 2 * padx, ch + 2 * pady
    tw, th = w + 2 * outline, h + 2 * outline + depth
    big, s = ss_canvas(tw, th + 16)
    d = ImageDraw.Draw(big)
    r = h / 2
    d.rounded_rectangle((0, depth * s, tw * s, (h + 2 * outline + depth) * s), (r + outline) * s, fill=dark + (255,))
    d.rounded_rectangle((outline * s, (outline + depth) * s, (outline + w) * s, (outline + h + depth - 2) * s), r * s,
                        fill=tuple(int(c * 0.78) for c in color) + (255,))
    d.rounded_rectangle((0, 0, tw * s, (h + 2 * outline) * s), (r + outline) * s, fill=dark + (255,))
    d.rounded_rectangle((outline * s, outline * s, (outline + w) * s, (outline + h) * s), r * s, fill=color + (255,))
    # glossy highlight
    d.rounded_rectangle(((outline + r * 0.6) * s, (outline + h * 0.12) * s, (outline + w - r * 0.6) * s,
                         (outline + h * 0.32) * s), h * 0.1 * s, fill=(255, 255, 255, 60))
    im = big.resize((tw, th + 16), Image.LANCZOS)
    x = outline + padx
    y = outline + (h - text_sprite.height) // 2
    im.alpha_composite(text_sprite, (x, y))
    if extra is not None:
        im.alpha_composite(extra, (x + text_sprite.width + gap, outline + (h - extra.height) // 2))
    return trim(im)


def number_badge(n, d=130):
    big, s = ss_canvas(d + 20, d + 28)
    dr = ImageDraw.Draw(big)
    dr.ellipse((0, 10 * s, (d + 20) * s, (d + 28) * s), fill=DARK + (255,))
    dr.ellipse((0, 0, (d + 20) * s, (d + 18) * s), fill=DARK + (255,))
    dr.ellipse((8 * s, 8 * s, (d + 12) * s, (d + 10) * s), fill=ORANGE + (255,))
    dr.ellipse((22 * s, 14 * s, (d - 2) * s, (d * 0.55) * s), fill=(255, 180, 110, 110))
    im = big.resize((d + 20, d + 28), Image.LANCZOS)
    num = styled_text([str(n)], int(d * 0.62), fill=CREAM, ext_color=ORANGE_D, shadow=False)
    im.alpha_composite(num, ((im.width - num.width) // 2, (d + 18 - num.height) // 2 + 2))
    return im


def panel(w, h, r=36, fill=(28, 14, 24, 175), border=(245, 122, 33, 230), bw=4):
    big, s = ss_canvas(w, h)
    d = ImageDraw.Draw(big)
    d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), r * s, fill=border)
    d.rounded_rectangle((bw * s, bw * s, (w - bw) * s, (h - bw) * s), (r - bw) * s, fill=fill)
    return big.resize((w, h), Image.LANCZOS)


def ghost(size=240):
    """Cute white ghost in the style of the ones in the store picture."""
    w, h = size, int(size * 1.2)
    big, s = ss_canvas(w, h)
    d = ImageDraw.Draw(big)
    S = lambda *v: tuple(int(a * s) for a in v)
    body = (238, 236, 244, 255)
    d.ellipse(S(0, 0, w, w), fill=body)
    d.rectangle(S(0, w / 2, w, h - w * 0.14), fill=body)
    n = 4
    rr = w / (2 * n)
    for i in range(n):
        cx = rr + i * 2 * rr
        d.ellipse(S(cx - rr, h - w * 0.14 - rr, cx + rr, h - w * 0.14 + rr), fill=body)
    # little arms
    d.ellipse(S(-w * 0.05, w * 0.55, w * 0.18, w * 0.78), fill=body)
    d.ellipse(S(w * 0.82, w * 0.48, w * 1.0, w * 0.70), fill=body)
    # face
    ex, ey, er = w * 0.33, w * 0.45, w * 0.075
    for x in (ex, w - ex):
        d.ellipse(S(x - er, ey - er * 1.35, x + er, ey + er * 1.35), fill=(30, 22, 28, 255))
        d.ellipse(S(x - er * 0.45, ey - er * 1.0, x + er * 0.15, ey - er * 0.3), fill=(255, 255, 255, 255))
    d.chord(S(w * 0.4, w * 0.5, w * 0.6, w * 0.68), 0, 180, fill=(70, 30, 40, 255))
    for x in (w * 0.2, w * 0.8):
        d.ellipse(S(x - w * 0.07, w * 0.56, x + w * 0.07, w * 0.63), fill=(255, 150, 170, 150))
    im = big.resize((w, h), Image.LANCZOS)
    # soft glow + shade
    glow = im.getchannel("A").filter(ImageFilter.GaussianBlur(size * 0.06))
    out = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    g = Image.new("RGBA", out.size, (255, 230, 200, 0))
    ga = Image.new("L", out.size, 0)
    ga.paste(glow.point(lambda v: int(v * 0.5)), (20, 20))
    g.putalpha(ga)
    out.alpha_composite(g)
    out.alpha_composite(im, (20, 20))
    return out


def candy(color, size=70):
    w, h = size * 2, size
    big, s = ss_canvas(w, h)
    d = ImageDraw.Draw(big)
    S = lambda *v: tuple(int(a * s) for a in v)
    dark = tuple(int(c * 0.7) for c in color) + (255,)
    d.polygon(S(w * 0.3, h * 0.5, 0, h * 0.08, w * 0.06, h * 0.5, 0, h * 0.92), fill=dark)
    d.polygon(S(w * 0.7, h * 0.5, w, h * 0.08, w * 0.94, h * 0.5, w, h * 0.92), fill=dark)
    d.ellipse(S(w * 0.24, h * 0.1, w * 0.76, h * 0.9), fill=color + (255,))
    d.ellipse(S(w * 0.33, h * 0.2, w * 0.5, h * 0.42), fill=(255, 255, 255, 140))
    for k in range(3):
        x = w * (0.36 + 0.11 * k)
        d.line(S(x, h * 0.18, x + w * 0.05, h * 0.82), fill=(255, 255, 255, 90), width=int(3 * s))
    return big.resize((w, h), Image.LANCZOS)


def star(size=40, color=(255, 214, 102)):
    big, s = ss_canvas(size, size)
    d = ImageDraw.Draw(big)
    c = size * s / 2
    pts = []
    for i in range(10):
        r = c if i % 2 == 0 else c * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(pts, fill=color + (255,))
    return big.resize((size, size), Image.LANCZOS)


def glow_dot(size, color):
    r = size // 2
    yy, xx = np.mgrid[0:size, 0:size]
    dist = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = np.clip(1 - dist, 0, 1) ** 1.8
    arr = np.zeros((size, size, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr)


def rounded_card(img, size, radius=44, border=12, outline=5, border_color=CREAM):
    """Photo card with rounded corners, cream frame, dark outline and a soft shadow."""
    inner = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    tot = size + 2 * (border + outline)
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size * 4, size * 4), radius * 4, fill=255)
    inner.putalpha(m.resize((size, size), Image.LANCZOS))
    frame, s = ss_canvas(tot, tot)
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle((0, 0, tot * s, tot * s), (radius + border + outline) * s, fill=DARK + (255,))
    d.rounded_rectangle((outline * s, outline * s, (tot - outline) * s, (tot - outline) * s),
                        (radius + border) * s, fill=border_color + (255,))
    frame = frame.resize((tot, tot), Image.LANCZOS)
    frame.alpha_composite(inner, (border + outline, border + outline))
    pad = 60
    out = Image.new("RGBA", (tot + 2 * pad, tot + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("L", out.size, 0)
    sh.paste(frame.getchannel("A"), (pad, pad + 24))
    sh = sh.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.6))
    shadow = Image.new("RGBA", out.size, (8, 2, 6, 0))
    shadow.putalpha(sh)
    out.alpha_composite(shadow)
    out.alpha_composite(frame, (pad, pad))
    return out


def background(src, darken=0.72, blur=26):
    """Warm bokeh background built from the store photo, slightly larger than the frame so it can drift."""
    b = src.convert("RGB").filter(ImageFilter.GaussianBlur(blur))
    side = H + 140
    b = b.resize((side, side), Image.LANCZOS)
    arr = np.asarray(b).astype(np.float32) * darken
    # warm, slightly purple-tinted vignette
    yy, xx = np.mgrid[0:side, 0:side]
    cx, cy = side / 2, side / 2
    dist = np.sqrt(((xx - cx) / (W * 0.75)) ** 2 + ((yy - cy) / (H * 0.62)) ** 2)
    v = np.clip(1.15 - 0.55 * dist ** 1.6, 0.25, 1.0)
    arr *= v[..., None]
    arr[..., 2] *= 1.04
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


def bg_frame(bg, t, speed=1.0):
    side = bg.width
    mx, my = (side - W) / 2, (side - H) / 2
    x = mx + mx * 0.6 * math.sin(0.23 * t * speed)
    y = my + my * 0.6 * math.cos(0.31 * t * speed)
    return bg.crop((int(x), int(y), int(x) + W, int(y) + H))
