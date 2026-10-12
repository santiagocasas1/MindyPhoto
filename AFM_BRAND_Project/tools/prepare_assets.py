#!/usr/bin/env python3
"""Download the original AFM BRAND logo + catalog photos from afmbrand.com.ar and
produce clean product cut-outs (alpha) for the commercial.

Nothing is redrawn or generated: the logo is copied byte-for-byte and the product
photos are the store's own catalog packshots, only background-removed (rembg),
trimmed and saved as WebP with alpha.

Usage:  python3 tools/prepare_assets.py   (needs: pip install "rembg[cpu]" pillow)
"""
import io, json, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUB = ROOT / "public" / "assets"
CACHE = ROOT / "tools" / ".cache"
LOGO_URL = ("https://acdn-us.mitiendanube.com/stores/006/238/130/themes/common/"
            "logo-8762369692423002390-1778183517-d5ef35bdb744a97a99eb3c05b20586321778183517.png")
UA = {"User-Agent": "Mozilla/5.0"}


def split_logo(trim):
    """Split the ORIGINAL logo pixels into two exact, complementary layers (red dome / black
    lettering) so each can be revealed with its own mask. Composited, they reproduce the
    original byte-for-byte (checked below); no pixel is recoloured or redrawn."""
    import numpy as np
    from PIL import Image
    a = np.asarray(trim).astype(np.int32)
    red = (a[..., 0] - np.maximum(a[..., 1], a[..., 2])) > 60
    red_l = a.copy(); red_l[~red, 3] = 0
    ink_l = a.copy(); ink_l[red, 3] = 0
    Image.fromarray(red_l.astype(np.uint8)).save(PUB / "brand" / "afm_logo_layer_red.png")
    Image.fromarray(ink_l.astype(np.uint8)).save(PUB / "brand" / "afm_logo_layer_ink.png")
    back = Image.alpha_composite(Image.fromarray(ink_l.astype(np.uint8)), Image.fromarray(red_l.astype(np.uint8)))
    diff = np.abs(np.asarray(back).astype(np.int32) - a)
    # pixels are disjoint, so the recombination must match exactly wherever alpha > 0
    assert diff[a[..., 3] > 0].max() == 0, "logo split is not lossless"
    print("logo layers ok: red px", int(red.sum()), "ink px", int((~red & (a[..., 3] > 0)).sum()))


def fetch(url: str, dest: pathlib.Path) -> pathlib.Path:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            dest.write_bytes(r.read())
    return dest


# How each packshot's mask is cleaned up after rembg:
#  hull  -> cans are convex: use the convex hull of the subject (keeps clear/white can parts)
#  fill  -> fill enclosed holes (white lettering on boxes)
#  rows  -> clear PET cans (OKF): per row, fill between the outermost non-white pixels
#  plain -> rembg mask as-is (bottles: necks are concave, hull would add background)
STRATEGY = {"okf": "rows", "milkis": "hull", "htb": "hull", "pepero": "fill", "soonhari": "fill", "saero": "fill"}


