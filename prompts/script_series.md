<!--
tier: 2
last_synced_with: v5.17.0
ssot_for: [prompt-script_series]
depends_on: [prompts/script_user.md, workers/script_worker.py, script/series_refs.py]
last_review: 2026-09-29
note: ScriptWorker 데이터 레코드 블록(v4.4.0, back_and_forth D-0090 작업 1) — 주문(order.yaml data.series)이 있을 때만 {series_block} 에 들어간다. 이 주석은 로더가 떼어 낸다.
-->
데이터 레코드 (order.yaml — 문장 sources 에 series:<id> 로 인용한다. 자막 수치는 레코드 값 그대로, 코드가 대조한다)
-----------------------------------------------------------------------------------------------
{records}

