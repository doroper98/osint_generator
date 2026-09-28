<!--
tier: 2
last_synced_with: v3.2.0
ssot_for: [prompt-research_user]
depends_on: [rules/video_rules.yaml, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
note: ResearchWorker user prompt 템플릿 (v3.2.0 — claims.json → Facts). 이 주석은 로더가 떼어 낸다.
-->
프로젝트 메타데이터
-------------------
project_id        : {project_id}
title             : {title}
category          : {category}
target_duration_min: {duration}
topic_summary     : {summary}

소스 (intake/sources.json — 참고용, 인용은 claim_id 로)
-------------------------------------------------------
{sources}

주장 목록 (intake/claims.json — status 는 코드가 원문 대조로 정했다)
-------------------------------------------------------------------
{claims}

지시
----
위 주장 목록으로 Facts JSON 을 만드십시오.
- source_ids 는 위 claim_id 만. contested claim 을 인용하면 contested + sides.
- 출력은 JSON 한 객체. 자연어/설명/markdown fence 일체 금지.
