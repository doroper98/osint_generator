<!--
tier: 2
last_synced_with: v3.3.0
ssot_for: [prompt-director_user]
depends_on: [prompts/director.md, workers/director_worker.py]
last_review: 2026-09-28
note: DirectorWorker user prompt 템플릿 — 자리표시는 워커가 .replace() 로 채운다(C2). 이 주석은 로더가 떼어 낸다.
-->
원고 (script.yaml)
------------------
{script_yaml}

문장 타이밍 (plan — sid · 장면 · 시작~끝 초 · 자막)
-----------------------------------------------
{plan_table}

엔티티 레지스트리 (뱃지 pid · flag · img)
--------------------------------------
{entities}

미디어 레지스트리 (mid · 종류 · 설명)
----------------------------------
{media}

지오 역량 (카메라가 갈 수 있는 범위)
------------------------------------
{geo}

이벤트 필드 (타입별 — 필수는 *)
------------------------------
{event_fields}

카메라 제안값 (engine.camera_suggest — 참고용, 강제 아님)
----------------------------------------------------
{camera_suggest}

지시
----
위 원고 전체를 연출하는 direction JSON 을 출력하십시오. 모든 장면(scene)을 다룬다.
카메라 제안값은 장소가 전부 화면에 들어오는 최소 폭과 전환(move/dip) 계산 결과다. 따를지·고칠지는 연출 의도로 정한다.
