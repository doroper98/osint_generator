import React from "react";
import { line as d3Line, area as d3Area, curveMonotoneX } from "d3-shape";

import { Axis } from "../../components/Axis";
import { ChartFrame } from "../../components/ChartFrame";
import { ReferenceRegion } from "../../components/ReferenceRegion";
import {
  accent,
  chart as chartToken,
  fontFamily,
  koreanTextStyle,
  seriesColor,
  size,
  stroke,
  surface,
  text,
  weight,
} from "../../design";
import { buildXScale, buildYScale, useDrawProgress } from "../util";

export type ForecastPoint = { x: string; y: number };
export type ForecastBand = { x: string; low: number; mid: number; high: number };

export type ForecastChartProps = {
  chartId: string;
  title?: string | null;
  subtitle?: string | null;
  kicker?: string | null;
  source?: string | null;
  unit?: string;
  data: {
    actual?: ForecastPoint[];
    forecast?: ForecastBand[];
  };
  width: number;
  height: number;
};

export const ForecastChart: React.FC<ForecastChartProps> = ({
  chartId,
  title,
  subtitle,
  kicker,
  source,
  unit,
  data,
  width,
  height,
}) => {
  const actual = data?.actual ?? [];
  const fc = data?.forecast ?? [];

  if (!actual.length && !fc.length) {
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

  const xs: string[] = [];
  const seen = new Set<string>();
  for (const p of actual) {
    if (!seen.has(p.x)) {
      xs.push(p.x);
      seen.add(p.x);
    }
  }
  for (const p of fc) {
    if (!seen.has(p.x)) {
      xs.push(p.x);
      seen.add(p.x);
    }
  }
  const xScale = buildXScale(xs, [x0, x1]);
  const allY = [
    ...actual.map((p) => p.y),
    ...fc.flatMap((p) => [p.low, p.mid, p.high]),
  ];
  const yScale = buildYScale(allY, [y0, y1], { unit });

  const progress = useDrawProgress();
  const clipId = `clip-${chartId}`;

  const colActual = seriesColor(0);
  const colFc = accent.quote;

  const lineGen = d3Line<[number, number]>()
    .x((d) => d[0])
    .y((d) => d[1])
    .curve(curveMonotoneX);

  const actualPts = actual.map((p) => [xScale.apply(p.x), yScale.apply(p.y)] as [number, number]);
  const midPts = fc.map((p) => [xScale.apply(p.x), yScale.apply(p.mid)] as [number, number]);
  const pathActual = lineGen(actualPts) ?? "";
  const pathMid = lineGen(midPts) ?? "";

  // Band area (high → low).
  const areaGen = d3Area<ForecastBand>()
    .x((p) => xScale.apply(p.x))
    .y0((p) => yScale.apply(p.low))
    .y1((p) => yScale.apply(p.high))
    .curve(curveMonotoneX);
  const bandPath = fc.length ? areaGen(fc) ?? "" : "";

  // Forecast 구간 = ReferenceRegion 으로 (전망 영역 시각 분리).
  const fcStart = fc.length ? xScale.apply(fc[0].x) : null;
  const fcEnd = fc.length ? xScale.apply(fc[fc.length - 1].x) : null;

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

        {/* Forecast region 음영 */}
        {fcStart !== null && fcEnd !== null && (
          <ReferenceRegion
            x={Math.min(fcStart, fcEnd)}
            y={y0}
            width={Math.abs(fcEnd - fcStart)}
            height={plotH}
            label="전망 구간"
            intensity={0.08}
            color={colFc}
            labelPlacement="top"
          />
        )}

        <Axis
          orientation="y"
          ticks={yScale.ticks}
          axisPos={x0}
          domainStart={y0}
          domainEnd={y1}
          gridLength={plotW}
          showAxisLine={false}
        />
        <Axis
          orientation="x"
          ticks={xScale.ticks}
          axisPos={y1}
          domainStart={x0}
          domainEnd={x1}
        />

        <g clipPath={`url(#${clipId})`}>
          {/* Band */}
          {bandPath && <path d={bandPath} fill={colFc} opacity={0.18} />}
          {/* Actual */}
          {pathActual && (
            <path
              d={pathActual}
              fill="none"
              stroke={colActual}
              strokeWidth={stroke.thick}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}
          {/* Forecast mid (dashed) */}
          {pathMid && (
            <path
              d={pathMid}
              fill="none"
              stroke={colFc}
              strokeWidth={stroke.base}
              strokeLinejoin="round"
              strokeLinecap="round"
              strokeDasharray="10 8"
            />
          )}
        </g>

        {/* 끝점 라벨: 실측 마지막, 전망 마지막 */}
        {actual.length > 0 &&
          (() => {
            const last = actual[actual.length - 1];
            const px = xScale.apply(last.x);
            const py = yScale.apply(last.y);
            return (
              <g opacity={progress}>
                <circle cx={px} cy={py} r={6} fill={colActual} stroke={surface.base} strokeWidth={stroke.base} />
                <text
                  x={px - 10}
                  y={py - 14}
                  fill={colActual}
                  fontFamily={fontFamily}
                  fontSize={size.caption}
                  fontWeight={weight.bold}
                  textAnchor="end"
                >
                  실측
                </text>
              </g>
            );
          })()}
        {fc.length > 0 &&
          (() => {
            const last = fc[fc.length - 1];
            const px = xScale.apply(last.x);
            const py = yScale.apply(last.mid);
            return (
              <g opacity={progress > 0.6 ? Math.min(1, (progress - 0.6) / 0.3) : 0}>
                <circle cx={px} cy={py} r={6} fill={colFc} stroke={surface.base} strokeWidth={stroke.base} />
                <text
                  x={px + 10}
                  y={py - 14}
                  fill={colFc}
                  fontFamily={fontFamily}
                  fontSize={size.caption}
                  fontWeight={weight.bold}
                  textAnchor="start"
                >
                  전망
                </text>
              </g>
            );
          })()}
      </svg>
    </ChartFrame>
  );
};
