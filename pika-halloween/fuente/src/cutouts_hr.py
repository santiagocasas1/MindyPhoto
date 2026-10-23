"""High-resolution sprites from the Real-ESRGAN x4 renders.

The low-res mattes (rembg isnet, cleaned in cutouts.py) are upsampled and snapped to the sharp
edges of the upscaled image with a guided filter; edge colours are decontaminated so no orange
halo from the old background survives. Sprites are saved at 2x the original screenshot scale.

Usage: python3 cutouts_hr.py <work dir>
"""
import sys
import numpy as np
import cv2
from PIL import Image, ImageDraw

work = sys.argv[1]
OUT = f"{work}/assets_hr"


def guided_filter(I, p, r, eps):
    box = lambda x: cv2.boxFilter(x, -1, (r, r), borderType=cv2.BORDER_REFLECT)
    mI, mp = box(I), box(p)
    a = (box(I * p) - mI * mp) / (box(I * I) - mI * mI + eps)
    b = mp - a * mI
    return box(a) * I + box(b)


def refine_alpha(sr_rgb, alpha_lr, r=13, eps=2e-4, gain=1.35):
    h, w = sr_rgb.shape[:2]
    a = cv2.resize(alpha_lr, (w, h), interpolation=cv2.INTER_CUBIC).clip(0, 1)
    gray = cv2.cvtColor(sr_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    q = guided_filter(gray, a.astype(np.float32), r, eps)
    q = ((q - 0.5) * gain + 0.5).clip(0, 1)
    # never grow outside a slightly dilated version of the original matte
    hull = cv2.dilate((a > 0.02).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
    return q * hull


def decontaminate(rgb, alpha, sigma=5):
    """Replace colours of semi-transparent edge pixels with nearby fully-opaque foreground colours."""
    inner = (alpha > 0.96).astype(np.float32)
    f = rgb.astype(np.float32)
    num = cv2.GaussianBlur(f * inner[..., None], (0, 0), sigma)
    den = cv2.GaussianBlur(inner, (0, 0), sigma)[..., None]
    est = np.where(den > 1e-3, num / np.maximum(den, 1e-3), f)
    w = np.clip((0.96 - alpha) / 0.5, 0, 1)[..., None]
    return (f * (1 - w) + est * w).clip(0, 255).astype(np.uint8)


def detail_transfer(sr_rgb, lr_rgb, amount=0.65):
    """Add back the fine felt texture that SR smoothed away, only where the SR image is flat."""
    h, w = sr_rgb.shape[:2]
    bic = cv2.resize(lr_rgb, (w, h), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    detail = bic - cv2.GaussianBlur(bic, (0, 0), 2.2)
    g = cv2.cvtColor(sr_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    grad = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
    flat = np.exp(-cv2.GaussianBlur(grad, (0, 0), 3) / 40.0)[..., None]
    return (sr_rgb.astype(np.float32) + amount * detail * flat).clip(0, 255).astype(np.uint8)


def save(rgb, alpha, name, scale=0.5, pad=8):
    rgba = np.dstack([rgb, (alpha * 255 + 0.5).astype(np.uint8)])
    im = Image.fromarray(rgba, "RGBA")
    if scale != 1:
        # premultiplied resize avoids dark fringes
        pm = np.asarray(im).astype(np.float32)
        pm[..., :3] *= pm[..., 3:4] / 255
        w, h = int(im.width * scale), int(im.height * scale)
        pm = cv2.resize(pm, (w, h), interpolation=cv2.INTER_AREA)
        a = pm[..., 3:4]
        pm[..., :3] = np.where(a > 0, pm[..., :3] * 255 / np.maximum(a, 1e-3), 0)
        im = Image.fromarray(pm.clip(0, 255).astype(np.uint8), "RGBA")
    bb = im.getchannel("A").point(lambda v: 255 if v > 6 else 0).getbbox()
    im = im.crop(bb)
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad))
    out.paste(im, (pad, pad))
    out.save(f"{OUT}/{name}.png")
    print(name, out.size)
    return out


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    cover = np.asarray(Image.open(f"{work}/cover.png").convert("RGB"))
    matte = np.asarray(Image.open(f"{work}/piku_isnet-general-use.png").convert("RGBA"))[..., 3].astype(np.float32) / 255
    H, W = matte.shape

    # ---------- Piku ----------
    x0, y0, x1, y1 = 340, 430, 870, 1080
    sr = np.asarray(Image.open(f"{work}/sr/piku_x4.png").convert("RGB"))
    a = matte[y0:y1, x0:x1].copy()
    # floor reflection between the shoes (same polygon as cutouts.py, in crop coords)
    gap = Image.new("L", ((x1 - x0) * 4, (y1 - y0) * 4), 0)
    poly = [(582, 957), (600, 962), (620, 966), (644, 957), (651, 985), (653, 1066), (573, 1066), (572, 1000), (577, 975)]
    ImageDraw.Draw(gap).polygon([((x - x0) * 4, (y - y0) * 4) for x, y in poly], fill=255)
    gap = np.asarray(gap).astype(np.float32) / 255
    a[1062 - y0:] = 0
    n, lab, stats, _ = cv2.connectedComponentsWithStats((a > 0.25).astype(np.uint8))
    keep = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    a *= cv2.dilate((lab == keep).astype(np.uint8), np.ones((5, 5), np.uint8))
    alpha = refine_alpha(sr, a) * (1 - gap)
    rgb = detail_transfer(sr, cover[y0:y1, x0:x1])
    rgb = decontaminate(rgb, alpha)
    save(rgb, alpha, "piku")

    # ---------- logo + title ----------
    x0, y0, x1, y1 = 80, 80, 1170, 440
    sr = np.asarray(Image.open(f"{work}/sr/logo_title_x4.png").convert("RGB"))
    a = matte[y0:y1, x0:x1].copy()
    # fill the HALLOWEEN pill (the model made its letters transparent)
    pill = (a > 0.4).astype(np.uint8)
    pill[: 200 - y0] = 0; pill[262 - y0:] = 0; pill[:, : 470 - x0] = 0; pill[:, 740 - x0:] = 0
    cnts, _ = cv2.findContours(pill, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    fill = np.zeros_like(pill)
    cv2.drawContours(fill, [max(cnts, key=cv2.contourArea)], -1, 1, -1)
    a = np.maximum(a, cv2.erode(fill, np.ones((3, 3), np.uint8)).astype(np.float32))
    alpha = refine_alpha(sr, a, r=11, eps=1e-4, gain=1.25)
    rgb = decontaminate(sr, alpha, sigma=4)
    split = (272 - y0) * 4  # logo above, title below
    la = alpha.copy(); la[split:] = 0
    ta = alpha.copy(); ta[:split] = 0
    save(rgb, la, "logo")
    save(rgb, ta, "title")
    # bat (left one in the logo)
    ba = alpha.copy(); ba[: (190 - y0) * 4] = 0; ba[(268 - y0) * 4:] = 0; ba[:, : (370 - x0) * 4] = 0; ba[:, (480 - x0) * 4:] = 0
    n, lab, stats, _ = cv2.connectedComponentsWithStats((ba > 0.3).astype(np.uint8))
    keep = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    ba *= cv2.dilate((lab == keep).astype(np.uint8), np.ones((7, 7), np.uint8))
    save(rgb, ba, "bat")

    # ---------- Pepero box (geometric quad, from the store picture) ----------
    x0, y0 = 50, 540
    sr = np.asarray(Image.open(f"{work}/sr/pepero_x4.png").convert("RGB"))
    quad = [(62.7, 559.3), (172.3, 555.3), (171.0, 749.0), (60.7, 744.3)]
    S = 4
    m = Image.new("L", (sr.shape[1] * S, sr.shape[0] * S), 0)
    ImageDraw.Draw(m).polygon([((x - x0) * 4 * S, (y - y0) * 4 * S) for x, y in quad], fill=255)
    m = np.asarray(m.resize((sr.shape[1], sr.shape[0]), Image.LANCZOS)).astype(np.float32) / 255
    save(sr, m, "pepero", scale=0.75)

    # ---------- store photo at 2x ----------
    st = Image.open(f"{work}/sr/store_x4.png").convert("RGB")
    st.resize((st.width // 2, st.height // 2), Image.LANCZOS).save(f"{OUT}/store_2x.png")
    print("store_2x", st.width // 2)


if __name__ == "__main__":
    main()
