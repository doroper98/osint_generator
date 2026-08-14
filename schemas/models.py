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
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    target_duration_min: int = Field(default=18, ge=3, le=20)
    topic_summary: str = ""
    # 프로젝트 생성 시 사용자가 미리 제공한 자료 링크 (분석 리포트·기사·영상 등).
    # IntakePlanner 가 plan 생성에 참고하며, 사용자 자체 제공이므로 후속 source
    # 단계에서 manual_user_provided 후보로 다룬다. additive (schema_version 1 유지).
    initial_links: list[str] = Field(default_factory=list)
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
    target_duration_min: int = Field(ge=3, le=20)
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
    reliability_score: float = Field(default=0.5, ge=0.0, le=1.0)
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
    # 정책 §2 에 정의되지 않은 rights_status 값 (스키마 drift). '검토 필요' 와 구분되는
    # 별도 진단 — known review_required 와 unknown value 를 혼동하지 않기 위함.
    RIGHTS_STATUS_UNKNOWN_VALUE = "rights_status_unknown_value"


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
    reliability_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    total_sources: int = 0
    usable_sources: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    overall_status: Literal["ready", "needs_attention", "insufficient"] = "ready"
    issues: list[CompletenessIssue] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 7.6 ResearchDossier (Phase 6A, Research Agent 산출)
# ---------------------------------------------------------------------------


class ResearchClaimStatus(str, Enum):
    """주장의 검증 상태. 영상 내 라벨의 근거가 된다.

    docs/12_QA_AND_REVIEW_SPEC.md §3 의 claim_type 과 docs/06_SOURCE_AND_RIGHTS_POLICY.md
    §6 의 라벨(<미검증>/<추론>/<주장>)을 통합한다. 라벨 문자열은 CLAIM_STATUS_LABELS
    에서 파생되며 status 가 SSOT (이중 출처 방지).
    """

    CONFIRMED = "confirmed"      # <확인> — 2개 이상 독립 출처로 교차검증된 사실.
    INFERRED = "inferred"        # <추론> — 자료에서 합리적으로 도출했으나 직접 진술 아님.
    CLAIM = "claim"              # <주장> — 특정 출처가 주장하나 교차검증 안 됨.
    UNVERIFIED = "unverified"    # <미검증> — 확인 불가/근거 부족.
    DISPUTED = "disputed"        # <반박됨> — 다른 출처가 반박.


# status → 영상 내 표기 라벨. docs/06 §6 / docs/12 §4 의 라벨 시스템과 동기화.
CLAIM_STATUS_LABELS: dict[str, str] = {
    ResearchClaimStatus.CONFIRMED.value: "<확인>",
    ResearchClaimStatus.INFERRED.value: "<추론>",
    ResearchClaimStatus.CLAIM.value: "<주장>",
    ResearchClaimStatus.UNVERIFIED.value: "<미검증>",
    ResearchClaimStatus.DISPUTED.value: "<반박됨>",
}


class ResearchSeed(BaseModel):
    """ProjectManifest.initial_links 유래의 리서치 시드.

    사용자가 사전 제공한 자료(자체 생성 OSINT 분석 리포트 등)는 2차/파생 분석이므로
    사실 앵커가 아니라 리서치 시드로 다룬다 (docs/13 Phase 6 분해 노트). 여기서 추출한
    주장은 1차 출처로 별도 교차검증이 필요함을 구조에 박는다.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    seed_id: str
    url: str
    description: str = ""
    # 기본 True — 사용자 사전 제공 리포트는 파생 분석으로 가정. 1차 자료면 False.
    is_derivative: bool = True
    requires_verification: bool = True


class Evidence(BaseModel):
    """주장(ResearchClaim)의 근거 1건.

    source_id (source_registry.json 의 1차 자료) 또는 seed_id (파생 시드) 중 하나 이상을
    가리킨다. registry source_id 존재 여부의 cross-check 는 6B Evidence Guard 의 책임이므로
    본 모델에는 validator 를 두지 않는다 (additive 유지).
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    source_id: Optional[str] = None
    seed_id: Optional[str] = None
    quote: str = ""
    locator: Optional[str] = None
    stance: Literal["supports", "refutes", "contextual"] = "supports"


