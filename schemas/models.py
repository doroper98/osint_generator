"""longform-briefing-pipeline 의 도메인 Pydantic 모델 SSOT.

원칙
----
- 모든 JSON 산출물은 본 모듈의 모델 중 하나로 직렬화/역직렬화 가능해야 합니다.
- 모든 모델은 `schema_version` 필드를 갖습니다 (현재 1).
- 신규 필드는 optional로 추가 → schema_version 유지. Breaking change는 schema_version 증분.
- raw dict 로 도메인 데이터를 다루지 마십시오.

본 파일이 변경되면 docs/05_DATA_SCHEMA_SPEC.md 와 docs/03_AGENT_ARCHITECTURE.md 가
동기화 대상입니다 (DOCS_GOVERNANCE.md §5).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

__schema_version__: int = 1


# ---------------------------------------------------------------------------
# Enum / Literal 타입
# ---------------------------------------------------------------------------


class Category(str, Enum):
    """주제 카테고리. GOAL.md G2 와 동기화."""

    GEOPOLITICS = "geopolitics"
    WAR_MILITARY = "war_military"
    ECONOMY = "economy"
    DISINFORMATION = "disinformation"
    EARTHQUAKE = "earthquake"


class ProjectState(str, Enum):
    """프로젝트 상태 머신. docs/02_SYSTEM_ARCHITECTURE.md §4 와 동기화."""

    CREATED = "created"
    INTAKE_PLANNING = "intake_planning"
    INTAKE_PENDING_USER = "intake_pending_user"
    SOURCE_COLLECTING = "source_collecting"
    SOURCE_COMPLETENESS_REVIEW = "source_completeness_review"
    RESEARCH_IN_PROGRESS = "research_in_progress"
    BLUEPRINT_REVIEW = "blueprint_review"
    SCRIPT_WRITING = "script_writing"
    SCRIPT_REVIEW = "script_review"
    SCENE_PLANNING = "scene_planning"
    ASSET_PRODUCTION = "asset_production"
    SCENE_REVIEW = "scene_review"
    AUDIO_PRODUCTION = "audio_production"
    RENDER_DEBUG = "render_debug"
    DEBUG_REVIEW = "debug_review"
    RENDER_PREVIEW = "render_preview"
    PREVIEW_REVIEW = "preview_review"
    THUMBNAIL_PRODUCTION = "thumbnail_production"
    THUMBNAIL_REVIEW = "thumbnail_review"
    RENDER_FINAL = "render_final"
    FINAL_REVIEW = "final_review"
    PUBLISH_READY = "publish_ready"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_USER_UPLOAD = "needs_user_upload"
    NEEDS_USER_CONFIRMATION = "needs_user_confirmation"
    RIGHTS_REVIEW_REQUIRED = "rights_review_required"
    SKIPPED = "skipped"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    MUST_USE = "must_use"


class WorkerSlotStatus(str, Enum):
    IDLE = "idle"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_USER = "waiting_user"
    STALE = "stale"


class QAStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    PENDING = "pending"


class RightsStatus(str, Enum):
    """docs/06_SOURCE_AND_RIGHTS_POLICY.md §2 와 동기화."""

    RIGHTS_CLEAR = "rights_clear"
    RIGHTS_UNKNOWN = "rights_unknown"
    REVIEW_REQUIRED = "review_required"
    MANUAL_USER_PROVIDED = "manual_user_provided"
    DOWNLOAD_FAILED = "download_failed"
    LOGIN_REQUIRED = "login_required"
    PRIVATE_OR_DELETED = "private_or_deleted"
    DO_NOT_USE = "do_not_use"


class IntakeMode(str, Enum):
    """docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md §3 와 동기화."""

    DIRECT_PROVIDE = "direct_provide"
    LINK_PROVIDE = "link_provide"
    GDRIVE_PROVIDE = "gdrive_provide"
    FILE_UPLOAD = "file_upload"
    AI_DELEGATE = "ai_delegate"
    MIXED = "mixed"
    SKIP = "skip"
    MUST_USE = "must_use"
    REFERENCE_ONLY = "reference_only"


class RenderMode(str, Enum):
    DEBUG = "debug"
    PREVIEW = "preview"
    FINAL = "final"


# ---------------------------------------------------------------------------
# 공통 베이스
# ---------------------------------------------------------------------------


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VersionedModel(BaseModel):
    """모든 직렬화 산출물의 공통 베이스. schema_version 필드를 강제."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    schema_version: int = Field(default=__schema_version__)


