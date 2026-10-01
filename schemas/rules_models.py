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
    screen: Optional[list[tuple[float, float]]] = None   # v4.8.0 D-0104 D2(c) — 패널 위 화면 고정 점들(동시 n 번째 = n 번째 점)
    stages: Optional[list[str]] = None   # v5.2.0 D-0132 — 이 주 무대에서만 쓰는 슬롯(없으면 무대 무관). 다른 무대 = 배치 오류(P10)

    @model_validator(mode="after")
    def _one(self) -> "PlacementSlot":
        is_card = "card" in self.model_fields_set
        if sum([self.box is not None, self.point is not None, is_card, self.beside_panel is not None, bool(self.screen)]) != 1:
            raise ValueError("슬롯은 box·point·card·beside_panel·screen 중 하나")   # align(옛 기사 가운데)은 v5.1.0 D-0121 §C 에서 삭제(P2)
        return self


class PlacementRules(_Strict):
    auto_media: dict[str, dict[str, str]]    # 종류 → {map|panel → 슬롯}
    stage_slots: dict[str, dict[str, str]] = Field(default_factory=dict)   # v4.4.0 D-0093 — 무대 → {이벤트 종류 → 슬롯}
    slots: dict[str, PlacementSlot]

    @model_validator(mode="after")
    def _refs(self) -> "PlacementRules":
        bad = [s for m in self.auto_media.values() for s in m.values() if s not in self.slots]
        if bad:
            raise ValueError(f"auto_media 가 없는 슬롯을 가리킨다: {bad}")
        bad = [f"{st}.{k}→{s}" for st, m in self.stage_slots.items() for k, s in m.items() if s not in self.slots or k not in self.slots[s].kinds]
        if bad:
            raise ValueError(f"stage_slots 가 없는 슬롯이나 그 종류를 받지 않는 슬롯을 가리킨다: {bad}")
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


class StaticCreep(_Strict):
    """느린 푸시인(v4.11.0 back_and_forth D-0118 §1) — [static-window] 창에서만 카메라 w 를 창 길이에 걸쳐 w_ratio 로 선형 축소."""

    enabled: bool
    w_ratio: float = Field(gt=0.9, le=1)      # 0.96 = 4 % — 줌 범프 아님(G4-16)
    min_window_sec: float = Field(gt=0)


class StaticWindow(_Strict):
    """정적 구간 검사 `[static-window]`(v4.11.0 D-0118 §1) — 지도 무대의 window_sec 슬라이딩 창에서 change_kinds 변화 < min_changes = warning."""

    window_sec: float = Field(gt=0)
    min_changes: int = Field(ge=1)
    change_kinds: list[str] = Field(min_length=1)   # registries.event_types 이름 + camera(카메라 키)
    creep: StaticCreep
    ladder: str = Field(min_length=1)                # 연출 프롬프트 변화 사다리({{RULES.pacing.static_window}}), {window_sec} 자리


class PacingRules(_Strict):
    static_window: StaticWindow


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


class FlickrRules(_Strict):
    """v4.4.0 D-0090 작업 4 — 기관 공식 Flickr 사진 받기(tools/media_fetch)."""

    licenses_allowed: dict[str, str] = Field(min_length=1)
    size_suffix: str = Field(min_length=1)


class MediaRules(_Strict):
    density: MediaDensity
    flickr: Optional[FlickrRules] = None   # v4.4.0


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


class EndCardNotice(_Strict):
    """v4.5.0 D85 — 엔딩 카드 맨 마지막 줄 검증 안내(가장 작은 글씨 한 줄). template 의 `{n}` = 라벨 문장 수."""

    size: float = Field(gt=0)
    dy: float = Field(gt=0)
    template: str = Field(pattern=r"\{n\}")


class EndCardVersionStamp(_Strict):
    """v5.1.0 D-0124(사용자 결정 D109) — 엔딩 카드 오른쪽 아래 구석 버전 도장. 문자열 = "v" + VERSION 파일(렌더 시점, P3).
    notice_unverified 와 겹치면 notice 를 우선하고 도장을 dy 만큼 위로 올린다."""

    x_from_right: float = Field(ge=0)
    y_from_bottom: float = Field(ge=0)
    size: float = Field(gt=0)
    font: str
    alpha: float = Field(gt=0, le=1)
    dy: float = Field(gt=0)


