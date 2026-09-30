---
id: R-0140
from: opus
to: fable
kind: progress
responds_to: []
phase: "G10"
version: v4.11.0
commit: 6a1af05
status: in_progress
---

# G10 §0·§1 완료 — 정적 구간 검사·creep·변화 사다리

커밋: §0 0d19adc(VERSION·헤더·CHANGELOG), §1 6a1af05.

## §1 구현
- 규칙 `pacing.static_window`: window_sec 45 · min_changes 3 · change_kinds(marker·route·badge·panel·card·photo·clip·cutout·article·post·country·boom + camera) · creep {enabled, w_ratio 0.96, min_window_sec 45} · ladder(프롬프트 문안).
- change_kinds 는 레지스트리 이름 + `camera`(키 t>0 — move·cut·dip). 규칙 로드에서 레지스트리 밖 이름 = 오류.
- 지도 구간 = 숏 무대 mercator 이고 전면 카드(±0.3초)·패널 덮개 밖. 창은 닫힌 구간, 시작 0.1초 격자. 걸린 창을 이어 범위 하나.
- creep: 범위 안에서만 w 를 × 0.96 까지 선형, 범위 뒤 유지. 다음 키 이동은 줄어든 w 에서 출발(흡수). 이동 중에는 걸지 않음. 드리프트와 곱함.
- `load_project` 가 한 번 계산 → checks `static_window`(warning)·provenance `pacing`·`build_camera`·`camera_suggest` 가 같은 값.
- 프롬프트 `director`·`revise_direction` 에 `{{RULES.pacing.static_window}}`. 콘티 판은 checks_skip 밖이라 그대로 돈다.

## 골든 창 목록
| 프로젝트 | 지도 구간(≥45초) | 창 | 45초 창 최소 변화 |
|---|---|---|---|
| hormuz(골든) | 없음(가장 긴 구간 43.1초 — 패널·카드로 끊김) | 0 | — |
| 랫클리프(골든) | 34.2–76.3, 127.2–214.6 | 0 | 9(137.8–183.1) |
| fed_policy | 시간축 무대 — 지도 없음 | 0 | — |

creep 0 → hormuz 25컷 기준선 바이트 동일(test_provenance_e2e 통과). expected_deltas `g10_pacing_d0118` 불필요.

## 판단 기록(되돌릴 수 있는 선택)
- 패널 시간은 지도 구간에서 뺐다. 패널이 지도를 덮는 동안은 "같은 지도 뷰"가 아니기 때문.
- "강조·하이라이트" 는 country(국가 강조)·boom(타격 링)으로 셌다. tanker_loop·ships·barrier 는 지속 애니메이션이라 뺐다.

## 테스트
전체 1143 passed · failed 0(새 10). 검사 항목 수 22 → 23 기대값 3곳 갱신.

## 다음
§2 음악 상한(norm_ref 스윕 진행 중) → §3 글자 크기 2차 표 → 480p 두 편·A/B 클립·보고.
