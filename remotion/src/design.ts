// design.ts — 편집 dashboard 인포그래픽 디자인 시스템 (v0.33.0).
//
// 사용자 9장 레퍼런스 (orange-accent dashboard infographic + Japan tourism style) 기반:
//   - 밝은 크림 배경, 흰 라운드 카드 + soft shadow (Aurora glass 폐기)
//   - 굵은 산세리프 단일계, 거대 숫자 hero
//   - 오렌지 단일 accent + 4-5색 보조 (Okabe-Ito 8색 폐기)
//   - 모션 절제: slow fade + draw-on, no glow/neon/pop

// ────────────────────────────────────────────────────────────
// 1. Color — 편집 dashboard 팔레트
// ────────────────────────────────────────────────────────────

// 페이지 배경 — 따뜻한 크림 (white 도 #fafaf7 도 검토 후 cream 채택; Japan infographic 톤).
export const surface = {
  page: "#f5f1ea",        // 페이지 베이스 (따뜻한 크림)
  card: "#ffffff",        // 카드 (순백 — soft shadow 위)
  cardAlt: "#fdfbf7",     // 보조 카드 (약간 톤다운)
  divider: "rgba(26,26,26,0.08)",
} as const;

// 텍스트 — 다크 near-black + 알파.
export const text = {
  primary: "#1a1a1a",     // 헤드라인·본문
  secondary: "rgba(26,26,26,0.6)",  // 보조·부제
  tertiary: "rgba(26,26,26,0.42)",  // 출처·메타
  onAccent: "#ffffff",    // 액센트 위 흰 글씨
} as const;

// 메인 액센트 — 오렌지 (9장 레퍼런스 압도적 표준).
export const accent = {
  primary: "#e84a2d",     // 메인 오렌지·레드
  primaryDark: "#c8442a", // 호버·강조
  primarySoft: "#fce4dc", // 옅은 톤 (배경·hover)
} as const;

// 시리즈 팔레트 — 5색 편집 인포그래픽 (circle infographic 레퍼런스 정확 매핑).
// Sequential / categorical 둘 다 본 5색을 순서대로.
export const series = [
  "#e84a2d", // 1차 — 오렌지 (스토리의 주인공)
  "#1f3b6b", // 2차 — 네이비 (대비)
  "#a08bc4", // 3차 — 라벤더
  "#e5719a", // 4차 — 핑크 코랄
  "#f5a623", // 5차 — 앰버
] as const;

// 시리즈 강조 vs 비강조 — 단일 데이터 시리즈만 강조하고 나머진 회색으로 push back.
export const muted = {
  series: "#d4d0c8",      // 비강조 시리즈 색 (warm gray)
  bar: "#e8e5dc",         // 비강조 막대
  line: "#c8c4ba",        // 비강조 라인
} as const;

// 의미 / 검증 라벨 — 기존 유지 (G4 검증 시스템).
export const label = {
  verified: "#3a7d3a",    // <확인> — 영상미에 맞춰 톤다운된 녹
  inferred: "#2e6da4",    // <추론> — 톤다운된 블루
  claimed: "#e09c33",     // <주장> — 앰버
  unverified: "#c8442a",  // <미검증> — 차분한 레드
} as const;

// Grid / axis — 매우 옅게.
export const grid = {
  base: "rgba(26,26,26,0.06)",   // 차트 그리드 라인
  axis: "rgba(26,26,26,0.2)",    // 축선
} as const;

// 그림자 — 카드 부유감 (절제: 1단계만).
export const shadow = {
  card: "0 2px 16px rgba(26,26,26,0.06), 0 1px 3px rgba(26,26,26,0.04)",
  cardHover: "0 6px 28px rgba(26,26,26,0.10)",
} as const;

// ────────────────────────────────────────────────────────────
// 2. Typography — Pretendard 단일계, 굵은 display 위주
// ────────────────────────────────────────────────────────────

// fonts.ts 가 @remotion/fonts 로 woff2 등록. 여기는 family stack 만.
export const fontFamily =
  '"Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export const weight = {
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  extrabold: 800,
  black: 900,
} as const;

