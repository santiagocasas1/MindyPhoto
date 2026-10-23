"""2D puppet rig for Piku (linear-blend skinning on the high-res cutout).

Bones, each a rotation around a pivot with a soft weight map (so joints bend, nothing tears):
  lean  - upper body sways around the hips
  arm   - the raised fist waves around the shoulder
  bag   - the shoulder bag swings a little (follow-through)
plus a travelling-wave flutter on the cape hems and an eye blink.
All coordinates are in pixels of assets_hr/piku.png (990 x 1229).
"""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw

HIPS = (485.0, 1000.0)
SHOULDER = (790.0, 700.0)
BAG_PIVOT = (520.0, 800.0)
EYE_C, EYE_R = (684.0, 434.0), (36.0, 52.0)
ARM_POLY = [(810, 525), (820, 492), (845, 472), (880, 463), (915, 466), (945, 476), (990, 466), (990, 600),
            (960, 622), (920, 672), (880, 702), (840, 724), (800, 737), (772, 746), (788, 690), (798, 620),
            (804, 565)]
FIST = (900.0, 545.0)
BAG_POLY = [(300, 760), (540, 735), (548, 995), (300, 1000)]


def _soft_poly(shape, poly, feather):
    h, w = shape
    m = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(m).polygon([(x * 2, y * 2) for x, y in poly], fill=255)
    m = np.asarray(m.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255
    return cv2.GaussianBlur(m, (0, 0), feather) if feather else m


def _smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


class PikuRig:
    def __init__(self, path):
        src = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255
        self.h, self.w = src.shape[:2]
        prem = src.copy()
        prem[..., :3] *= prem[..., 3:4]
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.xx, self.yy = xx, yy

        # ---- eye: inpaint it away for the base, keep the original pixels as a layer ----
        ex, ey = EYE_C
        rx, ry = EYE_R
        ell = (((xx - ex) / rx) ** 2 + ((yy - ey) / ry) ** 2)
        eye_mask = np.clip((1.12 - ell) / 0.24, 0, 1).astype(np.float32)
        rgb8 = (src[..., :3] * 255).astype(np.uint8)
        hole = (ell < 1.25).astype(np.uint8) * 255
        filled = cv2.inpaint(cv2.cvtColor(rgb8, cv2.COLOR_RGB2BGR), hole, 9, cv2.INPAINT_TELEA)
        filled = cv2.cvtColor(filled, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        # soften the inpainted patch so it reads as smooth felt
        blur = cv2.GaussianBlur(filled, (0, 0), 3)
        k = (ell < 1.4).astype(np.float32)[..., None]
        filled = filled * (1 - k) + blur * k
        base = prem.copy()
        base[..., :3] = filled * src[..., 3:4]
        self.base = base
        y0, y1 = int(ey - ry * 1.3), int(ey + ry * 1.3)
        x0, x1 = int(ex - rx * 1.3), int(ex + rx * 1.3)
        self.eye_box = (x0, y0, x1, y1)
        self.eye = prem[y0:y1, x0:x1] * eye_mask[y0:y1, x0:x1, None]

        # ---- skin weights ----
        self.w_lean = (1 - _smoothstep(640, 1010, yy)).astype(np.float32)
        self.w_arm = _soft_poly((self.h, self.w), ARM_POLY, 5)
        self.w_bag = _soft_poly((self.h, self.w), BAG_POLY, 9) * _smoothstep(740, 860, yy)
        rgb = src[..., :3]
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        sat = (rgb.max(2) - rgb.min(2)) / np.maximum(rgb.max(2), 1e-4)
        purple = ((b > g + 0.08) & (r > g + 0.02) & (sat > 0.3) & (src[..., 3] > 0.5)).astype(np.uint8)
        flaps = np.zeros_like(purple)
        flaps[700:1010, :300] = 1
        flaps[720:1000, 760:] = 1
        cape = purple * flaps
        near = cv2.dilate(cape, np.ones((31, 31), np.uint8)) * (src[..., 3] < 0.5)
        wc = cv2.GaussianBlur(np.maximum(cape, near).astype(np.float32), (0, 0), 6)
        self.w_cape = wc * _smoothstep(760, 960, yy)
        self.side = np.where(xx < self.w / 2, -1.0, 1.0).astype(np.float32)
        # deformation maps are smooth: compute them at half resolution and upsample
        half = lambda a: cv2.resize(a, (self.w // 2, self.h // 2), interpolation=cv2.INTER_AREA)
        self.hx, self.hy = half(xx), half(yy)
        self.hw_lean, self.hw_arm, self.hw_bag = half(self.w_lean), half(self.w_arm), half(self.w_bag)
        self.hw_cape, self.hside = half(self.w_cape), half(self.side)

    @staticmethod
    def _rot_back(px, py, pivot, ang):
        """Inverse rotation (per-pixel angle in radians) of points around a pivot."""
        c, s = np.cos(-ang), np.sin(-ang)
        dx, dy = px - pivot[0], py - pivot[1]
        # visual CCW rotation in image coords (y down): x' = dx*c + dy*s ; y' = -dx*s + dy*c
        return pivot[0] + dx * c + dy * s, pivot[1] - dx * s + dy * c

    def pose(self, arm=0.0, lean=0.0, bag=0.0, cape_t=0.0, cape_amp=1.0, blink=0.0):
        """Angles in degrees (positive = counter-clockwise on screen). Returns a PIL RGBA image."""
        src = self.base.copy()
        x0, y0, x1, y1 = self.eye_box
        eh, ew = self.eye.shape[:2]
        if blink < 0.98:
            k = 1 - 0.9 * blink
            nh = max(2, int(round(eh * k)))
            sq = cv2.resize(self.eye, (ew, nh), interpolation=cv2.INTER_AREA)
            cy = int(round((eh - nh) * 0.6))
            reg = src[y0 + cy:y0 + cy + nh, x0:x1]
            src[y0 + cy:y0 + cy + nh, x0:x1] = sq + reg * (1 - sq[..., 3:4])
        else:
            # fully closed: a soft light line where the eye was
            line = np.zeros((eh, ew), np.float32)
            cv2.ellipse(line, (ew // 2, int(eh * 0.62)), (int(ew * 0.38), 5), 0, 0, 180, 1.0, 6, cv2.LINE_AA)
            line = cv2.GaussianBlur(line, (0, 0), 1.2)[..., None]
            col = np.array([0.98, 0.88, 0.9, 1.0], np.float32)
            reg = src[y0:y1, x0:x1]
            src[y0:y1, x0:x1] = col * line + reg * (1 - line)

        px, py = self.hx, self.hy
        # undo the outermost bone first (lean), then the ones that ride on it
        if lean:
            px, py = self._rot_back(px, py, HIPS, math.radians(lean) * self.hw_lean)
        if arm:
            px, py = self._rot_back(px, py, SHOULDER, math.radians(arm) * self.hw_arm)
        if bag:
            px, py = self._rot_back(px, py, BAG_PIVOT, math.radians(bag) * self.hw_bag)
        if cape_amp:
            ph = 2 * math.pi * 2.3 * cape_t
            px = px - 9.0 * np.sin(ph - py * 0.022) * cape_amp * self.hw_cape * self.hside
            py = py - 3.0 * np.cos(ph - py * 0.022) * cape_amp * self.hw_cape
        full = (self.w, self.h)
        mx = cv2.resize(px.astype(np.float32), full, interpolation=cv2.INTER_LINEAR)
        my = cv2.resize(py.astype(np.float32), full, interpolation=cv2.INTER_LINEAR)
        out = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        a = out[..., 3:4]
        rgb = out[..., :3] / np.maximum(a, 1e-4)
        rgba = np.concatenate([rgb, a], axis=2)
        return Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")

    def forward(self, pt, arm=0.0, lean=0.0):
        """Where a rest-pose point (e.g. the fist) ends up for a given pose (sprite pixels)."""
        x, y = pt
        def rot(x, y, piv, ang_deg):
            a = math.radians(ang_deg)
            dx, dy = x - piv[0], y - piv[1]
            return piv[0] + dx * math.cos(a) + dy * math.sin(a), piv[1] - dx * math.sin(a) + dy * math.cos(a)
        wa = float(self.w_arm[int(y), int(x)])
        x, y = rot(x, y, SHOULDER, arm * wa)
        wl = float(self.w_lean[int(min(self.h - 1, max(0, pt[1]))), int(pt[0])])
        return rot(x, y, HIPS, lean * wl)


def dance(t, beat, bar_start=0.0, energy=1.0):
    """Beat-synced pose parameters for the dance loop."""
    u = (t - bar_start) / beat
    arm = 4.5 + 7.5 * energy * math.sin(2 * math.pi * u / 2)          # wave once every 2 beats (-3..12 deg)
    lean = 2.6 * energy * math.sin(2 * math.pi * u / 2 + 0.6)         # sway, lagging the wave a bit
    bag = -2.0 * energy * math.sin(2 * math.pi * u / 2 - 0.9)         # follow-through
    return dict(arm=arm, lean=lean, bag=bag, cape_t=t, cape_amp=0.8 + 0.4 * energy)


def blink_amount(t, times=(1.25, 4.15, 6.85, 9.55, 12.2, 14.4), dur=0.2):
    for t0 in times:
        if t0 <= t < t0 + dur:
            u = (t - t0) / dur
            return math.sin(math.pi * u) ** 0.6
    return 0.0
