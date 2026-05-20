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

Codex Cloud 코드 리뷰 절차를 본 워크플로에 정식 편입.

### Added
- `WORKFLOWS.md` **W8. Codex Cloud 코드 리뷰** 절 신설. 흐름(AI push → 사용자 수동 실행 → 결과 전달 → 반영 → 재리뷰), 권장 프롬프트(CLAUDE.md 규칙 위반, Worker 규칙, 상태 머신 우회, 보안, SemVer, 일반 품질 6개 기준), 보류 사유 예시 포함.
- `WORKFLOWS.md` **W7. Phase 완료 체크리스트** 에 "Codex Cloud 코드 리뷰 통과" 항목 추가.
- `CLAUDE.md` **C8. 작업 흐름** 에 6번 항목 "Phase / PATCH 완료 시 Codex Cloud 리뷰 안내" 추가.
- `HANDOFF.md` **자주 까먹는 규칙** 에 Codex Cloud 리뷰 안내 한 줄 추가.

### Changed
- 모든 Tier 1·3 마크다운 `last_synced_with: v0.2.1 → v0.2.2` 일괄 갱신.

### Fixed
- 없음 (문서 보강 PATCH).

---

## [v0.2.1] — 2026-05-20

Phase 2 마무리 — HANDOFF DoD 후보 5/6번에서 누락된 두 구멍 메움.

### Added
- `docs/ANTIPATTERNS/SCHEMA_ANTIPATTERNS.md` 신설. `SCHEMA-AP-001 — ProjectState 임의 점프 / self-loop 전이` 첫 항목 등록. `ALLOWED_TRANSITIONS` 표 + `transition_state` 단일 진입점 + `InvalidTransitionError` 가 구조적 조치.
- TUI Job Dashboard 가 매 tick 마다 `project_manifest.json` 을 재로딩해 `current_state` 변경을 라이브 반영. 외부에서 `python -m orchestrator.main transition ...` 호출 시 TUI 가 즉시 따라잡음. 상태 변경 시 Orch CLI Log 에 `state changed: A → B` 1줄 emit.

### Changed
- `orchestrator/tui_app.py`: `_tick_loop` 에 `_reload_manifest_state()` 호출 추가. manifest 가 사라진 드문 경우 상태를 `unknown` 으로 표시하고 다음 tick 에서 재시도.
- 모든 Tier 1·3 마크다운 `last_synced_with: v0.2.0 → v0.2.1` 일괄 갱신.

### Fixed
- HANDOFF DoD 후보 5번 (SCHEMA-AP 카탈로그) 누락 보완.
- HANDOFF DoD 후보 6번 (TUI Job Dashboard 와 연동: 현재 프로젝트 / 상태 표시) 의 "라이브 반영" 부분 보완.

---

## [v0.2.0] — 2026-05-20

Phase 2 — Project Manager / State Machine 완료.

### Added
- `orchestrator/state_machine.py` 신설. `ProjectState` 24-state 선형 전이표 + 어디서든 `ARCHIVED` 도달 가능. `validate_transition` / `is_allowed` / `next_linear_state` 노출. `InvalidTransitionError`(`ValueError` 하위).
- `orchestrator/project_manager.py` 신설. `new_project` / `resume_project` / `transition_state` / `load_manifest` / `save_manifest`. atomic write (tmp → rename). 표준 하위 폴더 (`03_tasks/`, `03_tasks/task_results/`, `logs/workers/`) 자동 생성.
- `schemas/models.py` 에 `StateHistoryEntry` Pydantic 모델 추가. `ProjectManifest.state_history: list[StateHistoryEntry]` 필드 추가 (append-only 감사 로그). schema_version 은 1 유지 (additive).
- CLI 신규 서브커맨드: `new-project {pid} --category ... [--title ... --duration-min ... --topic-summary ...]`, `resume {pid}`, `transition {pid} --to {state} [--reason ...]`.
- 기존 `projects/demo/` 에 `project_manifest.json` 마이그레이션 (Phase 1 검증용 더미 프로젝트).

### Changed
- `orchestrator/main.py` 의 `command-center` import 가 지연 로딩으로 전환 (textual 미설치 환경에서도 비-TUI 커맨드 동작).
- `orchestrator/command_center.py` 가 manifest 존재 여부를 강제. 없으면 `ProjectNotFoundError` 로 진입 거부 (먼저 `new-project` 필요).
- `docs/05_DATA_SCHEMA_SPEC.md` ProjectManifest 표에 `state_history` 행 추가.
- `docs/13_IMPLEMENTATION_ROADMAP.md` Phase 1 ✅ v0.1.0, Phase 2 ✅ v0.2.0 마킹.
- 모든 Tier 1·2·3 마크다운 `last_synced_with: v0.1.5 → v0.2.0` 일괄 갱신.

### Fixed
- 없음 (Phase 2 신규 기능).

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
