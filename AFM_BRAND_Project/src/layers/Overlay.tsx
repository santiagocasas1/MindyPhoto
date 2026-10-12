// Typography, the hook's light arc, the end card and the finishing pass.
import React, { useMemo } from "react";
import { Rig, projectLocal, pxPerMm, W, H } from "../lib/choreo";
import { prog, ease, mix, clamp, rgba, rng, window01 } from "../lib/anim";
import { BRANDS, C, COPY, PAL } from "../lib/data";
import { LogoReveal } from "../ui/PhoneUI";

const JOST = "Jost, Futura, sans-serif";
const INTER = "Inter, system-ui, sans-serif";

/** A line of display type that rises out of a mask and leaves with a soft blur. */
const Line: React.FC<{ text: string; t: number; tin: number; tout: number; size: number; top: number; weight?: number; color?: string; dx?: number; spacing?: number }> = ({ text, t, tin, tout, size, top, weight = 600, color = "#fff", dx = 0, spacing = -0.01 }) => {
  const a = prog(t, tin, tin + 0.5, ease.out);
  const o = prog(t, tout - 0.32, tout, ease.in);
  if (a <= 0 || o >= 1) return null;
  return (
    <div style={{ position: "absolute", left: 0, top, width: W, height: size * 1.25, overflow: "hidden", display: "flex", justifyContent: "center" }}>
      <div style={{
        fontFamily: JOST, fontWeight: weight, fontSize: size, lineHeight: 1.15, color, letterSpacing: `${spacing}em`, whiteSpace: "nowrap",
        transform: `translate(${dx * (1 - a)}px, ${(1 - a) * size * 1.1 - o * size * 0.35}px)`, opacity: 1 - o, filter: o > 0 ? `blur(${o * 14}px)` : undefined,
        textShadow: "0 6px 40px rgba(0,0,0,.45)",
      }}>{text}</div>
    </div>
  );
};

export const Supers: React.FC<{ t: number }> = ({ t }) => {
  const B = C.brandBeats;
  const bi = B.findIndex((b, i) => t >= b - 0.12 && t < (B[i + 1] ?? 18.0) - 0.12);
  const legal = window01(t, 14.85, 18.05, 0.25, 0.25);
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      {/* hook */}
      <Line text={COPY.hook[0]} t={t} tin={0.3} tout={3.55} size={118} top={250} />
      <Line text={COPY.hook[1]} t={t} tin={0.48} tout={3.65} size={118} top={392} />
      {/* explore */}
      <Line text={COPY.explore} t={t} tin={8.0} tout={8.95} size={120} top={262} />
      {bi >= 0 && (
        <React.Fragment key={bi}>
          <Line text={BRANDS[bi].name} t={t} tin={B[bi] - 0.1} tout={(B[bi + 1] ?? 18.0) - 0.1} size={150} top={226} weight={700} dx={BRANDS[bi].side * 140} spacing={-0.02} />
          <Line text={BRANDS[bi].label} t={t} tin={B[bi] + 0.08} tout={(B[bi + 1] ?? 18.0) - 0.12} size={30} top={414} weight={500} color="rgba(255,255,255,.82)" spacing={0.26} />
        </React.Fragment>
      )}
      {/* order / advisor */}
      <Line text={COPY.order} t={t} tin={18.05} tout={21.05} size={104} top={262} />
      <Line text="Hablá con" t={t} tin={21.95} tout={23.05} size={104} top={210} />
      <Line text="un asesor" t={t} tin={22.07} tout={23.12} size={104} top={340} />
      {legal > 0 && (
        <div style={{ position: "absolute", left: 110, width: W - 220, top: 1418, padding: "16px 22px", boxSizing: "border-box", borderRadius: 14, background: `rgba(8,8,10,${0.82 * legal})`, border: `1px solid rgba(255,255,255,${0.14 * legal})`, textAlign: "center", fontFamily: INTER, fontWeight: 600, fontSize: 25, lineHeight: 1.38, letterSpacing: "0.04em", color: `rgba(255,255,255,${0.95 * legal})` }}>
          {COPY.alcoholLegal}
        </div>
      )}
    </div>
  );
};

