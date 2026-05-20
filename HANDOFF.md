<!--
tier: 1
last_synced_with: v0.2.7
ssot_for: [session-handoff]
depends_on: [CLAUDE.md, GOAL.md, VERSION, docs/13_IMPLEMENTATION_ROADMAP.md, docs/REVIEW_PROMPT.md]
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

## 1. 지금 어디까지 와 있나 (v0.2.7 기준)

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
| BaseLLMWorker 코드 도입 + LLM-AP-001 | v0.2.2 | `workers/base_llm_worker.py` 신설 (CLI_INVOCATION 매핑, `OSINT_LLM_STUB` 환경변수, 3-파일 영속화), `schemas/models.py` 에 `LLMCallRecord` 추가, `dummy_llm_worker.py` 로 4 케이스 smoke test. 실 `claude` CLI 호출 시 응답 wrapper 발견 → **LLM-AP-001** 등록. | py_compile 통과, 4 케이스 모두 의도대로 |
| LLM-AP-001 구조적 조치 | v0.2.3 | `_unwrap_response` / `_unwrap_claude_response` / `_extract_json_block` 도입. `run()` 의 검증 직전 backend 별 unwrap. `raw.txt` 는 원본 보존. `tests/test_base_llm_worker.py` 13 케이스. | 13/13 단위 테스트 |
| LLM-AP-002 (codex JSONL) | v0.2.4 | `codex exec --json` 이 단일 wrapper 아닌 JSONL stream 발견 (`thread.started` / `turn.started` / `item.completed` / `turn.completed`). `_unwrap_codex_response` 실 구현 (마지막 `agent_message.text` 채택). `CLI_INVOCATION` codex 매핑에 `--skip-git-repo-check` / `--color never` 추가. 단위 테스트 13 → 20. | 20/20 통과, codex-cli 0.130.0 실 캡쳐 fixture 보존 |
| 외부 코드 리뷰 1차 반영 + LLM-AP-003 | v0.2.5 | codex `exec review` 결과 (Critical 0 / High 6 / Medium 3) 일괄 흡수. `LLMSubprocessError.stdout/stderr/exit_code` 첨부, `parse_failed` vs `validation_failed` 분리, `try/finally` 로 record 영속화 보장, `_validate_output_path` 컨테인먼트, `allow_agent_mode` opt-in 가드 (LLM-AP-003), claude wrapper subtype 엄격화, `exit_code: Optional[int]`. `tests/test_base_llm_worker_run.py` 8 케이스. 단위 테스트 20 → 30. | 30/30 통과 |
| codex review 절차 정형화 | v0.2.6 | `CLAUDE.md` 에 **C10. 외부 코드 리뷰 의무화** 추가. `docs/REVIEW_PROMPT.md` 신설 (표준 프롬프트 + Windows/Linux 호출 명령어 + 결과 처리 가이드). MINOR/MAJOR/Phase 완료 직전 codex review 필수화. | 문서 only |
| 평행 브랜치 흡수 (Ij1TX) | v0.2.7 | 동일 출발점의 다른 세션 브랜치 `claude/start-after-handoff-Ij1TX` 의 차별점 3 가지 흡수: (1) **SCHEMA-AP 카탈로그** + SCHEMA-AP-001 (임의 상태 점프 / self-loop), (2) **TUI 라이브 manifest reload** (`_tick_loop` 가 매 tick 마다 `load_manifest` → 외부 transition 즉시 반영, 실패 모드 3 분류: unknown/invalid/정상), (3) **`_write_manifest` atomic write** (tmp→`Path.replace`, half-written race 차단). | py_compile + 5 케이스 smoke (atomic / corrupt JSON ValidationError / non-JSON JSONDecodeError 포함) 통과 |

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
- `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` — SCHEMA-AP-001 (v0.2.7 신설, 임의 상태 점프 / self-loop)
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md`:
  - LLM-AP-001 (resolved v0.2.3) — claude `--output-format json` 단일 wrapper
  - LLM-AP-002 (resolved v0.2.4) — codex `exec --json` JSONL 이벤트 stream
  - LLM-AP-003 (**resolved-partial** v0.2.5) — agent 모드 prompt injection. opt-in 가드 (`allow_agent_mode`) 만 완료. 본격 sandbox (`--sandbox`, scratch dir, 외부 자료 `<untrusted_source>` 격리) 는 Phase 3+ 후속.

**문제 발생 시 반드시 이 카탈로그를 먼저 검색.** 중복 발견 시 동일 번호에 `[superseded by ...]` 마킹만, 새로 발견 시 다음 번호로 append.

---

## 2. 다음 작업 — Phase 3 (v0.3.0) Dynamic Intake Page

BaseLLMWorker 인프라가 외부 리뷰까지 거쳐 견고해졌고 (v0.2.5), codex review 절차도
정형화 (v0.2.6) 됐다. 다음은 **첫 도메인 worker 인 IntakePlannerWorker** 를 도입하는 Phase 3.

### 2.1 Phase 3 의 범위 (v0.3.0 — MINOR)

#### 새 도메인 모델 (`schemas/models.py` 확장)

- `IntakePlanItem` — planner 가 사용자에게 제시할 인테이크 항목 (id, question, candidate_options, rationale, …)
- `IntakePlan(VersionedModel)` — `items: list[IntakePlanItem]`, `project_id`, `category` …
- `UserDecision` — 사용자가 인테이크 페이지에서 선택한 결과
- `SourceIntake(VersionedModel)` — `decisions: list[UserDecision]`, source_collecting Phase 의 입력

#### 새 Worker (`workers/intake_planner_worker.py`)

`IntakePlannerWorker(BaseLLMWorker)`:
- `llm_backend = "claude"` (또는 `"codex"` — 사용자 결정)
- `llm_mode = "response"` (agent 모드 불필요 — 외부 자료 읽기 없음)
- `response_model = IntakePlan`
- `system_prompt`: 카테고리별 표준 인테이크 항목 생성 지시 (지정학/군사/경제/허위정보/지진 별)
- `build_user_prompt(args, task)`: `ProjectManifest` 로딩 → title, category, target_duration_min, topic_summary 를 자연어 프롬프트로
- `output_path(args, task)`: `projects/{pid}/01_intake/intake_plan.json`

#### 새 웹 페이지 (`web/intake_page_app.py`)

- FastAPI. `GET /intake/{pid}` 가 `intake_plan.json` 렌더링.
- `POST /intake/{pid}/submit` 이 `UserDecision[]` 받아 `source_intake.json` 으로 영속화.
- 사용자가 항목 선택/추가/거절 가능. 각 결정마다 rationale 입력 옵션.

#### CLI 확장 (`orchestrator/main.py`)

- `python -m orchestrator.main plan-intake <pid>` — IntakePlannerWorker 호출 + 상태 전이
  `created → intake_planning → intake_pending_user`.
- 웹 제출 시 (또는 별도 CLI `submit-intake <pid>`) `intake_pending_user → source_collecting` 전이.

### 2.2 Phase 3 종료 조건 (DoD)

- [ ] `plan-intake demo3` 호출 시 `intake_plan.json` 생성, `state == intake_pending_user` 로 전이.
- [ ] 웹 페이지에서 항목 선택 후 제출하면 `source_intake.json` 생성, `state == source_collecting` 으로 전이.
- [ ] 모든 항목이 `IntakePlanItem` / `UserDecision` / `IntakePlan` / `SourceIntake` Pydantic 모델로 검증 통과.
- [ ] LLM 호출은 `BaseLLMWorker` 경유 + `llm_calls/{call_id}.{json,prompt.txt,raw.txt}` 영속화.
- [ ] Windows cmd 에서 `codex` backend 도 정상 동작 검증 (이전 세션이 LLM-AP-002 까지 처리해 둠).
- [ ] `python -m py_compile` 통과 + `tests/` 30+ → 35+ (IntakePlanner 단위 테스트 추가).
- [ ] `CHANGELOG.md` `[v0.3.0]` 절 추가, `DEVLOG.md` 엔트리.
- [ ] **C10.1 의무**: v0.3.0 (MINOR) 증분 직전에 codex review 1 회 실행, 결과 흡수.

### 2.3 Phase 3 의 알려진 risk

1. **agent 모드 필요 없음** — IntakePlannerWorker 는 ProjectManifest 의 사용자 입력만 읽고 외부 자료 안 봄. `allow_agent_mode=False` 그대로. LLM-AP-003 우회.
2. **시스템 프롬프트 길이** — 카테고리 5 종 × 표준 항목 다수를 한 프롬프트로 묶으면 길어짐. 카테고리별 분리 또는 system_prompt 의 동적 조합 (`.replace()`, **never `.format()`**) 고려.
3. **claude vs codex 선택** — claude 가 한국어 지시 이해 더 자연스러우나 codex 의 `--output-schema` 가 강제 검증에 유리. 사용자에게 한 번 의견 묻기.
4. **Windows quoting** — codex backend 사용 시 prompt 안의 큰따옴표가 cmd 인용부호와 충돌할 수 있음. `subprocess.run([...])` 의 argv 리스트는 안전하지만 실 호출 검증 필요.

### 2.4 Phase 3 이후 (Phase 4 예고)

`docs/13_IMPLEMENTATION_ROADMAP.md` Phase 4 절:
- `source_intake.json → task_queue.json` 변환 (orchestrator 책임).
- AI Delegation 항목 → Worker subprocess 실행.
- 첫 agent 모드 Worker (`source_collector_worker`, `BaseLLMWorker(mode="agent", allow_agent_mode=True)`) — LLM-AP-003 후속 작업의 첫 실증.

---

## 2.5 대안: LLM-AP-003 후속 (Phase 3 전에 보안 강화)

원하시면 Phase 3 전에 LLM-AP-003 후속을 한 PATCH 로 처리할 수 있다:
- codex `--sandbox read-only` / `workspace-write` 매핑.
- agent 모드 worker 용 scratch dir 격리.
- prompt 안의 외부 자료를 `<untrusted_source>` envelope 으로 자동 wrap 하는 헬퍼.

다만 IntakePlannerWorker 는 agent 모드를 안 쓰니 Phase 3 와 무관하다. **Phase 4 (source_collector_worker) 진입 전에만** 처리하면 충분. 사용자 우선순위에 따라 선택.

---

## 3. 작업 시작 전 체크리스트

다음 세션이 첫 번째로 실행할 일 (순서 중요):

1. **읽기 (필독)**: `CLAUDE.md` (특히 신규 **C10**) → `GOAL.md` → `VERSION` (현재 `0.2.7`) → 본 `HANDOFF.md` → `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` → `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` (LLM-AP-001/002/003 정독) → `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` (SCHEMA-AP-001) → `docs/REVIEW_PROMPT.md` (codex review 절차) → `docs/13_IMPLEMENTATION_ROADMAP.md` → 가장 최근 `DEVLOG.md` 엔트리 6 개 (v0.2.2 ~ v0.2.7).
2. **상태 확인**:
   ```bash
   git status                                       # clean 인지
   git log --oneline -10                            # 최근 커밋
   cat VERSION                                      # 현재 버전 (0.2.6)
   git fetch origin main                            # 다른 세션이 main 에 push 했을 수 있음
   git log --oneline HEAD..origin/main              # 비어 있으면 OK, 아니면 pull/rebase 필수
   python -m py_compile orchestrator/*.py workers/*.py schemas/*.py
   python -m unittest tests.test_base_llm_worker tests.test_base_llm_worker_run   # 30 케이스 통과 확인
   ```
3. **사용자 의도 확인**: "Phase 3 (IntakePlannerWorker) 직행?" 또는 "LLM-AP-003 후속 보안 강화 먼저?" 한 줄 질문.
4. **작업 진행**: 항상 작은 단위 커밋, 한 커밋 = 한 의도.
5. **MINOR / MAJOR / Phase 완료 직전**: C10.1 의무 — codex review 1 회 실행, 결과 흡수 후 증분.

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
- ✅ **agent 모드 worker** 는 `allow_agent_mode = True` 명시 opt-in (LLM-AP-003). 기본은 `False`. 외부 자료 prompt 는 향후 `<untrusted_source>` envelope 으로 격리 예정.
- ✅ **MINOR/MAJOR/Phase 완료 직전**: `docs/REVIEW_PROMPT.md` 절차로 codex review 1 회 실행. Critical/High 흡수 후에만 버전 증분 (CLAUDE.md C10).
- ✅ **`parsed_status` 4 상태 의미**: `ok` / `parse_failed` (JSON 깨짐) / `validation_failed` (schema 위반) / `subprocess_error` (CLI 자체 실패). 새 상태 추가하지 말고 기존 4 개로 흡수.
- ✅ **`LLMCallRecord.exit_code` 는 `Optional[int]`**. None = "미실행 (FileNotFoundError) 또는 timeout".
- ✅ **`output_path` 는 project_dir 안 + task.output_refs 와 일치**해야 함 (`_validate_output_path` 가드).

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

마지막 갱신: v0.2.7, 2026-05-20.
