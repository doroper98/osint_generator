<!--
tier: 3
last_synced_with: v5.13.0
ssot_for: [phaseQ0-run-log]
depends_on: [docs/handoff/23_QUALITY_GUIDE_20261010.md, rules/video_rules.yaml, geo/prep_tiers.py, engine/stage.py, engine/cascade.py, script/tts/elevenlabs.py]
last_review: 2026-10-10
-->

# Phase Q0 실행 기록 — 유료 TTS 차단·지도 테마 시제품·cascade 단절 재현·자산 표 (v5.13.0)

지침은 D-0153 §3 입니다. 근거는 가이드 `docs/handoff/23`(사용자 제공, 수정 금지)과 사용자 결정 D148·D149 입니다.

## 1. 유료 TTS 호출 차단(Q0-1, 가이드 §19 P0)

차단 지점은 `script/tts/elevenlabs.require_allowed()` 한 곳입니다. `config tts.elevenlabs_allowed` 를 읽는 코드도 이 함수 하나입니다(AST 테스트).

| 경로 | 차단 시점 |
|---|---|
| `script/plan.build(--tts elevenlabs)` | 린트·`tts/` 폴더 생성 전 |
| `elevenlabs.eleven_one` | `requests` import·키 접근·요청 전 |
| `tools/tts_align_probe.py` | 키·`tts_el/` 폴더·요청 전(반환 2) |

키가 환경에 있어도 기본 백엔드(supertonic)는 ElevenLabs 로 넘어가지 않습니다. 허용(true)일 때만 요청이 나갑니다(테스트로 확인).

## 2. 지도 테마 틀(Q0-2)

### 2.1 구조

지형 색은 `geo.prep` 단계에서 래스터에 구워집니다. 그래서 테마는 준비 산출물 분기로 만들었습니다.

| 층 | 내용 |
|---|---|
| 규칙 | `rules geo.themes.{default, dark, light}`. 각 테마는 `terrain`(geo.prep 가 굽는 값)과 `map`(렌더가 읽는 선·지명 색) |
| 준비 | `python -m geo.prep <proj> --theme light` → `assets/theme_light/`(`--res` 와 함께면 `assets/theme_light/res_<프로파일>/`). 기본 테마는 `assets/` 그대로 |
| 선택 | `direction stage_config.mercator.theme: dark|light`. 키 검사는 `engine.stage.mercator_theme()` 한 곳(전편 무대·콘티 막지도·`load_project`) |
| 자산 | `Assets(theme=)` 가 테마 티어를 읽습니다. 없으면 오류이고 기본 테마로 대신 그리지 않습니다(P6). 무대 테마와 자산 테마가 다르면 `StageError` |
| 렌더 | `engine/layers/borders.py`·`labels.py` 의 색·폭·대시 = `stage.theme`. `typography.text(halo_rgb=)` 는 지도 지명만 테마 값을 넘깁니다(기본값 그대로) |

`colors.sea_label` 은 `geo.themes.<테마>.map.sea_label` 로 옮겼습니다(이관, 옛 키 삭제 — P2).

### 2.2 dark = 현재 값 그대로(바이트 동일)

- 호르무즈 W·G·K 티어를 옛 코드와 새 코드로 k = 1·1.5 에서 만들었습니다. 18장 PNG md5 가 모두 같았습니다.
- 골든 25컷(`test_provenance_e2e`, phaseG17 기준선) md5 가 바뀌지 않았습니다.
- 테스트가 dark 값을 v3 `reference_code/prep3.py` 리터럴과 대조합니다. 합성 고도로 만든 래스터를 v3 식과 바이트 비교합니다.

### 2.3 light 값(시안)