# ---------------------------------------------------------------------------
# 1. ProjectManifest
# ---------------------------------------------------------------------------


class StateTransition(BaseModel):
    """ProjectManifest.state_history 항목.

    append-only 히스토리. from_state -> to_state 전이를 시간순으로 기록합니다.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    from_state: ProjectState
    to_state: ProjectState
    transitioned_at: datetime = Field(default_factory=utc_now)
    reason: str = ""


class ProjectManifest(VersionedModel):
    project_id: str
    title: str
    category: Category
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    current_state: ProjectState = ProjectState.CREATED
    target_duration_min: int = 18
    topic_summary: str = ""
    paths: dict[str, str] = Field(default_factory=dict)
    render_mode_status: dict[str, str] = Field(default_factory=dict)
    approval_status: dict[str, str] = Field(default_factory=dict)
    final_outputs: dict[str, str] = Field(default_factory=dict)
    state_history: list[StateTransition] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 2. IntakePlan
# ---------------------------------------------------------------------------


class IntakePlanItem(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    item_id: str
    label: str
    description: str
    why_needed: str
    priority: TaskPriority = TaskPriority.NORMAL
    expected_input_types: list[str] = Field(default_factory=list)
    default_mode: IntakeMode = IntakeMode.AI_DELEGATE
    user_options: list[IntakeMode] = Field(default_factory=list)
    ai_delegate_task: Optional[str] = None
    risk_notice: Optional[str] = None
    status: Literal["pending", "ready", "skipped"] = "pending"


class IntakePlan(VersionedModel):
    project_id: str
    topic: str
    category: Category
    target_duration_min: int
    orchestrator_assessment: str = ""
    required_items: list[IntakePlanItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 3. SourceIntake (Dynamic Intake Page 제출 결과)
# ---------------------------------------------------------------------------


class UserDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    item_id: str
    mode: IntakeMode
    user_note: str = ""
    uploaded_files: list[str] = Field(default_factory=list)
    provided_links: list[str] = Field(default_factory=list)
    google_drive_links: list[str] = Field(default_factory=list)
    ai_delegate_remaining: bool = False


class SourceIntake(VersionedModel):
    project_id: str
    submitted_at: datetime = Field(default_factory=utc_now)
    user_decisions: list[UserDecision] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 4. TaskQueue
# ---------------------------------------------------------------------------


class TaskQueueItem(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    task_id: str
    input_item_id: Optional[str] = None
    assigned_worker: str
    task_type: str
    description: str = ""
    status: TaskStatus = TaskStatus.QUEUED
    priority: TaskPriority = TaskPriority.NORMAL
    depends_on: list[str] = Field(default_factory=list)
    parallelizable: bool = True
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None


class TaskQueue(VersionedModel):
    project_id: str
    tasks: list[TaskQueueItem] = Field(default_factory=list)

    def find(self, task_id: str) -> Optional[TaskQueueItem]:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None


# ---------------------------------------------------------------------------
# 5. WorkerSlot / WorkerSlotsSnapshot
# ---------------------------------------------------------------------------


class WorkerSlot(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    slot_id: int
    status: WorkerSlotStatus = WorkerSlotStatus.IDLE
    assigned_task_id: Optional[str] = None
    assigned_worker: Optional[str] = None
    started_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    progress: float = 0.0
    log_path: Optional[str] = None


class WorkerSlotsSnapshot(VersionedModel):
    project_id: str
    slots: list[WorkerSlot] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 6. TaskResult
# ---------------------------------------------------------------------------


class TaskResult(VersionedModel):
    project_id: str
    task_id: str
    worker: str
    status: TaskStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    scene_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    asset_refs: list[str] = Field(default_factory=list)
    qa_status: QAStatus = QAStatus.PENDING
    risk_flags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 7. SourceRegistry
# ---------------------------------------------------------------------------


class SourceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    source_id: str
    platform: str
    source_type: str
    original_url: Optional[str] = None
    local_path: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    language: Optional[str] = None
    original_text: Optional[str] = None
    translated_text: Optional[str] = None
    rights_status: RightsStatus = RightsStatus.RIGHTS_UNKNOWN
    reliability_score: float = 0.5
    verification_status: Literal["unverified", "cross_checked", "official", "disputed"] = "unverified"
    risk_flags: list[str] = Field(default_factory=list)
    usage_plan: list[str] = Field(default_factory=list)


class SourceRegistry(VersionedModel):
    project_id: str
    sources: list[SourceEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 7.5 SourceCompletenessReport (Phase 5, Review Gate 2 입력)
# ---------------------------------------------------------------------------


class CompletenessSeverity(str, Enum):
    """source_completeness_report 이슈 심각도.

    분류 정책 (v0.6.0, 사용자 확정): 사용 가능 자료가 0개일 때만 blocker.
    권리 미확보 / 신뢰도 낮음 / 위험 플래그는 warning (게이트에서 사용자 판단),
    rights_unknown 은 info (Review Gate 통과 시 사용 가능).
    """

    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class CompletenessIssueType(str, Enum):
    """부족 자료 식별 결과의 이슈 종류. docs/06_SOURCE_AND_RIGHTS_POLICY.md §2 와 동기화."""

    NO_USABLE_SOURCES = "no_usable_sources"
    RIGHTS_DO_NOT_USE = "rights_do_not_use"
    RIGHTS_REVIEW_REQUIRED = "rights_review_required"
    RIGHTS_UNKNOWN = "rights_unknown"
    SOURCE_UNUSABLE = "source_unusable"
    LOW_RELIABILITY = "low_reliability"
    RISK_FLAG_PRESENT = "risk_flag_present"


class CompletenessIssue(BaseModel):
    """단일 부족/위험 항목. registry-level 이슈 (NO_USABLE_SOURCES) 는 source_id=None."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    issue_type: CompletenessIssueType
    severity: CompletenessSeverity
    source_id: Optional[str] = None
    detail: str = ""
    recommendation: str = ""


