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
  seriesColor,
  size,
  stagger as staggerToken,
  stroke as strokeToken,
  surface,
  text,
  weight,
} from "../../design";
import { buildYScale, easeDecelerate } from "../util";

// Waterfall — 누적 증감을 시각화. 각 막대 사이에 connector 선(이전 막대 끝 → 다음 막대 시작).
// type: "pos" / "neg" / "total".

export type WaterfallProps = {
  chartId: string;
  title?: string | null;
  subtitle?: string | null;
  kicker?: string | null;
  source?: string | null;
  unit?: string;
  data: Array<{ label: string; value: number; type?: "pos" | "neg" | "total" }>;
  width: number;
  height: number;
};

export const Waterfall: React.FC<WaterfallProps> = ({
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

  // 누적 계산.
  let run = 0;
  const bars = rows.map((d) => {
    if (d.type === "total") {
      run = d.value;
      return { lo: Math.min(0, d.value), hi: Math.max(0, d.value), type: "total" as const, label: d.label, val: d.value, prev: run };
    }
    const lo = run;
    const hi = run + d.value;
    const result = { lo: Math.min(lo, hi), hi: Math.max(lo, hi), type: (d.type ?? (d.value >= 0 ? "pos" : "neg")) as "pos" | "neg", label: d.label, val: d.value, prev: run };
    run = hi;
    return result;
  });

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

  const labels = bars.map((b) => b.label);
  const bandScale = scaleBand<string>().domain(labels).range([x0, x1]).padding(0.32);

  const yScale = buildYScale(
    bars.flatMap((b) => [b.lo, b.hi]),
    [y0, y1],
    { includeZero: true, unit },
  );

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stagMs = staggerToken(bars.length);

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

        {bars.map((b, i) => {
          const cx = (bandScale(b.label) ?? 0) + bandScale.bandwidth() / 2;
          const bw = bandScale.bandwidth();
          const startF = Math.round(0.25 * fps) + msToFrames(stagMs * i, fps);
          const endF = startF + msToFrames(duration.long, fps);
          const prog = interpolate(frame, [startF, endF], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: easeDecelerate,
          });

          const yTop = yScale.apply(b.hi);
          const yBot = yScale.apply(b.lo);
          const totalH = yBot - yTop;
          const drawH = totalH * prog;
          // grow 방향: pos 면 아래에서 위로(yBot → yTop), neg 면 위에서 아래로.
          const yRect = b.val >= 0 || b.type === "total" ? yBot - drawH : yTop;
          const col =
            b.type === "total"
              ? seriesColor(0)
              : b.type === "pos"
                ? label.verified
                : label.unverified;

          return (
            <g key={`b-${i}`}>
              {/* Connector — 이전 막대 끝 (i>0) 에서 본 막대 시작 ymax/ymin 까지 점선. */}
              {i > 0 && b.type !== "total" && prog > 0.05 && (
                <line
                  x1={(bandScale(bars[i - 1].label) ?? 0) + bw * 0.86}
                  y1={yScale.apply(bars[i - 1].type === "total" ? bars[i - 1].val : bars[i - 1].hi)}
                  x2={cx - bw * 0.46}
                  y2={yScale.apply(b.val >= 0 ? b.lo : b.hi)}
                  stroke={text.tertiary}
                  strokeWidth={strokeToken.thin}
                  strokeDasharray="4 4"
                  opacity={0.6}
                />
              )}
              <rect
                x={cx - bw * 0.36}
                y={yRect}
                width={bw * 0.72}
                height={Math.max(2, drawH)}
                rx={5}
                fill={col}
              />
              {/* 값 라벨 */}
              <text
                x={cx}
                y={(b.val >= 0 || b.type === "total" ? yTop : yBot + size.caption + 4) - (b.val >= 0 || b.type === "total" ? 8 : 0)}
                fill={text.primary}
                fontFamily={fontFamily}
                fontSize={size.caption}
                fontWeight={weight.bold}
                textAnchor="middle"
                opacity={prog}
              >
                {b.type === "total"
                  ? fmtVal(b.val, unit)
                  : `${b.val > 0 ? "+" : ""}${fmtVal(b.val, unit)}`}
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
