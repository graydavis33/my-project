import React from "react";
import { Composition } from "remotion";
import { DayInLife, dayInLifeSchema, DayInLifeProps } from "./DayInLife";
import { CLIPS, FPS, WIDTH, HEIGHT } from "./clips";

const computeDuration = ({ props }: { props: DayInLifeProps }) => {
  const total = props.clips.reduce((sum, c) => sum + c.durationInFrames, 0);
  return { durationInFrames: Math.max(1, total) };
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DayInLife"
        component={DayInLife}
        schema={dayInLifeSchema}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        durationInFrames={1}
        calculateMetadata={computeDuration}
        defaultProps={{
          showTimestamps: true,
          timestampColor: "#F28129",
          fontSize: 95,
          clips: CLIPS,
        }}
      />
      <Composition
        id="DayInLife-NoTimestamps"
        component={DayInLife}
        schema={dayInLifeSchema}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        durationInFrames={1}
        calculateMetadata={computeDuration}
        defaultProps={{
          showTimestamps: false,
          timestampColor: "#F28129",
          fontSize: 95,
          clips: CLIPS,
        }}
      />
    </>
  );
};
