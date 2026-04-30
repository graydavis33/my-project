import React from "react";
import { Composition } from "remotion";
import { DayInLife } from "./DayInLife";
import { CLIPS, FPS, WIDTH, HEIGHT } from "./clips";

const TOTAL = CLIPS.reduce((sum, c) => sum + c.durationInFrames, 0);

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DayInLife"
        component={DayInLife}
        durationInFrames={TOTAL}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{ showTimestamps: true }}
      />
      <Composition
        id="DayInLife-NoTimestamps"
        component={DayInLife}
        durationInFrames={TOTAL}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{ showTimestamps: false }}
      />
    </>
  );
};
