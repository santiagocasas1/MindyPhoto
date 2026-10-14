import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Logo} from '../components/Logo';
import {MBlur} from '../components/fx';
import {NEON_FLICKER} from '../timeline';
import {C, F} from '../theme';
import {decay, ease, pop, tw} from '../lib/anim';

const SLAMS = {P: 0, I: 15, K: 30, A: 45};
const DROP = 60;
const SUB = 'K · STORE · CABALLITO';

/** Compases 1-2: P·I·K·A golpean con cada beat y en el drop aparece el logo completo. */
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();

  const letters = Object.fromEntries(
    Object.entries(SLAMS).map(([id, at]) => {
      const s = pop(frame, at, 9, 260, 0.5);
      return [id, {opacity: tw(frame, at, at + 2, 0, 1), scale: 2.8 - 1.8 * s, y: (1 - s) * -60}];
    }),
  );
  const lastSlam = Math.max(...Object.values(SLAMS).filter((a) => a <= frame), 0);
  const slamBlur = Math.max(0, 1 - pop(frame, lastSlam, 9, 260, 0.5)) * 16;

  // anticipación antes del drop, golpe en el drop y zoom-through de salida
  const anticip = tw(frame, 52, DROP, 1, 0.9, ease.in);
  const dropS = frame >= DROP ? 0.9 + 0.1 * pop(frame, DROP, 8, 220, 0.6) : anticip;
  const exit = tw(frame, 104, 119, 1, 7.5, ease.in);
  const exitO = tw(frame, 111, 118, 1, 0, ease.in);
  const push = tw(frame, DROP, 104, 1, 1.07, ease.inOut);
  const depth = frame < DROP ? 1 : 1 + 0.7 * decay(frame, DROP, 18) + 0.3 * tw(frame, DROP, DROP + 6, 0, 1);
  const tiltX = frame >= DROP ? Math.sin((frame - DROP) / 16) * 6 : 0;
  const tiltY = frame >= DROP ? Math.cos((frame - DROP) / 20) * 8 : 0;

  const neonOn = frame < NEON_FLICKER.length ? NEON_FLICKER[frame] : 1;
  const ring = tw(frame, DROP, DROP + 22, 0, 1, ease.out);

  return (
    <AbsoluteFill style={{opacity: exitO}}>
      {/* 피카 en neón detrás: titila al encender y queda como textura después del drop */}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div
          style={{
            fontFamily: F.kr,
            fontWeight: 900,
            fontSize: 560,
            lineHeight: 1,
            letterSpacing: -20,
            color: frame >= DROP ? `${C.orange}22` : 'transparent',
            WebkitTextStroke: `4px ${C.orange}`,
            textShadow: neonOn && frame < DROP ? `0 0 30px ${C.orange}, 0 0 80px ${C.orange}` : 'none',
            opacity: frame < DROP ? (neonOn ? 0.9 : 0.12) * tw(frame, 30, 50, 1, 0.25) : 0.55,
            transform: `translateY(${frame >= DROP ? -40 - (frame - DROP) * 0.8 : -40}px) scale(${frame >= DROP ? 1.15 + (frame - DROP) * 0.002 : 1})`,
          }}
        >
          피카
        </div>
      </AbsoluteFill>

      {/* onda expansiva del drop */}
      {frame >= DROP && ring < 1 && (
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
          <div
            style={{
              width: 200 + ring * 1700,
              height: 200 + ring * 1700,
              borderRadius: '50%',
              border: `${10 * (1 - ring) + 2}px solid ${C.cream}`,
              boxShadow: `0 0 60px ${C.orange}, inset 0 0 60px ${C.orange}`,
              opacity: 1 - ring,
            }}
          />
        </AbsoluteFill>
      )}

      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', perspective: 1400}}>
        <div
          style={{
            transform: `translateY(-30px) scale(${dropS * exit * push}) rotateX(${tiltX}deg) rotateY(${tiltY}deg)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <MBlur y={slamBlur * (frame < DROP ? 1 : 0) + (exit - 1) * 3}>
            <Logo width={960} depth={depth} letters={letters} />
          </MBlur>
          <div style={{display: 'flex', marginTop: 26, height: 70}}>
            {SUB.split('').map((ch, i) => {
              const at = DROP + 3 + i * 0.9;
              const o = tw(frame, at, at + 5, 0, 1);
              return (
                <span
                  key={i}
                  style={{
                    fontFamily: F.display,
                    fontWeight: 700,
                    fontSize: 50,
                    letterSpacing: 10,
                    color: C.orange,
                    whiteSpace: 'pre',
                    opacity: o,
                    transform: `translateY(${(1 - o) * 30}px)`,
                    textShadow: `0 0 24px ${C.orange}88`,
                  }}
                >
                  {ch}
                </span>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
