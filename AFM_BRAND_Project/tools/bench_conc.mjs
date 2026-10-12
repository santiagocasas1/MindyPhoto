import { bundle } from "@remotion/bundler";
import { renderFrames, selectComposition } from "@remotion/renderer";
import path from "node:path";
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const opts = { serveUrl, browserExecutable: process.env.AFM_BROWSER, chromiumOptions: { gl: "swangle" } };
const composition = await selectComposition({ ...opts, id: "AFMCommercial" });
for (const c of [2, 3]) {
  const t0 = Date.now();
  await renderFrames({ ...opts, composition, frameRange: [400, 423], outputDir: "out/bench", imageFormat: "png", concurrency: c, onStart: () => {} });
  console.log(`concurrency ${c}: ${((Date.now() - t0) / 24000).toFixed(2)} s/frame`);
}
