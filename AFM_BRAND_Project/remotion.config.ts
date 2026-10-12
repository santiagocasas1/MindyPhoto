import { Config } from "@remotion/cli/config";

// Software WebGL (no GPU in the render box): SwiftShader through ANGLE.
Config.setChromiumOpenGlRenderer("swangle");
// Use the locally installed headless shell when present (no download needed).
if (process.env.AFM_BROWSER) Config.setBrowserExecutable(process.env.AFM_BROWSER);
Config.setVideoImageFormat("png");
Config.setConcurrency(Number(process.env.AFM_CONCURRENCY ?? 2));
Config.setDelayRenderTimeoutInMilliseconds(120000);
