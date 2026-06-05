<!--
tier: 2
last_synced_with: v0.30.0
ssot_for: [professional-rebuild, charting-rebuild, visual-system-rebuild]
depends_on: [CLAUDE.md, GOAL.md, docs/07_VIDEO_STYLE_GUIDE.md, docs/10_RENDERING_PIPELINE_SPEC.md]
last_review: 2026-06-05
-->

# PROFESSIONAL_REBUILD_PLAN — 차팅·자막·타이포 영상미 전면 재빌드 계획

본 문서는 **v0.30.0 ~ v0.36.x** 사이클에 진행하는 차팅·자막·타이포의 **프로페셔널 수준 재빌드**의 단일
진실원(SSOT)이다. 외부 리서치(차트 애니메이션 / 한글 타이포 / 시각화 이론 / 다크 컬러 / 날리지식·Vox
미학) 5 트랙 통합 결과 + 현 코드 자기 평가 + Phase 0 → 5+E 실행 계획 + 합격 기준(MVP Professional
Bar 20)을 담는다. **상위 규칙은 CLAUDE.md (특히 C0 영상미) 와 GOAL.md (G0/G4)**.

---

## 0. 배경 (왜 재빌드인가)

v0.27.0 에서 21 차트 family 렌더러를 한 번에 박았고, v0.29.0 에서 Aurora Glass Card 스킨을 캡션·배지·
브랜드에 입혔다. 그러나 사용자 평가:

> "전반적으로 차팅의 기술이나 시각화 기술이 너무 구려. 전반적으로 너무 구려. 총체적으로 다시 재빌드,
> 리팩토링을 전면적으로 해야 할거 같아. 프로페셔널한 수준으로 그 레벨을 높일 수 있는 계획을 세워."

→ **수준 미달의 근본 원인 분석**:

1. **공용 골격 부재**: 차트마다 축·격자·라벨·플레이트가 ad-hoc 으로 그려져, 차트끼리·자막/지도/배지와의
   타이포·여백·색 일관성이 깨진다.
2. **모션 빈약**: 대부분 단일 `draw` 진행도 하나만 쓰고, 강조·맥락(annotation)·시선 유도(stagger,
   spotlight) 모션이 없다.
3. **한글 타이포 디테일 부재**: `word-break`, `keep-all`, line-height, 자간 등 한글 영상 기본기 미적용.
4. **색·대비 시스템 부재**: 다크 베이스가 `#0e1116` 단발이고 시맨틱 토큰이 없다. 색맹 안전성 미고려.
5. **레퍼런스 부재**: 날리지식·Vox·FT 의 시각문법(annotation pattern, time hierarchy) 미반영.

→ **재빌드의 본질**: 차트 재구현이 아니라, **디자인 시스템(토큰·공용 컴포넌트) → 차트 family →
모멘트(음성 싱크) → 자막/타이포 표준** 의 4 층 재배치.

---

## 1. Phase A — 외부 리서치 통합 결과

5 개 병렬 에이전트로 차트 애니메이션 / 한글 타이포 / 시각화 이론 / 다크 컬러 / 날리지식·Vox 미학을
조사했다. 결과를 본 시스템 적용 가능 형태로 정리한다.

### 1.1 모션·이징 (Material/Apple/Netflix 기반)

| 항목 | 결정값 | 근거 |
|---|---|---|
| 기본 이징 | `cubic-bezier(0, 0, 0.2, 1)` (Material decelerate) | 데이터 시각화 진입 표준 |
| 강조 이징 | `cubic-bezier(0.4, 0, 0.2, 1)` (standard) | 강조 모션·콜아웃 |
| 짧은 진행 | 150–200ms | 라벨 페이드, 호버 |
| 표준 진행 | 300–400ms | 라인/바 draw, 축 등장 |
| 긴 진행 | 600–900ms | Chart 진입·전환 |
| Stagger | `clamp(min(80ms, 600/N))` | N 개 시리즈/카테고리 |
| 진입 패턴 | Subject → Note → Connector (D3-annotation) | 데이터 → 맥락 → 연결 순 |
| Spotlight | dim background 50–60%, highlight 100% | 음성 싱크 모멘트 강조 |

