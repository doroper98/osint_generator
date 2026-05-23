<!--
tier: 2
last_synced_with: v0.7.2
ssot_for: [json-contracts-overview]
depends_on: [../schemas/models.py]
last_review: 2026-05-23
-->

# 05 — Data Schema Spec

> **SSOT 주의**: 실제 필드 정의의 SSOT는 `schemas/models.py`의 Pydantic 클래스입니다.
> 본 문서는 인덱스와 운영 가이드만 제공합니다. 필드를 추가/변경할 때는 코드를 먼저 수정한 뒤 본 문서를 동기화하세요.

## 1. 공통 규칙

- 모든 JSON은 최상단에 `schema_version: int` 필드를 갖습니다.
- 현재 schema_version = **1**.
- 모든 시각은 ISO 8601 UTC (`2026-05-19T13:42:11Z`).
- 모든 경로는 프로젝트 루트(`projects/{project_id}/`) 기준 상대 경로.
- `null` 보다 누락을 선호. Optional 필드는 기본값 사용.

## 2. JSON 산출물 인덱스

| 파일 | Pydantic 모델 | 생성 주체 | 단계 |
|---|---|---|---|
| `project_manifest.json` | `ProjectManifest` | Orchestrator | 0 → 모든 단계 |
| `intake_plan.json` | `IntakePlan` | Dynamic Intake Planner | 1 |
| `source_intake.json` | `SourceIntake` | Web App | 2 |
| `task_queue.json` | `TaskQueue` | Orchestrator | 3 |
| `worker_slots.json` | `WorkerSlotsSnapshot` | Worker Slot Manager | 3+ |
| `task_results/{task_id}_result.json` | `TaskResult` | Worker | 3+ |
| `source_registry.json` | `SourceRegistry` | Source Registry Builder | 4 |
| `source_completeness_report.json` | `SourceCompletenessReport` | Orchestrator | 4 |
| `research_dossier.json` | `ResearchDossier` | Research Agent | 5 |
| `argument_map.json` | `ArgumentMap` | Research Agent | 5 |
| `episode_blueprint.json` | `EpisodeBlueprint` | Script Agent | 5 |
| `full_script.json` | `FullScript` | Script Agent | 5 |
| `qa_evidence_report.json` | `QAEvidenceReport` | Evidence Guard | 5 |
| `scene_manifest.json` | `SceneManifest` | Scene Planner | 6 |
| `asset_manifest.json` | `AssetManifest` | Orchestrator | 7 |
| `annotation_manifest.json` | `AnnotationManifest` | Annotation Worker | 7 |
| `narration_segments.json` | `NarrationSegments` | Script Agent | 8 |
| `audio_manifest.json` | `AudioManifest` | TTS Worker | 8 |
| `tts_qa_report.json` | `TTSQAReport` | TTS QA Worker | 8 |
| `music_manifest.json` | `MusicManifest` | Music Worker | 8 |
| `remotion_job_debug.json` | `RemotionJob` | Remotion Job Builder | 9 |
| `remotion_job_preview.json` | `RemotionJob` | Remotion Job Builder | 9 |
| `remotion_job_final.json` | `RemotionJob` | Remotion Job Builder | 9 |
| `render_report.json` | `RenderReport` | Render Worker | 9 |
| `thumbnail_brief.json` | `ThumbnailBrief` | Thumbnail Agent | 10 |
| `thumbnail_manifest.json` | `ThumbnailManifest` | Thumbnail Worker | 10 |
| `thumbnail_qa.json` | `ThumbnailQA` | Thumbnail Worker | 10 |
| `youtube_metadata.json` | `YouTubeMetadata` | YouTube Metadata Agent | 11 |
| `approval_log.json` | `ApprovalLog` | Orchestrator | 모든 단계 |

## 3. 핵심 모델 요약 (필드 SSOT는 코드)

### 3.1 `ProjectManifest`

| 필드 | 타입 | 설명 |
|---|---|---|
| schema_version | int | 1 |
| project_id | str | UUID 또는 `proj_{YYYYMMDD}_{slug}` |
| title | str | 사용자가 의도한 제목 |
| category | enum | geopolitics / war_military / economy / disinformation / earthquake |
| created_at | datetime | UTC |
| updated_at | datetime | UTC |
| current_state | enum | `02_SYSTEM_ARCHITECTURE.md §4` 참조 |
| target_duration_min | int | 3–20 (ge=3, le=20) |
| topic_summary | str | |
| initial_links | list[str] | 생성 시 사용자 사전 제공 자료 링크. IntakePlanner 가 참고, 후속 단계의 manual_user_provided 후보 |
| paths | dict[str, str] | 주요 산출물 상대경로 인덱스 |
| render_mode_status | dict[str, str] | debug/preview/final 별 상태 |
| approval_status | dict[str, str] | gate_id → status |
| final_outputs | dict[str, str] | 최종 산출물 경로 |

### 3.2 `TaskQueue` / `TaskQueueItem`

