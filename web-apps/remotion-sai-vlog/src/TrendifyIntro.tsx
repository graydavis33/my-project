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
const LOGO_TYPE_DUR = 14;

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

const TrendifyLogo: React.FC<{
  accent: string;
  textColor: string;
  startFrame: number;
}> = ({ accent, textColor, startFrame }) => {
  const typed = useSlice("trendify", startFrame, LOGO_TYPE_DUR);
  if (typed.length === 0) return null;

  return (
    <span
      style={{
        position: "relative",
        display: "inline-block",
        fontFamily,
        fontWeight: 600,
        fontSize: TEXT_SIZE,
        lineHeight: 1.1,
        color: textColor,
        letterSpacing: "-0.04em",
        marginLeft: 10,
      }}
    >
      <span
        style={{
          position: "absolute",
          top: -9,
          left: 6,
          width: 16,
          height: 10,
          backgroundColor: accent,
          clipPath: "polygon(0 0, 100% 0, 70% 100%, 0 100%)",
        }}
      />
      {typed}
    </span>
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

  const dayPrefixStart = 6;
  const dayPrefixDur = 6;
  const numberStart = 14;
  const numberDur = 14;
  const buildingStart = 30;
  const buildingDur = 14;
  const logoStart = 46;
  const ageStart = 78;
  const ageDur = 8;
  const locStart = 90;
  const locDur = 12;
  const missionStart = 106;
  const missionDur = 28;

  const dayPrefix = useSlice("Day ", dayPrefixStart, dayPrefixDur);
  const buildingText = useSlice(" of building", buildingStart, buildingDur);
  const age = useSlice("Age: 21", ageStart, ageDur);
  const location = useSlice("Location: NYC", locStart, locDur);
  const mission = useSlice("Mission: build the most creative ad agency", missionStart, missionDur);
  const frame = useCurrentFrame();

  const showCursor = (s: number, d: number) =>
    frame >= s && frame < s + d + 4;

  const lineStyle = {
    fontSize: TEXT_SIZE,
    fontWeight: 600 as const,
    lineHeight: 1.1,
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "#00FF00" }}>
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
          <div style={lineStyle}>
            {dayPrefix}
            <SlotNumber
              from={yesterdayCount}
              to={todayCount}
              startFrame={numberStart}
              durationFrames={numberDur}
              accent={accent}
            />
            {buildingText}
            <TrendifyLogo
              accent={accent}
              textColor={textColor}
              startFrame={logoStart}
            />
            {showCursor(dayPrefixStart, logoStart + LOGO_TYPE_DUR - dayPrefixStart) && (
              <Cursor color={textColor} size={TEXT_SIZE} />
            )}
          </div>

          <div style={lineStyle}>
            {age}
            {showCursor(ageStart, ageDur) && (
              <Cursor color={textColor} size={TEXT_SIZE} />
            )}
          </div>

          <div style={lineStyle}>
            {location}
            {showCursor(locStart, locDur) && (
              <Cursor color={textColor} size={TEXT_SIZE} />
            )}
          </div>

          <div style={lineStyle}>
            {mission}
            {showCursor(missionStart, missionDur) && (
              <Cursor color={textColor} size={TEXT_SIZE} />
            )}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