### 1.2 한글 타이포 (Netflix Korean / Pretendard / NAVER)

| 항목 | 결정값 | 근거 |
|---|---|---|
| 본문 폰트 | Pretendard Variable (45–920 wght axis) | 화면용 한글 가변폰트 표준 |
| 자막 1 줄 폭 | 16 자 (한글 기준) | Netflix Korean TTSG |
| 자막 최대 줄수 | 2 줄 | TTSG 동일 |
| CPS | ≤ 17 | TTSG 동일 |
| Cue 노출 | 5–7 sec | TTSG 동일 |
| word-break | `keep-all` | 한글은 단어 단위 줄바꿈 |
| overflow-wrap | `anywhere` | keep-all 의 안전 fallback |
| line-height | 1.45–1.55 | 한글은 영문보다 큰 행간 |
| 자간 (letter-spacing) | 본문 0, kicker/배지 +2–4 | 한글은 자간 0 이 표준 |
| 자막 폰트 굵기 | 600 (semibold) | 1080p 다크 위 가독 |
| 제목 폰트 굵기 | 800–900 | OSINT 키 메시지 |

### 1.3 시각화 이론 (Cleveland-McGill / FT Visual Vocabulary)

| 항목 | 결정값 | 근거 |
|---|---|---|
| 인지 정확도 우선 채널 | position > length > angle > area > color | Cleveland-McGill |
| 비교 차트 디폴트 | bar (length) | Donut 은 카테고리 ≤ 4 일 때만 |
| 시계열 디폴트 | line / area | x=시간 위계 우선 |
| 부분-전체 | stacked_area (시계열) / stacked_bar | Donut 은 보조 |
| 분포 | scatter / bubble | Encoding ≤ 3 |
| 흐름 | sankey / waterfall | sankey 는 노드 ≤ 12 |
| Annotation 패턴 | Subject + Note + Connector | d3-annotation 표준 |
| Reference shading | 회색 25% 알파 영역 + 라벨 | 위기/구간 표시 |
| Direct labeling | 끝점·peak 에 값 + 라벨 | 범례 의존 최소화 |
| Label collision | labella.js (1D) / 수동 stagger | 끝점 라벨 회피 |

### 1.4 다크 컬러·대비 (Material Dark / WCAG)

| 항목 | 결정값 | 근거 |
|---|---|---|
| 베이스 | `#121214` (Material Dark 권장) | `#000000` 은 OLED 잔상·대비 과함 |
| 표면 1 | `#1a1d22` | 카드/플레이트 |
| 표면 2 | `#22262d` | hover/raised |
| 텍스트 primary | `#f5f7fa` (대비 14.5:1 on base) | WCAG AAA |
| 텍스트 secondary | `rgba(245,247,250,0.72)` | 부제·축 라벨 |
| 텍스트 tertiary | `rgba(245,247,250,0.48)` | 출처·메타 |
| Grid | `rgba(245,247,250,0.08)` | 정보 보조 |
| 시리즈 컬러 (색맹 안전) | Okabe-Ito 8 색 | 색맹 안전 + 다크 가독 |
| 의미 컬러 (확인/추론/주장/미검증) | `#5cb85c`/`#5bc0de`/`#f0ad4e`/`#d9534f` | 기존 라벨 시스템 유지 |
| 자막 대비 | ≥ 7:1 (AAA) | 1080p 다크 위 |

**Okabe-Ito 팔레트** (`#000000` 제외 7 색 + 우리 base):
- `#56B4E9` 스카이블루 (1차 시리즈)
- `#E69F00` 오렌지 (2차 시리즈)
- `#009E73` 청록 (3차)
- `#F0E442` 옐로우 (4차)
- `#0072B2` 딥블루 (5차)
- `#D55E00` 다크오렌지 (6차)
- `#CC79A7` 핑크 (7차)

### 1.5 날리지식 / Vox / OSINT Twitter 미학

날리지식 채널(YouTube `FaOqn3-YdkI`, `ucl9RED4Ye4`, **YTN 세계는 날리지가 아님**)의 비주얼 문법:

