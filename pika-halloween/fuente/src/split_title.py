"""Split the 'DULCE O PIKU' title cutout into one sprite per letter (plus the side dashes).

Each letter's cream face is a separate blob; every other opaque pixel (outline, orange extrusion)
is given to the nearest face, measured from a face mask shifted along the extrusion direction.
Output: assets_hr/title_parts/*.png and parts.json with each part's top-left in title coords.
"""
import json
import os
import sys
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage

work = sys.argv[1]
src = np.asarray(Image.open(f"{work}/assets_hr/title.png").convert("RGBA"))
a = src[..., 3].astype(np.float32) / 255
rgb = src[..., :3].astype(np.int32)
face = (rgb[..., 0] > 200) & (rgb[..., 1] > 185) & (rgb[..., 2] > 150) & (a > 0.6)
face = cv2.morphologyEx(face.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, lab, stats, _ = cv2.connectedComponentsWithStats(face)
letters = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > 2500]
letters.sort(key=lambda i: stats[i, cv2.CC_STAT_LEFT])
print("faces:", len(letters))

# shift faces down-right a little (the extrusion direction) before the nearest-face assignment
seed = np.zeros_like(lab)
for k, i in enumerate(letters, start=1):
    m = (lab == i).astype(np.uint8)
    m = np.maximum(m, np.roll(np.roll(m, 10, axis=0), 3, axis=1))
    seed[m > 0] = k
_, (iy, ix) = ndimage.distance_transform_edt(seed == 0, return_indices=True)
owner = seed[iy, ix]

# the orange side dashes are their own blobs: give them labels too
opaque = (a > 0.02).astype(np.uint8)
n2, lab2, stats2, _ = cv2.connectedComponentsWithStats((a > 0.3).astype(np.uint8))
dash_label = {}
for j in range(1, n2):
    x, y, w, h, area = stats2[j]
    if area < 8000:  # dashes are small blobs at both ends
        side = "dashL" if x < src.shape[1] / 2 else "dashR"
        dash_label.setdefault(side, []).append(j)
names = list("DULCEOPIKU")
os.makedirs(f"{work}/assets_hr/title_parts", exist_ok=True)
parts = []


def save_part(mask, name):
    alpha = (a * mask).astype(np.float32)
    ys, xs = np.nonzero(alpha > 0.01)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = src[y0:y1, x0:x1].copy()
    rgba[..., 3] = (alpha[y0:y1, x0:x1] * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(f"{work}/assets_hr/title_parts/{name}.png")
    parts.append(dict(name=name, x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0)))


dash_px = np.zeros(a.shape, bool)
for side, js in dash_label.items():
    m = np.isin(lab2, js)
    m = cv2.dilate(m.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    dash_px |= m
    save_part(m.astype(np.float32), side)
for k, nm in enumerate(names, start=1):
    m = ((owner == k) & ~dash_px).astype(np.float32)
    save_part(m, f"{k:02d}_{nm}")
json.dump(dict(size=[src.shape[1], src.shape[0]], parts=parts), open(f"{work}/assets_hr/title_parts/parts.json", "w"), indent=1)
print([p["name"] for p in parts])
