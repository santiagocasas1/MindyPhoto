import {AbsoluteFill, Img, useCurrentFrame} from 'remotion';
import {MBlur, extrude} from '../components/fx';
import {P, fit} from '../products';
import {C, F} from '../theme';
import {ease, pop, tw} from '../lib/anim';

const START = 120;
const WORDS = [
  {kr: '라면', es: 'RAMEN', p: P.volcano, at: 180},
  {kr: '음료', es: 'BEBIDAS', p: P.bigball, at: 195},
  {kr: '스낵', es: 'SNACKS', p: P.pocachip, at: 210},
  {kr: '캔디', es: 'DULCES', p: P.jelly, at: 225},
];

const Slam: React.FC<{at: number; children: React.ReactNode; from?: number; style?: React.CSSProperties}> = ({
  at,
  children,
  from = 1.8,
  style,
}) => {
  const frame = useCurrentFrame();
  if (frame < at) return null;
  const s = pop(frame, at, 10, 240, 0.55);
  return (
    <MBlur y={(1 - s) * 14} style={{...style, transform: `scale(${from - (from - 1) * s})`, opacity: tw(frame, at, at + 2, 0, 1)}}>
      {children}
    </MBlur>
  );
};

/** Compases 3-4: "Tu K-store en Caballito" + carrusel de categorías a tempo. */
export const Tagline: React.FC = () => {
  const frame = useCurrentFrame();
  const lift = tw(frame, 165, 177, 0, 1, ease.inOut);
  const exitY = tw(frame, 228, 236, 0, -1920, ease.in);

  const current = [...WORDS].reverse().find((w) => frame >= w.at);

  return (
    <AbsoluteFill style={{transform: `translateY(${exitY}px)`}}>
      {/* bloque de título */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 470 - lift * 170,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `scale(${1 - lift * 0.16})`,
          transformOrigin: '50% 0%',
        }}
      >
        <Slam at={START}>
          <div style={{fontFamily: F.display, fontWeight: 700, fontSize: 70, color: C.cream, letterSpacing: 18, textAlign: 'center'}}>
            TU
          </div>
          <div
            style={{
              fontFamily: F.display,
              fontWeight: 900,
              fontSize: 196,
              lineHeight: 0.95,
              color: C.cream,
              letterSpacing: -4,
              textShadow: extrude(14, C.orange),
            }}
          >
            K-STORE
          </div>
        </Slam>
        <Slam at={START + 15} from={1.5}>
          <div style={{fontFamily: F.display, fontWeight: 700, fontSize: 70, color: C.cream, letterSpacing: 18, marginTop: 30}}>EN</div>
        </Slam>
        <Slam at={START + 30}>
          <div style={{position: 'relative'}}>
            <div
              style={{
                fontFamily: F.display,
                fontWeight: 900,
                fontSize: 150,
                lineHeight: 1,
                color: C.orange,
                letterSpacing: -2,
                textShadow: `0 0 50px ${C.orange}88`,
              }}
            >
              CABALLITO
            </div>
            <div
              style={{
                height: 12,
                borderRadius: 6,
                marginTop: 8,
                background: C.cream,
                width: `${tw(frame, START + 45, START + 52, 0, 100)}%`,
                boxShadow: `0 0 20px ${C.cream}`,
              }}
            />
          </div>
        </Slam>
      </div>

      {/* carrusel: una categoría por beat */}
      {current && (
        <div style={{position: 'absolute', left: 0, right: 0, top: 930, height: 460}}>
          {WORDS.filter((w) => frame >= w.at && frame < w.at + 15).map((w) => {
            const into = pop(frame, w.at, 12, 260, 0.5);
            const out = tw(frame, w.at + 12, w.at + 15, 0, 1, ease.in);
            const size = fit(w.p, 420, 430);
            const rot = (WORDS.indexOf(w) % 2 ? 8 : -8) * (1 - into) + (WORDS.indexOf(w) % 2 ? -4 : 4);
            return (
              <AbsoluteFill key={w.es} style={{opacity: 1 - out}}>
                <div
                  style={{
                    position: 'absolute',
                    left: 300 - size.width / 2,
                    top: 230 - size.height / 2,
                    transform: `translateY(${out * -120}px) scale(${0.3 + 0.7 * into}) rotate(${rot}deg)`,
                  }}
                >
                  <Img
                    src={w.p.file}
                    style={{
                      ...size,
                      filter: `drop-shadow(0 30px 40px rgba(0,0,0,.7)) drop-shadow(0 0 40px ${C.orange}55)`,
                    }}
                  />
                </div>
                <MBlur
                  y={(1 - into) * 10 + out * 14}
                  style={{
                    position: 'absolute',
                    left: 560,
                    top: 40,
                    transform: `translateY(${(1 - into) * 120 - out * 140}px)`,
                  }}
                >
                  <div
                    style={{
                      fontFamily: F.kr,
                      fontWeight: 900,
                      fontSize: 200,
                      lineHeight: 1.05,
                      color: C.orange,
                      textShadow: `0 0 50px ${C.orange}66`,
                    }}
                  >
                    {w.kr}
                  </div>
                  <div style={{fontFamily: F.display, fontWeight: 800, fontSize: 76, color: C.cream, letterSpacing: 4, marginTop: 6}}>
                    {w.es}
                  </div>
                </MBlur>
              </AbsoluteFill>
            );
          })}
        </div>
      )}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 1420,
          textAlign: 'center',
          fontFamily: F.display,
          fontWeight: 600,
          fontSize: 40,
          color: C.muted,
          letterSpacing: 1,
          opacity: tw(frame, 182, 190, 0, 1),
          transform: `translateY(${tw(frame, 182, 190, 20, 0)}px)`,
        }}
      >
        de Corea y Asia, <span style={{color: C.cream}}>cerca de casa.</span>
      </div>
    </AbsoluteFill>
  );
};
