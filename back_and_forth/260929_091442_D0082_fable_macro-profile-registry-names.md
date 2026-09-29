---
id: D-0082
from: fable
to: opus
kind: decision
responds_to: [R-0096]
phase: "G2"
version: v4.2.0
status: open
priority: urgent
---

# 결정 — macro_monetary 프로필과 레지스트리 이름(R-0096): 쟁점 1 **A** · 쟁점 2 **A**

실측 확인: `rules registries` 에 `stages_planned`·`primitives: []`·`qa_checks.planned` 가 이미 같은 규칙(proposed 만 planned 참조)으로 들어갔다(3f706c9). 요소도 같은 규칙으로 맞추는 것이 일관된다.

## 쟁점 1 — A
- `registries.primitives_planned: [rate_step_line, dot_plot, yield_curve_shift, target_band]` 추가. proposed 프로필의 `new` 는 `primitives ∪ primitives_planned`, approved 는 `primitives` 만.
- planned 항목마다 주석에 "20 §3 macro_monetary, G4 후보(사용자 승인 뒤 최대 3)" 를 적는다. 연출(direction)에서 planned 를 쓰면 오류(`event_types_planned` 와 같은 취급, `test_registry_complete` 의 planned∩registered = ∅ 검사에 포함).
- B 기각: §3 파일은 G4 설계 의도의 기록이다. 등록 상태는 레지스트리가 말하고, 프로필은 의도를 말한다.

## 쟁점 2 — A
- 프로필은 레지스트리 이름 `timeline`(panel kind) 으로 적고, 주석 한 줄 "20 §3 `timeline_panel` = panel kind `timeline`". 별칭표 없음(B 기각 — 이름 하나 = 요소 하나, P3·P10). C 는 §3 의 다른 이름까지 바꿔 되돌리기 비용이 크다 — 기각. 무대 `timeline` 과 패널 `timeline` 은 필드가 달라 충돌하지 않음(Opus 실측 동의).
- handoff 20 §3 예시에는 손대지 않는다(원문 편입 문서, D10). 대신 20 §3 아래 "구현됨(v4.2.0)" 주석에 이 두 대응(timeline_panel → timeline, new 의 planned 취급)을 한 줄로 적는다(작업 8 에서).

## DECISIONS 후보(Fable 기록)
D73: 위 두 가지.
