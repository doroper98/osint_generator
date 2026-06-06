import React from "react";
import { line as d3Line, area as d3Area, curveMonotoneX } from "d3-shape";

import { Axis } from "../../components/Axis";
import { Callout } from "../../components/Callout";
import { ChartFrame } from "../../components/ChartFrame";
import { ReferenceRegion } from "../../components/ReferenceRegion";
import {
  chart as chartToken,
  fontFamily,
  koreanTextStyle,
  lineHeight,
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
  groupBySeries,
  layoutEndpointLabels,
  unionXs,
  useDrawProgress,
  useSeriesProgress,
} from "../util";

// XYChart — line / area / stacked_area / small_multiples 를 한 컴포넌트로.
//
// 입력 데이터 (legacy 호환):
//   - line / area: Array<{x, y, series?, event?}>
//   - stacked_area: {series: [{name, values: [{x,y}]}]}
//   - small_multiples: {panels: [{label, series: [{x,y}]}]}  ← 일단 single panel 처럼 시리즈 매핑.
//
// 옵션 메타:
//   - referenceRegions: [{startX, endX, label?, intensity?}] (선택)
//   - kicker / subtitle / source: ChartFrame 슬롯.

export type XYChartProps = {
  chartId: string;
  type: "line" | "area" | "stacked_area" | "small_multiples";
  title?: string | null;
  subtitle?: string | null;
  kicker?: string | null;
  source?: string | null;
  unit?: string;
  data: unknown;
  width: number;
  height: number;
  // 선택 — 위기·이벤트 구간 (회색 알파 음영).
  referenceRegions?: Array<{
    startX: string;
    endX: string;
    label?: string | null;
    intensity?: number;
  }>;
};

type Row = { x: string; y: number; series?: string; event?: string };

const normalizeRows = (type: XYChartProps["type"], data: unknown): Row[] => {
  if (type === "stacked_area") {
    const series = (data as { series?: Array<{ name: string; values?: Array<{ x: string; y: number }> }> })?.series ?? [];
    return series.flatMap((s) =>
      (s.values ?? []).map((p) => ({ x: String(p.x), y: p.y, series: s.name })),
    );
  }
  if (type === "small_multiples") {
    const panels = (data as { panels?: Array<{ label: string; series?: Array<{ x: string; y: number }> }> })?.panels ?? [];
    return panels.flatMap((pn) =>
      (pn.series ?? []).map((p) => ({ x: String(p.x), y: p.y, series: pn.label })),
    );
  }
  if (Array.isArray(data)) {
    return (data as Array<Record<string, unknown>>)
      .filter((d) => typeof (d as { y?: unknown }).y === "number")
      .map((d) => ({
        x: String((d as { x: unknown }).x),
        y: (d as { y: number }).y,
        series: (d as { series?: string }).series,
        event: (d as { event?: string }).event,
      }));
  }
  return [];
};

