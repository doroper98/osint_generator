<!--
tier: 1
last_synced_with: v0.2.2
ssot_for: [session-handoff]
depends_on: [CLAUDE.md, GOAL.md, VERSION, docs/13_IMPLEMENTATION_ROADMAP.md]
last_review: 2026-05-20
-->

# HANDOFF — 다음 세션 AI 인계 문서

본 문서는 **다음 Claude Code 세션이 작업을 이어받을 때 가장 먼저 읽어야 할 문서**입니다.
짧고 행동 지향적으로 유지합니다. 과거 항목은 `DEVLOG.md` 가, 미래 항목은 `docs/13_IMPLEMENTATION_ROADMAP.md` 가 정식 SSOT 입니다.

---

## 0. 너의 역할

너는 OSINT 영상 자동 생성 시스템을 단계별로 구축하는 본인 사용자의 페어 프로그래머다.
사용자는 한국어로 대화하며, **버전(vX.Y.Z) 중심으로 소통**한다.
모든 작업 규칙은 `CLAUDE.md` 에 정의되어 있다. **반드시 먼저 정독하라.**

핵심 원칙:

1. **단순함을 우선**. 만들지 않아도 되는 추상화는 만들지 마라.
2. **버전 표기 의무**. 모든 산출물에 버전 박기 (C5).
3. **append-only 카탈로그**. Antipatterns / CHANGELOG / DEVLOG 는 과거 항목 수정 금지.
4. **Worker 는 사용자에게 질문하지 않는다**. 판단이 필요하면 `status="needs_user_confirmation"`.
5. **사용자가 명시적으로 요청하지 않은 PR 생성 금지**.

---

## 1. 지금 어디까지 와 있나 (v0.2.1 기준)

### 완료된 Phase

| Phase | 버전 | 무엇 | 검증 |
|---|---|---|---|
| Phase 0: Governance | v0.1.0 | 저장소 구조, CLAUDE.md, GOAL.md, 16개 docs, 3개 ADDENDUM, Antipatterns, .githooks | commit-msg hook 통과 |
| Phase 1: Command Center MVP | v0.1.0 | Textual TUI (좌상단 Orch CLI Log, 좌하단 Job Dashboard, 우측 Worker Slot 1–4), WorkerSlotManager, dummy worker × 4 종료 코드 모두 검증 | `python -m py_compile`, smoke test, 6 tasks 병렬 실행 |
| 호스팅 / 인증 | v0.1.1 | Vercel 정적 호스팅 셋업, PAT 인증 다이얼로그, default branch `main` 통합 | 사용자 측 Vercel 연결 완료 |
| 호스팅 hotfix | v0.1.2 | Vercel 루트 URL 404 수정 (`docs/index.html` 추가) | 사용자 측 재배포 확인 |
| 브랜치 뷰어 그래프화 | v0.1.3 | `@gitgraph/js` 라이브러리로 진짜 git 토폴로지 SVG 그래프 렌더링 | 사용자 시각 확인 |
| 한글 라벨 + 분기 검증 | v0.1.4 | `COMMIT_DESCRIPTIONS` 한글 override, `BRANCH_PRIORITY` 정렬, `test/graph-demo` 분기 시연 | 사용자 스크린샷 확인 |
| 검증 정리 | v0.1.5 | `test/graph-demo` 삭제 + dead code 청소 | 원격 브랜치 목록 2개로 복귀 |
| Phase 2: Project Manager / State Machine | v0.2.0 | `project_manager.py` + `state_machine.py` 신설, `new-project / resume / transition` CLI, `state_history` 감사 로그, 24-state 선형 전이표 + ARCHIVED 어디서든 도달 | smoke test 9개 시나리오, CLI 종단 테스트, `python -m py_compile` 통과 |
| Phase 2 마무리 | v0.2.1 | `SCHEMA-AP` 안티패턴 카탈로그 신설 (SCHEMA-AP-001 — 임의 상태 점프 / self-loop), TUI Job Dashboard 가 매 tick 마다 manifest 재로딩 (외부 `transition` 후 라이브 반영) | TUI reload 시뮬레이션 검증, `python -m py_compile` 통과 |