class EndCardLayout(_Strict):
    dur_sec: float
    item_size: float
    license_size: float
    notice_unverified: EndCardNotice
    version_stamp: EndCardVersionStamp
    bottom_margin: float = Field(ge=0)   # v4.5.0 D-0098 — 크레딧 마지막 기준선과 하단 구분선(H−44) 사이 최소 여백
    hold_black_after: bool = True        # v4.4.0 dmz_mine_2026(v4.7.0 병합) — 카드 뒤 검정 유지(지도가 다시 드러나지 않게)
    # v4.7.0 D-0106 1-C — 넘치면 롤(속도 상한 넘으면 오류)
    scroll_top: float
    scroll_bottom: float
    scroll_hold_in_sec: float = Field(ge=0)
    scroll_hold_out_sec: float = Field(ge=0)
    scroll_fade_px: float = Field(ge=0)
    scroll_max_px_per_sec: float = Field(gt=0)

    @model_validator(mode="after")
    def _scroll_span(self) -> "EndCardLayout":
        if self.dur_sec <= self.scroll_hold_in_sec + self.scroll_hold_out_sec:
            raise ValueError("end_card.dur_sec 는 scroll_hold_in_sec + scroll_hold_out_sec 보다 길어야 한다(롤 시간)")
        if self.scroll_bottom <= self.scroll_top + self.scroll_fade_px:
            raise ValueError("end_card.scroll_bottom 은 scroll_top + scroll_fade_px 보다 아래여야 한다")
        if self.version_stamp.size > min(self.license_size, self.notice_unverified.size):
            raise ValueError("end_card.version_stamp.size 는 엔딩 카드에서 가장 작은 글씨(license_size·notice) 이하여야 한다(D-0124)")
        return self


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
    cap_size: float       # v4.8.0 D-0101 §3 — 큰 숫자 아래 캡션(옛 리터럴 11)
    line_gap: float       # 줄 간격(옛 21)
    src_gap: float        # 출처 줄이 더하는 높이(옛 18)


class MediaCaptionLayout(_Strict):
    """v4.8.0 D-0101 §3 — 사진·영상 캡션 바·PHOTO/VIDEO 태그·컷아웃 캡션(옛 engine/layers/media.py 리터럴). 바 높이 = media_beats.caption_bar_px."""

    pad_x: float
    caption_size: float
    caption_dy: float
    credit_size: float
    credit_dy: float
    tag_size: float
    tag_h: float
    tag_dy: float
    cutout_caption_size: float
    cutout_credit_size: float


class MarkerLayout(_Strict):
    label_size: float
    sub_size: float
    sub_dy: float


class RouteLabelLayout(_Strict):
    route_size: float
    barrier_size: float


class ArticleTheme(_Strict):
    overlay: tuple[float, float, float]
    ink: tuple[float, float, float]
    muted: tuple[float, float, float]
    rule: tuple[float, float, float]


class ArticleRule(_Strict):
    w: float = Field(gt=0)
    gap: float = Field(ge=0)


class ArticleHeadline(_Strict):
    size: float = Field(gt=0)
    gap: float = Field(gt=0)
    max_lines: int = Field(ge=1)
    quotes: bool


class ArticleSub(_Strict):
    size: float = Field(gt=0)
    gap: float = Field(gt=0)
    max_lines: int = Field(ge=0)
    lead: float = Field(ge=0)


class ArticleSource(_Strict):
    size: float = Field(gt=0)
    lead: float = Field(ge=0)
    format: str = Field(pattern=r"\{publisher\}")
    translated_note: str = Field(min_length=1)


class ArticlePressFallback(_Strict):
    """v5.2.0 D-0129 §A — 프레스 사진이 없을 때 지금 무대를 흐리는 값(배경 사진 stage_backdrop 값과 분리 — hormuz 기사 골든 불변)."""

    blur_px: float = Field(gt=0)
    dim: float = Field(ge=0, le=1)


