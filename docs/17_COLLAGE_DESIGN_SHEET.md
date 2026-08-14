<!--
tier: 2
last_synced_with: v0.44.1
ssot_for: [collage-design-sheet, shorts-design-tokens, collage-components, shorts-scene-templates]
depends_on: [07_VIDEO_STYLE_GUIDE.md, SHORTS_COLLAGE_OVERHAUL_PLAN.md, ../schemas/models.py]
last_review: 2026-08-14
-->

# 17 — Collage Design Sheet (쇼츠 콜라주 디자인 시트)

본 문서는 쇼츠 콜라주 컴포지션(`hyperframes/shorts/`)의 **디자인 시트 3계층(L1 토큰 / L2
컴포넌트 / L3 씬 템플릿)의 SSOT** 다. 직렬화 형식은 `schemas/models.py:DesignSheet` — 씬
조립기는 하드코딩 대신 시트 JSON 을 읽는다("시트가 곧 골격"). 상위 미학 원칙과 벤치마크는
[SHORTS_COLLAGE_OVERHAUL_PLAN.md](SHORTS_COLLAGE_OVERHAUL_PLAN.md) §1, 스타일 규범은
[07_VIDEO_STYLE_GUIDE.md](07_VIDEO_STYLE_GUIDE.md).

합격선: **§1.0 최소 기준(원카AI SK하이닉스 샘플 0:35~1:16) 동급** — 종이 질감이 살아있고,
컷아웃이 물성 있게 움직이며, 검증 라벨이 스탬프로 명확히 구분되는 화면.

> **대원칙 — 시트는 문법이지 조판이 아니다** (사용자 지시, 계획 §6.0): 본 시트는 어휘·재료·
> 위계를 고정할 뿐, 화면 조판을 고정하지 않는다. 모든 L2 컴포넌트는 **표현 변형 2~4종**을
> 갖고, 배경 문법·구도·조합은 영상마다 V1(시드)·V2(콘텐츠 규칙)·V3(아트 디렉터) 변주로
> 달라진다. 씬 조립기가 본 시트를 "그대로 찍어내는" 구현은 리뷰에서 반려 대상이다.

---

## 1. L1 — 토큰 (sheet_id: `shorts_collage_v1`)

### 1.1 캔버스·Safe Area

| 토큰 | 값 | 근거 |
|---|---|---|
| canvas | **1080×1920 @ 30fps** | 쇼츠·릴스·틱톡 공용 마스터 |
| safe_top | 220px | 쇼츠 검색/릴스 상단 UI |
| safe_bottom | 350px | 3사 캡션·액션 UI |
| safe_right | 140px | **틱톡·릴스 우측 액션 레일** |
| safe_left | 60px | 여백 균형 |
| content_zone | x:60~940, y:220~1570 | 핵심 텍스트·라벨은 반드시 이 안 |

### 1.2 종이 팔레트 (palette)

콜라주는 **라이트 종이 기조**가 기본이다 (다크 잉크는 롱폼 briefing 의 정체성으로 동결).

| 키 | 값 | 용도 |
|---|---|---|
| `paper_base` | `#E8DFC9` | 기본 크라프트지 배경 |
| `paper_aged` | `#D9CBAA` | 낡은 종이 (과거 씬·아카이브) |
| `paper_file` | `#C9BC9C` | 서류 파일/폴더 표면 |
| `ink` | `#1C1A17` | 본문 잉크·판화 선 |
| `ink_soft` | `#4A443B` | 보조 텍스트 |
| `sunburst_a` / `sunburst_b` | `#E4B33C` / `#3E6E8E` | 선버스트 방사 (노랑/청) — 카테고리 액센트로 교체 가능 |
| `tape` | `#D8D2BFcc` | 반투명 테이프 |
| `string_red` | `#B03A2E` | 붉은 실 관계선·형광펜 |
| `stamp_confirm` | `#1C1A17` | `<확인>` 스탬프 (검정) |
| `stamp_inferred` | `#C9A227` | `<추론>` 스탬프 (노랑) |
| `stamp_unverified` | `#A63428` | `<미검증>` 스탬프 (빨강) |
| `stamp_refuted` | `#6E6A61` | `<반박됨>` 스탬프 (회색, 빨강 사선) |

