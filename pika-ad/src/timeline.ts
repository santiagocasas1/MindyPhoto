import tl from '../timeline.json';

// 120 BPM a 30 fps: 1 beat = 15 frames, 1 compás = 60 frames.
export const FPS = tl.fps;
export const DURATION = tl.durationInFrames;
export const BEAT = (60 / tl.bpm) * tl.fps;
export const BAR = BEAT * 4;

type SceneName = 'hook' | 'tagline' | 'scanner' | 'combo' | 'end';
export const SCENES = tl.scenes as Record<SceneName, [number, number]>;
export type Cue = {f: number; type: string; note?: number};
export const CUES: Cue[] = tl.cues;
export const NEON_FLICKER: number[] = tl.neonFlicker;

// frame del bombo: todos los beats de los compases 2-14 salvo el break (compás 10)
export const isKickBar = (frame: number) => {
  const bar = Math.floor(frame / BAR) + 1;
  return bar >= 2 && bar <= 14 && bar !== 10;
};
