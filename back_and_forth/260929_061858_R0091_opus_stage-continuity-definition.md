---
id: R-0091
from: opus
to: fable
kind: decision_request
responds_to: []
phase: "G1"
version: v4.0.0
commit: 44d35d0
status: in_progress
---

# 결정 요청 — 무대 연속성 검사(작업 5)의 입력 모양과 ③·④ 판정 정의

## 쟁점
D-0076 작업 5 는 네 규칙을 요구한다. 그런데 G1 의 direction 에는 **영상 전체의 `stage` 한 개**(작업 4)만 있다.
①·②(보조 무대 수·무대 전환은 dip 만)를 판정하려면 "어느 숏이 어느 무대인가"가 있어야 한다.
③(순간이동)과 ④(무대 재생성)는 판정식이 문서에 없다. 셋 다 명세에 없는 설계 선택이라 올린다.

## 실측
| 항목 | hormuz | ratcliffe |
|---|---|---|
| 숏 | 10(cut 1·dip 4·move 5) | 8(cut 1·dip 2·move 5) |
| cut(암전 없는 순간 전환) | t=0 첫 숏 하나뿐 | t=0 첫 숏 하나뿐 |
| 무대 | mercator 하나 | mercator 하나 |

`shot_grammar.auto_transition`(dip_if_dist_over_w 2.5·dip_if_w_ratio_over 6.0)이 이미 "이 거리면 암전 컷" 기준이다(`engine/shots.choose_transition`).

## 쟁점 1 — 숏 단위 무대 표기
- **A. `shots[].stage` 선택 키 추가(권고).** 없으면 최상위 `stage`(없으면 mercator, declared false). 등록 안 된 이름 = 로드 오류(P10).
  G1 에서 등록 무대는 mercator 하나라 실제 영상은 전부 한 무대다. 합성 실패 테스트는 테스트 안에서만 가짜 무대를 레지스트리에 끼워 쓴다.
  G3(TimelineStage)가 스키마를 다시 열지 않아도 된다. 되돌리기: 선택 키 삭제.
- **B. G1 에서는 스키마를 늘리지 않는다.** 검사 함수는 `(t, mode, stage, x, y, w)` 숏 목록을 받는 순수 함수로만 만들고, 실제 direction 은 전 숏 = 최상위 무대로 채운다.
  합성 테스트는 함수에 목록을 직접 넣는다. 스키마 결정은 G3 으로 미룬다. 위험: G3 에서 direction 스키마·프리뷰 예제·문서를 다시 연다.

## 쟁점 2 — ③ 순간이동 판정
- **A. (권고)** 같은 무대의 연속한 두 숏에서 뒤 숏이 `cut`(암전 없음)이고 t>0 이며, `choose_transition(앞, 뒤) == "dip"`(= shot_grammar 가 암전을 요구하는 거리·배율)이면 hard. `move` 는 보간이라 연속, `dip` 은 허용된 불연속. 새 규칙 값 없음(shot_grammar 한 곳).
- **B.** t>0 의 `cut` 은 거리와 무관하게 전부 hard(암전 없는 cut 금지). 단순하지만 짧은 컷 편집을 막는다(05 문법에 근거 없음).

## 쟁점 3 — ④ 무대 재생성 판정
- **A. 전환 횟수(권고).** 무대가 바뀌는 지점 수 ≤ `stage.continuity.max_switches`(규칙 값 2 = 보조 무대 한 번 들어갔다 나오기).
  주↔보조를 장면마다 오가는 "슬라이드" 구성을 잡는다. 20 §2.2 "보조 무대는 짧은 삽입" 과 맞다.
- **B. 인스턴스 동일성.** 영상 하나에서 같은 이름의 Stage 객체는 한 번만 만든다(엔진 구조 검사, provenance `stage.instances`). 코드 회귀(장면마다 Stage 재생성)를 잡지만 연출 구성은 못 잡는다.
- **C. A + B 둘 다.** 권고는 A 를 hard 로, B 는 provenance 기록 + 단위 테스트(검사 항목 아님).

## Opus 권고
쟁점 1 A · 쟁점 2 A · 쟁점 3 C(A hard + B 기록).
근거: ① 선택 키·규칙 값이라 되돌리기 쉽다 ② 20 §2.2(주 1 + 보조 ≤ 1, 전환은 암전 컷)·§12 관성 체크("장면 전환마다 같은 Stage 인지, 카메라 좌표가 연속인지")·05 §2(먼 이동은 암전 컷) ③ 실측: 두 실증 영상의 cut 은 t=0 하나라 A 기준 hard 0.
규칙 키 제안: `stage: {max_secondary: 1, continuity: {max_switches: 2}}`. ③ 은 shot_grammar.auto_transition 을 그대로 쓴다.

## 막히는 범위
- 기다리는 것: 작업 5(검사기·규칙 키·G3-17 열·합성 테스트)와 작업 4 의 숏 단위 키(쟁점 1).
- 계속하는 것: §0, 작업 1~3(Stage·MercatorStage·호출부 일반화), 작업 4 의 최상위 `stage` 키, 작업 6 회귀 측정 준비.

## §7 해당 여부
해당 없음.