// Size scale — 거대 숫자 hero 가 핵심. 큰 단계 (hero / display) 확대.
export const size = {
  meta: 16,        // 출처·각주
  caption: 20,     // 보조·라벨
  body: 28,        // 본문·축 라벨
  subtitle: 36,    // 부제
  title: 56,       // 차트 제목
  display: 96,     // 차트 안의 큰 숫자
  hero: 180,       // 풀 스크린 키 숫자 ($750K 같은)
} as const;

export const lineHeight = {
  tight: 1.05,     // 거대 숫자
  display: 1.15,   // 헤드라인
  normal: 1.35,
  relaxed: 1.5,    // 본문
  loose: 1.65,
} as const;

export const letterSpacing = {
  tightest: -2,    // 거대 숫자 (display) 자간 조이기
  tighter: -1,
  tight: -0.3,
  normal: 0,
  wide: 1,
  wider: 2,
  caps: 3,         // 소문자 caps 강조 (kicker)
} as const;

// 한글 줄바꿈 안전 — 모든 텍스트에 spread.
export const koreanTextStyle = {
  wordBreak: "keep-all" as const,
  overflowWrap: "anywhere" as const,
};

// 자막 표준 (Netflix Korean TTSG, 유지).
export const subtitle = {
  maxCharsPerLine: 16,
  maxLines: 2,
  cps: 17,
  cueSecMin: 5,
  cueSecMax: 7,
} as const;

// ────────────────────────────────────────────────────────────
// 3. Motion — Material decelerate 만. 글로우/팝/스프링 폐기.
// ────────────────────────────────────────────────────────────

export const easing = {
  decelerate: [0.0, 0.0, 0.2, 1.0] as const, // 진입 표준
  standard: [0.4, 0.0, 0.2, 1.0] as const,   // 강조·이동
  accelerate: [0.4, 0.0, 1.0, 1.0] as const, // 퇴장
  linear: [0, 0, 1, 1] as const,
} as const;

export const easingCss = {
  decelerate: "cubic-bezier(0, 0, 0.2, 1)",
  standard: "cubic-bezier(0.4, 0, 0.2, 1)",
  accelerate: "cubic-bezier(0.4, 0, 1, 1)",
} as const;

export const duration = {
  micro: 150,
  short: 300,
  medium: 500,
  long: 800,
  xlong: 1200,
} as const;

// Stagger — 한 element 씩, 80~150ms (Vox / NYT 편집 기준).
export const stagger = (n: number, max = 100, total = 600): number => {
  if (n <= 1) return 0;
  const candidate = Math.min(max, total / n);
  return Math.max(50, Math.min(150, candidate));
};

// ────────────────────────────────────────────────────────────
// 4. Spacing & Layout — 넉넉한 여백, 큰 카드.
// ────────────────────────────────────────────────────────────

export const space = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 36,
  xxl: 56,
  xxxl: 80,
} as const;

export const safeArea = {
  top: 90,
  right: 130,
  bottom: 90,
  left: 130,
} as const;

export const chart = {
  width: 1360,
  height: 600,
  padTop: 64,
  padRight: 180,   // v0.33.1 — 끝점 직접 라벨 ("사우디 8.1 mb/d") 잘림 픽스.
  padBottom: 72,
  padLeft: 96,
} as const;

export const radius = {
  sm: 8,
  md: 14,
  lg: 22,     // 카드 — 9장 레퍼런스 곡률 (Inclety circle infographic 톤)
  xl: 32,
  pill: 999,
} as const;

export const stroke = {
  hairline: 1,
  thin: 1.5,
  base: 2,
  thick: 3,
  bold: 4,
} as const;

// ────────────────────────────────────────────────────────────
// 5. Helpers
// ────────────────────────────────────────────────────────────

export const msToFrames = (ms: number, fps: number): number =>
  Math.max(1, Math.round((ms / 1000) * fps));

// 시리즈 컬러 사이클 — 5색 순환.
export const seriesColor = (i: number): string => series[i % series.length];

// 의미 라벨 → 색.
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
