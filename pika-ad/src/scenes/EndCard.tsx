import {AbsoluteFill, Img, useCurrentFrame} from 'remotion';
import {Logo} from '../components/Logo';
import {Stamp} from '../components/Stamp';
import {BagIcon, InstagramIcon, PinIcon, TruckIcon, WhatsAppIcon} from '../components/Icons';
import {P, Product, fit} from '../products';
import {C, F} from '../theme';
import {decay, ease, pop, tw} from '../lib/anim';

const START = 780;
const FINAL = 840;

// collage de productos alrededor: [producto, x, y, tamaño, profundidad 0-1]
const FLOAT: [Product, number, number, number, number][] = [
  [P.pomegranate, 990, 150, 300, 0.2],
  [P.kimchi, 110, 170, 230, 0.25],
  [P.maxim, 80, 520, 280, 0.45],
  [P.kokomen, 1010, 560, 240, 0.5],
  [P.tuemsae, 40, 980, 260, 0.6],
  [P.omori, 1030, 1000, 230, 0.35],
  [P.bibimmenCup, 130, 1500, 330, 0.85],
  [P.shoyu, 960, 1440, 250, 0.8],
  [P.jellyGrape, 300, 1760, 280, 0.55],
  [P.wang, 820, 1730, 240, 0.6],
  [P.bibimmen, 560, 1860, 340, 0.3],
];

const Card: React.FC<{at: number; top: number; icon: React.ReactNode; title: string; sub: string}> = ({at, top, icon, title, sub}) => {
  const frame = useCurrentFrame();
  if (frame < at) return null;
  const k = pop(frame, at, 12, 220, 0.6);
  return (
    <div
      style={{
        position: 'absolute',
        left: 110,
        right: 110,
        top,
        display: 'flex',
        alignItems: 'center',
        gap: 30,
        padding: '26px 34px',
        borderRadius: 30,
        background: 'rgba(29, 26, 23, 0.9)',
        border: '2px solid rgba(245, 239, 231, 0.16)',
        boxShadow: '0 24px 60px rgba(0,0,0,.55)',
        transform: `translateX(${(1 - k) * 380}px) scale(${0.9 + 0.1 * k})`,
        opacity: Math.min(1, k * 1.5),
      }}
    >
      <div style={{width: 100, height: 100, borderRadius: 50, background: C.orange, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: `0 0 30px ${C.orange}88`}}>
        {icon}
      </div>
      <div>
        <div style={{fontFamily: F.display, fontWeight: 800, fontSize: 50, color: C.cream, lineHeight: 1.1}}>{title}</div>
        <div style={{fontFamily: F.display, fontWeight: 500, fontSize: 34, color: C.muted, marginTop: 4}}>{sub}</div>
      </div>
    </div>
  );
};

/** Compases 14-15: cierre con logo, beneficios y llamado a la acción. */
export const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const logoK = pop(frame, START, 9, 220, 0.6);
  const bump = 1 + 0.035 * decay(frame, FINAL, 12);
  const shine = ((frame - FINAL) % 40) / 40;
  const ctaK = frame >= 825 ? pop(frame, 825, 10, 240, 0.55) : 0;

  return (
    <AbsoluteFill style={{transform: `scale(${bump})`}}>
      {FLOAT.map(([p, x, y, s, depth], i) => {
        const k = pop(frame, START + 2 + i, 14, 140, 0.8);
        const size = fit(p, s, s);
        const dy = -(frame - START) * (0.4 + depth * 1.4);
        const rot = Math.sin((frame + i * 20) / 30) * 6 + (i % 2 ? 8 : -8);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x - size.width / 2,
              top: y - size.height / 2 + dy,
              transform: `scale(${k * (0.75 + depth * 0.35)}) rotate(${rot}deg)`,
              filter: `blur(${(1 - depth) * 5}px) brightness(${0.42 + depth * 0.3})`,
            }}
          >
            <Img src={p.file} style={size} />
          </div>
        );
      })}

      {/* logo */}
      <div style={{position: 'absolute', left: 0, right: 0, top: 270, display: 'flex', flexDirection: 'column', alignItems: 'center', transform: `scale(${1.7 - 0.7 * logoK})`, opacity: Math.min(1, logoK * 2)}}>
        <Logo width={720} depth={1 + 0.5 * decay(frame, START, 14)} />
        <div style={{fontFamily: F.display, fontWeight: 700, fontSize: 40, letterSpacing: 10, color: C.orange, marginTop: 14, textShadow: `0 0 24px ${C.orange}88`}}>
          K · STORE · CABALLITO
        </div>
      </div>
      {frame >= START + 6 && (
        <Stamp
          size={190}
          ring="SEOUL MOOD · PIKA SELECT · "
          rotate={(frame - START) * 2}
          center={<span style={{fontFamily: F.kr, fontWeight: 900, fontSize: 50, color: C.orange}}>피카</span>}
          style={{position: 'absolute', left: 830, top: 190, transform: `scale(${pop(frame, START + 6, 10, 200, 0.6)}) rotate(12deg)`}}
        />
      )}

      <Card at={795} top={640} icon={<PinIcon size={56} />} title="RETIRO GRATIS" sub="Av. La Plata 169 · Caballito" />
      <Card at={810} top={830} icon={<TruckIcon size={56} />} title="ENVÍOS A DOMICILIO" sub="Calculalos con tu código postal" />

      {/* CTA */}
      {frame >= 825 && (
        <div style={{position: 'absolute', left: 110, right: 110, top: 1030, transform: `scale(${0.6 + 0.4 * ctaK})`, opacity: Math.min(1, ctaK * 1.5)}}>
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              height: 140,
              borderRadius: 70,
              background: C.orange,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 20,
              boxShadow: `0 0 ${50 + 40 * decay(frame, FINAL, 16)}px ${C.orange}, 10px 10px 0 ${C.cream}`,
            }}
          >
            <BagIcon size={62} />
            <span style={{fontFamily: F.display, fontWeight: 900, fontSize: 70, color: C.black, letterSpacing: -1}}>PEDÍ ONLINE</span>
            {frame >= FINAL && (
              <div
                style={{
                  position: 'absolute',
                  top: -40,
                  bottom: -40,
                  width: 120,
                  left: `${-20 + shine * 140}%`,
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,.55), transparent)',
                  transform: 'rotate(18deg)',
                }}
              />
            )}
          </div>
          <div style={{textAlign: 'center', marginTop: 22, fontFamily: F.mono, fontWeight: 700, fontSize: 36, color: C.cream}}>pikakstore.mitiendanube.com</div>
        </div>
      )}

      {/* redes */}
      {frame >= FINAL && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 1300,
            display: 'flex',
            justifyContent: 'center',
            gap: 46,
            transform: `translateY(${(1 - pop(frame, FINAL, 12, 220, 0.6)) * 60}px)`,
            opacity: tw(frame, FINAL, FINAL + 5, 0, 1),
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
            <InstagramIcon size={54} />
            <span style={{fontFamily: F.display, fontWeight: 800, fontSize: 46, color: C.cream}}>@pika.kstore</span>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <WhatsAppIcon size={52} />
            <span style={{fontFamily: F.display, fontWeight: 700, fontSize: 42, color: C.muted}}>11 6796-3800</span>
          </div>
        </div>
      )}
      <AbsoluteFill style={{background: C.black, opacity: tw(frame, 893, 900, 0, 0.6, ease.in)}} />
    </AbsoluteFill>
  );
};
