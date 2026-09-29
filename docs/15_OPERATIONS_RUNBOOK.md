<!--
tier: 2
last_synced_with: v4.8.0
ssot_for: [operations-runbook]
depends_on: [../WORKFLOWS.md, 02_SYSTEM_ARCHITECTURE.md]
last_review: 2026-09-29
-->

# 15 — Operations Runbook

## 1. 일상 운영

| 작업 | 명령 |
|---|---|
| Command Center 진입 | `run_pipeline.bat` 또는 `python -m orchestrator.main command-center --project {pid}` |
| 새 프로젝트 | `python -m orchestrator.main new-project {pid} --title "..." --category ... --topic-summary "..."` |
| 다음 단계 진행 | `python -m orchestrator.main advance --project {pid}` (엔진 상태는 engine_service 로 CLI 실행) |
| 게이트 화면 | `python -m orchestrator.main gate-view --project {pid}` |
| 승인·반려 | `python -m orchestrator.main approve --project {pid} --gate script_approval\|preview_approval --comment "..." [--version N]` / `reject …` |
| 단일 Worker 실행 | `python -m workers.{worker_name} --project-id {pid} --task-id {tid}` |
| 로그 확인 | `logs/orchestrator.log`, `projects/{pid}/logs/workers/{task_id}.log` |

## 2. 장애 대응

### 2.1 Worker subprocess가 행(hang) 되었다

1. Job Dashboard에서 `stale` 상태 확인.
2. `worker_slots.json`에서 해당 slot의 pid 확인.
3. `taskkill /PID {pid}` (Windows) 또는 `kill {pid}`.
4. Orchestrator가 자동 재배정 (`status=queued`로 되돌림).
5. PIPELINE-AP에 패턴 기록.

### 2.2 Pydantic 검증 실패

1. 에러 메시지에서 어느 필드인지 확인.
2. 입력 JSON을 `python -m json.tool` 으로 검사.
3. SCHEMA-AP에 패턴 기록.
4. 필요 시 schema_version 증분.

### 2.3 엔진 렌더 실패

1. 엔진 CLI 마지막 줄 `StageResult`(ok·errors·drops)와 표준 오류 로그를 본다. 오케스트레이터는 `logs/stages/` 에 전체 결과를 남긴다.
2. 글꼴 없음(`FontMissingError`) → `python tools/fetch_data.py fonts`. 지형 티어 없음 → `python -m geo.prep <proj> [--res 1080p]`.
3. 청크 하나만 실패했으면 그 구간만 다시 렌더한다(handoff 11 §3.1). **긴 렌더·AI 연출 중에는 같은 워크트리의 코드·규칙을 바꾸지 않는다**(PIPELINE-AP, Phase 10 운영 기록).
4. RENDER-AP에 패턴 기록.

### 2.4 발음이 같은 단어에서 반복해서 틀린다

1. 원고의 발음 텍스트(`tts`)를 고친다. 규칙으로 막을 수 있으면 `rules/video_rules.yaml tts_rules`·`tts_risk` 개정(사람 승인, 15 P11).
2. `python -m script.plan <proj> --tts …` 로 다시 합성(캐시 키가 달라진다).
3. TTS-AP에 패턴 기록.

### 2.5 모서리 요소·도장·비네팅이 영상에 보인다 (사고)

1. **즉시 영상 격리**. 업로드 중지.
2. 프리뷰 `prev/checks.json` 의 `forbidden` 항목 확인(결정적 검사가 놓쳤다면 검사기 구멍 — 15 P6).
3. RENDER-AP에 패턴 기록하고 검사기를 고친다.

## 3. 백업

- `projects/` 폴더는 git에서 ignore.
- 별도 외부 백업 권장 (NAS / S3 / Drive).

## 4. 의존성 업데이트

- Python 패키지: `requirements.txt` 변경 → `pip install -r requirements.txt`.
- 엔진 패키지: `requirements-engine.txt` 변경 → `pip install -r requirements-engine.txt`. 시스템: ffmpeg·fontconfig·fonts-noto-cjk.
- 업데이트 후 `python -m py_compile` 전수 검사.

## 5. 비밀 정보

- `.env`에 키 저장. 절대 커밋 금지.
- `.env.example`을 유지하여 키 이름만 노출.

## 6. 모니터링 (Phase 후속)

- `logs/orchestrator.log` 회전 정책: 일 단위, 30일 보관.
- 매 Phase 완료 시 평균 task duration, 실패율 측정.

## 7. 운영자 의무

- 매주 Antipattern 카탈로그 1회 리뷰.
- 매 영상 완료 시 DEVLOG에 1엔트리 추가.
- 새 외부 의존성 추가 시 라이선스 확인.
