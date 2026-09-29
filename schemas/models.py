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
    """프로젝트 상태 머신 (v3.0.0, docs/handoff/16 §2). 전이표는 orchestrator/state_machine.py.

    옛 24개 상태(v2 이전)는 삭제했다(15 P2). 옛 값을 담은 manifest 는 schema_version 1 이라
    로드 시 ManifestVersionError — 변환하지 않는다(19 §3.6).
    """

    CREATED = "created"
    INTAKE = "intake"                      # 소스 접수 + 요청 정리 [18]
    SOURCE_VERIFY = "source_verify"        # 출처 검증·주장 추출·교차 확인 [18]
    RESEARCH = "research"                  # 보강 리서치, 사실 목록 확정
    SCRIPT_DRAFT = "script_draft"          # 원고 YAML
    SCRIPT_APPROVAL = "script_approval"    # ★ 사용자 승인 게이트 ①
    VOICE_TIMELINE = "voice_timeline"      # 린트 → TTS → plan.json
    ASSETS = "assets"                      # 지오·인물·휘장·국기·미디어
    DIRECTION = "direction"                # 연출
    PREVIEW_QA = "preview_qa"              # 결정적 검사·시각 검수·프리뷰 시트
    PREVIEW_APPROVAL = "preview_approval"  # ★ 사용자 승인 게이트 ②
    RENDER = "render"                      # 전체 렌더
    AUDIO_MIX = "audio_mix"                # 내레이션·음악·효과음
    DELIVER = "deliver"                    # 먹싱·SRT·설명문·provenance
    DONE = "done"


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


class GateDecision(BaseModel):
    """승인 게이트 기록 (v3.0.0, 16 §5). append-only. 반려 코멘트는 이 프로젝트의 수정 지시로만 쓴다(15 P11)."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    gate: ProjectState
    decision: Literal["approved", "rejected"]
    by: str = Field(min_length=1)
    at: datetime = Field(default_factory=utc_now)
    comment: str = ""
    rollback_to: Optional[ProjectState] = None   # 반려일 때 되돌아간 상태
    shown: dict[str, str] = Field(default_factory=dict)   # 게이트 화면에 보인 근거(시트 경로·provenance 요약 등)
    chosen_version: Optional[int] = None   # v3.1.0 게이트 ② 에서 사람이 고른 AI 연출 판(D-0049 쟁점 3). 없으면 코드 선택 그대로

    @model_validator(mode="after")
    def _rollback_iff_rejected(self) -> "GateDecision":
        if (self.decision == "rejected") != (self.rollback_to is not None):
            raise ValueError("rollback_to 는 반려(rejected)일 때만, 반려면 반드시")
        return self


class StageRecord(BaseModel):
    """엔진 단계 실행 기록 요약 (v3.0.0, 16 §4). 전체 StageResult 는 logs/stages/ 에."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    state: ProjectState
    stage: str
    ok: bool
    at: datetime = Field(default_factory=utc_now)
    artifacts: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    drops: int = 0
    log: str = ""


MANIFEST_SCHEMA_VERSION: int = 2   # v3.0.0 — 상태 머신 교체(16 §2), 옛 manifest 는 재생성(19 §3.6)


