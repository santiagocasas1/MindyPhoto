"""'Living photo': 2.5D parallax of the store picture driven by an AI depth map
(Depth Anything V2 Small), plus flickering jack-o'-lantern light.
"""
import math
import numpy as np
import cv2
from PIL import Image


class LivingPhoto:
    def __init__(self, img_path, depth_path, work=1320):
        img = Image.open(img_path).convert("RGB").resize((work, work), Image.LANCZOS)
        self.img = np.asarray(img).astype(np.float32) / 255
        d = np.asarray(Image.open(depth_path)).astype(np.float32) / 65535
        d = cv2.resize(d, (work, work), interpolation=cv2.INTER_CUBIC)
        # grow near objects a little so their silhouettes stay solid and the background stretches instead
        d = cv2.dilate(d, np.ones((9, 9), np.uint8))
        self.depth = cv2.GaussianBlur(d, (0, 0), 3)
        self.n = work
        yy, xx = np.mgrid[0:work, 0:work].astype(np.float32)
        self.xx, self.yy = xx, yy
        # glowing pumpkin faces / warm bulbs: bright, saturated orange-yellow pixels
        r, g, b = self.img[..., 0], self.img[..., 1], self.img[..., 2]
        glow = np.clip((r - 0.75) * 4, 0, 1) * np.clip((g - 0.45) * 3, 0, 1) * np.clip((0.55 - b) * 3, 0, 1)
        self.glow = cv2.GaussianBlur(glow.astype(np.float32), (0, 0), 2.5)[..., None]
        self.halo = cv2.GaussianBlur(glow.astype(np.float32), (0, 0), 18)[..., None]

    def render(self, t, out_size, cam=(0.0, 0.0), zoom=1.0, amp=1.0, return_full=False):
        """cam: camera offset in [-1, 1]; returns an RGB float32 image (out_size x out_size)."""
        n = self.n
        c = n / 2
        sx = float(cam[0] * 16 * amp)
        sy = float(cam[1] * 10 * amp)
        zoom = float(zoom)
        d0 = 0.35
        # two fixed-point iterations of the backward parallax mapping
        px = c + (self.xx - c) / zoom
        py = c + (self.yy - c) / zoom
        qx, qy = px, py
        for _ in range(2):
            dd = cv2.remap(self.depth, qx, qy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            qx = (px - sx * (dd - d0)).astype(np.float32)
            qy = (py - sy * (dd - d0)).astype(np.float32)
        out = cv2.remap(self.img, qx.astype(np.float32), qy.astype(np.float32), cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT)
        # lantern flicker (deterministic "noise" from a few sines)
        fl = 0.5 + 0.5 * (0.6 * math.sin(t * 17.0) + 0.3 * math.sin(t * 29.0 + 1.3) + 0.1 * math.sin(t * 53.0 + 0.4))
        glow = cv2.remap(self.glow, qx.astype(np.float32), qy.astype(np.float32), cv2.INTER_LINEAR)[..., None]
        halo = cv2.remap(self.halo, qx.astype(np.float32), qy.astype(np.float32), cv2.INTER_LINEAR)[..., None]
        warm = np.array([1.0, 0.62, 0.22], np.float32)
        out = out * (1 + 0.28 * fl * glow) + warm * halo * (0.10 + 0.12 * fl)
        out = np.clip(out, 0, 1)
        small = cv2.resize(out, (out_size, out_size), interpolation=cv2.INTER_AREA)
        return (small, out) if return_full else small
