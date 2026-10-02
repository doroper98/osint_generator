<!--
tier: 2
last_synced_with: v5.4.0
ssot_for: [json-contracts-overview]
depends_on: [../schemas/models.py, ../schemas/source_models.py, ../schemas/engine_models.py, ../script/schema.py, ../engine/direction.py, ../engine/qa.py, ../orchestrator/config.py]
last_review: 2026-09-29
-->

# 05 — Data Schema Spec

> **SSOT 주의**: 실제 필드 정의의 SSOT는 `schemas/models.py`의 Pydantic 클래스입니다.
> 본 문서는 인덱스와 운영 가이드만 제공합니다. 필드를 추가/변경할 때는 코드를 먼저 수정한 뒤 본 문서를 동기화하세요.

## 1. 공통 규칙

- 모든 JSON은 최상단에 `schema_version: int` 필드를 갖습니다.
- 현재 schema_version = **1**. 예외: `project_manifest.json` = **2**(v3.0.0 상태 머신 교체, MAJOR).
- 모든 시각은 ISO 8601 UTC (`2026-05-19T13:42:11Z`).
- 모든 경로는 프로젝트 루트(`projects/{project_id}/`) 기준 상대 경로.
- `null` 보다 누락을 선호. Optional 필드는 기본값 사용.

## 2. 산출물 인덱스 (v4.0.0 실측 — 프로젝트 `projects/<pid>/` 기준)

| 파일 | 모델(필드 SSOT) | 만드는 주체 | 상태 |
|---|---|---|---|
| `project_manifest.json` | `schemas.models.ProjectManifest`(sv 2, `gate_decisions`·`stage_records`) | 오케스트레이터 | 전 단계 |
| `intake_plan.json` | `IntakePlan` | IntakePlannerWorker | INTAKE |
| `intake/sources.json` | `schemas.source_models.SourcesFile` | 인테이크(CLI·웹) + 사용자 확인 | INTAKE |
| `intake/drafts/<id>.json` | `CaptureDraft` | CaptureReadWorker | INTAKE |
| `intake/verify_draft.json` | `VerifyDraft` | VerifySourcesWorker | SOURCE_VERIFY |
| `intake/claims.json` | `ClaimsFile` | `orchestrator/source_verify`(코드 판정) | SOURCE_VERIFY |
| `facts.json` | `script.schema.Facts` | ResearchWorker | RESEARCH |
| `script.yaml`, `script_labels.json` | `script.schema.Script`, `script.labels.ScriptLabels` | ScriptWorker(또는 사람) | SCRIPT_DRAFT |
| `plan.json`, `tts/*.mp3(.align.json)` | `script.schema.Plan` | `script.plan` | VOICE_TIMELINE |
| `geo.yaml`, `labels.yaml` | `geo.prep` 설정 모델, 라벨 모델 | 사람 | ASSETS |
| `assets/{geo.pkl, tiers.pkl, base_*.png, geo_report.json}`, `assets/res_<프로파일>/` | `schemas.engine_models.Tier` | `geo.prep` | ASSETS |
| `assets/rights_registry.json`, `credits.yaml` | `RightsRegistry`, `engine.credits.Credits` | 사람·`tools/fetch_data` | ASSETS |
| `direction.yaml`(+`direction.v*.yaml`, `direction.meta.json`) | `engine.direction.Direction` | DirectorWorker(또는 사람) | DIRECTION |
| `prev/checks.json`, `prev/frames.json`, `prev/provenance.json`, `prev/sheet.jpg` | `engine/checks.py` 출력(sv 1) | `engine.render --preview` | PREVIEW_QA |
| `prev/qa_verdict.v*.json`, `prev/qa_loop.json` | `engine.qa.QAVerdict`, `engine.qa.QALoopRecord` | VisualQAWorker·`orchestrator/ai_direction` | PREVIEW_QA |
| `out/video_noaudio.mp4`, `out/render.json` | render 기록(sv 1 — `resolution`·jobs·프레임·시간·RSS) | `engine.render` | RENDER |
| `out/mix.f32` | — | `audio.mix` | AUDIO_MIX |
| `out/final.mp4`, `final.srt`, `description.txt`, `provenance.json` | provenance 필수 키 = `rules/video_rules.yaml provenance.required_keys` | `engine.mux` | DELIVER |
| `task_queue.json`, `worker_slots.json`, `task_results/*.json`, `llm_calls/*.json` | `TaskQueue`, `WorkerSlotsSnapshot`, `TaskResult`, `LLMCallRecord` | 오케스트레이터·워커 | 전 단계 |
| 엔진 CLI 마지막 줄 | `schemas.engine_models.StageResult` | 엔진 CLI 전부 | — |

