<!--
tier: 3
last_synced_with: v0.2.2
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
- [ ] **Codex Cloud 코드 리뷰 통과** (W8 참조). 사용자가 실행, AI 는 push 후 사용자에게 "Codex 리뷰 돌려주세요" 안내. 의도적 보류 시 사유를 DEVLOG 에 명시.

## W8. Codex Cloud 코드 리뷰

본 저장소는 Phase / PATCH 완료 직전 단계로 **Codex Cloud** (chatgpt.com/codex) 리뷰를 거칩니다.
Claude Code (이 세션) 가 push 한 직후 사용자가 수동으로 실행합니다.

### 흐름

1. **AI 가 push**: 작업 브랜치에 커밋 push. 사용자에게 "Codex Cloud 에서 `{branch}` 리뷰해 주세요" 한 줄 안내.
2. **사용자가 Codex Cloud 실행**:
   - chatgpt.com/codex 진입 → 본 저장소 (`doroper98/osint_generator`) 의 작업 브랜치를 가리킴.
   - 아래 권장 프롬프트로 리뷰 요청.
3. **사용자가 결과 전달**: Codex 의 코멘트 / suggested diff 를 그대로 본 세션에 붙여넣음.
4. **AI 가 반영**: 같은 버전 안에서 PATCH 추가 commit, 또는 다음 PATCH 로 묶음.
5. **재리뷰**: 큰 수정 후엔 1 회 더 Codex 리뷰. 사소한 수정이면 생략 가능.

### 권장 프롬프트

```
이 브랜치 (diff) 를 코드 리뷰해줘. 다음 기준을 함께 확인:
1. CLAUDE.md 규칙 위반: Python 3.11+ 타입 힌트 누락, Pydantic v2 BaseModel 미사용,
   .format() 사용 (.replace() 만 허용), schema_version 누락.
2. Worker 규칙: 사용자 stdin 질문, 다른 Worker 산출물 수정, task_result.json
   누락, stdout 1줄 1이벤트 위반.
3. 상태 머신 우회: ALLOWED_TRANSITIONS 표를 거치지 않고 ProjectManifest.current_state
   직접 대입.
4. 보안: 하드코딩된 키·토큰, .env / credentials.json 커밋 흔적.
5. SemVer / 버전 표기: VERSION 일관성, last_synced_with 누락, schema_version 증분 규칙.
6. 일반 코드 품질: dead code, 미사용 import, 명백한 버그.
```

### 의도적 보류 사유 (예시)

- "Hotfix urgency, post-merge review" — 우선순위로 머지 후 다음 PATCH 에서 처리.
- "Docs-only change, no executable code" — 코드 변경 없음.

이 경우 DEVLOG 의 "결과" 절에 `Codex 리뷰: 보류 ({사유})` 한 줄 남깁니다.
