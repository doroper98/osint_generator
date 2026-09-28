<!--
tier: 2
last_synced_with: v3.2.0
ssot_for: [json-contracts-overview]
depends_on: [../schemas/models.py]
last_review: 2026-09-28
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
| `intake/sources.json` (v3.2.0, 옛 `source_intake.json`·`SourceIntake` 삭제) | `source_models.SourcesFile` | 인테이크(CLI `add-source`·웹) + 사용자 확인 | 2 |
| `task_queue.json` | `TaskQueue` | Orchestrator | 3 |
| `worker_slots.json` | `WorkerSlotsSnapshot` | Worker Slot Manager | 3+ |
| `task_results/{task_id}_result.json` | `TaskResult` | Worker | 3+ |
| `intake/claims.json` (v3.2.0, 옛 `source_registry.json`·`source_completeness_report.json`·소스 수집 partial 삭제) | `source_models.ClaimsFile` | source_verify(VerifySourcesWorker 초안 → 코드 판정) | 4 |
| `facts.json` (v3.2.0, 옛 `research_dossier.json`·`ResearchDossier` 삭제) | `script.schema:Facts` | ResearchWorker | 5 |
| `report_bundle.json` (수신, 외부 연동) | `ReportBundle` | agents_reviewer (외부) | 외부 → 5 |
| `argument_map.json` | `ArgumentMap` | Research Agent | 5 |
| `episode_blueprint.json` | `EpisodeBlueprint` | Script Agent | 5 |
| `script.yaml` · `script_labels.json` | `script.schema:Script` · `script.labels:ScriptLabels` | Script Agent (v3.0.0) | 5 |
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
| schema_version | int | **2** (v3.0.0 — 상태 머신 교체. 1 이면 ManifestVersionError "재생성 필요") |
| project_id | str | UUID 또는 `proj_{YYYYMMDD}_{slug}` |
| title | str | 사용자가 의도한 제목 |
| category | enum | geopolitics / war_military / economy / disinformation / earthquake |
| created_at | datetime | UTC |
| updated_at | datetime | UTC |
| current_state | enum | `02_SYSTEM_ARCHITECTURE.md §4` 참조 |
| target_duration_min | int | 3–20 (ge=3, le=20) |
| topic_summary | str | |
| initial_links | list[str] | 생성 시 사용자 사전 제공 자료 링크. IntakePlanner 가 참고, 후속 단계의 manual_user_provided 후보 |
| paths | dict[str, str] | 주요 산출물 상대경로 인덱스(v3.0.0 — 16 §6 `project_manager.PROJECT_PATHS`) |
| render_mode_status | dict[str, str] | debug/preview/final 별 상태 |
| gate_decisions | list[`GateDecision`] | v3.0.0 — 승인 게이트 기록(gate·decision·by·at·comment·rollback_to·shown, v3.1.0 optional `chosen_version` = 게이트 ② 에서 고른 AI 연출 판). 옛 approval_status 대체 |
| stage_records | list[`StageRecord`] | v3.0.0 — 엔진 단계 실행 요약(전체 StageResult 는 logs/stages/) |
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
| worker_provenance | `WorkerProvenance` \| None | v2.0.0 — LLM 워커만. `{prompt_name, prompt_sha1, rules_hash}` (docs/handoff/15 P5). prompt_sha1 = `prompts/{prompt_name}.md` 렌더 결과의 sha1 |

### 3.4b (v3.2.0 삭제) `SourceCompletenessReport` — 소스 부족·출처 확인은 `intake/claims.json` 과 원고 출처 강제로 옮겼다(§8, D-0052 D52).

(이력) `source_completeness_report.json` 은 `source_registry.json` 에서 '부족 자료'(권리·신뢰도·위험 플래그)를
찾아 Review Gate 2 입력으로 쓰던 보고서였다. `CompletenessIssue*`·`SourceRegistry`·`SourceEntry` 와 함께 삭제(P2).
같은 이름의 `orchestrator/source_completeness_checker.py` 는 v3.2.0 에서 **원고 출처 검사**로 용도가 바뀌었다
(원고 문장의 claim id 가 claims.json 에 없거나 수치 문장에 출처가 없으면 SCRIPT_APPROVAL 전 차단).

