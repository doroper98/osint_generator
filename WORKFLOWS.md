<!--
tier: 3
last_synced_with: v0.2.1
ssot_for: [execution-procedures]
depends_on: [README.md, docs/15_OPERATIONS_RUNBOOK.md]
last_review: 2026-05-19
-->

# WORKFLOWS

본 문서는 실제 운영 절차를 정리합니다. 새 절차가 정착되면 본 문서로 들어옵니다.

---

## W1. 신규 영상 프로젝트 생성

```bash
# 1) 프로젝트 생성
python -m orchestrator.main new-project \
  --title "러시아 본토 피격 18분 영상" \
  --category war_military \
  --duration-min 18

# 2) Command Center 진입
python -m orchestrator.main command-center --project {project_id}
```

생성 직후 상태는 `state=intake_planning`이며 `intake_plan.json`이 비동기 생성됩니다.

## W2. Command Center 진입 (이미 존재하는 프로젝트)

```bash
run_pipeline.bat
# 또는
python -m orchestrator.main command-center --project {project_id}
```

화면 구성:
- 왼쪽 상단: Orch CLI Log Panel
- 왼쪽 하단: Job Dashboard Panel
- 오른쪽: Worker Slot 1–4 Panel

키보드 단축키 (Phase 1 기준):
- `q`: 종료
- `r`: 새로고침
- `1~4`: 해당 Worker Slot 포커스
- `s`: 현재 상태를 `worker_slots.json`에 강제 저장

## W3. Worker 추가

1. `workers/{name}_worker.py` 생성, `BaseWorker` 상속.
2. `agents_reviewer` 컨벤션에 맞춰 type hint + Pydantic 모델 사용.
3. `docs/03_AGENT_ARCHITECTURE.md`의 Worker 카탈로그 표에 한 줄 추가.
4. `docs/CATALOGS.md`에도 같은 줄 동기화 (SSOT 위반 아님: 003은 상세, CATALOGS는 목록).
5. `tests/workers/test_{name}_worker.py` 작성.
6. 새 Worker가 만드는 task_type을 `schemas/models.py:TaskType` Literal에 추가.
7. CHANGELOG `Added` 섹션에 기록.

## W4. Antipattern 기록

1. 사고 / 오류 발생 시 즉시 재현 절차 확보.
2. 카테고리 결정 (`TTS-AP`, `PIPELINE-AP`, `RIGHTS-AP`, `RENDER-AP`, `SCHEMA-AP`).
3. `docs/ANTIPATTERNS/{CAT}_ANTIPATTERNS.md` 끝에 새 N번 append.
4. 같은 클래스의 재발을 막는 구조적 조치 (검증기·테스트·hook) 추가.
5. `DEVLOG.md`에 한 줄 요약 + AP 번호.

## W5. 커밋

```bash
# 매 변경 후
python -m py_compile $(git diff --cached --name-only | grep '\.py$')

# 버전 prefix 일치 검증 (자동, .githooks/commit-msg)
git commit -m "v0.2.0: Phase 2 — project manager and state machine"
```

`__version__`은 `orchestrator/__init__.py`에서 관리합니다.

## W6. Review Gate 통과 처리

```bash
# Review Dashboard에서 승인하거나 CLI로 직접 기록
python -m orchestrator.main approve \
  --project {project_id} \
  --gate script_review \
  --comment "OK. scene_0034만 출처 표기 보강 요청"
```

기록 위치: `projects/{project_id}/logs/approvals/approval_log.json`

## W7. Phase 완료 체크리스트

- [ ] Phase별 acceptance criteria 모두 통과
- [ ] `python -m py_compile` 전수 통과
- [ ] 새 Antipattern 발견 시 모두 카탈로그에 기록
- [ ] CHANGELOG `Unreleased` → 신규 버전 섹션으로 승격
- [ ] MINOR 또는 PATCH 버전 증분
- [ ] `last_synced_with` 모든 Tier 1·2 헤더 일괄 업데이트
- [ ] DEVLOG에 Phase 회고 1엔트리 추가