class ResearchClaim(BaseModel):
    """주장-근거 페어. 영상 서사의 사실 단위.

    display_label 은 status 에서 파생되는 읽기 전용 속성으로, 직렬화되지 않는다.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    claim_id: str
    statement: str
    status: ResearchClaimStatus = ResearchClaimStatus.UNVERIFIED
    evidence: list[Evidence] = Field(default_factory=list)
    cross_checked: bool = False
    confidence: Literal["low", "medium", "high"] = "low"
    notes: str = ""
    risk_flags: list[str] = Field(default_factory=list)

    @property
    def display_label(self) -> str:
        """영상 내 표기 라벨 (<확인>/<추론>/<주장>/<미검증>/<반박됨>)."""
        status_value = self.status if isinstance(self.status, str) else self.status.value
        return CLAIM_STATUS_LABELS.get(status_value, "<미검증>")


class ResearchDossier(VersionedModel):
    """Research Agent (ResearchWorker, Phase 6A) 산출.

    `source_registry.json` (사용 가능 소스) + `ProjectManifest.initial_links` (리서치 시드)
    를 입력으로, 영상 서사의 토대가 될 주장-근거 페어를 정리한다. docs/12 §3 의
    qa_evidence_report (6B) 와 docs/13 의 6C Blueprint 의 입력이 된다.

    스키마 추가는 optional 모델 추가에 해당해 schema_version 1 유지 (C3).
    """

    project_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    topic: str = ""
    summary: str = ""
    seeds: list[ResearchSeed] = Field(default_factory=list)
    claims: list[ResearchClaim] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 7.7 FullScript (Phase 6 Script, Script Agent 산출)
# ---------------------------------------------------------------------------


class ScriptChapter(BaseModel):
    """대본 챕터(서사 단위). full_script 의 segments 를 그룹핑한다."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    chapter_id: str
    title: str
    summary: str = ""


class ScriptSegment(BaseModel):
    """나레이션 1세그먼트. TTS 가 읽는 최소 단위이자 scene 매핑의 기준.

    label 은 ResearchClaim.display_label 에서 유래하는 영상 표기 라벨
    (`<미검증>` 등). 미검증/추론/주장/반박 항목을 화면에서 분리하기 위함
    (docs/06 §6, GOAL G4 — 미검증 정보는 라벨로만, 제목/썸네일 금지).
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    segment_id: str
    chapter_id: str
    narration: str
    on_screen_caption: str = ""
    claim_refs: list[str] = Field(default_factory=list)
    label: Optional[str] = None
    est_duration_sec: float = 0.0


class FullScript(VersionedModel):
    """Script Agent (ScriptWorker) 산출. research_dossier → 영상 대본.

    docs/12 §1 의 `script_review` (Review Gate 4) 입력이며, Scene Planner(다음
    단계)의 입력이 된다. 스키마 추가는 optional 모델 추가에 해당해 schema_version
    1 유지 (C3).
    """

    project_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    title: str = ""
    topic: str = ""
    target_duration_min: int = Field(default=8, ge=3, le=20)
    chapters: list[ScriptChapter] = Field(default_factory=list)
    segments: list[ScriptSegment] = Field(default_factory=list)
    total_est_duration_sec: float = 0.0


# ---------------------------------------------------------------------------
# 7.8 RenderProps (수직 슬라이스 V3, Remotion 최소 렌더 입력)
# ---------------------------------------------------------------------------


class SubtitleCue(BaseModel):
    """자막 1줄(큐). 한 scene 의 narration 을 문장/줄 단위로 쪼갠 조각 + scene 시작
    기준 상대 타이밍. 통문단 자막 대신 순차 표시하기 위함(타임스탬프 부재 시 글자수 비례
    추정). Remotion 이 현재 프레임에 해당하는 큐만 띄운다.
    """

    model_config = ConfigDict(extra="forbid")

    text: str
    startSec: float
    durationSec: float


class RenderMapMarker(BaseModel):
    """지도 마커(좌표 핀). Remotion MapView 가 d3-geo 투영으로 화면 좌표로 그린다."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = ""
    lng: float
    lat: float
    highlight: bool = False


