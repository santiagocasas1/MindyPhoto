"""AI super-resolution (Real-ESRGAN family, loaded with spandrel) with overlapping tiles.

Usage: python3 sr.py model.pth in.png out.png [--box x0,y0,x1,y1] [--tile 192]
"""
import sys
import time
import numpy as np
import torch
from PIL import Image
from spandrel import ModelLoader

torch.set_num_threads(4)


def upscale(model, img, tile=192, overlap=16):
    """img: HxWx3 float32 [0,1] -> (sH)x(sW)x3, blending tiles with a feathered window."""
    s = model.scale
    h, w, _ = img.shape
    out = np.zeros((h * s, w * s, 3), np.float32)
    acc = np.zeros((h * s, w * s, 1), np.float32)
    step = tile - 2 * overlap
    ys = list(range(0, max(1, h - 2 * overlap), step))
    xs = list(range(0, max(1, w - 2 * overlap), step))
    for y0 in ys:
        for x0 in xs:
            y1, x1 = min(h, y0 + tile), min(w, x0 + tile)
            y0_, x0_ = max(0, y1 - tile), max(0, x1 - tile)
            patch = torch.from_numpy(img[y0_:y1, x0_:x1].transpose(2, 0, 1)).unsqueeze(0)
            with torch.inference_mode():
                res = model(patch).clamp(0, 1)[0].numpy().transpose(1, 2, 0)
            ph, pw = res.shape[:2]
            wy = np.minimum(np.arange(ph) + 1, np.arange(ph)[::-1] + 1).astype(np.float32)
            wx = np.minimum(np.arange(pw) + 1, np.arange(pw)[::-1] + 1).astype(np.float32)
            win = np.minimum(np.minimum(wy[:, None], overlap * s), np.minimum(wx[None, :], overlap * s))[..., None]
            out[y0_ * s:y0_ * s + ph, x0_ * s:x0_ * s + pw] += res * win
            acc[y0_ * s:y0_ * s + ph, x0_ * s:x0_ * s + pw] += win
    return out / np.maximum(acc, 1e-6)


def main():
    mpath, src, dst = sys.argv[1:4]
    tile = int(sys.argv[sys.argv.index("--tile") + 1]) if "--tile" in sys.argv else 192
    im = Image.open(src).convert("RGB")
    if "--box" in sys.argv:
        im = im.crop(tuple(int(v) for v in sys.argv[sys.argv.index("--box") + 1].split(",")))
    model = ModelLoader().load_from_file(mpath).eval()
    t = time.time()
    res = upscale(model, np.asarray(im).astype(np.float32) / 255, tile)
    Image.fromarray((res * 255 + 0.5).astype(np.uint8)).save(dst)
    print(f"{mpath.split('/')[-1]}: {im.size} -> x{model.scale} in {time.time() - t:.1f}s")


if __name__ == "__main__":
    main()
