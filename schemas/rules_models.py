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
    labels: dict[str, Optional[str]]          # v3.0.0 — 도시어 claim status → 라벨 문구(D-0043)
    label_strength_order: list[str]           # 약한 것부터(한 문장에 여러 claim 이면 가장 약한 것)
    attribution_markers: list[str] = Field(min_length=1)   # v3.2.0 — unverified 인용 문장의 귀속 표현(린트 경고)

    @model_validator(mode="after")
    def _label_keys(self) -> "ScriptSchemaRules":
        if set(self.labels) != set(self.label_strength_order) or len(self.label_strength_order) != len(set(self.label_strength_order)):
            raise ValueError("script_schema.labels 키와 label_strength_order 가 같은 집합이어야 한다")
        return self


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


class TTSRiskPattern(_Strict):
    kind: str
    regex: str
    hint: str
    ignore_case: bool = False


class TTSRisk(_Strict):
    """v3.0.0 — 옛 orchestrator/tts_lint 패턴(D-0040 작업 8). 발음 텍스트 경고."""

    covered_before_roman: list[str]
    patterns: list[TTSRiskPattern]


class PronounceRules(_Strict):
    """v3.0.0 — 옛 orchestrator/tts_pronounce 사전 경로(저장소 기준)."""

    dict_path: str


class BesidePanel(_Strict):
    """패널 옆 미디어 슬롯(v3.2.0, D-0050 NB9). 그 시각 활성 패널이 차지한 상자(`engine.panels.OCCUPIED`)·자막·날짜
    예약 영역을 피하는 첫 후보 자리 [x, y](폭 w). 모든 후보가 막히면 오류(조용히 겹치지 않는다, P6)."""

    w: float = Field(gt=0)
    gap_px: float = Field(ge=0)
    candidates: list[tuple[float, float]] = Field(min_length=1)


class PlacementSlot(_Strict):
    """배치 슬롯(v3.1.0, 17 §2 `place:`). box·point·card·beside_panel 중 정확히 하나."""

    kinds: list[str] = Field(min_length=1)
    box: Optional[tuple[float, float, float]] = None
    point: Optional[tuple[float, float]] = None
    card: Optional[float] = None
    beside_panel: Optional[BesidePanel] = None

    @model_validator(mode="after")
    def _one(self) -> "PlacementSlot":
        is_card = "card" in self.model_fields_set
        if sum([self.box is not None, self.point is not None, is_card, self.beside_panel is not None]) != 1:
            raise ValueError("슬롯은 box·point·card·beside_panel 중 하나")
        return self


class PlacementRules(_Strict):
    auto_media: dict[str, dict[str, str]]    # 종류 → {map|panel → 슬롯}
    slots: dict[str, PlacementSlot]

    @model_validator(mode="after")
    def _refs(self) -> "PlacementRules":
        bad = [s for m in self.auto_media.values() for s in m.values() if s not in self.slots]
        if bad:
            raise ValueError(f"auto_media 가 없는 슬롯을 가리킨다: {bad}")
        return self


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
    scene_attach_lead_sec: float = Field(ge=0)
    w_guide: dict[str, float | Range2]


class MediaBeats(_Strict):
    kinds: list[str]
    photo_show_sec: Range2
    clip_show_sec: Range2
    file_photo_label_required: bool
    caption_credit_required: bool
    ai_generated_forbidden: bool
    casualty_identifiable_forbidden: bool
    credit_formats: dict[str, str]           # v2.5.5 — 화면 출처 줄(레지스트리 필드로만 조립, D-0036 작업 3)
    triggers: dict[str, list[str]]           # v2.5.5 — 14 §10.2 트리거 → 형태 제안(제안만, P8)
    caption_bar_px: float                    # 사진·영상 캡션 바 높이(14 §4.1) — 배치 점검용
    registry: str                            # v2.5.5 — 미디어 레지스트리 경로(저장소 기준)


