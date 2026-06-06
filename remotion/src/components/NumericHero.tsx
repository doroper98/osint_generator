import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

import {
  accent,
  duration,
  fontFamily,
  koreanTextStyle,
  letterSpacing,
  lineHeight,
  msToFrames,
  size,
  text,
  weight,
} from "../design";

// NumericHero — 거대 숫자 카운트업 + 라벨. 9장 레퍼런스의 시그니처 (`$750K`, `31 MILLION`).
//
// 진입: count-up (0 → value) over 800ms, Material decelerate.
// 라벨: 숫자 뒤에 작게 (오른쪽 또는 아래).

export type NumericHeroProps = {
  value: number;
  prefix?: string;        // 예: "$"
  suffix?: string;        // 예: "%", "M", "K"
  label?: string | null;
  decimals?: number;
  color?: string;
  sizePx?: number;
  startFrame?: number;
  durationMs?: number;
};

export const NumericHero: React.FC<NumericHeroProps> = ({
  value,
  prefix = "",
  suffix = "",
  label,
  decimals = 0,
  color = text.primary,
  sizePx = size.display,
  startFrame = 0,
  durationMs = duration.long,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const f = Math.max(0, frame - startFrame);
  const dur = msToFrames(durationMs, fps);

  // Material decelerate count-up.
  const progress = interpolate(f, [0, dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: (t) => 1 - Math.pow(1 - t, 3),
  });
  const current = value * progress;
  const display =
    decimals > 0 ? current.toFixed(decimals) : Math.round(current).toLocaleString("en-US");

  // Suffix 페이드인 (count-up 끝나갈 때).
  const suffixOpacity = interpolate(f, [dur * 0.7, dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        fontFamily,
        ...koreanTextStyle,
      }}
    >
      <div
        style={{
          fontSize: sizePx,
          fontWeight: weight.black,
          lineHeight: lineHeight.tight,
          letterSpacing: letterSpacing.tightest,
          color,
          fontVariantNumeric: "tabular-nums",
          display: "flex",
          alignItems: "baseline",
        }}
      >
        {prefix && <span>{prefix}</span>}
        <span>{display}</span>
        {suffix && (
          <span
            style={{
              fontSize: sizePx * 0.45,
              fontWeight: weight.bold,
              marginLeft: sizePx * 0.05,
              color: accent.primary,
              opacity: suffixOpacity,
            }}
          >
            {suffix}
          </span>
        )}
      </div>
      {label && (
        <div
          style={{
            fontSize: size.caption,
            fontWeight: weight.semibold,
            color: text.secondary,
            marginTop: 12,
            letterSpacing: letterSpacing.tight,
            ...koreanTextStyle,
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};