| 요소 | 패턴 |
|---|---|
| 화면 분할 | 좌측 핵심 한 줄 + 우측 비주얼(지도/차트) — 또는 풀 비주얼 + 하단 자막 |
| 키 메시지 | 굵은 한글 800 wght, 70–96pt, 줄당 12–16 자 |
| 자막 | 화면 하단 1/4, 글래스 플레이트, 굵기 600 |
| 지도 | 단색 베이스 + 강조 영역만 색, 핀·아크로 연결 |
| 차트 | 끝점 값 + 직접 라벨, 격자 최소, 음성에 맞춰 등장 stagger |
| 모션 | 카메라 줌(spotlight), draw progression, 데이터 → 맥락 순서 |
| 색 | 다크 베이스 + 1 차 강조색 1 개 + 보조 1–2 개 (Vox earth studio 동일) |

→ **본 시스템의 의역**: Aurora Glass Card(있음) + Pretendard + Okabe-Ito + Material easing +
Subject+Note+Connector annotation + time-wipe stagger.

---

## 2. Phase B — 현 코드 자기 평가

### 2.1 점수표 (10 점 만점)

| 영역 | 현재 | 목표 | 갭 |
|---|---|---|---|
| 디자인 시스템 (토큰·공용 컴포넌트) | 2 | 9 | -7 (없음) |
| 한글 타이포 | 3 | 9 | -6 (`word-break` 등 누락) |
| 다크 컬러·대비 | 4 | 9 | -5 (Material Dark + Okabe-Ito 미적용) |
| 차트 모션 (이징·stagger·spotlight) | 3 | 9 | -6 (단순 draw 만) |
| Annotation (Subject+Note+Connector) | 1 | 9 | -8 (없음) |
| Direct labeling / 끝점 값 | 2 | 8 | -6 |
| Reference shading / 위기 영역 | 0 | 7 | -7 |
| Specialty (network/sankey/choropleth) | 3 | 7 | -4 (force/sankey lib 미사용) |
| 자막 표준 (Netflix Korean) | 4 | 9 | -5 |
| 음성 싱크 모멘트 | 3 | 8 | -5 (alignment 큐만, spotlight 없음) |

**평균 갭 -5.9** — 5+1 Phase 로 단계적으로 해소한다.

### 2.2 우선 청산 부채 (Phase 0 에서 처리)

1. 토큰 모듈 부재 → `remotion/src/design.ts` 신설
2. Pretendard 미로딩 → CDN 로딩
3. ChartFrame 부재 → 공용 골격 신설
4. Axis 헬퍼 부재 → tick·grid 표준화
5. Callout 패턴 부재 → Subject+Note+Connector 컴포넌트
6. ReferenceRegion 부재 → 회색 알파 영역 + 라벨

---

## 3. Phase C — 실행 계획 (Phase 0 → 5+E)

각 Phase 는 **하나의 MINOR 버전**으로 매핑. Phase 0 = v0.30.0, Phase 1 = v0.31.0 … Phase E = v0.36.0.

### Phase 0 — 디자인 시스템 토대 (v0.30.0) [본 PATCH]

**목표**: 차트 변경은 한 줄도 안 한다. 토큰·공용 컴포넌트만 박는다.

- [x] `docs/PROFESSIONAL_REBUILD_PLAN.md` (본 문서)
- [x] `remotion/src/design.ts` — typography scale (1.618 황금비), color tokens (Material Dark +
  Okabe-Ito + 의미 컬러), easing (Material decelerate/standard), durations (150/300/600/900ms),
  spacing scale, font config
- [x] Pretendard Variable 로딩 (`@cdnfonts/pretendard` 또는 jsdelivr CDN)
- [x] `remotion/src/components/ChartFrame.tsx` — kicker / title / subtitle / source 슬롯 골격
- [x] `remotion/src/components/Axis.tsx` — x/y 축 + grid + tick 라벨 (Pretendard, 보조 컬러)
- [x] `remotion/src/components/Callout.tsx` — Subject + Note + Connector + leader line
- [x] `remotion/src/components/ReferenceRegion.tsx` — 회색 알파 영역 + 라벨
- [x] npm: `d3-scale, d3-shape, d3-time-format, d3-array, d3-scale-chromatic, labella`
- [x] 단위 테스트 회귀 (기존 통과 유지)

