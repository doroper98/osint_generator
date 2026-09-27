<!--
tier: 2
last_synced_with: v2.0.0
ssot_for: [prompt-research_user]
depends_on: [rules/video_rules.yaml, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
note: ResearchWorker user prompt 템플릿 — 원본 workers/research_worker.py build_user_prompt (v2.0.0 파일 분리, 문안 개정은 Phase 6.9). 이 주석은 로더가 떼어 낸다.
-->
프로젝트 메타데이터
-------------------
project_id        : {project_id}
title             : {title}
category          : {category}
target_duration_min: {duration}
topic_summary     : {summary}

사용 가능 소스 (source_registry — 인용 시 source_id 사용)
--------------------------------------------------------
{sources}

리서치 시드 (사용자 사전 제공 = 2차/파생 분석, 사실 앵커 아님)
-------------------------------------------------------------
{seeds}

지시
----
위 소스와 시드를 바탕으로 ResearchDossier JSON 을 생성하십시오.
- project_id, topic 은 위 메타데이터 기준.
- claims 는 8~25개. 본 주제의 핵심 사실부터 우선.
- evidence.source_id 는 위 source_registry 에 실제 존재하는 값만 인용.
- 시드(seed) 만 근거인 주장은 status 를 confirmed 로 두지 말고 claim/unverified
  로 분류하고, 1차 출처로 별도 검증이 필요함을 notes 에 명시.
- 미확인/반박/추론 항목은 status 로 구분 (<미검증>/<반박됨>/<추론> 라벨 대상).
- 출력은 JSON 한 객체. 자연어/설명/markdown fence 일체 금지.
