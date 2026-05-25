import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

// 다크 럭셔리 OSINT 브리핑 카드 스킨 (영상미 C0).
// - 다크 glassmorphism fill + 얇은 오로라 그라데이션 보더 + 느리게 도는 엣지 하이라이트 + soft bloom.
// - 회전각을 Remotion frame 으로 구동 → 프레임 정확(결정론적). CSS 키프레임 애니 미사용.
// - 절제 원칙: 본체(차트/축/격자) 아닌 카드(자막·배지·브랜드·콜아웃)에만, 느린 sweep, no pulsing.
const AURORA = ["#78d7ff", "#7b61ff", "#d45cff", "#d6b37a"]; // 블루·바이올렛·마젠타·샴페인 골드

export const AuroraGlassCard: React.FC<{
  children: React.ReactNode;
  radius?: number;
  padding?: string;
  glow?: boolean;
  sweepSec?: number;       // 보더 하이라이트가 한 바퀴 도는 시간(느릴수록 고급).
  maxWidth?: number;
  accentBar?: string;      // 좌측 강조 바 색(인용 등). 없으면 미표시.
  border?: number;
}> = ({ children, radius = 16, padding = "18px 36px", glow = true, sweepSec = 9, maxWidth, accentBar, border = 2 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const angle = ((frame / (fps * sweepSec)) % 1) * 360; // 느린 1회전.
  // conic 그라데이션을 frame 으로 회전 → 보더 색이 천천히 돌며 엣지 하이라이트 효과.
  const auroraBorder = `conic-gradient(from ${angle.toFixed(2)}deg, ${AURORA[0]}, ${AURORA[1]}, ${AURORA[2]}, ${AURORA[3]}, ${AURORA[0]})`;
  return (
    <div
      style={{
        position: "relative",
        borderRadius: radius,
        padding: border,
        background: auroraBorder,
        maxWidth: maxWidth,
        boxShadow: glow
          ? "0 0 30px rgba(123,97,255,0.20), 0 0 14px rgba(120,215,255,0.16)"
          : "none",
      }}
    >
      <div
        style={{
          borderRadius: Math.max(0, radius - border),
          padding,
          background: "rgba(9,12,19,0.74)",
          backdropFilter: "blur(3px)",
          WebkitBackdropFilter: "blur(3px)",
          borderLeft: accentBar ? `6px solid ${accentBar}` : undefined,
        }}
      >
        {children}
      </div>
    </div>
  );
};
