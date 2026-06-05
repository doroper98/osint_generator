import React from "react";
import { line as d3Line, curveMonotoneX } from "d3-shape";

import { Axis } from "../../components/Axis";
import { ChartFrame } from "../../components/ChartFrame";
import {
  chart as chartToken,
  fontFamily,
  koreanTextStyle,
  letterSpacing,
  seriesColor,
  size,
  stroke,
  surface,
  text,
  weight,
} from "../../design";
import {
  buildXScale,
  buildYScale,
  unionXs,
  useDrawProgress,
} from "../util";

export type DualLineSide = {
  label?: string | null;
  unit?: string | null;
  series?: Array<{ x: string; y: number }>;
};

export type DualLineChartProps = {
  chartId: string;
  title?: string | null;
  subtitle?: string | null;
  kicker?: string | null;
  source?: string | null;
  data: { left?: DualLineSide; right?: DualLineSide };
  width: number;
  height: number;
};

export const DualLineChart: React.FC<DualLineChartProps> = ({
  chartId,
  title,
  subtitle,
  kicker,
  source,
  data,
  width,
  height,
}) => {
  const left = data?.left;
  const right = data?.right;
  const leftPts = left?.series ?? [];
  const rightPts = right?.series ?? [];

  if (leftPts.length < 2 && rightPts.length < 2) {
    return (
      <ChartFrame
        kicker={kicker}
        title={title}
        subtitle={subtitle}
        source={source}
        width={width}
        height={height}
      >
        <div
          style={{
            width,
            height,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: text.tertiary,
            fontFamily,
            fontSize: size.body,
            ...koreanTextStyle,
          }}
        >
          데이터 부족
        </div>
      </ChartFrame>
    );
  }

  const padL = chartToken.padLeft;
  const padR = chartToken.padRight;
  const padT = 16;
  const padB = chartToken.padBottom - 16;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;
  const x0 = padL;
  const x1 = padL + plotW;
  const y0 = padT;
  const y1 = padT + plotH;

  const xs = unionXs([...leftPts, ...rightPts]);
  const xScale = buildXScale(xs, [x0, x1]);
  const yL = buildYScale(leftPts.map((p) => p.y), [y0, y1], {
    unit: left?.unit ?? undefined,
  });
  const yR = buildYScale(rightPts.map((p) => p.y), [y0, y1], {
    unit: right?.unit ?? undefined,
  });

  const progress = useDrawProgress();
  const clipId = `clip-${chartId}`;

  const colL = seriesColor(0);
  const colR = seriesColor(1);

  const lineGen = d3Line<[number, number]>()
    .x((d) => d[0])
    .y((d) => d[1])
    .curve(curveMonotoneX);

  const pathLeft = lineGen(
    leftPts.map((p) => [xScale.apply(p.x), yL.apply(p.y)] as [number, number]),
  ) ?? "";
  const pathRight = lineGen(
    rightPts.map((p) => [xScale.apply(p.x), yR.apply(p.y)] as [number, number]),
  ) ?? "";

  return (
    <ChartFrame
      kicker={kicker}
      title={title}
      subtitle={subtitle}
      source={source}
      width={width}
      height={height}
    >
      <svg width={width} height={height} style={{ display: "block" }}>
        <defs>
          <clipPath id={clipId}>
            <rect
              x={x0}
              y={y0 - 10}
              width={Math.max(0, plotW * progress)}
              height={plotH + 20}
            />
          </clipPath>
        </defs>

        <rect
          x={x0}
          y={y0}
          width={plotW}
          height={plotH}
          fill={surface.s1}
          opacity={0.35}
          rx={8}
        />

        {/* 왼쪽 y 축 — grid 있음 */}
        <Axis
          orientation="y"
          ticks={yL.ticks}
          axisPos={x0}
          domainStart={y0}
          domainEnd={y1}
          gridLength={plotW}
          showAxisLine={false}
        />

        {/* 오른쪽 y 축 — grid 없음, 색 colR 로 표기 */}
        <g>
          {yR.ticks.map((t, i) => (
            <text
              key={`yr-${i}`}
              x={x1 + 12}
              y={t.pos}
              fill={colR}
              fontFamily={fontFamily}
              fontSize={size.caption}
              fontWeight={weight.medium}
              textAnchor="start"
              dominantBaseline="middle"
            >
              {t.label}
            </text>
          ))}
        </g>

        {/* x 축 */}
        <Axis
          orientation="x"
          ticks={xScale.ticks}
          axisPos={y1}
          domainStart={x0}
          domainEnd={x1}
        />

        {/* 축 라벨 (왼쪽/오른쪽 시리즈명) */}
        <text
          x={x0}
          y={y0 - 6}
          fill={colL}
          fontFamily={fontFamily}
          fontSize={size.caption}
          fontWeight={weight.bold}
          letterSpacing={letterSpacing.wider}
          textAnchor="start"
        >
          {(left?.label ?? "").toUpperCase()}
          {left?.unit ? ` (${left.unit})` : ""}
        </text>
        <text
          x={x1}
          y={y0 - 6}
          fill={colR}
          fontFamily={fontFamily}
          fontSize={size.caption}
          fontWeight={weight.bold}
          letterSpacing={letterSpacing.wider}
          textAnchor="end"
        >
          {(right?.label ?? "").toUpperCase()}
          {right?.unit ? ` (${right.unit})` : ""}
        </text>

        {/* 시리즈 (wipe clipped) */}
        <g clipPath={`url(#${clipId})`}>
          {pathLeft && (
            <path
              d={pathLeft}
              fill="none"
              stroke={colL}
              strokeWidth={stroke.thick}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}
          {pathRight && (
            <path
              d={pathRight}
              fill="none"
              stroke={colR}
              strokeWidth={stroke.thick}
              strokeLinejoin="round"
              strokeLinecap="round"
              strokeDasharray="8 7"
            />
          )}
        </g>

        {/* 끝점 마커 */}
        {leftPts.length > 0 &&
          (() => {
            const last = leftPts[leftPts.length - 1];
            return (
              <circle
                cx={xScale.apply(last.x)}
                cy={yL.apply(last.y)}
                r={6}
                fill={colL}
                stroke={surface.base}
                strokeWidth={stroke.base}
                opacity={progress}
              />
            );
          })()}
        {rightPts.length > 0 &&
          (() => {
            const last = rightPts[rightPts.length - 1];
            return (
              <circle
                cx={xScale.apply(last.x)}
                cy={yR.apply(last.y)}
                r={6}
                fill={colR}
                stroke={surface.base}
                strokeWidth={stroke.base}
                opacity={progress}
              />
            );
          })()}
      </svg>
    </ChartFrame>
  );
};