class MediaDensity(_Strict):
    """14 §10.1 밀도 (v2.5.5, D-0037·D38). 모두 경고(오류 아님)."""

    per_item_sec: Range2                  # 전체 러닝타임 ÷ 개수
    per_scene_max: int
    scene_exempt_kinds: list[str]         # 장면당 개수에서 뺀다(기사 카드 = 일반 카드 자리 대체)
    no_same_kind_adjacent_scenes: bool
    window_sec: float                     # 짧은 구간 몰림 창
    window_max: int                       # 창 안 최대 개수 — 넘으면 경고
    window_exempt_kinds: list[str]


class MediaRules(_Strict):
    density: MediaDensity


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


class SubtitleLabelStyle(_Strict):
    """v3.3.0 NB12 — 자막 앞 검증 라벨(<미검증>·<논쟁>)."""

    size_ratio: float = Field(gt=0, le=1)
    color: str
    gap_px: float = Field(ge=0)


class SubtitleLayout(_Strict):
    size: float
    last_line_y: float
    line_gap: float
    halo: float
    halo_alpha: float
    emphasis_color: str
    label_style: SubtitleLabelStyle


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


class PostCardLayout(_Strict):
    """v3.2.0 18 §5 — X 게시물 카드."""

    w: float
    y: float
    panel_y: float
    radius: float
    bg: tuple[float, float, float, float]
    border_alpha: float
    pad: float
    icon_r: float
    name_size: float
    handle_size: float
    chip_size: float
    body_size: float
    body_line: float
    body_max_lines: int
    orig_size: float
    orig_max_words: int
    foot_size: float
    slide_px: float
    fade_sec: float
    hl_delay_sec: float
    hl_sec: float


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
    post_card: PostCardLayout    # v3.2.0
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
    edge_label: RelationEdgeLabel   # 규칙 4 — 라벨은 첫 선이 자라기 시작한 뒤(08 §3 v2.5.5 정정, D-0035 NB6)
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


class TimelinePanelRules(_Strict):
    """08 §5 v3 P_timeline 합격 값 + 자동 층 배치(08 §11-3, D-0032 작업 3)."""

    x: Range2                   # 축 x0→x1
    y: float                    # 축 y
    axis_draw_sec: float
    axis_alpha: float
    axis_width: float
    tick_h: float
    tick_w: float
    month: PanelText            # 월 라벨(IBM Plex Sans KR — Mono 에는 한글이 없다)
    month_dx: float
    month_dy: float
    month_alpha: float
    band_h: float
    band_alpha: float
    band_fade_sec: float
    band_label: PanelText
    band_label_dy: float
    event_fade_sec: float
    dim_alpha: float
    stem_alpha: float
    stem_width: float
    dot_r: float
    layer_px: list[float] = Field(min_length=1)   # 층 1·2·3… 의 축에서 거리(위·아래 같은 값)
    date: PanelText
    date_dy_above: float
    date_dy_below: float
    label: PanelText
    label_dy_above: float
    label_dy_below: float
    label_gap_px: float         # 같은 층 라벨 상자 사이 최소 간격(자동 층 배치)
    cursor_alpha: float
    cursor_width: float
    cursor_dash: list[float]
    cursor_y: Range2


class ReservedRules(_Strict):
    """카드·기사 카드 영역 RESERVED — 지도 뱃지·마커 라벨 회피 (D-0033, D36, 08 §10·§11-4)."""

    badge_strategy: Literal["push", "hide"]
    push_gap_px: float
    push_directions: list[Literal["left", "down", "left-down"]] = Field(min_length=1)   # 같은 이동량이면 앞 방향 우선
    max_push_px: float            # 넘으면 hide 로 떨어진다(카드가 떠 있는 동안만) — provenance reserved.avoidance
    marker_label_strategy: Literal["hide", "none"]
    min_zone_alpha: float         # 이 값 이하의 영역 존재도는 영역으로 치지 않는다
    lead_sec: float               # 영역 존재도: 카드 구간 [t0, t1] 은 1, 앞뒤 lead_sec 동안 오르내림 — 카드가 겹쳐 바뀌어도 뱃지가 튀지 않는다


# ------------------------------------------------------------------ v2 번들 차트 이식 (D-0032 작업 5, 08 §8·§9)
XY = tuple[float, float]


