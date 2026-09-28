<!--
tier: 2
last_synced_with: v3.1.0
ssot_for: [prompt-revise_direction_user]
depends_on: [prompts/revise_direction.md, workers/revise_direction_worker.py]
last_review: 2026-09-28
note: ReviseDirectionWorker user prompt 템플릿 — 자리표시는 워커가 .replace() 로 채운다(C2). 이 주석은 로더가 떼어 낸다.
-->
직전 연출 (direction, JSON)
--------------------------
{direction}

시각 검수 판정 (qa_verdict)
--------------------------
{qa_verdict}

결정적 검사 (checks 요약)
------------------------
{checks}

문장 시각표 (sid · 장면 · 시작~끝 초 · 문장)
-------------------------------------------
{plan_table}

전면 카드 시각
-------------
{cards}

이 루프의 앞 회차 (판 → 지적 → 바꾼 것)
-------------------------------------
{history}

이벤트 필드 (타입별 — 필수는 *)
------------------------------
{event_fields}

지시
----
지적된 문제만 고친 연출 전체와 changelog 를 JSON 으로 출력하십시오.
