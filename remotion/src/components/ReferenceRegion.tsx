import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

import {
  duration,
  fontFamily,
  koreanTextStyle,
  msToFrames,
  size,
  text,
  weight,
} from "../design";

// ReferenceRegion v2 (v0.33.0) — light 톤. 회색 fill + 라벨, glow 없음.

export type ReferenceRegionProps = {
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string | null;
  labelPlacement?: "top" | "inside" | "bottom";
  intensity?: number;
  color?: string;
  startFrame?: number;
};

export const ReferenceRegion: React.FC<ReferenceRegionProps> = ({
  x,
  y,
  width,
  height,
  label,
  labelPlacement = "top",
  intensity = 0.08,
  color = "#1a1a1a",
  startFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const f = Math.max(0, frame - startFrame);
  const fadeIn = msToFrames(duration.medium, fps);

  const opacity = interpolate(f, [0, fadeIn], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const labelX = x + width / 2;
  let labelY = y - 12;
  let dominantBaseline: "auto" | "middle" | "hanging" = "auto";
  if (labelPlacement === "inside") {
    labelY = y + height / 2;
    dominantBaseline = "middle";
  } else if (labelPlacement === "bottom") {
    labelY = y + height + 12;
    dominantBaseline = "hanging";
  }

  return (
    <g opacity={opacity}>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={color}
        opacity={intensity}
      />
      <line
        x1={x}
        y1={y}
        x2={x}
        y2={y + height}
        stroke={color}
        strokeOpacity={0.18}
        strokeDasharray="4 4"
      />
      <line
        x1={x + width}
        y1={y}
        x2={x + width}
        y2={y + height}
        stroke={color}
        strokeOpacity={0.18}
        strokeDasharray="4 4"
      />
      {label ? (
        <text
          x={labelX}
          y={labelY}
          fill={text.secondary}
          fontFamily={fontFamily}
          fontSize={size.caption}
          fontWeight={weight.semibold}
          textAnchor="middle"
          dominantBaseline={dominantBaseline}
          style={koreanTextStyle as React.CSSProperties}
        >
          {label}
        </text>
      ) : null}
    </g>
  );
};