**비-목표 (다음 Phase 로 이관)**: 차트 family 본체 교체, annotation 실제 사용, network/sankey
재작성.

### Phase 1 — XY family 정통 재구현 (v0.31.0) [완료]

- [x] line / area / stacked_area / small_multiples / dual_line / forecast
- [x] d3-scale (time + linear) + d3-shape `line()` / `area()` + `curveMonotoneX`
- [x] 시간 위계 축 (year / month / day 자동) — d3-time-format
- [x] Direct labeling (끝점 값 + 시리즈명) + 1D 라벨 충돌 회피(자체 구현, 결정론)
- [x] Subject+Note+Connector 콜아웃 (XY 의 `event` 필드 자동)
- [x] ReferenceRegion (위기/전망 구간 음영) — XY 옵션 + Forecast 전망 구간 자동
- [x] Draw progression: clipPath x-wipe + Material decelerate
- [x] Stagger 헬퍼 (`charts/util.ts` 의 `useSeriesProgress`, stacked_area 후속 적용 예정)

### Phase 2 — Bar/Point family (v0.32.0)

- bar / lollipop / range_bar / stacked_bar / waterfall / scatter / bubble / slope / candle
- Waterfall: connector 선 + +/- 색 + 누적값 라벨
- Bubble: quadrant label + Okabe-Ito 카테고리 색
- Lollipop: stem grow + head pop
- Label collision: labella 1D 사용
- Stagger: 카테고리 순/값 정렬 순 등장

### Phase 3 — Specialty 정통 (v0.33.0)

- network: 헤드리스 force layout (사전 시뮬레이션, degree 큰 노드부터 등장)
- sankey: d3-sankey 실 사용
- gantt: time-wipe stagger + 마일스톤 별 표시
- choropleth: world-atlas + ISO 매핑 + sequential 색 스케일
- donut: 카테고리 ≤ 4 일 때만, 외부 라벨 + 값 + 백분율
- heatmap: 셀 등장 stagger (행 → 열)

### Phase 4 — 모멘트 (음성 싱크 강조) (v0.34.0)

- subtitle_align 백엔드 결과를 이용해 cue 시작 시점에 차트의 특정 요소를 spotlight
- spotlight = 배경 dim 50–60% + 강조 요소 100% + Callout 등장
- 모멘트 큐 메타데이터 형식 정의 (`SubtitleCue.spotlight?: { kind, target }`)
- 모멘트 누락 시 그냥 cue 만 페이드 (현재 동작 유지)

### Phase 5 — 자막·타이포·플레이트 표준 (v0.35.0)

- Netflix Korean 자막 규격 적용 (16 자/줄, 2 줄, 17 CPS, 5–7 sec)
- 자막 자동 줄바꿈: 16 자 + `keep-all` + 단어 단위
- Pretendard wght axis 가변 사용 (제목 800, 자막 600, 메타 400)
- AuroraGlassCard 토큰화 (design.ts 의 radii / glow 강도)
- 모든 텍스트에 `word-break: keep-all; overflow-wrap: anywhere;` 적용

### Phase E — 최종 mp4 렌더 + 사용자 검수 (v0.36.0)

- Hormuz 번들 ~30 sec 클립 (line + map + subtitles + alignment 큐)
- 사용자 머신 (Windows) 에서 실제 음성으로 풀 렌더 → SendUserFile / 다운로드 제공
- 사용자 평가표 5 영역 (영상, 타이포 애니, 자막, 폰트 세련도, 정보 전달) 첨부
- 사용자 피드백 → 다음 사이클 (v0.37+)

---

## 4. MVP Professional Bar — 합격 기준 20

본 사이클 종료 시 (v0.36.0) 아래 20 항목을 **모두** 통과해야 한다.

### 디자인 시스템
1. [ ] 모든 차트가 `design.ts` 토큰만 사용 (하드코딩 색·폰트 0)
2. [ ] Pretendard Variable 적용 (제목·자막·축·메타 모두)
3. [ ] Material Dark 베이스 + Okabe-Ito 시리즈 컬러

