<!--
tier: 2
last_synced_with: v2.0.0
ssot_for: [prompt-intake_planner_user]
depends_on: [rules/video_rules.yaml, docs/handoff/15_ANTI_INERTIA_PRINCIPLES.md]
last_review: 2026-09-27
note: IntakePlannerWorker user prompt 템플릿 — 원본 workers/intake_planner_worker.py build_user_prompt (v2.0.0 파일 분리, 문안 개정은 Phase 6.9). 이 주석은 로더가 떼어 낸다.
-->
프로젝트 메타데이터
-------------------
project_id        : {project_id}
title             : {title}
category          : {category}
target_duration_min: {duration}
topic_summary     : {summary}

사용자 사전 제공 자료 (manual_user_provided 후보)
------------------------------------------------
{links}

카테고리별 가이드 (참고 baseline, 자유롭게 추가/조정 가능)
---------------------------------------------------------
{guidance}

지시
----
위 메타데이터를 바탕으로 IntakePlan JSON 을 생성하십시오.
- required_items 는 5~12개. 본 주제에 핵심적인 자료부터 우선.
- project_id, category, target_duration_min 은 위 값 그대로 사용.
- topic 은 title 보다 간결한 1줄 표현 (필요 시 title 그대로 사용).
- 사용자 사전 제공 자료가 있으면, 해당 자료로 충족되는 required_item 의
  default_mode 를 link_provide 로, why_needed 에 어떤 링크가 관련되는지
  명시. 단 사용자 제공 자료라도 사실 검증은 별도로 필요함을 전제로 한다.
- 출력은 JSON 한 객체. 자연어/설명/markdown fence 일체 금지.
