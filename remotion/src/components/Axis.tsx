import React from "react";

import {
  fontFamily,
  grid as gridToken,
  size,
  stroke,
  text,
  weight,
} from "../design";

// Axis v2 (v0.33.0) — light 톤 + 절제. 그리드 매우 옅게(2% 알파), 축선 옅은 회색.

export type Tick = { pos: number; label: string };

export type AxisProps = {
  orientation: "x" | "y";
  ticks: Tick[];
  axisPos: number;
  domainStart: number;
  domainEnd: number;
  gridLength?: number;
  tickSize?: number;
  showAxisLine?: boolean;
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
                stroke={gridToken.base}
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
              stroke={gridToken.base}
              strokeWidth={stroke.hairline}
            />
          );
        })}

      {showAxisLine && (
        <line
          x1={isX ? domainStart : axisPos}
          y1={isX ? axisPos : domainStart}
          x2={isX ? domainEnd : axisPos}
          y2={isX ? axisPos : domainEnd}
          stroke={gridToken.axis}
          strokeWidth={stroke.thin}
        />
      )}

      {ticks.map((t, i) => {
        if (isX) {
          return (
            <g key={`t-${i}`}>
              <line
                x1={t.pos}
                y1={axisPos}
                x2={t.pos}
                y2={axisPos + tickSize}
                stroke={gridToken.axis}
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
              stroke={gridToken.axis}
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
