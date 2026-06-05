// design.ts — 영상미 디자인 시스템 토큰 (Phase 0, v0.30.0)
//
// 본 모듈은 차트·자막·플레이트·헤더의 폰트·색·모션·여백을 **하나의 SSOT** 로 모은다.
// 차트 family 코드가 색·폰트를 하드코딩하면 코드 리뷰에서 차단한다 (CLAUDE.md C0 영상미 + C8 추상화 절제).
//
// 출처는 docs/PROFESSIONAL_REBUILD_PLAN.md §1 Phase A 리서치.

// ────────────────────────────────────────────────────────────
// 1. Color tokens
// ────────────────────────────────────────────────────────────

// 다크 베이스 (Material Dark 권장; #000 은 잔상·과대비).
export const surface = {
  base: "#121214",
  s1: "#1a1d22",
  s2: "#22262d",
} as const;

// 텍스트 (모두 surface.base 위 WCAG AAA 7:1+).
export const text = {
  primary: "#f5f7fa",
  secondary: "rgba(245,247,250,0.72)",
  tertiary: "rgba(245,247,250,0.48)",
  inverse: "#0c0e12",
} as const;

// Grid / divider (정보 보조).
export const line = {
  grid: "rgba(245,247,250,0.08)",
  divider: "rgba(245,247,250,0.16)",
  axis: "rgba(245,247,250,0.32)",
} as const;

// 검증 라벨 의미 컬러 (docs/06 §6 라벨 시스템과 동일 — 기존 유지).
export const label = {
  verified: "#5cb85c",    // <확인>
  inferred: "#5bc0de",    // <추론>
  claimed: "#f0ad4e",     // <주장>
  unverified: "#d9534f",  // <미검증> / <반박됨>
} as const;

// 시리즈 컬러 — Okabe-Ito 색맹 안전 팔레트 (다크 베이스 위 가독 검증).
// 차트 본체 시리즈/카테고리 색은 본 팔레트만 사용. 의미 컬러(label.*) 와 분리.
export const series = [
  "#56B4E9", // 스카이블루
  "#E69F00", // 오렌지
  "#009E73", // 청록
  "#F0E442", // 옐로우
  "#0072B2", // 딥블루
  "#D55E00", // 다크오렌지
  "#CC79A7", // 핑크
  "#94a3b8", // 슬레이트 (8 번째 안전색)
] as const;

// 인용·강조 (자막 인용 분기).
export const accent = {
  quote: "#e0a458",       // 샴페인 골드 — 인용 강조
  positive: "#5cb85c",
  negative: "#d9534f",
  spotlight: "#78d7ff",   // 모멘트 스포트라이트
} as const;

// Aurora 보더 그라디언트 (AuroraGlassCard 토큰화).
export const aurora = ["#78d7ff", "#7b61ff", "#d45cff", "#d6b37a"] as const;

// ────────────────────────────────────────────────────────────
// 2. Typography
// ────────────────────────────────────────────────────────────

// Pretendard Variable (45–920 wght axis). 실제 fetch 는 사용자 환경 (npm `pretendard`
// 또는 jsdelivr CDN). Remotion 환경에서 폰트 로드는 `delayRender` 로 대기 — 본 토큰은
// CSS family stack 만 정의하고, 실제 등록은 fonts 모듈 (별도) 에서 한다.
export const fontFamily =
  '"Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

// 한글 영상 본문 굵기 (Pretendard wght axis).
export const weight = {
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  extrabold: 800,
  black: 900,
} as const;

// 1.618 황금비 스케일 — body=18 기준.
// 14 → 18 → 28 → 46 → 76 → 124 (다음 단계는 제목용).
export const size = {
  meta: 14,       // 출처·각주
  caption: 18,    // 보조 텍스트
  body: 28,       // 본문 / 축 라벨
  title: 46,      // 차트 제목
  display: 76,    // 키 메시지
  hero: 124,      // 전체 풀-스크린 메시지 (Phase 5 한정)
} as const;

// 행간 — 한글은 영문보다 행간 크게 (1.45–1.55).
export const lineHeight = {
  tight: 1.2,
  normal: 1.35,
  relaxed: 1.5,
  loose: 1.65,
} as const;

// 자간 — 한글 본문은 0, kicker/배지는 +2–4.
export const letterSpacing = {
  tight: -0.5,
  normal: 0,
  wide: 2,
  wider: 4,
} as const;