### 3.4c (v3.2.0 삭제) `ResearchDossier` — 리서치 산출은 `facts.json`(`script/schema.py:Facts`), 검증 status 는 `intake/claims.json`(§8, D-0052 D52).

(이력) `research_dossier.json` 은 `ResearchWorker` 가 `source_registry.json`·`initial_links` 로 만든 주장-근거 페어
(`ResearchSeed`·`ResearchClaim`·`Evidence`, status 5종 confirmed/inferred/claim/unverified/disputed, `CLAIM_STATUS_LABELS`)였다.
`research_io`·번들 변환(`bundle_to_research_dossier`)과 함께 삭제(P2). 검증 라벨은 이제 claims.json status 4종에서
코드가 계산한다(`rules/video_rules.yaml script_schema.labels`). `ResearchClaimStatus` enum 은 report_bundle 계약 어휘로만 남았다.

### 3.4d (v3.0.0 삭제) `FullScript` — 원고 정본은 `projects/<pid>/script.yaml`(`script/schema.py:Script`, docs/handoff/02 §2.1).
검증 라벨은 `script_labels.json`(`script/labels.py:ScriptLabels`, 도시어 status 로 코드 계산, D-0043). 아래 표는 이력.

### (이력) `FullScript` (Phase 6 Script, Script Agent 산출)

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

`RenderSceneProps`: `sceneId`, `startSec`, `durationSec`, `caption`(중앙 key takeaway),
`narration`(full_script 에서 해석), `subtitleCues`(narration 을 줄 단위로 쪼갠 자막 큐 —
하단 자막 바에 **순차** 표시; 글자수 비례 추정 타이밍, scene 시작 기준 상대), `label`
(`<미검증>` 등 — 우상단 배지), `sourceLinkRequired`, `source`(상단 출처 표기 텍스트,
배선 전엔 ""), `isQuote`(인용이면 강조색+인용부호 렌더 — 영상 문법 ③), `audioPath`(V4b —
audio_manifest 가 있으면 나레이션 wav 의 project 상대경로; Remotion 이 `--public-dir`=
project_dir + `staticFile` 로 참조). audio_manifest 가 있으면 startSec/durationSec 는
**실측 음성 길이**로 재계산된다 (무음이면 scene 추정 유지).

영상 문법(v0.19.0): 화면엔 **key takeaway(caption)만 중앙**에 크게, **전체 나레이션은 하단
자막 바**, 좌상단 브랜드 / 상단 출처 / 우상단 검증 라벨 배지. 인용(`isQuote`)은 테마 강조색 +
인용부호로 명확히 구분. Remotion `Briefing` 컴포지션이 SSOT.

`mapData`(`RenderMap`: center/zoom/markers/arcs, v0.23.0 Phase B): scene 의 claim_refs 에
bundle map id 가 있으면 붙는다. Remotion `MapView`(d3-geo + world-atlas)가 중앙에 지도를
재렌더(마커·arc·highlight)하고 caption 은 제목으로 축소. `chartData`(`RenderChart`: type/title/data/unit): scene 의 claim_refs 에 지원 차트 id 가
있으면 붙는다. Remotion `ChartView` family 렌더러가 데이터로 **cinematic 재렌더**(line:
좌→우 draw-on + event 강조; v0.26.0). 지원 타입(v0.27.0): line/area/stacked_area/small_multiples/dual_line/forecast/bar/
lollipop/range_bar/stacked(_bar)/waterfall/scatter/bubble/candle/donut/gantt/slope/heatmap/
network/sankey/choropleth (전 타입). `render_io.SUPPORTED_CHART_TYPES` 가 SSOT. 미지원 타입은 텍스트 폴백(외부 SVG 폴백은 복잡 타입 한정 추후).

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

### 3.4g `ReportBundle` (외부 연동 — agents_reviewer 인터페이스 계약 v1)

