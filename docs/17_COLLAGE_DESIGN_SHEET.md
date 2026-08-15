<!--
tier: 2
last_synced_with: v1.0.6
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

## 0. L0 — 명명 규약 (사용자 지시 2026-08-15 — "재활용 가능하게 정규화")

시트는 **한 번 쓰고 버리는 조판이 아니라 재사용되는 어휘집**이다. 시트가 늘어나고(다른 미학·
다른 포맷) 자산이 누적될수록, 이름이 규칙 없이 붙으면 재활용 시점에 전수 개명이 필요해진다.
본 절은 **시트 자체의 이름과 시트에 들어가는 모든 항목의 이름**을 규정한다.

규약 위반은 `schemas/models.py:DesignSheet` 의 validator 가 차단한다 — 문서와 코드가 갈라지지
않도록 **기계 검증이 SSOT 의 집행자**다.

### 0.1 시트 ID

```
{format}_{concept}_v{gen}
```

| 자리 | 규칙 | 예 |
|---|---|---|
| `format` | `shorts` \| `briefing` — `DesignSheet.format` 과 반드시 일치 | `shorts` |
| `concept` | 미학 계보 이름. lowercase snake, 1~2 낱말 | `collage`, `dark_ink` |
| `gen` | 정수 세대. **토큰의 의미·구성이 바뀌면 증가**, 값만 바뀌면 유지 | `v1` |

예: `shorts_collage_v1`, `briefing_dark_ink_v2`. 파일은 `design_sheets/{sheet_id}.json`.

> `gen` 증가 기준이 "값"이 아니라 "의미"인 이유: 팔레트 색을 조정하는 일은 잦지만 그때마다
> 세대를 올리면 씬 조립기가 참조하는 시트 ID 가 계속 깨진다. 토큰이 추가·삭제·재정의될 때만
> 올린다.

### 0.2 토큰 키 (L1)

```
{group}_{name}[_{unit}]
```

lowercase snake, ASCII 만. **그룹 접두어는 아래 9종 고정** (신설은 본 문서 개정으로만):

| 접두어 | 대상 | 예 |
|---|---|---|
| `paper_` | 종이 표면색 | `paper_crumpled` |
| `ink_` | 잉크·텍스트색 | `ink_base`, `ink_soft` |
| `accent_` | 카테고리·엔티티 액센트색 | `accent_geopolitics` |
| `stamp_` | 검증 라벨색 (**4종 고정** — G4 / 07 §6) | `stamp_confirm` |
| `mark_` | 강조 마크색 (형광펜·펜) | `mark_highlighter` |
| `prop_` | 소품색 (테이프·실·클립) | `prop_tape` |
| `bg_` | 배경 문법 전용색 | `bg_sunburst_a` |
| `type_` | 타이포 | `type_subtitle` |
| `motion_` | 모션 | `motion_place_ms` |

safe area 는 토큰 dict 가 아니라 `DesignSheet.safe_area` 구조 필드다 (`SafeArea` 모델) — 값이
4개로 고정이고 전 시트 공통이라 open key-value 로 둘 이유가 없다.

**단위 접미어 — `motion_` 수치 토큰은 필수**:

`_ms` · `_px` · `_deg` · `_fps` · `_pct` · (무차원) `_scale` · `_count`

**값은 반드시 단일 스칼라**다. 범위·복수값은 토큰을 쪼갠다 — `push_in_scale: 1.0→1.08` 처럼
한 키에 두 값을 넣으면 `motion: dict[str, float]` 에 담기지 않아 직렬화에서 유실된다
(v1.0.5 까지 실제로 모션 토큰 7개 중 4개가 이 상태였다).

```
❌ push_in_scale = "1.0→1.08"     ✅ motion_push_in_from_scale = 1.0
                                      motion_push_in_to_scale   = 1.08
❌ paper_breath  = "scale 3, 8s"  ✅ motion_breath_scale     = 3
                                      motion_breath_period_ms = 8000
❌ grain_loop    = "4장 12fps"     ✅ motion_grain_count = 4
                                      motion_grain_fps   = 12
```

