import {Product} from '../products';
import {C, F} from '../theme';
import {ease, rand, tw} from '../lib/anim';

export const Barcode: React.FC<{seed: number; width: number; height: number; color?: string}> = ({seed, width, height, color = C.black}) => {
  const bars: {x: number; w: number}[] = [];
  let x = 0;
  let i = 0;
  while (x < width) {
    const w = 2 + Math.floor(rand(seed * 31 + i) * 4) * 1.5;
    if (i % 2 === 0) bars.push({x, w});
    x += w + 1.5;
    i++;
  }
  return (
    <svg width={width} height={height}>
      {bars.map((b, k) => (
        <rect key={k} x={b.x} y={0} width={Math.min(b.w, width - b.x)} height={height} fill={color} />
      ))}
    </svg>
  );
};

const Zigzag: React.FC<{flip?: boolean}> = ({flip}) => {
  const pts: string[] = [];
  for (let x = 0; x <= 720; x += 18) pts.push(`${x},${(x / 18) % 2 ? 0 : 14}`);
  return (
    <svg width={720} height={14} style={{display: 'block', transform: flip ? 'scaleY(-1)' : undefined}}>
      <polygon points={`0,14 ${pts.join(' ')} 720,14`} fill={C.cream} />
    </svg>
  );
};

const Row: React.FC<{h: number; children: React.ReactNode}> = ({h, children}) => (
  <div style={{height: h, overflow: 'hidden', display: 'flex', alignItems: 'center'}}>{children}</div>
);

const Leader: React.FC<{left: React.ReactNode; right: React.ReactNode; bold?: boolean}> = ({left, right, bold}) => (
  <div style={{display: 'flex', alignItems: 'baseline', width: '100%', gap: 10, fontWeight: bold ? 700 : 400}}>
    {left}
    <div style={{flex: 1, borderBottom: `3px dotted ${C.black}55`, transform: 'translateY(-6px)'}} />
    {right}
  </div>
);

const ROW = 50;
const REVEAL = 540;
const FOOTER = [552, 558, 564, 570];
const RIP = 585;

/** Ticket térmico: imprime cada producto escaneado y en el break se revela completo. */
export const Receipt: React.FC<{frame: number; printed: number; lastPrint: number; items: Product[]}> = ({frame, printed, lastPrint, items}) => {
  const reveal = tw(frame, REVEAL, REVEAL + 16, 0, 1, ease.inOut);
  const slotY = 1490 - reveal * 50;
  const windowTop = 1250 - reveal * 1500;
  const rip = tw(frame, RIP, RIP + 15, 0, 1, ease.in);
  const grow = (at: number, h: number) => tw(frame, at, at + 6, 0, h, ease.out);

  const mono: React.CSSProperties = {fontFamily: F.mono, fontSize: 25, color: C.black, letterSpacing: 0.5, width: '100%'};

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: 0,
        height: 1920,
        maskImage: `linear-gradient(to bottom, transparent ${windowTop}px, black ${windowTop + 60}px)`,
        WebkitMaskImage: `linear-gradient(to bottom, transparent ${windowTop}px, black ${windowTop + 60}px)`,
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: 180,
          width: 720,
          bottom: 1920 - slotY,
          transform: `translateY(${-rip * 1700}px) rotate(${-2 * reveal - rip * 14}deg) scale(${1 - reveal * 0.04})`,
          transformOrigin: '50% 100%',
          filter: 'drop-shadow(0 30px 40px rgba(0,0,0,.6))',
        }}
      >
        <Zigzag />
        <div style={{background: C.cream, padding: '18px 36px 26px'}}>
          {/* encabezado */}
          <div style={{textAlign: 'center', paddingBottom: 14}}>
            <div style={{fontFamily: F.display, fontWeight: 900, fontSize: 70, color: C.black, lineHeight: 1}}>
              PIKA <span style={{fontFamily: F.kr, fontSize: 46, color: C.orange}}>피카</span>
            </div>
            <div style={{...mono, fontWeight: 700, fontSize: 24, marginTop: 6}}>K-STORE · AV. LA PLATA 169 · CABALLITO</div>
            <div style={{...mono, fontSize: 22, color: '#5a5048', marginTop: 4}}>편의점 · TU TIENDA DE CONVENIENCIA</div>
            <div style={{borderBottom: `3px dashed ${C.black}66`, marginTop: 14}} />
          </div>
          {/* ítems */}
          {items.slice(0, printed).map((p, i) => (
            <Row key={i} h={i === printed - 1 && frame < REVEAL ? grow(lastPrint, ROW) : ROW}>
              <div style={mono}>
                <Leader
                  left={
                    <>
                      <span style={{color: C.orange, fontWeight: 700}}>{String(i + 1).padStart(2, '0')}</span>
                      <span style={{fontFamily: F.kr, fontWeight: 700, fontSize: 22, width: 70}}>{p.kr}</span>
                      <span style={{whiteSpace: 'nowrap'}}>{p.short}</span>
                    </>
                  }
                  right={<span>x1</span>}
                />
              </div>
            </Row>
          ))}
          {/* pie: se imprime en el break */}
          {frame >= FOOTER[0] && (
            <>
              <Row h={grow(FOOTER[0], 64)}>
                <div style={{...mono, fontSize: 30}}>
                  <div style={{borderTop: `3px dashed ${C.black}66`, paddingTop: 12}}>
                    <Leader bold left={<span>TOTAL</span>} right={<span style={{color: C.orange}}>SEOUL MOOD ✓</span>} />
                  </div>
                </div>
              </Row>
              <Row h={grow(FOOTER[1], ROW)}>
                <div style={mono}>
                  <Leader left={<span>RETIRO</span>} right={<span style={{fontWeight: 700}}>GRATIS</span>} />
                </div>
              </Row>
              <Row h={grow(FOOTER[2], ROW)}>
                <div style={mono}>
                  <Leader left={<span>ENVÍOS</span>} right={<span style={{fontWeight: 700}}>A DOMICILIO</span>} />
                </div>
              </Row>
              <Row h={grow(FOOTER[3], 140)}>
                <div style={{width: '100%', textAlign: 'center', paddingTop: 14}}>
                  <Barcode seed={42} width={420} height={64} />
                  <div style={{...mono, fontSize: 22, marginTop: 6}}>
                    <span style={{fontFamily: F.kr, fontWeight: 700}}>감사합니다</span> · ¡GRACIAS!
                  </div>
                </div>
              </Row>
            </>
          )}
        </div>
        {frame >= RIP - 2 && <Zigzag flip />}
      </div>
      {/* ranura de la impresora */}
      <div
        style={{
          position: 'absolute',
          left: 130,
          width: 820,
          top: slotY - 6 + reveal * 260,
          height: 46,
          borderRadius: 23,
          background: `linear-gradient(${C.raised}, ${C.black})`,
          border: `2px solid #2c2722`,
          boxShadow: `0 -8px 30px rgba(0,0,0,.8), inset 0 3px 0 ${C.orange}`,
          opacity: 1 - reveal,
        }}
      >
        <div style={{position: 'absolute', right: 26, top: 15, width: 14, height: 14, borderRadius: 7, background: frame - lastPrint < 8 ? C.orange : '#3a332d', boxShadow: frame - lastPrint < 8 ? `0 0 16px ${C.orange}` : 'none'}} />
      </div>
    </div>
  );
};
