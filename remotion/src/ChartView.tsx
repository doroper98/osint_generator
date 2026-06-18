import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

import { BarChart as BarChartV2 } from "./charts/cat/BarChart";
import { CandleChart as CandleChartV2 } from "./charts/cat/CandleChart";
import { PointChart as PointChartV2 } from "./charts/cat/PointChart";
import { SlopeChart as SlopeChartV2 } from "./charts/cat/SlopeChart";
import { StackedBarChart as StackedBarChartV2 } from "./charts/cat/StackedBarChart";
import { Waterfall as WaterfallV2 } from "./charts/cat/Waterfall";
import { DualLineChart } from "./charts/xy/DualLineChart";
import { ForecastChart as ForecastChartV2 } from "./charts/xy/ForecastChart";
import { XYChart } from "./charts/xy/XYChart";

// render_props.json 의 chartData 와 동일 구조 (orchestrator/render_io.py:RenderChart).
export type ChartData = {
  chartId: string;
  type: string;
  title?: string;
  data: any;
  unit?: string;
};

// ── 공용 토큰/헬퍼 ────────────────────────────────────────────────
const ACCENT = "#e0a458";
const GRID = "#2c3647";
const TXT = "#aeb6c2";
const FG = "#f5f7fa";
const PALETTE = ["#5bc0de", "#e0a458", "#6bbf6b", "#cf6f6f", "#9b8bd6", "#d6c45b", "#5fa8d3", "#c98a6a"];
const POS = "#6bbf6b";
const NEG = "#cf6f6f";
const FONT = { fontFamily: "sans-serif" } as const;

function fmtNum(v: number): string {
  if (!isFinite(v)) return "";
  if (Math.abs(v) >= 1000) return Math.round(v).toLocaleString("en-US");
  if (Number.isInteger(v)) return String(v);
  return Math.round(v * 10) / 10 + "";
}

// 라벨이 SVG 경계서 잘리지 않게 anchor + clamp (다듬기).
function edgeAnchor(x: number, width: number, pad = 8): "start" | "middle" | "end" {
  if (x < width * 0.12) return "start";
  if (x > width * 0.88) return "end";
  return "middle";
}
function clampX(x: number, width: number, pad = 10): number {
  return Math.max(pad, Math.min(width - pad, x));
}

function useDraw(startF = 8, durSec = 1.6): number {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return interpolate(frame, [startF, startF + fps * durSec], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
}

const Halo: React.FC<any> = (p) => (
  <text {...p} stroke="#0b0f16" strokeWidth={5} paintOrder="stroke" style={FONT} />
);

type Box = { width: number; height: number };
const PAD = { l: 84, r: 56, t: 30, b: 56 };

function yGrid(min: number, max: number, Y: (v: number) => number, x0: number, x1: number, unit?: string) {
  const vals = [max, (max + min) / 2, min];
  return vals.map((v, k) => {
    const yy = Y(v);
    return (
      <g key={`g${k}`}>
        <line x1={x0} y1={yy} x2={x1} y2={yy} stroke={GRID} strokeWidth={1} />
        <text x={x0 - 12} y={yy + 7} fontSize={22} fill={TXT} textAnchor="end" style={FONT}>
          {fmtNum(v)}{unit ? ` ${unit}` : ""}
        </text>
      </g>
    );
  });
}

// NOTE: XY family (v0.31.0) + Bar/Point/Waterfall/Slope/Candle family (v0.32.0) 는
// charts/{xy,cat}/ 로 이관됨. 본 파일의 legacy 는 Phase 3 의 Donut/Gantt/Heatmap/Network/
// Sankey 만 임시 유지(Phase 3 에서 d3-force/d3-sankey/world-atlas 로 정통 재구현).

// ── donut ─────────────────────────────────────────────────────────
const Donut: React.FC<{ data: any } & Box> = ({ data, width, height }) => {
  const prog = useDraw(8, 1.0);
  const rows: any[] = Array.isArray(data) ? data.filter((d) => (d.value ?? 0) > 0) : [];
  if (!rows.length) return null;
  const total = rows.reduce((s, d) => s + d.value, 0);
  const cx = width / 2, cy = height / 2 + 6, R = Math.min(width, height) * 0.34, r = R * 0.58;
  let a0 = -Math.PI / 2;
  const arc = (s: number, e: number) => {
    const p = (ang: number, rad: number) => [cx + rad * Math.cos(ang), cy + rad * Math.sin(ang)];
    const large = e - s > Math.PI ? 1 : 0;
    const [x1, y1] = p(s, R), [x2, y2] = p(e, R), [x3, y3] = p(e, r), [x4, y4] = p(s, r);
    return `M${x1},${y1} A${R},${R} 0 ${large} 1 ${x2},${y2} L${x3},${y3} A${r},${r} 0 ${large} 0 ${x4},${y4} Z`;
  };
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {rows.map((d, i) => {
        const frac = d.value / total, a1 = a0 + frac * 2 * Math.PI * prog;
        const seg = arc(a0, a1); const mid = (a0 + a1) / 2; a0 += frac * 2 * Math.PI;
        const lx = cx + (R + 28) * Math.cos(mid), ly = cy + (R + 28) * Math.sin(mid);
        return (
          <g key={i}>
            <path d={seg} fill={PALETTE[i % PALETTE.length]} />
            <text x={clampX(lx, width)} y={ly} fontSize={20} fill={FG} textAnchor={edgeAnchor(lx, width)} style={FONT}>{d.label} {Math.round(frac * 100)}%</text>
          </g>
        );
      })}
    </svg>
  );
};