| 항목 | 값 | 근거 |
|---|---|---|
| 육지 높이 톤 | 0 m `#f3f3f1` → 400 `#ececea` → 1500 `#dfdfdc` → 4000 `#d2d2ce` | §13 "밝은 회색 높이 톤", 목업 육지 실측 225~246 |
| 육지 음영 | × clip(1.0 + 0.35·(hs − sin 42°), 0.86, 1.05) | §13 "대비를 낮게" |
| 해저 깊이 톤 | 회색 g: 0 m 211 → 60 200 → 400 185 → 2000 165 → 6000 147 | 변환 뒤 목업 바다 범위(중앙값 RGB 165/182/194)에 맞춤 |
| 해저 음영 | 별도 hillshade × clip(1.0 + 0.3·(hs − sin 42°), 0.9, 1.06) | §13 "별도 hillshade" |
| 바다 변환 | g → (g−21, g−5, g+8), 0~255, 육지 제외 | §15 |
| 광원·과장 | 315°·42°, 과장 [2.7, 1.7](설계 ppd < 64, 이상) | §13 "2.7→1.7" |
| 해안 광채 | 세기 0 | 밝은 바다에 청록 광채가 얼룩처럼 보여서 끔 |
| 국경 | 실선 0.77 px, RGB 54, α 0.90 | §15 1.15 px@720 ÷ 1.5 |
| 행정선 | **실선** 0.37 px, gray 151, α 0.42(LOD 페이드 그대로) | §15 ADM1 0.55 px@720 ÷ 1.5 |
| 지명 | 어두운 글자 + 밝은 테두리(halo `0.97/0.97/0.96`), 해역 `#3d6f8e` | 밝은 바탕 대비(§7 4.5:1 목표 — Q3 에서 실측) |

### 2.4 시제품

호르무즈 골든 25컷을 light 로 렌더했습니다. 저장소 프로젝트는 건드리지 않고, 연출만 `theme: light` 로 바꾼 사본에서 돌렸습니다.
- `hormuz_light_sheet.jpg`: light 25컷 시트.
- `hormuz_dark_vs_light.jpg`: 컷마다 왼쪽 dark(현재 골든) / 오른쪽 light.

골든 기준선·expected_deltas 는 건드리지 않았습니다(dark 가 기본).

**시제품에서 보인 점(Q3 과제, 결함 기록):**
1. 국경선 글로우(청록, 기본 켜짐)가 밝은 바탕에서 국경을 푸르게 보이게 합니다. D-0153 §6 대로 Q3 에서 light 재조정값을 시트로 올립니다.
2. 해안선이 국경과 같은 짙은 선으로 그려집니다. 국가 폴리곤 고리를 통째로 긋기 때문입니다. dark 에서는 묻혔지만 light 에서 잘 보입니다. 가이드 §14 "해안과 국경 분리" 과제입니다(Q3 선 위계 범위).
3. 패널 장면(09~13·17·18·21컷)은 패널 덮개가 어둡게 깔려 dark 와 비슷합니다. 패널 대비는 그대로입니다.
4. 이란 강조(`country` 이벤트 붉은 채움)는 밝은 바탕에서 분홍빛이 됩니다.
5. 자막(흰 글자 + 어두운 테두리)과 경로·표식 라벨은 밝은 지도에서도 읽힙니다. 대비 실측은 Q3 에서 합니다.

## 3. cascade 뒤 카드 테두리 단절 재현(Q0-3, 가이드 §6)

현 코드(`engine/cascade.draw_cascade`·`island.draw_frame`·`badges.badge_at`)를 그대로 돌렸습니다. 가이드 §6 의 가상 기관 8항목(앵커 .5/2.6/…/15.2초), t = 5.8초, 480p 입니다.

| 카드 | x | y | 아래끝 | 세로 클립 x1 |
|---|---|---|---|---|
| 발표(뒤 2) | 22.00 | 70.00 | **140.52** | 90.00 |
| 협의(뒤 1) | 90.00 | 65.00 | **135.52** | 158.00 |
| 조치(앞) | 158.00 | 60.00 | 142.00 | 372.00 |

아래끝 값이 가이드 §6 과 같습니다(140.52·135.52).
- 원인: `cascade.py` 의 `ctx.rectangle(0, 0, c.clip_x1, H_OUT); ctx.clip()` 이 `draw_frame` 에도 걸립니다.
- 결과: '발표' 의 x ≥ 90 이 통째로 잘려 하단선이 x 90 에서 끊깁니다. '협의' 아래 띠(x 90~158, y 135.52~140.52)에 '발표' 카드 대신 바탕이 보입니다.
- 파일: `cascade_asis_clip.png`(위 = 전체 프레임 + 빨간 상자, 아래 = 상자 6배 확대). Q1 전/후 비교의 기준입니다.
- 국기는 자리표시로 `eu` 하나를 썼습니다(가상 기관 데모라서). 확대 상자에는 국기가 들어가지 않습니다.

## 4. 가이드 §20 자산 — 받은 것·받지 못한 것

