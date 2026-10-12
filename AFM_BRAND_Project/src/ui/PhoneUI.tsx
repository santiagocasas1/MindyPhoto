// The AFM BRAND web store as seen on the phone. Built as real HTML (crisp text, the
// store's real catalog photos) and mapped onto the 3D display with a homography.
import React from "react";
import { Img } from "remotion";
import { Rig, displayQuad, homography } from "../lib/choreo";
import { prog, ease, clamp, mix, window01 } from "../lib/anim";
import { BRANDS, C, COPY, LOGO, BANNER, bySku, packshot, brandIndexAt } from "../lib/data";

export const UW = 390, UH = 824, Z = 4; // logical points, rasterised at 4x
const RADIUS = 51;
const RED = "#D62210"; // the store's button colour
const FONT = "Inter, system-ui, sans-serif";

// ---------------------------------------------------------------- shared bits
const StatusBar: React.FC<{ dark?: boolean }> = ({ dark }) => {
  const c = dark ? "#fff" : "#0a0a0a";
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: UW, height: 54, color: c, fontFamily: FONT, zIndex: 50 }}>
      <div style={{ position: "absolute", left: 38, top: 17, fontSize: 16, fontWeight: 600 }}>21:47</div>
      <div style={{ position: "absolute", left: (UW - 124) / 2, top: 11, width: 124, height: 36, borderRadius: 18, background: "#000" }} />
      <div style={{ position: "absolute", right: 30, top: 19, display: "flex", gap: 6, alignItems: "center" }}>
        <svg width="18" height="12" viewBox="0 0 18 12">{[0, 1, 2, 3].map((i) => <rect key={i} x={i * 4.6} y={9 - i * 3} width="3.2" height={3 + i * 3} rx="1" fill={c} />)}</svg>
        <svg width="16" height="12" viewBox="0 0 16 12"><path d="M8 11.5 L10.6 8.6 A3.8 3.8 0 0 0 5.4 8.6 Z M2.6 5.8 A7.6 7.6 0 0 1 13.4 5.8 L12 7.3 A5.6 5.6 0 0 0 4 7.3 Z M0 3 A11.3 11.3 0 0 1 16 3 L14.6 4.5 A9.3 9.3 0 0 0 1.4 4.5 Z" fill={c} /></svg>
        <div style={{ width: 25, height: 12, border: `1.2px solid ${dark ? "rgba(255,255,255,.5)" : "rgba(0,0,0,.4)"}`, borderRadius: 4, padding: 1.5, boxSizing: "border-box" }}>
          <div style={{ width: "78%", height: "100%", background: c, borderRadius: 2 }} />
        </div>
      </div>
    </div>
  );
};

const HomeIndicator: React.FC<{ dark?: boolean }> = ({ dark }) => (
  <div style={{ position: "absolute", left: (UW - 134) / 2, bottom: 8, width: 134, height: 5, borderRadius: 3, background: dark ? "rgba(255,255,255,.85)" : "rgba(0,0,0,.85)", zIndex: 60 }} />
);

const CartIcon: React.FC<{ count: number; pop: number }> = ({ count, pop }) => (
  <div style={{ position: "relative", width: 28, height: 28 }}>
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#111" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 4h2.2l2.1 10.2a1.6 1.6 0 0 0 1.6 1.3h8.4a1.6 1.6 0 0 0 1.6-1.2L21 8H6.1" />
      <circle cx="9.5" cy="19.5" r="1.4" /><circle cx="17" cy="19.5" r="1.4" />
    </svg>
    <div style={{
      position: "absolute", right: -7, top: -6, minWidth: 19, height: 19, borderRadius: 10, background: RED, color: "#fff",
      fontSize: 12, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT,
      transform: `scale(${1 + 0.45 * pop})`,
    }}>{count}</div>
  </div>
);

