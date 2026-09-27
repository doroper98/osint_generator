<!--
tier: 2
last_synced_with: v2.0.0
ssot_for: [prompt-script_user]
depends_on: [rules/video_rules.yaml, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
note: ScriptWorker user prompt 템플릿 — 원본 workers/script_worker.py build_user_prompt (v2.0.0 파일 분리, 문안 개정은 Phase 6.9). 이 주석은 로더가 떼어 낸다.
-->
프로젝트 메타데이터
-------------------
project_id        : {project_id}
title             : {title}
topic             : {topic}
target_duration_min: {duration}

리서치 도시어 요약
------------------
{summary}

주장 목록 (claim_id 로 인용 — status/label 을 대본 라벨에 반영)
--------------------------------------------------------------
{claims}

지시
----
위 도시어를 바탕으로 FullScript JSON 을 생성하십시오.
- project_id, target_duration_min 은 위 값 그대로 사용.
- chapters 3~6개, 챕터당 segments 2~6개.
- 각 segment 의 claim_refs 는 위 주장 목록의 claim_id 만 인용.
- confirmed 가 아닌 claim 을 말하는 segment 는 label 에 해당 라벨을 박고
  단정적 표현을 피한다 (<미검증>/<추론>/<주장>/<반박됨>).
- 출력은 JSON 한 객체. 자연어/설명/markdown fence 일체 금지.