class SourceCompletenessReport(VersionedModel):
    """source_registry 의 '부족 자료 식별' 결과 (Phase 5).

    docs/12_QA_AND_REVIEW_SPEC.md §1 의 `source_completeness_review` (Review Gate 2)
    가 본 보고서를 검수하여 '부족 자료 보완' 또는 '계속 진행' 을 결정합니다.
    Orchestrator 가 생성하며, 자료 자체의 SSOT 는 `source_registry.json` 입니다.

    스키마 추가는 optional 모델 추가에 해당해 schema_version 1 유지 (C3).

    overall_status
    --------------
    - `insufficient` : 사용 가능 자료 (rights_clear / manual_user_provided) 0개.
    - `needs_attention` : 사용 가능 자료는 있으나 warning 이슈 존재.
    - `ready` : 사용 가능 자료 있고 warning 없음.
    """

    project_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    reliability_threshold: float = 0.5
    total_sources: int = 0
    usable_sources: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    overall_status: Literal["ready", "needs_attention", "insufficient"] = "ready"
    issues: list[CompletenessIssue] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 8. SceneManifest (Phase 6 핵심, 본 파일은 골격만)
# ---------------------------------------------------------------------------


class SceneProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    primary_worker: str
    supporting_workers: list[str] = Field(default_factory=list)
    generated_files: list[str] = Field(default_factory=list)
    input_manifests: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    asset_ids: list[str] = Field(default_factory=list)
    task_ids: list[str] = Field(default_factory=list)
    qa_status: QAStatus = QAStatus.PENDING
    risk_flags: list[str] = Field(default_factory=list)


class SceneEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    scene_id: str
    chapter_id: str
    start_sec: float
    duration_sec: float
    scene_type: str
    narration_segment_ids: list[str] = Field(default_factory=list)
    caption: str = ""
    visual_type: str = ""
    source_refs: list[str] = Field(default_factory=list)
    asset_refs: list[str] = Field(default_factory=list)
    map_refs: list[str] = Field(default_factory=list)
    annotation_refs: list[str] = Field(default_factory=list)
    transition: Optional[str] = None
    camera_motion: Optional[str] = None
    inference_label_required: bool = False
    source_link_required: bool = True
    worker_provenance: Optional[SceneProvenance] = None


