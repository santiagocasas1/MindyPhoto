import {Easing, interpolate, spring} from 'remotion';
import {CUES, FPS} from '../timeline';

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const ease = {
  out: Easing.bezier(0.16, 1, 0.3, 1),
  in: Easing.bezier(0.7, 0, 0.84, 0),
  inOut: Easing.bezier(0.65, 0, 0.35, 1),
  back: Easing.bezier(0.34, 1.56, 0.64, 1),
  snap: Easing.bezier(0.2, 0.9, 0.1, 1),
};

/** Interpola un valor entre dos frames (con clamp). */
export const tw = (frame: number, f0: number, f1: number, v0: number, v1: number, easing = ease.out) =>
  interpolate(frame, [f0, f1], [v0, v1], {...clamp, easing});

/** Resorte que arranca en `at`. */
export const pop = (frame: number, at: number, damping = 11, stiffness = 170, mass = 0.6) =>
  spring({frame: frame - at, fps: FPS, config: {damping, stiffness, mass}});

/** 1 en el golpe y cae exponencialmente. */
export const decay = (frame: number, at: number, len = 8) => (frame < at ? 0 : Math.exp(-(frame - at) / (len / 3)));

const STRENGTH: Record<string, number> = {
  slam: 1, drop: 1.5, hit: 0.75, final: 1.2, stamp: 0.6, pop: 0.28, scan: 0.35, flip: 0.22, tick: 0.18, rip: 0.5, ding: 0.2,
};

/** Energía de impacto (para shake, flashes y aberración cromática), sincronizada con timeline.json. */
export const impact = (frame: number, types?: string[]) => {
  let v = 0;
  for (const c of CUES) {
    if (types && !types.includes(c.type)) continue;
    const s = STRENGTH[c.type] ?? 0;
    if (s && frame >= c.f) v += s * Math.exp(-(frame - c.f) / 3.2);
  }
  return v;
};

/** Pseudo-random determinístico. */
export const rand = (seed: number) => {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