const StoreHeader: React.FC<{ count: number; pop: number }> = ({ count, pop }) => (
  <div style={{ position: "absolute", left: 0, top: 54, width: UW, height: 58, background: "#fff", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 18px", boxSizing: "border-box", borderBottom: "1px solid #eee", zIndex: 40 }}>
    <svg width="24" height="24" viewBox="0 0 24 24" stroke="#111" strokeWidth="1.8" strokeLinecap="round"><path d="M4 7h16M4 12h16M4 17h16" /></svg>
    <Img src={LOGO.trim} style={{ height: 40, position: "absolute", left: "50%", transform: "translateX(-50%)" }} />
    <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#111" strokeWidth="1.7"><circle cx="12" cy="8.5" r="3.8" /><path d="M4.5 20.5c1.2-3.6 4-5.3 7.5-5.3s6.3 1.7 7.5 5.3" strokeLinecap="round" /></svg>
      <CartIcon count={count} pop={pop} />
    </div>
  </div>
);

// ---------------------------------------------------------------- screens
const LockScreen: React.FC<{ t: number }> = ({ t }) => {
  const n = prog(t, C.notification, C.notification + 0.55, ease.out);
  const press = window01(t, C.tapNotification - 0.12, C.tapNotification + 0.2, 0.08, 0.12);
  return (
    <div style={{ position: "absolute", inset: 0, background: "radial-gradient(120% 70% at 50% 108%, #7a0f0b 0%, #2c0708 45%, #0b0506 75%, #050405 100%)", fontFamily: FONT, color: "#fff" }}>
      <div style={{ position: "absolute", top: 96, width: UW, textAlign: "center", fontSize: 18, fontWeight: 600, opacity: 0.85 }}>lunes, 12 de octubre</div>
      <div style={{ position: "absolute", top: 112, width: UW, textAlign: "center", fontSize: 92, fontWeight: 600, letterSpacing: -3, lineHeight: 1.1 }}>21:47</div>
      <div style={{
        position: "absolute", left: 12, top: 300, width: UW - 24, borderRadius: 22, padding: "13px 14px", boxSizing: "border-box",
        background: "rgba(244,242,240,0.86)", color: "#111", display: "flex", gap: 11, alignItems: "flex-start",
        opacity: n, transform: `translateY(${mix(-36, 0, n)}px) scale(${mix(0.94, 1, n) * (1 - 0.025 * press)})`,
        boxShadow: "0 10px 30px rgba(0,0,0,.35)",
      }}>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, boxShadow: "0 0 0 0.5px rgba(0,0,0,.12)" }}>
          <Img src={LOGO.trim} style={{ width: 34 }} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 15, fontWeight: 600 }}>
            <span>{COPY.notificationTitle}</span><span style={{ fontWeight: 400, color: "#666", fontSize: 13 }}>ahora</span>
          </div>
          <div style={{ fontSize: 15, marginTop: 2, lineHeight: 1.3 }}>{COPY.notificationBody}</div>
        </div>
      </div>
      {[0, 1].map((i) => (
        <div key={i} style={{ position: "absolute", bottom: 54, [i ? "right" : "left"]: 46, width: 50, height: 50, borderRadius: 25, background: "rgba(255,255,255,.14)" } as React.CSSProperties} />
      ))}
    </div>
  );
};

