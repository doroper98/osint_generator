import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

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

// NOTE: XY family (line/area/stacked_area/small_multiples/dual_line/forecast) 는
// v0.31.0 부터 charts/xy/ 로 이관됨. 본 파일은 Phase 2+ 의 bar/point/specialty 폴백.

// ── bar / lollipop / range_bar ────────────────────────────────────
const BarChart: React.FC<{ data: any; unit?: string; mode?: "bar" | "lollipop" | "range" } & Box> = ({ data, unit, mode = "bar", width, height }) => {
  const prog = useDraw(8, 1.0);
  const rows: any[] = Array.isArray(data) ? data : [];
  if (!rows.length) return null;
  const vals = mode === "range" ? rows.flatMap((d) => [d.low, d.high]) : rows.map((d) => d.value);
  let min = Math.min(0, ...vals), max = Math.max(...vals);
  if (min === max) max += 1;
  const n = rows.length;
  const bw = (width - PAD.l - PAD.r) / n;
  const Y = (v: number) => PAD.t + (1 - (v - min) / (max - min)) * (height - PAD.t - PAD.b);
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {yGrid(min, max, Y, PAD.l, width - PAD.r, unit)}
      {rows.map((d, i) => {
        const cx = PAD.l + bw * (i + 0.5);
        const col = PALETTE[i % PALETTE.length];
        const lab = (
          <text key={`l${i}`} x={clampX(cx, width)} y={height - 18} fontSize={20} fill={TXT}
            textAnchor={edgeAnchor(cx, width)} style={FONT}>{d.label}</text>
        );
        if (mode === "range") {
          const yH = Y(d.high), yL = Y(d.low);
          return (<g key={i}><rect x={cx - bw * 0.18} y={yH} width={bw * 0.36} height={(yL - yH) * prog} rx={6} fill={col} />{lab}</g>);
        }
        if (mode === "lollipop") {
          const y = Y(d.value);
          return (<g key={i}><line x1={cx} y1={Y(0)} x2={cx} y2={Y(0) + (y - Y(0)) * prog} stroke={col} strokeWidth={4} /><circle cx={cx} cy={Y(0) + (y - Y(0)) * prog} r={9} fill={col} />{lab}</g>);
        }
        const y = Y(d.value), base = Y(Math.max(0, min));
        const h = (base - y) * prog;
        return (<g key={i}><rect x={cx - bw * 0.32} y={base - h} width={bw * 0.64} height={Math.abs(h)} rx={5} fill={col} /><text x={cx} y={base - h - 8} fontSize={19} fill={FG} textAnchor="middle" style={FONT} opacity={prog}>{fmtNum(d.value)}</text>{lab}</g>);
      })}
    </svg>
  );
};

// ── stacked / stacked_bar ─────────────────────────────────────────
const StackedBar: React.FC<{ data: any; unit?: string } & Box> = ({ data, unit, width, height }) => {
  const prog = useDraw(8, 1.0);
  const cats: string[] = data?.categories ?? [];
  const series: any[] = data?.series ?? [];
  if (!cats.length || !series.length) return null;
  const totals = cats.map((_, ci) => series.reduce((s, se) => s + (se.values?.[ci] ?? 0), 0));
  const max = Math.max(...totals) || 1;
  const n = cats.length;
  const bw = (width - PAD.l - PAD.r) / n;
  const Y = (v: number) => PAD.t + (1 - v / max) * (height - PAD.t - PAD.b);
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {yGrid(0, max, Y, PAD.l, width - PAD.r, unit)}
      {cats.map((c, ci) => {
        const cx = PAD.l + bw * (ci + 0.5);
        let acc = 0;
        return (
          <g key={ci}>
            {series.map((se, si) => {
              const v = se.values?.[ci] ?? 0;
              const y0 = Y(acc), y1 = Y(acc + v);
              acc += v;
              return <rect key={si} x={cx - bw * 0.32} y={y1} width={bw * 0.64} height={(y0 - y1) * prog} fill={PALETTE[si % PALETTE.length]} />;
            })}
            <text x={clampX(cx, width)} y={height - 18} fontSize={20} fill={TXT} textAnchor={edgeAnchor(cx, width)} style={FONT}>{c}</text>
          </g>
        );
      })}
    </svg>
  );
};