목업 영상은 저장소에 원본(mp4)이 없습니다. Fable 이 만든 컨택트 시트(`mock_*.png`)만 있습니다(D-0153 머리말).
아래 "받음" 의 영상 이름은 시트 내용으로 대응시킨 것입니다.

| §20 자산 | 상태 | 비고 |
|---|---|---|
| 가이드 문서 | **받음** | `docs/handoff/23_QUALITY_GUIDE_20261010.md` |
| `cascade_alignment_continuity_v2_1080p.mp4` | **받음(시트)** | `mock_cascade_v2_sheet.png` — Q1 기준 |
| `portrait_flag_comparison.mp4` | **받음(시트)** | `mock_portrait_flag_sheet.png` — Q2 기준 |
| `ukraine_east_zoom_demo_v4.mp4` | **받음(시트)** | `mock_ukraine_map_v4_sheet.png` — Q0-2·Q3 기준(육지·바다 색 실측 출처) |
| `portrait_as_is_to_be.png`, `render_portrait_test.py` | 받지 못함 | Q2 는 시트·가이드 수치로 진행 가능 |
| F-35 SVG 일체(`f35-tobe.svg`, `f35-refined-v2*.svg`, `-transparent.png`, 비교 PNG), `build_f35_v2.py` | 받지 못함 | **Q5(자산 스킬) 착수 조건** |
| `east_asia_grayscale_map.png`, `osint_map_zoom_demo.mp4`, 우크라이나 v1~v3 | 받지 못함 | 이전 검토본 — 필요 없음(가이드가 v4 로 대체 명시) |
| `cascade_lines_as_is_to_be_1080p.mp4` | 받지 못함 | relation 참고용 — Q6 착수 전 확보 권고 |
| `render_comparison.py`, `render_cascade_v2.py`, `render_zoom.py` | 받지 못함 | 독립 harness — 저장소 렌더러로 쓰지 않음(§20), 수치는 가이드 표로 충분 |
| 지도 데이터(OCHA 2025 ADM, KOSTAT 2018, OSM PBF·도로, NE 강) | 받지 못함 | 도로·강·ADM2 레이어(§14·§15)의 착수 조건. Q3 선 위계는 기존 국경·ADM1 만으로 가능 |

## 5. 판단 기록(되돌릴 수 있는 선택)

1. 과장은 D-0153 의 "1.7" 대신 `[2.7, 1.7]` 두 값으로 뒀습니다. 기존 dark 가 설계 ppd 64 기준 두 값([2.8, 2.0])이고, 가이드 §13 이 "2.7→1.7" 로 적었기 때문입니다.
2. light 행정선은 대시 없는 실선입니다(§15 "실선"). dark 는 기존 대시 [2.5, 2.5] 그대로입니다.
3. light 해안 광채는 세기 0 으로 껐습니다. 구조(`coast_glow`)는 두 테마가 같습니다.
4. `colors.sea_label` 을 지우고 테마 토큰으로 옮겼습니다. 이 색을 읽는 곳이 지도 지명 하나뿐이라 두 곳에 두지 않았습니다.
5. 테마 이름은 `dark`·`light` 둘로 고정했습니다(스키마 필드). 사용자 결정 뒤 Q3 에서 하나를 지웁니다(D-0153 §2 교체형).

## 6. 테스트

Q0 새 테스트 15개입니다(요구 ≥ 8).

| 파일 | 수 | 내용 |
|---|---|---|
| `tests/test_tts_paid_block.py` | 6 | plan·provider·probe 세 경로 `requests.post` 0회, 키 있어도 자동 전환 없음, 허용일 때만 요청, 설정 읽는 곳 하나(AST) |
| `tests/test_q0_map_theme.py` | 9 | dark 값 = v3 리터럴, dark 래스터 = v3 식(바이트), light 바다 변환·육지 무변환·해저 결, 테마 extra 키·없는 기본값 거부, 테마 자산 경로, stage_config 검사, 자산 없음 오류·테마 불일치 오류, 지도 레이어 색 리터럴 없음(AST), halo 기본값 = dark |

## 7. 전체 pytest

`FONTCONFIG_FILE` 표준 설정입니다.

| 시점 | passed | failed | skipped | xfail |
|---|---|---|---|---|
| S5 끝 | 1415 | 0 | 0 | 0 |
| Q0 끝(c68fa6c) | **1430** | **0** | **0** | 0 |

기준 1415 + 15 = 1430 = 실측(26분 44초)입니다. `-rs` 출력에 SKIPPED 줄이 없습니다.
