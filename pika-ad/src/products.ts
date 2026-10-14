import {staticFile} from 'remotion';

export type Product = {file: string; name: string; short: string; kr: string; w: number; h: number};

const p = (file: string, name: string, short: string, kr: string, w: number, h: number): Product => ({
  file: staticFile(`products/${file}.webp`),
  name,
  short,
  kr,
  w,
  h,
});

// Productos reales del catálogo de pikakstore.mitiendanube.com (fondo recortado).
export const P = {
  volcano: p('volcano-chicken-hot-spicy-noodle-105g', 'VOLCANO CHICKEN HOT & SPICY', 'VOLCANO CHICKEN', '라면', 1004, 888),
  kimchiCup: p('mr-kimchi-noodles-king-cup-110g', 'MR. KIMCHI NOODLES KING CUP', 'MR. KIMCHI KING CUP', '라면', 964, 964),
  carbonara: p('topokki-spicy-carbonara-120-g', 'TOPOKKI SPICY CARBONARA', 'TOPOKKI CARBONARA', '떡볶이', 850, 952),
  sweetSpicy: p('topokki-sweet-spicy-140-g', 'TOPOKKI SWEET & SPICY', 'TOPOKKI SWEET&SPICY', '떡볶이', 498, 582),
  bigball: p('bigball-grape-340-ml', 'BIG BALL GRAPE', 'BIG BALL GRAPE', '음료', 556, 1001),
  soju: p('soonhari-soju-lychee-360-ml', 'SOONHARI SOJU LYCHEE', 'SOJU LYCHEE', '소주', 300, 999),
  pocachip: p('pocachip-original-66-g', 'POCACHIP ORIGINAL', 'POCACHIP ORIGINAL', '스낵', 324, 481),
  oreo: p('oreo-bts-hotteok-flavor-100-g', 'OREO BTS HOTTEOK', 'OREO BTS HOTTEOK', '과자', 1018, 466),
  jelly: p('tik-tok-jelly-strawberry-160-g', 'TIK TOK JELLY STRAWBERRY', 'TIK TOK JELLY', '젤리', 615, 725),
  chocopick: p('chocopick-biscuit-45g', 'CHOCO PICK BISCUIT', 'CHOCO PICK', '과자', 300, 600),
  seafood: p('king-cup-noodle-seafood-110g', 'KING CUP SEAFOOD', 'KING CUP SEAFOOD', '라면', 886, 730),
  bibimmenCup: p('bibimmen-cup-115g', 'BIBIMMEN CUP', 'BIBIMMEN CUP', '라면', 1005, 845),
  bibimmen: p('bibimmen-spicy-sweet-sour-noodles-130-gr', 'BIBIMMEN', 'BIBIMMEN', '라면', 842, 648),
  maxim: p('maxim-ice-coffee-mix-110t', 'MAXIM ICE COFFEE', 'MAXIM ICE COFFEE', '커피', 564, 868),
  kokomen: p('kokomen-spicy-chicken-noodle-120-gr', 'KOKOMEN', 'KOKOMEN', '라면', 358, 445),
  kimchi: p('mr-kimchi-115-gr', 'MR. KIMCHI', 'MR. KIMCHI', '라면', 446, 334),
  omori: p('omori-stew-tuna-noodle-cup-135-g', 'OMORI TUNA', 'OMORI TUNA', '라면', 403, 307),
  shoyu: p('ramen-shoyu-75ml', 'RAMEN SHOYU', 'RAMEN SHOYU', '라면', 264, 362),
  jellyGrape: p('tik-tok-jelly-grape-160-g', 'TIK TOK JELLY GRAPE', 'TIK TOK GRAPE', '젤리', 617, 726),
  tuemsae: p('tuemsae-spicy-noodles-120g', 'TEUMSAE', 'TEUMSAE', '라면', 433, 518),
  wang: p('wang-kumtuli-fruta-mix-75-gr', 'WANG KKUMTEULI', 'WANG KKUMTEULI', '젤리', 261, 346),
  pomegranate: p('wj-nature-s-pomegramate-180-ml', 'WJ POMEGRANATE', 'WJ POMEGRANATE', '음료', 399, 1013),
};

/** Ajusta un producto dentro de una caja manteniendo proporción. */
export const fit = (pr: Product, maxW: number, maxH: number) => {
  const s = Math.min(maxW / pr.w, maxH / pr.h);
  return {width: pr.w * s, height: pr.h * s};
};