class ArticleCardLayout(_Strict):
    """v5.1.0 back_and_forth D-0121 §C — 기사 프레스 규약 v2(engine/layers/article.py 수치 전부). 옛 카드 조판 키는 삭제(P2)."""

    theme_default: Literal["dark", "light"]
    themes: dict[Literal["dark", "light"], ArticleTheme]
    press_lead_sec: float = Field(ge=0)
    press_fallback: ArticlePressFallback   # v5.2.0 D-0129 §A
    overlay_alpha: float = Field(gt=0, le=1)
    overlay_fade_sec: float = Field(gt=0)
    x_left_ratio: float = Field(gt=0, lt=1)
    max_w_ratio: float = Field(gt=0, le=1)
    rule: ArticleRule
    headline: ArticleHeadline
    sub: ArticleSub
    source: ArticleSource

    @model_validator(mode="after")
    def _themes(self) -> "ArticleCardLayout":
        if set(self.themes) != {"dark", "light"}:
            raise ValueError("article_card.themes 는 dark·light 둘")
        return self

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


class BadgeLabelBox(_Strict):
    pad_x: float
    gap: float
    pad_y: float
    inset: float
    role_gap: float
    role_pad: float
    side_dx: float
    side_dy: float
    side_role_dy: float


class BadgeLayout(_Strict):
    R_person_solo: float
    R_person_group: Range2
    R_person_panel: float
    R_flag: Range2
    R_other: float
    resize_sec: float
    fade_in_sec: float
    fade_out_sec: float
    label_solo: Range2
    label_group: Range2
    label_side: Range2
    label_box: BadgeLabelBox
    head_reserve: Literal["measured", "factor"] = "factor"   # v4.8.0 D-0112
    edge_nudge: bool = False
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
    media_caption: MediaCaptionLayout      # v4.8.0 D-0101 §3
    marker: MarkerLayout
    route_label: RouteLabelLayout
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


class PrecedentPanelRules(_Strict):
    """v4.8.0 D-0101 §3 — 선례 카드 글자(옛 리터럴). 카드 상자 172×212 는 코드(v3 합격 기하)."""

    year_size: float
    title_size: float
    line_size: float
    caption_size: float


class VersusPanelRules(_Strict):
    title_size: float
    item_size: float
    src_size: float


class PanelRules(_Strict):
    relation: RelationPanelRules
    timeline: TimelinePanelRules
    reserved: ReservedRules
    prov_tag: ProvTagRules
    charts: ChartRules
    precedent: PrecedentPanelRules    # v4.8.0 D-0101 §3
    versus: VersusPanelRules


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


class GazetteerRules(_Strict):
    """v4.10.0 D-0116(B-1) — 지명 사전 위치와 NE 수록 기준. 항목별 허용 오차는 사전 파일에 있다."""

    path: str
    ne_min_population: int = Field(gt=0)
    ne_tol_km: float = Field(gt=0)


class GeoRules(_Strict):
    land_miss_allow_px2: float
    land_fill_min_ratio: float = Field(gt=0, le=1)   # v4.1.0 D-0078
    boundary_names: list[str] = Field(min_length=1)   # v4.7.0 D-0107 D2(b) — checks [boundary-as-route]
    gazetteer: GazetteerRules                         # v4.10.0 D-0116 — checks [geo-mismatch]


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
    bed_bass_rise_db: tuple[float, float]            # v4.6.0 D-0097 작업 3·D-0102 1-A(판정 = 상승폭)
    bed_bass_band_hz: tuple[float, float]
    bed_mid_band_hz: tuple[float, float]

    @model_validator(mode="after")
    def _bands(self) -> "AudioQARules":
        for name in ("bed_bass_rise_db", "bed_bass_band_hz", "bed_mid_band_hz"):
            lo, hi = getattr(self, name)
            if not lo < hi:
                raise ValueError(f"audio.qa.{name}: [낮은, 높은] 순서여야 한다 — {lo, hi}")
        return self


class BedShelf(_Strict):
    freq_hz: float = Field(gt=0)
    gain_db: float
    q: float = Field(gt=0)