`report_bundle.json` (수신) — agents_reviewer(텔레그램 보고서/분석 producer)가 emit 하는
핸드오프 산출물의 **소비자측 미러**다. (v3.2.0) `ResearchDossier` 변환은 삭제됐고, 번들 → sources.json·claims.json
변환이 Phase 9 에서 복귀할 때까지 `import-bundle` 은 명시 오류다(D52). 아래 변환 설명은 이력. 계약 정본은 agents_reviewer repo 의
`docs/CONTRACTS/report_bundle_v1.md` 이며, 본 모델은 수신 검증(fail-closed)용이다.

| 필드 | 타입 | 설명 |
|---|---|---|
| schema_version | int | 이 계약의 버전(현재 1). producer.version 과 분리 |
| bundle_kind | "report_bundle" | |
| producer / report | `BundleProducer` / `BundleReport` | 생산 시스템·보고서 메타(headline/deck/theme) |
| sections | list[`BundleSection`] | prose(나레이션 원천)·chart_refs·claim_refs |
| charts / map | list[`BundleChart`] / `BundleMap` | 차트 data 모양 SSOT 는 agents_reviewer schemas.py(§9) → `data: Any` |
| claims | list[`BundleClaim`] | status(=ResearchClaimStatus) 라벨 척추 단일 근거 |
| signals / contradictions / sources / confidence | list / Optional | 관찰 신호·모순·정규화 출처·신뢰도 |
| images | list[`BundleImage`] | 보도 사진(additive, v0.42.0). rights_status=cleared 만 영상 삽입(G4-8/C9). 계약: docs/IMAGE_BUNDLE_CONTRACT.md |

핵심 규약: ① **관대한 수신자(tolerant reader, `extra="ignore"`)** — 진화하는 보고서의
모르는 필드(새 top-level 블록·새 섹션 필드 등)는 무시해 추가 변경에 깨지지 않되, 선언 필드는
타입·enum·필수 검증(소비 데이터 건전성 유지). 미지 top-level 필드는 로더가 로그로 surface
(인지). 계약 §1 의 "additive=schema_version 무증분" 과 정합. ② `model_validator` 로 bundle 내
id unique + chart_refs/claim_refs resolve + `section.map_ref → map.id` resolve 강제,
③ 차트 `data` 는 재검증하지 않음(이중 SSOT 회피), ④ `provenance.verification` 을 그대로
신뢰(재검증 floor 없음). 진화 수용 예: v5.5.2 가 추가한 `timeline` 블록(모델에 흡수, 보관).

claims 분기(`orchestrator/bundle_io.py`): v5.5.0 real emit 은 `claims=[]`(라이브 2-call 은
산문+차트만 생성). 이때 어댑터가 **charts/map provenance + contradictions 에서 claim 을
합성**해 라벨 척추가 chart/map `verification` 을 타게 한다(measured→`<확인>`, narrative_
inference→`<추론>`, contradictions→`<반박됨>`). 섹션 prose 는 `summary` 로 실어 ScriptWorker
가 발화형으로 변환. bundle.claims 가 차 있으면(v5.6+) 그대로 직매핑. 변환 매핑(§9)은
`orchestrator/bundle_io.py:bundle_to_research_dossier` 참조.

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


## 6. v0.44.0 추가 모델 (쇼츠 콜라주 개편 Phase 0)

SSOT 는 `schemas/models.py`. 전부 additive — schema_version 1 유지.

| 모델 | 산출물 | 용도 |
|---|---|---|
| `BundleSectionVideo` / `BundleReportVideo` / `BundleTimelineVideo` | (수신) report_bundle | VIDEO_BUNDLE_CONTRACT 의 `video` 블록 정식 모델링 — 쇼츠 변환기는 raw dict 대신 본 모델 경유 (G4-5) |
| `AssetSourceRef`, `LibraryAssetVariant`, `LibraryPerson`, `LibraryLogo`, `LibraryFlag`, `AssetLibraryManifest` | `assets/library/library_manifest.json` | 인물·CI·국기 사전 구축 라이브러리 인덱스 + 권리 기록 (C9). id 유일성 검증 내장 |
| `SafeArea`, `DesignSheet` | `hyperframes/shorts/design_sheet.json` (Phase 3) | 디자인 시트 L1 토큰 운반 형식 — 값의 SSOT 는 [17_COLLAGE_DESIGN_SHEET.md](17_COLLAGE_DESIGN_SHEET.md) |

