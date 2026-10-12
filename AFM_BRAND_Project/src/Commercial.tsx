import React, { useEffect, useState } from "react";
import { AbsoluteFill, Audio, continueRender, delayRender, staticFile, useCurrentFrame, getStaticFiles, getInputProps } from "remotion";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/jost/500.css";
import "@fontsource/jost/600.css";
import "@fontsource/jost/700.css";
import { PhoneCanvas } from "./three/PhoneCanvas";
import { PhoneUI } from "./ui/PhoneUI";
import { Background, Products, Dust } from "./layers/World";
import { Supers, LightArc, EndCard, Finishing } from "./layers/Overlay";
import { rigAt } from "./lib/choreo";
import T from "../config/timeline.json";

const useFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    const specs = ["400 20px Inter", "500 20px Inter", "600 20px Inter", "700 20px Inter", "500 20px Jost", "600 20px Jost", "700 20px Jost", "20px 'Noto Color Emoji'"];
    Promise.all(specs.map((s) => document.fonts.load(s, "AÁá¿?🇰🇷🙌")))
      .then(() => document.fonts.ready)
      .then(() => continueRender(handle));
  }, [handle]);
};

// debug/perf: --props='{"skip":["phone","ui"]}' hides layers
const SKIP: string[] = (getInputProps() as { skip?: string[] }).skip ?? [];
const hasAudio = getStaticFiles().some((f) => f.name === "audio/soundtrack.wav");

export const Commercial: React.FC = () => {
  useFonts();
  const frame = useCurrentFrame();
  const t = frame / T.fps;
  const rig = rigAt(t);
  return (
    <AbsoluteFill style={{ background: "#060607", overflow: "hidden" }}>
      {!SKIP.includes("bg") && <Background rig={rig} />}
      {!SKIP.includes("phone") && <PhoneCanvas rig={rig} />}
      {!SKIP.includes("ui") && <PhoneUI rig={rig} />}
      {!SKIP.includes("products") && <Products rig={rig} />}
      <LightArc rig={rig} />
      {!SKIP.includes("dust") && <Dust rig={rig} />}
      <Supers t={t} />
      <EndCard t={t} />
      {!SKIP.includes("finish") && <Finishing t={t} frame={frame} />}
      {hasAudio && <Audio src={staticFile("audio/soundtrack.wav")} />}
    </AbsoluteFill>
  );
};