| 필드 | 타입 | 설명 |
|---|---|---|
| task_id | str | `task_{seq:04d}` |
| input_item_id | str | intake_plan 항목 id 또는 내부 생성 |
| assigned_worker | str | Worker 모듈명 (`video_acquisition_worker`) |
| task_type | str | Worker 카탈로그 참조 |
| description | str | 사람이 읽는 설명 |
| status | enum | queued / assigned / running / completed / failed / needs_user_upload / needs_user_confirmation / rights_review_required / skipped |
| priority | enum | low / normal / high / must_use |
| depends_on | list[str] | 선행 task_id 목록 |
| parallelizable | bool | 빈 Worker Slot이면 동시 실행 가능 |
| input_refs | list[str] | 입력 파일 상대경로 |
| output_refs | list[str] | 예상 출력 파일 상대경로 |
| error_message | str \| None | 실패 시 채워짐 |

### 3.3 `WorkerSlot` / `WorkerSlotsSnapshot`

| 필드 | 타입 | 설명 |
|---|---|---|
| slot_id | int | 1..N |
| status | enum | idle / assigned / running / completed / failed / waiting_user / stale |
| assigned_task_id | str \| None | |
| assigned_worker | str \| None | |
| started_at | datetime \| None | |
| last_heartbeat | datetime \| None | |
| progress | float | 0.0–1.0 |
| log_path | str \| None | 워커 로그 파일 상대경로 |

### 3.4 `TaskResult`

| 필드 | 타입 | 설명 |
|---|---|---|
| task_id | str | |
| worker | str | |
| status | enum | TaskStatus 동일 |
| started_at / completed_at | datetime | |
| outputs | list[str] | 실제 생성된 파일 경로 |
| warnings | list[str] | |
| errors | list[str] | |
| scene_refs | list[str] | 영향을 미치는 scene_id |
| source_refs | list[str] | 사용된 source_id |
| asset_refs | list[str] | 생성한 asset_id |
| qa_status | enum | pass / warn / fail / pending |
| risk_flags | list[str] | `graphic_content`, `youtube_age_restriction_risk` 등 |

### 3.4b `SourceCompletenessReport` (Review Gate 2 입력)

`source_completeness_report.json` — Orchestrator 가 `source_registry.json` 으로부터
'부족 자료' 를 식별한 결과. Review Gate 2 (`source_completeness_review`) 입력.

| 필드 | 타입 | 설명 |
|---|---|---|
| schema_version | int | 1 |
| project_id | str | registry 와 동일 |
| generated_at | datetime | UTC |
| reliability_threshold | float | `reliability_score <` 비교 임계 (기본 0.5, 범위 0.0~1.0) |
| total_sources | int | registry 의 전체 소스 수 |
| usable_sources | int | `rights_clear` / `manual_user_provided` 수 (정책 §2 ✅) |
| blocker_count / warning_count / info_count | int | severity 별 이슈 수 |
| overall_status | enum | `ready` / `needs_attention` / `insufficient` |
| issues | list[`CompletenessIssue`] | 이슈 목록 |

`CompletenessIssue`: `issue_type` (no_usable_sources / rights_do_not_use /
rights_review_required / rights_unknown / source_unusable / low_reliability /
risk_flag_present / rights_status_unknown_value), `severity` (blocker / warning
/ info), `source_id` (registry-level 이슈는 null), `detail`, `recommendation`.
`rights_status_unknown_value` 는 정책 §2 에 정의되지 않은 권리 상태(스키마 drift)
전용 — known `review_required` 와 구분되는 보수적 `warning` 진단.

**severity 정책**: 사용 가능 자료가 0개일 때만 `blocker` (`no_usable_sources`).
권리 미확보·신뢰도 낮음·위험 플래그는 `warning`, `rights_unknown` 은 `info`.
부족 여부의 최종 판단은 Review Gate 2 에서 사용자가 수행 (`docs/06` §2 근거).

### 3.5 `SceneManifest` Provenance

`SceneEntry.worker_provenance`:

| 필드 | 타입 | 설명 |
|---|---|---|
| primary_worker | str | |
| supporting_workers | list[str] | |
| generated_files | list[str] | |
| input_manifests | list[str] | |
| source_ids | list[str] | |
| asset_ids | list[str] | |
| task_ids | list[str] | |
| qa_status | enum | |
| risk_flags | list[str] | |

본 정보가 Pre-production Debug Layer의 입력입니다. [ADDENDUM_02](ADDENDUM_02_PRE_PRODUCTION_DEBUG_LAYER.md) 참조.

## 4. Render Mode

`render_mode ∈ {"debug", "preview", "final"}`

- debug → `DebugOverlay`가 활성화 → `draft_debug.mp4`
- preview → Debug Layer 비활성 → `draft_preview.mp4`
- final → Debug Layer 비활성 → `final.mp4`

이 값은 `RemotionJob.render_mode`에서만 전달되며, Remotion 컴포넌트는 props로 받습니다.

## 5. 스키마 버전 증분

- 필드 추가 (optional): schema_version 유지
- 필드 제거: schema_version 증분 + 마이그레이션 함수 작성
- 필드 의미 변경: schema_version 증분 필수

마이그레이션 함수는 `schemas/migrations/v{from}_to_v{to}.py`로 둡니다. (Phase 후속)
