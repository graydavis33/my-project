import React from "react";
import { AbsoluteFill } from "remotion";
import { z } from "zod";
import { TrendifyIntro, trendifyIntroSchema } from "./TrendifyIntro";

export const igReelPreviewSchema = trendifyIntroSchema;
export type IGReelPreviewProps = z.infer<typeof igReelPreviewSchema>;

const SAFE_TOP = 220;
const SAFE_BOTTOM = 500;
const SAFE_RIGHT = 200;

const GradientBar: React.FC<{
  position: "top" | "bottom";
  height: number;
}> = ({ position, height }) => {
  const dir = position === "top" ? "to bottom" : "to top";
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        [position]: 0,
        height,
        background: `linear-gradient(${dir}, rgba(0,0,0,0.55), rgba(0,0,0,0))`,
      }}
    />
  );
};

const ActionButton: React.FC<{ label: string; bottom: number }> = ({ label, bottom }) => (
  <div
    style={{
      position: "absolute",
      right: 36,
      bottom,
      width: 88,
      height: 88,
      borderRadius: 44,
      background: "rgba(255,255,255,0.18)",
      border: "2px solid rgba(255,255,255,0.7)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "white",
      fontSize: 16,
      fontFamily: "sans-serif",
      fontWeight: 600,
    }}
  >
    {label}
  </div>
);

const IGOverlay: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <GradientBar position="top" height={260} />
    <GradientBar position="bottom" height={520} />

    <div
      style={{
        position: "absolute",
        top: 70,
        left: 0,
        right: 0,
        textAlign: "center",
        color: "white",
        fontFamily: "sans-serif",
        fontWeight: 700,
        fontSize: 32,
        letterSpacing: "0.1em",
      }}
    >
      Reels
    </div>

    <ActionButton label="like" bottom={1100} />
    <ActionButton label="cmt" bottom={990} />
    <ActionButton label="send" bottom={880} />
    <ActionButton label="save" bottom={770} />
    <ActionButton label="more" bottom={660} />

    <div
      style={{
        position: "absolute",
        left: 36,
        bottom: 280,
        color: "white",
        fontFamily: "sans-serif",
        fontWeight: 700,
        fontSize: 30,
        textShadow: "0 2px 6px rgba(0,0,0,0.6)",
      }}
    >
      @sai_karra
    </div>
    <div
      style={{
        position: "absolute",
        left: 36,
        right: 200,
        bottom: 200,
        color: "white",
        fontFamily: "sans-serif",
        fontSize: 26,
        opacity: 0.9,
        textShadow: "0 2px 6px rgba(0,0,0,0.6)",
      }}
    >
      Sample caption text would sit here…
    </div>
    <div
      style={{
        position: "absolute",
        left: 36,
        bottom: 80,
        color: "white",
        fontFamily: "sans-serif",
        fontSize: 22,
        opacity: 0.85,
        textShadow: "0 2px 6px rgba(0,0,0,0.6)",
      }}
    >
      ♪ Original audio · @sai_karra
    </div>

    <div
      style={{
        position: "absolute",
        top: SAFE_TOP,
        bottom: SAFE_BOTTOM,
        left: 0,
        right: SAFE_RIGHT,
        border: "4px dashed rgba(0,255,180,0.95)",
        boxSizing: "border-box",
      }}
    />
    <div
      style={{
        position: "absolute",
        top: SAFE_TOP - 50,
        left: 20,
        color: "rgba(0,255,180,0.95)",
        fontFamily: "sans-serif",
        fontWeight: 700,
        fontSize: 22,
        letterSpacing: "0.05em",
      }}
    >
      SAFE ZONE
    </div>
  </AbsoluteFill>
);

export const IGReelPreview: React.FC<IGReelPreviewProps> = (props) => (
  <AbsoluteFill>
    <TrendifyIntro {...props} />
    <IGOverlay />
  </AbsoluteFill>
);
