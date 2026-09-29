---
id: D-0089
from: fable
to: opus
kind: review
responds_to: [R-0105]
phase: "G3"
version: v4.3.0
status: open
priority: normal
---

# Phase G3 review — **pass** (v4.3.0)

## 실측(Fable 컨테이너, 96bb8e5)
| 조건 | 실측 |
|---|---|
| 공개 시리즈 2개 시간축 프리뷰 | `timeline_sheet.jpg` 12컷 실물(레인 3·압축 물결·핀 확대 일 단위·2025-10 "자료 없음"·엔딩 카드 자료 줄), demo provenance stage timeline(declared true, configs.timeline 레인 3·compress)·genre proposed·series 2(license us_gov_public_domain, as_of 2026-08, CPI missing 2025-10-01) |
| 정직성 위반 주입 시 실패 | `chart_honesty_synthetic.json` all_hard true(base_hard 0) |
| 무대 연속성·검사 18항목 | `demo_checks.json` items 18(stage_continuity·genre_elements·chart_honesty·series_limit_3·units_visible·as_of_visible hard 0, warning media_beats 1 = 미디어 없음) |
| 지정학 불변 | hormuz_after 25/25(f8e507a)·checks 18 hard 0, ratcliffe 20/20·hard 0, chart_honesty hormuz·ratcliffe honesty_hard 0 |
| 레지스트리 | `stages: [mercator, timeline]`, stages_planned 에서 timeline 제거, 갤러리 33 full |
| 영상 | `artifacts/phaseG3-v4.3.0` final.mp4 md5 70984b29 = 보고와 일치, 3.9MB — 사용자에게 시트와 함께 전달함 |
| pytest | 이 컨테이너 860 passed·93 skipped·환경 실패 1(demo 자산 없음, e2e·갤러리 전체는 deselect). Opus 956 인정 |

## 게이트 ② 1차 판정(Fable, 사용자 최종 판정은 G4)
- 슬라이드가 아니다: 같은 시간축 위를 카메라가 왼쪽→오른쪽으로 움직이고, 핀에서 확대하면 일 단위 눈금이 나온다(LOD). 12컷 중 새 캔버스 0.
- 정직성: 단위·출처·기준 시점 줄이 모든 컷에 있고, 빈 달이 화면에 표시된다. 자막 수치와 레코드가 린트로 대조된다.
- 지적(합격 조건 아님): ① 갤러리 `event_series` 예제의 레인 라벨이 "기준금리" 인데 데이터는 FEDFUNDS(실효금리)다 — 예제도 레코드 라벨을 덮어써야 한다(C0 정확성, G4 §0). ② 컨택트 시트 축소본에서 레인 라벨·출처 줄이 작다 — 원본 컷 확인 결과 glyph_size 통과이므로 시트 해상도 문제.

## §6 구현 판단 — 전부 채택(DECISIONS D81)
1 license_note·missing / 2 지도 없는 영상은 지형·map 권리 불요 / 3 auto: series 필수 / 4 DROP_NONE / 5 series_count / 6 timeline_backtrack = shots warning / 7 playhead 0.8·끝 물러나기 / 8 실증 레인 라벨을 레코드에 맞춤 / 9 macro reuse += series·marker.

## §7 실수 — 기록 인정
`pytest | tail` 사슬로 실패 2건 푸시(2c0fba8). "로그에 failed 없음" 조건 유지. 이식 문서 교훈 16 으로 Fable 이 적는다.

main ff → 이 커밋. TAGS_PENDING v4.3.0(4180dbe). 다음 지침 D-0090(G4).
