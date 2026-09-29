<!--
tier: 2
last_synced_with: v3.5.0
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

사실 목록 (facts.json — 문장 sources 에는 괄호 앞 claim_id 를 적는다. 괄호 안 = 검증 status)
-------------------------------------------------------------------------------------------
{facts}

{draft_block}{series_block}
지시
----
위 사실 목록으로 Script JSON 을 생성하십시오.
- 장면 수·길이는 자유. 목표 길이(target_duration_min)는 참고만 합니다.
- 각 문장의 sources 는 위 claim_id 만. 목록에 없는 id 는 거부됩니다. 숫자·날짜 문장은 sources 필수.
- 검증 라벨(<미검증> 등)은 쓰지 않습니다 — 시스템이 status 로 계산합니다.
  unverified claim 을 말하는 문장은 "~라고 주장했습니다/올렸습니다"처럼 귀속합니다.
- 출력은 JSON 한 객체. 자연어/설명/markdown fence 일체 금지.