class BedSub(_Strict):
    band_hz: tuple[float, float]
    out_lp_hz: float = Field(gt=0)
    filter_order: int = Field(ge=1)
    gain: float = Field(ge=0)
    env_attack_sec: float = Field(gt=0)
    env_release_sec: float = Field(gt=0)
    env_block_sec: float = Field(gt=0)

    @model_validator(mode="after")
    def _band(self) -> "BedSub":
        if not 0 < self.band_hz[0] < self.band_hz[1]:
            raise ValueError(f"audio.bed_bass.sub.band_hz: 0 < 낮은 < 높은 — {self.band_hz}")
        return self


class BedSwell(_Strict):
    sec: float = Field(gt=0)
    depth: float = Field(ge=0)


class BedBass(_Strict):
    """v4.6.0 D-0097 — 베드 저음 보강(audio/mix.py process_bed)."""

    shelf: BedShelf
    sub: BedSub
    swell: BedSwell
    norm_ref: float = Field(ge=0, le=1)   # D-0102 2-C — 정규화 기준 = 처리 전 피크^(1−k) × 처리 후 피크^k


class AudioRules(_Strict):
    bed_gain: float
    duck_depth: float
    duck_pre_sec: float
    duck_post_sec: float
    duck_smooth_sec: float
    narration_peak: float
    master_peak: float
    loudnorm: Loudnorm
    post_limiter_dbfs: float = Field(lt=0)   # 2패스 loudnorm 뒤 샘플 피크 리미터(AAC 트루 피크 초과 방지, RENDER-AP-004)
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
    bed_bass: BedBass
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
    empty_exempt: list[Literal["article_press_lead"]] = Field(default_factory=list)   # v5.1.0 D-0127 §5 — 검수 empty 제외 구간
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


class AnimaticFlatMap(_Strict):
    """막지도 — 육지·바다 단색 + 경계선(타일·지형·라벨 없음). data = 저장소 추적 자료(tools/build_flat_map.py)."""

    data: str
    sea: Color4
    land: Color4
    border: Color4
    border_w: float = Field(gt=0)


class AnimaticPlaceholder(_Strict):
    """자리표시 상자 — 요소와 같은 자리·크기·타이밍, 안에 `[종류: 이름]` 글자."""

    fill: Color4
    stroke: Color4
    stroke_w: float = Field(gt=0)
    dash: list[float]
    text: Color4
    font: str
    size: float = Field(gt=0)
    line_gap: float = Field(gt=0)
    max_chars: int = Field(ge=8)
    cutout_h_ratio: float = Field(gt=0)            # 컷아웃 높이 ÷ 폭(레지스트리에 비율 없음 — 근사)
    panel_box: tuple[float, float, float, float]   # 패널 자리표시 상자(설계 px x0, y0, x1, y1) — 패널 본문이 덮는 화면 영역
    kinds: dict[str, str]   # 요소 종류 → 화면 이름(뱃지·국기·휘장·사진…). 목록 밖 종류 = 오류


class AnimaticBand(_Strict):
    """화면 위 가운데 얇은 띠(모서리는 날짜만 규칙 유지)."""

    text: str
    font: str
    size: float = Field(gt=0)
    h: float = Field(gt=0)
    pad_x: float = Field(ge=0)
    baseline: float = Field(gt=0)
    bg: Color4
    fg: Color4


class AnimaticRules(_Strict):
    """v4.9.0 back_and_forth D-0108(사용자 결정 D97) — 콘티 판(animatic). 전편 렌더 경로는 이 블록을 읽지 않는다."""

    profile: str                       # config engine.output 프로파일(480p). fps 는 설계 fps 그대로
    output: str                        # out/ 아래 파일 이름
    preset: str                        # x264 preset(콘티 판 인코딩만)
    mp4_comment: str                   # mp4 메타데이터 표식 — deliver(engine.mux)가 보면 거부
    flat_map: AnimaticFlatMap
    placeholder: AnimaticPlaceholder
    band: AnimaticBand
    missing_license: str               # 권리 레지스트리(생성 자산)가 없는 환경의 엔딩 카드 license_ref 자리 문구(전편은 오류 그대로)
    checks_skip: list[str] = Field(min_length=1)   # 콘티 판에서 건너뛰는 checks id(provenance animatic.checks_skipped)
    cost_target_sec_per_300s: float = Field(gt=0)   # 5분 영상 콘티 판 목표 시간(4코어, run_log 실측과 비교)


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
    change_regime_months: int = Field(ge=1)   # v4.4.0 D-0091 ②


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


