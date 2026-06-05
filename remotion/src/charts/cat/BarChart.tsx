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
  msToFrames,
  seriesColor,
  size,
  stagger as staggerToken,
  stroke,
  surface,
  text,
  weight,
} from "../../design";
import { buildYScale, easeDecelerate } from "../util";

// BarChart — bar / lollipop / range_bar (mode 분기).
//
// 입력:
//   - bar / lollipop: Array<{label, value}>
//   - range:          Array<{label, low, high}>
//
// 진입: 카테고리 순 stagger + 막대 grow(아래→위, 음수면 위→아래).
// 끝에 값 라벨 (Material decelerate 끝나면 페이드).

export type BarChartProps = {
  chartId: string;
  mode: "bar" | "lollipop" | "range";
  title?: string | null;
  subtitle?: string | null;
  kicker?: string | null;
  source?: string | null;
  unit?: string;
  data: unknown;
  width: number;
  height: number;
};

export const BarChart: React.FC<BarChartProps> = ({
  chartId,
  mode,
  title,
  subtitle,
  kicker,
  source,
  unit,
  data,
  width,
  height,
}) => {
  const rows = Array.isArray(data)
    ? (data as Array<Record<string, unknown>>).filter((d) => typeof d.label === "string")
    : [];
  if (!rows.length) {
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
  const padR = chartToken.padRight - 40;
  const padT = 16;
  const padB = chartToken.padBottom - 16;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;
  const x0 = padL;
  const x1 = padL + plotW;
  const y0 = padT;
  const y1 = padT + plotH;

  const labels = rows.map((d) => String(d.label));
  const bandScale = scaleBand<string>().domain(labels).range([x0, x1]).padding(0.34);

  const allVals =
    mode === "range"
      ? rows.flatMap((d) => [Number(d.low), Number(d.high)])
      : rows.map((d) => Number(d.value));
  const yScale = buildYScale(allVals, [y0, y1], {
    includeZero: mode !== "range",
    unit,
  });

  const baseY = yScale.apply(Math.max(yScale.min, 0));

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const delaySec = 0.25;
  const stagMs = staggerToken(rows.length);
  const growMs = duration.long;

  // 카테고리 X tick — 라벨 자체.
  const xTicks = labels.map((lab) => ({
    pos: (bandScale(lab) ?? 0) + bandScale.bandwidth() / 2,
    label: lab,
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

        {rows.map((d, i) => {
          const cx = (bandScale(labels[i]) ?? 0) + bandScale.bandwidth() / 2;
          const bw = bandScale.bandwidth();
          const startF = Math.round(delaySec * fps) + msToFrames(stagMs * i, fps);
          const endF = startF + msToFrames(growMs, fps);
          const prog = interpolate(frame, [startF, endF], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: easeDecelerate,
          });
          const labelOpacity = interpolate(frame, [endF - msToFrames(150, fps), endF + msToFrames(100, fps)], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          if (mode === "range") {
            const yH = yScale.apply(Number(d.high));
            const yL = yScale.apply(Number(d.low));
            const top = Math.min(yH, yL);
            const totalH = Math.abs(yL - yH);
            const drawH = totalH * prog;
            const yBar = top + (totalH - drawH) / 2; // 중앙에서 양쪽으로 확장.
            const col = seriesColor(0);
            return (
              <g key={`b-${i}`}>
                <rect
                  x={cx - bw * 0.36}
                  y={yBar}
                  width={bw * 0.72}
                  height={drawH}
                  rx={6}
                  fill={col}
                />
                {/* 양 끝 값 라벨 */}
                <text
                  x={cx}
                  y={yH - 8}
                  fill={text.primary}
                  fontFamily={fontFamily}
                  fontSize={size.caption}
                  fontWeight={weight.bold}
                  textAnchor="middle"
                  opacity={labelOpacity}
                >
                  {fmtVal(Number(d.high), unit)}
                </text>
                <text
                  x={cx}
                  y={yL + size.caption + 4}
                  fill={text.secondary}
                  fontFamily={fontFamily}
                  fontSize={size.caption}
                  fontWeight={weight.medium}
                  textAnchor="middle"
                  opacity={labelOpacity}
                >
                  {fmtVal(Number(d.low), unit)}
                </text>
              </g>
            );
          }

          if (mode === "lollipop") {
            const y = yScale.apply(Number(d.value));
            const drawY = baseY + (y - baseY) * prog;
            const col = seriesColor(i);
            return (
              <g key={`b-${i}`}>
                <line
                  x1={cx}
                  y1={baseY}
                  x2={cx}
                  y2={drawY}
                  stroke={col}
                  strokeWidth={stroke.thick}
                />
                <circle
                  cx={cx}
                  cy={drawY}
                  r={9 * Math.min(1, prog * 1.4)}
                  fill={col}
                  stroke={surface.base}
                  strokeWidth={stroke.base}
                />
                <text
                  x={cx}
                  y={drawY - 16}
                  fill={text.primary}
                  fontFamily={fontFamily}
                  fontSize={size.caption}
                  fontWeight={weight.bold}
                  textAnchor="middle"
                  opacity={labelOpacity}
                >
                  {fmtVal(Number(d.value), unit)}
                </text>
              </g>
            );
          }

          // mode === "bar"
          const y = yScale.apply(Number(d.value));
          const drawH = Math.abs(baseY - y) * prog;
          const yTop = y < baseY ? baseY - drawH : baseY;
          const col = Number(d.value) >= 0 ? seriesColor(0) : seriesColor(5); // 음수는 다크오렌지.
          return (
            <g key={`b-${i}`}>
              <rect
                x={cx - bw * 0.36}
                y={yTop}
                width={bw * 0.72}
                height={drawH}
                rx={6}
                fill={col}
              />
              <text
                x={cx}
                y={y < baseY ? yTop - 8 : yTop + drawH + size.caption + 2}
                fill={text.primary}
                fontFamily={fontFamily}
                fontSize={size.caption}
                fontWeight={weight.bold}
                textAnchor="middle"
                opacity={labelOpacity}
              >
                {fmtVal(Number(d.value), unit)}
              </text>
            </g>
          );
        })}
      </svg>
    </ChartFrame>
  );
};

const fmtVal = (v: number, unit?: string): string => {
  let s: string;
  if (Math.abs(v) >= 10000) s = `${Math.round(v / 1000)}k`;
  else if (Math.abs(v) >= 100 || Number.isInteger(v)) s = String(Math.round(v));
  else s = (Math.round(v * 10) / 10).toString();
  return unit ? `${s} ${unit}` : s;
};
