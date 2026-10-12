// Small, deterministic animation toolkit. Every value is a pure function of time
// (seconds), so any frame can be rendered in isolation and in parallel.

export type Ease = (x: number) => number;

const bezier = (p1x: number, p1y: number, p2x: number, p2y: number): Ease => {
  // Cubic-bezier easing (same maths as CSS), solved with Newton + bisection.
  const cx = 3 * p1x, bx = 3 * (p2x - p1x) - cx, ax = 1 - cx - bx;
  const cy = 3 * p1y, by = 3 * (p2y - p1y) - cy, ay = 1 - cy - by;
  const sx = (t: number) => ((ax * t + bx) * t + cx) * t;
  const sy = (t: number) => ((ay * t + by) * t + cy) * t;
  const dx = (t: number) => (3 * ax * t + 2 * bx) * t + cx;
  return (x: number) => {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    let t = x;
    for (let i = 0; i < 6; i++) {
      const e = sx(t) - x;
      const d = dx(t);
      if (Math.abs(e) < 1e-6 || Math.abs(d) < 1e-6) break;
      t -= e / d;
    }
    let lo = 0, hi = 1;
    if (Math.abs(sx(t) - x) > 1e-5) {
      t = x;
      for (let i = 0; i < 30; i++) {
        if (sx(t) < x) lo = t; else hi = t;
        t = (lo + hi) / 2;
      }
    }
    return sy(t);
  };
};

export const ease = {
  linear: (x: number) => x,
  inOut: bezier(0.65, 0, 0.35, 1),
  out: bezier(0.16, 1, 0.3, 1), // expo-like decel: "precise, expensive"
  in: bezier(0.7, 0, 0.84, 0),
  inOutSoft: bezier(0.45, 0, 0.25, 1),
  snap: bezier(0.85, 0, 0.15, 1), // whip moves landing on the beat
  back: bezier(0.34, 1.4, 0.64, 1),
};

export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const mix = (a: number, b: number, t: number) => a + (b - a) * t;

/** Progress 0..1 of t inside [a,b] with easing. */
export const prog = (t: number, a: number, b: number, e: Ease = ease.inOut) =>
  e(clamp((t - a) / (b - a)));

/** Fade in over [a, a+inD], hold, fade out over [b-outD, b]. */
export const window01 = (t: number, a: number, b: number, inD = 0.3, outD = 0.3, e: Ease = ease.inOut) =>
  Math.min(prog(t, a, a + inD, e), 1 - prog(t, b - outD, b, e));

export type Key = [time: number, value: number, easeIn?: Ease];

/** Piecewise keyframe track. Each key's ease shapes the segment arriving at it. */
export const track = (keys: Key[]) => (t: number) => {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [t1, v1, e] = keys[i];
    const [t0, v0] = keys[i - 1];
    if (t <= t1) return mix(v0, v1, (e ?? ease.inOut)(clamp((t - t0) / (t1 - t0 || 1))));
  }
  return keys[keys.length - 1][1];
};

/** Deterministic PRNG (mulberry32). */
export const rng = (seed: number) => () => {
  seed |= 0;
  seed = (seed + 0x6d2b79f5) | 0;
  let r = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
  return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
};

/** Smooth 1D value-noise, for organic floating motion. */
export const noise1 = (x: number, seed = 0) => {
  const h = (n: number) => {
    const s = Math.sin(n * 127.1 + seed * 311.7) * 43758.5453;
    return s - Math.floor(s);
  };
  const i = Math.floor(x), f = x - i;
  const u = f * f * (3 - 2 * f);
  return mix(h(i), h(i + 1), u) * 2 - 1;
};

export const hexToRgb = (hex: string) => {
  const n = parseInt(hex.replace("#", ""), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255] as const;
};
export const rgba = (hex: string, a: number) => {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${a})`;
};
export const lerpColor = (a: string, b: string, t: number) => {
  const A = hexToRgb(a), B = hexToRgb(b);
  const c = A.map((v, i) => Math.round(mix(v, B[i], t)));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
};