/** Splash / welcome: the ORIGINAL logo revealed by masks (red dome sweep, then lettering). */
export const LogoReveal: React.FC<{ width: number; sweep: number; ink: number; glint?: number }> = ({ width, sweep, ink, glint = 0 }) => {
  const h = (width * LOGO.h) / LOGO.w;
  const ang = sweep * 184 - 2; // degrees travelled along the dome, from the left foot
  const cx = LOGO.domeCx * 100, cy = LOGO.domeCy * 100;
  const mask = `conic-gradient(from 268deg at ${cx}% ${cy}%, #000 0deg, #000 ${Math.max(0, ang)}deg, transparent ${Math.max(0, ang) + 6}deg)`;
  const headA = ((-180 + ang) * Math.PI) / 180;
  const R = LOGO.domeR * width;
  const hx = LOGO.domeCx * width + Math.cos(headA) * R;
  const hy = LOGO.domeCy * h + Math.sin(headA) * R;
  return (
    <div style={{ position: "relative", width, height: h }}>
      <Img src={LOGO.ink} style={{ position: "absolute", inset: 0, width, height: h, opacity: ink, clipPath: `inset(${(1 - ink) * 30}% 0 0 0)` }} />
      <Img src={LOGO.red} style={{ position: "absolute", inset: 0, width, height: h, WebkitMaskImage: sweep >= 1 ? undefined : mask, maskImage: sweep >= 1 ? undefined : mask }} />
      {sweep > 0 && sweep < 1 && (
        <div style={{ position: "absolute", left: hx - width * 0.06, top: hy - width * 0.06, width: width * 0.12, height: width * 0.12, borderRadius: "50%", background: "radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(255,90,70,.75) 22%, rgba(236,9,10,0) 70%)" }} />
      )}
      {glint > 0 && glint < 1 && (
        <div style={{
          position: "absolute", inset: 0, WebkitMaskImage: `url(${LOGO.trim})`, maskImage: `url(${LOGO.trim})`, WebkitMaskSize: "100% 100%", maskSize: "100% 100%",
          background: `linear-gradient(105deg, transparent ${glint * 140 - 30}%, rgba(255,255,255,.75) ${glint * 140 - 15}%, transparent ${glint * 140}%)`,
        }} />
      )}
    </div>
  );
};

const Splash: React.FC<{ t: number }> = ({ t }) => {
  const sweep = prog(t, C.impactReveal, C.impactReveal + 0.65, ease.inOutSoft);
  const ink = prog(t, C.impactReveal + 0.22, C.impactReveal + 0.85, ease.out);
  const glint = prog(t, 4.75, 5.45, ease.inOut);
  const w1 = prog(t, C.taglineIn + 0.25, C.taglineIn + 0.75, ease.out);
  const w2 = prog(t, C.taglineIn + 0.42, C.taglineIn + 0.92, ease.out);
  const w3 = prog(t, 5.95, 6.45, ease.out);
  const press = window01(t, C.tapExplore - 0.1, C.tapExplore + 0.2, 0.06, 0.12);
  const settle = prog(t, 4.95, 5.6, ease.inOut);
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff", fontFamily: FONT }}>
      <div style={{ position: "absolute", left: (UW - 316) / 2, top: mix(300, 160, settle) }}>
        <LogoReveal width={316} sweep={sweep} ink={ink} glint={glint} />
      </div>
      <div style={{ position: "absolute", top: 392, width: UW, textAlign: "center", opacity: w1, transform: `translateY(${(1 - w1) * 14}px)` }}>
        <div style={{ fontSize: 23, fontWeight: 500, letterSpacing: 0.5, color: "#111" }}>{COPY.welcome}</div>
      </div>
      <div style={{ position: "absolute", top: 434, left: 40, width: UW - 80, textAlign: "center", opacity: w2, transform: `translateY(${(1 - w2) * 14}px)`, fontSize: 17, lineHeight: 1.4, color: "#333" }}>
        {COPY.tagline}
      </div>
      <div style={{
        position: "absolute", top: 540, left: 45, width: UW - 90, height: 54, borderRadius: 6, background: RED, color: "#fff",
        display: "flex", alignItems: "center", justifyContent: "center", fontSize: 17, fontWeight: 600, letterSpacing: 0.3,
        opacity: w3, transform: `translateY(${(1 - w3) * 16}px) scale(${1 - 0.04 * press})`, filter: `brightness(${1 - 0.12 * press})`,
      }}>Explorar productos</div>
    </div>
  );
};

