import {AbsoluteFill, Img, useCurrentFrame} from 'remotion';
import {Logo} from '../components/Logo';
import {Stamp} from '../components/Stamp';
import {MBlur, extrude} from '../components/fx';
import {P, Product, fit} from '../products';
import {C, F} from '../theme';
import {ease, pop, rand, tw} from '../lib/anim';

const START = 600;
const SLOT_AT = 660;
const EQUALS = 705;
const HERO = 720;

type Slot = {p: Product; at: number; label: string; kr: string; box: [number, number]; from: [number, number]; at0: [number, number]; at1: [number, number]};
const SLOTS: Slot[] = [
  {p: P.seafood, at: 660, label: 'RAMEN', kr: '라면', box: [520, 430], from: [0, 900], at0: [540, 1120], at1: [540, 1010]},
  {p: P.bigball, at: 675, label: 'BEBIDA', kr: '음료', box: [300, 440], from: [-700, 0], at0: [250, 700], at1: [340, 770]},
  {p: P.pocachip, at: 690, label: 'SNACK', kr: '스낵', box: [320, 420], from: [700, 0], at0: [830, 700], at1: [740, 780]},
];

const Sparkle: React.FC<{x: number; y: number; s: number; t: number}> = ({x, y, s, t}) => {
  const k = Math.max(0, Math.sin(t));
  return (
    <svg width={s} height={s} viewBox="-10 -10 20 20" style={{position: 'absolute', left: x - s / 2, top: y - s / 2, opacity: k, transform: `scale(${0.4 + k * 0.6}) rotate(${t * 20}deg)`}}>
      <path d="M0-10 C1-2 2-1 10 0 C2 1 1 2 0 10 C-1 2-2 1-10 0 C-2-1-1-2 0-10Z" fill={C.cream} />
    </svg>
  );
};

