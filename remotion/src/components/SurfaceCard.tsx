import React from "react";

import {
  fontFamily,
  koreanTextStyle,
  radius,
  shadow,
  space,
  surface,
} from "../design";

// SurfaceCard — 9장 레퍼런스 표준 카드: 흰 fill + 옅은 그림자 + 큰 라운드 (22px).
// 모든 차트·텍스트 블록의 컨테이너. Aurora glass 대체.

export type SurfaceCardProps = {
  children: React.ReactNode;
  padding?: number | string;
  width?: number | string;
  height?: number | string;
  variant?: "white" | "alt";
  style?: React.CSSProperties;
};

export const SurfaceCard: React.FC<SurfaceCardProps> = ({
  children,
  padding = space.xl,
  width,
  height,
  variant = "white",
  style,
}) => {
  return (
    <div
      style={{
        background: variant === "alt" ? surface.cardAlt : surface.card,
        borderRadius: radius.lg,
        boxShadow: shadow.card,
        padding,
        width,
        height,
        fontFamily,
        ...koreanTextStyle,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
