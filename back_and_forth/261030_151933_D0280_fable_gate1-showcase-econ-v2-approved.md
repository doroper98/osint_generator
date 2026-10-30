---
id: D-0280
from: user
to: opus
kind: gate_decision
responds_to: [R-0283]
phase: "E0"
version: v7.4.0
status: open
priority: urgent
---

# 게이트 ① 재승인 — showcase_econ 원고 v2(발언 자리 2곳, 커밋 4ce2896c)

사용자 원문(2026-10-30, 감독 세션 대화): **"승인. 그리고 만들어진 샘플들은 바로바로 보여줘"** — 전달 자료 `projects/showcase_econ/gate1_v2_changes.md`·`gate1_view_v2.txt`. 수정 지시 없음 → 원고 v2 그대로.
두 번째 문장은 작업 순서 의견 → `rules/user_feedback.yaml` **UF-144**(장치: FABLE_HANDOFF §6 "샘플·시트·콘티 판은 만들어지는 즉시 사용자에게 보낸다" — 감독은 R 이 오면 모아 두지 않고 그 자리에서 전달).

## Opus 할 일(순서, WORKFLOWS W0 — D-0255 와 같다)
1. `python -m orchestrator.main approve --gate script_approval`(showcase_econ, 원고 v2 지문) — 승인 기록에 사용자 원문 "승인."·이 D 번호.
2. `script.plan` v2(표준 음성 C0.2 — 묻지 않는다) → 미디어 등록(연준 클립 넷 D-0275·사진 12·기사 4·초상) → 연출(preview_v10 의 direction §1 그대로 + 발언 자리 2곳 `clip_frame main` 원음·번역 자막 hold, 현장 broll, 핀 on series) → `audio.mix`(클립 트랙·덕킹 D-0276) → `engine.render --animatic`.
3. 콘티 판 v3 R(progress): 경로·md5·길이·hard·checks·미디어 요약·발언 구간 두 곳의 시각, 30 MB 이하본(`-c:a copy`). **artifacts 에 올리는 즉시 R** — 감독이 바로 사용자에게 보낸다(UF-144). geo 콘티 판 v2 가 먼저면 먼저.
4. 프리뷰 시트(게이트 ② 자료)도 나오는 대로 따로 R — 묶어 기다리지 않는다.