def refine(src, cut, strategy):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    from scipy import ndimage
    if strategy == "plain":
        return cut
    rgb = np.asarray(src).astype(np.int16)
    alpha = np.asarray(cut.getchannel("A"))
    # anything clearly darker/more saturated than the white studio sweep is product
    nonwhite = (rgb.min(axis=2) < 232) | ((rgb.max(axis=2) - rgb.min(axis=2)) > 18)
    nonwhite = ndimage.binary_opening(nonwhite, iterations=2)
    mask = (alpha > 127) | (nonwhite & ndimage.binary_dilation(alpha > 127, iterations=25))
    lab, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        mask = lab == (1 + int(np.argmax(sizes)))
    if strategy == "rows":
        g = ndimage.median_filter(rgb.min(axis=2), size=5)
        ink = (g < 246) | (alpha > 127)
        ink = ndimage.binary_opening(ink, iterations=1)
        H, W = ink.shape
        left = np.full(H, -1.0); right = np.full(H, -1.0)
        for y in range(H):
            xs = np.flatnonzero(ink[y])
            if xs.size > 3:
                left[y], right[y] = xs[0], xs[-1]
        rows = np.flatnonzero(left >= 0)
        y0, y1 = rows[0], rows[-1]
        idx = np.arange(y0, y1 + 1)
        L = np.interp(idx, rows, left[rows]); R = np.interp(idx, rows, right[rows])
        L = ndimage.median_filter(L, size=15); R = ndimage.median_filter(R, size=15)
        L = ndimage.gaussian_filter1d(L, 2.0); R = ndimage.gaussian_filter1d(R, 2.0)
        S = 4
        big = Image.new("L", (W * S, H * S), 0)
        poly = [(float(L[i]) * S, float(idx[i]) * S) for i in range(len(idx))] + \
               [(float(R[i]) * S + S, float(idx[i]) * S) for i in range(len(idx) - 1, -1, -1)]
        ImageDraw.Draw(big).polygon(poly, fill=255)
        a = np.asarray(big.resize((W, H), Image.LANCZOS).filter(ImageFilter.MinFilter(3)))
    elif strategy == "fill":
        mask = ndimage.binary_fill_holes(mask)
        soft = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
        a = np.maximum(np.asarray(soft), alpha * mask)
    else:
        from scipy.spatial import ConvexHull
        ys, xs = np.nonzero(mask)
        pts = np.stack([xs, ys], 1)
        hull = pts[ConvexHull(pts).vertices]
        S = 4
        big = Image.new("L", (src.width * S, src.height * S), 0)
        ImageDraw.Draw(big).polygon([(float(x) * S + S / 2, float(y) * S + S / 2) for x, y in hull], fill=255)
        hm = np.asarray(big.resize(src.size, Image.LANCZOS))
        # erode 1px so the white sweep never shows as a halo
        a = np.asarray(Image.fromarray(hm).filter(ImageFilter.MinFilter(3)))
    out = src.convert("RGBA")
    out.putalpha(Image.fromarray(a.astype(np.uint8)))
    return out


def main() -> None:
    from PIL import Image
    from rembg import remove, new_session

    # 1) Logo: original file untouched + a copy cropped to its transparent bounding box.
    logo = fetch(LOGO_URL, PUB / "brand" / "afm_logo_original.png")
    im = Image.open(logo).convert("RGBA")
    bbox = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    pad = 24
    box = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.width), min(bbox[3] + pad, im.height))
    trim = im.crop(box)
    trim.save(PUB / "brand" / "afm_logo_trim.png")
    print("logo", im.size, "->", box)
    split_logo(trim)

    # Real store banner photo (used in the in-phone home screen)
    fetch("https://acdn-us.mitiendanube.com/stores/006/238/130/themes/brasilia/"
          "2-slide-1778095130717-1263111743-464a79354f89359cf656bcf6dc7b37cf1778095132-1024-1024.webp",
          PUB / "site" / "banner_okf.webp")

    # 2) Products: catalog packshots -> alpha cut-outs.
    manifest = json.loads((ROOT / "config" / "products.json").read_text())
    session = new_session("isnet-general-use")
    for p in manifest["products"]:
        raw = fetch(p["image"], CACHE / f"{p['brandKey']}_{p['sku']}.png")
        ui = PUB / "ui" / f"{p['brandKey']}_{p['sku']}.webp"
        if not ui.exists():  # untouched packshot on its white sweep, for the in-phone store UI
            ui.parent.mkdir(parents=True, exist_ok=True)
            Image.open(raw).convert("RGB").resize((720, 720), Image.LANCZOS).save(ui, "WEBP", quality=90, method=6)
        p["ui"] = f"ui/{p['brandKey']}_{p['sku']}.webp"
        out = PUB / p["file"]
        if out.exists():
            continue
        src = Image.open(raw).convert("RGB")
        cut = remove(src, session=session, post_process_mask=True)
        cut = refine(src, cut, STRATEGY.get(p["brandKey"], "plain"))
        a = cut.getchannel("A")
        bb = a.point(lambda v: 255 if v > 10 else 0).getbbox()
        m = 12
        cut = cut.crop((max(bb[0] - m, 0), max(bb[1] - m, 0), min(bb[2] + m, cut.width), min(bb[3] + m, cut.height)))
        out.parent.mkdir(parents=True, exist_ok=True)
        cut.save(out, "WEBP", quality=92, method=6)
        p["size"] = list(cut.size)
        print("cut", p["sku"], cut.size)
    for p in manifest["products"]:
        if "size" not in p:
            p["size"] = list(Image.open(PUB / p["file"]).size)
    (ROOT / "config" / "products.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
