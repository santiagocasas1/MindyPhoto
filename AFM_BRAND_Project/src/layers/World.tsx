// Everything around the phone: background light, floating products, dust.
import React, { useLayoutEffect, useRef } from "react";
import { Img } from "remotion";
import * as THREE from "three";
import { Rig, projectLocal, project, pxPerMm, W, H, PHONE } from "../lib/choreo";
import { prog, ease, mix, clamp, rgba, noise1, rng, window01, lerpColor } from "../lib/anim";
import { BRANDS, C, PAL, cutout, aspect } from "../lib/data";

// ------------------------------------------------------------ scene tint
/** Colour of the light pool behind the phone; follows the story and each brand. */
export function tintAt(t: number) {
  if (t < 8) return PAL.afmRed;
  if (t < 18) {
    const B = C.brandBeats;
    let c = "#c9c2b8";
    for (let i = 0; i < B.length; i++) {
      const k = prog(t, B[i] - 0.25, B[i] + 0.35, ease.inOut);
      if (k > 0) c = lerpColor(i === 0 ? "#c9c2b8" : BRANDS[i - 1].tint, BRANDS[i].tint, k);
    }
    return lerpColor(c, PAL.afmRed, prog(t, 17.7, 18.3));
  }
  return PAL.afmRed;
}

// Soft-edged beam sprite (horizontal falloff x vertical falloff), built once.
let BEAM: HTMLCanvasElement | null = null;
const beamSprite = () => {
  if (BEAM) return BEAM;
  const c = document.createElement("canvas");
  c.width = 256; c.height = 1024;
  const g = c.getContext("2d")!;
  const hx = g.createLinearGradient(0, 0, 256, 0);
  hx.addColorStop(0, "rgba(255,244,230,0)"); hx.addColorStop(0.38, "rgba(255,244,230,1)");
  hx.addColorStop(0.62, "rgba(255,244,230,1)"); hx.addColorStop(1, "rgba(255,244,230,0)");
  g.fillStyle = hx; g.fillRect(0, 0, 256, 1024);
  g.globalCompositeOperation = "destination-in";
  const vy = g.createLinearGradient(0, 0, 0, 1024);
  vy.addColorStop(0, "rgba(0,0,0,1)"); vy.addColorStop(0.45, "rgba(0,0,0,.32)"); vy.addColorStop(0.8, "rgba(0,0,0,0)");
  g.fillStyle = vy; g.fillRect(0, 0, 256, 1024);
  BEAM = c;
  return c;
};

const ellipseGlow = (g: CanvasRenderingContext2D, cx: number, cy: number, rx: number, ry: number, stops: [number, string][]) => {
  g.save();
  g.translate(cx, cy);
  g.scale(1, ry / rx);
  const r = g.createRadialGradient(0, 0, 0, 0, 0, rx);
  stops.forEach(([o, c]) => r.addColorStop(o, c));
  g.fillStyle = r;
  g.fillRect(-rx, -rx, rx * 2, rx * 2);
  g.restore();
};

/** Background light, drawn in one 2D canvas (additive light, no compositor blend modes). */
export const Background: React.FC<{ rig: Rig }> = ({ rig }) => {
  const ref = useRef<HTMLCanvasElement>(null);
  const t = rig.t;
  useLayoutEffect(() => {
    const cv = ref.current!;
    const dpr = window.devicePixelRatio || 1;
    if (cv.width !== W * dpr) { cv.width = W * dpr; cv.height = H * dpr; }
    const g = cv.getContext("2d")!;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const c = projectLocal(rig, 0, 0, 0);
    const s = pxPerMm(rig, c.depth);
    const tint = tintAt(t);
    const aura = Math.min(1, t < 4 ? mix(0.15, 0.55, prog(t, 0.6, 3.8)) : t < 8 ? 0.85 : 0.75);
    const flash = t >= C.impactReveal ? Math.max(0, 1 - (t - C.impactReveal) / 0.6) : 0;
    const screenGlow = (t > 3.3 && t < 8.2 ? 1 : 0.55) * prog(t, C.screenWake, 1.4);
    const beams = mix(0.35, 1, prog(t, 0.4, 2.5)) * (1 - 0.4 * prog(t, 21.8, 22.3));
    const par = -rig.yaw * 7;
    // base
    g.globalCompositeOperation = "source-over";
    const base = g.createRadialGradient(W * (0.5 + par / 3000), H * 0.38, 0, W * 0.5, H * 0.38, H * 0.75);
    base.addColorStop(0, "#17171c"); base.addColorStop(0.48, "#0c0c0f"); base.addColorStop(1, "#050506");
    g.fillStyle = base;
    g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = "lighter";
    // volumetric beams from a high key light, camera-left
    const spr = beamSprite();
    [0, 1, 2].forEach((i) => {
      g.save();
      g.globalAlpha = 0.16 * beams;
      g.translate(-260 + i * 210 + par * (0.6 + i * 0.2) + (210 - i * 50) / 2, -380);
      g.rotate(((-24 + i * 7) * Math.PI) / 180);
      g.drawImage(spr, -(210 - i * 50) / 2, 0, 210 - i * 50, 2600);
      g.restore();
    });
    // light pool behind the phone, tinted per scene
    ellipseGlow(g, c.x, c.y, 95 * s, 120 * s, [[0, rgba(tint, 0.55 * aura)], [0.42, rgba(tint, 0.18 * aura)], [0.72, rgba(tint, 0)], [1, rgba(tint, 0)]]);
    // screen light spilling into the haze
    ellipseGlow(g, c.x, c.y, 70 * s, 105 * s, [[0, `rgba(255,255,255,${0.10 * screenGlow + 0.35 * flash})`], [0.7, "rgba(255,255,255,0)"], [1, "rgba(255,255,255,0)"]]);
    // floor haze
    ellipseGlow(g, W / 2, c.y + 92 * s, W * 0.6, 130, [[0, rgba(tint, 0.12 * aura)], [0.7, rgba(tint, 0)], [1, rgba(tint, 0)]]);
    g.globalCompositeOperation = "source-over";
  });
  return <canvas ref={ref} style={{ position: "absolute", inset: 0, width: W, height: H }} />;
};