class SceneManifest(VersionedModel):
    project_id: str
    scenes: list[SceneEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 9. RemotionJob
# ---------------------------------------------------------------------------


class DebugLayerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    enabled: bool = False
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = "top-left"
    opacity: float = 0.85


class RemotionJob(VersionedModel):
    episode_id: str
    render_mode: RenderMode
    composition: str = "LongformBriefing"
    format: Literal["mp4", "webm"] = "mp4"
    style: dict[str, str] = Field(default_factory=dict)
    scenes: list[SceneEntry] = Field(default_factory=list)
    audio: dict[str, str] = Field(default_factory=dict)
    music: dict[str, str] = Field(default_factory=dict)
    subtitles: dict[str, str] = Field(default_factory=dict)
    source_links: list[dict[str, str]] = Field(default_factory=list)
    debug_layer: DebugLayerSpec = Field(default_factory=DebugLayerSpec)


# ---------------------------------------------------------------------------
# 10. ApprovalLog
# ---------------------------------------------------------------------------


class ApprovalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    gate_id: str
    artifact_refs: list[str] = Field(default_factory=list)
    status: Literal["approved", "revision_requested", "rejected"]
    user_comment: str = ""
    approved_at: datetime = Field(default_factory=utc_now)
    revision_requested: bool = False
    revision_notes: str = ""


class ApprovalLog(VersionedModel):
    project_id: str
    entries: list[ApprovalEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 11. ThumbnailManifest (Phase 10 골격)
# ---------------------------------------------------------------------------


class ThumbnailEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    thumbnail_id: str
    layout_type: Literal["L1", "L2", "L3"]
    text: str
    image_assets: list[str] = Field(default_factory=list)
    map_assets: list[str] = Field(default_factory=list)
    output_path: Optional[str] = None
    category_color: Optional[str] = None
    qa_status: QAStatus = QAStatus.PENDING


class ThumbnailManifest(VersionedModel):
    project_id: str
    candidates: list[ThumbnailEntry] = Field(default_factory=list)
    chosen_thumbnail_id: Optional[str] = None


# ---------------------------------------------------------------------------
# 11.5 SourceCollectionPartial (Phase 5 의 source_collector_worker 단일 task 출력)
# ---------------------------------------------------------------------------


class SourceCollectionPartial(VersionedModel):
    """source_collector_worker 의 단일 task 출력 (Phase 5).

    한 task 는 SourceIntake 의 한 UserDecision (ai_delegate / mixed 의 잔여분) 을 처리.
    수집된 후보 자료를 SourceEntry 목록으로 영속화하며, Phase 5 의
    SourceRegistryBuilder 가 모든 partial 을 합쳐 정식 SourceRegistry 를 생성합니다.

    스키마 추가는 optional 모델 추가에 해당해 schema_version 1 유지.

    필드 주의 (v0.4.1, codex 1차 리뷰 L1):
    - input_item_id 는 Optional[str] 이지만 도메인적으로는 한 partial 이
      한 UserDecision 에 대응하므로 사실상 필수. C3 의 additive-first 원칙을
      지키기 위해 schema 는 optional 로 두고, source_collector_worker (Phase 5)
      에서 task_type 별 필수 검증을 추가한다 (LLM-AP-003 known-limit 항목).
    """

    project_id: str
    task_id: str
    input_item_id: Optional[str] = None
    collected_sources: list[SourceEntry] = Field(default_factory=list)
    # v0.4.1 (codex 1차 리뷰 M3): notes → collector_notes 로 rename.
    # consumer/aggregator 가 출처가 명확하도록. 본 모델은 v0.4.0 도입으로 아직
    # 영속화된 인스턴스가 없어 호환성 부담 없음.
    collector_notes: str = ""


# ---------------------------------------------------------------------------
# 12. LLMCallRecord (docs/ADDENDUM_04 §6 의 추적성 영속화)
# ---------------------------------------------------------------------------


class LLMCallRecord(VersionedModel):
    """단일 LLM 호출의 추적·재현 메타데이터.

    `projects/{pid}/llm_calls/{call_id}.json` 으로 영속화됩니다.
    실제 프롬프트/응답 본문은 별도 파일(`{call_id}.prompt.txt`, `{call_id}.raw.txt`)에 둡니다.

    schema_version 은 1 유지. 본 모델은 v0.2.2 신규 도입 (optional 모델 추가는 호환).
    """

    call_id: str
    task_id: str
    worker: str
    backend: Literal["claude", "codex"]
    mode: Literal["response", "agent"]
    system_prompt_hash: str
    user_prompt_path: str
    raw_response_path: str
    parsed_status: Literal["ok", "parse_failed", "validation_failed", "subprocess_error"]
    started_at: datetime
    completed_at: datetime
    exit_code: Optional[int] = None
    retry_index: int = 0
    error_message: Optional[str] = None
