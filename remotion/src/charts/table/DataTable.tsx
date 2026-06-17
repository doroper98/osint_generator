import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

import {
  accent,
  fontFamily,
  grid,
  koreanTextStyle,
  label,
  lineHeight,
  msToFrames,
  stagger as staggerToken,
  surface,
  text,
  weight,
} from "../../design";
import { easeDecelerate } from "../util";

// DataTable — cinematic 표 렌더러 (v0.41.0).
//
// "정적 표를 화면에 박는 것"(C0 금지)이 아니라, 헤더 → 행 순차 등장(stagger)으로
// 읽기 흐름을 만들고, 강조 행(highlight)은 accent 배경이 부드럽게 차오르게 한다.
// 분석 보고서의 비교표·매핑표(OCML vs E-BOM, 반제품별 검사 매핑 등) — 현재 차트
// family 밖이라 영상화 못 하던 타입 — 를 영상용으로 재렌더하기 위한 첫 표 렌더러.
//
// 입력 (data):
//   {
//     columns: Array<{ key, label, align?, weight?, accent? }>,
//     rows:    Array<{ cells: { [key]: string }, highlight?: boolean }>,
//   }
//   - align: "left" | "center" | "right" (기본 left, 첫 열 외 center 권장)
//   - weight: 열 너비 가중치 (기본 1)
//   - accent: 헤더 셀 색 (열 강조)
//   - highlight: 행 강조 (★ 행 — accent 배경 + 좌측 바)
//
// 셀 텍스트 선두 기호로 의미색 자동 부여 (보편 표 관례, 결정론):
//   ✓ ● → <확인> 녹 / ✗ ✘ ✕ → <미검증> 레드 / ○ → 회색.

type TableColumn = {
  key: string;
  label: string;
  align?: "left" | "center" | "right";
  weight?: number;
  accent?: string;
};

type TableRow = {
  cells: Record<string, string>;
  highlight?: boolean;
};

type TableData = {
  columns: TableColumn[];
  rows: TableRow[];
};

export type DataTableProps = {
  data: unknown;
  width: number;
  height: number;
  title?: string | null;
};

const parse = (data: unknown): TableData | null => {
  if (typeof data !== "object" || data === null) return null;
  const d = data as Record<string, unknown>;
  const columns = Array.isArray(d.columns) ? (d.columns as TableColumn[]) : [];
  const rows = Array.isArray(d.rows) ? (d.rows as TableRow[]) : [];
  const validCols = columns.filter((c) => c && typeof c.key === "string");
  if (!validCols.length || !rows.length) return null;
  return { columns: validCols, rows };
};

// 셀 선두 기호 → 의미색 (없으면 기본 본문색).
const cellTone = (value: string): string => {
  const s = value.trim();
  if (s.startsWith("✓") || s.startsWith("●")) return label.verified;
  if (s.startsWith("✗") || s.startsWith("✘") || s.startsWith("✕")) return label.unverified;
  if (s.startsWith("○")) return text.tertiary;
  return text.primary;
};

export const DataTable: React.FC<DataTableProps> = ({ data, width, height }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const parsed = parse(data);

  if (!parsed) {
    return (
      <div
        style={{
          width,
          height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: text.tertiary,
          fontFamily,
          fontSize: 20,
          ...koreanTextStyle,
        }}
      >
        표 데이터 부족
      </div>
    );
  }

  const { columns, rows } = parsed;
  const nCols = columns.length;
  const nRows = rows.length;

  // 적응형 폰트 — 열·행이 많을수록 축소.
  let cellFont = nCols <= 3 ? 27 : nCols === 4 ? 23 : 20;
  if (nRows > 8) cellFont -= 2;
  if (nRows > 11) cellFont -= 2;
  const headerFont = Math.max(15, cellFont - 2);

  // 열 너비 — weight 비례 grid template.
  const gridTemplate = columns
    .map((c) => `${Math.max(0.4, c.weight ?? 1)}fr`)
    .join(" ");

  const headerH = headerFont + 26;
  const rowH = Math.max(28, (height - headerH) / nRows);

  const cellPadH = 16;
  const align = (c: TableColumn): "left" | "center" | "right" => c.align ?? "left";

  // 헤더 진입.
  const headerOpacity = interpolate(frame, [4, 4 + msToFrames(220, fps)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeDecelerate,
  });

  const delayF = Math.round(0.32 * fps);
  const stagMs = staggerToken(nRows, 90, 700);

  return (
    <div
      style={{
        width,
        height,
        fontFamily,
        color: text.primary,
        display: "flex",
        flexDirection: "column",
        ...koreanTextStyle,
      }}
    >
      {/* 헤더 */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: gridTemplate,
          alignItems: "end",
          height: headerH,
          opacity: headerOpacity,
          borderBottom: `2px solid ${grid.axis}`,
        }}
      >
        {columns.map((c) => (
          <div
            key={c.key}
            style={{
              fontSize: headerFont,
              fontWeight: weight.bold,
              color: c.accent ?? text.secondary,
              textAlign: align(c),
              padding: `0 ${cellPadH}px 8px`,
              ...koreanTextStyle,
            }}
          >
            {c.label}
          </div>
        ))}
      </div>

      {/* 행 */}
      <div style={{ flex: 1 }}>
        {rows.map((row, i) => {
          const startF = delayF + msToFrames(stagMs * i, fps);
          const endF = startF + msToFrames(360, fps);
          const prog = interpolate(frame, [startF, endF], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: easeDecelerate,
          });
          const ty = (1 - prog) * 14;
          // 강조 행 배경은 행 등장 직후 차오른다.
          const hlProg = interpolate(frame, [startF + 3, endF + 6], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: easeDecelerate,
          });
          const stripe = i % 2 === 1 ? surface.cardAlt : "transparent";

          return (
            <div
              key={i}
              style={{
                position: "relative",
                display: "grid",
                gridTemplateColumns: gridTemplate,
                alignItems: "center",
                height: rowH,
                opacity: prog,
                transform: `translateY(${ty}px)`,
                background: row.highlight
                  ? `rgba(232, 74, 45, ${0.1 * hlProg})`
                  : stripe,
                borderBottom: `1px solid ${surface.divider}`,
              }}
            >
              {row.highlight ? (
                <div
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: 4,
                    background: accent.primary,
                    transform: `scaleY(${hlProg})`,
                    transformOrigin: "center",
                  }}
                />
              ) : null}
              {columns.map((c) => {
                const value = row.cells?.[c.key] ?? "";
                return (
                  <div
                    key={c.key}
                    style={{
                      fontSize: cellFont,
                      fontWeight: c.key === columns[0].key ? weight.semibold : weight.regular,
                      lineHeight: lineHeight.tight,
                      color: cellTone(value),
                      textAlign: align(c),
                      padding: `0 ${cellPadH}px`,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      ...koreanTextStyle,
                    }}
                  >
                    {value}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
};