### 핵심 산출물

- 라이브 사이트: <https://osint-generator.vercel.app/> (PAT 필요, Private 저장소)
- TUI 진입: `python -m orchestrator.main command-center --project demo` 또는 `run_pipeline.bat`
- 새 프로젝트: `python -m orchestrator.main new-project {pid} --category {cat} [--title ...]`
- 재개: `python -m orchestrator.main resume {pid}`
- 상태 전이: `python -m orchestrator.main transition {pid} --to {state} [--reason ...]`
- 더미 워커: `workers/dummy_worker.py`
- Phase 2 산출물: `orchestrator/project_manager.py`, `orchestrator/state_machine.py`

### 인프라 상태

- **default branch**: `main` (모든 푸시는 여기로)
- **Vercel**: `main` 푸시마다 자동 재배포. `osint-generator.vercel.app` 안정 도메인.
- **GitHub**: doroper98/osint_generator, Private. PAT 인증으로 브랜치 뷰어 접근.

### 알려진 antipattern 카탈로그

- `docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md` — TTS-AP-001 ~ TTS-AP-053
- `docs/ANTIPATTERNS/PIPELINE_ANTIPATTERNS.md` — PIPELINE-AP-001 ~ PIPELINE-AP-006
- `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` — SCHEMA-AP-001 (Phase 2 신설)

**문제 발생 시 반드시 이 카탈로그를 먼저 검색.** 중복 발견 시 동일 번호에 `[superseded by ...]` 마킹만, 새로 발견 시 다음 번호로 append.

---

## 2. 다음 작업 — Phase 3 (v0.3.0 예상)

### 목표: Dynamic Intake Page

사용자가 주제를 입력하면, Dynamic Intake Planner Agent 가 그 주제에 필요한
정보 항목을 동적으로 생성하고, 웹 페이지에서 사용자가 항목별로 입력 방식을 선택해
제출할 수 있게 한다.

**Roadmap 출처**: `docs/13_IMPLEMENTATION_ROADMAP.md` Phase 3 절을 정식 SSOT 로 따른다.
**스펙 SSOT**: `docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md`, `docs/03_AGENT_ARCHITECTURE.md`.
**스키마 SSOT**: `schemas/models.py` 의 `IntakePlan / IntakePlanItem / SourceIntake / UserDecision`.

### 구체 작업 단위 (Phase 3 후보)

1. `agents/dynamic_intake_planner.py` 신설.
   - 입력: `ProjectManifest.title + topic_summary + category`.
   - 출력: `IntakePlan` (`required_items: list[IntakePlanItem]`).
   - Anthropic / OpenAI API 호출 (.env 의 키 사용). `.replace()` 로 시스템 프롬프트 포맷.
2. CLI 추가: `python -m orchestrator.main plan-intake {pid}` → `projects/{pid}/intake_plan.json` 생성.
   - 동시에 manifest 를 `intake_planning` 상태로 전이, 완료 시 `intake_pending_user` 로 전이.
3. `web/intake_page_app.py` 신설 (FastAPI 또는 Flask 1 파일).
   - `intake_plan.json` 을 읽어 항목별 선택 UI 렌더.
   - 제출 시 `source_intake.json` (`SourceIntake`) 생성, manifest 를 `source_collecting` 으로 전이.
4. 파일 업로드 경로: `projects/{pid}/uploads/{item_id}/...`. `UserDecision.uploaded_files` 에 상대경로 기록.
5. 사용자에게 보여줄 URL 은 로컬 `http://localhost:8765/intake/{pid}` (포트는 config.yaml).

### Phase 3 의 종료 조건 (DoD)

- [ ] `plan-intake demo2` 하면 `projects/demo2/intake_plan.json` 이 생성되고 manifest 상태가 `intake_pending_user` 로 전이.
- [ ] `web/intake_page_app.py` 를 띄우고 브라우저에서 항목별 선택·파일 업로드·링크 입력 가능.
- [ ] 제출 시 `source_intake.json` 이 검증된 Pydantic 모델로 저장.
- [ ] manifest 가 `source_collecting` 으로 전이.
- [ ] `python -m py_compile` 통과.
- [ ] `CHANGELOG.md` `[v0.3.0]` 절 + `DEVLOG.md` 엔트리.
- [ ] 모든 Tier 1·2 마크다운 `last_synced_with: v0.2.2 → v0.3.0`.

