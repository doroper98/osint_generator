import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

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
  stroke as strokeToken,
  surface,
  text,
  weight,
} from "../../design";
import { buildYScale, easeDecelerate, layoutEndpointLabels } from "../util";

// PointChart — scatter / bubble.
//
// 입력: Array<{x: number, y: number, size?: number, label?: string}>
// bubble: size 가 면적에 비례하도록 반지름 = sqrt(size / smax) * maxR.
// 진입: 점 stagger pop-in. 라벨 충돌 회피로 라벨이 겹치지 않게 배치.

export type PointChartProps = {
  chartId: string;
  bubble?: boolean;
  title?: string | null;
  subtitle?: string | null;
  kicker?: string | null;
  source?: string | null;
  xLabel?: string | null;
  yLabel?: string | null;
  unit?: string;
  data: Array<{ x: number; y: number; size?: number; label?: string }>;
  width: number;
  height: number;
};

export const PointChart: React.FC<PointChartProps> = ({
  chartId,
  bubble,
  title,
  subtitle,
  kicker,
  source,
  xLabel,
  yLabel,
  unit,
  data,
  width,
  height,
}) => {
  const rows = (data ?? []).filter((d) => typeof d.x === "number" && typeof d.y === "number");
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

  const maxR = bubble ? 50 : 9;
  const padL = chartToken.padLeft;
  const padR = chartToken.padRight;
  const padT = 16 + maxR;
  const padB = chartToken.padBottom - 16 + maxR;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;
  const x0 = padL;
  const x1 = padL + plotW;
  const y0 = padT;
  const y1 = padT + plotH;

  const xScale = buildYScale(rows.map((r) => r.x), [x1, x0]);
  // x 는 horizontal 이라 buildYScale 의 range 를 뒤집어 사용 (apply 가 [hi → lo] 매핑이므로 [x1, x0] 으로 호출).
  const yScale = buildYScale(rows.map((r) => r.y), [y0, y1], { unit });

  const X = (v: number) => xScale.apply(v);
  const Y = (v: number) => yScale.apply(v);

  const sMax = Math.max(...rows.map((r) => r.size ?? 1));
  const radius = (v: number): number => {
    if (!bubble) return maxR;
    const ratio = Math.sqrt((v ?? 1) / sMax);
    return Math.max(8, maxR * ratio);
  };

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stagMs = staggerToken(rows.length, 60, 400);

  // 라벨 충돌 회피 — 모든 점이 라벨을 가질 때 가장자리 외곽에 라벨 배치.
  const labelSpots = rows
    .map((r, i) => ({ i, idealY: Y(r.y), data: r }))
    .filter((s) => s.data.label);
  const layout = layoutEndpointLabels(
    labelSpots.map((s) => ({ idealY: s.idealY, data: s })),
    y0,
    y1,
    size.body * 1.05,
  );

  // x tick 위치는 xScale.ticks 의 pos 가 [x1→x0] 방향이므로 그대로 사용.
  const xTicks = xScale.ticks.map((t) => ({ pos: t.pos, label: t.label }));

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
        <rect x={x0} y={y0 - maxR} width={plotW} height={plotH + 2 * maxR} fill={surface.cardAlt} opacity={0.35} rx={8} />

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
        />

        {/* 축 라벨 */}
        {yLabel && (
          <text
            x={x0 - 60}
            y={y0 + plotH / 2}
            fill={text.secondary}
            fontFamily={fontFamily}
            fontSize={size.caption}
            fontWeight={weight.semibold}
            textAnchor="middle"
            transform={`rotate(-90, ${x0 - 60}, ${y0 + plotH / 2})`}
          >
            {yLabel}
          </text>
        )}
        {xLabel && (
          <text
            x={x0 + plotW / 2}
            y={y1 + 56}
            fill={text.secondary}
            fontFamily={fontFamily}
            fontSize={size.caption}
            fontWeight={weight.semibold}
            textAnchor="middle"
          >
            {xLabel}
          </text>
        )}

        {/* Points */}
        {rows.map((r, i) => {
          const startF = Math.round(0.25 * fps) + msToFrames(stagMs * i, fps);
          const endF = startF + msToFrames(duration.medium, fps);
          const prog = interpolate(frame, [startF, endF], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: easeDecelerate,
          });
          const r0 = radius(r.size ?? 1);
          const cx = X(r.x);
          const cy = Y(r.y);
          const col = seriesColor(i);
          return (
            <g key={`p-${i}`}>
              <circle cx={cx} cy={cy} r={r0 * prog} fill={col} opacity={0.62} stroke={col} strokeWidth={strokeToken.thin} />
            </g>
          );
        })}

        {/* 라벨 (충돌 회피 + leader line) */}
        {layout.map((spot, k) => {
          const meta = (spot.data as { i: number; data: { x: number; y: number; size?: number; label?: string } }).data;
          const idx = (spot.data as { i: number }).i;
          const startF = Math.round(0.25 * fps) + msToFrames(stagMs * idx, fps) + msToFrames(duration.medium, fps);
          const endF = startF + msToFrames(duration.short, fps);
          const opacity = interpolate(frame, [startF, endF], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const cx = X(meta.x);
          const cy = Y(meta.y);
          const onRight = cx < x0 + plotW * 0.6;
          const labX = onRight ? cx + radius(meta.size ?? 1) + 10 : cx - radius(meta.size ?? 1) - 10;
          return (
            <g key={`lab-${k}`} opacity={opacity}>
              <line
                x1={cx + (onRight ? radius(meta.size ?? 1) : -radius(meta.size ?? 1))}
                y1={cy}
                x2={labX}
                y2={spot.y}
                stroke={text.tertiary}
                strokeOpacity={0.4}
                strokeWidth={strokeToken.hairline}
              />
              <text
                x={labX + (onRight ? 4 : -4)}
                y={spot.y}
                fill={text.primary}
                fontFamily={fontFamily}
                fontSize={size.caption}
                fontWeight={weight.semibold}
                textAnchor={onRight ? "start" : "end"}
                dominantBaseline="middle"
              >
                {meta.label}
              </text>
            </g>
          );
        })}
      </svg>
    </ChartFrame>
  );
};
