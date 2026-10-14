import {AbsoluteFill, Img, useCurrentFrame} from 'remotion';
import {MBlur} from '../components/fx';
import {Barcode, Receipt} from '../components/Receipt';
import {P, Product, fit} from '../products';
import {C, F} from '../theme';
import {decay, ease, pop, tw} from '../lib/anim';

const START = 240;
const STEP = 30; // un producto cada 2 beats
const REVEAL = 540;

const CATS = [
  {kr: '라면', es: 'RAMEN'},
  {kr: '떡볶이', es: 'TOPOKKI'},
  {kr: '음료', es: 'BEBIDAS & SOJU'},
  {kr: '스낵', es: 'SNACKS'},
  {kr: '달콤', es: 'DULCES'},
];
export const SCAN_ITEMS: Product[] = [
  P.volcano, P.kimchiCup, P.carbonara, P.sweetSpicy, P.bigball, P.soju, P.pocachip, P.oreo, P.jelly, P.chocopick,
];

const BOX = {x: 170, y: 470, w: 740, h: 640};

const Corners: React.FC<{snap: number; opacity: number}> = ({snap, opacity}) => {
  const L = 90;
  const inset = 14 * snap;
  const s: React.CSSProperties = {position: 'absolute', width: L, height: L, borderColor: C.cream, borderStyle: 'solid', borderWidth: 0};
  const c = (pos: React.CSSProperties, b: React.CSSProperties) => <div style={{...s, ...pos, ...b}} />;
  return (
    <div style={{position: 'absolute', left: BOX.x + inset, top: BOX.y + inset, width: BOX.w - 2 * inset, height: BOX.h - 2 * inset, opacity}}>
      {c({left: 0, top: 0}, {borderTopWidth: 8, borderLeftWidth: 8, borderTopLeftRadius: 26})}
      {c({right: 0, top: 0}, {borderTopWidth: 8, borderRightWidth: 8, borderTopRightRadius: 26})}
      {c({left: 0, bottom: 0}, {borderBottomWidth: 8, borderLeftWidth: 8, borderBottomLeftRadius: 26})}
      {c({right: 0, bottom: 0}, {borderBottomWidth: 8, borderRightWidth: 8, borderBottomRightRadius: 26})}
    </div>
  );
};

const ProductShot: React.FC<{p: Product; s: number; i: number}> = ({p, s, i}) => {
  const frame = useCurrentFrame();
  const enter = tw(frame, s - 6, s, 1, 0, ease.out);
  const exit = tw(frame, s + 24, s + 30, 0, 1, ease.in);
  const x = enter * 820 - exit * 820;
  const vel = Math.abs(tw(frame, s - 6, s, 1, 0, ease.out) - tw(frame - 1, s - 6, s, 1, 0, ease.out)) + Math.abs(exit - tw(frame - 1, s + 24, s + 30, 0, 1, ease.in));
  const size = fit(p, 600, 560);
  const flash = tw(frame, s, s + 9, 1.8, 1);
  const float = Math.sin((frame - s) / 9) * 8;
  const rotY = (i % 2 ? -1 : 1) * (10 - 10 * pop(frame, s - 6, 14, 120, 0.8)) + Math.sin((frame - s) / 14) * 4;
  const laser = tw(frame, s, s + 8, 0, 1, ease.inOut);
  const laserO = frame < s ? 0 : tw(frame, s + 7, s + 11, 1, 0);
  return (
    <AbsoluteFill style={{perspective: 1200}}>
      <MBlur
        x={vel * 140}
        style={{
          position: 'absolute',
          left: BOX.x + BOX.w / 2 - size.width / 2,
          top: BOX.y + BOX.h / 2 - size.height / 2 + float,
          transform: `translateX(${x}px) rotateY(${rotY}deg) rotate(${enter * 12 - exit * 12}deg)`,
        }}
      >
        <Img
          src={p.file}
          style={{
            ...size,
            filter: `brightness(${flash}) drop-shadow(0 40px 50px rgba(0,0,0,.75)) drop-shadow(0 0 46px ${C.orange}66)`,
          }}
        />
        {/* láser del escáner */}
        <div
          style={{
            position: 'absolute',
            left: -60,
            right: -60,
            top: laser * size.height - 3,
            height: 6,
            borderRadius: 3,
            background: '#fff',
            opacity: laserO,
            boxShadow: `0 0 12px ${C.laser}, 0 0 30px ${C.laser}, 0 0 80px ${C.laser}, 0 -40px 60px ${C.laser}55`,
          }}
        />
      </MBlur>
    </AbsoluteFill>
  );
};

const BeepSticker: React.FC<{s: number; i: number}> = ({s, i}) => {
  const frame = useCurrentFrame();
  if (frame < s + 1 || frame > s + 24) return null;
  const k = pop(frame, s + 1, 9, 300, 0.5);
  const o = tw(frame, s + 18, s + 24, 1, 0);
  return (
    <div
      style={{
        position: 'absolute',
        left: i % 2 ? 140 : 720,
        top: 500,
        transform: `scale(${k}) rotate(${i % 2 ? -14 : 12}deg)`,
        opacity: o,
        background: C.orange,
        color: C.black,
        fontFamily: F.kr,
        fontWeight: 900,
        fontSize: 64,
        padding: '10px 30px 16px',
        borderRadius: 999,
        boxShadow: `0 10px 30px rgba(0,0,0,.5), 0 0 40px ${C.orange}`,
      }}
    >
      삑!
    </div>
  );
};

