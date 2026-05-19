<!--
tier: 2
last_synced_with: v0.1.2
ssot_for: [phase-roadmap]
depends_on: [../GOAL.md, ../CHANGELOG.md]
last_review: 2026-05-19
-->

# 13 — Implementation Roadmap

## Phase 0: 프로젝트 초기화

- 저장소 구조 생성, docs 19종, Tier 1/3 거버넌스, 스캐폴딩 파일.
- 완료 기준: `run_pipeline.bat` 진입 가능.
- **상태**: ✅ v0.1.0

## Phase 1: Orchestrator Command Center MVP

- 방식 B TUI (Textual + Rich).
- Orch CLI Log + Job Dashboard + Worker Slot 4개.
- Log Router, Worker Slot Manager.
- 완료 기준: dummy Worker 4개가 subprocess로 동시 실행되며 각 Slot 패널에 로그가 흐른다.
- **상태**: 🚧 v0.1.0 진행 중

## Phase 2: Project Manager / State Machine

- 프로젝트 생성, `project_manifest.json`, 상태 전이, 프로젝트 폴더 구조 생성.
- 완료 기준: 새 project_id 생성·재진입·상태 복구 가능.

## Phase 3: Dynamic Intake Page

- Dynamic Intake Planner Agent → `intake_plan.json`.
- 웹 앱 (`web/intake_page_app.py`) → `source_intake.json`.
- 완료 기준: 주제 입력 시 동적 항목 생성, 웹페이지에서 선택 저장 가능.

## Phase 4: Task Queue & AI Delegation

- `source_intake.json` → `task_queue.json` 변환.
- Worker Slot 배정, `task_result.json` 수집.
- 완료 기준: AI Delegation 항목이 Worker task로 변환·실행되고 결과 수집.

## Phase 5: Source Registry & Source Completeness Check

- `source_registry.json`, `source_completeness_report.json`.
- 완료 기준: 소스별 권리·신뢰도·위험도 기록, 부족 자료 식별.

## Phase 6: Research / Script / Scene

- `research_dossier.json`, `argument_map.json`, `episode_blueprint.json`, `full_script.json`, `scene_manifest.json` (with provenance), `asset_manifest.json`.
- 완료 기준: 샘플 주제로 15–20분 구조 생성.

## Phase 7: Media Workers

- Video Acquisition / Article Capture / X Card / Telegram Card / Map / Earthquake / Chart / Annotation Worker.
- 완료 기준: 각 Worker가 `task_result.json` 생성, `asset_manifest` 반영.

## Phase 8: TTS / Music

- TTS Worker, TTS Pronunciation QA, Music Worker.
- 완료 기준: narration 생성 → ASR QA → 통과한 wav만 채택, BGM loop 생성.

## Phase 9: Remotion Rendering

- `remotion_job_builder`, Remotion 컴포넌트, `DebugOverlay`, `draft_debug.mp4` / `draft_preview.mp4` / `final.mp4`.
- 완료 기준: 3개 render mode 모두 작동, `debug`에만 Debug Layer 표시.

## Phase 10: Thumbnail System

- `thumbnail_brief`, `thumbnail_manifest`, `ThumbnailComposition`, `thumbnail_qa`.
- 완료 기준: 2–4개 시안 생성, 사용자 선택 가능.

## Phase 11: Review Dashboard & Publish

- `review_dashboard_app`, `youtube_metadata_agent`.
- 완료 기준: 대본·영상·썸네일 승인 가능, `youtube_metadata.json` 생성.

## 진행 원칙

1. Phase 단위 구현.
2. 각 Phase는 테스트 가능한 산출물.
3. 전체 기능을 한 번에 만들지 않는다.
4. 각 Phase 완료 시 CHANGELOG/DEVLOG 동기화.
5. 각 Phase 완료 시 새 Antipattern 발견 → 카탈로그 append.

상세 합격 기준은 [GOAL.md G3](../GOAL.md#g3-mvp-acceptance-criteria-v2-17).
