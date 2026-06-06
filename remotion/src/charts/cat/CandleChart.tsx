import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { scaleBand } from "d3-scale";

import { Axis } from "../../components/Axis";
import { ChartFrame } from "../../components/ChartFrame";
import {
  label,
  chart as chartToken,
  duration,
  fontFamily,
  koreanTextStyle,
  msToFrames,
  size,
  stagger as staggerToken,
  stroke as strokeToken,
  surface,
  text,
} from "../../design";
import { buildYScale, easeDecelerate } from "../util";

export type CandlePoint = { x: string; open: number; close: number; high: number; low: number };

export type CandleChartProps = {
  chartId: string;
  title?: string | null;
  subtitle?: string | null;
  kicker?: string | null;
  source?: string | null;
  unit?: string;
  data: CandlePoint[];
  width: number;
  height: number;
};

export const CandleChart: React.FC<CandleChartProps> = ({
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
  const rows = data ?? [];
  if (!rows.length) {
    return (
      <ChartFrame kicker={kicker} title={title} subtitle={subtitle} source={source} width={width} height={height}>
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

  const xs = rows.map((r) => String(r.x));
  const bandScale = scaleBand<string>().domain(xs).range([x0, x1]).padding(0.3);

  const yScale = buildYScale(
    rows.flatMap((r) => [r.low, r.high]),
    [y0, y1],
    { unit },
  );

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stagMs = staggerToken(rows.length, 40, 400);

  // x tick — 라벨 너무 많으면 첫·중간·마지막 + 4 분포.
  const tickCount = Math.min(6, rows.length);
  const xTicks = xs
    .filter((_, i) => {
      if (rows.length <= tickCount) return true;
      return i % Math.max(1, Math.floor(rows.length / tickCount)) === 0 || i === rows.length - 1;
    })
    .map((lab) => ({
      pos: (bandScale(lab) ?? 0) + bandScale.bandwidth() / 2,
      label: lab,
    }));

  return (
    <ChartFrame kicker={kicker} title={title} subtitle={subtitle} source={source} width={width} height={height}>
      <svg width={width} height={height} style={{ display: "block" }}>
        <rect x={x0} y={y0} width={plotW} height={plotH} fill={surface.cardAlt} opacity={0.35} rx={8} />

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

        {rows.map((r, i) => {
          const startF = Math.round(0.25 * fps) + msToFrames(stagMs * i, fps);
          const endF = startF + msToFrames(duration.short, fps);
          const prog = interpolate(frame, [startF, endF], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: easeDecelerate,
          });
          const cx = (bandScale(String(r.x)) ?? 0) + bandScale.bandwidth() / 2;
          const bw = bandScale.bandwidth();
          const up = r.close >= r.open;
          const col = up ? label.verified : label.unverified;
          const yHi = yScale.apply(r.high);
          const yLo = yScale.apply(r.low);
          const yO = yScale.apply(r.open);
          const yC = yScale.apply(r.close);
          const top = Math.min(yO, yC);
          const h = Math.max(2, Math.abs(yO - yC));

          return (
            <g key={`c-${i}`} opacity={prog}>
              <line x1={cx} y1={yHi} x2={cx} y2={yLo} stroke={col} strokeWidth={strokeToken.thin} />
              <rect
                x={cx - bw * 0.32}
                y={top}
                width={bw * 0.64}
                height={h * prog}
                fill={col}
                rx={2}
              />
            </g>
          );
        })}
      </svg>
    </ChartFrame>
  );
};
