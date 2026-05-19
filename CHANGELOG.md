<!--
tier: 3
last_synced_with: v0.1.0
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
