import {useId} from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from 'remotion';
import {C} from '../theme';

/** Desenfoque direccional real (motion blur) vía filtro SVG anisotrópico. */
export const MBlur: React.FC<{x?: number; y?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({
  x = 0,
  y = 0,
  children,
  style,
}) => {
  const id = 'mb' + useId().replace(/[^a-zA-Z0-9]/g, '');
  const on = Math.abs(x) > 0.3 || Math.abs(y) > 0.3;
  return (
    <div style={{...style, filter: on ? `url(#${id})` : undefined}}>
      {on && (
        <svg style={{position: 'absolute', width: 0, height: 0}}>
          <filter id={id} x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation={`${Math.abs(x).toFixed(2)} ${Math.abs(y).toFixed(2)}`} />
          </filter>
        </svg>
      )}
      {children}
    </div>
  );
};

/** Aberración cromática (separación RGB) para los golpes fuertes. */
export const ChromaSplit: React.FC<{amount: number; children: React.ReactNode}> = ({amount, children}) => {
  const id = 'ca' + useId().replace(/[^a-zA-Z0-9]/g, '');
  if (amount < 0.6) return <AbsoluteFill>{children}</AbsoluteFill>;
  const a = amount.toFixed(2);
  return (
    <AbsoluteFill style={{filter: `url(#${id})`}}>
      <svg style={{position: 'absolute', width: 0, height: 0}}>
        <filter id={id} x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
          <feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r" />
          <feOffset in="r" dx={a} dy="0" result="r2" />
          <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="g" />
          <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="b" />
          <feOffset in="b" dx={`-${a}`} dy="0" result="b2" />
          <feBlend in="r2" in2="g" mode="screen" result="rg" />
          <feBlend in="rg" in2="b2" mode="screen" />
        </filter>
      </svg>
      {children}
    </AbsoluteFill>
  );
};

/** Grano de película + viñeta. */
export const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <Img
        src={staticFile(`fx/grain-${frame % 4}.webp`)}
        style={{width: '100%', height: '100%', mixBlendMode: 'overlay', opacity: 0.22}}
      />
      <AbsoluteFill
        style={{background: 'radial-gradient(ellipse 75% 60% at 50% 48%, transparent 55%, rgba(0,0,0,0.62) 100%)'}}
      />
    </AbsoluteFill>
  );
};

/** Texto con extrusión 3D (sombra sólida en diagonal, como el logo). */
export const extrude = (depth: number, color: string = C.orange, step = 1) => {
  const s: string[] = [];
  for (let i = step; i <= depth; i += step) s.push(`${i}px ${i}px 0 ${color}`);
  return s.join(', ') || 'none';
};