/** Hook: the dome of the AFM logo traced as a single light stroke around the phone. */
export const LightArc: React.FC<{ rig: Rig }> = ({ rig }) => {
  const t = rig.t;
  if (t > 2.2) return null;
  const [a0, a1] = C.arcSweep;
  // already in motion on frame 0, so the very first frame carries the red stroke
  const p = Math.sin((Math.PI / 2) * clamp((t - (a0 - 0.3)) / (a1 + 0.3 - a0)));
  const fade = 1 - prog(t, 1.2, 2.1, ease.inOut);
  const c = projectLocal(rig, 0, 0, 0);
  const cx = W / 2, cy = c.y + 70, R = 470;
  const len = Math.PI * R;
  const head = p * len;
  const trail = len * 0.55;
  const arc = `M ${cx - R} ${cy} A ${R} ${R} 0 0 1 ${cx + R} ${cy}`;
  const ha = Math.PI * (1 - p);
  const hx = cx + Math.cos(ha) * R, hy = cy - Math.sin(ha) * R;
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14" /></filter>
        <linearGradient id="arcg" gradientUnits="userSpaceOnUse" x1={cx - R} y1={cy} x2={cx + R} y2={cy}>
          <stop offset="0" stopColor={PAL.afmRed} /><stop offset="1" stopColor="#ff5a3c" />
        </linearGradient>
      </defs>
      <g opacity={fade}>
        <path d={arc} stroke="url(#arcg)" strokeWidth={16} fill="none" filter="url(#glow)" strokeDasharray={`${Math.min(head, trail)} ${len * 2}`} strokeDashoffset={-Math.max(0, head - trail)} opacity={0.75} />
        <path d={arc} stroke="url(#arcg)" strokeWidth={4} fill="none" strokeLinecap="round" strokeDasharray={`${Math.min(head, len)} ${len * 2}`} strokeDashoffset={0} opacity={0.9} />
        {p < 1 && <circle cx={hx} cy={hy} r={9} fill="#fff" filter="url(#glow)" />}
        {p < 1 && <circle cx={hx} cy={hy} r={3.5} fill="#fff" />}
      </g>
    </svg>
  );
};

/** End card: the original logo, the store's own tagline and real contact points. */
export const EndCard: React.FC<{ t: number }> = ({ t }) => {
  const [d0, d1] = C.dive;
  const white = prog(t, d1 - 0.16, d1, ease.inOut);
  if (white <= 0) return null;
  const [l0, l1] = C.logoDraw;
  const sweep = prog(t, l0, l1 - 0.1, ease.inOutSoft);
  const ink = prog(t, l0 + 0.3, l1 + 0.1, ease.out);
  const glint = prog(t, 27.4, 28.1, ease.inOut);
  const settle = prog(t, d1, C.holdFrom, ease.out);
  const tg = prog(t, C.endTagline, C.endTagline + 0.6, ease.out);
  const cta = prog(t, C.endCta, C.endCta + 0.6, ease.out);
  const rule = prog(t, C.endCta - 0.1, C.endCta + 0.5, ease.out);
  const LW = 760;
  void d0;
  return (
    <div style={{ position: "absolute", inset: 0, opacity: white, background: "radial-gradient(90% 60% at 50% 40%, #ffffff 0%, #fbfaf8 60%, #f1eeea 100%)" }}>
      <div style={{ position: "absolute", left: (W - LW) / 2, top: 486, transform: `scale(${mix(1.06, 1, settle)})`, transformOrigin: "50% 60%" }}>
        <LogoReveal width={LW} sweep={sweep} ink={ink} glint={glint} />
      </div>
      <div style={{ position: "absolute", top: 1010, width: W, textAlign: "center", fontFamily: JOST, fontWeight: 500, fontSize: 44, lineHeight: 1.28, color: "#1b1b1d", opacity: tg, transform: `translateY(${(1 - tg) * 22}px)` }}>
        ¡Tu puente directo a lo mejor<br />de Corea y el Mundo!
      </div>
      <div style={{ position: "absolute", top: 1172, left: (W - 90) / 2, width: 90, height: 4, background: PAL.afmRed, transform: `scaleX(${rule})` }} />
      <div style={{ position: "absolute", top: 1210, width: W, textAlign: "center", opacity: cta, transform: `translateY(${(1 - cta) * 18}px)` }}>
        <div style={{ fontFamily: JOST, fontWeight: 600, fontSize: 58, letterSpacing: "0.01em", color: "#111" }}>{COPY.web}</div>
        <div style={{ fontFamily: INTER, fontWeight: 500, fontSize: 35, color: "#2a2a2e", marginTop: 16, letterSpacing: "0.005em" }}>{COPY.whatsapp}</div>
        <div style={{ fontFamily: INTER, fontWeight: 500, fontSize: 35, color: "#2a2a2e", marginTop: 8 }}>{COPY.instagram}</div>
      </div>
    </div>
  );
};

/** Impact bloom and vignette. (Film grain/dither is added at encode time, see tools/render.sh.) */
export const Finishing: React.FC<{ t: number; frame: number }> = ({ t }) => {
  const end = prog(t, C.dive[1] - 0.16, C.dive[1]);
  const drop = Math.max(0, 1 - Math.abs(t - C.drop) / 0.18);
  return (
    <>
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(75% 62% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,.6) 100%)", opacity: 1 - end }} />
      {drop > 0 && <div style={{ position: "absolute", inset: 0, background: "#fff", opacity: 0.12 * drop }} />}
    </>
  );
};

export const _unused = { pxPerMm, clamp, rgba, rng, useMemo };
