<!--
tier: 3
last_synced_with: v0.2.2
ssot_for: [release-notes]
depends_on: [README.md, GOAL.md]
last_review: 2026-05-19
-->

# CHANGELOG

본 문서는 사용자(또는 후속 개발자) 관점의 릴리즈 노트입니다.
released 항목은 **append-only**입니다.

본 저장소는 [Semantic Versioning](https://semver.org/)을 따릅니다.

---

## [Unreleased]

### Added
- 

### Changed
-

### Fixed
-

---

## [v0.2.2] — 2026-05-20

### Added
- **`workers/base_llm_worker.py:BaseLLMWorker` 코드 도입** (ADDENDUM_04 §4 의 정식 구현).
  - 클래스 변수: `llm_backend ∈ {"claude", "codex"}`, `llm_mode ∈ {"response", "agent"}`, `system_prompt`, `response_model`.
  - 추상 메서드: `build_user_prompt(args, task)`, `output_path(args, task)`.
  - `_invoke_llm` 가 backend/mode 별 `CLI_INVOCATION` 매핑으로 subprocess 호출. `FileNotFoundError` / `TimeoutExpired` / 비0 종료 모두 `LLMSubprocessError` 로 흡수.
  - `OSINT_LLM_STUB=1` + `OSINT_LLM_STUB_RESPONSE` 환경변수로 실 CLI 우회 (smoke test 전용).
  - 전 호출이 `projects/{pid}/llm_calls/{call_id}.{json,prompt.txt,raw.txt}` 3 파일로 영속화.
- `schemas/models.py` 에 `LLMCallRecord` Pydantic 모델 추가. `parsed_status ∈ {"ok", "parse_failed", "validation_failed", "subprocess_error"}`.
- `workers/dummy_llm_worker.py` 신설 (`DummyLLMResponse` 응답 모델 포함). smoke test 전용.
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 의 첫 항목 **LLM-AP-001** 등록 — `claude -p ... --output-format json` 응답이 wrapper JSON (`type/subtype/result/usage/uuid` 등) 으로 감싸여 있어 그대로는 도메인 Pydantic 모델 검증 통과 안 함. 구조적 조치 v0.2.3 patch.

### Changed
- `docs/ADDENDUM_04 §4` 인트로를 "v0.2.2 코드 도입 완료" 로 갱신, §8 #1 미결 항목을 LLM-AP-001 으로 구체화.

### Notes
- smoke test 4 케이스 (정상 stub / 잘못된 JSON / 스키마 위반 / 실 claude CLI) 모두 의도대로 동작. LLMCallRecord 4건 영속화 확인.
- `BaseLLMWorker` 는 새 Worker 베이스이므로 C5.4 의 MINOR 사유 ("새 Worker 추가") 에 해당. MINOR 0.2.1 → 0.2.2.

---

## [v0.2.1] — 2026-05-19

### Added
- **Subscription LLM Bridge 패턴 정식 문서화** — 본 시스템은 LLM API 키를 사용하지 않고, 사용자가 이미 구독 중인 `claude` (Claude.ai) 와 `codex` (ChatGPT Plus/Pro) CLI 를 subprocess 로 자동 호출한다는 핵심 아키텍처 결정 정립.
- `docs/ADDENDUM_04_SUBSCRIPTION_LLM_BRIDGE.md` 신설. GOAL.md G4 와 동등한 강제력으로 운용. `BaseLLMWorker` 인터페이스 명세, 호출 모드 (`response` / `agent`), 백엔드 선택 가이드, 추적성 (`projects/{pid}/llm_calls/{call_id}.json`), 에러 모드 정의.
- `docs/03_AGENT_ARCHITECTURE.md` §4.5 에 `BaseLLMWorker` 계약 요약 추가. §4 베이스워커 안내문에 "LLM 호출은 `BaseLLMWorker` 상속 필수" 명시.
- `CLAUDE.md` C6 안티패턴 카테고리에 `LLM-AP-N` 추가.
- `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` 골격 신설 (항목은 Phase 3 첫 실 호출부터 누적).
- `docs/ANTIPATTERNS/README.md` 인덱스에 `LLM-AP` 행 추가.

### Notes
- 본 변경은 **G4 본문은 건드리지 않는** PATCH. ADDENDUM_04 가 G4 와 동등한 강제력을 갖도록 본문에 명시. v1.0.0 시점에 G4 #13 으로 정식 흡수 (MAJOR 증분).
- 코드 변경 없음. `BaseLLMWorker` 코드는 v0.2.2 patch 또는 Phase 3 시작 시점에 도입.

---

## [v0.2.0] — 2026-05-19

### Added
- **Phase 2 완료: Project Manager / State Machine**.
- `orchestrator/state_machine.py` 신설. `LINEAR_SEQUENCE` 가 docs/02 §4 의 24개 상태 선형 흐름을 SSOT 로 보유. `allowed_next_states` / `validate_transition` 순수 함수 제공.
- `orchestrator/project_manager.py` 신설. `project_manifest.json` 의 유일한 쓰기자. `new_project` / `resume_project` / `transition_state` 공개 API.
- `schemas/models.py` 에 `StateTransition` 모델 추가, `ProjectManifest.state_history` (append-only) 필드 추가. schema_version 은 1 유지 (optional 필드 추가).
- CLI 명령 `new-project <pid> --title ... --category ... [--duration-min] [--topic-summary]`, `resume <pid>`, `transition <pid> --to <state> [--reason]` 정식 구현.
- 전이 규칙: 선형 다음 상태 또는 `archived` 만 허용. 동일 상태 전이 / 임의 점프는 명확한 한글 메시지와 함께 `ValueError` (CLI exit=2).

### Changed
- `orchestrator/command_center.py` 가 `project_manager.load_manifest` 를 통해 manifest 를 read-only 로 로드하도록 정리. raw json 파싱 코드 제거.
- `orchestrator/main.py` 의 `new-project` / `approve` placeholder 문구 제거, 실 구현으로 교체.

---

## [v0.1.5] — 2026-05-19

### Removed
- `docs/branches.html` 의 `BRANCH_DESCRIPTIONS` 에서 `test/graph-demo` 항목 삭제 (브랜치 자체가 삭제됨).
- `COMMIT_DESCRIPTIONS` 에서 `0159299` 엔트리 삭제 (해당 commit 이 도달 가능한 브랜치가 없어 dead code).

### Changed
- `test/graph-demo` 원격 브랜치 사용자 측에서 삭제 완료 (v0.1.3 그래프 분기 시각화 검증 종료).

---

## [v0.1.4] — 2026-05-19

### Added
- `docs/branches.html` 에 `COMMIT_DESCRIPTIONS` 맵 추가. 영어로 작성된 과거 커밋의 한글 설명을 SHA(앞 7자) 기준으로 override. 신규 커밋은 처음부터 한글로 작성하면 맵 갱신 불필요.
- `BRANCH_PRIORITY` + `sortBranchRefs` 헬퍼 추가. 같은 SHA 에 여러 브랜치가 가리킬 때 라벨 표시 우선순위 결정 (main → develop → release/ → feature/ → test/ → claude/ → 그 외 알파벳).
- `BRANCH_DESCRIPTIONS` 에 `test/graph-demo` 항목 추가 (임시 검증 브랜치).

### Fixed
- 같은 SHA 를 두 브랜치가 가리킬 때 `main` 라벨이 안 보이고 부차 브랜치 라벨만 보이던 문제 수정. (`sortBranchRefs` 가 main 을 항상 앞에 배치)

---

## [v0.1.3] — 2026-05-19

### Added
- `HANDOFF.md` (Tier 1) 신설. 다음 Claude Code 세션이 작업을 이어받을 때 가장 먼저 읽어야 할 인계 문서. 현재 상태, Phase 2 후보, 체크리스트, 자주 까먹는 규칙 정리.
- `docs/branches.html` 에 `@gitgraph/js` (jsDelivr CDN) 통합. 모든 브랜치를 단일 SVG git graph 로 렌더. 브랜치가 갈라지면 자동으로 가지 그림이 나옴.
- 사이드 패널이 등록되지 않은 브랜치를 자동 감지해서 "설명 미등록" 경고 카드로 노출 (한글).

### Changed
- `docs/branches.html` 의 데이터 모델을 commit-graph 중심으로 재작성. 브랜치별 commit 을 전역 SHA 맵으로 통합, parents 필드 활용해 토폴로지 보존. 모든 브랜치 commit fetch 병렬화 (`Promise.all`).

---

## [v0.1.2] — 2026-05-19

### Added
- `docs/index.html` 추가. 루트 URL (`/`) 접근 시 `/branches.html` 로 즉시 리다이렉트 (meta-refresh + JS 양쪽).

### Fixed
- Vercel 배포에서 루트 URL 이 `404: NOT_FOUND` 를 반환하던 문제 수정. `vercel.json` 의 `rewrites` 룰이 `outputDirectory: "docs"` 와 함께 쓰일 때 안정적이지 않아 실제 `index.html` 파일로 대체.

### Changed
- `vercel.json` 에서 `rewrites` 블록 제거 (정적 `index.html` 로 충분).

---

## [v0.1.1] — 2026-05-19

### Added
- `vercel.json` 루트 추가. Vercel 로 `docs/` 정적 호스팅 (Private 저장소 호환). 푸시마다 자동 재배포.
- `docs/branches.html` 에 Personal Access Token 입력 다이얼로그 추가. 토큰은 브라우저 localStorage 에만 저장. Private 저장소 GitHub API 호출에 사용.
- README 에 Vercel 설정 절차 + PAT 발급 절차 안내.

### Changed
- GitHub default branch 가 `main` 으로 통합됨에 따라 로컬 브랜치도 `main` 으로 rename, `branches.html:BRANCH_DESCRIPTIONS` 도 갱신.
- `branches.html:loadVersion` 이 raw.githubusercontent.com 대신 `/contents/VERSION` API 를 사용하도록 변경 (Private 저장소에서도 Bearer 인증으로 동작).
- 모든 Tier 1·2·3 마크다운/HTML 의 `last_synced_with: v0.1.0 → v0.1.1` 동기화.

### Fixed
- 없음 (Phase 1 PIPELINE-AP-006 은 v0.1.0 안에서 fix 됨).

---

## [v0.1.0] — 2026-05-19

### Added
- 저장소 초기화 (Phase 0)
- Tier 1 거버넌스 문서: `README.md`, `GOAL.md`, `CLAUDE.md`, `DOCS_GOVERNANCE.md`
- Tier 3 운영 문서: `CHANGELOG.md`, `DEVLOG.md`, `WORKFLOWS.md`
- Tier 2 스펙 문서 19종 (`docs/00_~16_`, `docs/ADDENDUM_01~03`)
- Antipattern 카탈로그 골격 (`docs/ANTIPATTERNS/README.md`, `TTS_ANTIPATTERNS.md`, `PIPELINE_ANTIPATTERNS.md`)
- 프로젝트 스캐폴딩: `pyproject.toml`, `requirements.txt`, `config.yaml`, `run_pipeline.bat`, `.gitignore`, `.githooks/commit-msg`
- Pydantic 스키마 모듈 `schemas/models.py` (project_manifest, task_queue, worker_slot, task_result 등)
- **Phase 1 MVP**: Orchestrator Command Center (Textual TUI)
  - `orchestrator/command_center.py` — TUI 진입점
  - `orchestrator/tui_app.py` — Orch CLI Log + Job Dashboard + Worker Slot 4개 패널
  - `orchestrator/worker_slot_manager.py` — Worker subprocess 배정
  - `orchestrator/log_router.py` — Worker stdout/stderr 라우팅
  - `orchestrator/dashboard.py` — 작업 현황 집계
  - `orchestrator/config.py` — config.yaml 로더
  - `workers/base_worker.py` — Worker CLI 공통 베이스
  - `workers/dummy_worker.py` — Phase 1 검증용 더미 워커
- 데모 프로젝트 `projects/demo/`와 4개 dummy task가 포함된 `task_queue.json`
