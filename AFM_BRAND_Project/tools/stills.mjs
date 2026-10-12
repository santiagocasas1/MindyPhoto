// Render a handful of frames quickly for look-dev / QA:  node tools/stills.mjs out/dir 0 45 120 ...
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";
import fs from "node:fs";

const [outDir, ...frames] = process.argv.slice(2);
const scale = Number(process.env.AFM_SCALE ?? 0.5);
fs.mkdirSync(outDir, { recursive: true });
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const opts = {
  serveUrl,
  browserExecutable: process.env.AFM_BROWSER,
  chromiumOptions: { gl: "swangle" },
};
const composition = await selectComposition({ ...opts, id: "AFMCommercial" });
for (const f of frames.map(Number)) {
  await renderStill({ ...opts, composition, frame: f, output: path.join(outDir, `f${String(f).padStart(3, "0")}.png`), scale, timeoutInMilliseconds: 120000 });
  process.stdout.write(`${f} `);
}
console.log("done");