class TextAt(_Strict):
    x: float = 0.0
    y: float
    size: float
    halo: float = 0.0
    spacing: float = 0.0


class ProvTagRules(_Strict):
    """08 §9 추정 태그 — 위치는 D-0034(D37): 제목 아래 가운데. 모서리(HUD) 아님."""

    anchor: Literal["below_title"]
    y_offset_px: float
    align: Literal["center"]
    font: str
    size: float
    color: str
    border_px: float
    alpha: float
    pad_x: float
    h: float
    box_dy: float
    r: float
    gap_px: float
    claim_color: str
    body_top_px: float
    body_top_px_with_tag: float


class DotsRules(_Strict):
    origin: XY
    spacing: float
    radius: float
    grid: tuple[int, int]          # 행 × 열
    fill_start_sec: float
    fill_step_sec: float
    fill_sec: float
    base_rgb: tuple[float, float, float]
    pulse_rate: float              # sin(t × rate)
    pulse_r: float
    pulse_base: float
    pulse_amp: float
    pulse_alpha: float
    big: TextAt
    unit_dx: float
    unit_size: float
    caption: TextAt
    detail: TextAt
    label_sec: float
    label_fade_sec: float
    rule: tuple[float, float, float, float]   # x, y, w, 알파
    note_sec: float
    note_label: TextAt
    note_value: TextAt
    note_caption: TextAt


class GanttRules(_Strict):
    x: Range2
    axis_y: float
    axis_alpha: float
    tick_h: float
    year_dy: float
    year_size: float
    row_y0: float
    row_dy: float
    bar_h: float
    bar_r: float
    bar_alpha: float
    bar_min_w: float
    grow_start_sec: float
    grow_step_sec: float
    grow_sec: float
    label_dx: float                # 막대 왼쪽 라벨 오른쪽 끝(축 x0 기준 음수)
    label_dy: float
    label_size: float
    note_dy: float
    note_size: float
    today_sec: float
    today_fade_sec: float
    today_top: float
    today_dash: list[float]
    today_width: float
    today_alpha: float
    today_label_dy: float
    today_label_size: float
    today_label_halo: float


class DualLineRules(_Strict):
    x: Range2
    y: Range2                      # 위 y, 아래 y
    grid_alpha: float
    tick_dx: float
    tick_dy: float
    tick_size: float
    x_pad: float
    x_label_dy: float
    x_label_size: float
    draw_start_sec: float
    draw_step_sec: float           # 두 번째 선 지연
    draw_sec: float
    samples: int                   # 점 사이 보간 수
    line_width: float
    point_r: float
    value_dy_above: float
    value_dy_below: float
    value_size: float
    value_halo: float
    name_dx: float
    name_dy: float
    name_size: float


class ForkRules(_Strict):
    origin: XY
    origin_r: float
    origin_label_dy: float
    origin_label_size: float
    origin_label_halo: float
    card_rgb: tuple[float, float, float]
    branch_x: float
    card_x: float
    card_w: float
    card_h: float
    card_r: float
    card_y0: float
    card_dy: float
    card_alpha: float
    card_bar_w: float
    grow_start_sec: float
    grow_step_sec: float
    grow_sec: float
    card_start_sec: float
    card_fade_sec: float
    samples: int
    line_width: float
    head: TextAt
    body: TextAt


class ChecklistRules(_Strict):
    box_x: float
    box: float                     # 체크박스 한 변
    box_top_dy: float              # 상자 위 끝 = 글자 기준선 + box_top_dy
    check_points: list[XY] = Field(min_length=3, max_length=3)   # 체크 두 획의 세 점(상자 왼쪽 위 기준 px)
    box_r: float
    box_alpha: float
    y0: float
    dy: float
    appear_start_sec: float
    appear_step_sec: float
    appear_sec: float
    check_delay_sec: float
    check_sec: float
    check_width: float
    text_x: float
    text_size: float
    footer_y: float
    footer_size: float
    footer_sec: float
    footer_fade_sec: float
    max_items: int