class ReopenRecord(BaseModel):
    """렌더 이후 연출 되돌림 기록(v4.7.0 back_and_forth D-0104 D4). append-only. 사유는 이 프로젝트 수정 지시로만(15 P11)."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    from_state: ProjectState
    to_state: ProjectState
    by: str = Field(min_length=1)
    at: datetime = Field(default_factory=utc_now)
    reason: str = Field(min_length=1)
    direction_version: Optional[int] = None   # 되돌리는 시점의 최신 연출 판 번호(direction.v{N}.yaml 의 N, 없으면 None)


class ProjectManifest(VersionedModel):
    schema_version: Literal[2] = MANIFEST_SCHEMA_VERSION  # type: ignore[assignment]
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
    gate_decisions: list[GateDecision] = Field(default_factory=list)   # v3.0.0 — 옛 approval_status 대체(16 §5)
    stage_records: list[StageRecord] = Field(default_factory=list)     # v3.0.0 — engine_service 실행 기록
    final_outputs: dict[str, str] = Field(default_factory=dict)
    state_history: list[StateTransition] = Field(default_factory=list)
    reopens: list[ReopenRecord] = Field(default_factory=list)          # v4.7.0 D-0104 D4 — 렌더 이후 연출 되돌림(선택 필드, schema_version 2 유지)


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


# 3. (v3.2.0 삭제) SourceIntake·UserDecision — 소스 레코드는 schemas/source_models.py(18 §2, D52)


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


class WorkerProvenance(BaseModel):
    """LLM 워커가 실제로 쓴 프롬프트·규칙의 증명 (v2.0.0, docs/handoff/15 P5).

    prompt_sha1 은 `prompts/{prompt_name}.md` 를 규칙으로 렌더한 system prompt 의 sha1.
    """

    model_config = ConfigDict(extra="forbid")

    prompt_name: str
    prompt_sha1: str
    rules_hash: str
    genre: Optional[str] = None             # v4.4.0 D-0090 작업 1 — 장르 프롬프트 층에 쓴 장르(기본 장르면 None, 추가 문단 0)
    genre_declared: Optional[bool] = None   # 주문(order.yaml)에 선언했는가


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
    worker_provenance: Optional[WorkerProvenance] = None  # v2.0.0 — LLM 워커만 기록


# 7. (v3.2.0 삭제) SourceRegistry·SourceEntry·SourceCompletenessReport — 주장-출처 매핑은 claims.json(18 §3-6, D52)


# ---------------------------------------------------------------------------
# 7.6 외부 번들 주장 status 어휘 (v3.2.0 — ResearchDossier·ResearchClaim 삭제, D52)
# ---------------------------------------------------------------------------
# 우리 파이프라인의 검증 status 는 schemas/source_models.py(18 §2 4종)다. 아래 enum 은 agents_reviewer
# report_bundle 계약 v1 의 어휘로만 남는다(ReportBundle 검증용). 번들 변환은 Phase 9 에서 복귀.

class ResearchClaimStatus(str, Enum):
    """report_bundle 계약 v1 의 주장 status 어휘(외부). 영상 라벨은 이것이 아니라 claims.json status 로 계산한다."""

    CONFIRMED = "confirmed"      # <확인> — 2개 이상 독립 출처로 교차검증된 사실.
    INFERRED = "inferred"        # <추론> — 자료에서 합리적으로 도출했으나 직접 진술 아님.
    CLAIM = "claim"              # <주장> — 특정 출처가 주장하나 교차검증 안 됨.
    UNVERIFIED = "unverified"    # <미검증> — 확인 불가/근거 부족.
    DISPUTED = "disputed"        # <반박됨> — 다른 출처가 반박.


# ---------------------------------------------------------------------------
# 10·11 (v4.0.0 삭제, back_and_forth D-0073) ApprovalLog·ApprovalEntry·ThumbnailManifest·ThumbnailEntry — 사용처 0.
#   게이트 기록은 ProjectManifest.gate_decisions(GateDecision). 썸네일 시스템은 v2 파이프라인에 없다. 보존 archive/hyperframes-briefing.
# ---------------------------------------------------------------------------


# 11.5 (v3.2.0 삭제) SourceCollectionPartial — 소스 수집 워커 삭제(D52)


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
    # v0.43.5: claude 백엔드에 실제 전달된 --model 값 (재현성). codex 는 None.
    model: Optional[str] = None
    mode: Literal["response", "agent", "vision"]   # v3.1.0 vision = 이미지 첨부 읽기(시각 검수, D-0047 작업 8)
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
    """bundle 수신 모델의 공용 베이스 — **fail-closed**(v3.5.0 D-0064 쟁점 1 A).

    `extra="forbid"`: 모델이 선언하지 않은 필드는 **로드 오류**다. v3.4.0 까지의 관대한 수신자(`extra="ignore"`)는
    어댑터가 쓰는 마커 종류·호 종류·논쟁 영상 문구를 조용히 버렸다(코퍼스 68건 실측, 15 P6·P10). agents_reviewer 가
    필드를 더하면(additive 포함) 이 파일의 번들 모델 선언과 같이 간다 — 그 전까지 import 는 멈춘다(의도된 동작).
    로더(`bundle.load.load_report_bundle`)는 미지 필드 경로를 **모든 깊이에서 한 번에** 오류 본문에 나열한다.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


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
    display: str = ""                 # v3.5.0 선언(D-0064) — 보고서 표시 폭(full 등). 영상은 쓰지 않는다


