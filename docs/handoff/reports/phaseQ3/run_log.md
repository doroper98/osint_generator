<!--
tier: 3
last_synced_with: v5.18.0
ssot_for: [phaseQ3-run-log]
depends_on: [docs/handoff/reports/phaseQ0/run_log.md, engine/direction.py, engine/stage.py, engine/layers/borders.py, engine/checks.py, rules/video_rules.yaml, rules/series_registry.yaml, genres/geopolitics.yaml]
last_review: 2026-10-11
-->

# Phase Q3 실행 기록 — 지도 테마 두 개 정식 (v5.18.0)

지침은 D-0161(사용자 결정 D154)·D-0170 §3 입니다. 시리즈는 D-0171(D165), light 값은 D-0172(D166, 잠정 — 사용자 시트 확인)입니다.
모든 렌더는 표준 `FONTCONFIG_FILE`(phaseS0 §0.2)로 했습니다. dark 골든은 V3 기준선(phaseV3) 그대로 25/25 입니다.

## 1. 만든 것
| 항목 | 내용 |
|---|---|
| 테마 고르기 | direction `stage_config.mercator.theme`(사유 `theme_reason` 필수) → 장르 프로필 `genres/geopolitics.yaml stage.mercator.theme: light`. 프로필에 값이 없으면 `StageError`(조용한 dark 폴백 없음, D-0171 §3). 연출에 지도 설정은 하나라 숏별 혼용은 문법상 불가 |
| 기록·검사 | provenance `map_theme {effective, source, declared, reason, series}`. `[map-theme-override]` warning(장르와 다를 때, 시리즈 소속이면 안 냄). `rules/series_registry.yaml`(빈 시작) + `[series-theme-mismatch]` hard, 한 프로젝트 두 시리즈 = 로드 오류 |
| 골든 | `projects/hormuz_korea/direction.yaml` 에 `theme: dark` + 사유 → override warning 1건(정상). director 예시에는 넣지 않음(테마 덮어쓰기를 가르치지 않게, 테스트가 그 차이만 허용) |
| 의미색 보정 | `colors.themes.light`(색상 불변·휘도 0.06, D-0172 C). 지도 위 요소만 `map_c(view.stage, 키)` — 경로·국가 채움·폭발·마커 점·마커 이름·부제. 무대 기준이라 아일랜드 차트 안 마커는 공통값. 카드·자막·HUD·엔딩·아일랜드는 지도 색 함수를 쓰지 않는다(테스트) |
| 해안선 ↔ 국경 | `geo.themes.light.map.coast` 가 있으면 두 나라가 **공유하는 변만** 국경, 나머지는 해안(물빛 얇은 선). 공유 변은 한 번만 긋는다. 거리 buffer 미사용(가이드 23 §14). dark 는 `coast` 없음 = 종전 바이트 |
| 글로우·테두리 | 테마별 `border_glow`(light = `enabled: false`), `route_casing`(선택 키, 시안에서 이득 없어 미사용) |
| 콘티 판 | 막지도가 전편과 같은 테마(`rules animatic.flat_map.themes.light`) |
| 대비 검사 | `[map-contrast]` — 렌더 프레임의 **지도 층 합성본**(카드·패널·사진·전면 카드 전)에서 측정. 필수 글자(마커 이름·부제·도시) 4.5 hard, 경로 선 3 warning(컷·경로별 표본 중앙값). 국가·바다·도 이름은 보조 질감(§7) — 측정표에만 |

## 2. light 시안 비교(R-0201 → D-0172)
시트 `light_variants_sheet.jpg`, 값 `variants.json`. 한 의미색으로 밝은 육지(휘도 0.84)와 깊은 바다(0.29~0.34) 둘 다 3:1 을 넘기려면 휘도 ≈ 0.06 이하.
| 시안 | 필수 글자 최저 | 경로 선 중앙값 최저 | 결과 |
|---|---|---|---|
| A 휘도 0.11 | 3.81(미달 2 — 금색 부제) | 2.31 | 기각 |
| B 테두리·글로우 끔 | 3.84 | 2.22 | 기각(이득 없음) |
| **C 휘도 0.06·글로우 끔·글자 톤 짙게** | **4.94** | **3.33** | **채택(잠정, D166)** |
| D 테두리·짙은 청록 글로우 | 3.84 | 2.22 | 기각 |

