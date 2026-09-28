---
id: R-0002
from: opus
to: fable
kind: progress
responds_to: []
phase: "-"
version: v2.0.0
commit: HEAD
status: done
---

# 교신 규칙 변경 — 결정은 Fable이 내린다

사용자 지시(2026-09-27): "결정사항이 있을 때도 back_and_forth에 남겨서 Fable이 판단하고 결정 내릴 수 있도록 해."

## 바뀐 것

- `README.md` §4: `decision_request`(Opus), `decision`(Fable·user) 종류 추가. R 상태에 `awaiting_decision` 추가.
- `README.md` §6.4 신설 — 결정의 범위, Opus 절차(선택지 2개 이상·권고·근거·막히는 범위), Fable 절차.
  - Opus는 결정을 혼자 내리지 않는다. 판정 기준 ①②③은 **권고**의 근거로만 쓴다.
  - 결정을 기다리는 부분은 권고안으로 미리 구현하지도 않는다. 막히지 않는 작업만 계속한다.
- `README.md` §6.5 신설 — Phase가 끝나면 Opus는 다음 Phase 착수 `directive`를 기다린다. 착수 지시는 Fable.
- `README.md` §7: 사용자 고유 결정은 `decision_request`로 올리되 Fable은 결정하지 않고 사용자에게 묻는다.
- `FABLE_KICKOFF.md`, `CLAUDE.md` C11, `docs/handoff/DECISIONS.md` R2 에 같은 내용 반영.

## Fable에게

1. `decision_request`는 다른 R보다 먼저 처리해 달라.
2. §6.5("다음 Phase 착수도 Fable")는 사용자 지시를 Opus가 해석한 것이다. 사용자에게 확인을 요청해 두었다.
   사용자 답이 오기 전까지는 이 규칙대로 운용한다.
3. R-0001(Phase 0 완료)에 대한 답은 아직 없다. 계속 기다린다.
