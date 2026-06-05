// charts/util.ts — XY family 공용 헬퍼 (Phase 1, v0.31.0).
//
// 차트마다 다시 그리지 않을 것들:
//   1. x 좌표 스케일 (time-aware: ISO 면 scaleTime, 아니면 scalePoint).
//   2. y tick 생성 (보기 좋은 분할 수).
//   3. draw progression (Material decelerate).
//   4. 끝점 라벨 1D 충돌 회피 (자체 구현 — labella 의존 회피, 결정론).
//   5. stagger.

import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { scaleLinear, scalePoint, scaleTime } from "d3-scale";
import { timeFormat, timeParse } from "d3-time-format";

import { duration, easing, msToFrames, stagger as staggerToken } from "../design";

// ────────────────────────────────────────────────────────────
// 1. X 스케일 (time / categorical 자동 판별)
// ────────────────────────────────────────────────────────────

const DATE_PARSERS: Array<(s: string) => Date | null> = [
  timeParse("%Y-%m-%d"),
  timeParse("%Y-%m"),
  timeParse("%Y/%m/%d"),
  timeParse("%Y"),
];

const tryParseDate = (s: string): Date | null => {
  for (const p of DATE_PARSERS) {
    const d = p(s);
    if (d) return d;
  }
  return null;
};

export type XScale = {
  kind: "time" | "point";
  apply: (x: string) => number;
  ticks: Array<{ pos: number; label: string }>;
};

// xs: 원본 x 라벨 배열 (순서 유지).
// range: [px_start, px_end].
// maxTicks: 축 위 최대 tick 개수.
export const buildXScale = (
  xs: string[],
  range: [number, number],
  maxTicks = 6,
): XScale => {
  // Time 판별: 모든 x 가 파싱 가능하면 time.
  const dates = xs.map(tryParseDate);
  const allDates = dates.every((d) => d !== null);

  if (allDates && dates.length >= 2) {
    const ds = dates as Date[];
    const scale = scaleTime().domain([ds[0], ds[ds.length - 1]]).range(range);
    // 시간 위계 자동: 도메인 폭에 따라 year / month / day 포맷.
    const span = ds[ds.length - 1].getTime() - ds[0].getTime();
    const yr = 365 * 24 * 3600 * 1000;
    const fmt =
      span > yr * 3
        ? timeFormat("%Y")
        : span > yr * 0.5
          ? timeFormat("%Y-%m")
          : timeFormat("%m-%d");
    const ticks = scale.ticks(maxTicks).map((t) => ({
      pos: scale(t),
      label: fmt(t),
    }));
    return {
      kind: "time",
      apply: (x: string) => {
        const d = tryParseDate(x);
        return d ? scale(d) : range[0];
      },
      ticks,
    };
  }

  // Categorical fallback — scalePoint.
  const scale = scalePoint<string>().domain(xs).range(range).padding(0.5);
  // tick 은 첫·중간·마지막 + maxTicks 분포.
  let pickIdx: number[];
  if (xs.length <= maxTicks) {
    pickIdx = xs.map((_, i) => i);
  } else {
    pickIdx = [];
    for (let i = 0; i < maxTicks; i++) {
      pickIdx.push(Math.round((i * (xs.length - 1)) / (maxTicks - 1)));
    }
  }
  const ticks = pickIdx.map((i) => ({
    pos: scale(xs[i]) ?? 0,
    label: xs[i],
  }));
  return {
    kind: "point",
    apply: (x: string) => scale(x) ?? range[0],
    ticks,
  };
};

// ────────────────────────────────────────────────────────────
// 2. Y 스케일 + "보기 좋은" tick
// ────────────────────────────────────────────────────────────

export type YScale = {
  apply: (v: number) => number;
  ticks: Array<{ pos: number; label: string }>;
  min: number;
  max: number;
};

const niceNum = (range: number, round: boolean): number => {
  const expv = Math.floor(Math.log10(range));
  const f = range / Math.pow(10, expv);
  let nf: number;
  if (round) {
    nf = f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10;
  } else {
    nf = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
  }
  return nf * Math.pow(10, expv);
};

export const buildYScale = (
  values: number[],
  range: [number, number],
  opts: { includeZero?: boolean; unit?: string; maxTicks?: number } = {},
): YScale => {
  const { includeZero = false, unit, maxTicks = 5 } = opts;
  let lo = Math.min(...values);
  let hi = Math.max(...values);
  if (includeZero) {
    lo = Math.min(0, lo);
    hi = Math.max(0, hi);
  }
  if (lo === hi) {
    lo -= 1;
    hi += 1;
  }
  // Nice ticks.
  const nrange = niceNum(hi - lo, false);
  const step = niceNum(nrange / (maxTicks - 1), true);
  const niceLo = Math.floor(lo / step) * step;
  const niceHi = Math.ceil(hi / step) * step;
  const scale = scaleLinear().domain([niceLo, niceHi]).range([range[1], range[0]]);
  const tickVals: number[] = [];
  for (let v = niceLo; v <= niceHi + 1e-9; v += step) tickVals.push(v);
  const fmt = (v: number): string => {
    let s: string;
    if (Math.abs(v) >= 10000) s = `${Math.round(v / 1000)}k`;
    else if (Math.abs(v) >= 100 || Number.isInteger(v)) s = String(Math.round(v));
    else s = (Math.round(v * 10) / 10).toString();
    return unit ? `${s} ${unit}` : s;
  };
  return {
    apply: (v: number) => scale(v),
    ticks: tickVals.map((v) => ({ pos: scale(v), label: fmt(v) })),
    min: niceLo,
    max: niceHi,
  };
};