// ── waterfall ─────────────────────────────────────────────────────
const Waterfall: React.FC<{ data: any; unit?: string } & Box> = ({ data, unit, width, height }) => {
  const prog = useDraw(8, 1.1);
  const rows: any[] = Array.isArray(data) ? data : [];
  if (!rows.length) return null;
  let run = 0; const bars = rows.map((d) => {
    if (d.type === "total") { const b = { lo: 0, hi: d.value, t: "total", label: d.label, val: d.value }; run = d.value; return b; }
    const lo = run, hi = run + d.value; run = hi; return { lo: Math.min(lo, hi), hi: Math.max(lo, hi), t: d.type, label: d.label, val: d.value };
  });
  const max = Math.max(...bars.map((b) => b.hi)), min = Math.min(0, ...bars.map((b) => b.lo));
  const n = bars.length, bw = (width - PAD.l - PAD.r) / n;
  const Y = (v: number) => PAD.t + (1 - (v - min) / (max - min)) * (height - PAD.t - PAD.b);
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {yGrid(min, max, Y, PAD.l, width - PAD.r, unit)}
      {bars.map((b, i) => {
        const cx = PAD.l + bw * (i + 0.5);
        const col = b.t === "total" ? PALETTE[0] : b.t === "pos" ? POS : NEG;
        const yTop = Y(b.hi), yBot = Y(b.lo);
        return (
          <g key={i} opacity={i / n <= prog + 0.05 ? 1 : 0}>
            <rect x={cx - bw * 0.32} y={yTop} width={bw * 0.64} height={Math.max(2, yBot - yTop)} rx={4} fill={col} />
            <text x={cx} y={yTop - 8} fontSize={19} fill={FG} textAnchor="middle" style={FONT}>{(b.val > 0 && b.t !== "total" ? "+" : "") + fmtNum(b.val)}</text>
            <text x={clampX(cx, width)} y={height - 18} fontSize={18} fill={TXT} textAnchor={edgeAnchor(cx, width)} style={FONT}>{b.label}</text>
          </g>
        );
      })}
    </svg>
  );
};

// ── scatter / bubble ──────────────────────────────────────────────
const PointChart: React.FC<{ data: any; bubble?: boolean } & Box> = ({ data, bubble, width, height }) => {
  const prog = useDraw(8, 0.9);
  const rows: any[] = Array.isArray(data) ? data.filter((d) => typeof d.x === "number" && typeof d.y === "number") : [];
  if (!rows.length) return null;
  const xs = rows.map((d) => d.x), ys = rows.map((d) => d.y);
  let xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys);
  if (xmin === xmax) { xmin -= 1; xmax += 1; } if (ymin === ymax) { ymin -= 1; ymax += 1; }
  const smax = Math.max(...rows.map((d) => d.size ?? 1));
  const maxR = bubble ? 60 : 12; // 원이 가장자리서 잘리지 않게 plot 영역을 반지름만큼 inset (다듬기).
  const X = (v: number) => PAD.l + maxR + ((v - xmin) / (xmax - xmin)) * (width - PAD.l - PAD.r - 2 * maxR);
  const Y = (v: number) => PAD.t + maxR + (1 - (v - ymin) / (ymax - ymin)) * (height - PAD.t - PAD.b - 2 * maxR);
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {yGrid(ymin, ymax, Y, PAD.l, width - PAD.r)}
      {rows.map((d, i) => {
        const r = bubble ? 14 + 46 * Math.sqrt((d.size ?? 1) / smax) : 11;
        const cx = X(d.x), cy = Y(d.y), col = PALETTE[i % PALETTE.length];
        return (
          <g key={i} opacity={prog}>
            <circle cx={cx} cy={cy} r={r * prog} fill={col} opacity={0.62} stroke={col} strokeWidth={2} />
            {d.label && <Halo x={clampX(cx, width)} y={cy - r - 6} fontSize={20} fontWeight={700} fill={FG} textAnchor={edgeAnchor(cx, width)}>{d.label}</Halo>}
          </g>
        );
      })}
    </svg>
  );
};

