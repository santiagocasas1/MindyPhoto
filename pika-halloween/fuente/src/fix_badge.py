import sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

work = sys.argv[1]
BADGES = {"cover": (1048, 39, 1173, 129, 0.50), "steps": (1041, 39, 1173, 129, 0.62), "store": (1041, 39, 1173, 129, 0.62)}

def badge_mask(X0, Y0, X1, Y1, scale=4):
    R = 40
    W, H = 1220 * scale, 1220 * scale
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle((X0*scale, Y0*scale, (X1+1)*scale, (Y1+1)*scale), R*scale, fill=255)
    return np.asarray(m.resize((1220, 1220), Image.LANCZOS)).astype(float) / 255

for name, (x0, y0, x1, y1, k) in BADGES.items():
    m = badge_mask(x0, y0, x1, y1)
    img = np.asarray(Image.open(f"{work}/{name}_raw.png").convert("RGB")).astype(float)
    fixed = img / (1 - k * m[..., None])
    fixed = np.clip(fixed, 0, 255).astype(np.uint8)
    # inpaint the antialiased border ring and any opaque white counter text
    ring = ((m > 0.02) & (m < 0.98)).astype(np.uint8) * 255
    ring = cv2.dilate(ring, np.ones((5, 5), np.uint8))
    lum = img.mean(axis=2)
    inside = m > 0.5
    txt = (inside & (lum > 150)).astype(np.uint8) * 255
    txt[:, :1060] = 0; txt[:, 1165:] = 0; txt[:60] = 0; txt[112:] = 0
    txt = cv2.dilate(txt, np.ones((7, 7), np.uint8))
    hole = cv2.bitwise_or(ring, txt)
    out = cv2.inpaint(cv2.cvtColor(fixed, cv2.COLOR_RGB2BGR), hole, 6, cv2.INPAINT_TELEA)
    out = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    Image.fromarray(out).save(f"{work}/{name}.png")
    Image.fromarray(out).crop((980, 0, 1220, 200)).resize((480, 400)).save(f"{work}/{name}_badge_fixed.png")
print("done")
