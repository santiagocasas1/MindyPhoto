#!/usr/bin/env python3
"""Per-frame change between consecutive rendered PNGs (before encode/grain).
Flags jumps (sudden large change outside scripted cuts) and confirms the final hold is static.
Usage: python3 tools/frame_diff.py out/frames_1080"""
import sys, pathlib
import numpy as np
from PIL import Image

d = pathlib.Path(sys.argv[1])
files = sorted(d.glob("element-*.png"))
prev = None
diffs = []
for f in files:
    im = np.asarray(Image.open(f).convert("L").resize((270, 480)), dtype=np.float32)
    if prev is not None:
        diffs.append(float(np.abs(im - prev).mean()))
    prev = im
diffs = np.array(diffs)
print(f"frames {len(files)}  mean change {diffs.mean():.2f}  median {np.median(diffs):.2f}")
thr = max(6.0, np.median(diffs) * 6)
for i, v in enumerate(diffs):
    if v > thr:
        print(f"  big change into frame {i+1} (t={(i+1)/30:.2f}s): {v:.1f}")
hold = diffs[int(28.4 * 30):]
print(f"final hold 28.4-30.0s: max frame-to-frame change {hold.max():.3f} (0 = perfectly static)")
