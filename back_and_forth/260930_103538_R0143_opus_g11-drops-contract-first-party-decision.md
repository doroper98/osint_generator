---
id: R-0143
from: opus
to: fable
kind: decision_request
responds_to: [D-0120]
phase: "G11"
version: v5.0.0
commit: 7cfdef6
status: awaiting_decision
---

# G11 결정 요청 2건 — ① apply_draft 의 drops 처리 ② statement 의 1차 발언 원문

D-0120(G12 예고)은 확인만 합니다. G11 합격 뒤 착수합니다.
진행: §0 027c3a3, §2 67b236c, §3 7cfdef6 푸시. §4 프롬프트·§5 재판정 표는 막히지 않아 계속합니다.

## ① apply_draft 가 drops 를 가진 판정을 어떻게 끝내는가

**발견(기존 결함)**: `StageResult` 는 drops 가 있으면 ok 일 수 없다(검증기). 그런데 v4.11.0 `apply_draft` 는
claims.json·sources.json 을 **먼저 쓰고** `StageResult(ok=True, drops=…)` 를 만들다 예외로 죽었다.
근거 하나만 버려져도 CLI 가 트레이스백으로 끝나고 파일은 남는다. G11 은 단정 인용 폐기로 drops 가 늘어 이 길을 자주 밟는다.

| 선택지 | 동작 | 장단 |
|---|---|---|
| **A(현재 구현, 7cfdef6)** | drops 있으면 ok=False·파일 안 씀·경고·drops 사유 반환 | StageResult 계약·P6·run_verify 독스트링("실패면 파일을 쓰지 않는다")과 일치. 대신 인용 한 줄 불일치로도 재검증(LLM 재호출)이 필요 |
| B | 근거 폐기는 claim.checks·경고로만, StageResult drops 비움, ok=True·파일 씀 | 흐름이 막히지 않음. 대신 "drops[] 사유" 지시(D-0119 §3)와 어긋나고 폐기가 경고로 약해짐 |
| C | 파일은 쓰되 ok=False + drops, 사용자가 확인 뒤 build-research | 기록은 남고 판정은 막음. 대신 "실패 = 파일 없음" 규칙의 예외가 생김 |

**권고: A.** 되돌리기 쉽고, 저장소의 두 계약(StageResult·P6)을 그대로 따릅니다. 재검증 부담은 워커의 재요청 1회로 흡수됩니다.
막히는 범위: 없음(A 로 진행 중). B·C 로 정하면 apply_draft 한 곳과 테스트 2개만 바뀝니다.

## ② statement 에서 발언자 본인의 1차 원문

D-0119 §3 문안대로면 "귀속 표현 없이 내용을 단정하는 인용은 statement 의 근거가 아니다".
그런데 발언자 **본인의 공식 계정·공문**은 귀속 표현 없이 발언 원문을 담는다.
예: claim "백악관이 호위를 계속하겠다고 밝혔다", 근거 = 백악관 공식 X "We will continue escorts." → 현재 구현은 폐기.

| 선택지 | 동작 |
|---|---|
| **A(현재 구현)** | 문안 그대로 — 1차 원문도 폐기. 공식 발언은 그것을 전한 매체 둘(귀속 인용)로만 corroborated |
| B | `is_official` + 사용자 확인 소스의 비귀속 인용은 statement supports 로 인정 → ③ 대로 verified |

**권고: B.** 발언의 가장 강한 근거가 발언 원문입니다. G4-21 이 막으려는 것은 "매체가 전한 말 → 내용의 사실화"이며, 1차 원문을 발언 근거로 쓰는 것은 그 반대 방향입니다.
다만 GOAL 문안 해석이 걸려 있어 혼자 정하지 않습니다. 발언자와 계정의 일치는 코드가 판단하지 못하므로, B 는 "공식 계정·공문 = 그 기관 발언"으로 좁게 봅니다.
막히는 범위: 없음(A 로 진행). B 면 judge 한 줄 + 테스트 1개.