// ────────────────────────────────────────────────────────────
// 3. Draw progression — Material decelerate.
// ────────────────────────────────────────────────────────────

const easeBezier = (cp: readonly [number, number, number, number]) => {
  // 3차 Bezier(0,0)→(cp[0],cp[1])→(cp[2],cp[3])→(1,1) 의 t→y 근사.
  // Remotion `interpolate` 의 easing 시그니처 (t) => v 와 호환.
  // 정확도 < 0.005, 표준 polynomial root 탐색 대신 Newton 2 step.
  return (t: number): number => {
    if (t <= 0) return 0;
    if (t >= 1) return 1;
    const ax = 3 * cp[0] - 3 * cp[2] + 1;
    const bx = 3 * cp[2] - 6 * cp[0];
    const cx = 3 * cp[0];
    const ay = 3 * cp[1] - 3 * cp[3] + 1;
    const by = 3 * cp[3] - 6 * cp[1];
    const cy = 3 * cp[1];
    // x(s) = t 가 되는 s 를 찾는다.
    let s = t;
    for (let i = 0; i < 4; i++) {
      const x = ((ax * s + bx) * s + cx) * s - t;
      const dx = (3 * ax * s + 2 * bx) * s + cx;
      if (Math.abs(dx) < 1e-6) break;
      s = s - x / dx;
    }
    s = Math.max(0, Math.min(1, s));
    return ((ay * s + by) * s + cy) * s;
  };
};

export const easeDecelerate = easeBezier(easing.decelerate);
export const easeStandard = easeBezier(easing.standard);

// Hook — 차트 진입 progression (0→1). delaySec 만큼 늦춤.
export const useDrawProgress = (
  delaySec = 0.25,
  durMs = duration.long,
): number => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const start = Math.round(delaySec * fps);
  const end = start + msToFrames(durMs, fps);
  return interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeDecelerate,
  });
};

// 시리즈 별 stagger — i 번째 시리즈의 진입 progression.
export const useSeriesProgress = (
  i: number,
  total: number,
  delaySec = 0.25,
  durMs = duration.long,
): number => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const staggerMs = staggerToken(total);
  const start = Math.round(delaySec * fps) + msToFrames(staggerMs * i, fps);
  const end = start + msToFrames(durMs, fps);
  return interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeDecelerate,
  });
};

// ────────────────────────────────────────────────────────────
// 4. 끝점 라벨 1D 충돌 회피 (자체 구현, 결정론).
//    각 라벨에 ideal y 가 있을 때 인접 라벨이 minGap 이상 떨어지도록 조정.
// ────────────────────────────────────────────────────────────

export type LabelSpot = { y: number; idealY: number; data: unknown };

export const layoutEndpointLabels = (
  spots: Array<{ idealY: number; data: unknown }>,
  yMin: number,
  yMax: number,
  minGap: number,
): LabelSpot[] => {
  if (!spots.length) return [];
  // ideal y 오름차순 정렬 + 원래 인덱스 보존.
  const indexed = spots.map((s, i) => ({ ...s, idx: i }));
  indexed.sort((a, b) => a.idealY - b.idealY);
  // 첫 패스: 위에서 아래로 — 이전 라벨 + minGap 보다 작으면 밀어내림.
  const ys = indexed.map((s) => s.idealY);
  for (let i = 1; i < ys.length; i++) {
    if (ys[i] - ys[i - 1] < minGap) ys[i] = ys[i - 1] + minGap;
  }
  // 둘째 패스: 아래에서 위로 — 영역 밖이면 위로 압축.
  if (ys[ys.length - 1] > yMax) ys[ys.length - 1] = yMax;
  for (let i = ys.length - 2; i >= 0; i--) {
    if (ys[i + 1] - ys[i] < minGap) ys[i] = ys[i + 1] - minGap;
  }
  // 위 경계 밖이면 다시 누르기.
  if (ys[0] < yMin) ys[0] = yMin;
  for (let i = 1; i < ys.length; i++) {
    if (ys[i] - ys[i - 1] < minGap) ys[i] = ys[i - 1] + minGap;
  }
  // 원래 인덱스 순서로 복원.
  const out: LabelSpot[] = new Array(spots.length);
  for (let i = 0; i < indexed.length; i++) {
    out[indexed[i].idx] = {
      y: ys[i],
      idealY: indexed[i].idealY,
      data: indexed[i].data,
    };
  }
  return out;
};

// ────────────────────────────────────────────────────────────
// 5. 시리즈 추출 — flat (rows with .series) 또는 stacked-area dict.
// ────────────────────────────────────────────────────────────

export type XYPoint = { x: string; y: number; event?: string };

export const groupBySeries = (
  rows: Array<{ x: string; y: number; series?: string; event?: string }>,
): Array<{ name: string; points: XYPoint[] }> => {
  const map = new Map<string, XYPoint[]>();
  const order: string[] = [];
  for (const r of rows) {
    const k = r.series ?? "_";
    if (!map.has(k)) {
      map.set(k, []);
      order.push(k);
    }
    map.get(k)!.push({ x: r.x, y: r.y, event: r.event });
  }
  return order.map((name) => ({ name, points: map.get(name)! }));
};

// 모든 시리즈의 x 라벨 합집합 (순서 보존: 첫 등장 순).
export const unionXs = (rows: Array<{ x: string }>): string[] => {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const r of rows) {
    const k = String(r.x);
    if (!seen.has(k)) {
      seen.add(k);
      out.push(k);
    }
  }
  return out;
};
