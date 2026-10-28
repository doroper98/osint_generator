---
id: D-0254
from: user
to: opus
kind: gate_decision
responds_to: [R-0257]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 게이트 ① 승인 — showcase_geo 원고 v1(39문장, 커밋 c9522d46)

사용자 원문(2026-10-28, 감독 세션 대화): **"승인"** — 전달 자료 `projects/showcase_geo/gate1_view.txt`(원고 전문·출처 표·린트·미디어 계획)·`gate1_elements.md`(막별 요소·미포함 3건). 감독이 덧붙인 메모("자료 장으로" 제작 용어)에 대한 수정 지시는 없음 → 원고 그대로.

## Opus 할 일(순서, WORKFLOWS W0)
1. `python -m orchestrator.main approve --gate script_approval` (showcase_geo) — 승인 기록에 원고 지문(script_sha1 = c9522d46 의 script.yaml). 기록에 사용자 원문 "승인" 과 이 D 번호를 남긴다.
2. `python -m script.plan projects/showcase_geo`(표준 음성, 묻지 않는다) → 미디어 등록(article_register·media_fetch — 등재본 재사용, 새 자산 없음 → `asset_library.py check` = 0) → 연출(`ai_direction_run`, 기준 문법 = diesel v2, 카탈로그 요소 계획 gate1_elements.md 와 대조) → `python -m audio.mix` → `python -m engine.render projects/showcase_geo --animatic`.
3. 콘티 판이 나오면 R(progress)에 경로·길이·hard 수·checks 요약·미디어 요약을 적고 send_message. 감독이 사용자에게 보낸다. 콘티 판은 30 MB 이하 재인코딩본도 함께(`-c:a copy`).
4. 병행: showcase_econ 원고(D-0253 X) → 게이트 ① 자료 → R.
