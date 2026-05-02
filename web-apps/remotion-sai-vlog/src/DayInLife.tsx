import React from "react";
import { AbsoluteFill, Series, Video, staticFile } from "remotion";
import { z } from "zod";

export const clipSchema = z.object({
  src: z.string(),
  durationInFrames: z.number().int().positive(),
  label: z.string(),
  source: z.string().optional(),
});

export const dayInLifeSchema = z.object({
  showTimestamps: z.boolean(),
  timestampColor: z.string(),
  fontSize: z.number().int().positive(),
  clips: z.array(clipSchema),
});

export type DayInLifeProps = z.infer<typeof dayInLifeSchema>;

const TimestampOverlay: React.FC<{ label: string; color: string; fontSize: number }> = ({
  label,
  color,
  fontSize,
}) => (
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
        fontSize,
        color,
        textShadow: "4px 4px 0 rgba(0,0,0,0.45)",
        letterSpacing: "-0.01em",
      }}
    >
      {label}
    </div>
  </AbsoluteFill>
);

export const DayInLife: React.FC<DayInLifeProps> = ({
  showTimestamps,
  timestampColor,
  fontSize,
  clips,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Series>
        {clips.map((c, i) => (
          <Series.Sequence key={i} durationInFrames={c.durationInFrames}>
            <AbsoluteFill>
              <Video src={staticFile(c.src)} muted />
              {showTimestamps && (
                <TimestampOverlay
                  label={c.label}
                  color={timestampColor}
                  fontSize={fontSize}
                />
              )}
            </AbsoluteFill>
          </Series.Sequence>
        ))}
      </Series>
    </AbsoluteFill>
  );
};