class RenderMapArc(BaseModel):
    """마커 간 흐름선(arc). fromId/toId 는 marker id. TS 친화 camelCase."""

    model_config = ConfigDict(extra="forbid")

    fromId: str
    toId: str
    label: str = ""
    highlight: bool = False


class RenderMap(BaseModel):
    """scene 중앙에 그릴 지도 지오데이터(bundle.map 에서 유래). Phase B — 우리가 d3-geo 로
    재렌더해 마커·arc 배치·애니를 제어한다(차트와 달리 지도는 타입이 하나라 재렌더가 합리적).
    """

    model_config = ConfigDict(extra="forbid")

    center: list[float] = Field(default_factory=list)  # [lng, lat]
    zoom: float = 0.0
    markers: list[RenderMapMarker] = Field(default_factory=list)
    arcs: list[RenderMapArc] = Field(default_factory=list)


class RenderChart(BaseModel):
    """scene 중앙에 그릴 차트(bundle.chart 에서 유래). 영상미 최우선(C0): 정적 SVG 이식이
    아니라 우리 Remotion family 렌더러가 데이터로 cinematic 재렌더(애니·강조). data 의 타입별
    모양 SSOT 는 agents_reviewer schemas.py 라 Any 로 통과(Remotion 측이 type 별 해석).
    """

    model_config = ConfigDict(extra="forbid")

    chartId: str
    type: str
    title: str = ""
    data: Any = None
    unit: str = ""


class RenderSceneProps(BaseModel):
    """Remotion 컴포지션이 읽는 scene 1개 props. 필드명은 TS 친화 camelCase.

    scene_manifest(타이밍/라벨 신호) + full_script(나레이션/캡션)를 해석해 만든 평면
    구조. 텍스트 슬라이드 렌더에 필요한 값만 담는다 (정식 RemotionJob 은 추후).
    """

    model_config = ConfigDict(extra="forbid")

    sceneId: str
    startSec: float
    durationSec: float
    caption: str = ""
    narration: str = ""
    # narration 을 줄 단위로 쪼개 순차 표시할 자막 큐(scene 시작 기준 상대 타이밍).
    # 비면 Remotion 이 narration 전체를 폴백 표시.
    subtitleCues: list[SubtitleCue] = Field(default_factory=list)
    label: Optional[str] = None
    sourceLinkRequired: bool = False
    # 화면 상단 출처 표기 텍스트(있을 때만 표시). 소스 본문 배선 전엔 빈 문자열.
    source: str = ""
    # 이 scene 의 on-screen 텍스트가 인용(누군가의 발언/quote)인지. True 면 강조색 +
    # 인용부호로 렌더(영상 문법 ③). pull_quote/evidence quote 출처일 때 set.
    isQuote: bool = False
    # 이 scene 이 지도 비주얼을 가질 때(claim_refs 에 bundle map id 포함) 지오데이터. Phase B.
    # 있으면 중앙에 지도를 그리고 caption 은 제목으로 축소된다.
    mapData: Optional[RenderMap] = None
    # 이 scene 이 차트 비주얼을 가질 때(claim_refs 에 chart id 포함, 지원 타입). 영상미 C0:
    # 우리 family 렌더러가 데이터로 cinematic 재렌더. 있으면 중앙에 차트, caption 은 제목으로.
    chartData: Optional[RenderChart] = None
    # 나레이션 wav 의 project_dir 기준 상대경로 (audio_manifest 가 있을 때). Remotion 은
    # --public-dir 를 project_dir 로 두고 staticFile(audioPath) 로 참조한다. 무음이면 None.
    audioPath: Optional[str] = None


class RenderProps(VersionedModel):
    """Remotion 렌더 props (`09_render/render_props.json`). 수직 슬라이스 V3.

    Remotion `Briefing` 컴포지션의 입력. schema_version 은 VersionedModel 이 강제하나
    Remotion 측 타입은 무시한다 (구조적 타이핑). 정식 RemotionJob/render_worker 는 추후.
    """

    project_id: str
    title: str = ""
    fps: int = 30
    width: int = 1920
    height: int = 1080
    scenes: list[RenderSceneProps] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 7.9 AudioManifest (Phase 8 TTS, 수직 슬라이스 V4 — 나레이션 음성)
