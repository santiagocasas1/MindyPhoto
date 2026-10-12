import React from "react";
import { Composition } from "remotion";
import { Commercial } from "./Commercial";
import T from "../config/timeline.json";

export const RemotionRoot: React.FC = () => (
  <Composition
    id="AFMCommercial"
    component={Commercial}
    durationInFrames={T.duration * T.fps}
    fps={T.fps}
    width={T.width}
    height={T.height}
  />
);
