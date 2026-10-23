"""Winner clip: Piku catches a Pepero box — "¡GANASTE!" (7.5 s, 1080x1920) to send by DM.

Usage:
  python3 render_winner.py out.mp4 music.wav
  python3 render_winner.py --stills 1.0,2.0 outdir
"""
import math
import os
import subprocess
import sys
from PIL import Image, ImageDraw

import render_main as rm
from gfx import *  # noqa: F401,F403

DUR = 4 * BAR  # 7.5 s
PEPERO = load("pepero.png")
GANASTE = styled_text(["¡GANASTE!"], 178, fill=YELLOW, max_width=1000)
SUB = styled_text(["¡Encontraste las 3 Pepero!"], 70, max_width=990)
RET = styled_text(["Retirá tu premio el", ("sábado 31/10 en Pika", YELLOW)], 66, max_width=990)
HANDLE = rm.HANDLE

# Piku's raised fist, in piku.png pixels, and the sprite's anchor (bottom centre)
FIST = (455, 272)
ANCHOR = (rm.PIKU.width / 2, rm.PIKU.height)
CATCH = 3 * BEAT  # box lands in the fist on beat 3


def sunburst(size=1500, rays=18):
    big = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = size / 2
    for i in range(rays):
        a0 = 2 * math.pi * i / rays
        a1 = a0 + math.pi / rays
        d.polygon([(c, c), (c + c * 1.5 * math.cos(a0), c + c * 1.5 * math.sin(a0)),
                   (c + c * 1.5 * math.cos(a1), c + c * 1.5 * math.sin(a1))], fill=(255, 214, 140, 70))
    yy, xx = np.mgrid[0:size, 0:size]
    fade = np.clip(1 - np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c, 0, 1) ** 1.2
    a = np.asarray(big.getchannel("A")).astype(np.float32) * fade
    big.putalpha(Image.fromarray(a.astype(np.uint8)))
    return big


RAYS = sunburst()


def fist_world(x, y, s, sx, sy, rot):
    lx = (FIST[0] - ANCHOR[0]) * s * sx
    ly = (FIST[1] - ANCHOR[1]) * s * sy
    th = math.radians(rot)
    return x + lx * math.cos(th) + ly * math.sin(th), y - lx * math.sin(th) + ly * math.cos(th)


def frame(t):
    c = bg_frame(rm.BG, t).copy()
    rm.particles(c, t)
    # rays behind Piku once he has the box
    ra = ease_out_cubic(prog(t, CATCH, 0.4))
    if ra:
        place(c, RAYS, 540, 1000, scale=0.6 + 0.4 * ra, rot=-t * 25, alpha=ra)
    # candy rain after the catch
    for q in rm.CONFETTI:
        tt = t - CATCH - q["delay"] * 0.5
        if tt < 0:
            continue
        y = -60 + q["sp"] * tt
        if y > H + 80:
            continue
        x = q["x"] + q["sway"] * math.sin(tt * 3 + q["rot0"])
        k = q["kind"]
        spr = rm.CANDIES[k] if k < len(rm.CANDIES) else rm.STARS[k - len(rm.CANDIES)]
        place(c, spr, x, y, scale=q["sc"], rot=q["rot0"] + q["vr"] * tt)
    rm.bat(c, t, 0.3, 3.4, 560, 1, 1.2)
    rm.bat(c, t, 3.2, 7.2, 820, -1, 1.0, 40)

    final = 3 * BAR
    hit = 1 + 0.07 * max(0.0, 1 - (t - final) / 0.3) if t >= final else 1.0
    # Piku: jump in, then dance; squash when he catches the box
    feet, s = 1330, 1.12 * hit
    if t < 0.45:
        p = ease_out_back(prog(t, 0.0, 0.45), 1.4)
        x, y, sx, sy, rot = 540, 2500 + (feet - 2500) * p, 1, 1, -14 * (1 - p)
    else:
        hop, sx, sy, rot = rm.piku_dance(t, amp=30 if t < final else 44, sway=4)
        land = max(0.0, 1 - (t - 0.45) / 0.18)
        catch = max(0.0, 1 - (t - CATCH) / 0.2) if t >= CATCH else 0.0
        sx += 0.10 * land + 0.06 * catch
        sy -= 0.14 * land + 0.08 * catch
        x, y = 540, feet + hop
    # the box: falls spinning, then stays in the fist (drawn first so the fist covers it)
    fx, fy = fist_world(x, y, s, sx, sy, rot)
    box_s = 0.7 * hit
    if t >= CATCH:
        pop = 1 + 0.12 * max(0.0, 1 - (t - CATCH) / 0.25)
        tilt = -14 + rot + 4 * math.sin(t * 5)
        place(c, PEPERO, fx + 10, fy + 36, scale=box_s * pop, rot=tilt, anchor=(0.5, 1.0))
    elif t >= 2 * BEAT:
        p = prog(t, 2 * BEAT, CATCH - 2 * BEAT)
        by = -300 + (fy + 36 + 300) * p * p
        bx = 700 + (fx + 10 - 700) * p
        place(c, PEPERO, bx, by, scale=box_s, rot=-14 + 540 * (1 - p), anchor=(0.5, 1.0))
    place(c, rm.PIKU, x, y, scale=s, sx=sx, sy=sy, rot=rot, anchor=(0.5, 1.0))

    sc, a = rm.stamp(t, BEAT, 0.3, 2.2)
    if sc:
        place(c, GANASTE, 540, 300, scale=sc * rm.bar_pulse(t, BAR, 0.05) * hit, rot=-3, alpha=a)
    sc = pop_in(t, BAR, 0.4)
    if sc:
        place(c, SUB, 540, 470, scale=sc)
    sc = pop_in(t, BAR + 2 * BEAT, 0.4)
    if sc:
        place(c, RET, 540, 1470, scale=sc * hit)
    sc = pop_in(t, 2 * BAR, 0.4)
    if sc:
        place(c, HANDLE, 540, 1650, scale=sc * (1 + 0.04 * math.sin(t * 6)))
    if 0 <= t - CATCH < 0.12:
        c.alpha_composite(Image.new("RGBA", (W, H), (255, 236, 210, int(90 * (1 - (t - CATCH) / 0.12)))))
    return c.convert("RGB")


def main():
    if sys.argv[1] == "--stills":
        os.makedirs(sys.argv[3], exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(",")]:
            frame(t).save(os.path.join(sys.argv[3], f"w_{t:05.2f}.png"))
        return
    out, wav = sys.argv[1], sys.argv[2]
    n = int(round(DUR * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-level", "4.2", "-g", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-t", f"{DUR:.3f}", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    print("done", out)


if __name__ == "__main__":
    main()