검증 라벨 4종의 **의미·색 구분은 07 §6 을 승계** — 표면 처리(고무도장 질감)만 콜라주화.
카테고리 액센트(지정학/전쟁/경제/재난/정보전)는 07 §4 색 체계를 선버스트·스탬프 보조색에 매핑.

### 1.3 타이포 (typography)

| 키 | 값 | 용도 |
|---|---|---|
| `subtitle` | Pretendard **ExtraBold 68px**, 흰색+검정 4px 외곽선, keep-all | 하단 대형 자막 (모바일 가독) |
| `ransom_headline` | 혼합 활자 **96~140px** (씬당 1줄, 6어절 이내) | 랜섬노트 헤드라인 — **헤드라인·강조어 한정** (본문 금지) |
| `name_tag` | Noto Serif KR Bold 44px | 인물 이름·직함 태그 |
| `kicker` | Pretendard SemiBold 36px, letter-spacing 0.06em | 씬 키커 |
| `credit` | Pretendard Regular 26px | 출처·사진 크레딧 (우하단) |

랜섬노트 활자 소스: 시스템 내 폰트 4~6종(Pretendard 웨이트 변형 + Noto Serif KR + 자체 스탬프체)
을 글자 단위로 랜덤 조합하되 **시드 = 문자열 해시** (결정론 — `Math.random` 금지).

### 1.4 모션 (motion) — 이원 체계

| 키 | 값 | 용도 |
|---|---|---|
| `place_duration` | 0.22s | 컷아웃 "탁" 놓기 (위 1.06배 → 1.0 착지 + 그림자 수축) |
| `step_fps` | 10 | 물성 요소 SteppedEase 스텝/초 |
| `jitter_deg` | 0.3 | 정지 컷아웃 미세 회전 노이즈 (인덱스 시드) |
| `push_in_scale` | 1.0→1.08 | 씬 내 슬로 푸시인 |
| `draw_on` | getTotalLength 패턴 | 판화 선·붉은 실·형광펜 (RENDER-AP: v0.34.2 학습 준수) |
| `paper_breath` | feTurbulence scale 3, 8s 주기 | 종이 숨쉬기 (seed 고정) |
| `grain_loop` | 노이즈 프레임 4장 12fps 순환 | 필름 그레인 (자체 생성) |
| 정보 요소 이징 | Material decelerate `cubic-bezier(0,0,0.2,1)` | 차트·라벨 (PROFESSIONAL_REBUILD_PLAN §1.1 승계) |

**섞지 않는다**: 물성 요소(컷아웃·소품·종이) = 스텝/바운스, 정보 요소(차트·라벨·자막) = Material.

---

### 1.5 변주 파라미터 (V1 시드)

`seed = fnv1a(report_id)` 에서 파생 (결정론 — 같은 번들이면 항상 같은 값):

| 파라미터 | 범위 | 대상 |
|---|---|---|
| `paper_tone` | paper_base / paper_aged / paper_file | 영상 기조 종이 톤 |
| `sunburst_rotation` | 0~360° | 선버스트 초기 각도 |
| `cutout_tilt` | ±4° (요소별 서브시드) | 컷아웃 기울기 |
| `tape_layout` | 4 변형 | 테이프·핀 배치 패턴 |
| `ransom_seed` | 문자열 해시 | 랜섬 글자별 활자 조합 |

### 1.6 배경 문법 후보군 (V2 규칙 변주의 재료)

`sunburst` / `stage_curtain`(무대) / `file_desk`(서류 책상) / `paper_map` / `montage_wall`
(사진 벽) / `plain_grain`(정적 종이 — 절제 씬용). 선택 규칙: 카테고리별 후보 2~4종 중
콘텐츠 조건(인물 수·차트 유무)으로 압축 → 동일 문법 연속 2씬 금지 → 최근 N편 HOOK 이력
(`projects/style_history.json`)과 중복 회피.

## 2. L2 — 컴포넌트 시트 (10종)

