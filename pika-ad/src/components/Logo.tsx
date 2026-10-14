import {useId} from 'react';
import {LOGO, LOGO_LETTERS} from '../brand/logo';
import {C} from '../theme';

export type LetterState = {opacity?: number; scale?: number; x?: number; y?: number; rotate?: number};

/**
 * Logo PIKA vectorial. `depth` controla la extrusión (0 = plano, 1 = la del logo oficial).
 * `letters` permite animar P·I·K·A por separado.
 */
export const Logo: React.FC<{
  width: number;
  depth?: number;
  face?: string;
  shadow?: string;
  letters?: Partial<Record<string, LetterState>>;
  style?: React.CSSProperties;
}> = ({width, depth = 1, face = C.cream, shadow = C.orange, letters = {}, style}) => {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, '');
  const pad = 40;
  const vw = LOGO.width + pad * 2;
  const vh = LOGO.height + pad * 2;
  const d = LOGO.dx * depth;
  const steps = Math.max(0, Math.ceil(d / 1.5));
  return (
    <svg width={width} height={(width * vh) / vw} viewBox={`${-pad} ${-pad} ${vw} ${vh}`} style={{overflow: 'visible', ...style}}>
      <defs>
        {LOGO_LETTERS.filter((l) => l.clip).map((l) => (
          <clipPath key={l.id} id={`${uid}${l.id}`}>
            <polygon points={l.clip} />
          </clipPath>
        ))}
      </defs>
      {LOGO_LETTERS.map((l) => {
        const st = letters[l.id] ?? {};
        const op = st.opacity ?? 1;
        if (op <= 0) return null;
        const sc = st.scale ?? 1;
        const tr = `translate(${(st.x ?? 0) + l.cx} ${(st.y ?? 0) + l.cy}) rotate(${st.rotate ?? 0}) scale(${sc}) translate(${-l.cx} ${-l.cy})`;
        const clip = l.clip ? `url(#${uid}${l.id})` : undefined;
        return (
          <g key={l.id} transform={tr} opacity={op}>
            {Array.from({length: steps}, (_, i) => {
              const o = d * ((steps - i) / steps);
              return (
                <g key={i} transform={`translate(${o} ${o})`}>
                  <path d={l.d} fill={shadow} fillRule="evenodd" clipPath={clip} />
                </g>
              );
            })}
            <path d={l.d} fill={face} fillRule="evenodd" clipPath={clip} />
          </g>
        );
      })}
    </svg>
  );
};
