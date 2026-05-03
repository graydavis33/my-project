import React from "react";
import {
  AbsoluteFill,
  Video,
  staticFile,
  interpolate,
  useCurrentFrame,
  Easing,
} from "remotion";
import { z } from "zod";
import { loadFont } from "@remotion/google-fonts/Montserrat";

const { fontFamily } = loadFont("normal", { weights: ["600"] });

export const trendifyIntroSchema = z.object({
  startDate: z.string(),
  bgVideoSrc: z.string().optional(),
  accent: z.string(),
  textColor: z.string(),
});

export type TrendifyIntroProps = z.infer<typeof trendifyIntroSchema>;

const TEXT_SIZE = 44;
const ABERRATION_DUR = 18;

const daysSince = (startDate: string): number => {
  const [y, m, d] = startDate.split("-").map(Number);
  const start = Date.UTC(y, m - 1, d);
  const now = new Date();
  const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.floor((today - start) / 86_400_000) + 1;
};

const useSlice = (text: string, startFrame: number, durationFrames: number) => {
  const frame = useCurrentFrame();
  const t = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  return text.slice(0, Math.floor(t * text.length));
};

const Cursor: React.FC<{ color: string; size: number }> = ({ color, size }) => {
  const frame = useCurrentFrame();
  const on = Math.floor(frame / 8) % 2 === 0;
  return (
    <span
      style={{
        display: "inline-block",
        width: size * 0.06,
        height: size * 0.9,
        backgroundColor: color,
        marginLeft: size * 0.04,
        verticalAlign: "text-bottom",
        opacity: on ? 1 : 0,
      }}
    />
  );
};

const TrendifyLogo: React.FC<{ accent: string; textColor: string }> = ({
  accent,
  textColor,
}) => {
  const frame = useCurrentFrame();
  const offset = interpolate(frame, [0, ABERRATION_DUR], [18, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        position: "relative",
        fontFamily,
        fontWeight: 600,
        fontSize: 110,
        lineHeight: 1,
        color: textColor,
        letterSpacing: "-0.04em",
        filter: `drop-shadow(${offset}px 0 0 rgba(255,0,80,0.85)) drop-shadow(${-offset}px 0 0 rgba(0,200,255,0.85))`,
      }}
    >
      <span
        style={{
          position: "absolute",
          top: -22,
          left: 14,
          width: 38,
          height: 24,
          backgroundColor: accent,
          clipPath: "polygon(0 0, 100% 0, 70% 100%, 0 100%)",
        }}
      />
      trendify
    </div>
  );
};

const SlotNumber: React.FC<{
  from: number;
  to: number;
  startFrame: number;
  durationFrames: number;
  accent: string;
}> = ({ from, to, startFrame, durationFrames, accent }) => {
  const frame = useCurrentFrame();
  if (frame < startFrame) return null;
  const t = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );
  const settled = t >= 1;
  const value = settled
    ? to
    : Math.floor(from + (to - from + 1) * t * 0.999);
  return <span style={{ color: accent }}>{value}</span>;
};

export const TrendifyIntro: React.FC<TrendifyIntroProps> = ({
  startDate,
  bgVideoSrc,
  accent,
  textColor,
}) => {
  const todayCount = daysSince(startDate);
  const yesterdayCount = todayCount - 1;

  const dayLabelStart = 14;
  const dayLabelDur = 8;
  const numberStart = 22;
  const numberDur = 12;
  const missionStart = 38;
  const missionDur = 20;
  const locationStart = 60;
  const locationDur = 12;
  const ageStart = 74;
  const ageDur = 10;

  const dayLabel = useSlice("day ", dayLabelStart, dayLabelDur);
  const mission = useSlice("Mission: most creative ad agency", missionStart, missionDur);
  const location = useSlice("Location: nyc", locationStart, locationDur);
  const age = useSlice("Age: 21", ageStart, ageDur);
  const frame = useCurrentFrame();

  const showCursor = (s: number, d: number) =>
    frame >= s && frame < s + d + 4;

  const lineStyle = {
    fontSize: TEXT_SIZE,
    fontWeight: 600 as const,
    lineHeight: 1.1,
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {bgVideoSrc && <Video src={staticFile(bgVideoSrc)} muted />}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            left: 60,
            bottom: 60,
            display: "flex",
            flexDirection: "column",
            gap: 18,
            fontFamily,
            color: textColor,
          }}
        >
          <TrendifyLogo accent={accent} textColor={textColor} />

          <div style={lineStyle}>
            {dayLabel}
            <SlotNumber
              from={yesterdayCount}
              to={todayCount}
              startFrame={numberStart}
              durationFrames={numberDur}
              accent={accent}
            />
            {showCursor(dayLabelStart, dayLabelDur + numberDur) &&
              frame < numberStart + numberDur && (
                <Cursor color={textColor} size={TEXT_SIZE} />
              )}
          </div>

          <div style={lineStyle}>
            {mission}
            {showCursor(missionStart, missionDur) && (
              <Cursor color={textColor} size={TEXT_SIZE} />
            )}
          </div>

          <div style={lineStyle}>
            {location}
            {showCursor(locationStart, locationDur) && (
              <Cursor color={textColor} size={TEXT_SIZE} />
            )}
          </div>

          <div style={lineStyle}>
            {age}
            {showCursor(ageStart, ageDur) && (
              <Cursor color={textColor} size={TEXT_SIZE} />
            )}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