class NetworkRules(_Strict):
    """08 §3.1 — v2 P_network 를 정돈된 관계선 규칙(panels.relation 의 선 타이밍·곡선)으로 고쳐 이식."""

    columns: dict[str, float]      # left·center·right x
    cy: float
    dy: float
    R_person: float
    R_big: float
    R_other: float
    node_start_sec: float
    node_step_sec: float
    col_step_sec: float
    styles: dict[str, "RelationEdgeStyle"]   # 영향·연관·대립·동맹
    label: TextAt
    label_sec: float
    mention_pulse_rate: float
    mention_alpha: float
    mention_width: float
    mention_ring: float
    mention_grow: float
    mention_hold_sec: float
    mention_lead_sec: float
    max_edges: int


class ChartRules(_Strict):
    dots: DotsRules
    gantt: GanttRules
    dual_line: DualLineRules
    fork: ForkRules
    checklist: ChecklistRules
    network: NetworkRules


class PanelRules(_Strict):
    relation: RelationPanelRules
    timeline: TimelinePanelRules
    reserved: ReservedRules
    prov_tag: ProvTagRules
    charts: ChartRules


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
    land_fill_min_ratio: float = Field(gt=0, le=1)   # v4.1.0 D-0078


class CreditRules(_Strict):
    """D-0030(D35) — 권리 종류별 표기 위치(엔딩 카드 / 설명문만)."""

    card_kinds: list[str] = Field(min_length=1)
    description_only_kinds: list[str] = Field(default_factory=list)
    music_card_license: str        # v3.4.0 D-0060 작업 1 — 엔딩 카드 음악 라이선스 줄(.replace 자리표시 {author}·{license})
    music_description: str         # 설명란 음악 문구({name}·{author}·{license}) — description.yaml footer 의 {music} 자리


class Registries(_Strict):
    event_types: list[str]
    event_types_planned: list[str]
    panel_kinds: list[str]
    panel_kinds_planned: list[str]
    badge_kinds: list[str]
    accents: list[str]
    stages: list[str] = Field(min_length=1)   # v4.1.0 D-0076 — 무대 레지스트리(engine.stage.STAGE_CLASSES 와 일치)
    stages_planned: list[str] = Field(default_factory=list)   # v4.2.0 D-0081 — 20 §2.1 구현 전 무대(장르 프로필 proposed 만)
    primitives: list[str] = Field(default_factory=list)       # v4.2.0 D-0081 — engine/primitives/<id>.py (20 §4.2)
    primitives_planned: list[str] = Field(default_factory=list)   # v4.2.0 D-0082 — 구현 전 프리미티브(장르 프로필 proposed 만)

    @model_validator(mode="after")
    def _disjoint(self) -> "Registries":
        for a, b in (("stages", "stages_planned"), ("primitives", "primitives_planned")):
            both = set(getattr(self, a)) & set(getattr(self, b))
            if both:
                raise ValueError(f"registries.{a} 와 {b} 에 같은 이름: {sorted(both)}")
        return self


class Loudnorm(_Strict):
    I: float  # noqa: E741 — ffmpeg loudnorm 파라미터 이름 그대로
    TP: float
    LRA: float


class WhooshSfx(_Strict):
    dur_sec: float
    shape_pow: float
    low_b: float
    low_a: float
    low_gain: float
    high_b: float
    high_a: float
    high_gain: float
    release_sec: float
    release_tau_sec: float
    gain: float


class BoomSfx(_Strict):
    dur_sec: float
    f0_hz: float
    sweep_hz: float
    sweep_tau_sec: float
    tone_tau_sec: float
    tone_gain: float
    noise_b: float
    noise_a: float
    noise_tau_sec: float
    noise_gain: float


class TickSfx(_Strict):
    dur_sec: float
    freq_hz: float
    tau_sec: float
    gain: float


class TitleCardSfx(_Strict):
    offset_sec: float
    whoosh_dur_sec: float
    whoosh_v: float
    boom_v: float


class SceneStartSfx(_Strict):
    lead_sec: float
    whoosh_dur_sec: float
    whoosh_v: float


class SfxRules(_Strict):
    whoosh: WhooshSfx
    boom: BoomSfx
    tick: TickSfx
    title_card: TitleCardSfx
    scene_start: SceneStartSfx


