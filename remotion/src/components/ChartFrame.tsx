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

// ChartFrame v2 (v0.33.0) — 편집 dashboard light 톤.
// kicker (소문자 caps) → title (굵은 디스플레이) → subtitle (보조) → 차트 본체 → source 메타.
// 카드 안에 들어가므로 자체 fill / shadow 없음 (SurfaceCard 가 그 역할).

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
      {(kicker || title || subtitle) && (
        <div style={{ marginBottom: 20 }}>
          {kicker ? (
            <div
              style={{
                fontSize: size.meta,
                fontWeight: weight.bold,
                letterSpacing: letterSpacing.caps,
                color: text.secondary,
                textTransform: "uppercase",
                marginBottom: 8,
              }}
            >
              {kicker}
            </div>
          ) : null}
          {title ? (
            <div
              style={{
                fontSize: size.title,
                fontWeight: weight.black,
                lineHeight: lineHeight.display,
                letterSpacing: letterSpacing.tight,
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
                marginTop: 12,
                ...koreanTextStyle,
              }}
            >
              {subtitle}
            </div>
          ) : null}
        </div>
      )}

      <div style={{ width, height }}>{children}</div>

      {source ? (
        <div
          style={{
            fontSize: size.meta,
            color: text.tertiary,
            marginTop: 12,
            fontWeight: weight.medium,
            ...koreanTextStyle,
          }}
        >
          출처 : {source}
        </div>
      ) : null}
    </div>
  );
};
