import {useId} from 'react';
import {C, F} from '../theme';

/** Sello circular con texto en anillo (como el "SEOUL MOOD / PIKA SELECT" del sitio). */
export const Stamp: React.FC<{
  size: number;
  ring: string;
  center: React.ReactNode;
  rotate?: number;
  bg?: string;
  fg?: string;
  style?: React.CSSProperties;
}> = ({size, ring, center, rotate = 0, bg = C.cream, fg = C.black, style}) => {
  const id = 'st' + useId().replace(/[^a-zA-Z0-9]/g, '');
  const r = 100 - 22;
  return (
    <div style={{width: size, height: size, position: 'relative', ...style}}>
      <svg viewBox="0 0 200 200" width={size} height={size} style={{position: 'absolute', inset: 0}}>
        <circle cx={100} cy={100} r={98} fill={bg} />
        <circle cx={100} cy={100} r={62} fill="none" stroke={fg} strokeWidth={2} strokeDasharray="3 5" />
        <defs>
          <path id={id} d={`M100,100 m-${r},0 a${r},${r} 0 1,1 ${r * 2},0 a${r},${r} 0 1,1 -${r * 2},0`} />
        </defs>
        <g transform={`rotate(${rotate} 100 100)`}>
          <text fill={fg} style={{fontFamily: F.display, fontWeight: 800, fontSize: 17, letterSpacing: 4.2}}>
            <textPath href={`#${id}`}>{ring}</textPath>
          </text>
        </g>
      </svg>
      <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: fg}}>{center}</div>
    </div>
  );
};