const Tile: React.FC<{ sku: string }> = ({ sku }) => (
  <div style={{ width: 171, fontFamily: FONT }}>
    <div style={{ width: 171, height: 171, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
      <Img src={packshot(sku)} style={{ width: 171, height: 171, objectFit: "cover" }} />
    </div>
    <div style={{ fontSize: 13, color: "#222", lineHeight: 1.3, marginTop: 8, height: 34, overflow: "hidden" }}>{bySku[sku].name}</div>
  </div>
);

const HOME_TILES = ["8OKFSPWML", "8LOTMKORG", "8LOTPPCCK", "8HTBCOPEA", "8LOTSHSTR", "8LOTSRORG", "8OKFSPSTR", "8LOTMKBAN"];
const CHIPS = ["BEBIDAS", "SNACKS", "GALLETITAS", "CHOCOLATES", "ALCOHÓLICAS", "COMIDAS"];

const Home: React.FC<{ t: number; count: number; pop: number }> = ({ t, count, pop }) => {
  const scroll = prog(t, 8.05, 8.78, ease.out) * 395;
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff", fontFamily: FONT, overflow: "hidden" }}>
      <div style={{ position: "absolute", left: 0, top: 112 - scroll, width: UW }}>
        <div style={{ margin: "8px 16px 0", height: 44, display: "flex", border: "1px solid #ddd", borderRadius: 2 }}>
          <div style={{ flex: 1, padding: "0 12px", display: "flex", alignItems: "center", color: "#999", fontSize: 15 }}>¿Qué estás buscando?</div>
          <div style={{ width: 44, background: RED, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2"><circle cx="11" cy="11" r="6.5" /><path d="M16 16l4.5 4.5" strokeLinecap="round" /></svg>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, padding: "14px 16px 0", whiteSpace: "nowrap" }}>
          {CHIPS.map((c, i) => (
            <div key={c} style={{ padding: "8px 12px", borderRadius: 16, fontSize: 12, fontWeight: 600, letterSpacing: 0.4, background: i === 0 ? "#111" : "#f2f2f2", color: i === 0 ? "#fff" : "#222" }}>{c}</div>
          ))}
        </div>
        <Img src={BANNER} style={{ width: UW - 32, margin: "14px 16px 0", display: "block", borderRadius: 4 }} />
        <div style={{ fontSize: 26, fontWeight: 500, margin: "22px 16px 14px", color: "#111" }}>Destacados</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "18px 16px", padding: "0 16px" }}>
          {HOME_TILES.map((s) => <Tile key={s} sku={s} />)}
        </div>
      </div>
      <StoreHeader count={count} pop={pop} />
    </div>
  );
};

const ProductPage: React.FC<{ i: number; t: number; count: number; pop: number; added: number }> = ({ i, t, count, pop, added }) => {
  const b = BRANDS[i];
  const p = bySku[b.hero];
  const press = window01(t, C.addToCart[i] - 0.1, C.addToCart[i] + 0.2, 0.06, 0.14);
  const crumbs = b.label.split(" · ");
  const similar = b.variants.length ? b.variants : ["8LOTPPCCK"];
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff", fontFamily: FONT }}>
      <div style={{ position: "absolute", top: 122, left: 18, fontSize: 12, color: "#777" }}>Inicio › {crumbs.join(" › ")}</div>
      <div style={{ position: "absolute", top: 146, left: 30, width: 330, height: 330 }}>
        <Img src={packshot(b.hero)} style={{ width: 330, height: 330, objectFit: "contain" }} />
      </div>
      <div style={{ position: "absolute", top: 488, left: 18, fontSize: 12, fontWeight: 700, letterSpacing: 1.6, color: RED }}>{b.name.toUpperCase()}</div>
      <div style={{ position: "absolute", top: 508, left: 18, width: UW - 36, fontSize: 22, fontWeight: 500, lineHeight: 1.25, color: "#111" }}>{p.name}</div>
      <div style={{ position: "absolute", top: 576, left: 18, fontSize: 12.5, color: "#555", display: "flex", gap: 6, alignItems: "center" }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#555" strokeWidth="2"><path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6z" /></svg>
        Compra protegida
      </div>
      <div style={{ position: "absolute", top: 606, left: 18, width: 104, height: 50, border: "1px solid #ccc", borderRadius: 4, display: "flex", alignItems: "center", justifyContent: "space-around", fontSize: 18, color: "#111" }}>
        <span>−</span><span style={{ fontWeight: 600 }}>1</span><span>+</span>
      </div>
      <div style={{
        position: "absolute", top: 606, left: 132, width: UW - 150, height: 50, borderRadius: 4, background: added > 0 ? "#111" : RED, color: "#fff",
        display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 600, transform: `scale(${1 - 0.04 * press})`,
      }}>{added > 0 ? "✓ Agregado" : "Agregar al carrito"}</div>
      <div style={{ position: "absolute", top: 680, left: 18, fontSize: 15, fontWeight: 600, color: "#111" }}>Productos similares</div>
      <div style={{ position: "absolute", top: 706, left: 18, display: "flex", gap: 10 }}>
        {similar.map((s) => <Img key={s} src={packshot(s)} style={{ width: 84, height: 84, objectFit: "cover", border: "1px solid #eee" }} />)}
      </div>
      <StoreHeader count={count} pop={pop} />
    </div>
  );
};

const CART = BRANDS.map((b) => b.hero);
const Cart: React.FC<{ t: number; count: number; pop: number }> = ({ t, count, pop }) => {
  const btn = prog(t, 19.65, 20.1, ease.out);
  const press = window01(t, C.tapAdvisor - 0.1, C.tapAdvisor + 0.22, 0.06, 0.14);
  return (
    <div style={{ position: "absolute", inset: 0, background: "#fff", fontFamily: FONT }}>
      <div style={{ position: "absolute", top: 124, left: 18, fontSize: 24, fontWeight: 500, color: "#111" }}>Carrito de compras</div>
      <div style={{ position: "absolute", top: 158, left: 18, fontSize: 13, color: "#777" }}>{CART.length} productos de Corea</div>
      {CART.map((s, k) => {
        const a = prog(t, C.cartAdds[k] - 0.05, C.cartAdds[k] + 0.3, ease.out);
        return (
          <div key={s} style={{ position: "absolute", top: 190 + k * 70, left: 18, width: UW - 36, height: 62, display: "flex", alignItems: "center", gap: 12, opacity: a, transform: `translateX(${(1 - a) * 60}px)`, borderBottom: "1px solid #f0f0f0" }}>
            <Img src={packshot(s)} style={{ width: 56, height: 56, objectFit: "cover", borderRadius: 4 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.2, color: RED }}>{BRANDS[k].name.toUpperCase()}</div>
              <div style={{ fontSize: 13, color: "#222", lineHeight: 1.25, height: 32, overflow: "hidden" }}>{bySku[s].name}</div>
            </div>
            <div style={{ width: 70, height: 30, border: "1px solid #ddd", borderRadius: 15, display: "flex", alignItems: "center", justifyContent: "space-around", fontSize: 14 }}>
              <span>−</span><b>1</b><span>+</span>
            </div>
          </div>
        );
      })}
      <div style={{ position: "absolute", top: 622, left: 18, width: UW - 36, height: 50, borderRadius: 4, background: RED, color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 600, opacity: btn, transform: `translateY(${(1 - btn) * 14}px)` }}>Iniciar compra</div>
      <div style={{
        position: "absolute", top: 684, left: 18, width: UW - 36, height: 50, borderRadius: 4, border: "1.5px solid #1FA855", color: "#13863f",
        display: "flex", alignItems: "center", justifyContent: "center", gap: 8, fontSize: 16, fontWeight: 600, opacity: btn,
        transform: `translateY(${(1 - btn) * 14}px) scale(${1 - 0.04 * press})`, background: press > 0 ? "rgba(31,168,85,.12)" : "#fff",
      }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#13863f" strokeWidth="2" strokeLinejoin="round"><path d="M4 19.5l1.3-3.8A8 8 0 1 1 8.4 18.6z" /></svg>
        Hablar con un asesor
      </div>
      <StoreHeader count={count} pop={pop} />
    </div>
  );
};

const Bubble: React.FC<{ from: string; text: string; a: number; time?: string }> = ({ from, text, a, time = "21:48" }) => {
  const me = from === "me";
  return (
    <div style={{ display: "flex", justifyContent: me ? "flex-end" : "flex-start", marginBottom: 8, opacity: a, transform: `translateY(${(1 - a) * 18}px) scale(${mix(0.92, 1, a)})`, transformOrigin: me ? "right bottom" : "left bottom" }}>
      <div style={{ maxWidth: 290, padding: "9px 12px 7px", borderRadius: 15, [me ? "borderBottomRightRadius" : "borderBottomLeftRadius"]: 4, background: me ? "#D9FDD3" : "#fff", fontSize: 17.5, lineHeight: 1.3, color: "#111", boxShadow: "0 1px 1px rgba(0,0,0,.08)" } as React.CSSProperties}>
        {text}
        <span style={{ fontSize: 11, color: "#6b7a72", marginLeft: 8, whiteSpace: "nowrap", float: "right", marginTop: 6 }}>{time}{me ? <span style={{ color: "#3EA6E6", marginLeft: 3 }}>✓✓</span> : null}</span>
      </div>
    </div>
  );
};

const Chat: React.FC<{ t: number }> = ({ t }) => {
  const msgs = COPY.chat;
  const typing = t >= C.typing[0] && t < C.typing[1];
  return (
    <div style={{ position: "absolute", inset: 0, background: "#EFEAE2", fontFamily: FONT }}>
      <div style={{ position: "absolute", top: 0, left: 0, width: UW, height: 122, background: "#fff", borderBottom: "1px solid #e6e6e6" }}>
        <div style={{ position: "absolute", top: 68, left: 14, display: "flex", alignItems: "center", gap: 10 }}>
          <svg width="14" height="22" viewBox="0 0 14 22" fill="none" stroke="#111" strokeWidth="2.2" strokeLinecap="round"><path d="M11 2L3 11l8 9" /></svg>
          <div style={{ width: 42, height: 42, borderRadius: 21, background: "#fff", border: "1px solid #e4e4e4", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Img src={LOGO.trim} style={{ width: 34 }} />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: "#111" }}>AFM BRAND</div>
            <div style={{ fontSize: 12.5, color: "#1FA855" }}>Asesor de ventas · en línea</div>
          </div>
        </div>
      </div>
      <div style={{ position: "absolute", top: 136, left: 0, width: UW, textAlign: "center" }}>
        <span style={{ fontSize: 12, background: "#fff", padding: "4px 10px", borderRadius: 8, color: "#555" }}>Hoy</span>
      </div>
      <div style={{ position: "absolute", top: 176, left: 12, width: UW - 24 }}>
        {msgs.map((m, k) => {
          const a = prog(t, C.chatMessages[k], C.chatMessages[k] + 0.28, ease.out);
          return a > 0 ? <Bubble key={k} from={m.from} text={m.text} a={a} /> : null;
        })}
        {typing && (
          <div style={{ display: "inline-flex", gap: 5, background: "#fff", padding: "13px 14px", borderRadius: 14, borderBottomLeftRadius: 4 }}>
            {[0, 1, 2].map((d) => (
              <div key={d} style={{ width: 8, height: 8, borderRadius: 4, background: "#8a8f8c", opacity: 0.4 + 0.6 * Math.max(0, Math.sin((t * 7 - d * 0.9) * 1.0)) }} />
            ))}
          </div>
        )}
      </div>
      <div style={{ position: "absolute", left: 0, bottom: 0, width: UW, height: 86, background: "#F6F5F3", display: "flex", alignItems: "flex-start", padding: "10px 10px 0", boxSizing: "border-box", gap: 8 }}>
        <div style={{ flex: 1, height: 40, borderRadius: 20, background: "#fff", display: "flex", alignItems: "center", padding: "0 16px", color: "#999", fontSize: 15 }}>Mensaje</div>
        <div style={{ width: 40, height: 40, borderRadius: 20, background: "#1FA855", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="#fff"><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M6 11a6 6 0 0 0 12 0" stroke="#fff" strokeWidth="2" fill="none" /><path d="M12 17v4" stroke="#fff" strokeWidth="2" /></svg>
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- touches
type Tap = { t: number; x: number; y: number };
const TAPS: Tap[] = [
  { t: C.tapNotification, x: 200, y: 340 },
  { t: C.tapExplore, x: 195, y: 567 },
  { t: 8.82, x: 104, y: 420 },
  ...C.addToCart.map((tt) => ({ t: tt, x: 262, y: 631 })),
  { t: C.tapCart, x: 357, y: 82 },
  { t: C.tapAdvisor, x: 195, y: 709 },
];
const Touches: React.FC<{ t: number }> = ({ t }) => (
  <>
    {TAPS.map((p, i) => {
      const pre = prog(t, p.t - 0.16, p.t, ease.out);
      const ring = clamp((t - p.t) / 0.45);
      if (t < p.t - 0.16 || t > p.t + 0.5) return null;
      return (
        <React.Fragment key={i}>
          <div style={{ position: "absolute", left: p.x - 22, top: p.y - 22, width: 44, height: 44, borderRadius: 22, background: "rgba(120,120,128,.38)", opacity: pre * (1 - ring), transform: `scale(${mix(0.6, 1, pre)})`, zIndex: 90 }} />
          {ring > 0 && <div style={{ position: "absolute", left: p.x - 50, top: p.y - 50, width: 100, height: 100, borderRadius: 50, border: "2px solid rgba(120,120,128,.55)", opacity: 1 - ring, transform: `scale(${mix(0.3, 1.1, ease.out(ring))})`, zIndex: 90 }} />}
        </React.Fragment>
      );
    })}
    {/* swipe trails between product pages */}
    {C.brandBeats.slice(1).map((b, i) => {
      const s = clamp((t - (b - 0.42)) / 0.3);
      if (s <= 0 || s >= 1) return null;
      const x = mix(330, 70, ease.inOut(s));
      return <div key={i} style={{ position: "absolute", left: x - 22, top: 320, width: 44, height: 44, borderRadius: 22, background: "rgba(120,120,128,.35)", boxShadow: "30px 0 30px rgba(120,120,128,.18)", zIndex: 90 }} />;
    })}
  </>
);

// ---------------------------------------------------------------- composition of screens
function screenStack(t: number) {
  const count = C.addToCart.filter((a) => t >= a).length;
  const lastAdd = [...C.addToCart].reverse().find((a) => t >= a) ?? -9;
  const pop = Math.max(0, 1 - (t - lastAdd) / 0.3) * (t - lastAdd < 0.3 ? Math.sin(Math.PI * Math.min(1, (t - lastAdd) / 0.3)) : 0);
  const layers: React.ReactNode[] = [];
  const wake = prog(t, C.screenWake, C.screenWake + 0.3, ease.out);

  if (t < 3.6) layers.push(<div key="lock" style={{ position: "absolute", inset: 0, opacity: wake, filter: `brightness(${mix(0.3, 1, wake)})` }}><LockScreen t={t} /></div>);
  // notification morphs into the opened store
  const m = prog(t, 2.72, 3.5, ease.inOut);
  if (t >= 2.72 && t < 7.95) {
    const x = mix(12, 0, m), y = mix(300, 0, m), w = mix(UW - 24, UW, m), h = mix(86, UH, m), r = mix(22, RADIUS, m);
    layers.push(
      <div key="splash" style={{ position: "absolute", left: x, top: y, width: w, height: h, borderRadius: r, overflow: "hidden", background: "#fff" }}>
        {t >= 3.9 && <div style={{ position: "absolute", left: -x, top: -y, width: UW, height: UH }}><Splash t={t} /></div>}
      </div>,
    );
  }
  const homeIn = prog(t, 7.45, 7.95, ease.inOut);
  if (t >= 7.45 && t < 9.25) layers.push(<div key="home" style={{ position: "absolute", inset: 0, transform: `translateY(${(1 - homeIn) * UH}px)`, borderRadius: RADIUS, overflow: "hidden" }}><Home t={t} count={count} pop={pop} /></div>);

  const bi = brandIndexAt(t);
  if (t >= 8.88 && t < 18.35) {
    for (let i = Math.max(0, bi - 1); i <= Math.max(0, bi); i++) {
      const enter = i === 0 ? prog(t, 8.88, 9.2, ease.out) : prog(t, C.brandBeats[i] - 0.38, C.brandBeats[i] + 0.06, ease.snap);
      const leave = i < BRANDS.length - 1 ? prog(t, C.brandBeats[i + 1] - 0.38, C.brandBeats[i + 1] + 0.06, ease.snap) : 0;
      const tx = i === 0 ? 0 : (1 - enter) * UW;
      const ty = i === 0 ? (1 - enter) * 60 : 0;
      layers.push(
        <div key={`p${i}`} style={{ position: "absolute", inset: 0, opacity: i === 0 ? enter : 1, transform: `translate(${tx - leave * UW * 0.3}px, ${ty}px)`, filter: `brightness(${1 - leave * 0.35})` }}>
          <ProductPage i={i} t={t} count={count} pop={pop} added={t >= C.addToCart[i] ? 1 : 0} />
        </div>,
      );
    }
  }
  const cartIn = prog(t, 17.95, 18.3, ease.out);
  if (t >= 17.95 && t < 21.6) layers.push(<div key="cart" style={{ position: "absolute", inset: 0, transform: `translateX(${(1 - cartIn) * UW}px)` }}><Cart t={t} count={count} pop={pop} /></div>);
  const chatIn = prog(t, C.chatOpen, C.chatOpen + 0.4, ease.out);
  if (t >= C.chatOpen) layers.push(<div key="chat" style={{ position: "absolute", inset: 0, transform: `translateX(${(1 - chatIn) * UW}px)` }}><Chat t={t} /></div>);
  const white = prog(t, C.screenToWhite, C.screenToWhite + 0.3, ease.inOut);
  if (white > 0) layers.push(<div key="white" style={{ position: "absolute", inset: 0, background: "#fff", opacity: white }} />);

  const dark = t < 3.25;
  return { layers, dark };
}

export const PhoneUI: React.FC<{ rig: Rig }> = ({ rig }) => {
  const t = rig.t;
  if (rig.facing < 0.08 || t < C.screenWake - 0.02) return null;
  const quad = displayQuad(rig);
  const { layers, dark } = screenStack(t);
  // glass reflection that slides with the viewing angle
  const sheen = 50 + rig.yaw * 2.2;
  const sheenA = dark ? 0.16 : 0.07;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: UW * Z, height: UH * Z, transformOrigin: "0 0", transform: homography(UW * Z, UH * Z, quad), opacity: clamp((rig.facing - 0.08) * 6) }}>
      <div style={{ zoom: Z, position: "relative", width: UW, height: UH, overflow: "hidden", borderRadius: RADIUS, background: "#000" } as React.CSSProperties}>
        {layers}
        <Touches t={t} />
        <StatusBar dark={dark} />
        <HomeIndicator dark={dark} />
        <div style={{ position: "absolute", inset: 0, background: `linear-gradient(118deg, transparent ${sheen - 22}%, rgba(255,255,255,${sheenA}) ${sheen}%, transparent ${sheen + 16}%)`, pointerEvents: "none", zIndex: 99 }} />
      </div>
    </div>
  );
};
