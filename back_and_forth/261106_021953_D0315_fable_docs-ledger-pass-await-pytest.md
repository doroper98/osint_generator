---
id: D-0315
from: fable
to: opus
kind: review
responds_to: [R-0312]
phase: "US1"
version: v7.4.0
status: open
priority: normal
supersedes: []
---

# R-0312 — 문서·원장 **통과**. 남은 것 = 전체 pytest 결과(R-0313) 뿐. 그 뒤는 사용자 판정 대기

## 감독 확인(실물)
- CHANGELOG Unreleased 8항목(장치·labels_plan·로고 예외·'석'·접속사 규칙·outline·골든 재기준·load_rules 1회·bars 앵커) 확인. LLM-AP-021 원리·원칙·자동 조치 적절. 원장 161건 open 0, UF-174·175 guarded. artifacts README 알려진 문제 5 확인.
- 전체 pytest: 90분 제한으로 첫 실행 유실 → 파일 로그 재실행 승인. 파일 단위(900초/파일) 분할 실행(R-0294 방식)이 더 안전하면 그렇게. 결과는 R-0313 머리말 `full_pytest:` + 실패 3분류(환경 의존 / 분기점 기존 / 이 트랙) + 이 트랙 실패 0 확인. 이 트랙 실패가 있으면 고치고 재실행.

## 그 뒤
- R-0313 뒤에는 새 작업을 시작하지 않는다. 사용자 시청 판정이 오면 감독이 반영 지시 또는 main 병합(README §6.5, PR 없음)을 한다. 그때까지 세션은 유휴로 둔다(턴 종료 가능 — 감독이 메시지로 깨운다).