이징 커브처럼 수치가 아닌 기법은 토큰이 아니다 — 본 문서의 고정 상수로 둔다 (§1.4).

### 0.3 CSS 변수 매핑 (기계적 1:1, 예외 없음)

```
token_key  ↔  --{token_key 의 _ 를 - 로 치환}
paper_crumpled  ↔  --paper-crumpled
motion_place_ms ↔  --motion-place-ms
```

양방향 전단사다. **CSS 에만 있고 시트에 없는 변수를 만들지 않는다** — 이 규칙이 없어서
`--paper-card` / `--hl-yellow` 가 시트 밖에서 태어나 문서와 코드가 갈라졌다 (v1.0.6 에서 정규
토큰으로 흡수). 컴포지션은 `DesignSheet.to_css_vars()` 산출을 그대로 주입받는다.

### 0.4 컴포넌트 (L2)

**PascalCase 명사**. 세 곳의 표기가 같아야 한다: 본 문서 §2 표기 = `collage_kit.js` export 이름
= 시트/로그 JSON 의 등록 키(단, JSON 은 snake_case 변환형).

```
CutoutActor  ↔  cutout_actor
```

이름은 **재료+역할**로 짓는다 (`PaperPanel`, `StampLabel`, `StringConnector`). 구현 기법을
이름에 넣지 않는다 — `SvgDrawOnLine` 같은 이름은 구현이 바뀌면 거짓말이 된다.

### 0.5 표현 변형 (variant)

```
{component_snake}.{variant}
```

`variant` 는 lowercase snake이며 **보이는 형태를 서술**한다 (구현·라이브러리 이름 금지).
기본 변형은 반드시 `base`.

```
stamp_label.base / stamp_label.slam / stamp_label.worn
photo_montage_grid.base / photo_montage_grid.stack / photo_montage_grid.fan
cutout_actor.base / cutout_actor.bottom_in / cutout_actor.side_in
```

변형은 §2 대원칙상 컴포넌트당 2~4종이며, 선택 주체는 V1 시드 / V2 규칙 / V3 아트 디렉터다
(컴포넌트는 `variant` 인자로 받기만 한다).

### 0.6 씬 (L3)

씬 타입은 **SCREAMING_SNAKE 고정 6종**: `HOOK` `CONTEXT` `ACTORS` `EVIDENCE` `TURN` `CLOSING`.
한 영상 안의 씬 인스턴스 id 는 `{SCENE}_{NN}` (2자리 0 패딩) — 예: `EVIDENCE_02`.

### 0.7 고정 enum (배경 문법 · 섀도 3축)

lowercase snake. 값 추가는 본 문서 개정으로만.

| 축 | 값 |
|---|---|
| 배경 문법 (§1.6) | `sunburst` `stage_curtain` `file_desk` `paper_map` `montage_wall` `plain_grain` |
| 섀도 형태 (§1.7.1) | `offset` `outline` |
| 섀도 채움 (§1.7.1) | `solid` `hatch` `dots` |

### 0.8 라이브러리 자산 id · 파일명

| 대상 | 규칙 | 예 |
|---|---|---|
| `person_id` | 로마자 lowercase snake. **통용 표기 기준**(성-이름 어순 강제 안 함). 동명이인은 뒤에 구분자 | `trump` `xi_jinping` `jensen_huang` `chey_tae_won` |
| `logo_id` | 기업 통용 영문 snake | `sk_hynix` |
| `country_code` | ISO 3166-1 alpha-2 소문자 | `kr` |

```
assets/library/{kind}/{id}_{style}_v{NN}.{ext}
```

- `kind` ∈ `people` `logos` `flags` `textures`
- `style` = `LibraryAssetVariant.style` enum (`mono` `halftone` `linescreen` …)
- `NN` = 2자리 0 패딩 세대
- **섀도는 파일명에 넣지 않는다** — §1.7 상 섀도는 런타임 합성이고 사전 자산은 mono 컷아웃
  1장이면 되기 때문. 파일명에 박으면 액센트 색이 영상마다 다른 설계와 모순된다.
