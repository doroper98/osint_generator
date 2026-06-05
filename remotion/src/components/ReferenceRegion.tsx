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

// ReferenceRegion — 차트 위에 회색 알파 영역 + 라벨로 위기/구간/이벤트를 표시.
// 가로 영역 (시계열 차트의 위기 구간 등) 디폴트, 세로 영역도 지원.
//
// SVG group. 호출자가 차트 좌표계 안에 위치시킨다.

export type ReferenceRegionProps = {
  // 영역 좌상단 + 크기.
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string | null;
  // 라벨 위치 (영역 위 / 안 / 아래).
  labelPlacement?: "top" | "inside" | "bottom";
  // 알파 강도 (0–1).
  intensity?: number;
  // 컬러 (디폴트 텍스트 보조 컬러의 알파).
  color?: string;
  // 진입 시작 프레임.
  startFrame?: number;
};

export const ReferenceRegion: React.FC<ReferenceRegionProps> = ({
  x,
  y,
  width,
  height,
  label,
  labelPlacement = "top",
  intensity = 0.10,
  color = "#f5f7fa",
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

  // 라벨 위치 계산.
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
      {/* 영역 fill */}
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={color}
        opacity={intensity}
      />
      {/* 좌우 경계선 (얇게) */}
      <line
        x1={x}
        y1={y}
        x2={x}
        y2={y + height}
        stroke={color}
        strokeOpacity={0.25}
        strokeDasharray="4 4"
      />
      <line
        x1={x + width}
        y1={y}
        x2={x + width}
        y2={y + height}
        stroke={color}
        strokeOpacity={0.25}
        strokeDasharray="4 4"
      />
      {/* 라벨 */}
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
