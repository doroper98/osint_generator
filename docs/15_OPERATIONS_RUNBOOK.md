<!--
tier: 2
last_synced_with: v0.1.1
ssot_for: [operations-runbook]
depends_on: [../WORKFLOWS.md, 02_SYSTEM_ARCHITECTURE.md]
last_review: 2026-05-19
-->

# 15 — Operations Runbook

## 1. 일상 운영

| 작업 | 명령 |
|---|---|
| Command Center 진입 | `run_pipeline.bat` 또는 `python -m orchestrator.main command-center --project {pid}` |
| 새 프로젝트 | `python -m orchestrator.main new-project --title "..." --category ... --duration-min 18` |
| 단일 Worker 실행 | `python -m workers.{worker_name} --project-id {pid} --task-id {tid}` |
| 승인 기록 | `python -m orchestrator.main approve --project {pid} --gate {gate_id} --comment "..."` |
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

### 2.3 Remotion 렌더 실패

1. `render_report.json`의 `stderr_tail` 확인.
2. Node 버전 (`node -v`) 20 LTS인지 확인.
3. Remotion 캐시 청소: `npx remotion clean`.
4. RENDER-AP에 패턴 기록.

### 2.4 TTS QA가 같은 단어에서 반복 실패

1. `pronunciation_ko.yaml`에 항목 추가.
2. 해당 segment 재생성.
3. TTS-AP에 패턴 기록.

### 2.5 `final.mp4`에 Debug Layer가 보인다 (사고)

1. **즉시 영상 격리**. 업로드 중지.
2. RENDER-AP에 패턴 기록.
3. Render Worker의 `render_mode=final` 분기 점검.
4. CI 검사기 추가 (Phase 9 후속).

## 3. 백업

- `projects/` 폴더는 git에서 ignore.
- 별도 외부 백업 권장 (NAS / S3 / Drive).

## 4. 의존성 업데이트

- Python 패키지: `requirements.txt` 변경 → `pip install -r requirements.txt`.
- Node 패키지: `remotion/package.json` 변경 → `npm install`.
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
