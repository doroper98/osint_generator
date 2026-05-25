import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// render_props.json 의 chartData 와 동일 구조 (orchestrator/render_io.py:RenderChart).
export type ChartData = {
  chartId: string;
  type: string;
  title?: string;
  data: any;
  unit?: string;
};

const ACCENT = "#e0a458";
const GRID = "#2c3647";
const TXT = "#aeb6c2";
const LINE = "#5bc0de";

function fmtNum(v: number): string {
  if (Math.abs(v) >= 1000) return Math.round(v).toLocaleString("en-US");
  if (Number.isInteger(v)) return String(v);
  return v.toFixed(1);
}

// line family — 데이터로 cinematic 재렌더(좌→우 draw-on + event 강조). 영상미 C0.
const LineChart: React.FC<{ data: any; unit?: string; width: number; height: number }> = ({
  data,
  unit,
  width,
  height,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pts: Array<{ x: any; y: number; event?: string }> = Array.isArray(data)
    ? data.filter((d) => d && typeof d.y === "number")
    : [];
  if (pts.length < 2) return null;

  const padL = 80;
  const padR = 48;
  const padT = 28;
  const padB = 54;
  const ys = pts.map((d) => d.y);
  let min = Math.min(...ys);
  let max = Math.max(...ys);
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const n = pts.length;
  const X = (i: number) => padL + (i * (width - padL - padR)) / (n - 1);
  const Y = (v: number) => padT + (1 - (v - min) / (max - min)) * (height - padT - padB);

  const coords = pts.map((d, i) => [X(i), Y(d.y)] as [number, number]);
  const dPath = coords.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  let pathLen = 0;
  for (let i = 1; i < coords.length; i++) {
    pathLen += Math.hypot(coords[i][0] - coords[i - 1][0], coords[i][1] - coords[i - 1][1]);
  }
  // 좌→우 그려지기 (10프레임 뒤 ~1.8초간).
  const progress = interpolate(frame, [10, 10 + fps * 1.8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const gridVals = [max, (max + min) / 2, min];

  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {gridVals.map((v, k) => {
        const yy = Y(v);
        return (
          <g key={`g${k}`}>
            <line x1={padL} y1={yy} x2={width - padR} y2={yy} stroke={GRID} strokeWidth={1} />
            <text x={padL - 12} y={yy + 7} fontSize={22} fill={TXT} textAnchor="end" style={{ fontFamily: "sans-serif" }}>
              {fmtNum(v)}
              {unit ? ` ${unit}` : ""}
            </text>
          </g>
        );
      })}
      <text x={padL} y={height - 18} fontSize={22} fill={TXT} textAnchor="start" style={{ fontFamily: "sans-serif" }}>
        {String(pts[0].x ?? "")}
      </text>
      <text x={width - padR} y={height - 18} fontSize={22} fill={TXT} textAnchor="end" style={{ fontFamily: "sans-serif" }}>
        {String(pts[n - 1].x ?? "")}
      </text>

      <path
        d={dPath}
        fill="none"
        stroke={LINE}
        strokeWidth={4}
        strokeLinejoin="round"
        strokeLinecap="round"
        strokeDasharray={pathLen}
        strokeDashoffset={pathLen * (1 - progress)}
      />

      {pts.map((d, i) => {
        if (!d.event) return null;
        if (i / (n - 1) > progress + 0.03) return null; // 선이 도달한 뒤 등장
        const [cx, cy] = coords[i];
        return (
          <g key={`e${i}`}>
            <circle cx={cx} cy={cy} r={7} fill={ACCENT} stroke="#0e1116" strokeWidth={2} />
            <text
              x={cx}
              y={cy - 16}
              fontSize={22}
              fontWeight={700}
              fill="#f5f7fa"
              textAnchor="middle"
              stroke="#0b0f16"
              strokeWidth={5}
              paintOrder="stroke"
              style={{ fontFamily: "sans-serif" }}
            >
              {d.event}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

// 타입별 family 디스패치. 지원 타입만 렌더, 그 외엔 null(상위가 텍스트로 폴백).
export const ChartView: React.FC<{ chart: ChartData; width: number; height: number }> = ({
  chart,
  width,
  height,
}) => {
  if (chart.type === "line") {
    return <LineChart data={chart.data} unit={chart.unit} width={width} height={height} />;
  }
  return null;
};