class TimelineBand(_Strict):
    """v4.4.0 D-0090 작업 2 — series band(목표 범위 띠)."""

    fill_alpha: float = Field(gt=0, le=1)
    edge_alpha: float = Field(gt=0, le=1)
    edge_w: float = Field(gt=0)
    sep: str = Field(min_length=1)


class TimelineAxisScale(_Strict):
    """v5.1.0 D-0121 §A(사용자 피드백 D105) — 시간축 축 스케일(카메라 w) 고정. checks timeline_rescale(hard)·provenance timeline.w_changes[].
    grammar 의 {max}·{ratio} 는 같은 블록 값(프롬프트 {{RULES.stage_timeline.axis_scale}})."""

    w_changes_per_video_max: int = Field(ge=0)
    w_change_ratio_min: float = Field(gt=1)
    scene_fixed: bool
    grammar: str = Field(pattern=r"\{max\}")


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
    band: TimelineBand             # v4.4.0 — D-0090 작업 2
    missing_mark: TimelineMissingMark
    axis_scale: TimelineAxisScale  # v5.1.0 — D-0121 §A


class StageBackdropRules(_Strict):
    """v5.1.0 D-0121 §B·D-0123 §1 — 사진 배경 무대·backdrop 이벤트 토큰(engine/stage_backdrop.py·engine/layers/backdrop.py)."""

    kind: Literal["photo"]
    blur_px: float = Field(gt=0)
    dim: float = Field(ge=0, le=1)
    desaturate: float = Field(ge=0, le=1)
    crossfade_sec: float = Field(gt=0)
    ken_burns: float = Field(ge=0)
    change_on: Literal["scene"]
    min_photos: int = Field(ge=1)
    max_photos: int = Field(ge=1)
    bg_rgb: tuple[float, float, float]
    grammar: list[str] = Field(min_length=1)   # 연출·수정 프롬프트 {{RULES.backdrop_island}}

    @model_validator(mode="after")
    def _range(self) -> "StageBackdropRules":
        if self.max_photos < self.min_photos:
            raise ValueError("stage_backdrop.max_photos < min_photos")
        return self


class IslandChart(_Strict):
    pad_top: float = Field(ge=0)
    pad_bottom: float = Field(ge=0)
    label_flip_pad: float = Field(ge=0)   # v5.2.0 D-0133 §1 — 아일랜드 마커 라벨 ↔ 상자 가장자리 여백(넘으면 반대쪽, 그래도 넘으면 클램프)


class CascadeFrontRules(_Strict):
    w: float
    h: float
    pad_x: float
    date_dx: float
    date_dy: float
    title_dy: float
    line_dy: float
    date_size: float
    title_size: float
    line_size: float
    accent_w: float


class CascadeRules(_Strict):
    """v5.2.0 겹침 카드(cascade — 사용자 재구성 2026-10-01, 시안). 설계 px(480p). 상자 모양은 rules island 재사용.
    최악 폭 (max_back + 1) × step + front.w ≤ width_cap 을 여기서 검증하고, 실제 폭은 checks cascade 가 잰다."""

    status: Literal["prototype", "adopted"]
    x0: float
    y: float
    step: float
    flag_R: float
    front: CascadeFrontRules
    back_scale: float = Field(gt=0, lt=1)
    back_text_alpha: float = Field(gt=0, le=1)
    back_fade_px: float = Field(ge=0)      # D-0138 — 덮이는 경계 글자 알파 그라데이션 폭
    back_dy: float = Field(ge=0)           # D-0138 — 층마다 내려앉음
    back_dim: float = Field(ge=0, lt=1)    # D-0138 — 층마다 어두워짐
    max_back: int = Field(ge=1)
    focus_sec: float = Field(gt=0)
    shift_sec: float = Field(gt=0)
    width_cap: float

    @model_validator(mode="after")
    def _fits(self) -> "CascadeRules":
        need = (self.max_back + 1) * self.step + self.front.w
        if need > self.width_cap:
            raise ValueError(f"cascade: (max_back+1)×step+front.w = {need} > width_cap {self.width_cap}")
        if self.step >= self.front.w * self.back_scale:
            raise ValueError("cascade: step 이 뒤 카드 폭 이상이면 겹치지 않는다")
        return self