# ---------------------------------------------------------------------------


class AudioSegment(BaseModel):
    """나레이션 세그먼트 1개의 합성 결과. full_script 의 ScriptSegment 와 segment_id 로 대응."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    segment_id: str
    audio_path: str            # project_dir 기준 상대경로 (예: 08_audio/narration/seg_01.wav)
    duration_sec: float        # 실제 합성 음성 길이 (scene 타이밍의 권위 소스가 됨)
    text: str = ""             # 합성에 사용된 나레이션 본문 (추적성)
    backend: str = ""          # stub / elevenlabs / local
    voice: Optional[str] = None


class AudioManifest(VersionedModel):
    """TTS 산출 (`08_audio/audio_manifest.json`). 수직 슬라이스 V4.

    백엔드 교체 가능(local/elevenlabs/stub). 실제 음성 길이를 담아 후속 scene/render 타이밍
    정확도를 올린다. wav 자체는 gitignore(08_audio/narration/), 본 manifest 만 추적.
    """

    project_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    backend: str = ""
    total_duration_sec: float = 0.0
    segments: list[AudioSegment] = Field(default_factory=list)


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


# ---------------------------------------------------------------------------
# 13. ReportBundle (외부 연동 — agents_reviewer 인터페이스 계약 v1)
# ---------------------------------------------------------------------------
#
# agents_reviewer(보고서/분석 producer)가 emit 하는 핸드오프 산출물의 소비자측
# 미러다. 계약 정본은 agents_reviewer repo 의 docs/CONTRACTS/report_bundle_v1.md 이며,
# 본 모델은 수신 검증(fail-closed)용이다. 차트 data 의 타입별 모양 SSOT 는
# agents_reviewer 의 src/visual/schemas.py 이고(계약 §9), 본 계약은 그것을 재정의하지
# 않으므로 BundleChart.data 는 Any 로 통과시킨다. 우리 라벨 척추는 provenance.verification
# (= ResearchClaimStatus) 단일 축에서만 파생되며, 우리는 그 값을 그대로 신뢰한다
# (재검증/강등 floor 없음 — 사용자 결정).


class _BundleModel(BaseModel):
    """bundle 수신 모델의 공용 베이스 — **관대한 수신자(tolerant reader)**.

    `extra="ignore"`: agents_reviewer 보고서 양식은 계속 진화하므로(새 top-level 블록,
    새 섹션 필드 등), 모르는 필드는 **무시**해 추가 변경에 깨지지 않는다. 우리가 선언한
    필드는 여전히 타입·enum·필수 검증되어 소비 데이터의 건전성은 유지된다. 미지 필드의
    "인지"는 로더(bundle_io.load_report_bundle)가 로그로 surface 한다. 계약 §1 의
    "additive 변경은 schema_version 무증분" 원칙과 정합 — 추가 필드에 consumer 가 깨지면
    안 된다.
    """

    model_config = ConfigDict(extra="ignore", use_enum_values=True)


class BundleProducer(_BundleModel):
    system: str
    version: str
    mode: str = ""


class BundleTheme(_BundleModel):
    id: str
    tokens: dict[str, str] = Field(default_factory=dict)
    fonts: dict[str, str] = Field(default_factory=dict)


class BundleSectionVideo(_BundleModel):
    """섹션별 영상 대본 블록 (docs/VIDEO_BUNDLE_CONTRACT.md — sections[i].video).

    v0.44.0 까지 라이브 변환기(bundle_to_video)가 raw dict 로 읽던 계약을 Pydantic 으로
    정식 모델링(additive — schema_version 1 유지). 자막=narration, 음성=narration_tts.
    """

    narration: list[str] = Field(default_factory=list)
    narration_tts: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    emphasis: list[str] = Field(default_factory=list)


class BundleReportVideo(_BundleModel):
    """리포트 수준 영상 대본 (계약 — report.video). shorts 필드는 쇼츠 전용 대본이
    추가될 경우를 위한 예약(additive 제안, SHORTS_COLLAGE_OVERHAUL_PLAN §5.3-6)."""

    intro_narration: list[str] = Field(default_factory=list)
    outro_narration: list[str] = Field(default_factory=list)
    intro_narration_tts: list[str] = Field(default_factory=list)
    outro_narration_tts: list[str] = Field(default_factory=list)


class BundleTimelineVideo(_BundleModel):
    """타임라인 씬 대본 (계약 — timeline.video)."""

    narration: list[str] = Field(default_factory=list)
    narration_tts: list[str] = Field(default_factory=list)


class BundleReport(_BundleModel):
    report_id: str
    headline: str
    deck: str = ""
    closing: str = ""
    html_url: str = ""
    theme: Optional[BundleTheme] = None
    video: Optional[BundleReportVideo] = None


class BundleProvenanceSource(_BundleModel):
    source_id: str = ""
    provider: str = ""
    code: str = ""
    unit: str = ""
    fetched_at: str = ""
    url: str = ""


class BundleProvenance(_BundleModel):
    """차트/지도/주장의 출처·검증 메타 (계약 §5).

    verification 이 우리 화면 라벨의 단일 근거다. origin→verification 기본 매핑
    (measured→confirmed / narrative_inference→inferred / model_forecast→inferred)은
    producer 책임이며, 우리는 verification 을 그대로 신뢰한다.
    """

    origin: Literal["measured", "narrative_inference", "model_forecast"]
    verification: ResearchClaimStatus = ResearchClaimStatus.UNVERIFIED
    confidence: Literal["low", "medium", "high"] = "medium"
    sources: list[BundleProvenanceSource] = Field(default_factory=list)


class BundleChart(_BundleModel):
    """차트 1개. data 의 타입별 모양 SSOT 는 agents_reviewer schemas.py (계약 §9) 라
    본 모델은 data 를 Any 로 통과시킨다(이중 SSOT 회피). prerendered_svg 는 B안
    대상(sankey/choropleth/map/network)에서만 채워진다.
    """

    chart_id: str
    type: str
    title: str = ""
    data: Any = None
    note: str = ""
    provenance: BundleProvenance
    prerendered_svg: Optional[str] = None


class BundleMapMarker(_BundleModel):
    id: str
    name: str = ""
    lng: float
    lat: float
    highlight: bool = False


class BundleMapArc(_BundleModel):
    from_id: str = ""
    to_id: str = ""
    label: str = ""
    highlight: bool = False


class BundleMapLegend(_BundleModel):
    label: str = ""
    kind: str = ""
    highlight: bool = False


class BundleMap(_BundleModel):
    id: str = ""
    center: list[float] = Field(default_factory=list)
    zoom: float = 0.0
    markers: list[BundleMapMarker] = Field(default_factory=list)
    arcs: list[BundleMapArc] = Field(default_factory=list)
    legend: list[BundleMapLegend] = Field(default_factory=list)
    provenance: Optional[BundleProvenance] = None
    prerendered_svg: Optional[str] = None


class BundleSection(_BundleModel):
    """서사 섹션. prose 는 '나레이션 원천'(편집체)이며, 최종 발화형 변환은 우리
    ScriptWorker 가 한다(계약 §6). chart_refs/map_ref 는 시각 에셋 착지점(Phase 7).
    """

    section_id: str
    heading: str = ""
    kicker: str = ""
    prose: str = ""
    pull_quote: str = ""
    chart_refs: list[str] = Field(default_factory=list)
    map_ref: Optional[str] = None
    image_refs: list[str] = Field(default_factory=list)
    claim_refs: list[str] = Field(default_factory=list)
    video: Optional[BundleSectionVideo] = None


class BundleEvidence(_BundleModel):
    source_id: str = ""
    quote_or_data: str = ""
    locator: str = ""
    reliability: str = ""
    stance: Literal["supports", "refutes", "contextual"] = "supports"


class BundleClaim(_BundleModel):
    """주장-근거 페어 (우리 ResearchDossier.claims 직매핑). status 는 우리 enum 그대로."""

    claim_id: str
    statement: str
    status: ResearchClaimStatus = ResearchClaimStatus.UNVERIFIED
    confidence: Literal["low", "medium", "high"] = "medium"
    cross_checked: bool = False
    evidence: list[BundleEvidence] = Field(default_factory=list)
    chart_refs: list[str] = Field(default_factory=list)


class BundleSignal(_BundleModel):
    signal: str
    description: str = ""
    indicates: str = ""
    deadline: str = ""
    verification: ResearchClaimStatus = ResearchClaimStatus.UNVERIFIED


class BundleContradiction(_BundleModel):
    side_a: str = ""
    side_b: str = ""
    evidence: str = ""
    resolution: str = ""


class BundleSource(_BundleModel):
    source_id: str
    url: str = ""
    publisher: str = ""
    title: str = ""
    fetched_at: str = ""


class BundleConfidence(_BundleModel):
    score: float = 0.0
    summary: str = ""


class BundleTimelinePoint(_BundleModel):
    date: str = ""
    label: str = ""
    phase: str = ""  # past / present / future
    note: str = ""


class BundleTimeline(_BundleModel):
    heading: str = ""
    points: list[BundleTimelinePoint] = Field(default_factory=list)
    video: Optional[BundleTimelineVideo] = None


class BundleImage(_BundleModel):
    """보도 사진 1장 (docs/IMAGE_BUNDLE_CONTRACT.md). 섹션 image_refs 로 참조되어
    영상 photo 씬이 된다. rights_status == "cleared" 만 영상에 삽입한다(G4-8/C9) —
    소비측(bundle_to_video)이 게이트를 강제하고 photos_manifest 에 기록한다.
    """

    image_id: str
    url: str
    caption: str = ""
    credit: str = ""
    rights_status: Literal["cleared", "needs_review", "blocked"] = "needs_review"
    license: str = ""
    source_id: str = ""
    focus: Literal["center", "top", "bottom", "left", "right"] = "center"


class ReportBundle(VersionedModel):
    """agents_reviewer → osint_generator 핸드오프 (인터페이스 계약 v1).

    **관대한 수신자**: `extra="ignore"` 로 미지 필드(진화하는 보고서의 새 블록 등)를
    무시하되, 선언 필드는 검증하고 model_validator 로 id unique + chart_refs/claim_refs/
    map_ref resolve 를 강제한다(계약 §8). 미지 top-level 필드는 로더가 로그로 알린다.
    schema_version 은 이 계약의 버전(현재 1)이며 producer.version 과 분리된다(§1).
    """

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    bundle_kind: Literal["report_bundle"] = "report_bundle"
    generated_at: Optional[datetime] = None
    producer: BundleProducer
    report: BundleReport
    sections: list[BundleSection] = Field(default_factory=list)
    charts: list[BundleChart] = Field(default_factory=list)
    map: Optional[BundleMap] = None
    claims: list[BundleClaim] = Field(default_factory=list)
    signals: list[BundleSignal] = Field(default_factory=list)
    contradictions: list[BundleContradiction] = Field(default_factory=list)
    sources: list[BundleSource] = Field(default_factory=list)
    confidence: Optional[BundleConfidence] = None
    # 진화 수용 예: v5.5.2 가 추가한 연표. 현재는 보관만(영상 소비는 추후 — 타임라인 비주얼).
    timeline: Optional[BundleTimeline] = None
    # 보도 사진 (IMAGE_BUNDLE_CONTRACT, additive). 부재 시 기존 동작(하위 호환).
    images: list[BundleImage] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_referential_integrity(self) -> "ReportBundle":
        for label, ids in (
            ("chart_id", [c.chart_id for c in self.charts]),
            ("section_id", [s.section_id for s in self.sections]),
            ("claim_id", [c.claim_id for c in self.claims]),
            ("source_id", [s.source_id for s in self.sources]),
            ("image_id", [i.image_id for i in self.images]),
        ):
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            if dupes:
                raise ValueError(f"중복 {label}: {dupes}")

        image_ids = {i.image_id for i in self.images}
        for s in self.sections:
            bad = [r for r in s.image_refs if r not in image_ids]
            if bad:
                raise ValueError(f"section {s.section_id} 의 미해결 image_refs: {bad}")

        chart_ids = {c.chart_id for c in self.charts}
        claim_ids = {c.claim_id for c in self.claims}
        # 계약 v1 보정: 보고서당 map 은 단일 객체 + id. section.map_ref 는 그 map.id 로
        # resolve 하거나 null (다중 지도는 회피 — speculative generality).
        map_id = self.map.id if self.map is not None else None
        for s in self.sections:
            bad = [r for r in s.chart_refs if r not in chart_ids]
            if bad:
                raise ValueError(f"section {s.section_id} 의 미해결 chart_refs: {bad}")
            bad = [r for r in s.claim_refs if r not in claim_ids]
            if bad:
                raise ValueError(f"section {s.section_id} 의 미해결 claim_refs: {bad}")
            if s.map_ref is not None and s.map_ref != map_id:
                raise ValueError(
                    f"section {s.section_id} 의 미해결 map_ref: {s.map_ref} "
                    f"(map.id={map_id})"
                )
        for c in self.claims:
            bad = [r for r in c.chart_refs if r not in chart_ids]
            if bad:
                raise ValueError(f"claim {c.claim_id} 의 미해결 chart_refs: {bad}")
        return self
        for label, ids in (
            ("chart_id", [c.chart_id for c in self.charts]),
            ("section_id", [s.section_id for s in self.sections]),
            ("claim_id", [c.claim_id for c in self.claims]),
            ("source_id", [s.source_id for s in self.sources]),
        ):
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            if dupes:
                raise ValueError(f"중복 {label}: {dupes}")

        chart_ids = {c.chart_id for c in self.charts}
        claim_ids = {c.claim_id for c in self.claims}
        # 계약 v1 보정: 보고서당 map 은 단일 객체 + id. section.map_ref 는 그 map.id 로
        # resolve 하거나 null (다중 지도는 회피 — speculative generality).
        map_id = self.map.id if self.map is not None else None
        for s in self.sections:
            bad = [r for r in s.chart_refs if r not in chart_ids]
            if bad:
                raise ValueError(f"section {s.section_id} 의 미해결 chart_refs: {bad}")
            bad = [r for r in s.claim_refs if r not in claim_ids]
            if bad:
                raise ValueError(f"section {s.section_id} 의 미해결 claim_refs: {bad}")
            if s.map_ref is not None and s.map_ref != map_id:
                raise ValueError(
                    f"section {s.section_id} 의 미해결 map_ref: {s.map_ref} "
                    f"(map.id={map_id})"
                )
        for c in self.claims:
            bad = [r for r in c.chart_refs if r not in chart_ids]
            if bad:
                raise ValueError(f"claim {c.claim_id} 의 미해결 chart_refs: {bad}")
        return self


# ---------------------------------------------------------------------------
# 22. Asset Library (쇼츠 콜라주 개편 — SHORTS_COLLAGE_OVERHAUL_PLAN §3)
# ---------------------------------------------------------------------------


class AssetSourceRef(BaseModel):
    """라이브러리 자산의 원본 출처·권리 기록 (C9/G4-8).

    판화 스타일라이즈를 거쳐도 원본 사진의 권리는 소멸하지 않으므로,
    모든 파생 variant 는 본 기록을 공유한다.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    url: str = ""
    license: str = ""                       # 예: "public_domain", "CC BY 4.0"
    rights_status: RightsStatus = RightsStatus.RIGHTS_UNKNOWN
    credit: str = ""                        # 출처표시 의무 문구 (있는 경우 필수 표기)
    note: str = ""                          # nominative_use / self_made 등 메모


