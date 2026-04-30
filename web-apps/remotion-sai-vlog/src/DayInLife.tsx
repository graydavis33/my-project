import React from "react";
import { AbsoluteFill, Series, Video, staticFile } from "remotion";
import { CLIPS } from "./clips";

const TimestampOverlay: React.FC<{ label: string }> = ({ label }) => (
  <AbsoluteFill
    style={{
      alignItems: "center",
      justifyContent: "center",
      pointerEvents: "none",
    }}
  >
    <div
      style={{
        fontFamily: '"Arial Black", Arial, Helvetica, sans-serif',
        fontWeight: 900,
        fontSize: 95,
        color: "#F28129",
        textShadow: "4px 4px 0 rgba(0,0,0,0.45)",
        letterSpacing: "-0.01em",
      }}
    >
      {label}
    </div>
  </AbsoluteFill>
);

export const DayInLife: React.FC<{ showTimestamps?: boolean }> = ({
  showTimestamps = true,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Series>
        {CLIPS.map((c, i) => (
          <Series.Sequence key={i} durationInFrames={c.durationInFrames}>
            <AbsoluteFill>
              <Video src={staticFile(c.src)} muted />
              {showTimestamps && <TimestampOverlay label={c.label} />}
            </AbsoluteFill>
          </Series.Sequence>
        ))}
      </Series>
    </AbsoluteFill>
  );
};