// ── gantt ─────────────────────────────────────────────────────────
const Gantt: React.FC<{ data: any } & Box> = ({ data, width, height }) => {
  const prog = useDraw(8, 1.2);
  const rows: any[] = Array.isArray(data) ? data : [];
  if (!rows.length) return null;
  const t = (s: string) => new Date(s).getTime();
  const starts = rows.map((d) => t(d.start)), ends = rows.map((d) => t(d.end));
  const tmin = Math.min(...starts), tmax = Math.max(...ends);
  const X = (v: number) => PAD.l + ((v - tmin) / (tmax - tmin || 1)) * (width - PAD.l - PAD.r);
  const n = rows.length, rh = (height - PAD.t - PAD.b) / n;
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {rows.map((d, i) => {
        const y = PAD.t + rh * i + rh * 0.18, h = rh * 0.5;
        const x0 = X(t(d.start)), x1 = X(t(d.end));
        const col = PALETTE[i % PALETTE.length];
        return (
          <g key={i} opacity={i / n <= prog + 0.05 ? 1 : 0}>
            <rect x={x0} y={y} width={Math.max(4, (x1 - x0))} height={h} rx={6} fill={col} opacity={0.85} />
            <text x={clampX(x0, width)} y={y - 6} fontSize={19} fill={FG} textAnchor={edgeAnchor(x0, width)} style={FONT}>{d.label}</text>
            {d.note && <text x={clampX(x0, width)} y={y + h + 20} fontSize={16} fill={TXT} textAnchor={edgeAnchor(x0, width)} style={FONT}>{d.note}</text>}
          </g>
        );
      })}
    </svg>
  );
};