### Phase 3 이후 (Phase 4 예고)

- Task Queue Builder: `source_intake.json` → `task_queue.json` 변환 + Worker 배정 + 결과 수집.

---

## 3. 작업 시작 전 체크리스트

다음 세션이 첫 번째로 실행할 일 (순서 중요):

1. **읽기**: `CLAUDE.md` → `GOAL.md` → `VERSION` (현재 `0.2.2`) → 본 `HANDOFF.md` → `docs/13_IMPLEMENTATION_ROADMAP.md` → `docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md` → `WORKFLOWS.md W7-W8` → 가장 최근 `DEVLOG.md` 엔트리 3 개.
2. **상태 확인**:
   ```bash
   git status                       # clean 인지
   git log --oneline -10            # 최근 커밋
   cat VERSION                       # 현재 버전
   python -m py_compile orchestrator/*.py workers/*.py schemas/*.py
   python -m orchestrator.main version
   ```
3. **사용자 의도 확인**: "Phase 3 시작?" 또는 "그 외 작업?" 한 줄 질문.
4. **작업 진행**: 항상 작은 단위 커밋, 한 커밋 = 한 의도.

---

## 4. 자주 까먹는 규칙 (Reminder)

- ✅ 모든 커밋 첫 줄: `vX.Y.Z: {summary}`. **`{summary}` 는 한국어로 작성** (사용자가 `branches.html` 에서 한글로 본다. 영문으로 쓰면 `COMMIT_DESCRIPTIONS` SHA 매핑을 추가해야 한다).
- ✅ 버전 증분 시: `VERSION` 한 줄 + 30 개 마크다운 `last_synced_with` 일괄 갱신 (`sed -i`).
- ✅ `orchestrator/__version__` 은 VERSION 을 동적으로 읽으므로 별도 편집 불필요.
- ✅ Worker subprocess 는 stdout 1 줄 1 이벤트, `task_result.json` 필수 종료.
- ✅ Worker `_finalize_slot` 종료 후 slot 은 즉시 idle 환원 (PIPELINE-AP-006).
- ✅ JSON 산출물은 `schema_version` 필드 필수.
- ✅ 도메인 데이터는 Pydantic v2 BaseModel 만 사용. raw dict 금지.
- ✅ 시스템 프롬프트 포맷팅은 `.replace()` (`format()` 은 JSON `{}` 와 충돌).
- ✅ 새 브랜치 만들면 `docs/branches.html` 의 `BRANCH_DESCRIPTIONS` 에 **한국어** 설명 한 줄 추가.
- ✅ Phase / PATCH 완료 push 직후 사용자에게 **Codex Cloud 리뷰 안내** (`WORKFLOWS.md W8`). 사용자가 결과 붙여넣을 때까지 다음 Phase 시작 보류.

---

## 5. 사용자 측 환경 (참고)

- OS: Windows (사용자), Linux (이 컨테이너).
- 진입 스크립트: `run_pipeline.bat` (Windows 더블클릭).
- Python: 3.11+ 가정.
- 브라우저: 사용자 측 PAT 는 `localStorage` (key: `osint_generator.github_token.v1`).

---

## 6. 본 문서의 갱신 규칙

- Phase 가 완료될 때마다 "1. 지금 어디까지 와 있나" 표 행 추가.
- Phase 가 시작될 때 "2. 다음 작업" 절 갱신 (현재 Phase 의 DoD 로 교체).
- 본 문서 자체도 `last_synced_with` 헤더 갱신 대상에 포함.
- append-only 가 아니라 **현재 상태 미러**. 과거 정보는 `DEVLOG.md` / `CHANGELOG.md` 로 흘려보낸다.

---

마지막 갱신: v0.2.2, 2026-05-20.
