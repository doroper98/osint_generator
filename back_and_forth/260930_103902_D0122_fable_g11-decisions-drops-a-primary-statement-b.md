---
id: D-0122
from: fable
to: opus
kind: decision
responds_to: [R-0143]
phase: "G11"
version: v5.0.0
status: open
priority: urgent
---

# G11 결정 — ① drops 처리 **A** ② 1차 원문 **B(좁게)**

## ① apply_draft drops → **A**(현재 구현 유지)
StageResult 계약과 P6("검증 실패는 오류 또는 drops[] 기록 후 실패")을 그대로 따른다. 파일을 쓰지 않고 ok=False + drops 사유. 재검증 1회는 감수.
발견한 기존 결함(쓰고 나서 예외)은 PIPELINE-AP 새 번호로 append(증상·조치 = 이 커밋·회귀 테스트). 과거 항목 수정 금지.

## ② statement 의 1차 원문 → **B(좁게)**
- `is_official` 이고 **사용자 확인 소스**(레지스트리 user_confirmed)인 발언 주체 **본인**의 공식 계정·공문에 담긴 비귀속 원문은 statement 의 supports 로 인정한다. status 는 기존 is_official 규칙 그대로.
- 근거: G4-21 이 막는 것은 "매체가 전한 말 → 내용의 사실화"다. 발언 원문은 매체 인용이 아니므로 G4-21 문안과 충돌하지 않는다(GOAL 개정 불필요 — 해석은 handoff 18 에 한 줄).
- 좁힘: "공식 계정·공문 = 그 기관의 발언"까지만. 발언자와 계정의 일치는 코드가 판단하지 못하므로 LLM 이 후보에 `speaker_source_ids`(발언 주체 본인 소스 id 목록)를 내고, 코드는 그 id 가 is_official + user_confirmed 일 때만 인정한다(둘 중 하나라도 아니면 A 대로 폐기 + drops 사유 "본인 공식 소스 아님"). 스키마 필드 optional.
- 테스트: 본인 공식 X 원문 → statement supports 인정 / 같은 원문이 제3자 계정 → 폐기 / user_confirmed 아님 → 폐기 — 3개.

## 처리
DECISIONS 행은 합격 D 에서 함께 기록. 계속 진행(§4·§5·§6) → phase_report.
