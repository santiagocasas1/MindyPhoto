import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {NEON_FLICKER, SCENES} from '../timeline';
import {C} from '../theme';
import {rand, tw} from '../lib/anim';

/** Piso de grilla en perspectiva (como el hero editorial de la tienda). */
const GridFloor: React.FC<{opacity: number; speed?: number}> = ({opacity, speed = 3}) => {
  const frame = useCurrentFrame();
  const cell = 120;
  const off = (frame * speed) % cell;
  if (opacity <= 0) return null;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 900, perspective: 700, opacity, overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          left: -1500,
          width: 4080,
          height: 2400,
          bottom: -500,
          transformOrigin: '50% 100%',
          transform: 'rotateX(74deg)',
          backgroundImage: `linear-gradient(${C.orange}55 2px, transparent 2px), linear-gradient(90deg, ${C.orange}40 2px, transparent 2px)`,
          backgroundSize: `${cell}px ${cell}px`,
          backgroundPosition: `0px ${off}px`,
          maskImage: 'linear-gradient(to top, black 30%, transparent 85%)',
          WebkitMaskImage: 'linear-gradient(to top, black 30%, transparent 85%)',
        }}
      />
    </div>
  );
};

const Dust: React.FC<{opacity: number}> = ({opacity}) => {
  const frame = useCurrentFrame();
  if (opacity <= 0) return null;
  return (
    <AbsoluteFill style={{opacity}}>
      {Array.from({length: 46}, (_, i) => {
        const sp = 0.6 + rand(i) * 2.2;
        const x = rand(i + 50) * 1080 + Math.sin((frame + i * 40) / 50) * 18;
        const y = 1920 - ((rand(i + 99) * 2100 + frame * sp) % 2100);
        const s = 3 + rand(i + 7) * 7;
        const cream = i % 5 === 0;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: s,
              height: s,
              borderRadius: s,
              background: cream ? C.cream : C.orange,
              opacity: 0.25 + rand(i + 3) * 0.55,
              boxShadow: `0 0 ${s * 3}px ${cream ? C.cream : C.orange}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Marco de neón naranja; parpadea al encenderse (mismo patrón que el zumbido del audio). */
export const NeonFrame: React.FC<{opacity?: number; inset?: number}> = ({opacity = 1, inset = 34}) => {
  const frame = useCurrentFrame();
  const on = frame < NEON_FLICKER.length ? NEON_FLICKER[frame] : 1;
  const o = opacity * (on ? 1 : 0.08);
  return (
    <div
      style={{
        position: 'absolute',
        inset,
        borderRadius: 46,
        border: `5px solid ${on ? '#ffb27a' : C.orangeDeep}`,
        boxShadow: `0 0 18px ${C.orange}, 0 0 60px ${C.orange}aa, inset 0 0 18px ${C.orange}, inset 0 0 70px ${C.orange}55`,
        opacity: o,
      }}
    />
  );
};

export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const [, hookEnd] = SCENES.hook;
  const grid = frame < 60 ? 0 : frame < hookEnd ? tw(frame, 60, 75, 0, 1) : frame < SCENES.combo[0] ? 0.8 : 0.9;
  const glow = frame < 60 ? 0.35 : 1;
  const gx = 50 + Math.sin(frame / 70) * 18;
  const gy = 40 + Math.cos(frame / 90) * 10;
  return (
    <AbsoluteFill style={{background: C.black}}>
      <AbsoluteFill
        style={{
          opacity: glow,
          background: `radial-gradient(circle at ${gx}% ${gy}%, ${C.orange}3a 0%, transparent 45%), radial-gradient(circle at ${100 - gx}% ${gy + 40}%, #ff3d0030 0%, transparent 40%), radial-gradient(ellipse at 50% 100%, ${C.orange}30 0%, transparent 55%)`,
        }}
      />
      <GridFloor opacity={grid} />
      <Dust opacity={frame < 60 ? 0 : 0.9} />
    </AbsoluteFill>
  );
};