/** Compases 11-13: "Armá tu Combo PIKA": ramen + bebida + snack, golpe a golpe. */
export const Combo: React.FC = () => {
  const frame = useCurrentFrame();
  const panelY = tw(frame, 654, 662, 0, -1920, ease.in);
  const merge = tw(frame, EQUALS, EQUALS + 10, 0, 1, ease.inOut);
  const exit = tw(frame, 765, 780, 0, 1, ease.in);
  const exitV = exit - tw(frame - 1, 765, 780, 0, 1, ease.in);
  const orbit = frame >= HERO ? Math.sin((frame - HERO) / 18) * 7 : 0;

  return (
    <AbsoluteFill>
      {/* compás 12-13: arma del combo sobre fondo oscuro */}
      <MBlur x={exitV * 260} style={{position: 'absolute', inset: 0, transform: `translateX(${-exit * 1300}px)`}}>
        {frame >= HERO && (
          <AbsoluteFill style={{alignItems: 'center'}}>
            <div
              style={{
                position: 'absolute',
                top: 1150,
                width: 820,
                height: 170,
                borderRadius: '50%',
                background: `radial-gradient(ellipse, ${C.orange}aa 0%, ${C.orange}33 45%, transparent 70%)`,
                opacity: tw(frame, HERO - 15, HERO, 0, 1),
              }}
            />
          </AbsoluteFill>
        )}
        <AbsoluteFill style={{perspective: 1300}}>
          <AbsoluteFill style={{transform: `rotateY(${orbit}deg) translateY(${frame >= HERO ? Math.sin((frame - HERO) / 12) * 8 : 0}px)`}}>
            {SLOTS.map((s, i) => {
              if (frame < s.at) return null;
              const k = pop(frame, s.at, 10, 200, 0.6);
              const size = fit(s.p, s.box[0], s.box[1]);
              const cx = s.at0[0] + (s.at1[0] - s.at0[0]) * merge;
              const cy = s.at0[1] + (s.at1[1] - s.at0[1]) * merge;
              const sc = 1 + merge * 0.12;
              const z = i === 0 ? 3 : 2;
              return (
                <div
                  key={s.label}
                  style={{
                    position: 'absolute',
                    left: cx - size.width / 2,
                    top: cy - size.height / 2,
                    zIndex: z,
                    transform: `translate(${s.from[0] * (1 - k)}px, ${s.from[1] * (1 - k)}px) scale(${sc}) rotate(${(i - 1) * 6 * (1 - merge) + (i === 1 ? -8 : i === 2 ? 8 : 0) * merge}deg)`,
                  }}
                >
                  <Img src={s.p.file} style={{...size, filter: `drop-shadow(0 34px 40px rgba(0,0,0,.75)) drop-shadow(0 0 40px ${C.orange}55)`}} />
                </div>
              );
            })}
          </AbsoluteFill>
        </AbsoluteFill>

        {/* etiquetas y signos (antes del "=") */}
        <AbsoluteFill style={{opacity: 1 - merge}}>
          {SLOTS.map((s) => {
            if (frame < s.at + 2) return null;
            const k = pop(frame, s.at + 2, 12, 240, 0.5);
            const y = s.label === 'RAMEN' ? 1360 : 410;
            return (
              <div key={s.label} style={{position: 'absolute', left: s.at0[0] - 200, width: 400, top: y, textAlign: 'center', transform: `translateY(${(1 - k) * 40}px)`, opacity: k}}>
                <span style={{fontFamily: F.display, fontWeight: 900, fontSize: 56, color: C.cream, letterSpacing: 2}}>{s.label}</span>
                <span style={{fontFamily: F.kr, fontWeight: 900, fontSize: 40, color: C.orange, marginLeft: 14}}>{s.kr}</span>
              </div>
            );
          })}
          {[
            {at: 675, x: 395, y: 960},
            {at: 690, x: 685, y: 960},
          ].map((pl) =>
            frame >= pl.at ? (
              <div
                key={pl.at}
                style={{
                  position: 'absolute',
                  left: pl.x - 60,
                  top: pl.y - 80,
                  width: 120,
                  textAlign: 'center',
                  fontFamily: F.display,
                  fontWeight: 900,
                  fontSize: 150,
                  lineHeight: 1,
                  color: C.orange,
                  textShadow: `0 0 40px ${C.orange}`,
                  transform: `scale(${pop(frame, pl.at, 8, 300, 0.4)}) rotate(${(1 - pop(frame, pl.at, 8, 300, 0.4)) * 90}deg)`,
                }}
              >
                +
              </div>
            ) : null,
          )}
        </AbsoluteFill>

        {/* "=" y héroe */}
        {frame >= EQUALS && frame < HERO + 4 && (
          <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: tw(frame, HERO, HERO + 4, 1, 0)}}>
            <div style={{fontFamily: F.display, fontWeight: 900, fontSize: 260, color: C.cream, marginTop: -980, transform: `scale(${pop(frame, EQUALS, 8, 300, 0.5)})`, textShadow: extrude(10, C.orange)}}>=</div>
          </AbsoluteFill>
        )}
        {frame >= HERO && (
          <>
            <div style={{position: 'absolute', left: 0, right: 0, top: 330, display: 'flex', justifyContent: 'center'}}>
              <div
                style={{
                  transform: `scale(${pop(frame, HERO, 9, 260, 0.6)}) rotate(-3deg)`,
                  background: C.orange,
                  color: C.black,
                  fontFamily: F.display,
                  fontWeight: 900,
                  fontSize: 92,
                  letterSpacing: -1,
                  padding: '14px 52px 18px',
                  borderRadius: 999,
                  boxShadow: `0 20px 50px rgba(0,0,0,.6), 0 0 60px ${C.orange}88, 8px 8px 0 ${C.cream}`,
                }}
              >
                COMBO PIKA
              </div>
            </div>
            <Stamp
              size={210}
              ring="SEOUL MOOD · PIKA SELECT · "
              rotate={(frame - HERO) * 2.4}
              center={<span style={{fontFamily: F.kr, fontWeight: 900, fontSize: 52}}>콤보</span>}
              style={{position: 'absolute', left: 70, top: 1000, transform: `scale(${pop(frame, HERO + 4, 10, 200, 0.6)}) rotate(-12deg)`}}
            />
            {Array.from({length: 9}, (_, i) => (
              <Sparkle key={i} x={180 + rand(i) * 720} y={520 + rand(i + 9) * 620} s={30 + rand(i + 4) * 40} t={(frame - HERO) / 5 + i * 1.7} />
            ))}
            <div
              style={{
                position: 'absolute',
                left: 100,
                right: 100,
                top: 1310,
                textAlign: 'center',
                fontFamily: F.display,
                fontWeight: 600,
                fontSize: 46,
                lineHeight: 1.3,
                color: C.cream,
              }}
            >
              {'Elegí tu ramen, sumá una bebida y completalo con tu snack favorito.'.split(' ').map((w, i) => {
                const o = tw(frame, HERO + 2 + i * 1.2, HERO + 7 + i * 1.2, 0, 1);
                const hi = /ramen|bebida|snack/.test(w);
                return (
                  <span key={i} style={{display: 'inline-block', marginRight: 13, opacity: o, transform: `translateY(${(1 - o) * 24}px)`, color: hi ? C.orange : C.cream, fontWeight: hi ? 800 : 600}}>
                    {w}
                  </span>
                );
              })}
            </div>
          </>
        )}
      </MBlur>

      {/* compás 11: placa naranja "ARMÁ TU COMBO PIKA" */}
      {frame < 662 && (
        <AbsoluteFill style={{background: C.orange, transform: `translateY(${panelY}px)`, overflow: 'hidden'}}>
          <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
            <div style={{fontFamily: F.kr, fontWeight: 900, fontSize: 620, color: 'transparent', WebkitTextStroke: `4px ${C.black}22`, transform: `translateY(${-(frame - START) * 1.5}px)`}}>
              콤보
            </div>
          </AbsoluteFill>
          <div style={{position: 'absolute', left: 0, right: 0, top: 560, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            {frame >= START && (
              <div style={{fontFamily: F.display, fontWeight: 900, fontSize: 132, color: C.black, letterSpacing: -2, transform: `scale(${1.8 - 0.8 * pop(frame, START, 10, 260, 0.5)})`}}>
                ARMÁ TU
              </div>
            )}
            {frame >= START + 15 && (
              <div
                style={{
                  fontFamily: F.display,
                  fontWeight: 900,
                  fontSize: 250,
                  lineHeight: 0.95,
                  color: C.cream,
                  letterSpacing: -6,
                  textShadow: extrude(16, C.black),
                  transform: `scale(${1.9 - 0.9 * pop(frame, START + 15, 10, 260, 0.5)})`,
                }}
              >
                COMBO
              </div>
            )}
            {frame >= START + 30 && (
              <div style={{marginTop: 40, transform: `scale(${1.9 - 0.9 * pop(frame, START + 30, 10, 260, 0.5)})`}}>
                <Logo width={760} shadow={C.black} depth={1.2} />
              </div>
            )}
          </div>
          {frame >= START + 45 && (
            <Stamp
              size={250}
              ring="COMBO · PIKA · COMBO · PIKA · "
              rotate={(frame - START) * 3}
              bg={C.black}
              fg={C.cream}
              center={<span style={{fontFamily: F.kr, fontWeight: 900, fontSize: 64, color: C.orange}}>콤보</span>}
              style={{position: 'absolute', left: 760, top: 1290, transform: `scale(${1.8 - 0.8 * pop(frame, START + 45, 9, 300, 0.5)}) rotate(-14deg)`}}
            />
          )}
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
