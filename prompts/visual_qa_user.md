<!--
tier: 2
last_synced_with: v3.1.0
ssot_for: [prompt-visual_qa_user]
depends_on: [prompts/visual_qa.md, workers/visual_qa_worker.py]
last_review: 2026-09-28
note: VisualQAWorker user prompt 템플릿 — 자리표시는 워커가 .replace() 로 채운다(C2). 이미지는 파일 경로로 첨부(17 §4.1). 이 주석은 로더가 떼어 낸다.
-->
첨부 이미지
-----------
{images}

컷별 정보 (prev/frames.json — 번호·파일·시각·문장·떠 있는 요소)
-------------------------------------------------------------
{frames}

결정적 검사 요약 (prev/checks.json)
----------------------------------
{checks}

지시
----
첨부 이미지를 직접 열어 보고 판정 JSON 을 출력하십시오.