`direction.yaml` 무대 표기(v4.1.0, back_and_forth D-0076 작업 4·D-0077): 최상위 `stage`(주 무대)와 숏 단위 `shots[].stage`(선택). 없으면 장르 프로필의 `stage.primary`(기본 장르 geopolitics = mercator, v4.2.0)이고 provenance `stage.declared` 가 false 다. 있으면 장르 프로필 주·보조 무대 안이어야 한다. 이름은 `rules:registries.stages` 에 있어야 한다(없으면 스키마 오류). 무대마다 프리뷰 예제 `tests/fixtures/preview/stage_{이름}.yaml`.

`direction.yaml` 장르(v4.2.0, back_and_forth D-0081 작업 3): 최상위 `genre`(선택, 없으면 geopolitics — provenance `genre.declared` false). 장르 프로필 `genres/<genre>.yaml` = `schemas.genre_models.GenreProfile`(extra forbid, `rules:registries` 이름만). 프리미티브 이벤트 `{type: primitive, id}` 의 데이터 모델 = `engine/primitives/<id>.py` `SCHEMA`(봉투 `engine.events._Primitive` 와 합쳐 검증).

`direction.yaml` 시간축(v4.3.0, back_and_forth D-0084·D-0085·D-0088): `stage_config.timeline`(`engine/stage_timeline.py:TimelineConfig` — start·end·lanes·compress, 레인 기본값 = 장르 프로필), 카메라 `{date, lane?, w}`, 핀 `marker {date, lane}`, `series` 이벤트(`engine.events.SeriesEvent` — lane·series_id·style·grow·col, 값 필드 없음), 숏 `reason`. 데이터 레코드 `data/series/<id>.yaml`+`.csv`(+`raw/`) = `schemas.data_models.SeriesRecord`(extra forbid, 허용 목록 `rules:data`, 빈 달 `missing`). 원고 `sources` 의 `series:<id>` 는 레코드 참조(claim 아님). 엔딩 크레딧 절 `auto: series`.

번들 가져오기(`import-bundle`) 산출물은 §10, 저장소 공용 레지스트리(엔티티·휘장·미디어·BGM)는 §7·§9.
`approval_log.json`(`ApprovalLog`)·`thumbnail_manifest.json`(`ThumbnailManifest`)은 **삭제됨**(v4.0.0, back_and_forth D-0073, 보존 `archive/hyperframes-briefing`). 게이트 기록은 manifest `gate_decisions`다.

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

### 3.4e·3.4f (v2.0.0 삭제) `RenderProps`·`AudioManifest` — Remotion 렌더 입력·세그먼트 TTS 기록. 렌더 입력은 `script.yaml`+`plan.json`+`direction.yaml`, 음성은 `plan.json`(§2). 보존본 `archive/hyperframes-briefing`.

### 3.4g `ReportBundle` (외부 연동 — agents_reviewer 계약 v1, 수신 전용)

`report_bundle.json`은 agents_reviewer가 내는 핸드오프 산출물이다. 이 저장소의 모델은 **소비자측 미러**이고 계약 정본은 agents_reviewer의 `docs/CONTRACTS/report_bundle_v1.md`다.
로더는 `bundle/load.py`(`load_report_bundle`)다(v3.5.0 이동).

- **fail-closed**(v3.5.0 D-0064 쟁점 1 A): 번들 모델 베이스 `_BundleModel`은 `extra="forbid"`다. 선언하지 않은 필드가 있으면 모든 깊이의 경로를 한 번에 나열하는 `UnknownBundleFields` 오류로 멈춘다.
  옛 관대한 수신자(`extra="ignore"`)는 마커 종류·호 종류·논쟁 영상 문구를 조용히 버렸다(15 P6·P10). agents_reviewer가 필드를 더하면 이 파일 선언을 같이 바꾼다.
