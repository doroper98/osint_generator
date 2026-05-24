<!--
tier: 2
last_synced_with: v0.12.0
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

### 3.4c `ResearchDossier` (Phase 6A, Research Agent 산출)

`research_dossier.json` — `ResearchWorker` 가 `source_registry.json` (사용 가능 소스)
와 `ProjectManifest.initial_links` (리서치 시드) 로부터 영상 서사의 주장-근거 페어를
정리한 결과. docs/12 §3 의 qa_evidence_report (6B) 와 docs/13 의 6C Blueprint 입력.

| 필드 | 타입 | 설명 |
|---|---|---|
| schema_version | int | 1 |
| project_id | str | manifest 와 동일 |
| generated_at | datetime | UTC |
| topic | str | 영상 1줄 주제 |
| summary | str | 리서치 총평 (핵심 발견·미확인 영역) |
| seeds | list[`ResearchSeed`] | initial_links 유래 = 2차/파생 분석 (사실 앵커 아님) |
| claims | list[`ResearchClaim`] | 주장-근거 페어 |
| open_questions | list[str] | 추가 1차 확인 필요 질문 |

`ResearchSeed`: `seed_id`, `url`, `description`, `is_derivative`(기본 True),
`requires_verification`(기본 True). 사용자 사전 제공 리포트는 파생 분석이므로 1차
출처로 별도 교차검증 필요.

`ResearchClaim`: `claim_id`, `statement`, `status` (`ResearchClaimStatus`:
confirmed / inferred / claim / unverified / disputed), `evidence`
(list[`Evidence`]), `cross_checked`, `confidence` (low/medium/high), `notes`,
`risk_flags`. `display_label` 은 status 에서 파생되는 읽기 전용 속성
(`<확인>`/`<추론>`/`<주장>`/`<미검증>`/`<반박됨>`, `CLAIM_STATUS_LABELS` 매핑) —
status 가 SSOT 이며 라벨은 직렬화되지 않음.

`Evidence`: `source_id` (registry 1차 자료 인용) / `seed_id` (파생 시드 인용) 중
하나 이상, `quote`, `locator`, `stance` (supports/refutes/contextual). registry
source_id 존재 여부의 cross-check 는 6B Evidence Guard 책임 (본 스키마엔 validator 없음).

### 3.4d `FullScript` (Phase 6 Script, Script Agent 산출)

`full_script.json` — `ScriptWorker` 가 `research_dossier.json` 으로부터 영상 나레이션
대본을 생성. docs/12 §1 의 `script_review` (Review Gate 4) 입력이며 Scene Planner 입력.

| 필드 | 타입 | 설명 |
|---|---|---|
| schema_version | int | 1 |
| project_id | str | |
| generated_at | datetime | UTC |
| title / topic | str | 영상 제목 / 1줄 주제 |
| target_duration_min | int | 3~20 |
| chapters | list[`ScriptChapter`] | 서사 챕터 (chapter_id/title/summary) |
| segments | list[`ScriptSegment`] | 나레이션 세그먼트 |
| total_est_duration_sec | float | segment est_duration_sec 합 근사 |

`ScriptSegment`: `segment_id`, `chapter_id`, `narration`(TTS 본문), `on_screen_caption`,
`claim_refs`(research_dossier claim_id), `label`(`<미검증>` 등 — claim status 유래,
미검증/추론/주장/반박 항목 분리. confirmed 만이면 null), `est_duration_sec`. 미검증
정보의 제목/썸네일 사용 금지(GOAL G4)는 label 로 추적.

### 3.4e `RenderProps` (수직 슬라이스 V3, Remotion 렌더 입력)

`09_render/render_props.json` — scene_manifest(타이밍/라벨 신호) + full_script(나레이션/
캡션)를 합쳐 만든 Remotion `Briefing` 컴포지션 입력. 텍스트 슬라이드 렌더용 최소 평면
구조 (정식 `RemotionJob`/render_worker 는 Phase 9 에서). 필드명은 TS 친화 camelCase.

| 필드 | 타입 | 설명 |
|---|---|---|
| schema_version | int | 1 (Remotion 측은 무시) |
| project_id | str | |
| title | str | 영상 제목 |
| fps / width / height | int | 기본 30 / 1920 / 1080 |
| scenes | list[`RenderSceneProps`] | 슬라이드 목록 |

`RenderSceneProps`: `sceneId`, `startSec`, `durationSec`, `caption`, `narration`
(narration_segment_ids 로 full_script 에서 해석), `label`(`<미검증>` 등 — 배지 표기),
`sourceLinkRequired`.

### 3.4f `AudioManifest` (Phase 8 TTS, 수직 슬라이스 V4)

`08_audio/audio_manifest.json` — full_script 의 각 세그먼트를 TTS 로 합성한 결과.
백엔드 교체 가능(local/elevenlabs/stub). wav 는 `08_audio/narration/{segment_id}.wav`
(gitignore), 본 manifest 만 추적. **실제 음성 길이**를 담아 후속 scene/render 타이밍의
권위 소스가 된다.

| 필드 | 타입 | 설명 |
|---|---|---|
| schema_version | int | 1 |
| project_id | str | |
| generated_at | datetime | UTC |
| backend | str | stub / local / elevenlabs |
| total_duration_sec | float | 세그먼트 길이 합 |
| segments | list[`AudioSegment`] | |

`AudioSegment`: `segment_id`(full_script ScriptSegment 대응), `audio_path`(project
상대경로), `duration_sec`(실측), `text`, `backend`, `voice`. 백엔드 정책은
`workers/tts_backends.py` (기본 local=프라이버시, elevenlabs=opt-in 외부 API).

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
