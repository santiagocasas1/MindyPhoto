"""Cut Piku, the PIKA HALLOWEEN logo, the title and a bat out of the cover post."""
import sys
import numpy as np, cv2
from PIL import Image, ImageDraw

work = sys.argv[1]
cut = np.asarray(Image.open(f"{work}/piku_isnet-general-use.png").convert("RGBA")).copy()
H, W = cut.shape[:2]


def save_trim(arr, name, pad=6):
    a = arr.copy()
    a[..., 3][a[..., 3] < 18] = 0
    ys, xs = np.nonzero(a[..., 3])
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    im = Image.fromarray(a[y0:y1, x0:x1])
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad))
    out.paste(im, (pad, pad))
    out.save(f"{work}/assets/{name}.png")
    print(name, out.size, (x0, y0, x1, y1))


# Piku: rows below the title; remove the floor reflection between and under the shoes
piku = cut.copy()
piku[:440] = 0
alpha = piku[..., 3].astype(float)
yy, xx = np.mgrid[0:H, 0:W]
gap = Image.new("L", (W * 4, H * 4), 0)
poly = [(582, 957), (600, 962), (620, 966), (644, 957), (651, 985), (653, 1066), (573, 1066), (572, 1000), (577, 975)]
ImageDraw.Draw(gap).polygon([(x * 4, y * 4) for x, y in poly], fill=255)
gap = np.asarray(gap.resize((W, H), Image.LANCZOS)).astype(float) / 255
alpha *= 1 - gap
alpha[yy > 1062] = 0
# keep only the biggest connected blob (drops stray specks)
n, lab, stats, _ = cv2.connectedComponentsWithStats((alpha > 60).astype(np.uint8))
keep = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
blob = cv2.dilate((lab == keep).astype(np.uint8), np.ones((9, 9), np.uint8))
alpha *= blob
piku[..., 3] = alpha.astype(np.uint8)
save_trim(piku, "piku")

# Logo (PIKA + HALLOWEEN + bats + dashes) and title (DULCE O PIKU)
logo = cut.copy(); logo[:80] = 0; logo[272:] = 0
# the model left the HALLOWEEN letters transparent: fill the pill solid with the original pixels
cover = np.asarray(Image.open(f"{work}/cover.png").convert("RGB"))
pill = (logo[..., 3] > 100).astype(np.uint8)
pill[:200] = 0; pill[262:] = 0; pill[:, :470] = 0; pill[:, 740:] = 0
cnts, _ = cv2.findContours(pill, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
big = max(cnts, key=cv2.contourArea)
fill = np.zeros_like(pill)
cv2.drawContours(fill, [big], -1, 1, -1)
fill = cv2.erode(fill, np.ones((3, 3), np.uint8)).astype(bool)
logo[fill, :3] = cover[fill]
logo[fill, 3] = 255
save_trim(logo, "logo")
title = cut.copy(); title[:280] = 0; title[440:] = 0
save_trim(title, "title")

# One bat from the logo (left one)
bat = cut.copy(); bat[:190] = 0; bat[270:] = 0; bat[:, :370] = 0; bat[:, 480:] = 0
n, lab, stats, _ = cv2.connectedComponentsWithStats((bat[..., 3] > 40).astype(np.uint8))
keep = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
bat[..., 3] = bat[..., 3] * cv2.dilate((lab == keep).astype(np.uint8), np.ones((5, 5), np.uint8))
save_trim(bat, "bat", pad=2)

# Pepero "Choco Cookie" box from the store picture (for the winner clip)
store = Image.open(f"{work}/store.png").convert("RGB")
S = 4
quad = [(62.7, 559.3), (172.3, 555.3), (171.0, 749.0), (60.7, 744.3)]
m = Image.new("L", (store.width * S, store.height * S), 0)
ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in quad], fill=255)
m = m.resize(store.size, Image.LANCZOS)
box = store.copy().convert("RGBA")
box.putalpha(m)
box = box.crop((55, 550, 180, 755))
from PIL import ImageFilter
box = box.resize((box.width * 2, box.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2.2, 90, 2))
box.save(f"{work}/assets/pepero.png")
print("pepero", box.size)