class AudioQARules(_Strict):
    i_tol_lu: float = Field(gt=0)
    music_under_narration_db: tuple[float, float]
    tp_codec_margin_db: float = Field(ge=0)
    sentence_rms_dev_db: float = Field(gt=0)
    sentence_rms_window_sec: float = Field(gt=0)
    sentence_rms_floor_db: float = Field(lt=0)


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
    sample_rate: int              # v3.4.0 D-0060 §0 — 코덱 상수 확인용(코드 SR 과 테스트로 일치)
    seed: int
    tail_sec: float
    loop_xfade_sec: float
    fade_in_sec: float
    fade_out_sec: float
    fx_duck: float
    crossfade_sec: float = Field(gt=0)
    qa: AudioQARules
    norm_eps: float
    sfx: SfxRules


class QAChecks(_Strict):
    overlap_core_elements: int
    offscreen_clip: int
    missing_glyphs: int
    labels_per_frame_max: int
    subtitle_lines_max: int
    rights_missing: int
    forbidden_components: int
    glyph_size_exempt: list[Literal["end_card", "media_meta"]]   # v3.6.0 D-0069 — 역할 레지스트리(엔진 text(role=) 와 같은 이름)
    label_hidden_max_ratio: float = Field(gt=0, le=1)   # v3.6.0 D-0068
    planned: list[str] = Field(default_factory=list)   # v4.2.0 D-0081 — 예정 검사 id(장르 프로필 proposed qa_extra 만)
    chart_targets: dict[Literal["value", "date", "none"], list[Literal["chart_honesty", "series_limit_3", "units_visible", "as_of_visible"]]]   # v4.3.0 D-0087
    series_max: int = Field(ge=1)   # v4.3.0 — 20 §5.3 계열 수 상한
    visual_qa_loop_max: int
    loop_pick_order: list[Literal["checks_hard", "qa_hard", "qa_soft"]]


class BundleRules(_Strict):
    """v3.5.0 D-0063 작업 4 — 번들 어휘 → 저장소 어휘 대응표(bundle/to_direction.py)."""

    chart_panels: dict[str, str] = Field(min_length=1)
    edge_types: dict[str, str] = Field(min_length=1)
    verified_when: str
    dual_line_colors: list[str] = Field(min_length=2)
    gantt_colors: list[str] = Field(min_length=1)
    node_accent: str
    dual_line_ticks: int = Field(ge=1)
    nice_mantissas: list[float] = Field(min_length=1)


class ProvenanceRules(_Strict):
    required_keys: list[str]
    fail_if_drops: bool


class VerificationRules(_Strict):
    """v3.2.0 D-0052(D50) — 교차 확인(인용 대조) 수치. 판정 코드는 orchestrator/source_verify.py."""

    quote_max_chars: int = Field(gt=0)
    independent_min: int = Field(ge=2)
    reprint_markers: list[str] = Field(min_length=1)
    body_max_chars: int = Field(gt=0)


class PxBox(_Strict):
    up: float
    down: float
    side: float


class BadgePx(_Strict):
    up_factor: float
    down_px: float
    side_factor: float


class FramingRules(_Strict):
    margin_px: float
    top_px: float
    w_min: float = Field(gt=0)
    w_max: float = Field(gt=0)
    w_steps: int = Field(ge=2)
    center_grid: int = Field(ge=1)
    date_reserve_chars: float = Field(gt=0)
    cover_samples: int = Field(ge=2)
    verify_rounds: int = Field(ge=1)
    path_w_step: float = Field(gt=1)
    context_w_min: dict[str, float]   # v3.3.0 D-0058 — shot_grammar.w_guide 분류 → w 하한(키 집합 = w_guide, VideoRules 가 검사)
    marker_px: PxBox
    badge_px: BadgePx
    point_px: PxBox


class CameraRules(_Strict):
    """v3.3.0 D-0056 — 카메라 자동화 보조(05 §7)."""

    framing: FramingRules


class PreviewRules(_Strict):
    """v3.3.0 F6 — auto 프리뷰 샘플."""

    min_body_cuts: int = Field(ge=1)


