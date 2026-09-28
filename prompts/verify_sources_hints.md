<!--
tier: 2
last_synced_with: v3.5.0
ssot_for: [prompt-verify_sources_hints]
depends_on: [prompts/verify_sources_user.md, workers/verify_sources_worker.py, bundle/to_sources.py]
last_review: 2026-09-29
note: VerifySourcesWorker user prompt 의 선택 블록 `{bundle_hints}` — intake/bundle_claims.json 이 있을 때만 들어간다(D-0064 쟁점 3). 자리표시 {hints} 는 워커가 .replace() 로 채운다(C2). 이 주석은 로더가 떼어 낸다.
-->
번들이 제시한 주장 후보 (참고 — 후보일 뿐이다)
----------------------------------------------
아래는 분석 번들(2차 자료)이 내세운 주장·논쟁이다. 검증된 사실이 아니다.
- 위 소스 본문에서 그대로 인용할 근거가 있을 때만 claim 후보로 옮긴다. 인용이 소스 본문에 없으면 버린다.
- 논쟁 후보는 양측 입장을 sides 로 같은 무게로 적는다. 한쪽 근거만 있으면 그쪽만 인용하고 contested 로 둔다.
- 후보 문장을 그대로 베끼지 말고, 소스가 실제로 말한 범위로 좁혀 쓴다.

{hints}