// ── heatmap ───────────────────────────────────────────────────────
const Heatmap: React.FC<{ data: any } & Box> = ({ data, width, height }) => {
  const prog = useDraw(8, 0.9);
  const rows: any[] = Array.isArray(data) ? data : [];
  if (!rows.length) return null;
  const xsv = Array.from(new Set(rows.map((d) => String(d.x))));
  const ysv = Array.from(new Set(rows.map((d) => String(d.y))));
  const vmax = Math.max(...rows.map((d) => d.value)), vmin = Math.min(...rows.map((d) => d.value));
  const cw = (width - PAD.l - PAD.r) / xsv.length, ch = (height - PAD.t - PAD.b) / ysv.length;
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {rows.map((d, i) => {
        const xi = xsv.indexOf(String(d.x)), yi = ysv.indexOf(String(d.y));
        const t = (d.value - vmin) / (vmax - vmin || 1);
        return <rect key={i} x={PAD.l + xi * cw + 2} y={PAD.t + yi * ch + 2} width={cw - 4} height={ch - 4} rx={4}
          fill={ACCENT} opacity={(0.15 + 0.8 * t) * prog} />;
      })}
      {ysv.map((yv, i) => <text key={`y${i}`} x={PAD.l - 10} y={PAD.t + ch * (i + 0.6)} fontSize={18} fill={TXT} textAnchor="end" style={FONT}>{yv}</text>)}
      {xsv.map((xv, i) => <text key={`x${i}`} x={PAD.l + cw * (i + 0.5)} y={height - 18} fontSize={18} fill={TXT} textAnchor="middle" style={FONT}>{xv}</text>)}
    </svg>
  );
};

// ── network (원형 배치) ───────────────────────────────────────────
const Network: React.FC<{ data: any } & Box> = ({ data, width, height }) => {
  const prog = useDraw(8, 1.2);
  const nodes: any[] = data?.nodes ?? [];
  const links: any[] = data?.links ?? [];
  if (!nodes.length) return null;
  const cx = width / 2, cy = height / 2 + 4, R = Math.min(width, height) * 0.36;
  const pos: Record<string, [number, number]> = {};
  nodes.forEach((nd, i) => {
    const a = -Math.PI / 2 + (i / nodes.length) * 2 * Math.PI;
    pos[nd.id] = [cx + R * Math.cos(a), cy + R * Math.sin(a)];
  });
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {links.map((lk, i) => {
        const a = pos[lk.source], b = pos[lk.target];
        if (!a || !b) return null;
        const mx = (a[0] + b[0]) / 2 + (b[1] - a[1]) * 0.12, my = (a[1] + b[1]) / 2 - (b[0] - a[0]) * 0.12;
        return (
          <g key={i} opacity={prog}>
            <path d={`M${a[0]},${a[1]} Q${mx},${my} ${b[0]},${b[1]}`} fill="none" stroke={GRID} strokeWidth={2.5} />
            {lk.type && <text x={mx} y={my} fontSize={15} fill={TXT} textAnchor="middle" style={FONT}>{lk.type}</text>}
          </g>
        );
      })}
      {nodes.map((nd, i) => {
        const [x, y] = pos[nd.id]; const col = PALETTE[i % PALETTE.length];
        return (
          <g key={i} opacity={prog}>
            <circle cx={x} cy={y} r={16} fill={col} stroke="#0e1116" strokeWidth={2} />
            <Halo x={clampX(x, width)} y={y - 24} fontSize={19} fontWeight={700} fill={FG} textAnchor={edgeAnchor(x, width)}>{nd.label}</Halo>
          </g>
        );
      })}
    </svg>
  );
};

// ── sankey (간이 2~3열 흐름) ──────────────────────────────────────
const Sankey: React.FC<{ data: any } & Box> = ({ data, width, height }) => {
  const prog = useDraw();
  const nodes: any[] = data?.nodes ?? [];
  const links: any[] = data?.links ?? [];
  if (!nodes.length) return null;
  // 노드를 들어오는 링크 유무로 좌/우 2열 간이 배치.
  const targets = new Set(links.map((l) => l.target));
  const left = nodes.filter((n) => !targets.has(n.id));
  const right = nodes.filter((n) => targets.has(n.id));
  const colX = (arr: any[], side: 0 | 1) => (side === 0 ? PAD.l + 40 : width - PAD.r - 40);
  const place = (arr: any[], side: 0 | 1) => { const m: Record<string, [number, number]> = {}; arr.forEach((n, i) => { m[n.id] = [colX(arr, side), PAD.t + (height - PAD.t - PAD.b) * ((i + 0.5) / arr.length)]; }); return m; };
  const pos = { ...place(left, 0), ...place(right, 1) };
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {links.map((lk, i) => {
        const a = pos[lk.source], b = pos[lk.target]; if (!a || !b) return null;
        const w = Math.max(3, Math.min(28, (lk.value ?? 1)));
        return <path key={i} d={`M${a[0]},${a[1]} C${(a[0] + b[0]) / 2},${a[1]} ${(a[0] + b[0]) / 2},${b[1]} ${b[0]},${b[1]}`}
          fill="none" stroke={ACCENT} strokeWidth={w} opacity={0.4 * prog} />;
      })}
      {nodes.map((nd, i) => { const p = pos[nd.id]; if (!p) return null; const r = right.includes(nd); return (
        <g key={i} opacity={prog}><rect x={p[0] - 8} y={p[1] - 22} width={16} height={44} fill={PALETTE[i % PALETTE.length]} />
          <text x={p[0] + (r ? 14 : -14)} y={p[1] + 5} fontSize={18} fill={FG} textAnchor={r ? "start" : "end"} style={FONT}>{nd.label}</text></g>); })}
    </svg>
  );
};