class GoldenRules(_Strict):
    """v3.6.0 D-0066 작업 4 — 해상도 비교 임계."""

    res_compare_mad_max: float = Field(gt=0, lt=1)


class StageContinuityRules(_Strict):
    max_switches: int = Field(ge=0)


class TimelineLod(_Strict):
    quarter_below_w: float = Field(gt=0)
    month_below_w: float = Field(gt=0)
    day_below_w: float = Field(gt=0)
    day_label_every: int = Field(ge=1)

    @model_validator(mode="after")
    def _order(self) -> "TimelineLod":
        if not self.day_below_w < self.month_below_w < self.quarter_below_w:
            raise ValueError("stage_timeline.lod: day < month < quarter 여야 한다")
        return self


class TimelineGrid(_Strict):
    year_alpha: float
    minor_alpha: float
    line_w: float
    label_font: str
    label_size: float
    label_halo: float
    label_dy: float
    label_margin_px: float
    min_label_gap_px: float


class TimelineLaneLabel(_Strict):
    x: float
    dy: float
    size: float
    font: str
    halo: float


class TimelineWave(_Strict):
    amp_px: float
    period_px: float = Field(gt=0)
    line_w: float
    color: str
    alpha: float
    shade_alpha: float
    label: str = Field(min_length=1)
    label_font: str
    label_size: float
    label_halo: float
    label_dy: float
    label_margin_px: float


class TimelineSeries(_Strict):
    lane_pad_top: float = Field(ge=0, lt=0.5)
    lane_pad_bottom: float = Field(ge=0, lt=0.5)
    line_w: float
    tip_r: float
    fade_sec: float
    min_alpha: float
    playhead: float = Field(gt=0, le=1)
    grow_in_sec: float = Field(gt=0)
    clip_below_px: float
    value_dx: float
    value_dy: float
    value_size: float
    value_font: str
    value_halo: float
    value_min_x: float
    axis_zone_px: float
    grid_alpha: float
    zero_alpha: float
    grid_w: float
    axis_label_margin_px: float
    axis_label_dy: float
    axis_label_size: float
    axis_label_font: str
    axis_label_halo: float
    source_dy: float
    source_step: float
    source_size: float
    source_font: str
    source_halo: float


class TimelineMissingMark(_Strict):
    label: str = Field(min_length=1)
    label_font: str
    label_size: float
    label_halo: float
    label_dy: float
    color: str
    alpha: float
    dash: list[float]
    line_w: float
    inset_px: float


class StageTimelineRules(_Strict):
    """v4.3.0 D-0084 작업 3·4·D-0085·D-0086 — 시간축 무대·시리즈 레이어 토큰(engine/stage_timeline.py·engine/layers/series.py)."""

    lane_h: float = Field(gt=0)
    area_top: float
    area_bottom: float
    bg_rgb: tuple[float, float, float]
    band_alpha: list[float] = Field(min_length=1)
    lane_line_alpha: float
    lane_line_w: float
    lod: TimelineLod
    grid: TimelineGrid
    lane_label: TimelineLaneLabel
    wave: TimelineWave
    series: TimelineSeries
    missing_mark: TimelineMissingMark


class GenrePromptRules(_Strict):
    """v4.4.0 D-0090 작업 1 — 장르 프롬프트 층(docs/handoff/20 §5·§6·§7·§9). 문장은 여기, 켜고 끄는 것은 장르 프로필."""

    base_genre: str
    narration: dict[str, str] = Field(min_length=1)
    data_sources: list[str] = Field(min_length=1)
    rubric_extra: list[str] = Field(min_length=1)
    stage_grammar: dict[str, list[str]] = Field(min_length=1)


class DataRules(_Strict):
    """v4.3.0 D-0084 작업 1 — 데이터 레코드 허용 목록(docs/handoff/20 §5.1, schemas/data_models.py)."""

    units: list[str] = Field(min_length=1)
    licenses_allowed: list[str] = Field(min_length=1)
    unit_prefixes: list[str] = Field(min_length=1)   # v4.3.0 D-0087 보정 1
    sources_allowed: list[str] = Field(min_length=1)
    frequencies: list[Literal["monthly"]] = Field(min_length=1)
    transforms: dict[str, str] = Field(min_length=1)
    series_dir: str