class BundleMapMarker(_BundleModel):
    id: str
    name: str = ""
    lng: float
    lat: float
    highlight: bool = False
    kind: str = ""                    # v3.5.0 선언(D-0064) — military·chokepoint 등(번들 어휘 그대로)
    value: str = ""                   # 마커 값 표기(예: "8월 25일 회담")
    label_side: str = ""              # 보고서 지도 라벨 방향(left·right·top·bottom) — 참고용


class BundleMapArc(_BundleModel):
    from_id: str = ""
    to_id: str = ""
    label: str = ""
    highlight: bool = False
    kind: str = ""                    # v3.5.0 선언(D-0064) — flow(이동·경로) | tension(긴장선), 12 §2
    weight: Optional[float] = None    # 선 굵기 등급(번들 표기)
    label_t: Optional[float] = None   # 호 위 라벨 위치(0~1)


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


class BundleContradictionVideo(_BundleModel):
    """논쟁 영상 문구(v3.5.0 선언, D-0064) — 양측 라벨·한 줄 요지·내레이션. 어댑터는 versus 재료·contested 후보 sides 라벨로만 쓴다."""

    label_a: str = ""
    label_b: str = ""
    line_a: str = ""
    line_b: str = ""
    narration: list[str] = Field(default_factory=list)
    narration_tts: list[str] = Field(default_factory=list)


class BundleContradiction(_BundleModel):
    side_a: str = ""
    side_b: str = ""
    evidence: str = ""
    resolution: str = ""
    video: Optional[BundleContradictionVideo] = None


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

    **fail-closed**(v3.5.0 D-0064): 미지 필드 = 오류(`extra="forbid"`, 모든 깊이). 선언 필드는 검증하고
    model_validator 로 id unique + chart_refs/claim_refs/map_ref resolve 를 강제한다(계약 §8).
    schema_version 은 이 계약의 버전(현재 1)이며 producer.version 과 분리된다(§1).
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

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
    # v1.0.0 (G4-10 개정): 가공 도구·프롬프트 기록 의무 — ChatGPT 가공 자산 추적 (계획 §2.0)
    tool: str = "procedural"                # "procedural" | "chatgpt_image" 등
    prompt_ref: str = ""                    # 프롬프트 사본 파일 경로 (ChatGPT 가공 시 필수)


class LibraryPerson(BaseModel):
    """주요 인물 1명 (판화/컷아웃 변형 세트 + 별칭 사전)."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    person_id: str                          # 예: "trump"
    name_ko: str
    name_en: str = ""
    role: str = ""                          # 자막 소개용 직함 (예: "미국 대통령")
    aliases: list[str] = Field(default_factory=list)   # 엔티티 매칭용 표기 변형
    accent_hint: str = ""                   # 섀도 시그니처 색 hex (선택 — 17 §1.7.1)
    source: AssetSourceRef
    variants: list[LibraryAssetVariant] = Field(default_factory=list)
    usage_count: int = 0                    # 온디맨드→코어 승격 판단용 (계획 §3.0)


class LibraryLogo(BaseModel):
    """기업/기관 CI 1종. 상표권 유의 — 보도·논평 인용 목적(nominative use) 기록."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    logo_id: str                            # 예: "sk_hynix"
    name_ko: str
    name_en: str = ""
    aliases: list[str] = Field(default_factory=list)
    accent_hint: str = ""                   # 브랜드 컬러 hex (선택 — 섀도/무대 액센트)
    source: AssetSourceRef
    path: str                               # SVG 경로
    usage_count: int = 0                    # 온디맨드→코어 승격 판단용 (계획 §3.0)


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


# (v2.0.0 삭제) 23. Design Sheet · 23.1 Art Direction — 쇼츠 콜라주 트랙 보관(GOAL G5). 원본은
# archive/hyperframes-briefing.
