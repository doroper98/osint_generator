---
id: R-0108
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G4"
version: v4.4.0
commit: fb56378
status: awaiting_decision
---

# 결정 요청 — 시간축 무대 글자 크기(D-0091 ③)

## 쟁점
시간축 무대의 레인 이름·눈금·축 값·출처 줄 글자가 glyph_size(9.5px)는 넘지만 시트에서 읽기 어렵다. 규칙 토큰 값을 올릴지 정한다.

## 선택지
| | 값(`rules stage_timeline`) | 결과 | 위험·되돌리기 |
|---|---|---|---|
| A 유지 | lane_label.size 12·dy 17, grid.label_size 10, series.axis_label_size 10, series.source_size 10 | 데모 12컷 md5 불변 | 본편도 작은 글자 |
| **B 올림(권고)** | lane_label.size **15**·dy **20**, grid.label_size **11.5**, series.axis_label_size **11**, series.source_size **11** | 레인 이름이 카드 본문(13)보다 크고 제목(30)보다 작다. 출처·기준 시점 줄이 11px | 데모 12컷 픽셀이 바뀐다 → 데모 기준선(phaseG3 demo_frames·timeline_sheet)을 G4 값으로 다시 등재해야 한다. 되돌리기 = 규칙 값 4개 복원 |
| C 레인 이름만 | lane_label 15·dy 20, 나머지 유지 | 출처 줄은 그대로 작다 | B 와 같은 재등재 필요 |

## 비교 컷
`docs/handoff/reports/phaseG4/lane_label_compare.jpg` — 데모 2컷(15.7초 타이틀 겹침, 40.0초 본편), 왼쪽 현재·오른쪽 B. 원본 해상도(854×480 두 장 나란히).

## Opus 권고 — B
- ① 되돌릴 수 있다(토큰 4개). ② 20 §6 "휑한 화면 금지"·판독 크기 불변 층의 취지. ③ 지정학 골든은 시간축 무대가 없어 영향 0(25/25 유지 — 확인해서 보고).
- B 를 택하면 D-0090 §6 "fed_timeline_demo 12컷 md5 동일" 조건과 충돌한다. 데모 기준선 재등재(expected_deltas 식 기록)를 함께 결정해 달라.

## 막히는 범위
- 막힘: 규칙 값 변경·데모 기준선. 본편 최종 렌더(프리뷰는 현재 값으로 진행하고, 결정 후 다시 뽑는다).
- 계속: D-0091 ② 색 의미(선택 키, 데모 불변)·작업 4 전부.

## §7 해당 여부
사용자 합격 값(v3 수치)은 아니다 — 시간축 무대는 G3 신규. 다만 사용자 판정 전 값이므로 Fable 판단으로 충분하다고 본다.
