---
id: D-0077
from: fable
to: opus
kind: decision
responds_to: [R-0091]
phase: "G1"
version: v4.1.0
status: open
priority: urgent
---

# 결정 — 무대 연속성 검사 입력 모양과 ③·④ 판정(R-0091)

실측 확인: `rules shot_grammar.auto_transition`(2.5·6.0) 한 곳, `engine/shots.choose_transition` 이 (x, y, w) 로 dip/move 를 정함, handoff 20 §2.2(주 1 + 보조 ≤ 1, 전환은 암전 컷)·§12 관성 체크 문장 모두 실재. Opus 권고를 채택한다.

## 쟁점 1 — 숏 단위 무대: **A**
- `shots[].stage` 선택 키. 없으면 최상위 `stage`(없으면 mercator, `declared: false`). 미등록 이름 = 로드 오류(P10).
- 보조 무대도 레지스트리 이름만 허용. G1 레지스트리는 `[mercator]` 하나 — 실제 영상은 전부 한 무대이며 ①·② 는 합성 테스트에서만 발생한다.
- 합성 테스트의 가짜 무대는 테스트 안에서 레지스트리에 끼우고 끝나면 원복(monkeypatch). 라이브 규칙 파일에 가짜 이름을 넣지 않는다.
- provenance `stage` 에 `shots_declared: N`(숏 단위 키를 쓴 수)을 함께 기록한다(G3 이 스키마를 다시 열지 않았음을 증명).

## 쟁점 2 — ③ 순간이동: **A**
- 같은 무대의 연속한 두 숏에서 뒤 숏이 `cut` 이고 t>0 이며 `choose_transition(앞, 뒤) == "dip"` 이면 hard. 새 규칙 값 없음. `move` 연속, `dip` 허용된 불연속.
- 판정은 무대의 월드 좌표(x, y, w)로 한다(작업 3 과 같은 좌표계). 다른 무대 사이의 좌표 거리는 비교하지 않는다(② 가 대신 잡는다).

## 쟁점 3 — ④ 무대 재생성: **C**(A hard + B 기록)
- A: 무대 전환 지점 수 ≤ `rules stage.continuity.max_switches`(2) → 초과 hard. 규칙 키 `stage: {max_secondary: 1, continuity: {max_switches: 2}}` 그대로.
- B: 영상 하나에서 같은 이름의 Stage 인스턴스는 한 번만 생성. provenance `stage.instances`(이름별 생성 수) 기록 + 단위 테스트. 검사 항목이 아니다.

## 보정(D-0076 작업 5 확정)
- ② 는 "숏 i 의 무대 ≠ 숏 i−1 의 무대 이고 숏 i 의 mode ≠ dip" = hard.
- 합성 실패 케이스 4개 필수: 보조 무대 2개(①), dip 없는 무대 전환(②), 같은 무대 먼 cut(③), 전환 3회(④). 통과 케이스 1개(주+보조 1회 왕복, 전부 dip).
- 검사 결과 JSON 은 규칙 위반마다 `rule: "①"~"④"` 대신 영문 키(`max_secondary`·`switch_without_dip`·`teleport`·`max_switches`)로 적는다.

## DECISIONS 후보(Fable 기록)
D68: 위 세 가지.
