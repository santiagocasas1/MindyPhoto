import {noise2D} from '@remotion/noise';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame} from 'remotion';
import {Background, NeonFrame} from './components/Background';
import {ChromaSplit, Grain} from './components/fx';
import {Combo} from './scenes/Combo';
import {EndCard} from './scenes/EndCard';
import {Hook} from './scenes/Hook';
import {Scanner} from './scenes/Scanner';
import {Tagline} from './scenes/Tagline';
import {BEAT, CUES, isKickBar} from './timeline';
import {C} from './theme';
import {impact} from './lib/anim';

const FLASH: Record<string, [number, string]> = {
  slam: [0.28, '#ffffff'],
  drop: [0.9, '#ffffff'],
  hit: [0.18, '#ffffff'],
  final: [0.75, '#ffffff'],
  scan: [0.1, C.orange],
  stamp: [0.12, '#ffffff'],
};

export const PikaAd: React.FC = () => {
  const frame = useCurrentFrame();

  // cámara: temblor en los golpes + "pump" en cada bombo
  const shake = impact(frame, ['slam', 'drop', 'hit', 'final', 'stamp', 'rip']);
  const sx = noise2D('sx', frame * 0.4, 0) * shake * 18;
  const sy = noise2D('sy', 0, frame * 0.4) * shake * 18;
  const rot = noise2D('rot', frame * 0.3, 3) * shake * 0.9;
  const pulse = isKickBar(frame) ? 1 + 0.014 * Math.exp(-(frame % BEAT) / 3) : 1;
  const chroma = impact(frame, ['slam', 'drop', 'final', 'hit']) * 7;

  let flash = 0;
  let flashColor = '#ffffff';
  for (const c of CUES) {
    const fl = FLASH[c.type];
    if (!fl || frame < c.f) continue;
    const v = fl[0] * Math.exp(-(frame - c.f) / 2.2);
    if (v > flash) {
      flash = v;
      flashColor = fl[1];
    }
  }

  const neon = frame < 120 ? 1 : frame < 240 ? 0.85 : frame < 600 ? 0.55 : frame < 662 ? 0 : frame < 780 ? 0.75 : 1;

  return (
    <AbsoluteFill style={{background: C.black}}>
      <Audio src={staticFile('audio/pika-soundtrack.wav')} />
      <AbsoluteFill style={{transform: `scale(${1 + (pulse - 1) * 0.5})`}}>
        <Background />
      </AbsoluteFill>
      <ChromaSplit amount={chroma}>
        <AbsoluteFill style={{transform: `translate(${sx}px, ${sy}px) rotate(${rot}deg) scale(${pulse})`}}>
          {frame < 120 && <Hook />}
          {frame >= 120 && frame < 242 && <Tagline />}
          {frame >= 232 && frame < 602 && <Scanner />}
          {frame >= 600 && frame < 782 && <Combo />}
          {frame >= 780 && <EndCard />}
        </AbsoluteFill>
      </ChromaSplit>
      <NeonFrame opacity={neon} />
      <AbsoluteFill style={{background: flashColor, opacity: flash, mixBlendMode: flashColor === '#ffffff' ? 'normal' : 'screen'}} />
      <Grain />
    </AbsoluteFill>
  );
};