class LibraryAssetVariant(BaseModel):
    """자산 1개의 스타일 변형 (원본 → 가공 산출물 1개)."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    # mono = 고대비 모노톤 컷아웃 (기본, 17 §1.7 v2). halftone/linescreen = 스크리닝
    # 변주 옵션. stipple/engraving 은 v0.45.0 반려로 신규 생산 금지 (기존 값 호환용 유지).
    style: Literal[
        "source", "cutout", "mono", "halftone", "linescreen", "stipple", "engraving", "crosshatch"
    ]
    pose: str = "front"                     # front / side / point 등
    path: str                               # 저장소 상대 경로 (assets/library/...)
    generator_version: str = ""             # engraving_stylizer 버전 (재현성)


class LibraryPerson(BaseModel):
    """주요 인물 1명 (판화/컷아웃 변형 세트 + 별칭 사전)."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    person_id: str                          # 예: "trump"
    name_ko: str
    name_en: str = ""
    role: str = ""                          # 자막 소개용 직함 (예: "미국 대통령")
    aliases: list[str] = Field(default_factory=list)   # 엔티티 매칭용 표기 변형
    source: AssetSourceRef
    variants: list[LibraryAssetVariant] = Field(default_factory=list)


class LibraryLogo(BaseModel):
    """기업/기관 CI 1종. 상표권 유의 — 보도·논평 인용 목적(nominative use) 기록."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    logo_id: str                            # 예: "sk_hynix"
    name_ko: str
    name_en: str = ""
    aliases: list[str] = Field(default_factory=list)
    source: AssetSourceRef
    path: str                               # SVG 경로


class LibraryFlag(BaseModel):
    """국기 1종 (hyperframes flags 승격)."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    country_code: str                       # ISO 3166-1 alpha-2 소문자 (예: "kr")
    name_ko: str
    aliases: list[str] = Field(default_factory=list)
    source: AssetSourceRef
    path: str