// ------------------------------------------------------------ products
const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);
const heroHeight = (key: string) => (key === "soonhari" || key === "saero" ? 92 : key === "pepero" ? 70 : 74);
const heroX = (key: string) => (key === "pepero" ? 50 : 56);

type Obj = { key: string; src: string; ar: number; p: THREE.Vector3; hMm: number; roll: number; ry: number; alpha: number; dof: boolean; tint: string; sweep: number; dim: number };

function productsAt(rig: Rig): Obj[] {
  const t = rig.t;
  const out: Obj[] = [];
  const B = C.brandBeats;
  BRANDS.forEach((b, i) => {
    const t0 = B[i];
    const side = b.side;
    const next = i < B.length - 1 ? B[i + 1] : 17.75;
    const bob = V(noise1(t * 0.7, i) * 2.5, noise1(t * 0.6, i + 9) * 3.5, 0);
    // display point where the product sits in the on-screen product page
    const start = V(0, 37, PHONE.t / 2 + 1).applyMatrix4(rig.phone);
    if (t >= t0 && t < next + 0.5) {
      const e = prog(t, t0 + 0.06, t0 + 0.6, ease.out);
      const x = prog(t, next - 0.12, next + 0.42, ease.in);
      const end = V(side * heroX(b.key), 18, 46);
      let p = start.clone().lerp(end, e).add(V(0, 0, Math.sin(Math.PI * e) * 22)).add(bob.clone().multiplyScalar(e));
      p = p.add(V(side * 170 * x, 10 * x, -90 * x));
      out.push({
        key: b.key, src: cutout(b.hero), ar: aspect(b.hero), p, hMm: mix(46, heroHeight(b.key), e), alpha: clamp(e * 4) * (1 - x),
        roll: side * mix(0, -6, e) + noise1(t * 0.5, i + 4) * 2, ry: side * mix(0, -14, e),
        dof: false, tint: b.tint, sweep: prog(t, t0 + 0.32, t0 + 1.02, ease.inOut), dim: 1,
      });
      // flavour variants peek out behind the hero
      b.variants.forEach((v, j) => {
        const ve = prog(t, t0 + 0.14 + j * 0.07, t0 + 0.7 + j * 0.07, ease.out);
        const vend = V(side * (j ? 70 : 74), j ? -44 : 50, j ? -46 : -30);
        const vp = start.clone().lerp(vend, ve).add(bob).add(V(side * 170 * x, 10 * x, -90 * x));
        out.push({
          key: `${b.key}${j}`, src: cutout(v), ar: aspect(v), p: vp, hMm: mix(40, j ? 56 : 60, ve), alpha: clamp(ve * 3) * (1 - x) * 0.92,
          roll: side * (j ? 10 : -6) * ve, ry: side * -18 * ve, dof: true, tint: b.tint, sweep: 0, dim: 0.8,
        });
      });
    }
    // order scene: each hero swoops back in from off-frame and drops into its cart row
    const k = i;
    const f = prog(t, C.cartAdds[k] - 0.6, C.cartAdds[k] + 0.02, ease.inOut);
    if (f > 0 && f < 1) {
      const from = V(side * 120, 60 - k * 18, 190);
      const cart = V((46 - UW_ / 2) / UW_ * PHONE.dw, (UH_ / 2 - (190 + k * 70 + 31)) / UH_ * PHONE.dh, PHONE.t / 2 + 2).applyMatrix4(rig.phone);
      const mid = from.clone().lerp(cart, 0.5).add(V(0, 26, 50));
      const p = from.clone().lerp(mid, f).lerp(mid.clone().lerp(cart, f), f);
      out.push({
        key: `cart${k}`, src: cutout(b.hero), ar: aspect(b.hero), p, hMm: mix(heroHeight(b.key) * 1.05, 10, ease.in(f)), alpha: clamp(f * 5) * (1 - prog(f, 0.8, 1)),
        roll: side * mix(-12, 0, f), ry: 0, dof: false, tint: b.tint, sweep: 0, dim: 1,
      });
    }
  });
  return out;
}
const UW_ = 390, UH_ = 824;