class IslandRules(_Strict):
    """v5.1.0 D-0123 §1·D-0126 — backdrop 무대 위 아일랜드 공통 규칙(engine/island.py)."""

    radius: float = Field(ge=0)
    fill_alpha: float = Field(ge=0, le=1)
    edge_alpha: float = Field(ge=0, le=1)
    edge_w: float = Field(gt=0)
    shadow: list[tuple[float, float]]
    max_concurrent: int = Field(ge=1)
    boxes: dict[str, tuple[float, float, float, float]] = Field(min_length=1)
    panel_box: tuple[float, float, float, float]
    chart: IslandChart
    main_required: bool                  # v5.2.0 D-0129 §B — backdrop 무대에 주 아일랜드 상시(checks backdrop_main_missing)
    main_kinds: list[Literal["chart", "primitive", "photo", "clip", "article", "panel"]] = Field(min_length=1)
    card_only_max_sec: float = Field(gt=0)   # 주 아일랜드 없는 구간 상한(전환 허용)

    @model_validator(mode="after")
    def _same_h(self) -> "IslandRules":
        if len({b[3] for b in self.boxes.values()}) != 1:
            raise ValueError("island.boxes 높이는 모두 같아야 한다(차트 레인 영역 한 벌, D-0126 Q2)")
        return self


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
    frequencies: list[Literal["monthly", "release"]] = Field(min_length=1)   # release = v4.4.0 scatter
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


class DotPlotLayout(_Strict):
    """v4.4.0 D-0090 작업 3 — dot_plot 레이아웃 토큰(설계 px)."""

    w: float = Field(gt=0)
    plot_h: float = Field(gt=0)
    pad_x: float
    pad_top: float
    head_gap: float
    plot_gap: float
    col_label_gap: float
    src_gap: float
    pad_bottom: float
    axis_w: float
    tick_step: float = Field(gt=0)
    tick_label_every: int = Field(ge=1)
    tick_label_dx: float
    legend_rise: float
    dot_r: float = Field(gt=0)
    dot_gap: float = Field(ge=0)
    dot_color: str
    dot_alpha: float = Field(gt=0, le=1)
    median_color: str
    median_w: float
    median_half: float
    median_size: float
    grid_alpha: float
    tick_size: float
    col_size: float
    tag_size: float
    tag_spacing: float
    note_size: float
    note: str = Field(min_length=1)
    median_label: str = Field(min_length=1)
    radius: float
    bar_w: float
    bar_inset: float
    fade_sec: float = Field(ge=0.4, le=0.6)
    slide_px: float
    dot_stagger_sec: float = Field(ge=0)


class SiteDiagramLayout(_Strict):
    """v4.4.0 dmz_mine_2026 — site_diagram(사건 현장 개념도, 벡터) 레이아웃 토큰(설계 px·비율)."""

    x: float
    y: float
    w: float = Field(gt=0)
    h: float = Field(gt=0)
    radius: float
    fade_sec: float = Field(ge=0.4, le=0.6)
    scale_from: float = Field(gt=0, le=1)
    north_bg: str
    south_bg: str
    foot_bg: str
    foot_h: float
    mdl_v: float = Field(gt=0, lt=1)
    nll_v: float = Field(ge=0, lt=1)
    sll_v: float = Field(gt=0, lt=1)
    wave_amp_a: float
    wave_len_a: float = Field(gt=0)
    wave_amp_b: float
    wave_len_b: float = Field(gt=0)
    wave_step: float = Field(gt=0)
    mdl_w: float
    limit_w: float
    limit_dash: list[float]
    limit_alpha: float
    site_u: float
    site_dy: float
    site_r: float
    site_ring_r: float
    bracket_du: float
    bracket_half: float
    bracket_w: float
    dist_dx: float
    dist_dy: float
    dist_size: float
    dist_src_size: float
    dist_src_gap: float
    leader_w: float
    leader_alpha: float
    burst_offsets: list[tuple[float, float]] = Field(min_length=1)
    burst_r: float
    burst_inner: float
    burst_points: int = Field(ge=3)
    burst_rim: str
    pop_sec: float = Field(gt=0)
    pop_from: float = Field(ge=1)
    flash_r: float
    flash_sec: float = Field(gt=0)
    mine_offset: tuple[float, float]
    mine_w: float
    mine_h: float
    mine_color: str
    left_x_u: float
    right_x_u: float
    label_v: float
    row_h: float
    label_size: float
    label_fade_sec: float = Field(gt=0)
    limit_label_size: float
    mdl_label_size: float
    side_size: float
    header_size: float
    header_dy: float
    width_note_size: float
    width_note_v: float
    foot_size: float
    pad_x: float