## 7. v2.4.0 추가 계약 (Phase 5 — 뱃지·엔티티·권리, back_and_forth D-0029)

필드 SSOT 는 코드다. 여기서는 위치와 규칙만 적는다.

| 파일 | 모델 | 규칙 |
|---|---|---|
| `assets/entities.yaml` | `schemas/entity_models.py` `EntitiesFile`·`Entity` | 인물·기관·국가. 라이브러리 24인(`library_manifest.json`) 자동 조인. 별칭 중복·미등재 참조 = `RegistryError`(15 P10) |
| `assets/emblems/registry.json` | `schemas/emblem_models.py` `EmblemRegistry`·`EmblemEntry` | `decision ∈ {use, flag_fallback}` 은 코드 규칙(`decide_emblem`)과 같아야 로드된다. Restrictions 하나라도 → `flag_fallback`(D5) |
| 프로젝트 `assets/rights_registry.json` | `schemas/engine_models.py` `RightsRegistry` | people·emblems + (선택) flags·music·fonts·map·narration(`AssetRights`). `rights_status`·`retrieved_at`·`processing` 선택 필드 추가(C3 호환) |
| `assets/rights_bundles.yaml` | `AssetRights` | 묶음 자산 권리 원본. `fetch_data people` 이 프로젝트 레지스트리에 병합 |
| 프로젝트 `credits.yaml` | `engine/credits.py` `Credits` | 항목 `rights: [절.키]`, 절 `auto: <절>`. 렌더가 쓰는 자산이 레지스트리에 없거나·미확인이거나·크레딧에 없으면 `RightsError` |
| provenance `assets` | `engine/mux.py asset_usage` | `images_used`, `emblems.{used, flag_fallback}`, `badges.{suggested, used, suggested_and_used}` |

## 8. v3.2.0 추가 계약 (Phase 6.95 — 소스 인테이크, back_and_forth D-0051, docs/handoff/18)

| 파일 | 모델 | 규칙 |
|---|---|---|
| 프로젝트 `intake/sources.json` | `schemas/source_models.py` `SourcesFile`·`XPostSource`·`ArticleSource`·`DocumentSource` | type 판별 3종(18 §2). 기사는 요지(`key_facts`)만, 원문 장문 금지. X 캡처는 `capture` 경로 필수. `confirmed_by` 가 비면 검증 단계로 못 간다(18 §7). `account_class` 는 `rules/official_accounts.yaml` 로 코드가 정한다 |
| 프로젝트 `intake/claims.json` | `ClaimsFile`·`Claim`·`ClaimSide` | `status ∈ {verified, corroborated, unverified, disputed}`. 분쟁 사안(`contested`)은 `sides ≥ 2` 가 없으면 `unverified` 만 허용(18 §3-5). 소스 id 는 sources.json 안(`check_claim_sources`) |
| 프로젝트 `intake/screenshots/<id>.png`·`intake/bodies/<id>.txt` | — | X 캡처 원본·기사/공문 본문. **비공개 보관**(레코드에는 요지만) |
| 프로젝트 `intake/drafts/<id>.json` | `CaptureDraft` | 캡처 판독 워커(`CaptureReadWorker`, vision) 초안. 소스 레코드로 합치는 것은 `orchestrator/source_intake` + 사용자 확인 |
| 프로젝트 `intake/verify_draft.json` | `VerifyDraft`·`ClaimCandidate`·`EvidenceQuote` | 검증 워커(`VerifySourcesWorker`) 초안 — 주장 후보와 소스 본문 인용. id·status 는 LLM 이 아니라 `orchestrator/source_verify.judge` 가 인용 대조로 정한다(D-0052 D50) |
| 프로젝트 `facts.json` | `script/schema.py` `Facts`·`Fact` | ResearchWorker 출력(claims.json → 사실 목록). `source_ids` = claims.json `claim_id`. 원고(ScriptWorker) 입력 = facts.json + claims.json |
| `rules/official_accounts.yaml` | `OfficialAccountsFile`·`OfficialAccount` | 공식 계정 목록(출처 URL·확인일). 미등재 핸들 = `unknown` |
