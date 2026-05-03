import React from "react";
import {
  AbsoluteFill,
  Video,
  staticFile,
  interpolate,
  useCurrentFrame,
  random,
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
  const glitchEnd = 14;
  const inGlitch = frame < glitchEnd;
  const flicker = inGlitch
    ? random(`flick-${Math.floor(frame / 2)}`) > 0.4
      ? 1
      : 0.15
    : 1;
  const jitterX = inGlitch ? (random(`jx-${frame}`) - 0.5) * 14 : 0;
  const jitterY = inGlitch ? (random(`jy-${frame}`) - 0.5) * 6 : 0;
  const splitX = inGlitch ? (random(`sx-${frame}`) - 0.5) * 10 : 0;
  const settle = interpolate(frame, [glitchEnd, glitchEnd + 6], [flicker, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
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
        opacity: inGlitch ? flicker : settle,
        transform: `translate(${jitterX}px, ${jitterY}px)`,
        letterSpacing: "-0.04em",
        textShadow: inGlitch
          ? `${splitX}px 0 0 ${accent}, ${-splitX}px 0 0 rgba(0,200,255,0.6)`
          : "none",
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

  const dayLabelStart = 12;
  const dayLabelDur = 8;
  const numberStart = 20;
  const numberDur = 14;
  const missionStart = 38;
  const missionDur = 24;
  const statsStart = 64;
  const statsDur = 18;

  const dayLabel = useSlice("DAY ", dayLabelStart, dayLabelDur);
  const mission = useSlice("the most creative ad agency", missionStart, missionDur);
  const stats = useSlice("21  ·  NYC", statsStart, statsDur);
  const frame = useCurrentFrame();

  const showCursor = (s: number, d: number) =>
    frame >= s && frame < s + d + 4;

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
            gap: 22,
            fontFamily,
            color: textColor,
          }}
        >
          <TrendifyLogo accent={accent} textColor={textColor} />

          <div
            style={{
              fontSize: 96,
              fontWeight: 600,
              lineHeight: 1,
              letterSpacing: "-0.02em",
            }}
          >
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
                <Cursor color={textColor} size={96} />
              )}
          </div>

          <div style={{ fontSize: 44, fontWeight: 600, lineHeight: 1.1 }}>
            {mission}
            {showCursor(missionStart, missionDur) && (
              <Cursor color={textColor} size={44} />
            )}
          </div>

          <div
            style={{
              fontSize: 36,
              fontWeight: 600,
              lineHeight: 1.1,
              opacity: 0.85,
            }}
          >
            {stats}
            {showCursor(statsStart, statsDur) && (
              <Cursor color={textColor} size={36} />
            )}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