// ── candle ────────────────────────────────────────────────────────
const Candle: React.FC<{ data: any; unit?: string } & Box> = ({ data, unit, width, height }) => {
  const prog = useDraw(8, 1.0);
  const rows: any[] = Array.isArray(data) ? data : [];
  if (!rows.length) return null;
  const min = Math.min(...rows.map((d) => d.low)), max = Math.max(...rows.map((d) => d.high));
  const n = rows.length, bw = (width - PAD.l - PAD.r) / n;
  const Y = (v: number) => PAD.t + (1 - (v - min) / (max - min)) * (height - PAD.t - PAD.b);
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {yGrid(min, max, Y, PAD.l, width - PAD.r, unit)}
      {rows.map((d, i) => {
        if (i / n > prog + 0.05) return null;
        const cx = PAD.l + bw * (i + 0.5);
        const up = d.close >= d.open, col = up ? POS : NEG;
        return (
          <g key={i}>
            <line x1={cx} y1={Y(d.high)} x2={cx} y2={Y(d.low)} stroke={col} strokeWidth={2} />
            <rect x={cx - bw * 0.28} y={Y(Math.max(d.open, d.close))} width={bw * 0.56} height={Math.max(2, Math.abs(Y(d.open) - Y(d.close)))} fill={col} />
          </g>
        );
      })}
    </svg>
  );
};

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

// ── slope ─────────────────────────────────────────────────────────
const Slope: React.FC<{ data: any } & Box> = ({ data, width, height }) => {
  const prog = useDraw();
  const items: any[] = data?.items ?? [];
  if (!items.length) return null;
  const all = items.flatMap((d) => [d.a, d.b]);
  let min = Math.min(...all), max = Math.max(...all); if (min === max) { min -= 1; max += 1; }
  const Y = (v: number) => PAD.t + (1 - (v - min) / (max - min)) * (height - PAD.t - PAD.b);
  const xL = PAD.l + 60, xR = width - PAD.r - 60;
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      <text x={xL} y={PAD.t - 6} fontSize={20} fill={TXT} textAnchor="middle" style={FONT}>{data.left_label}</text>
      <text x={xR} y={PAD.t - 6} fontSize={20} fill={TXT} textAnchor="middle" style={FONT}>{data.right_label}</text>
      {items.map((d, i) => {
        const col = PALETTE[i % PALETTE.length];
        const yA = Y(d.a), yB = Y(d.b), xMid = xL + (xR - xL) * prog;
        return (
          <g key={i}>
            <line x1={xL} y1={yA} x2={xMid} y2={yA + (yB - yA) * prog} stroke={col} strokeWidth={3} />
            <circle cx={xL} cy={yA} r={6} fill={col} />
            <text x={xL - 12} y={yA + 5} fontSize={18} fill={FG} textAnchor="end" style={FONT}>{d.label}</text>
            {prog > 0.98 && <circle cx={xR} cy={yB} r={6} fill={col} />}
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

// ── choropleth (간이: 지역코드 막대 — 추후 지도 채색으로 업그레이드) ──
const ChoroplethBars: React.FC<{ data: any; unit?: string } & Box> = ({ data, unit, width, height }) => (
  <BarChart data={(Array.isArray(data) ? data : []).map((d: any) => ({ label: d.country_code, value: d.value }))} unit={unit} width={width} height={height} />
);

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
          title={chart.title}
          unit={u}
          data={d}
          width={width}
          height={height}
        />
      );
    case "dual_line":
      return <DualLineChart chartId={chart.chartId} title={chart.title} data={d} width={width} height={height} />;
    case "forecast":
      return (
        <ForecastChartV2
          chartId={chart.chartId}
          title={chart.title}
          unit={u}
          data={d}
          width={width}
          height={height}
        />
      );
    case "bar": return <BarChart data={d} unit={u} mode="bar" {...box} />;
    case "lollipop": return <BarChart data={d} unit={u} mode="lollipop" {...box} />;
    case "range_bar": return <BarChart data={d} unit={u} mode="range" {...box} />;
    case "stacked": case "stacked_bar": return <StackedBar data={d} unit={u} {...box} />;
    case "waterfall": return <Waterfall data={d} unit={u} {...box} />;
    case "scatter": return <PointChart data={d} {...box} />;
    case "bubble": return <PointChart data={d} bubble {...box} />;
    case "candle": return <Candle data={d} unit={u} {...box} />;
    case "donut": return <Donut data={d} {...box} />;
    case "gantt": return <Gantt data={d} {...box} />;
    case "slope": return <Slope data={d} {...box} />;
    case "heatmap": return <Heatmap data={d} {...box} />;
    case "network": return <Network data={d} {...box} />;
    case "sankey": return <Sankey data={d} {...box} />;
    case "choropleth": return <ChoroplethBars data={d} unit={u} {...box} />;
    default: return null;
  }
};
