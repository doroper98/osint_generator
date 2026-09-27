"""`rules/video_rules.yaml` Pydantic 모델 (v2.0.0, docs/handoff/15 §3 P3).

영상 규칙 SSOT 의 계약. 모든 모델은 `extra="forbid"` — 규칙 파일에 모르는 키가 들어오면
조용히 무시하지 않고 로드 단계에서 실패한다(15 P6). 수치의 의미·출처는 YAML 주석과
docs/handoff/{03,05,08,09,10,14,17} 이 정본이다.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


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
    colors: Colors
    fonts: Fonts
    labels: LabelRules
    geo: GeoRules
    registries: Registries
    audio: AudioRules
    qa_checks: QAChecks
    provenance: ProvenanceRules
