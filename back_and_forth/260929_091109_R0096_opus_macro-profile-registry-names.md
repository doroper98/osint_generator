---
id: R-0096
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G2"
version: v4.2.0
commit: 0e66d1c
status: in_progress
---

# 결정 요청 — macro_monetary "20 §3 그대로" 와 레지스트리 이름 규칙의 충돌 (쟁점 2개)

D-0081 §1-2 는 macro_monetary 를 **20 §3 예시 그대로** 쓰라고 한다. 같은 지침 §1-1 은 `primitives.reuse` ⊆ registries(event_types·panel_kinds·badge_kinds·primitives), `new` ⊆ `registries.primitives`, 미등록 이름 = 로드 오류(P10)라고 한다. §3 예시는 이 규칙을 두 곳에서 통과하지 못한다.

## 쟁점 1 — `new` 5개 중 G2 등록은 statement_diff 하나
§3 `new: [rate_step_line, dot_plot, yield_curve_shift, statement_diff, target_band]`. G2 에서 `registries.primitives` = [statement_diff] 뿐이다(§3 "statement_diff 외 프리미티브 = G4"). 나머지 4개는 로드 오류가 된다.

| 선택지 | 결과 | 위험 | 되돌리기 |
|---|---|---|---|
| **A** `registries.primitives_planned: [rate_step_line, dot_plot, yield_curve_shift, target_band]` 추가. proposed 프로필만 planned 참조 허용(stages_planned·qa_checks.planned 와 같은 규칙) | §3 그대로 통과. approved 로 바꾸면 planned 4개가 오류 → 등록 전 승인 불가(G4 절차와 맞음) | planned 목록이 하나 늘어난다 | 키 삭제 |
| B macro_monetary `new` 를 [statement_diff] 로 줄임 | 규칙 변경 없음 | "§3 그대로" 위반, G4 설계 의도(§10 새 요소 3)가 파일에서 사라짐 | 파일 수정 |

## 쟁점 2 — `reuse` 의 `timeline_panel`
레지스트리 이름은 패널 kind `timeline` 이다. `timeline_panel` 은 어느 목록에도 없다.

| 선택지 | 결과 | 위험 | 되돌리기 |
|---|---|---|---|
| **A** 프로필에 `timeline`(패널 kind) 으로 적고 주석에 "§3 timeline_panel = panel kind timeline" | 이름 하나 = 레지스트리 하나(P10). 별칭 코드 없음 | §3 문자 그대로는 아님 | 한 줄 |
| B 스키마에 별칭표(timeline_panel → timeline) | §3 문자 그대로 | 이름 두 개가 같은 요소 — P3·P10 의 "단일 이름" 약화, 이후 별칭 누적 | 별칭 삭제 |
| C reuse 를 네임스페이스로(`panel:timeline`, `panel:versus`, `event:card` …) | 무대 이름 timeline·패널 kind timeline 같은 충돌까지 원천 차단 | §3 의 다른 이름(versus·checklist·card)도 전부 바뀜 | 파일·스키마 수정 |

## Opus 권고
- 쟁점 1 = **A**. 판정 기준 ②(D-0081 의 "proposed 는 planned 허용" 규칙을 요소에도 같게 적용, §3 그대로) ①(키 하나 삭제로 되돌림).
- 쟁점 2 = **A**. 기준 ③(저장소 실측 레지스트리 이름이 정본, 별칭 없음) + 기록. 이름 충돌(timeline)은 요소 네임스페이스(이벤트·패널·뱃지·프리미티브)와 무대 네임스페이스가 서로 다른 필드라 생기지 않는다.

## 근거
- docs/handoff/20 §3(예시)·§4.1-4(등록 = 한 커밋)·§10(새 요소 3), rules `registries`(panel_kinds 에 timeline, primitives 키 없음).
- D-0081 §1-1·§1-2·§3.

## 막히는 범위
- 막힘: 작업 2 의 macro_monetary.yaml 과 그 통과 테스트, 작업 1 의 "new ⊆ primitives ∪ planned(proposed)" 분기.
- 계속: 작업 1 스키마 본체(무대·qa_extra·reuse 검사), geopolitics.yaml, 작업 3(direction genre·genre_elements), 작업 4~6(프리미티브 계약·statement_diff·갤러리).
- §7 해당 없음(Fable 전결).