- 프롬프트 사본은 같은 경로 + `.prompt.txt` (G4-10 기록 의무).

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

키 이름은 §0.2 그룹 접두어 규약을 따른다. CSS 변수는 §0.3 매핑으로 기계 생성한다.

| 키 | 값 | 용도 |
|---|---|---|
| `paper_base` | `#E8DFC9` | 기본 크라프트지 배경 |
| `paper_aged` | `#D9CBAA` | 낡은 종이 (과거 씬·아카이브) |
| `paper_file` | `#C9BC9C` | 서류 파일/폴더 표면 |
| `paper_crumpled` | `#DDD3BD` 기조 + 절차 텍스처 | **꾸겼다 편 갱지** (사용자 확정 — 기본 배경 질감). `make_crumpled_paper` 결정론 생성: 다중 스케일 노이즈 + 각진 크리즈 능선 + 섬유 그레인, 명도 변동 ±6% 이내 |
| `paper_card` | `#F4EFE3` | **카드 흰 종이** (기사·논문 패널 표면). v1.0.6 정규 토큰 승격 — 기존 `--paper-card` |
| `ink_base` | `#1C1A17` | 본문 잉크·판화 선 (구 `ink`) |
| `ink_soft` | `#4A443B` | 보조 텍스트 |
| `bg_sunburst_a` / `bg_sunburst_b` | `#E4B33C` / `#3E6E8E` | 선버스트 방사 (노랑/청) — 카테고리 액센트로 교체 가능 (구 `sunburst_a/b`) |
| `prop_tape` | `#D8D2BFcc` | 반투명 테이프 (구 `tape`) |
| `prop_string` | `#B03A2E` | 붉은 실 관계선 (구 `string_red`) |
| `prop_date_chip` | `#B03A2E` | 날짜 칩 배경 (§2 #11 ArticleCollageCard) |
| `mark_pen` | `#B03A2E` | 손그림 펜 — 밑줄·동그라미·화살표 |
| `mark_highlighter` | `#F2D24B` | **형광펜 자국** (노랑). v1.0.6 정규 토큰 승격 — 기존 `--hl-yellow` |
| `stamp_confirm` | `#1C1A17` | `<확인>` 스탬프 (검정) |
| `stamp_inferred` | `#C9A227` | `<추론>` 스탬프 (노랑) |
| `stamp_unverified` | `#A63428` | `<미검증>` 스탬프 (빨강) |
| `stamp_refuted` | `#6E6A61` | `<반박됨>` 스탬프 (회색, 빨강 사선) |

`mark_pen` / `prop_string` / `prop_date_chip` 은 현재 같은 hex 지만 **역할이 달라 분리**한다
(펜 자국 / 물리적 실 / 인쇄된 칩). v1.0.5 까지 문서는 `string_red` 하나가 "붉은 실·형광펜"을
겸한다고 기술했으나 실제 코드의 형광펜은 노란색이었다 — 문서 기술 오류를 v1.0.6 에서 정정.

> **SVG data URI 안의 색은 CSS 변수를 못 받는다.** 형광펜 자국(`.hl-v0`~`.hl-v3`)처럼 색이
> data URI 안에 박히는 경우, 토큰은 여전히 SSOT 이되 값은 복제된다. 복제본이 조용히 갈라지지
> 않도록 `tests/test_design_sheet_naming.py` 가 **시트의 `mark_highlighter` 와 스페시먼의
> 하드코딩 hex 가 같은지 검증**한다. 새로 이런 케이스를 만들면 같은 방식으로 고정할 것.

`accent_` 그룹은 카테고리 액센트(07 §4)·엔티티 `accent_hint` 주입용으로 **예약**되어 있다.
시트에 고정값을 박지 않고 V2 규칙/V3 아트 디렉터가 런타임에 채운다 (§1.7.1).

검증 라벨 4종의 **의미·색 구분은 07 §6 을 승계** — 표면 처리(고무도장 질감)만 콜라주화.
카테고리 액센트(지정학/전쟁/경제/재난/정보전)는 07 §4 색 체계를 선버스트·스탬프 보조색에 매핑.

### 1.3 타이포 (typography)

| 키 | 값 | 용도 |
|---|---|---|
| `type_subtitle` | Pretendard **ExtraBold 68px**, 흰색+검정 4px 외곽선, keep-all | 하단 대형 자막 (모바일 가독) |
| `type_ransom_headline` | 혼합 활자 **96~140px** (씬당 1줄, 6어절 이내) | 랜섬노트 헤드라인 — **헤드라인·강조어 한정** (본문 금지) |
| `type_name_tag` | Noto Serif KR Bold 44px | 인물 이름·직함 태그 |
| `type_kicker` | Pretendard SemiBold 36px, letter-spacing 0.06em | 씬 키커 |
| `type_credit` | Pretendard Regular 26px | 출처·사진 크레딧 (우하단) |

랜섬노트 활자 소스: 시스템 내 폰트 4~6종(Pretendard 웨이트 변형 + Noto Serif KR + 자체 스탬프체)
을 글자 단위로 랜덤 조합하되 **시드 = 문자열 해시** (결정론 — `Math.random` 금지).

### 1.4 모션 (motion) — 이원 체계

전 토큰이 **단일 스칼라 + 단위 접미어**다 (§0.2) — 그래야 `DesignSheet.motion: dict[str, float]`
에 손실 없이 담긴다. v1.0.5 까지는 4개 토큰이 복수값·비수치라 직렬화에서 유실됐다.

| 키 | 값 | 용도 |
|---|---|---|
| `motion_place_ms` | 220 | 컷아웃 "탁" 놓기 (구 `place_duration` 0.22s) |
| `motion_place_from_scale` | 1.06 | 놓기 시작 배율 (위에서 살짝 크게 → 1.0 착지 + 그림자 수축) |
| `motion_step_fps` | 10 | 물성 요소 SteppedEase 스텝/초 |
| `motion_jitter_deg` | 0.3 | 정지 컷아웃 미세 회전 노이즈 (인덱스 시드) |
| `motion_push_in_from_scale` | 1.0 | 씬 내 슬로 푸시인 시작 (구 `push_in_scale` 의 앞값) |
| `motion_push_in_to_scale` | 1.08 | 씬 내 슬로 푸시인 끝 (구 `push_in_scale` 의 뒷값) |
| `motion_draw_on_ms` | 400 | 판화 선·붉은 실·형광펜 draw-on 기본 길이 (구 `draw_on`) |
| `motion_breath_scale` | 3 | 종이 숨쉬기 feTurbulence displacement 강도 (구 `paper_breath` 앞값) |
| `motion_breath_period_ms` | 8000 | 종이 숨쉬기 주기 (구 `paper_breath` 뒷값) |
| `motion_grain_count` | 4 | 필름 그레인 노이즈 프레임 장수 (구 `grain_loop` 앞값) |
| `motion_grain_fps` | 12 | 필름 그레인 순환 속도 (구 `grain_loop` 뒷값) |
| `motion_stagger_ms` | 120 | 단체 컷아웃·몽타주 순차 등장 간격 (§1.7 / §2 #7) |

**토큰이 아닌 고정 상수** (수치가 아니라 기법·커브라 §0.2 상 토큰 자격이 없다):

- draw-on 구현은 `getTotalLength` 패턴 — RENDER-AP v0.34.2 학습 준수 (inline dasharray 명시).
- 정보 요소 이징 = Material decelerate `cubic-bezier(0,0,0.2,1)`
  (PROFESSIONAL_REBUILD_PLAN §1.1 승계).
- 그레인·숨쉬기·지터의 난수는 전부 **시드 고정 결정론** — `Math.random` 금지.

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

### 1.7 인물 표현 규칙 (사용자 확정 2026-08-14 v2 — NYT 콜라주 에딧 레퍼런스)

**기본 표현은 전 샷 스케일 공통 하나로 통일한다** (v0.45.0 판화 PoC 사용자 반려 → 단순화):

> **배경 제거 컷아웃 + 고대비 모노톤 + 한쪽 컬러 오프셋 섀도**

- 모노톤: 강한 S-커브 고대비 흑백 + 하이라이트 클리핑 (회색 안개 금지 — 흑/백이 명확한
  인쇄 사진 질감). 사진 디테일은 보존한다 (획 재구성 금지).
- 섀도: 컷아웃 실루엣 복제 레이어를 **카테고리 액센트 색**으로 채워 우하단 기본
  12~18px 오프셋 (좌/우는 V1 시드로 변주). 실루엣을 정확히 따라야 하며 사각형 그림자 금지.
- 등장: **하단에서 등장** (bottom-in, place 이징). 단체(2인+)는 stagger 120ms 순차.
- 컷아웃 가장자리는 침식 1~2px + 페더링으로 깨끗하게 (배경 잔재·후광 금지).
- 섀도는 런타임 처리 — 사전 자산은 mono cutout 1장이면 되고, 액센트가 영상마다 달라도 대응.

인쇄 스크리닝(규칙 격자 halftone / 45° linescreen)은 **변주 옵션**(V2/V3 선택지)으로만 보유
— 기본값 아님, 사용자 검수 통과본에 한함. v1 규칙의 "클로즈업 판화(합성 stipple/engraving)"는
**폐기** (v0.45.0 반려 — DEVLOG 참조).

**가공 엔진 (v1.0.0)**: 위 표현의 제작은 **ChatGPT 이미지 가공이 1순위** (실사진 입력 +
표준 프롬프트 + 스타일 앵커 시트 — 계획 §2.0), 절차식 `engraving_stylizer` 는 폴백.
어느 엔진이든 산출물은 검수 게이트 → 라이브러리 고정 → 렌더는 등록본만 (도구·프롬프트
manifest 기록).

#### 1.7.1 섀도 문법 (사용자 확장 지시 2026-08-14 — 색·형태·채움 3축 변주)

| 축 | 값 | 규칙 |
|---|---|---|
| **색** | 액센트 hex | 기본 = 카테고리 액센트(07 §4) → 엔티티 시그니처 색(`accent_hint` — 기업 브랜드 컬러·국가 상징색 등, manifest 에 기록) 이 있으면 우선 가능 → 최종 선택은 V2 규칙/V3 아트 디렉터. **한 씬에 섀도 색 최대 2종** (혼잡 방지) |
| **형태** | `offset` (한쪽 치우침, 기본) / `outline` (실루엣 팽창 — 인물을 감싸는 키라인) | 두 형태 모두 **경계 명확(하드 에지) — 블러 금지**. offset 방향·outline 두께는 V1 시드 변주 |
| **채움** | `solid` (기본) / `hatch` (45° 평행선) / `dots` (규칙 격자 도트) | 패턴은 섀도 실루엣에 정확히 클리핑. 스크리닝 변주(§1.7)와 같은 계열 질감 — 같은 씬에서 인물 스크리닝과 패턴 섀도 동시 사용 금지 (과밀) |

선택 주체: V1 시드(방향·위상) / V2 규칙(카테고리·엔티티) / V3 아트 디렉터(씬 연출) —
컴포넌트는 파라미터로 받기만 한다 (§2 CutoutActor).

## 2. L2 — 컴포넌트 시트 (11종)

각 컴포넌트는 `hyperframes/shorts/assets/collage_kit.js` 에 구현될 예정(Phase 3). 여기서는
계약(입력·상태·모션·금지사항)만 확정한다. **각 컴포넌트는 표현 변형(variant) 2~4종을
갖는다** — 예: StampLabel 의 각도·마모도, PhotoMontageGrid 의 격자/스택/부채꼴, CutoutActor
의 등장 방향. 변형 선택은 V1~V3 변주 층의 몫이며 컴포넌트는 variant 인자로 받기만 한다.

| # | 컴포넌트 | 입력 | 모션 | 금지사항 |
|---|---|---|---|---|
| 1 | `CutoutActor` | LibraryPerson mono variant, 위치, 액센트 | **§1.7** — 모노톤+컬러 오프셋 섀도 + 하단 등장(단체 stagger 120ms), 이후 jitter | 즉석 생성 이미지 금지 — 라이브러리 자산만. 사각형 섀도 금지 |
| 2 | `ScreenedPortrait` (변주 옵션) | halftone/linescreen SVG | 점 성장/선 draw-on | 기본값 사용 금지 — V2/V3 가 명시 선택한 씬만. 컬러 필터 금지 |
| 3 | `RansomHeadline` | 문자열, emphasis 어절 | 글자 단위 stagger place (40ms) | 본문 자막에 사용 금지, 씬당 1줄 |
| 4 | `StampLabel` | 라벨 enum (확인/추론/미검증/반박됨) | 도장 "쾅" (1.3→1.0 + 5° 기울기) | 색·문구 변형 금지 (G4 — 07 §6) |
| 5 | `PaperPanel` | 자식 콘텐츠, 종이 톤 | place + paper_breath | AI-dashboard 글로우 금지 |
| 6 | `TapeStrip` / 핀·클립 | 각도, 길이 | PaperPanel 등장에 종속 | 남발 금지 (씬당 ≤3) |
| 7 | `PhotoMontageGrid` | BundleImage[] (cleared+credit만) | 순차 "찍기" 등장 120ms 간격 | credit 미표기 사진 금지 (IMAGE_BUNDLE_CONTRACT §3.1-a) |
| 8 | `StringConnector` | 노드 2개, 라벨 | 붉은 실 draw-on | 관계 근거 없는 연결 금지 (G4) |
| 9 | `SunburstStage` / 커튼 무대 | 액센트 색, 중앙 슬롯 | 방사 슬로 회전 / 커튼 스웨이 + 스포트라이트 | — |
| 10 | `ChartPlate` | 기존 SceneKit 차트 빌더 산출 | 종이 플레이트 위 얹기 | 차트 내부 문법 변경 금지 (기존 재사용) |
| 11 | `ArticleCollageCard` | 기사 캡처(발행처·제목·날짜·핵심 문장), 하이라이트 대상, 인물(선택) | 카드 place → 형광펜 draw-on(노랑, emphasis/근거 문장만) → 날짜 칩 스탬프 → 손그림 화살표 draw-on → 인물 컷아웃 하단 등장(카드 모서리에 걸침) | **기사 원문 변조 금지** (제목·문장 그대로 — G4), 발행처·날짜 표기 필수, 형광펜은 근거 문장에만 |

## 3. L3 — 씬 템플릿 (120초 기준)

| 씬 | 시간 | 필수 컴포넌트 | 데이터 바인딩 (번들) |
|---|---|---|---|
| HOOK | 0–3s | RansomHeadline + CutoutActor 1 | `report.video.intro_narration[0]` + headline |
| CONTEXT | 3–15s | SunburstStage 또는 PaperMap + 자막 | intro 잔여 + 최상위 섹션 도입 |
| ACTORS | 15–30s | CutoutActor(모노+섀도) + name_tag + StringConnector | 엔티티 매칭 결과 (§3.4) |
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
- 2026-08-14 v0.44.2: §1.7 인물 표현 샷 스케일 규칙(클로즈업=판화 / 상반신·단체=모노톤+
  컬러 오프셋 섀도+하단 등장) + `ArticleCollageCard` 컴포넌트 #11 (사용자 레퍼런스 —
  NYT 콜라주 에딧).
- 2026-08-14 v0.45.1: §1.7 v2 — 판화 PoC 사용자 반려로 **기본 인물 표현을 "모노톤+컬러
  오프셋 섀도" 하나로 통일** (전 샷 스케일). 합성 판화 폐기, 스크리닝(halftone/linescreen)은
  변주 옵션으로 강등. #2 EngravedPortrait → ScreenedPortrait(옵션).