export const Products: React.FC<{ rig: Rig }> = ({ rig }) => {
  const t = rig.t;
  if (t < 8.9 || t > 19.7) return null;
  const focus = projectLocal(rig, 0, 0, 0).depth;
  const objs = productsAt(rig)
    .map((o) => ({ o, s: project(rig, o.p) }))
    .sort((a, b) => b.s.depth - a.s.depth);
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      {objs.map(({ o, s }) => {
        const k = pxPerMm(rig, s.depth);
        const h = o.hMm * k, w = h * o.ar;
        const blur = o.dof ? clamp(Math.abs(s.depth - focus) * 0.028, 0, 9) : 0;
        return (
          <div key={o.key} style={{ position: "absolute", left: s.x - w / 2, top: s.y - h / 2, width: w, height: h, opacity: o.alpha, transform: `perspective(${1600}px) rotateY(${o.ry}deg) rotate(${o.roll}deg)` }}>
            <div style={{ position: "absolute", left: -w * 0.45, top: -h * 0.1, width: w * 1.9, height: h * 1.2, background: `radial-gradient(50% 50% at 50% 50%, ${rgba(o.tint, 0.32 * o.dim)} 0%, ${rgba(o.tint, 0)} 70%)` }} />
            <Img src={o.src} style={{ position: "absolute", inset: 0, width: w, height: h, filter: `drop-shadow(0 ${h * 0.05}px ${h * 0.07}px rgba(0,0,0,.55)) brightness(${o.dim}) ${blur > 0.3 ? `blur(${blur}px)` : ""}` }} />
            {o.sweep > 0 && o.sweep < 1 && (
              <div style={{
                position: "absolute", inset: 0, WebkitMaskImage: `url(${o.src})`, maskImage: `url(${o.src})`, WebkitMaskSize: "100% 100%", maskSize: "100% 100%",
                background: `linear-gradient(100deg, transparent ${o.sweep * 160 - 40}%, rgba(255,255,255,.42) ${o.sweep * 160 - 22}%, transparent ${o.sweep * 160 - 4}%)`,
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------ dust
const DUST = (() => {
  const r = rng(20261012);
  return Array.from({ length: 190 }, () => ({
    x: mix(-260, 260, r()), y: mix(-420, 420, r()), z: mix(-520, 300, r()),
    s: mix(0.12, 0.42, r() ** 2), ph: r() * 100, sp: mix(0.4, 1.4, r()), red: r() < 0.12,
  }));
})();

export const Dust: React.FC<{ rig: Rig }> = ({ rig }) => {
  const ref = useRef<HTMLCanvasElement>(null);
  const t = rig.t;
  useLayoutEffect(() => {
    const cv = ref.current!;
    const dpr = window.devicePixelRatio || 1;
    if (cv.width !== W * dpr) { cv.width = W * dpr; cv.height = H * dpr; }
    const g = cv.getContext("2d")!;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);
    const level = mix(0.5, 1, prog(t, 0, 1.5)) * (1 - prog(t, 25.95, 26.1));
    if (level <= 0) return;
    g.globalCompositeOperation = "lighter";
    for (const d of DUST) {
      const p = new THREE.Vector3(d.x + noise1(t * 0.12 * d.sp, d.ph) * 18, d.y + ((t * 6 * d.sp + d.ph * 10) % 840) - 420 + 0, d.z + noise1(t * 0.1, d.ph + 3) * 14);
      p.y = ((p.y + 420) % 840 + 840) % 840 - 420;
      const s = project(rig, p);
      if (s.depth < 8) continue;
      const k = pxPerMm(rig, s.depth);
      let rad = d.s * k;
      const near = s.depth < 230;
      if (near) rad = Math.min(60, rad * 2.6);
      if (s.x < -80 || s.x > W + 80 || s.y < -80 || s.y > H + 80 || rad < 0.35) continue;
      // brighter inside the high key beam (camera-left, upper frame)
      const beam = clamp(1.1 - Math.abs((s.x - 420) * 0.9 + (s.y - 300) * 0.42) / 700, 0.25, 1);
      const tw = 0.6 + 0.4 * Math.sin(t * 2.1 * d.sp + d.ph);
      const a = (near ? 0.10 : 0.55) * beam * tw * level;
      const grad = g.createRadialGradient(s.x, s.y, 0, s.x, s.y, rad);
      const col = d.red ? "255,70,55" : "255,240,225";
      grad.addColorStop(0, `rgba(${col},${a})`);
      grad.addColorStop(near ? 0.5 : 0.35, `rgba(${col},${a * 0.45})`);
      grad.addColorStop(1, `rgba(${col},0)`);
      g.fillStyle = grad;
      g.beginPath();
      g.arc(s.x, s.y, rad, 0, Math.PI * 2);
      g.fill();
    }
  });
  return <canvas ref={ref} style={{ position: "absolute", inset: 0, width: W, height: H }} />;
};

export const window01_ = window01;