/** Compases 5-10: escáner de 편의점, cada producto suena "삑" y se imprime en el ticket. */
export const Scanner: React.FC = () => {
  const frame = useCurrentFrame();
  const idx = Math.max(0, Math.min(SCAN_ITEMS.length - 1, Math.floor((frame - START + 6) / STEP)));
  const cat = Math.max(0, Math.min(CATS.length - 1, Math.floor((frame - START + 4) / 60)));
  const catAt = START + cat * 60 - 4;
  const catIn = pop(frame, catAt, 13, 220, 0.6);
  const reveal = tw(frame, REVEAL, REVEAL + 12, 0, 1, ease.inOut);
  const enter = tw(frame, START - 5, START - 1, 0, 1);
  const printed = SCAN_ITEMS.map((_, i) => START + i * STEP + 3).filter((f) => frame >= f).length;
  const lastPrint = START + (printed - 1) * STEP + 3;
  const s = START + idx * STEP;

  return (
    <AbsoluteFill style={{opacity: enter}}>
      {/* gran texto coreano de fondo */}
      <AbsoluteFill style={{alignItems: 'center', top: 380, opacity: (1 - reveal) * 0.9}}>
        <div
          style={{
            fontFamily: F.kr,
            fontWeight: 900,
            fontSize: CATS[cat].kr.length > 2 ? 330 : 470,
            lineHeight: 1,
            color: 'transparent',
            WebkitTextStroke: `3px ${C.orange}66`,
            transform: `scale(${1.25 - 0.25 * catIn}) translateY(${(frame - catAt) * -0.6}px)`,
            whiteSpace: 'nowrap',
          }}
        >
          {CATS[cat].kr}
        </div>
      </AbsoluteFill>

      {/* encabezado de categoría + contador */}
      <div style={{position: 'absolute', left: 90, right: 90, top: 250, height: 190, opacity: 1 - reveal, overflow: 'hidden'}}>
        <div style={{transform: `translateY(${(1 - catIn) * 190}px)`, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between'}}>
          <div>
            <div style={{fontFamily: F.kr, fontWeight: 900, fontSize: 96, color: C.orange, lineHeight: 1.1, textShadow: `0 0 40px ${C.orange}77`}}>
              {CATS[cat].kr}
            </div>
            <div style={{fontFamily: F.display, fontWeight: 800, fontSize: 52, color: C.cream, letterSpacing: 3}}>{CATS[cat].es}</div>
          </div>
          <div style={{textAlign: 'right', paddingBottom: 12}}>
            <div style={{fontFamily: F.mono, fontWeight: 700, fontSize: 26, color: C.muted, letterSpacing: 4, display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'flex-end'}}>
              <span style={{width: 16, height: 16, borderRadius: 8, background: C.laser, boxShadow: `0 0 14px ${C.laser}`, opacity: Math.floor(frame / 8) % 2 ? 1 : 0.3}} />
              SCAN
            </div>
            <div style={{fontFamily: F.mono, fontWeight: 700, fontSize: 54, color: C.cream}}>
              {String(idx + 1).padStart(2, '0')}
              <span style={{color: C.subtle}}>/10</span>
            </div>
          </div>
        </div>
      </div>

      {/* visor + producto */}
      <AbsoluteFill style={{opacity: 1 - reveal, transform: `scale(${1 - reveal * 0.15})`}}>
        <Corners snap={decay(frame, s, 10)} opacity={0.85} />
        {SCAN_ITEMS.map((p, i) => {
          const si = START + i * STEP;
          if (frame < si - 6 || frame > si + 30) return null;
          return <ProductShot key={i} p={p} s={si} i={i} />;
        })}
        <BeepSticker s={s} i={idx} />
        {/* nombre del producto, tipo ticket */}
        <div style={{position: 'absolute', left: 90, right: 90, top: 1140, display: 'flex', alignItems: 'center', gap: 22, justifyContent: 'center'}}>
          <Barcode seed={idx + 3} width={110} height={52} color={C.cream} />
          <div style={{fontFamily: F.mono, fontWeight: 700, fontSize: 38, color: C.cream, letterSpacing: 1, whiteSpace: 'nowrap'}}>
            {SCAN_ITEMS[idx].name.slice(0, Math.floor(tw(frame, s + 1, s + 10, 0, SCAN_ITEMS[idx].name.length, (t) => t)))}
            <span style={{opacity: Math.floor(frame / 4) % 2, color: C.orange}}>▌</span>
          </div>
        </div>
      </AbsoluteFill>

      <Receipt frame={frame} printed={printed} lastPrint={lastPrint} items={SCAN_ITEMS} />
    </AbsoluteFill>
  );
};
