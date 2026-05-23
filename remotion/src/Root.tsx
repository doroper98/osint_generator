import React from "react";
import { Composition } from "remotion";
import {
  Briefing,
  BriefingProps,
  DEFAULT_PROPS,
  FPS,
  HEIGHT,
  WIDTH,
} from "./Briefing";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Briefing"
      component={Briefing}
      durationInFrames={150}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
      defaultProps={DEFAULT_PROPS}
      calculateMetadata={({ props }: { props: BriefingProps }) => {
        const total = props.scenes.reduce((acc, s) => acc + s.durationSec, 0);
        return {
          durationInFrames: Math.max(1, Math.round((total || 5) * FPS)),
        };
      }}
    />
  );
};