### 한글 타이포
4. [ ] 자막 16 자/줄, 2 줄 max, 17 CPS
5. [ ] `word-break: keep-all` + `overflow-wrap: anywhere` 모든 텍스트
6. [ ] 자막 대비 ≥ 7:1 (WCAG AAA)

### 차트 모션
7. [ ] Material easing (decelerate/standard) 만 사용 (선형 0)
8. [ ] Stagger 적용 (다중 시리즈/카테고리)
9. [ ] Draw progression (line wipe / bar grow / 끝점 카운트업)

### Annotation
10. [ ] Subject+Note+Connector 패턴 모든 차트 family 에 사용 가능
11. [ ] Direct labeling (끝점 + 시리즈명, 범례 의존 최소)
12. [ ] ReferenceRegion (위기/구간 음영) 동작

### Specialty
13. [ ] network: 헤드리스 force, degree 순 등장
14. [ ] sankey: d3-sankey 실 사용
15. [ ] choropleth: world-atlas + ISO + sequential 스케일

### 음성 싱크
16. [ ] 큐 시작 시 spotlight 모멘트 (옵션) 동작

### 자막
17. [ ] Aurora Glass Card 자막 플레이트 토큰화 + 인용 강조색 분기

### 정확성·검증 (C0 경계)
18. [ ] 라벨 시스템 (확인/추론/주장/미검증) 기존 컬러·동작 유지
19. [ ] 출처 표기 / `sourceLinkRequired` 동작 유지

### 사용자 검수
20. [ ] 최종 mp4 클립 (~30 sec) 사용자 전달 + 5 영역 평가 수령

---

## 5. 의존성 (npm 추가분)

```
d3-scale       ^4.0
d3-shape       ^3.2
d3-time-format ^4.1
d3-array       ^3.2
d3-scale-chromatic ^3.0
labella        ^1.1
```

`d3-axis` 는 SVG 직접 그리는 우리 구조엔 과한 의존이라 제외 — `Axis.tsx` 가 직접 grid·tick·라벨을
그린다.

Pretendard 는 npm 패키지 (`pretendard` ^1.3) 또는 jsdelivr CDN 둘 다 가능. **Remotion 환경에서는
CDN 보다 npm 패키지가 결정론적 렌더에 유리**해 npm 권장. 다만 본 클라우드에선 npm 설치만 하고
실제 폰트 fetch 는 사용자 머신에서. 폴백 폰트 스택은 `Pretendard, -apple-system, BlinkMacSystemFont,
"Segoe UI", Roboto, sans-serif`.

---

## 6. 비-목표 (본 사이클에서 안 한다)

- 새로운 차트 family 추가 (현 21 종 유지)
- agents_reviewer 계약 변경 (v1 유지)
- TUI / 인테이크 페이지 변경
- 백엔드 (LLM/TTS/alignment) 교체

---

## 7. 위험·완화

| 위험 | 완화 |
|---|---|
| Pretendard 실제 폰트 fetch 안 되면 렌더 깨짐 | 폴백 스택 + Remotion `delayRender` 로 폰트 로드 대기 |
| d3-shape generator 결과가 너무 매끄러워 데이터 표현 왜곡 | 기본 `curveLinear` 유지, 사용자 의도 시만 monotone |
| Annotation 너무 많아 화면이 시끄러움 | 한 화면당 max 2 annotation 룰 |
| stagger 가 음성 cue 와 어긋나 산만함 | Phase 4 spotlight 큐와 sync 우선 |
| Okabe-Ito 색이 의미 라벨 색과 충돌 | 시리즈 컬러는 차트 본체, 의미 컬러는 라벨 배지로 분리 |

---

## 8. 트래킹

본 문서의 체크박스 (`- [ ]`) 는 Phase 가 끝날 때마다 갱신한다. v0.36.0 종료 시 본 문서를
`docs/ANTIPATTERNS/RENDER_ANTIPATTERNS.md` 에 흡수 회고(없으면 신설) + DEVLOG 한 줄 요약 + HANDOFF
의 차트 항목 제거.
