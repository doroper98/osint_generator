import React from "react";
import {
  fontFamily,
  line as lineToken,
  size,
  stroke,
  text,
  weight,
} from "../design";

// Axis — SVG group. x 또는 y 축 + tick + grid + 라벨.
// d3-axis 같은 헤비 의존 안 쓰고 직접 그린다 — Remotion 의 결정론적 렌더에 더 맞다.
// 호출자가 scale (d3-scale 또는 자체) 의 tick 위치를 미리 계산해 ticks 배열로 전달.

export type Tick = { pos: number; label: string };

export type AxisProps = {
  orientation: "x" | "y";
  ticks: Tick[];
  // 축 자체의 시작/끝 위치 (px) — orientation 에 따른 직교 축 좌표.
  // x 축: y0 (기저선 y), x 축 시작/끝 = ticks 의 도메인.
  // y 축: x0 (기저선 x), 길이 = ticks 의 도메인.
  axisPos: number;          // 직교 위치 (x축이면 y, y축이면 x).
  domainStart: number;      // tick.pos 와 같은 좌표축의 시작.
  domainEnd: number;        // 끝.
  // grid 길이 (orientation 의 직교 방향). 0 이면 grid 안 그림.
  gridLength?: number;
  tickSize?: number;        // tick 표시선 길이.
  showAxisLine?: boolean;   // 기저선 표시 여부.
  // 라벨 오프셋 (px). x: 라벨이 축 아래로, y: 축 왼쪽으로.
  labelOffset?: number;
};

export const Axis: React.FC<AxisProps> = ({
  orientation,
  ticks,
  axisPos,
  domainStart,
  domainEnd,
  gridLength = 0,
  tickSize = 6,
  showAxisLine = true,
  labelOffset = 12,
}) => {
  const isX = orientation === "x";

  return (
    <g>
      {/* Grid */}
      {gridLength > 0 &&
        ticks.map((t, i) => {
          if (isX) {
            return (
              <line
                key={`g-${i}`}
                x1={t.pos}
                y1={axisPos}
                x2={t.pos}
                y2={axisPos - gridLength}
                stroke={lineToken.grid}
                strokeWidth={stroke.hairline}
              />
            );
          }
          return (
            <line
              key={`g-${i}`}
              x1={axisPos}
              y1={t.pos}
              x2={axisPos + gridLength}
              y2={t.pos}
              stroke={lineToken.grid}
              strokeWidth={stroke.hairline}
            />
          );
        })}

      {/* Axis line */}
      {showAxisLine && (
        <line
          x1={isX ? domainStart : axisPos}
          y1={isX ? axisPos : domainStart}
          x2={isX ? domainEnd : axisPos}
          y2={isX ? axisPos : domainEnd}
          stroke={lineToken.axis}
          strokeWidth={stroke.thin}
        />
      )}

      {/* Ticks + labels */}
      {ticks.map((t, i) => {
        if (isX) {
          return (
            <g key={`t-${i}`}>
              <line
                x1={t.pos}
                y1={axisPos}
                x2={t.pos}
                y2={axisPos + tickSize}
                stroke={lineToken.axis}
                strokeWidth={stroke.hairline}
              />
              <text
                x={t.pos}
                y={axisPos + tickSize + labelOffset}
                fill={text.secondary}
                fontFamily={fontFamily}
                fontSize={size.caption}
                fontWeight={weight.medium}
                textAnchor="middle"
                dominantBaseline="hanging"
              >
                {t.label}
              </text>
            </g>
          );
        }
        return (
          <g key={`t-${i}`}>
            <line
              x1={axisPos}
              y1={t.pos}
              x2={axisPos - tickSize}
              y2={t.pos}
              stroke={lineToken.axis}
              strokeWidth={stroke.hairline}
            />
            <text
              x={axisPos - tickSize - labelOffset}
              y={t.pos}
              fill={text.secondary}
              fontFamily={fontFamily}
              fontSize={size.caption}
              fontWeight={weight.medium}
              textAnchor="end"
              dominantBaseline="middle"
            >
              {t.label}
            </text>
          </g>
        );
      })}
    </g>
  );
};