export const XYChart: React.FC<XYChartProps> = ({
  chartId,
  type,
  title,
  subtitle,
  kicker,
  source,
  unit,
  data,
  width,
  height,
  referenceRegions = [],
}) => {
  const rows = normalizeRows(type, data);
  if (rows.length < 2) {
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

  const isArea = type === "area" || type === "stacked_area";

  // 차트 내부 plot 영역.
  const padL = chartToken.padLeft;
  const padR = chartToken.padRight;
  const padT = 16;            // ChartFrame 헤더가 외부에 있으므로 내부 상단 padding 최소화.
  const padB = chartToken.padBottom - 16;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;
  const x0 = padL;
  const x1 = padL + plotW;
  const y0 = padT;
  const y1 = padT + plotH;

  const xs = unionXs(rows);
  const xScale = buildXScale(xs, [x0, x1]);
  const allY = rows.map((r) => r.y);
  const yScale = buildYScale(allY, [y0, y1], { includeZero: isArea, unit });
  const seriesList = groupBySeries(rows);
  const events = rows.filter((r) => r.event);

  const progress = useDrawProgress();

  // 끝점 라벨 충돌 회피.
  const endpointSpots = seriesList
    .filter((s) => s.points.length > 0)
    .map((s, i) => {
      const last = s.points[s.points.length - 1];
      return {
        idealY: yScale.apply(last.y),
        data: { name: s.name, value: last.y, color: seriesColor(i), idx: i },
      };
    });
  const labelGap = size.body * 1.1;
  const labelLayout = layoutEndpointLabels(endpointSpots, y0 + 8, y1 - 8, labelGap);

  // 진입용 wipe clip — x 방향 progress 비율로.
  const clipId = `clip-${chartId}`;

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

        {/* 배경 plate (subtle) */}
        <rect
          x={x0}
          y={y0}
          width={plotW}
          height={plotH}
          fill={surface.cardAlt}
          opacity={0.35}
          rx={8}
        />

        {/* Reference regions (위기 구간 음영) — wipe 와 무관하게 미리 노출. */}
        {referenceRegions.map((r, i) => {
          const xa = xScale.apply(r.startX);
          const xb = xScale.apply(r.endX);
          if (!isFinite(xa) || !isFinite(xb)) return null;
          return (
            <ReferenceRegion
              key={`ref-${i}`}
              x={Math.min(xa, xb)}
              y={y0}
              width={Math.abs(xb - xa)}
              height={plotH}
              label={r.label ?? null}
              intensity={r.intensity ?? 0.10}
            />
          );
        })}

        {/* Grid + axes */}
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

        {/* Series (wipe clipped) */}
        <g clipPath={`url(#${clipId})`}>
          {seriesList.map((s, i) => {
            const col = seriesColor(i);
            const pts = s.points
              .map((p) => [xScale.apply(p.x), yScale.apply(p.y)] as [number, number])
              .filter(([x, y]) => isFinite(x) && isFinite(y));
            if (pts.length < 2) return null;
            const lineGen = d3Line<[number, number]>()
              .x((d) => d[0])
              .y((d) => d[1])
              .curve(curveMonotoneX);
            const linePath = lineGen(pts) ?? "";

            let areaPath = "";
            if (isArea) {
              const baseY = yScale.apply(yScale.min);
              const areaGen = d3Area<[number, number]>()
                .x((d) => d[0])
                .y0(baseY)
                .y1((d) => d[1])
                .curve(curveMonotoneX);
              areaPath = areaGen(pts) ?? "";
            }

            return (
              <g key={`s-${i}`}>
                {isArea && (
                  <path
                    d={areaPath}
                    fill={col}
                    opacity={0.22}
                  />
                )}
                <path
                  d={linePath}
                  fill="none"
                  stroke={col}
                  strokeWidth={stroke.thick}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
              </g>
            );
          })}
        </g>

        {/* 끝점 동그라미 + 직접 라벨 (시리즈명 + 값) — 마지막 30% 진입 후 등장. */}
        {labelLayout.map((spot, k) => {
          const meta = spot.data as { name: string; value: number; color: string; idx: number };
          const lastPoint = seriesList[meta.idx].points[seriesList[meta.idx].points.length - 1];
          const px = xScale.apply(lastPoint.x);
          const py = yScale.apply(lastPoint.y);
          const showLabel = progress > 0.75 ? Math.min(1, (progress - 0.75) / 0.20) : 0;
          if (!isFinite(px) || !isFinite(py)) return null;
          return (
            <g key={`ep-${k}`}>
              {/* 마커 — wipe 끝나기 직전 등장. */}
              <circle
                cx={px}
                cy={py}
                r={6}
                fill={meta.color}
                stroke={surface.page}
                strokeWidth={stroke.base}
                opacity={progress}
              />
              {/* leader line (px,py) → (x1+10, spot.y). */}
              <line
                x1={px + 8}
                y1={py}
                x2={x1 + 14}
                y2={spot.y}
                stroke={meta.color}
                strokeOpacity={0.45 * showLabel}
                strokeWidth={stroke.hairline}
              />
              <foreignObject
                x={x1 + 18}
                y={spot.y - size.body * 0.6}
                width={padR - 22}
                height={size.body * 2.2}
                opacity={showLabel}
              >
                <div
                  style={{
                    fontFamily,
                    color: meta.color,
                    fontSize: size.caption,
                    fontWeight: weight.bold,
                    lineHeight: lineHeight.tight,
                    ...koreanTextStyle,
                  }}
                >
                  <div>{meta.name}</div>
                  <div
                    style={{
                      color: text.primary,
                      fontWeight: weight.extrabold,
                      fontSize: size.body,
                    }}
                  >
                    {fmtValue(meta.value, unit)}
                  </div>
                </div>
              </foreignObject>
            </g>
          );
        })}

        {/* 이벤트 콜아웃 — Subject + Note + Connector. */}
        {events.map((ev, i) => {
          const px = xScale.apply(ev.x);
          const py = yScale.apply(ev.y);
          if (!isFinite(px) || !isFinite(py)) return null;
          // Note 위치: 데이터 포인트 기준 오른쪽 위 / 왼쪽 위 자동.
          const noteOnRight = px < x0 + plotW * 0.7;
          const note = {
            x: noteOnRight ? px + 60 : px - 280,
            y: py - 80,
          };
          return (
            <Callout
              key={`ev-${i}`}
              subject={{ x: px, y: py }}
              note={note}
              title={ev.event ?? ""}
              startFrame={Math.round(0.4 * 30) + i * 6} // 차트 진입 + stagger 6f.
              color={seriesColor(rows.indexOf(ev) % 8)}
              noteWidth={260}
            />
          );
        })}
      </svg>
    </ChartFrame>
  );
};

// ────────────────────────────────────────────────────────────

const fmtValue = (v: number, unit?: string): string => {
  let s: string;
  if (Math.abs(v) >= 10000) s = `${Math.round(v / 1000)}k`;
  else if (Math.abs(v) >= 100 || Number.isInteger(v)) s = String(Math.round(v));
  else s = (Math.round(v * 10) / 10).toString();
  return unit ? `${s} ${unit}` : s;
};

// `useSeriesProgress` 는 stacked_area 의 시리즈별 진입에 쓸 예정(현 PATCH 는 wipe 단일).
// import 미사용 경고 회피.
void useSeriesProgress;