측정으로 바꾼 값(가이드 23·Q0 시안 대비):
| 키 | 옛 값 | 새 값 | 근거 |
|---|---|---|---|
| `colors.themes.light.*` | (없음 — 공통값) | 휘도 0.06 같은 색상(금 #5c400d 등) | 위 표 |
| `geo.themes.light.map.city_label` | [0.12, 0.13, 0.15] | [0.05, 0.05, 0.06] | 작은 글자 안티에일리어싱 뒤 4.5 |
| `colors.themes.light.white`(마커 이름) | 흰 글자 | #0e0f11 | 같음 |
| `geo.themes.light.map.border_glow` | 공통(하늘색) | 끔 | 밝은 지도에서 거의 안 보임 / 짙게 하면 국경이 무거움 |
| `geo.themes.light.map.coast` | (없음) | 물빛 얇은 선 | 가이드 §14 "밝고 얇은 coast" |

## 3. 대비 측정표(두 테마 × 25컷, `contrast_table.json`)
| 테마 | 종류 | 측정 수 | 최저 5 |
|---|---|---|---|
| dark | 필수 글자 | 210 | 5.33 도하 · 5.62 홍콩 · 5.67 콜카타 · 5.70 콜카타 · 5.78 콜카타 |
| dark | 경로 선(중앙값) | 225 | 5.38 teal · 5.45 gold · 5.45 gold · 5.47 gold · 6.81 봉쇄선 |
| dark | 보조 지명 | 140 | 1.87 인천 · 2.04 · 2.11 · 2.15 강원도 · 2.16 대구 |
| light | 필수 글자 | 210 | 4.77 벵갈루루 · 4.80 마닐라 · 4.92 · 4.94 · 4.94 |
| light | 경로 선(중앙값) | 225 | 3.33 gold · 3.40 · 3.47 · 3.49 · 3.56 teal |
| light | 보조 지명 | 140 | 1.23 남중국해 · 1.24~1.25 인도양 |
두 테마 모두 `[map-contrast]` hard 0·warning 0.

**dark 도형 warning 2건(R-0201 §4) 원인 — 측정 쪽**: 옛 판정(최저값)에서 teal 1.08 은 점선 경로의 **틈**에 떨어진 표본(선 휘도 0.009), gold 1.52 는 **마커·라벨 위** 표본(배경이 선보다 밝음)이었습니다. 같은 경로의 다른 표본은 3.0~10. 컷·경로별 중앙값 판정으로 바꾸자 0건 — dark 값은 바꾸지 않았습니다.
**관찰(결정 불필요)**: light 바다 이름(보조, 알파 0.62)은 대비 1.2 수준으로 거의 안 보입니다. 가이드 §7 은 보조 질감을 같은 기준으로 올리지 않으므로 그대로 둡니다.

## 4. 기준선·시트
- light 기준선 `hormuz_light_baseline.json`(25컷, V3 Supertonic 플랜 위, direction `theme: light`, 25_END 도장 가림). 재현 = `tests/anti_inertia/test_q3_light_e2e.py`(원본을 링크로 펼친 사본 → `geo.prep --theme light` → 프리뷰).
- 사용자 확인용 `hormuz_dark_vs_light.jpg`(25컷 dark 골든 | light).

## 5. 장르 미선언 옛 지도 프로젝트(D-0171 §3 수용 — 다음 렌더부터 light)
dmz_mine_2026 · hormuz-talks-2026 · hormuz_ai · hormuz_ai_cam · hormuz_camauto · kaliningrad-suwalki · ratcliffe2026 · taiwan_ai · taiwan_f1_music · taiwan_f1_nomusic · taiwan_strait · valdai-2026.
(호르무즈 골든만 dark 고정. fed_policy_2026·fed_timeline_demo 는 지도 무대 없음.) 다시 렌더하려면 `geo.prep --theme light` 자산이 필요합니다.

## 6. 판단(되돌릴 수 있음)
- 장르 기본값 키 = 장르 프로필 `stage.mercator.theme`(`rules genres` 대신 — 장르 SSOT, D-0171 §3 동의).
- YAML 1.1 에서 `on` 키가 참·거짓으로 읽혀 테마별 글로우 스위치 이름을 `enabled` 로 했습니다.

## 7. pytest

**1507 passed · 0 failed · 0 skipped**(313 subtests, 34분 37초). 1차 6 실패(검사 표 2·가짜 view 1·ratcliffe2026 light 자산 3 — 환경 준비 `python -m geo.prep projects/ratcliffe2026 --theme light`)를 고친 뒤 재실행.
