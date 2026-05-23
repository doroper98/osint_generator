<!--
tier: 2
last_synced_with: v0.9.0
ssot_for: [phase-roadmap]
depends_on: [../GOAL.md, ../CHANGELOG.md]
last_review: 2026-05-23
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
- **상태**: ✅ v0.6.0 — SourceCollectorWorker (v0.5.0) → partials, SourceRegistryBuilder
  (v0.5.3/v0.5.4) → registry, source_registry_io (v0.5.5) → 영속화 wiring,
  SourceCompletenessReport + checker (v0.6.0) → 부족 자료 식별. CLI
  `build-source-registry` 가 두 산출물 생성 후 `source_completeness_review` 전이.

## Phase 6: Research / Script / Scene

- `research_dossier.json`, `argument_map.json`, `episode_blueprint.json`, `full_script.json`, `scene_manifest.json` (with provenance), `asset_manifest.json`.
- 완료 기준: 샘플 주제로 3–20분 구조 생성 (target_duration_min 3~20 범위 내 폭넓게 조정 가능).

### Phase 6 세부 분해 (서브스텝)

Phase 6 는 단일 워커가 아니라 Research→Script→Scene 전 구간이다 (state:
`research_in_progress → blueprint_review → script_writing → script_review →
scene_planning → (Phase 7 asset_production) → scene_review`). Phase 5 패턴
(**모델 → 순수 worker/agent → io 경계 → thin CLI → Review Gate**) 을 각 서브스텝에 반복한다.
docs/03 §2 의 Agent 들은 모두 `BaseLLMWorker` 기반 Worker 로 구현된다 (Agent=역할명).

| 서브스텝 | 산출물 (신규 모델) | 워커 | 입력 | state / Gate | 증분 |
|---|---|---|---|---|---|
| **6A Research** ✅ v0.8.0 | `research_dossier.json` (`ResearchDossier`) | `ResearchWorker` | `source_registry.json` + `manifest.initial_links` | `research_in_progress` | MINOR |
| **6B Evidence Guard** | `qa_evidence_report.json` (`QaEvidenceReport`) | `EvidenceGuardWorker` | `research_dossier` | (research 내 QA, docs/12 §3) | MINOR |
| **6C Blueprint** | `argument_map.json` (`ArgumentMap`) + `episode_blueprint.json` (`EpisodeBlueprint`) | `BlueprintWorker` | `research_dossier` (+evidence) | → `blueprint_review` (**Gate 3**) | MINOR |
| **6D Script** ✅ v0.9.0 | `full_script.json` (`FullScript`/`ScriptSegment`) | `ScriptWorker` | `research_dossier` (blueprint 흡수) | `research_in_progress → blueprint_review → script_writing` | MINOR |
| **6E Scene** | `scene_manifest.json` (`SceneManifest` 골격 확장) + `asset_manifest.json` (`AssetManifest`) | `ScenePlannerWorker` | `full_script` | `scene_planning → … → scene_review` (**Gate 5**) | MINOR |

- **개발 방향 전환 (v0.8.1~, 수직 슬라이스)**: 6A 실제 LLM run 에서 인프라 이슈
  (LLM-AP-004) 와 "stub 만으로는 출력 품질을 못 본다"는 한계를 확인 후, **실물 영상까지
  최단경로로 관통하는 수직 슬라이스**로 전환. 6B(Evidence Guard)·6C(Blueprint) 정식
  산출물은 뒤로 미루고, 6D Script 가 dossier 에서 곧장 대본을 뽑음(blueprint 흡수).
  각 단계는 stub 단위테스트 + **실제 claude run 으로 출력 육안 검증**. codex 외부 리뷰
  (C10.1) 는 한시적으로 일시 중단(사용자 결정) — 깊이는 슬라이스 관통 후 보강.
- **이미 존재**: `SceneEntry`, `SceneManifest` (골격, schemas/models.py). 나머지 모델은 신규.
- **각 서브스텝 DoD**: py_compile + import smoke + 단위테스트 + CLI 1 서브커맨드 + state
  전이 + (해당 시) Review Gate 산출물. MINOR push 마다 codex 외부 리뷰 (C10.1),
  결과 흡수는 다음 PATCH. Phase 6 완료 marker 는 6E 직후.
- **공통 설계 원칙** (Phase 5 답습):
  - 모델은 `schemas/models.py` (SSOT), Pydantic v2, 가능하면 `schema_version` 1 유지(additive).
  - 워커는 `BaseLLMWorker` 상속, `build_user_prompt` 는 `.replace()` (C2), 사용자 질문 금지(C4).
  - 병합·판정 로직은 순수 함수, 디스크 I/O 는 별도 io 모듈 (예: `orchestrator/research_io.py`).
  - CLI 는 thin orchestration (`orchestrator/intake_service.py` 패턴) — precondition →
    atomic write → state 전이.
  - `manifest.initial_links` (사용자 분석 리포트) 는 **6A 에서 1차 자료 추출·교차검증의 입력**.
    리포트 자체는 2차/파생이므로 사실 앵커가 아니라 리서치 시드로 다룬다.

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
