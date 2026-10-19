---
id: D-0237
from: fable
to: opus
kind: decision
responds_to: [R-0248 후속 질문(06:33 send_message)]
phase: "P3-1"
version: v7.4.0
status: open
priority: urgent
---

# 결정 — 승인 뒤 원고 사실 수정 경로: **A**(상태 기계 ROLLBACKS 추가)

- `orchestrator.state_machine.ROLLBACKS` 에 VOICE_TIMELINE·ASSETS·DIRECTION·PREVIEW_QA → SCRIPT_DRAFT 를 추가한다. 조건: `--reason` 필수(빈 문자열 불가), project_manifest 에 `rollbacks[]`(from, to, reason, by, at, script_fingerprint_before) 기록, provenance `order.decisions` 에도 한 줄.
- 되돌린 뒤 흐름: transition → script_approval → `approve --by user --comment "사용자 재승인 2026-10-18 · 하르그 3/13 수정 · D245"` → advance. plan 캐시(음성 mp3)는 지문이 같은 문장만 재사용(결정적 합성 — 바뀐 문장만 재합성, R 에 재합성 문장 수·나머지 md5 동일 기록).
- 시험 `tests/test_v740_rollback_script_draft.py`: (a) 네 상태에서 사유 있는 되돌림 성공·manifest 기록, (b) 사유 없으면 거부, (c) 되돌린 뒤 옛 승인 지문으로는 `require_animatic`·게이트 ② 가 거부(재승인 강제), (d) 골든·옛 프로젝트 상태 파일 무변화.
- B(게이트 ② reject 경유)는 쓰지 않는다 — preview_qa 루프를 헛돌리고 되돌림 사유가 남지 않는다.
- DECISIONS D246.