// 한글 줄바꿈 안전 (모든 텍스트에 적용).
export const koreanTextStyle = {
  wordBreak: "keep-all" as const,
  overflowWrap: "anywhere" as const,
};

// 자막 표준 (Netflix Korean TTSG).
export const subtitle = {
  maxCharsPerLine: 16,
  maxLines: 2,
  cps: 17,
  cueSecMin: 5,
  cueSecMax: 7,
} as const;

// ────────────────────────────────────────────────────────────
// 3. Motion (Material easing)
// ────────────────────────────────────────────────────────────

// Remotion `interpolate` 는 함수 형태로 받는다 — 키워드 string ("ease-out" 등) 아님.
// 우리는 `cubic-bezier` 4 인자를 그대로 박아 결정론적 렌더.
export const easing = {
  // Material decelerate — 진입의 표준 (차트 draw, 라벨 fade-in).
  decelerate: [0.0, 0.0, 0.2, 1.0] as const,
  // Material standard — 강조·이동.
  standard: [0.4, 0.0, 0.2, 1.0] as const,
  // Material accelerate — 퇴장.
  accelerate: [0.4, 0.0, 1.0, 1.0] as const,
  // 선형 — 격자·축처럼 전환 없는 곳만.
  linear: [0, 0, 1, 1] as const,
} as const;

// CSS animation-timing 문자열 (필요 시).
export const easingCss = {
  decelerate: "cubic-bezier(0, 0, 0.2, 1)",
  standard: "cubic-bezier(0.4, 0, 0.2, 1)",
  accelerate: "cubic-bezier(0.4, 0, 1, 1)",
} as const;

// 진행 시간 (ms). Remotion 프레임 변환은 호출자 (fps 기반).
export const duration = {
  micro: 150,     // 라벨 페이드, 호버
  short: 300,     // 라인/바 draw
  medium: 400,    // 강조 모션, 축 등장
  long: 600,      // chart 진입
  xlong: 900,     // 전체 전환
} as const;

// Stagger interval (ms). N 시리즈일 때 사용. clamp(min(80, 600/N), 20, 120).
export const stagger = (n: number, max = 80, total = 600): number => {
  if (n <= 1) return 0;
  const candidate = Math.min(max, total / n);
  return Math.max(20, Math.min(120, candidate));
};

// ────────────────────────────────────────────────────────────
// 4. Spacing & Layout
// ────────────────────────────────────────────────────────────

// 8 grid (반·1·2·3·4·6·8·12·16 배수).
export const space = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 72,
} as const;

// 1080p 캔버스 안전 영역 (좌우 130px, 상하 60px — Briefing 과 정합).
export const safeArea = {
  top: 60,
  right: 130,
  bottom: 64,
  left: 130,
} as const;

// 차트 영역 표준 (ChartFrame 내부 — 1920 × 1080 중앙 비주얼 영역 기준).
export const chart = {
  width: 1360,
  height: 600,
  padTop: 56,    // title + kicker 슬롯
  padRight: 80,  // 끝점 라벨 여유
  padBottom: 64, // 축 + 출처
  padLeft: 96,   // y 축 라벨
} as const;

// 모서리 반경.
export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  pill: 999,
} as const;

// 보더 두께.
export const stroke = {
  hairline: 1,
  thin: 1.5,
  base: 2,
  thick: 3,
  bold: 4,
} as const;

// ────────────────────────────────────────────────────────────
// 5. Helpers — 토큰 단독으로 못 가는 미세 derivations.
// ────────────────────────────────────────────────────────────

// Remotion frame 환산: ms → frames (fps 의존, 호출자가 fps 주입).
export const msToFrames = (ms: number, fps: number): number =>
  Math.max(1, Math.round((ms / 1000) * fps));

// 시리즈 컬러 사이클 (N 개 시리즈 시 자동 분배).
export const seriesColor = (i: number): string => series[i % series.length];

// 의미 라벨 → 색 (없으면 secondary).
export const labelColor = (key: string | null | undefined): string => {
  switch (key) {
    case "<확인>":
      return label.verified;
    case "<추론>":
      return label.inferred;
    case "<주장>":
      return label.claimed;
    case "<미검증>":
    case "<반박됨>":
      return label.unverified;
    default:
      return text.secondary;
  }
};