class PrimitivesRules(_Strict):
    """v4.2.0 D-0081 작업 4 — 프리미티브별 레이아웃 토큰(engine.style.PRIMITIVES). 요소가 등록될 때 필드를 더한다."""

    statement_diff: Optional[StatementDiffLayout] = None
    dot_plot: Optional[DotPlotLayout] = None   # v4.4.0 D-0090 작업 3
    site_diagram: Optional[SiteDiagramLayout] = None   # v4.4.0 dmz_mine_2026 사용자 요청(현장 개념도)


class VideoRules(_Strict):
    """`rules/video_rules.yaml` 최상위 모델."""

    schema_version: int
    rules_version: str
    banned_phrases: BannedPhrases
    balance_principles: list[str]
    direction_grammar: list[str] = Field(min_length=1)   # v4.7.0 D-0104 D2(a) — 연출 문법(프롬프트 {{RULES.direction_grammar}})
    script_schema: ScriptSchemaRules
    verification: VerificationRules   # v3.2.0 — D-0052(D50)
    tts_rules: TTSRules
    tts_risk: TTSRisk             # v3.0.0 — D-0040 작업 8
    pronounce: PronounceRules     # v3.0.0 — D-0040 작업 8
    placement: PlacementRules     # v3.1.0 — D-0047 작업 5
    shot_grammar: ShotGrammar
    pacing: PacingRules            # v4.11.0 — D-0118 §1 정적 구간
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
    animatic: AnimaticRules        # v4.9.0 — D-0108 콘티 판
    golden: GoldenRules            # v3.6.0 — D-0066 작업 4
    camera: CameraRules            # v3.3.0 — D-0056 작업 2
    stage: StageRules              # v4.1.0 — D-0076 작업 5
    qa_checks: QAChecks
    primitives: PrimitivesRules = Field(default_factory=PrimitivesRules)   # v4.2.0 D-0081
    stage_timeline: StageTimelineRules   # v4.3.0 — D-0084 작업 3·D-0085
    stage_backdrop: StageBackdropRules   # v5.1.0 — D-0121 §B·D-0123
    island: IslandRules                  # v5.1.0 — D-0123 §1·D-0126
    cascade: CascadeRules                # v5.2.0 — 겹침 카드(사용자 재구성 2026-10-01, 시안)
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
        bad = sorted(set(self.pacing.static_window.change_kinds) - set(self.registries.event_types) - {"camera"})
        if bad:
            raise ValueError(f"pacing.static_window.change_kinds 가 registries.event_types(+camera) 에 없다: {bad}")
        bad = sorted(set(self.genre_prompt.stage_grammar) - set(self.registries.stages))
        if bad:
            raise ValueError(f"genre_prompt.stage_grammar 의 무대가 registries.stages 에 없다: {bad}")
        bad = sorted(f"{n}→{st}" for n, sl in self.placement.slots.items() for st in (sl.stages or []) if st not in self.registries.stages)
        if bad:
            raise ValueError(f"placement.slots 의 stages 가 registries.stages 에 없다: {bad}")   # v5.2.0 D-0132
        a, b = set(self.camera.framing.context_w_min), set(self.shot_grammar.w_guide)
        if a != b:
            raise ValueError(f"camera.framing.context_w_min 키가 shot_grammar.w_guide 와 다르다 — 누락 {sorted(b - a)} · 초과 {sorted(a - b)}")
        return self
