<!--
tier: 1
last_synced_with: v0.2.2
ssot_for: [session-handoff]
depends_on: [CLAUDE.md, GOAL.md, VERSION, docs/13_IMPLEMENTATION_ROADMAP.md]
last_review: 2026-05-19
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

## 1. 지금 어디까지 와 있나 (v0.2.2 기준)

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
| Phase 2: Project Manager / State Machine | v0.2.0 | `state_machine.py` + `project_manager.py` 신설, `ProjectManifest.state_history` 추가, CLI `new-project / resume / transition` 정식 구현, 전이 검증 | py_compile 통과, smoke test 10케이스 (정상/중복/불법/archived) 모두 의도대로 |
| LLM Bridge 패턴 정립 (문서 PATCH) | v0.2.1 | `ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` 신설, `docs/03 §4.5` 에 `BaseLLMWorker` 계약 추가, `CLAUDE.md C6` 에 `LLM-AP-N` 카테고리 추가, `LLM_ANTIPATTERNS.md` 골격. **시스템은 LLM API 키를 사용하지 않으며 사용자 구독의 `claude` / `codex` CLI 를 subprocess 로 호출한다 (G4 와 동등한 강제력)**. | 문서 only, 코드 변경 없음 |
| BaseLLMWorker 코드 도입 + LLM-AP-001 | v0.2.2 | `workers/base_llm_worker.py` 신설 (CLI_INVOCATION 매핑, `OSINT_LLM_STUB` 환경변수, 3-파일 영속화), `schemas/models.py` 에 `LLMCallRecord` 추가, `dummy_llm_worker.py` 로 4 케이스 smoke test. 실 `claude` CLI 호출 시 응답 wrapper 발견 → **LLM-AP-001** 등록 (구조적 조치 v0.2.3 대기). | py_compile 통과, 4 케이스 (정상 stub / 잘못된 JSON / 스키마 위반 / 실 CLI) 모두 의도대로 |

### 핵심 산출물

- 라이브 사이트: <https://osint-generator.vercel.app/> (PAT 필요, Private 저장소)
- TUI 진입: `python -m orchestrator.main command-center --project demo` 또는 `run_pipeline.bat`
- 프로젝트 라이프사이클 CLI:
  - `python -m orchestrator.main new-project <pid> --title ... --category geopolitics`
  - `python -m orchestrator.main resume <pid>`
  - `python -m orchestrator.main transition <pid> --to intake_planning --reason "..."`
- 더미 워커 directory: `workers/dummy_worker.py`
- Project Manager 모듈: `orchestrator/project_manager.py` (project_manifest.json 의 유일한 쓰기자)
- State Machine 모듈: `orchestrator/state_machine.py` (`LINEAR_SEQUENCE`, `allowed_next_states`, `validate_transition`)

### 인프라 상태

- **default branch**: `main` (모든 푸시는 여기로)
- **Vercel**: `main` 푸시마다 자동 재배포. `osint-generator.vercel.app` 안정 도메인.
- **GitHub**: doroper98/osint_generator, Private. PAT 인증으로 브랜치 뷰어 접근.

### 알려진 antipattern 카탈로그

