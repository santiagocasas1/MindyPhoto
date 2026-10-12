import { staticFile } from "remotion";
import T from "../../config/timeline.json";
import P from "../../config/products.json";

export type Product = (typeof P.products)[number];
export const bySku = Object.fromEntries(P.products.map((p) => [p.sku, p])) as Record<string, Product>;
export const cutout = (sku: string) => staticFile(`assets/${bySku[sku].file}`);
export const packshot = (sku: string) => staticFile(`assets/${bySku[sku].ui}`);
export const aspect = (sku: string) => bySku[sku].size[0] / bySku[sku].size[1];

export const LOGO = {
  trim: staticFile("assets/brand/afm_logo_trim.png"),
  red: staticFile("assets/brand/afm_logo_layer_red.png"),
  ink: staticFile("assets/brand/afm_logo_layer_ink.png"),
  w: 1831,
  h: 1086,
  // dome circle fitted on the original red strokes (fractions of the trimmed logo box)
  domeCx: 0.4996,
  domeCy: 0.8435,
  domeR: 0.4857,
};
export const BANNER = staticFile("assets/site/banner_okf.webp");

export const C = T.cues;
export const COPY = T.copy;
export const BRANDS = T.brands;
export const PAL = T.palette;

/** index of the brand on screen at time t (explore scene), -1 before the first beat */
export const brandIndexAt = (t: number) => {
  let idx = -1;
  C.brandBeats.forEach((b, i) => {
    if (t >= b - 0.2) idx = i;
  });
  return idx;
};