// ── 디스패치 ──────────────────────────────────────────────────────
// v0.31.0 부터 XY family (line/area/stacked_area/small_multiples/dual_line/forecast) 는
// charts/xy/ 의 정통 재구현 컴포넌트로 라우팅. 나머지는 본 파일의 legacy 렌더러 (Phase 2+ 에서 교체).
export const ChartView: React.FC<{ chart: ChartData; width: number; height: number }> = ({ chart, width, height }) => {
  const t = chart.type, d = chart.data, u = chart.unit, box = { width, height };
  switch (t) {
    case "line":
    case "area":
    case "stacked_area":
    case "small_multiples":
      return (
        <XYChart
          chartId={chart.chartId}
          type={t as "line" | "area" | "stacked_area" | "small_multiples"}
          title={null}
          unit={u}
          data={d}
          width={width}
          height={height}
        />
      );
    case "dual_line":
      return <DualLineChart chartId={chart.chartId} title={null} data={d} width={width} height={height} />;
    case "forecast":
      return (
        <ForecastChartV2
          chartId={chart.chartId}
          title={null}
          unit={u}
          data={d}
          width={width}
          height={height}
        />
      );
    case "bar":
      return <BarChartV2 chartId={chart.chartId} mode="bar" title={null} unit={u} data={d} width={width} height={height} />;
    case "lollipop":
      return <BarChartV2 chartId={chart.chartId} mode="lollipop" title={null} unit={u} data={d} width={width} height={height} />;
    case "range_bar":
      return <BarChartV2 chartId={chart.chartId} mode="range" title={null} unit={u} data={d} width={width} height={height} />;
    case "stacked":
    case "stacked_bar":
      return <StackedBarChartV2 chartId={chart.chartId} title={null} unit={u} data={d} width={width} height={height} />;
    case "waterfall":
      return <WaterfallV2 chartId={chart.chartId} title={null} unit={u} data={d} width={width} height={height} />;
    case "scatter":
      return <PointChartV2 chartId={chart.chartId} title={null} unit={u} data={d} width={width} height={height} />;
    case "bubble":
      return <PointChartV2 chartId={chart.chartId} title={null} unit={u} data={d} width={width} height={height} bubble />;
    case "candle":
      return <CandleChartV2 chartId={chart.chartId} title={null} unit={u} data={d} width={width} height={height} />;
    case "slope":
      return <SlopeChartV2 chartId={chart.chartId} title={null} unit={u} data={d} width={width} height={height} />;
    case "donut": return <Donut data={d} {...box} />;
    case "gantt": return <Gantt data={d} {...box} />;
    case "heatmap": return <Heatmap data={d} {...box} />;
    case "network": return <Network data={d} {...box} />;
    case "sankey": return <Sankey data={d} {...box} />;
    case "choropleth":
      return <BarChartV2 chartId={chart.chartId} mode="bar" title={null} unit={u} data={(Array.isArray(d) ? d : []).map((x: any) => ({ label: x.country_code, value: x.value }))} width={width} height={height} />;
    default: return null;
  }
};