각 컴포넌트는 `hyperframes/shorts/assets/collage_kit.js` 에 구현될 예정(Phase 3). 여기서는
계약(입력·상태·모션·금지사항)만 확정한다. **각 컴포넌트는 표현 변형(variant) 2~4종을
갖는다** — 예: StampLabel 의 각도·마모도, PhotoMontageGrid 의 격자/스택/부채꼴, CutoutActor
의 등장 방향. 변형 선택은 V1~V3 변주 층의 몫이며 컴포넌트는 variant 인자로 받기만 한다.

| # | 컴포넌트 | 입력 | 모션 | 금지사항 |
|---|---|---|---|---|
| 1 | `CutoutActor` | LibraryPerson variant, 위치, 스케일 | place → jitter, 퇴장은 슬라이드+페이드 | 즉석 생성 이미지 금지 — 라이브러리 자산만 |
| 2 | `EngravedPortrait` | stipple/engraving SVG | 선 draw-on 1.2s → 정지 | 컬러 필터 금지 (흑백 정체성) |
| 3 | `RansomHeadline` | 문자열, emphasis 어절 | 글자 단위 stagger place (40ms) | 본문 자막에 사용 금지, 씬당 1줄 |
| 4 | `StampLabel` | 라벨 enum (확인/추론/미검증/반박됨) | 도장 "쾅" (1.3→1.0 + 5° 기울기) | 색·문구 변형 금지 (G4 — 07 §6) |
| 5 | `PaperPanel` | 자식 콘텐츠, 종이 톤 | place + paper_breath | AI-dashboard 글로우 금지 |
| 6 | `TapeStrip` / 핀·클립 | 각도, 길이 | PaperPanel 등장에 종속 | 남발 금지 (씬당 ≤3) |
| 7 | `PhotoMontageGrid` | BundleImage[] (cleared+credit만) | 순차 "찍기" 등장 120ms 간격 | credit 미표기 사진 금지 (IMAGE_BUNDLE_CONTRACT §3.1-a) |
| 8 | `StringConnector` | 노드 2개, 라벨 | 붉은 실 draw-on | 관계 근거 없는 연결 금지 (G4) |
| 9 | `SunburstStage` / 커튼 무대 | 액센트 색, 중앙 슬롯 | 방사 슬로 회전 / 커튼 스웨이 + 스포트라이트 | — |
| 10 | `ChartPlate` | 기존 SceneKit 차트 빌더 산출 | 종이 플레이트 위 얹기 | 차트 내부 문법 변경 금지 (기존 재사용) |

## 3. L3 — 씬 템플릿 (120초 기준)

| 씬 | 시간 | 필수 컴포넌트 | 데이터 바인딩 (번들) |
|---|---|---|---|
| HOOK | 0–3s | RansomHeadline + CutoutActor 1 | `report.video.intro_narration[0]` + headline |
| CONTEXT | 3–15s | SunburstStage 또는 PaperMap + 자막 | intro 잔여 + 최상위 섹션 도입 |
| ACTORS | 15–30s | EngravedPortrait + name_tag + StringConnector | 엔티티 매칭 결과 (§3.4) |
| EVIDENCE | 30–85s | ChartPlate / PhotoMontageGrid / StampLabel | 상위 2개 섹션 `video.narration` + charts |
| TURN | 85–110s | StampLabel(추론/미검증) + RansomHeadline | 반전 섹션 + `emphasis` |
| CLOSING | 110–120s | 채널 스탬프 + credit | `report.video.outro_narration` + BGM 크레딧 |

## 4. 스페시먼

`hyperframes/shorts/specimen.html` (Phase 3) — 전 토큰·컴포넌트·씬 템플릿을 safe area
오버레이 가이드와 함께 한 페이지에 렌더. 디자인 검수는 mp4 렌더 전에 브라우저에서 반복한다.

## 이력

- 2026-08-14 v0.44.0: 최초 작성 (Phase 0 산출).
- 2026-08-14 v0.44.1: 대원칙 "시트는 문법이지 조판이 아니다" + §1.5 시드 변주 + §1.6 배경
  문법 후보군 + 컴포넌트 변형 2~4종 요구 (사용자 지시 — 기계적 반복 금지).
