---
id: D-0255
from: user
to: opus
kind: gate_decision
responds_to: [R-0258]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 게이트 ① 승인 — showcase_econ 원고 v1(23문장, 커밋 edf97422)

사용자 원문(2026-10-28, 감독 세션 대화): **"승인해봐"** — 전달 자료 `projects/showcase_econ/gate1_view.txt`·`gate1_elements.md`. 수정 지시 없음 → 원고 그대로.

## Opus 할 일(순서, WORKFLOWS W0)
1. `python -m orchestrator.main approve --gate script_approval` (showcase_econ) — 승인 기록에 원고 지문, 사용자 원문 "승인해봐", 이 D 번호.
2. `script.plan`(표준 음성) → 미디어 등록(연준 Flickr PD 등재본·fed 기사 4건, 새 자산 없음) → 연출 B(`direction.yaml`, 시간축 한 세계 — D-0251 §6.1, gate1_elements 와 대조, `[chart-only-run]` 12초·`[chart-world-split]` hard 0) + 비교 구간 A(`direction.A.yaml`, D-0253 §2) → `audio.mix` → `engine.render --animatic`(B).
3. 콘티 판 R(progress): 경로·길이·hard·checks·미디어 요약, 30 MB 이하본(`-c:a copy`). A/B 시트는 게이트 ② 때(프리뷰와 함께).
4. geo 콘티 판이 먼저 나오면 먼저 보낸다. 둘 다 같은 R 에 묶지 않아도 된다.
