<!--
tier: 2
last_synced_with: v3.2.0
ssot_for: [prompt-capture_read_user]
depends_on: [prompts/capture_read.md, workers/capture_read_worker.py]
last_review: 2026-09-28
note: CaptureReadWorker user prompt 템플릿 — 자리표시는 워커가 .replace() 로 채운다(C2). 이미지는 파일 경로로 첨부. 이 주석은 로더가 떼어 낸다.
-->
첨부 이미지
-----------
{images}

소스 id: {source_id}

사용자 메모(참고만 — 이미지에 보이는 것이 우선이다)
-------------------------------------------------
{user_note}

위 캡처 한 장을 읽어 JSON 하나로 출력하라.
