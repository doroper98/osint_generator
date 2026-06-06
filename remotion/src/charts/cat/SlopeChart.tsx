import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

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
  stroke as strokeToken,
  surface,
  text,
  weight,
} from "../../design";
import { buildYScale, easeDecelerate, layoutEndpointLabels } from "../util";

export type SlopeChartProps = {
  chartId: string;
  title?: string | null;
  subtitle?: string | null;
  kicker?: string | null;
  source?: string | null;
  unit?: string;
  data: {
    left_label?: string | null;
    right_label?: string | null;
    items?: Array<{ label: string; a: number; b: number }>;
  };
  width: number;
  height: number;
};

export const SlopeChart: React.FC<SlopeChartProps> = ({
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
  const items = data?.items ?? [];
  if (!items.length) {
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
  const padT = 56;       // 좌/우 헤더 공간.
  const padB = chartToken.padBottom - 16;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;
  const y0 = padT;
  const y1 = padT + plotH;
  const xL = padL + 60;
  const xR = width - padR - 60;

  const yScale = buildYScale(
    items.flatMap((d) => [d.a, d.b]),
    [y0, y1],
    { unit },
  );

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stagMs = staggerToken(items.length);

  // Left side & right side label collision avoidance.
  const leftLayout = layoutEndpointLabels(
    items.map((d, i) => ({ idealY: yScale.apply(d.a), data: { i, value: d.a, label: d.label } })),
    y0,
    y1,
    size.caption * 1.2,
  );
  const rightLayout = layoutEndpointLabels(
    items.map((d, i) => ({ idealY: yScale.apply(d.b), data: { i, value: d.b, label: d.label } })),
    y0,
    y1,
    size.caption * 1.2,
  );

  return (
    <ChartFrame kicker={kicker} title={title} subtitle={subtitle} source={source} width={width} height={height}>
      <svg width={width} height={height} style={{ display: "block" }}>
        <rect x={xL - 20} y={y0 - 8} width={xR - xL + 40} height={plotH + 16} fill={surface.cardAlt} opacity={0.3} rx={8} />

        {/* 좌·우 컬럼 헤더 */}
        <text
          x={xL}
          y={y0 - 18}
          fill={text.secondary}
          fontFamily={fontFamily}
          fontSize={size.caption}
          fontWeight={weight.bold}
          letterSpacing={letterSpacing.wider}
          textAnchor="middle"
        >
          {(data?.left_label ?? "").toUpperCase()}
        </text>
        <text
          x={xR}
          y={y0 - 18}
          fill={text.secondary}
          fontFamily={fontFamily}
          fontSize={size.caption}
          fontWeight={weight.bold}
          letterSpacing={letterSpacing.wider}
          textAnchor="middle"
        >
          {(data?.right_label ?? "").toUpperCase()}
        </text>

        {/* 좌·우 세로 가이드 */}
        <line x1={xL} y1={y0} x2={xL} y2={y1} stroke={text.tertiary} strokeOpacity={0.2} />
        <line x1={xR} y1={y0} x2={xR} y2={y1} stroke={text.tertiary} strokeOpacity={0.2} />

        {items.map((d, i) => {
          const startF = Math.round(0.25 * fps) + msToFrames(stagMs * i, fps);
          const endF = startF + msToFrames(duration.long, fps);
          const prog = interpolate(frame, [startF, endF], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: easeDecelerate,
          });
          const yA = yScale.apply(d.a);
          const yB = yScale.apply(d.b);
          const xMid = xL + (xR - xL) * prog;
          const yMid = yA + (yB - yA) * prog;
          const col = seriesColor(i);
          return (
            <g key={`it-${i}`}>
              <line x1={xL} y1={yA} x2={xMid} y2={yMid} stroke={col} strokeWidth={strokeToken.thick} strokeLinecap="round" />
              <circle cx={xL} cy={yA} r={6} fill={col} stroke={surface.page} strokeWidth={strokeToken.base} />
              {prog > 0.97 && (
                <circle cx={xR} cy={yB} r={6} fill={col} stroke={surface.page} strokeWidth={strokeToken.base} />
              )}
            </g>
          );
        })}

        {/* Left labels */}
        {leftLayout.map((spot, k) => {
          const meta = spot.data as { i: number; value: number; label: string };
          const col = seriesColor(meta.i);
          return (
            <g key={`lL-${k}`}>
              <text
                x={xL - 14}
                y={spot.y}
                fill={col}
                fontFamily={fontFamily}
                fontSize={size.caption}
                fontWeight={weight.bold}
                textAnchor="end"
                dominantBaseline="middle"
              >
                {meta.label}
              </text>
              <text
                x={xL + 14}
                y={spot.y}
                fill={text.secondary}
                fontFamily={fontFamily}
                fontSize={size.caption}
                fontWeight={weight.medium}
                textAnchor="start"
                dominantBaseline="middle"
              >
                {fmt(meta.value, unit)}
              </text>
            </g>
          );
        })}

        {/* Right labels */}
        {rightLayout.map((spot, k) => {
          const meta = spot.data as { i: number; value: number; label: string };
          const col = seriesColor(meta.i);
          return (
            <g key={`lR-${k}`}>
              <text
                x={xR + 14}
                y={spot.y}
                fill={col}
                fontFamily={fontFamily}
                fontSize={size.caption}
                fontWeight={weight.bold}
                textAnchor="start"
                dominantBaseline="middle"
              >
                {meta.label}
              </text>
              <text
                x={xR - 14}
                y={spot.y}
                fill={text.secondary}
                fontFamily={fontFamily}
                fontSize={size.caption}
                fontWeight={weight.medium}
                textAnchor="end"
                dominantBaseline="middle"
              >
                {fmt(meta.value, unit)}
              </text>
            </g>
          );
        })}
      </svg>
    </ChartFrame>
  );
};

const fmt = (v: number, unit?: string): string => {
  let s: string;
  if (Math.abs(v) >= 10000) s = `${Math.round(v / 1000)}k`;
  else if (Math.abs(v) >= 100 || Number.isInteger(v)) s = String(Math.round(v));
  else s = (Math.round(v * 10) / 10).toString();
  return unit ? `${s} ${unit}` : s;
};
