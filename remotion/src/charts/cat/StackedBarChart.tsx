import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { scaleBand } from "d3-scale";

import { Axis } from "../../components/Axis";
import { ChartFrame } from "../../components/ChartFrame";
import {
  chart as chartToken,
  duration,
  fontFamily,
  koreanTextStyle,
  letterSpacing,
  msToFrames,
  seriesColor,
  size,
  stagger as staggerToken,
  surface,
  text,
  weight,
} from "../../design";
import { buildYScale, easeDecelerate } from "../util";

export type StackedBarChartProps = {
  chartId: string;
  title?: string | null;
  subtitle?: string | null;
  kicker?: string | null;
  source?: string | null;
  unit?: string;
  data: {
    categories?: string[];
    series?: Array<{ name: string; values?: number[] }>;
  };
  width: number;
  height: number;
};

export const StackedBarChart: React.FC<StackedBarChartProps> = ({
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
  const cats = data?.categories ?? [];
  const series = data?.series ?? [];

  if (!cats.length || !series.length) {
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

  const totals = cats.map((_, ci) => series.reduce((s, se) => s + (se.values?.[ci] ?? 0), 0));
  const yScale = buildYScale(totals, [y0, y1], { includeZero: true, unit });
  const bandScale = scaleBand<string>().domain(cats).range([x0, x1]).padding(0.34);

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stagMs = staggerToken(cats.length);

  const xTicks = cats.map((c) => ({
    pos: (bandScale(c) ?? 0) + bandScale.bandwidth() / 2,
    label: c,
  }));

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
        <rect
          x={x0}
          y={y0}
          width={plotW}
          height={plotH}
          fill={surface.s1}
          opacity={0.35}
          rx={8}
        />

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
          ticks={xTicks}
          axisPos={y1}
          domainStart={x0}
          domainEnd={x1}
          tickSize={4}
        />

        {cats.map((c, ci) => {
          const cx = (bandScale(c) ?? 0) + bandScale.bandwidth() / 2;
          const bw = bandScale.bandwidth();
          const startF = Math.round(0.25 * fps) + msToFrames(stagMs * ci, fps);
          let acc = 0;
          return (
            <g key={`c-${ci}`}>
              {series.map((se, si) => {
                const v = se.values?.[ci] ?? 0;
                const segStart = acc;
                const segEnd = acc + v;
                acc = segEnd;
                const yTopFull = yScale.apply(segEnd);
                const yBotFull = yScale.apply(segStart);
                const fullH = Math.max(0, yBotFull - yTopFull);
                // 시리즈 별 stagger (카테고리 stagger + 시리즈 stagger).
                const sStartF = startF + msToFrames(60 * si, fps);
                const sEndF = sStartF + msToFrames(duration.long, fps);
                const prog = interpolate(frame, [sStartF, sEndF], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: easeDecelerate,
                });
                const drawH = fullH * prog;
                return (
                  <rect
                    key={`s-${si}`}
                    x={cx - bw * 0.36}
                    y={yBotFull - drawH}
                    width={bw * 0.72}
                    height={drawH}
                    fill={seriesColor(si)}
                    rx={si === series.length - 1 ? 4 : 0}
                  />
                );
              })}
            </g>
          );
        })}

        {/* 시리즈 범례 (우상단) */}
        <g>
          {series.map((se, si) => (
            <g key={`leg-${si}`} transform={`translate(${x1 - 200}, ${y0 + si * 26})`}>
              <rect width={14} height={14} y={1} fill={seriesColor(si)} rx={2} />
              <text
                x={22}
                y={12}
                fill={text.secondary}
                fontFamily={fontFamily}
                fontSize={size.caption}
                fontWeight={weight.semibold}
                letterSpacing={letterSpacing.normal}
                dominantBaseline="middle"
              >
                {se.name}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </ChartFrame>
  );
};