- id 유일성·`chart_refs`/`claim_refs`/`map_ref` 해석은 `model_validator`가 강제한다. 차트 `data`는 다시 검증하지 않는다(이중 SSOT 회피).
- 번들은 **재료**다(handoff 12 §5). 번들 → 원고·연출 변환은 §10.

### 3.5·§4 (v2.0.0 삭제) `SceneManifest` provenance·Render Mode

`scene_manifest`·`worker_provenance`·`render_mode ∈ {debug, preview, final}`·`RemotionJob`은 v2.0.0에서 삭제됐다(G3-legacy 19·20·26·27).
"이번 영상에 실제로 쓰인 것"은 `provenance.json`(15 P5)이, 해상도는 출력 프로파일(§9)이 맡는다.

## 5. 스키마 버전 증분

- 필드 추가 (optional): schema_version 유지
- 필드 제거: schema_version 증분 + 마이그레이션 함수 작성
- 필드 의미 변경: schema_version 증분 필수

마이그레이션 함수는 `schemas/migrations/v{from}_to_v{to}.py`로 둡니다. (Phase 후속)


## 6. v0.44.0 추가 모델 (쇼츠 콜라주 — 일부만 남음)

| 모델 | 산출물 | 상태 |
|---|---|---|
| `BundleSectionVideo` / `BundleReportVideo` / `BundleTimelineVideo` | (수신) report_bundle `video` 블록 | 유지 — 번들 모델(§3.4g) |
| `AssetSourceRef`, `LibraryAssetVariant`, `LibraryPerson`, `LibraryLogo`, `LibraryFlag`, `AssetLibraryManifest` | `assets/library/library_manifest.json` | 유지 — 인물·CI·국기 라이브러리 인덱스 + 권리(C9). 엔티티 레지스트리의 1차 소스(§7) |
| `SafeArea`, `DesignSheet` | (쇼츠 디자인 시트) | v2.0.0 삭제(쇼츠 트랙 보관, G5) |

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
| 프로젝트 `intake/claims.json` | `ClaimsFile`·`Claim`·`ClaimSide` | `status ∈ {verified, corroborated, unverified, disputed}`. 분쟁 사안(`contested`)은 `sides ≥ 2` 가 없으면 `unverified` 만 허용(18 §3-5). 소스 id 는 sources.json 안(`check_claim_sources`). `claim_kind ∈ {fact, statement}`(기본 fact, v5.0.0 GOAL G4-21 — optional 이라 `schema_version` 1 유지): fact = 내용 자체, statement = "그런 발언·보도가 있었다"(귀속 인용을 supports 로 센다). 값은 `judge` 가 확정한다 |
| 프로젝트 `intake/screenshots/<id>.png`·`intake/bodies/<id>.txt` | — | X 캡처 원본·기사/공문 본문. **비공개 보관**(레코드에는 요지만) |
| 프로젝트 `intake/drafts/<id>.json` | `CaptureDraft` | 캡처 판독 워커(`CaptureReadWorker`, vision) 초안. 소스 레코드로 합치는 것은 `orchestrator/source_intake` + 사용자 확인 |
| 프로젝트 `intake/verify_draft.json` | `VerifyDraft`·`ClaimCandidate`·`EvidenceQuote` | 검증 워커(`VerifySourcesWorker`) 초안 — 주장 후보와 소스 본문 인용. id·status 는 LLM 이 아니라 `orchestrator/source_verify.judge` 가 인용 대조로 정한다(D-0052 D50). `ClaimCandidate.claim_kind` 는 LLM 의 kind **후보**(기본 fact) — 확정은 코드(v5.0.0 G4-21). `speaker_source_ids`(optional) = statement 발언 주체 본인 소스 후보 — 코드가 공식·사용자 확인일 때만 인정(D-0122) |
| 프로젝트 `facts.json` | `script/schema.py` `Facts`·`Fact` | ResearchWorker 출력(claims.json → 사실 목록). `source_ids` = claims.json `claim_id`. 원고(ScriptWorker) 입력 = facts.json + claims.json |
| `rules/official_accounts.yaml` | `OfficialAccountsFile`·`OfficialAccount` | 공식 계정 목록(출처 URL·확인일). 미등재 핸들 = `unknown` |