class StageRules(_Strict):
    """v4.1.0 D-0076 작업 5·D-0077 — 무대 연속성 검사(checks stage_continuity)."""

    max_secondary: int = Field(ge=0)
    continuity: StageContinuityRules


class StatementDiffLayout(_Strict):
    """v4.2.0 D-0081 작업 5 — statement_diff(성명서 문구 비교) 레이아웃 토큰."""

    w: float = Field(gt=0)
    pad_x: float
    pad_top: float
    pad_bottom: float
    label_gap: float
    line_h: float
    row_gap: float
    src_gap: float
    tag_size: float
    tag_spacing: float
    label_size: float
    text_size: float
    radius: float
    bar_w: float
    bar_inset: float
    strike_w: float
    strike_rise: float
    fade_sec: float = Field(ge=0.4, le=0.6)   # 20 §4.2 등장 0.4~0.6초
    slide_px: float


class PrimitivesRules(_Strict):
    """v4.2.0 D-0081 작업 4 — 프리미티브별 레이아웃 토큰(engine.style.PRIMITIVES). 요소가 등록될 때 필드를 더한다."""

    statement_diff: Optional[StatementDiffLayout] = None


class VideoRules(_Strict):
    """`rules/video_rules.yaml` 최상위 모델."""

    schema_version: int
    rules_version: str
    banned_phrases: BannedPhrases
    balance_principles: list[str]
    script_schema: ScriptSchemaRules
    verification: VerificationRules   # v3.2.0 — D-0052(D50)
    tts_rules: TTSRules
    tts_risk: TTSRisk             # v3.0.0 — D-0040 작업 8
    pronounce: PronounceRules     # v3.0.0 — D-0040 작업 8
    placement: PlacementRules     # v3.1.0 — D-0047 작업 5
    shot_grammar: ShotGrammar
    media_beats: MediaBeats
    media: MediaRules
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
    preview: PreviewRules          # v3.3.0 — D-0056 F6
    golden: GoldenRules            # v3.6.0 — D-0066 작업 4
    camera: CameraRules            # v3.3.0 — D-0056 작업 2
    stage: StageRules              # v4.1.0 — D-0076 작업 5
    qa_checks: QAChecks
    primitives: PrimitivesRules = Field(default_factory=PrimitivesRules)   # v4.2.0 D-0081
    stage_timeline: StageTimelineRules   # v4.3.0 — D-0084 작업 3·D-0085
    data: DataRules                # v4.3.0 — D-0084 작업 1
    genre_prompt: GenrePromptRules  # v4.4.0 — D-0090 작업 1
    bundle: BundleRules            # v3.5.0 — D-0063 작업 4
    provenance: ProvenanceRules

    @model_validator(mode="after")
    def _context_keys(self) -> "VideoRules":
        """camera.framing.context_w_min 키 = shot_grammar.w_guide 키(누락·초과 = 규칙 로드 오류, D-0058 §1)."""
        bad = sorted(set(self.bundle.chart_panels.values()) - set(self.registries.panel_kinds))
        if bad:
            raise ValueError(f"bundle.chart_panels 의 패널 kind 가 registries.panel_kinds 에 없다: {bad}")
        bad = sorted(set(self.bundle.edge_types.values()) - set(self.panels.charts.network.styles))
        if bad:
            raise ValueError(f"bundle.edge_types 값이 panels.charts.network.styles 에 없다: {bad}")
        bad = sorted(set(self.genre_prompt.stage_grammar) - set(self.registries.stages))
        if bad:
            raise ValueError(f"genre_prompt.stage_grammar 의 무대가 registries.stages 에 없다: {bad}")
        a, b = set(self.camera.framing.context_w_min), set(self.shot_grammar.w_guide)
        if a != b:
            raise ValueError(f"camera.framing.context_w_min 키가 shot_grammar.w_guide 와 다르다 — 누락 {sorted(b - a)} · 초과 {sorted(a - b)}")
        return self
