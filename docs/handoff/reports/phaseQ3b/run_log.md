<!--
tier: 3
last_synced_with: v5.20.1
ssot_for: [phaseQ3b-run-log]
depends_on: [docs/handoff/reports/phaseQ3/run_log.md, rules/video_rules.yaml, engine/style.py, engine/layers/markers.py]
last_review: 2026-10-11
-->

# Phase Q3b 실행 기록 — light 의미색 A 확정·글자 최소 보정 (v5.20.1)

지침은 D-0178(사용자 결정 D173: A|C 시트에서 "왼쪽"(A))입니다. 렌더는 표준 `FONTCONFIG_FILE` 입니다.

## 1. 바꾼 값
| 토큰 | C 잠정(v5.18.0) | **v5.20.1** | 근거 |
|---|---|---|---|
| 도형 ru·us·gold·teal·green·muted·amber·water | 휘도 0.06 | **A 값(7c50aea)** #be0013·#005abc·#7c5612·#1a6673·#2f6a2a·#555e6e·#885000·#005eae | D173 |
| `geo.themes.light.map.border_glow` | `enabled: false` | **키 삭제 = 공통 글로우** | D173 |
| `white`(마커 이름) | #0e0f11 | **#1f2125(A 그대로)** | A 값으로 25컷 4.5 통과 — 보정 불필요 |
| `gold_text`(마커 부제, 새 토큰) | (gold #5c400d) | **#68480f** = A gold 명도 × 0.84 | 도형 gold(#7c5612)는 A 그대로, 글자만 분리 |
| `city_label`(도시 이름) | [0.05, 0.05, 0.06] | **[0.054, 0.0585, 0.0675]** = A [0.12, 0.13, 0.15] 명도 × 0.45 | 이분 탐색 |

`gold_text` 는 공통값이 없어 다른 테마에선 `gold` 로 간다(`style.TEXT_BASE`) — dark 바이트 동일.

## 2. 이분 탐색(`text_token_search.json`)
A 값에서 HLS 명도만 낮춰(색상·채도 유지) 25컷 전부 `[map-contrast]` 글자 4.5 를 넘는 가장 큰 계수를 찾았습니다(8회).
| 토큰 | A 그대로 미달 | 경계 계수 | 채택 계수 | 이유 |
|---|---|---|---|---|
| white | 0 | 1.0 | 1.0 | — |
| gold_text | "가장 좁은 곳 약 39km" 3.82 등 3 | 0.863 | **0.84** | 경계값은 최저 4.50(2자리 반올림 경계) — 한 단계 여유 |
| city_label | 마닐라 3.83·벵갈루루 3.91·홍콩 4.17·타이베이시 4.21 | 0.570 | **0.45** | 같은 이유(경계 최저 4.50 → 4.67) |

## 3. 측정(25컷, `phaseQ3/contrast_table.json` light 갱신)
| 항목 | C 잠정 | **A + 글자 보정** |
|---|---|---|
| 필수 글자 최저 | 4.77 | **4.67**(마닐라 route_3+3.5) — hard 0 |
| 경로 선 중앙값 최저 | 3.33 | **2.32**(gold route_2+2) — warning(사용자가 보고 고른 값, D173) |
| 보조 지명 | 1.23 | 1.23 |
dark: 값 변경 0 — phaseV3 25/25 그대로(전체 pytest dark e2e).

## 4. 기준선·시트
- `phaseQ3/hormuz_light_baseline.json` 25컷 재생성(옛 C 값은 git 04daa0a), `expected_deltas.q3_light_user_a_d173`.
- `phaseQ3/hormuz_dark_vs_light.jpg` 갱신(dark 골든 | light A).
