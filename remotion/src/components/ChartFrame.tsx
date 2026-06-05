import React from "react";
import {
  chart,
  fontFamily,
  koreanTextStyle,
  letterSpacing,
  lineHeight,
  size,
  text,
  weight,
} from "../design";

// ChartFrame — 모든 차트 family 가 공유하는 외곽 골격.
// kicker (작은 빨간선/카테고리 라벨), title (큰 제목), subtitle (한 줄 보조), source (출처).
// 본 컴포넌트는 SVG 가 아니라 div 로 박는다 — 차트 본체 (SVG/Canvas) 가 children 으로 들어감.
//
// 슬롯이 비면 해당 슬롯을 차지하지 않는다 (공간 절약). 빈 출처 슬롯은 라벨 시스템과 정합:
// `sourceLinkRequired` 가 true 이고 source 가 비면 호출자가 다른 곳에 표시 (별도 정책).

export type ChartFrameProps = {
  kicker?: string | null;
  title?: string | null;
  subtitle?: string | null;
  source?: string | null;
  width?: number;
  height?: number;
  children: React.ReactNode;
};

export const ChartFrame: React.FC<ChartFrameProps> = ({
  kicker,
  title,
  subtitle,
  source,
  width = chart.width,
  height = chart.height,
  children,
}) => {
  return (
    <div
      style={{
        width,
        fontFamily,
        color: text.primary,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        ...koreanTextStyle,
      }}
    >
      {/* Header — kicker + title + subtitle */}
      {(kicker || title || subtitle) && (
        <div style={{ marginBottom: 12 }}>
          {kicker ? (
            <div
              style={{
                fontSize: size.meta,
                fontWeight: weight.bold,
                letterSpacing: letterSpacing.wider,
                color: text.tertiary,
                textTransform: "uppercase",
                marginBottom: 6,
              }}
            >
              {kicker}
            </div>
          ) : null}
          {title ? (
            <div
              style={{
                fontSize: size.title,
                fontWeight: weight.extrabold,
                lineHeight: lineHeight.tight,
                color: text.primary,
                ...koreanTextStyle,
              }}
            >
              {title}
            </div>
          ) : null}
          {subtitle ? (
            <div
              style={{
                fontSize: size.body,
                fontWeight: weight.medium,
                lineHeight: lineHeight.normal,
                color: text.secondary,
                marginTop: 8,
                ...koreanTextStyle,
              }}
            >
              {subtitle}
            </div>
          ) : null}
        </div>
      )}

      {/* Body — 차트 본체 (SVG 또는 div) */}
      <div style={{ width, height }}>{children}</div>

      {/* Footer — 출처 */}
      {source ? (
        <div
          style={{
            fontSize: size.meta,
            color: text.tertiary,
            marginTop: 8,
            ...koreanTextStyle,
          }}
        >
          출처 : {source}
        </div>
      ) : null}
    </div>
  );
};