## 9. v3.6.0 추가 계약 (Phase 10 — 출력 프로파일)

| 위치 | 모델 | 규칙 |
|---|---|---|
| `config.yaml engine.output` | `orchestrator/config.py` `OutputConfig`·`OutputProfile` | 프로파일 표(폭·높이·fps·crf·preset·청크당 메모리)와 기본값. fps는 설계 fps와 같아야 한다. 모르는 프로파일 이름 = 오류 |
| `config.yaml engine.output.profiles.<이름>.clip` | `OutputProfile.clip` | (v4.0.0 D-0074) 그 프로파일의 영상 클립 npy 크기 [폭, 높이], 16:9 검증. 기본 프로파일은 없음(레지스트리 scale). 파일 `media/res_<이름>/{file}.npy`, 없으면 렌더 오류 |
| `config.yaml engine.trial`·`engine.final` | `EngineConfig` | 별칭(트라이얼 480p·최종 1080p). CLI `--res` 가 이름·별칭을 받는다 |
| `config.yaml engine.render.jobs` | `RenderConfig` | 청크 병렬 수(null = CPU 수), 메모리 ÷ 프로파일 상한으로 줄임 |
| provenance `render.resolution`, `out/render.json` | 렌더 기록(sv 1) | 프로파일·폭·높이·fps·k·pad_x·crf·preset(+전편은 jobs·프레임·시간·청크 피크 RSS) |
| `assets/media/media_registry.json` | `schemas/media_models.py` `MediaRegistryFile`·`MediaAsset`·`SourceVariant` | 미디어 권리·검증·가공 기록. 장치 해상도 원본은 variant로 기록(업스케일 = checks warning) |

설계 좌표는 한 벌(`rules/video_rules.yaml layout_480p.base`)이다. 해상도 변환은 렌더 진입 장치 변환 한 곳이다(D60, [10](10_RENDERING_PIPELINE_SPEC.md) §4).

## 10. v3.5.0 추가 계약 (Phase 9 — 번들 어댑터, back_and_forth D-0063)

`python -m orchestrator.main import-bundle <pid> --file <bundle.json>`이 만드는 파일이다. 최종 `script.yaml`·`direction.yaml`·`claims.json`은 쓰지 않는다.

| 파일 | 모델 | 규칙 |
|---|---|---|
| `intake/files/<번들>` | `ReportBundle`(§3.4g) | 원본 보관 |
| `intake/sources.json`(기사 레코드 추가) | `ArticleSource` | 인용 문자열 → 기사 가져오기. 본문·제목·매체·게시일이 안 차면 만들지 않는다. 사용자 확인 전 |
| `intake/bundle_import.json` | `orchestrator/bundle_service` 기록 | 이관·`unresolved_sources[]`(blocked_host·fetch_failed·missing). 게이트 ①·소스 확인 화면·provenance가 읽음 |
| `intake/bundle_claims.json` | `bundle.to_sources.BundleClaimsFile` | claim 후보(번들 status는 참고). 검증 워커의 `{bundle_hints}` 재료 |
| `script.draft.yaml`, `script.draft.notes.json` | `script.schema.Script`, `bundle.to_script.DraftNotes` | 장면 묶음 제안·금지 문구 `rewrite_required` 주석. ScriptWorker `{draft_block}` 재료 |
| `intake/bundle_materials.json`, `direction.draft.yaml` | `bundle.to_direction.BundleMaterials`, `Direction` | 장소·경로·패널·미디어·뱃지·인용 재료. 패널 렌더러 없는 차트는 `unsupported[]`. DirectorWorker `{bundle_materials}` 재료 |
| provenance `bundle` | — | 번들 id·producer·섹션/장면·rewrite_required·unmatched·패널·출처 이관/미해결·`draft_used` |

어휘 대응(차트 → 패널 종류, 관계 종류, 검증 판정 기준)은 `rules/video_rules.yaml bundle`이다(15 P3).