class AssetLibraryManifest(VersionedModel):
    """assets/library/library_manifest.json — 사전 구축 자산 전체 인덱스.

    엔티티 매칭(bundle_to_shorts)의 단일 조회처. 매칭 실패 시 씬 스킵 + 로그,
    핵심 인물 부재 시 needs_user_upload (SHORTS_COLLAGE_OVERHAUL_PLAN §3.4).
    """

    generated_at: datetime = Field(default_factory=utc_now)
    people: list[LibraryPerson] = Field(default_factory=list)
    logos: list[LibraryLogo] = Field(default_factory=list)
    flags: list[LibraryFlag] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_unique_ids(self) -> "AssetLibraryManifest":
        for label, ids in (
            ("person_id", [p.person_id for p in self.people]),
            ("logo_id", [l.logo_id for l in self.logos]),
            ("country_code", [f.country_code for f in self.flags]),
        ):
            dup = {i for i in ids if ids.count(i) > 1}
            if dup:
                raise ValueError(f"asset library 중복 {label}: {sorted(dup)}")
        return self


# ---------------------------------------------------------------------------
# 23. Design Sheet (쇼츠 콜라주 개편 — SHORTS_COLLAGE_OVERHAUL_PLAN §6)
# ---------------------------------------------------------------------------


class SafeArea(BaseModel):
    """플랫폼 UI 침범 금지 마진 (px). 쇼츠+릴스+틱톡 합집합이 기본값의 근거
    (docs/17_COLLAGE_DESIGN_SHEET.md §1)."""

    model_config = ConfigDict(extra="forbid")

    top: int = 220
    bottom: int = 350
    left: int = 60
    right: int = 140


class DesignSheet(VersionedModel):
    """디자인 시트 L1 토큰의 직렬화 형식 — 씬 조립기가 하드코딩 대신 본 시트를 읽는다.

    값의 SSOT 는 docs/17_COLLAGE_DESIGN_SHEET.md 이며 본 모델은 그 운반 형식.
    palette/typography/motion 은 open key-value (BundleTheme.tokens 전례) —
    키 목록·의미는 17 문서가 정의한다.
    """

    sheet_id: str                           # 예: "shorts_collage_v1"
    format: Literal["shorts", "briefing"] = "shorts"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    safe_area: SafeArea = Field(default_factory=SafeArea)
    palette: dict[str, str] = Field(default_factory=dict)
    typography: dict[str, str] = Field(default_factory=dict)
    motion: dict[str, float] = Field(default_factory=dict)
    texture_refs: list[str] = Field(default_factory=list)   # assets/library/textures/*
