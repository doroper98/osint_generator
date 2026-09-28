"""`rules/video_rules.yaml` Pydantic 모델 (v2.0.0, docs/handoff/15 §3 P3).

영상 규칙 SSOT 의 계약. 모든 모델은 `extra="forbid"` — 규칙 파일에 모르는 키가 들어오면
조용히 무시하지 않고 로드 단계에서 실패한다(15 P6). 수치의 의미·출처는 YAML 주석과
docs/handoff/{03,05,08,09,10,14,17} 이 정본이다.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


Color4 = tuple[float, float, float, float]
Range2 = tuple[float, float]


class BannedPhrases(_Strict):
    patterns: list[str]
    candidates: list[str]
    defect_classes: list[str]


class ScriptSchemaRules(_Strict):
    sentence_fields: list[str]
    date_formats: list[str]
    subtitle_max_lines: int
    subtitle_wrap_px_480p: int
    scene_count: Literal["free"]
    duration_limit_sec: Optional[float]


class TTSRules(_Strict):
    forbidden_chars_regex: str
    sino_numbers_no_inner_space: bool
    native_count_units: list[str]
    sino_count_units: list[str]
    month_readings: dict[str, str]
    abbreviation_policy: str
    decimal_policy: str
    emphasis_must_be_substring: bool
    alignment_sources: list[str]   # v2.3.0 D34 — `{mp3}.align.json` alignment_source 등재값(P10). 등재 외 = 오류


class Drift(_Strict):
    amount: float
    tau_sec: float


class EndingPullback(_Strict):
    w_from: float
    w_to: float
    dur_sec: float


class AutoTransition(_Strict):
    dip_if_dist_over_w: float
    dip_if_w_ratio_over: float


class ShotGrammar(_Strict):
    camera_moves_per_scene_max: int
    shot_min_hold_sec: float
    move_dur_sec: Range2
    move_lead_sec: Range2
    dip_total_sec: float
    dip_max_per_sec: float
    dip_alpha_peak: float
    zoom_bump: bool
    drift: Drift
    ending_pullback: EndingPullback
    auto_transition: AutoTransition
    w_guide: dict[str, float | Range2]


class MediaBeats(_Strict):
    per_runtime_sec: Range2
    per_scene_max: int
    article_card_exempt: bool
    no_consecutive_same_kind: bool
    kinds: list[str]
    photo_show_sec: Range2
    clip_show_sec: Range2
    file_photo_label_required: bool
    caption_credit_required: bool
    ai_generated_forbidden: bool
    casualty_identifiable_forbidden: bool


class DateBadge(_Strict):
    font: str
    size: float
    x_right: float
    y: float
    underline_y: float
    underline_w: float
    slide_px: float
    slide_sec: float


class HudRules(_Strict):
    allowed_corner_elements: list[str]
    forbidden_components: list[str]
    date_badge: DateBadge


class LayoutBase(_Strict):
    w: int
    h: int
    fps: int


class SubtitleLayout(_Strict):
    size: float
    last_line_y: float
    line_gap: float
    halo: float
    halo_alpha: float
    emphasis_color: str


class TitleCardLayout(_Strict):
    dur_sec: float
    title_size: float
    subtitle_size: float
    rule_w: float


class EndCardLayout(_Strict):
    dur_sec: float
    item_size: float
    license_size: float


class CardLayout(_Strict):
    x_right_margin: float
    y: float
    min_w: float
    slide_px: float
    fade_sec: float
    big_size: float
    line_size: float
    tag_size: float
    src_size: float


class ArticleCardLayout(_Strict):
    w: float
    y: float


class PanelLayout(_Strict):
    cover_alpha: float
    fade_sec: float
    title_size: float
    title_y: float
    subtitle_size: float
    subtitle_y: float
    min_screen_use: float


class BadgeLayout(_Strict):
    R_person_map: Range2
    R_person_panel: float
    R_flag: Range2
    reserve_top_factor: float
    reserve_bottom_px: float
    popin_sec: float


class TimelineGaps(_Strict):
    gap_sec: float
    scene_gap_sec: float
    lead_sec: float
    title_after_cold_open: bool


class FadeLayout(_Strict):
    in_sec: float
    out_sec: float


class CardZone(_Strict):
    x_from_right: float
    y: Range2


class SubtitleZone(_Strict):
    y_from: float


class ReservedZones(_Strict):
    card: CardZone
    subtitle: SubtitleZone


class Layout480p(_Strict):
    base: LayoutBase
    subtitle: SubtitleLayout
    min_font_px: float
    title_card: TitleCardLayout
    end_card: EndCardLayout
    card: CardLayout
    article_card: ArticleCardLayout
    panel: PanelLayout
    badge: BadgeLayout
    timeline_gaps: TimelineGaps
    fade: FadeLayout
    reserved_zones: ReservedZones



# ------------------------------------------------------------------ 패널 기하·타이밍 (D-0032, 08 §3·§8)
class RelationNodeCol(_Strict):
    x: float
    cy: float           # 열 세로 중심 — y_i = cy − (n−1)/2·dy + i·dy
    dy: float
    R: float
    t0: float           # 패널 시작 뒤 첫 노드 등장(초)
    step: float         # 노드 사이 등장 간격(초)
    pad: float          # 선 끝과 뱃지 원 사이 여백(px). 선 끝 = 원 반지름 + pad


class RelationEdgeStyle(_Strict):
    color: str          # colors 키
    alpha: float
    dash: list[float]


class PanelText(_Strict):
    size: float
    halo: float
    fade_sec: float = 0.0


class RelationStateLabel(PanelText):
    dx: float
    dy: float


class RelationEdgeLabel(PanelText):
    x: float
    y: float
    delay_sec: float


class RelationQuoteBottom(PanelText):
    y: float


class RelationQuoteSource(PanelText):
    dy: float


class RelationPanelRules(_Strict):
    """08 §3 정돈된 관계선 규칙 6개(코드 내장 대상) + v3 P_refusal 합격 값."""

    edge_dur_sec: float
    edge_dur_range: Range2          # 규칙 2 — 선 하나 1.0~1.3초
    edge_gap_sec: float
    edge_gap_range: Range2          # 규칙 2 — 간격 0.6~0.75초
    edges_after_nodes_sec: float    # 규칙 1 — 마지막 노드 등장 뒤에 첫 선
    max_edges: int                  # 규칙 6 — 초과 = lint 경고 + 분할 제안(실행하지 않음, P8)
    curve_samples: int              # 규칙 3 — 수평 접선 3차 베지어 표본 수
    line_width: float
    state_fade_sec: float           # 규칙 5 — 상태 변화는 단어 앵커 시각부터 이 시간 동안
    dash_after: float               # 상태 전환 진행률이 이 값을 넘으면 새 스타일의 점선
    source: RelationNodeCol
    target: RelationNodeCol
    styles: dict[str, RelationEdgeStyle]
    state_label: RelationStateLabel
    edge_label: RelationEdgeLabel   # 규칙 4 — 라벨은 선이 자라기 시작한 뒤(v3 값 3.2초)
    quote_bottom: RelationQuoteBottom
    quote_source: RelationQuoteSource

    @model_validator(mode="after")
    def _within_rules(self) -> "RelationPanelRules":
        lo, hi = self.edge_dur_range
        if not lo <= self.edge_dur_sec <= hi:
            raise ValueError(f"edge_dur_sec {self.edge_dur_sec} 가 규칙 범위 {self.edge_dur_range} 밖 (08 §3 규칙 2)")
        lo, hi = self.edge_gap_range
        if not lo <= self.edge_gap_sec <= hi:
            raise ValueError(f"edge_gap_sec {self.edge_gap_sec} 가 규칙 범위 {self.edge_gap_range} 밖 (08 §3 규칙 2)")
        return self


class PanelRules(_Strict):
    relation: RelationPanelRules


class Colors(_Strict):
    ru: str
    us: str
    gold: str
    teal: str
    green: str
    muted: str
    amber: str
    sea_label: str
    water: str
    badge_bg: str
    panel_cover: Color4
    card_bg: Color4
    panel_card_bg: Color4


class Fonts(_Strict):
    sans: str
    serif: str
    display: str
    mono: str
    mono_hangul_fallback: str
    display_space_advance: float


class LabelRules(_Strict):
    border_lod_w: float
    admin1_fade_w: Range2
    province_w_max: float
    city_max_per_frame: int
    country_rank_thr: dict[int, int]
    city_rank_thr: dict[int, int]


class GeoRules(_Strict):
    land_miss_allow_px2: float


class CreditRules(_Strict):
    """D-0030(D35) — 권리 종류별 표기 위치(엔딩 카드 / 설명문만)."""

    card_kinds: list[str] = Field(min_length=1)
    description_only_kinds: list[str] = Field(default_factory=list)


class Registries(_Strict):
    event_types: list[str]
    event_types_planned: list[str]
    panel_kinds: list[str]
    panel_kinds_planned: list[str]
    badge_kinds: list[str]
    accents: list[str]


class Loudnorm(_Strict):
    I: float  # noqa: E741 — ffmpeg loudnorm 파라미터 이름 그대로
    TP: float
    LRA: float


class AudioRules(_Strict):
    bed_gain: float
    duck_depth: float
    duck_pre_sec: float
    duck_post_sec: float
    duck_smooth_sec: float
    narration_peak: float
    master_peak: float
    loudnorm: Loudnorm
    sfx_policy: str


class QAChecks(_Strict):
    overlap_core_elements: int
    offscreen_clip: int
    missing_glyphs: int
    labels_per_frame_max: int
    subtitle_lines_max: int
    rights_missing: int
    forbidden_components: int
    visual_qa_loop_max: int


class ProvenanceRules(_Strict):
    required_keys: list[str]
    fail_if_drops: bool


class VideoRules(_Strict):
    """`rules/video_rules.yaml` 최상위 모델."""

    schema_version: int
    rules_version: str
    banned_phrases: BannedPhrases
    balance_principles: list[str]
    script_schema: ScriptSchemaRules
    tts_rules: TTSRules
    shot_grammar: ShotGrammar
    media_beats: MediaBeats
    hud: HudRules
    layout_480p: Layout480p
    panels: PanelRules
    colors: Colors
    fonts: Fonts
    labels: LabelRules
    geo: GeoRules
    credits: CreditRules
    registries: Registries
    audio: AudioRules
    qa_checks: QAChecks
    provenance: ProvenanceRules
