// Time a few full-res frames (perf check).  node tools/bench.mjs 300 560 700
import { bundle } from "@remotion/bundler";
import { renderFrames, selectComposition } from "@remotion/renderer";
import path from "node:path";
const frames = process.argv.slice(2).map(Number);
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const opts = { serveUrl, browserExecutable: process.env.AFM_BROWSER, chromiumOptions: { gl: "swangle" } };
const inputProps = JSON.parse(process.env.AFM_PROPS ?? "{}");
const composition = await selectComposition({ ...opts, id: "AFMCommercial", inputProps });
for (const f of frames) {
  const t0 = Date.now();
  await renderFrames({ ...opts, composition, frameRange: [f, f + 5], outputDir: "out/bench", imageFormat: "png", concurrency: 1, inputProps, onStart: () => {} });
  console.log(`frames ${f}-${f + 5}: ${((Date.now() - t0) / 6000).toFixed(2)} s/frame`);
}