- `docs/ANTIPATTERNS/TTS_ANTIPATTERNS.md` — TTS-AP-001 ~ TTS-AP-053
- `docs/ANTIPATTERNS/PIPELINE_ANTIPATTERNS.md` — PIPELINE-AP-001 ~ PIPELINE-AP-006
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` — LLM-AP-001 (active, v0.2.2 발견, v0.2.3 patch 대기: claude CLI 응답 wrapper unwrap)

**문제 발생 시 반드시 이 카탈로그를 먼저 검색.** 중복 발견 시 동일 번호에 `[superseded by ...]` 마킹만, 새로 발견 시 다음 번호로 append.

---

## 2. 다음 작업 — v0.2.3 (LLM-AP-001 fix) 또는 Phase 3 (v0.3.0)

v0.2.2 에서 `BaseLLMWorker` 코드를 도입했고 실 `claude` CLI 호출에서 응답 wrapper 문제 (LLM-AP-001) 를 발견. 다음 세션은 둘 중 선택.

### 옵션 A: v0.2.3 — LLM-AP-001 구조적 조치 (PATCH, 추천)

- `workers/base_llm_worker.py:_invoke_llm` 내부에 backend 별 wrapper unwrap 추가.
  - claude: `{"type":"result","subtype":"success","result":"<text>",...}` → `result` 필드 추출 → JSON 이면 그대로, markdown code fence 면 추출.
  - codex: 동일 패턴 검증 후 분기.
- `tests/test_base_llm_worker.py` 신설 + fixture 기반 회귀 테스트 (LLM-AP-001 의 "regression_test" 항목 closing).
- `LLM_ANTIPATTERNS.md` 의 LLM-AP-001 상태를 `active → fixed in v0.2.3` 으로 갱신.
- VERSION 0.2.2 → 0.2.3 (PATCH — 버그 수정).

### 옵션 B: 바로 Phase 3 (v0.3.0) — Dynamic Intake Page

- LLM-AP-001 은 wrapper 가 항상 같은 구조면 임시로 IntakePlannerWorker 안에서 우회 가능하지만, 깔끔하지 않음.
- `agents/dynamic_intake_planner.py` (= `IntakePlannerWorker(BaseLLMWorker)`) 신설.
  - `llm_backend="claude"`, `llm_mode="response"`, `response_model=IntakePlan`.
  - `system_prompt`: 카테고리별 표준 인테이크 항목 생성 지시.
  - `build_user_prompt`: ProjectManifest (title, category, target_duration_min, topic_summary) → 사용자 프롬프트.
  - `output_path`: `projects/{pid}/01_intake/intake_plan.json`.
- `web/intake_page_app.py` 신설 (FastAPI). `intake_plan.json` 렌더 + `source_intake.json` POST 저장.
- CLI: `python -m orchestrator.main plan-intake <pid>` (planner 호출 + 상태 `created → intake_planning → intake_pending_user`).
- 웹 제출 시 `intake_pending_user → source_collecting` 전이.

**추천**: 옵션 A. 작은 단위 (한 커밋 한 의도) + LLM-AP-001 이 fix 되지 않으면 Phase 3 의 IntakePlannerWorker 첫 호출부터 막힘.

### Phase 3 의 종료 조건 (DoD)

- [ ] `plan-intake demo3` 호출 시 `intake_plan.json` 생성, `state == intake_planning` 으로 전이.
- [ ] 웹 페이지에서 항목 선택 후 제출하면 `source_intake.json` 생성, `state == source_collecting` 으로 전이.
- [ ] 모든 항목이 `IntakePlanItem` / `UserDecision` Pydantic 모델로 검증 통과.
- [ ] LLM 호출은 `BaseLLMWorker` 경유 + `llm_calls/{call_id}.json` 영속화.
- [ ] `python -m py_compile` 통과.
- [ ] `CHANGELOG.md` `[v0.3.0]` 절 추가, `DEVLOG.md` 엔트리 추가.

### Phase 3 이후 (Phase 4 예고)

`docs/13_IMPLEMENTATION_ROADMAP.md` 의 Phase 4 절 참조:
- `source_intake.json → task_queue.json` 변환 로직
- AI Delegation 항목 → Worker subprocess 실행
- 첫 실제 Worker (`source_collector_worker`, `BaseLLMWorker(mode="agent")`) 도입

---

## 3. 작업 시작 전 체크리스트

다음 세션이 첫 번째로 실행할 일 (순서 중요):

1. **읽기**: `CLAUDE.md` → `GOAL.md` → `VERSION` (현재 `0.2.2`) → 본 `HANDOFF.md` → `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` → `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` (LLM-AP-001 정독) → `docs/13_IMPLEMENTATION_ROADMAP.md` → 가장 최근 `DEVLOG.md` 엔트리 3 개.
2. **상태 확인**:
   ```bash
   git status                       # clean 인지
   git log --oneline -10            # 최근 커밋
   cat VERSION                       # 현재 버전
   git fetch origin main            # 다른 세션이 main 에 push 했을 수 있음
   git log --oneline HEAD..origin/main   # 비어 있으면 OK, 아니면 pull/rebase 필수
   python -m py_compile orchestrator/*.py workers/*.py schemas/*.py
   ```
3. **사용자 의도 확인**: "v0.2.3 (LLM-AP-001 fix) 먼저?" 또는 "Phase 3 직행?" 한 줄 질문.
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
- ✅ **LLM API 키 / `anthropic` / `openai` SDK 절대 금지** (ADDENDUM_04). LLM 호출은 `BaseLLMWorker` 가 `claude` / `codex` CLI 를 subprocess 로 호출하는 방식만 허용. 위반 시 PR 차단.

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
