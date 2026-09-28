<!--
tier: 2
last_synced_with: v3.5.0
ssot_for: [prompt-script_draft]
depends_on: [prompts/script_user.md, workers/script_worker.py, bundle/to_script.py]
last_review: 2026-09-29
note: ScriptWorker user prompt 의 선택 블록 `{draft_block}` — 프로젝트에 script.draft.yaml(번들 어댑터 초안)이 있을 때만 들어간다(D-0064 쟁점 4). 자리표시 {draft} 는 워커가 .replace() 로 채운다(C2). 이 주석은 로더가 떼어 낸다.
-->
원고 초안 (script.draft.yaml — 분석 번들에서 만든 재료. 최종 원고가 아니다)
-----------------------------------------------------------------------------
아래 초안을 다듬어 Script 를 만드십시오.
- 장면 구성은 초안을 출발점으로 삼되 고쳐도 됩니다(합치기·나누기·순서). 섹션 제목(챕터명 후보)은 화면 문장이 아닙니다.
- `# rewrite_required: true` 가 붙은 문장은 금지 문구에 걸린 문장입니다. 뜻은 살리고 금지 문구 없이 다시 쓰십시오.
- 사실은 위 사실 목록(facts)에 있는 것만 씁니다. 사실 목록에 근거가 없는 초안 문장은 빼거나 귀속 표현으로 바꾸십시오.
- sources 는 초안에 비어 있습니다. 위 claim_id 로 채우십시오.
- `date_source: timeline` 표시가 없는 문장의 날짜는 번들 발행일(사건일 아님)입니다. facts 의 날짜로 바로잡으십시오.
- 발음 텍스트(tts)는 숫자·기호 없이 다시 확인하십시오.

```text
{draft}
```
