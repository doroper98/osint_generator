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
RGB = tuple[float, float, float]
Range2 = tuple[float, float]


class BannedPhrases(_Strict):
    patterns: list[str]
    candidates: list[str]
    defect_classes: list[str]
    examples: list[str] = []   # v7.4.0 UF-145 — 사용자가 든 금지 예문(patterns 가 전부 잡아야 한다 — 테스트)


class OpeningRules(_Strict):
    """v5.6.0 RENDER-AP-016 — 지도 영상 오프닝: 넓은 지도에서 대상 지역으로 천천히 들어간다."""

    min_w: float = Field(gt=0)          # 첫 카메라 폭(경도 °) 하한
    max_sec: float = Field(gt=0)        # 이 시간 안에 들어간다
    min_zoom: float = Field(gt=1)       # 첫 폭 ÷ 들어간 폭 하한
    min_move_sec: float = Field(gt=0)   # 들어가는 이동 시간 하한("천천히")


class WeaponPhotoRules(_Strict):
    """v5.6.0 RENDER-AP-017 — 무기체계 이름이 나오는 문장엔 실사 사진(경고)."""

    terms: list[str] = Field(min_length=1)


class RouteFrame(_Strict):
    """v5.6.0 RENDER-AP-012 — 경로 곡선 프레임 검사."""

    max_out: float = Field(default=0.25, ge=0, le=1)   # 다 그려진 경로 곡선 중 화면 밖 비율 상한


class SourceNote(_Strict):
    """v5.6.0 참조 출처 화면 표기(사용자 결정 2026-10-04) — 내레이션 대신 문장 동안 화면 아래 작은 링크."""

    publishers: list[str] = Field(min_length=1)
    x: float = Field(ge=0)
    y_from_bottom: float = Field(ge=0)
    alpha: float = Field(gt=0, le=1)
    prefix: str
    spoken_names: list[str] = Field(min_length=1)   # 내레이션에 나오면 린트 reference-in-narration 오류


class ScriptGrammar(_Strict):
    """v5.5.0 원고 서술 규약(사용자 결정 2026-10-02) — 프롬프트 줄 + 린트 값(엇갈린 수치·미확인 서술 금지, 문장 흐름 연결어)."""

    lines: list[str] = Field(min_length=1)
    connectives: list[str] = Field(min_length=1)
    connective_min_ratio: float = Field(ge=0, le=1)
    connective_max_ratio: float = Field(ge=0, le=1)
    uncertain_patterns: list[str] = Field(min_length=1)
    lint_waivable: list[str] = Field(min_length=1)   # v5.17.0 D-0168 — 프로젝트 면제 목록에 올릴 수 있는 린트 kind(문체·흐름만)


class ScriptVocab(_Strict):
    """v7.4.0 D-0229 §2.8(UF-108·UF-114) — 원고 어휘 린트 값."""

    hit_verbs: list[str] = Field(min_length=1)          # '맞히다' 활용 — 이동 표적에만
    fixed_targets: list[str] = Field(min_length=1)      # 고정 시설 명사 → [verb-target-mismatch] 오류(타격했다·때렸다)
    moving_targets: list[str] = Field(min_length=1)     # 이동 표적 명사(있으면 허용)
    contrast_heads: list[str] = Field(min_length=1)     # 대조 접속어 문장 머리
    statement_verbs: list[str] = Field(min_length=1)    # 앞 문장이 발표·주장이면 [contrast-conjunction] 경고
    contrast_hint: str = Field(min_length=1)


class TempoRules(_Strict):
    """v7.4.0 D-0229 §2.9(UF-104·UF-115 "호흡을 천천히, 막전 막후 설명을 충실히") — 템포·막 구조."""

    fact_sentences_per_min_max: int = Field(gt=0)   # 1분 창 안 사실(출처 귀속) 문장 상한 — 넘으면 warning [tempo-density]
    act_intro_min: int = Field(ge=0)                # 막(kind act)마다 role intro(+bridge) 문장 하한 — 미만 [act-frame] 오류
    act_outro_min: int = Field(ge=0)                # 막마다 role outro 문장 하한
    sentence_gap_sec: float = Field(gt=0)           # order.yaml tempo: breath 인 프로젝트의 문장 간격(그 밖 = layout_480p.timeline_gaps.gap_sec — 골든 불변)


class TransitionRules(_Strict):
    """v7.4.0 D-0229 §2.2(UF-105) — 시점(시간·무대) 전환 장치. 원고 bridge 문장 + 호흡 + 느린 카메라 + 날짜 배지 xfade."""

    bridge_pause_sec: float = Field(gt=0)        # bridge 문장 앞 내레이션 공백(음악만) — script.timeline.layout 이 넣는다
    camera_move_min_sec: float = Field(gt=0)     # 무대·시대 점프 지점 카메라 이동 하한(checks transition-camera)
    date_badge_xfade_sec: float = Field(gt=0)    # bridge 문장에서 날짜 배지를 옛 날짜 → 새 날짜로 교차 페이드
    jump_days: int = Field(gt=0)                 # 이웃 장면 대표 날짜(문장 날짜 중앙값) 차가 이 이상이면 시점 전환(D-0230 B)
    in_scene_jump_days: int = Field(gt=0)        # 장면 안 문장 날짜가 장면 중앙값과 이 이상 차이 나면 warning [transition-in-scene](role background 제외)
    # v7.4.0 D-0325(UF-159) — 요소 등장·퇴장(×1.5). element = 종류별 [in, out], element_motion = 등장 움직임 길이
    element_fade_min_sec: float = Field(gt=0)
    element_fade_exempt: dict[str, str] = Field(default_factory=dict)
    element: dict[str, tuple[float, float]]
    element_motion: dict[str, float]


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
    # v7.4.0 D-0233(UF-117, D243) — 보도 귀속 방식. credits = 보도·보고서 출처는 엔딩 크레딧 장면별 '보도 출처'로(자막·내레이션은 평서),
    # 귀속을 남기는 것 = 당사자 발언(claim_kind statement)·논쟁 수치(status disputed)·분석·추정·전망. narration = 옛 방식(문장마다 귀속).
    # 프로젝트 order.yaml attribution_mode 가 정한다. 없으면 원고 날짜 ≥ attribution_credits_since 면 attribution_mode, 아니면 narration(옛 원고·골든 불변)
    attribution_mode: Literal["credits", "narration"] = "narration"
    attribution_credits_since: Optional[str] = None
    press_markers: list[str] = Field(default_factory=list)   # credits 모드에서 자막에 남으면 [press-attribution] 경고
    press_relay_verbs: list[str] = Field(default_factory=list)   # v7.4.0 D-0234 — 당사자 발언 문장의 매체 접두 판정(발언 동사)

    @model_validator(mode="after")
    def _label_keys(self) -> "ScriptSchemaRules":
        if set(self.labels) != set(self.label_strength_order) or len(self.label_strength_order) != len(set(self.label_strength_order)):
            raise ValueError("script_schema.labels 키와 label_strength_order 가 같은 집합이어야 한다")
        return self


class AlignGateRules(_Strict):
    """v5.16.0 D-0165 — 정렬 게이트 기준(절대 시각·간격 일치 공통, ms)."""

    median_ms: float = Field(gt=0)
    p90_ms: float = Field(gt=0)


class ForcedAlignRules(_Strict):
    """v5.16.0 — 강제 정렬 신뢰도 문턱(문장 점수 = 어절 토큰 확률 평균의 평균)과 게이트 참값 정의(D-0165 §2·§3)."""

    min_score: float = Field(ge=0, le=1)
    silence_thr: float = Field(gt=0, lt=1)        # 무음 진폭 문턱(trim 과 같은 값)
    silence_sec: float = Field(gt=0)              # 이 길이 이상 이어진 무음 뒤 첫 문턱 초과 = 발화 시작(참값)
    match_window_sec: float = Field(gt=0)         # 참값 ↔ 정렬 어절 대응 창(±). 대응 없음 = 이 값으로 실패 계상
    gate: AlignGateRules


class OctaveCleanRules(_Strict):
    """v5.20.2 D-0180 §3 — 끝 억양 구간의 추적기 옥타브 오류 정리(게이트 프레임 중앙값 기준 /2·×2)."""

    enabled: bool
    ratio_hi: float = Field(gt=1)
    ratio_lo: float = Field(gt=0, lt=1)
    gate_db: float = Field(lt=0)               # 문장 피크 대비 RMS 문턱(들리는 프레임)
    rms_ms: float = Field(gt=0)                # RMS 창
    record_frames: int = Field(ge=1)           # 기록 f0 = 게이트 프레임 첫/마지막 n 개 중앙값


class FinalFallRules(_Strict):
    """v5.20.0 D-0175 — 문장 끝 억양 보정(사용자 결정 D169 시안 C). 값의 정본은 rules tts_rules.prosody.final_fall."""

    enabled: bool
    suffix: str = Field(min_length=1)          # 발음 텍스트가 이것(+문장부호)으로 끝날 때만
    span_chars: int = Field(ge=1)              # 끝에서 몇 글자 구간(습니다 = 3)
    semitones: float = Field(gt=0)             # 구간 끝까지 선형으로 내리는 반음
    pre_sec: float = Field(ge=0)               # 구간 첫 글자 시작보다 이만큼 앞에서
    crossfade_sec: float = Field(gt=0)         # 원음 → 합성음 전환
    f0_floor_hz: float = Field(gt=0)
    f0_ceil_hz: float = Field(gt=0)
    frame_ms: float = Field(gt=0)
    octave_clean: OctaveCleanRules             # v5.20.2 D-0180 §3


class ProsodyRules(_Strict):
    final_fall: FinalFallRules


class ShortKeyBoundary(_Strict):
    """v7.4.0 D-0246 보충 — 한글 짧은 사전 키(≤ max_len 음절)는 어절 경계(앞 글자가 한글 음절 아님) 또는 수사 음절 뒤에서만 치환."""

    max_len: int = Field(ge=1)
    allow_after: str = ""


class TensificationTraps(_Strict):
    """v7.4.0 D-0246(UF-127) — '…유 + 조사' 가 발음 사전 "유가"(油價) 치환에 걸리지 않게 하는 예외 항목의 원천(합성 직전 사전에 생성)."""

    suffix_nouns: list[str] = Field(min_length=1)
    particles: list[str] = Field(min_length=1)
    spoken: str = "{noun}{particle}"


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
    forced_align: "ForcedAlignRules"   # v5.16.0 D-0164 §5
    prosody: "ProsodyRules"   # v5.20.0 D-0175 — 문장 끝 억양 보정
    letter_names: list[str] = Field(default_factory=list)       # v5.6.0 TTS-AP-075 — 알파벳 글자 이름(한글). 등재 약어·사전 값의 글자 연속만 합성 직전 띄운다
    acronyms: list["Acronym"] = Field(default_factory=list)      # v5.6.0 사용자 결정 2026-10-04 — 약어 읽기 등재(린트 tts-acronym)
    tensification_traps: Optional[TensificationTraps] = None    # v7.4.0 D-0246(UF-127) — 발음 사전 '…유가' 예외 항목 원천
    short_key_boundary: Optional[ShortKeyBoundary] = None       # v7.4.0 D-0246 보충 — 짧은 사전 키 낱말 경계


class Acronym(_Strict):
    """약어 읽기(v5.6.0 사용자 결정 2026-10-04). read=letters: 글자 이름으로("AFP 통신" → 에이 에프 피 통신),
    letters_and_name: 글자 이름 + 국문 명칭("CSIS" → 씨 에스 아이 에스, 전략국제문제연구소 — 국내 뉴스처럼 둘 다 읽는 기관)."""

    abbr: str
    letters: str
    name: str = ""
    read: Literal["letters", "letters_and_name"]


class TTSRiskPattern(_Strict):
    kind: str
    regex: str
    hint: str
    ignore_case: bool = False


class TTSRisk(_Strict):
    """v3.0.0 — 옛 orchestrator/tts_lint 패턴(D-0040 작업 8). 발음 텍스트 경고."""

    covered_before_roman: list[str]
    patterns: list[TTSRiskPattern]
    # v5.3.0 TTS-AP-071~073 — 사전 적용 **뒤** 실제 합성 문자열(pronounce_tts)에서 보는 패턴. 사전이 고친 것은 경고하지 않는다
    spoken_patterns: list[TTSRiskPattern] = Field(default_factory=list)


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
    frame: bool = False   # v7.4.0 D-0274 §2① — 클립 액자(캡션 줄은 상자 안 위쪽 띠, 상자 = 16:9 본체만)

    @model_validator(mode="after")
    def _one(self) -> "PlacementSlot":
        is_card = "card" in self.model_fields_set
        if sum([self.box is not None, self.point is not None, is_card, self.beside_panel is not None, bool(self.screen)]) != 1:
            raise ValueError("슬롯은 box·point·card·beside_panel·screen 중 하나")   # align(옛 기사 가운데)은 v5.1.0 D-0121 §C 에서 삭제(P2)
        return self


class CenterMedia(_Strict):
    """v7.4.0 back_and_forth D-0306 §1.4(UF-148) — 구석 카드가 사라진 지도 무대에서 사진은 가운데 큰 자리로. 동시에 둘이면 좌우 2분할."""

    stage: str
    kinds: list[str] = Field(min_length=1)
    from_slots: list[str]          # 이 슬롯(구석 지도 자리·자동 자리)을 가운데로 바꾼다
    single: str
    pair: tuple[str, str]


class PlacementRules(_Strict):
    auto_media: dict[str, dict[str, str]]    # 종류 → {map|panel → 슬롯}
    stage_slots: dict[str, dict[str, str]] = Field(default_factory=dict)   # v4.4.0 D-0093 — 무대 → {이벤트 종류 → 슬롯}
    slots: dict[str, PlacementSlot]
    center_media: Optional[CenterMedia] = None   # v7.4.0 D-0306 §1.4

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


class CameraSpeedRules(_Strict):
    """v6.0.2 UF-97 D-0216 — 카메라 속도 상한. pan = 화면 중심 이동(화면 폭/초), zoom = |d ln w/dt|(/초). opening_* = 제목 카드 전."""

    max_pan_w_per_sec: float = Field(gt=0)
    max_zoom_per_sec: float = Field(gt=0)
    opening_max_pan_w_per_sec: float = Field(gt=0)
    opening_max_zoom_per_sec: float = Field(gt=0)
    stages: dict[str, list[Literal["pan", "zoom"]]]   # v7.0.1 D-0218 — 무대마다 재는 성분(없는 무대 = 검사 안 함)


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
    camera_speed: "CameraSpeedRules"   # v6.0.2 UF-97 D-0216 — 카메라 속도 상한(hard camera_speed)
    max_consecutive_move_sentences: int = Field(ge=1)   # v5.22.4 UF-19(C0 "문장마다 카메라 이동" 금지) — 이 수만큼 연속 문장이 모두 이동을 시작하면 camera_per_sentence hard
    move_ease: Literal["cubic", "quintic"]   # v5.21.9 D-0191 §1-1 — 카메라 이동 이징(cubic = 조각 3차, 중간 가속도 뒤집힘)
    move_path: Literal["linear", "fixed_point"] = "linear"   # v5.5.0 — 이동+줌 경로(fixed_point = 한 고정점 기준 줌, 지도 흐름이 직선)


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
    clip_show_sec: dict[Literal["main", "broll"], Range2]   # v7.4.0 D-0274 §2② — clip.role 별
    file_photo_label_required: bool
    caption_credit_required: bool
    ai_generated_forbidden: bool
    casualty_identifiable_forbidden: bool
    credit_formats: dict[str, str]           # v2.5.5 — 화면 출처 줄(레지스트리 필드로만 조립, D-0036 작업 3)
    triggers: dict[str, list[str]]           # v2.5.5 — 14 §10.2 트리거 → 형태 제안(제안만, P8)
    caption_bar_px: float                    # 사진·영상 캡션 바 높이(14 §4.1) — 배치 점검용
    registry: str                            # v2.5.5 — 미디어 레지스트리 경로(저장소 기준)
    sources_order: list["PhotoSourcePool"] = Field(min_length=1)   # v5.19.0 D-0163 §2 — 사진 소싱 풀 순서(media_fetch search)
    min_density_per_min: float = Field(gt=0)   # v7.4.0 D-0261(UF-139) — [media-density] hard: (photo+clip+cutout 이벤트) ÷ 영상 분 하한, 사유 통과 없음
    sources_excluded_licenses: list[str] = Field(default_factory=list)   # 라이선스 이름 조각(NC·ND) — 있으면 탈락
    sources_excluded_mimes: list[str] = Field(default_factory=list)      # v5.21.0 — 문서·도식 mime(pdf·svg) — 통과 수 밖
    inset_preferred_license: str = ""   # v7.4.0 D-0240 후속 — 위성 인셋 기본 라이선스 접두(그 밖은 fallback_reason 필수)
    inset_licenses: dict[str, "InsetLicense"] = Field(default_factory=dict)   # v7.3.0 D232 U1·D234 — 위성 인셋 라이선스 허용 목록


class InsetLicense(_Strict):
    private_only: bool   # 비공개 시청 한정(사용자 결정 D234) — 레지스트리 scope: private_only 필수


class PhotoSourcePool(_Strict):
    """v5.19.0 D-0163 §2 — 사진 소싱 풀 하나. via commons = Commons 검색 + query_suffix, manual = 안내 줄(hint)만."""

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    via: Literal["commons", "manual"]
    query_suffix: str = ""
    hint: str = ""

    @model_validator(mode="after")
    def _hint(self) -> "PhotoSourcePool":
        if self.via == "manual" and not self.hint:
            raise ValueError(f"사진 풀 {self.id}: manual 은 hint(사람 확인 방법)가 필요하다")
        return self


class MediaDensity(_Strict):
    """14 §10.1 밀도 (v2.5.5, D-0037·D38). 모두 경고(오류 아님)."""

    per_item_sec: Range2                  # 전체 러닝타임 ÷ 개수
    per_scene_max: int
    scene_exempt_kinds: list[str]         # 장면당 개수에서 뺀다(기사 카드 = 일반 카드 자리 대체)
    no_same_kind_adjacent_scenes: bool
    window_sec: float                     # 짧은 구간 몰림 창
    window_max: int                       # 창 안 최대 개수 — 넘으면 경고
    window_exempt_kinds: list[str]
    total_exempt_kinds: list[str]         # v5.19.0 D-0163 §2 — [media-density-total] 개수에서 뺀다(기사 = 분당 상한 따로)
    article_per_min_max: int = Field(ge=1)    # 기사 카드 후보 문장에 쓰는 기사 카드 — 60초 구간당 상한
    photo_target_per_min: float = Field(ge=0)   # 사진 목표(분당) — 미달이면 미디어 계획 표가 문장 단위 사유 요구
    inset_show_sec: Range2                      # v7.3.0 D232 U2 — 위성 인셋
    inset_per_scene_max: int = Field(ge=1)
    inset_min_gap_sec: float = Field(ge=0)
    grammar: list[str] = Field(min_length=1)    # 연출 프롬프트 {{RULES.media.density}} 문구({자리} = 이 블록 값)


class FlickrRules(_Strict):
    """v4.4.0 D-0090 작업 4 — 기관 공식 Flickr 사진 받기(tools/media_fetch)."""

    licenses_allowed: dict[str, str] = Field(min_length=1)
    size_suffix: str = Field(min_length=1)


class MediaRules(_Strict):
    density: MediaDensity
    flickr: Optional[FlickrRules] = None   # v4.4.0
    file_clip_date_gap_days: int = Field(default=30, gt=0)   # v7.4.0 D-0283 §1 — [clip-date-mismatch] 촬영일 ↔ 문장 날짜 차 상한(자료 표기 없을 때)


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
    date_badge_over_clip_frame: bool = False   # v7.4.0 D-0276 — 클립 액자 위에 날짜 뱃지(그 슬롯과의 교차만 예외)


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
    over_clip_frame: bool = False   # v7.4.0 D-0276 — 클립 액자 위에 자막(그 슬롯과의 교차만 예외)


class TitleCardLayout(_Strict):
    dur_sec: float
    title_size: float
    subtitle_size: float
    rule_w: float
    max_w_ratio: float = Field(gt=0, le=1)   # v5.21.3 — 제목 최대 폭(화면 폭 비율)
    title_min_size: float = Field(gt=0)      # v5.21.3 — 줄여도 이 크기 미만이면 TitleOverflowError(조용한 잘림 금지, P6)


class EndCardNotice(_Strict):
    """v4.5.0 D85 — 엔딩 카드 맨 마지막 줄 검증 안내(가장 작은 글씨 한 줄). template 의 `{n}` = 라벨 문장 수."""

    size: float = Field(gt=0)
    dy: float = Field(gt=0)
    template: str = Field(pattern=r"\{n\}")


class EndCardInvestNotice(_Strict):
    """v7.4.0 D-0278 §4.3 — 투자 고지 고정 문구(장르 invest_notice 일 때 맨 마지막 줄)."""

    size: float = Field(gt=0)
    text: str = Field(min_length=1)


class EndCardTemplateLine(_Strict):
    """v7.4.0 UF-147(D-0302 ⑤) — 템플릿 표시 줄(엔딩 카드 머리 줄 오른쪽 · 타이틀 부제 앞)."""

    size: float = Field(gt=0)
    y: float = Field(gt=0)
    font: str
    sep: str = Field(min_length=1)


class EndCardVersionStamp(_Strict):
    """v5.1.0 D-0124(사용자 결정 D109) — 엔딩 카드 오른쪽 아래 구석 버전 도장. 문자열 = "v" + VERSION 파일(렌더 시점, P3).
    notice_unverified 와 겹치면 notice 를 우선하고 도장을 dy 만큼 위로 올린다."""

    x_from_right: float = Field(ge=0)
    y_from_bottom: float = Field(ge=0)
    size: float = Field(gt=0)
    font: str
    alpha: float = Field(gt=0, le=1)
    dy: float = Field(gt=0)


class EndCardTemplateLine(_Strict):
    """v7.4.0 UF-147(D-0302 ⑤) — 템플릿 표시 줄(엔딩 카드 머리 줄 오른쪽 · 타이틀 부제 앞)."""

    size: float = Field(gt=0)
    y: float = Field(gt=0)
    font: str
    sep: str = Field(min_length=1)


class EndCardLayout(_Strict):
    dur_sec: float
    item_size: float
    license_size: float
    template_line: EndCardTemplateLine      # v7.4.0 UF-147
    notice_unverified: EndCardNotice
    notice_invest: EndCardInvestNotice      # v7.4.0 D-0278 §4.3
    template_line: EndCardTemplateLine      # v7.4.0 UF-147
    version_stamp: EndCardVersionStamp
    bottom_margin: float = Field(ge=0)   # v4.5.0 D-0098 — 크레딧 마지막 기준선과 하단 구분선(H−44) 사이 최소 여백
    hold_black_after: bool = True        # v4.4.0 dmz_mine_2026(v4.7.0 병합) — 카드 뒤 검정 유지(지도가 다시 드러나지 않게)
    after_max_luma: float = Field(gt=0, le=1)   # v5.22.3 UF-35 — 카드 퇴장 뒤~영상 끝 프레임 평균 밝기 상한(endcard_black hard)
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
    vline_dash: list[float] = Field(default_factory=lambda: [3.0, 3.0])   # v7.4.0 D-0309 §1-5
    vline_w: float = 1.1
    vline_alpha: float = 0.7


class RouteLabelLayout(_Strict):
    route_size: float
    barrier_size: float
    # v5.21.11 D-0191 §1-3·D-0192 — 경로 라벨 자리: 선에서 수직으로 line_gap 만큼 띄운 상자, 곡선 위 place_fracs 순서로 시도.
    # 후보 0 = 옛 자리(가운데 점 위 legacy_dy) — 선·지명·뱃지와 안 걸리면 그대로(골든 보존)
    legacy_dy: float
    line_gap: float = Field(ge=0)          # 선 ↔ 글자 상자 최소 거리(px)
    line_clear_px: float = Field(ge=0)     # 교차 판정 여유(상자를 이만큼 넓혀 잰다)
    place_fracs: list[float] = Field(min_length=1)
    screen_pad: float = Field(ge=0)        # 화면 가장자리 여백
    bottom_pad: float = Field(ge=0)        # 화면 아래 여백(자막 구역)


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


class ArticlePressPhotoCredit(_Strict):
    """v7.4.0 D-0240 §3 — 공식 사진(A) 프레스 바탕의 자료사진 출처 줄(화면 왼쪽 아래, 자막 띠 위)."""

    size: float = Field(gt=0)
    y_above_subtitle: float = Field(ge=0)


class ArticlePressCredit(_Strict):
    """v5.21.0 D-0177 §3 — 보도 인용(B) 사진 카드 안 크레딧 줄(source 줄 아래)."""

    size: float = Field(gt=0)
    lead: float = Field(ge=0)
    format: str = Field(pattern=r"\{agency\}.*\{publisher\}")


class ArticleTitleSink(_Strict):
    """v6.0.2 D-0216 UF-98 — 제목 카드가 기사 카드 위에 뜰 때 기사 글자를 남기는 정도(불투명도 배수·블러 px, 설계 좌표)."""

    alpha: float = Field(gt=0, le=1)
    blur_px: float = Field(ge=0)


class ArticlePressFallback(_Strict):
    """v5.2.0 D-0129 §A — 프레스 사진이 없을 때 지금 무대를 흐리는 값(배경 사진 stage_backdrop 값과 분리 — hormuz 기사 골든 불변)."""

    blur_px: float = Field(gt=0)
    dim: float = Field(ge=0, le=1)
    max_luma: float = Field(gt=0, le=1)   # v5.21.12 D-0193 — 블러·dim 뒤 평균 밝기(Rec.709) 상한. 지도 테마와 무관하게 같은 어두운 무대


class ArticleCardLayout(_Strict):
    """v5.1.0 back_and_forth D-0121 §C — 기사 프레스 규약 v2(engine/layers/article.py 수치 전부). 옛 카드 조판 키는 삭제(P2)."""

    theme_default: Literal["dark", "light"]
    themes: dict[Literal["dark", "light"], ArticleTheme]
    press_lead_sec: float = Field(ge=0)
    title_sink: "ArticleTitleSink"   # v6.0.2 D-0216 UF-98 — 제목 카드 아래 기사 글자 가라앉힘
    press_fallback: ArticlePressFallback   # v5.2.0 D-0129 §A
    overlay_alpha: float = Field(gt=0, le=1)
    overlay_fade_sec: float = Field(gt=0)
    x_left_ratio: float = Field(gt=0, lt=1)
    max_w_ratio: float = Field(gt=0, le=1)
    rule: ArticleRule
    headline: ArticleHeadline
    sub: ArticleSub
    source: ArticleSource
    press_credit: ArticlePressCredit   # v5.21.0 D-0177
    press_photo_credit: Optional[ArticlePressPhotoCredit] = None   # v7.4.0 D-0240 §3 — 없으면 그리지 않는다(옛 규칙 파일)

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


class BadgePortrait(_Strict):
    """v5.15.0 인물 초상(가이드 23 §10) — R 단위. alpha_thr 는 배치용(정규화 알파 > 40 과 별개)."""

    width: float = Field(gt=0)
    min_width: float = Field(gt=0)        # v5.15.0 D-0159 — 머리 우선: 잘리면 width → min_width 사이로 줄인다
    alpha_top: float = Field(gt=0, lt=1)
    alpha_thr: int = Field(ge=0, le=255)
    head_scan: float = Field(gt=0, le=1)      # 머리 폭을 찾는 맨 위 줄 범위(초상 폭 배수)
    head_h_ratio: float = Field(gt=0)         # 턱 줄 = 정수리 + 이 값 × 머리 폭
    head_margin_px: float = Field(ge=0)       # 설계 px — 머리 상자가 원(R − 이 값) 안
    shadow_alpha: float = Field(ge=0, le=1)
    shadow_dy: float = Field(ge=0)

    @model_validator(mode="after")
    def _widths(self) -> "BadgePortrait":
        if self.min_width > self.width:
            raise ValueError(f"badge.portrait min_width {self.min_width} > width {self.width}")
        return self


class BadgeFlagWave(_Strict):
    """v5.15.0 인물 뒤 국기 물결 — 띠 수는 장치 폭 기반, 하한·상한."""

    cx: float
    cy: float
    width: float = Field(gt=0)
    alpha: float = Field(gt=0, le=1)
    strip_px: float = Field(gt=0)
    strips_min: int = Field(ge=1)
    strips_max: int = Field(ge=1)
    speed: float
    phase_span: float
    amp: float = Field(ge=0, lt=0.1)
    shade_alpha: float = Field(ge=0, le=1)
    shade_phase: float

    @model_validator(mode="after")
    def _strips(self) -> "BadgeFlagWave":
        if self.strips_min > self.strips_max:
            raise ValueError(f"flag_wave strips_min {self.strips_min} > strips_max {self.strips_max}")
        return self


class BadgeRing(_Strict):
    outer_w: float = Field(gt=0)
    inner_w: float = Field(gt=0)
    outer_rgb: RGB
    inner_alpha: float = Field(ge=0, le=1)


class BadgeLayout(_Strict):
    R_person_solo: float
    R_person_group: Range2
    R_person_panel: float
    R_flag: Range2
    R_other: float
    flag_requires_anchor: bool = False   # v7.4.0 D-0240 §4 — 국기 뱃지는 카드·인용·마커에 붙을 때만([badge-orphan])
    anchor_marker_deg: float = Field(default=3.0, gt=0)
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
    head_popout: bool = True          # v5.5.0 — False = 초상 머리를 원 안에만(정수리가 원 밖으로 나오지 않음)
    portrait: BadgePortrait           # v5.15.0 D-0153 §5 — 인물 초상 배치(head_inside_max 대체)
    flag_wave: BadgeFlagWave          # v5.15.0 — 인물 뒤 국기 물결
    ring: BadgeRing                   # v5.15.0 — 인물 뱃지 링


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

    max_span_months: int = Field(default=36, gt=0)   # v5.6.0 RENDER-AP-011 — 월 눈금 축이라 이보다 긴 기간은 오류(연도 카드 precedent 로)

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
    badge_hold: bool = False      # v5.6.0 사용자 지적 2026-10-04 — 뱃지 수명 동안 겹치는 카드 전부를 피하는 이동을 한 번 정해 고정(위아래로 움직이지 않는다)
    hold_directions: list[Literal["left", "down", "left-down"]] = Field(default_factory=lambda: ["down"])   # 고정 이동 방향(아일랜드 아래)
    hold_sample_sec: float = 0.25  # 고정 이동 계산의 시간 표본 간격(카메라가 움직이면 가장 큰 이동을 쓴다)


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
    unit_gap: float   # v5.3.1 — 단위는 max(unit_dx, 큰 숫자 폭 + unit_gap) 에(두 자리 이상에서 숫자와 겹침 방지)
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
    few: "DotsFew"   # v7.4.0 D-0229 §2.6 — 점 수가 적을 때(N 중 M) 한 줄 큰 점


class DotsFew(_Strict):
    max_total: int = Field(ge=1)   # total 이 이 이하면 한 줄
    y: float                       # 줄 중심 y(설계 px)
    x0: float                      # 첫 점 중심 x
    x1: float                      # 줄 오른쪽 끝(점 간격 = min(spacing, (x1 − x0)/(n − 1)))
    spacing: float
    radius: float


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


class InterpolatedStyle(_Strict):
    """v7.4.0 D-0247 — 보간 구간 선 스타일(실측과 구분): 점선·알파 배율·점 표식(false 여야 정직성 통과)."""

    dash: list[float] = Field(min_length=2)
    alpha: float = Field(gt=0, lt=1)
    point: bool = False


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
    x_label_rot_rad: float  # v5.3.1 — 기운 라벨 각도(라디안, 45도)
    x_label_rot_dx: float   # v5.3.1 — 45도 기운 라벨 기준점(눈금 x 에서 오른쪽)
    x_label_rot_dy: float   # v5.3.1 — 45도 기운 라벨 기준점(축 아래)
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
    gap_policy: Literal["interpolate", "break"] = "break"   # v7.4.0 D-0247(UF-128) — 빈 달(null) 처리
    interpolated_style: Optional[InterpolatedStyle] = None
    gap_note: str = ""                                     # 보간 구간이 있으면 출처 줄 끝에 코드가 붙이는 문구


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
    footnote_size: float = Field(default=10.0, gt=0)   # v5.6.0 — 카드 아래 주석(layout_480p.min_font_px 이상)
    footnote_y: float = Field(default=381.0, gt=0)     # 첫 줄 기준선(설계 px) — 카드 아래 끝 362, 자막 구역 410 위
    footnote_gap: float = Field(default=13.0, gt=0)    # 줄 간격


class VersusPanelRules(_Strict):
    title_size: float
    item_size: float
    src_size: float
    item_pad_r: float = Field(gt=0)          # v5.3.1 — 항목 글자 오른쪽 여백(상자 테두리에 닿지 않게)
    item_max_lines: int = Field(ge=1, le=3)  # v5.3.1 — 한 항목 최대 줄 수(넘치면 오류, P6)
    item_line_gap: float = Field(gt=0)       # v5.3.1 — 접힌 항목 둘째 줄 간격(항목 간격 50 안)


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
    water: str
    badge_bg: str
    panel_cover: Color4
    card_bg: Color4
    panel_card_bg: Color4
    # v5.18.0 D-0161 §3 — 지도 위 요소의 의미색 테마 보정: {테마: {키: "#rrggbb"}}. 색상(hue)은 공통값과 같고 밝기·채도만 다르다(테스트).
    # 키 = 의미색(ru·us·gold·teal·green·muted·amber·water) + white(지도 위 마커 글자). 카드·패널·자막·HUD·엔딩·뱃지는 테마 무관
    themes: dict[str, dict[str, str]] = Field(default_factory=dict)


class Fonts(_Strict):
    sans: str
    serif: str
    display: str
    mono: str
    mono_hangul_fallback: str
    display_space_advance: float
    unit_font: Optional[Literal["sans"]] = None   # v7.4.0 D-0229 §2.4(UF-111) — display 숫자 뒤 라틴 단위(t·kb/d)를 이 글꼴로(GmarketSans 십자형 t 금지)
    glyph_fallback: dict[str, str] = Field(default_factory=dict)   # v7.4.0 D-0250(UF-131) — 글꼴 키 → 그 글꼴에 없는 글자를 그릴 글꼴 키


class LabelRules(_Strict):
    border_lod_w: float
    admin1_fade_w: Range2
    province_w_max: float
    city_max_per_frame: int
    country_rank_thr: dict[int, int]
    city_rank_thr: dict[int, int]
    # v7.4.0 D-0229 §2.1(UF-106) — 나라 수도(plc_cap0, NE Admin-0 capital)는 폭 LOD(city_rank_max)와 무관하게 도시 후보에 넣는다. 화면당 상한(city_labels_max)은 그대로.
    # capital_always_max_w = 상시 표기를 이 폭(도) 이하로 제한(None = 폭 무관). 골든이 바뀌면 60 으로 제한(D-0229 §2.1-1)
    capital_always: bool = False
    capital_always_max_w: Optional[float] = None


class GazetteerRules(_Strict):
    """v4.10.0 D-0116(B-1) — 지명 사전 위치와 NE 수록 기준. 항목별 허용 오차는 사전 파일에 있다."""

    path: str
    ne_min_population: int = Field(gt=0)
    ne_tol_km: float = Field(gt=0)


class Shade(_Strict):
    """hillshade 배율 = clip(base + gain·(hs − sin 고도), lo, hi)."""

    base: float
    gain: float
    lo: float
    hi: float

    @model_validator(mode="after")
    def _range(self) -> "Shade":
        if not 0 < self.lo <= self.hi:
            raise ValueError(f"shade lo·hi 는 0 < lo ≤ hi: {self.lo}·{self.hi}")
        return self


class CoastGlow(_Strict):
    rgb: str
    strength: float = Field(ge=0)
    blur_px: tuple[float, float]   # [설계 ppd < 64, 그 이상] × k


class TerrainTheme(_Strict):
    """geo.prep 가 지형 티어 래스터에 굽는 값(v5.13.0 D-0153 Q0-2)."""

    land_stops: list[tuple[float, str]] = Field(min_length=2)
    sea_stops: list[tuple[float, str]] = Field(min_length=2)
    exaggeration: tuple[float, float]   # [설계 ppd < 64, 그 이상]
    sun: tuple[float, float]            # 방위·고도(도)
    land_shade: Shade
    sea_shade: Optional[Shade]
    sea_tint: Optional[tuple[int, int, int]]   # 회색 g → (g+r, g+g', g+b), 0~255
    coast_glow: CoastGlow

    @model_validator(mode="after")
    def _stops(self) -> "TerrainTheme":
        for nm in ("land_stops", "sea_stops"):
            v = [a for a, _ in getattr(self, nm)]
            if v != sorted(v) or len(set(v)) != len(v):
                raise ValueError(f"{nm} 값은 오름차순·중복 없음: {v}")
        return self


class MapLine(_Strict):
    rgb: RGB
    width: float = Field(gt=0)
    alpha: Optional[float] = Field(default=..., ge=0, le=1)   # None = 무대 LOD 알파
    dash: list[float] = Field(default_factory=list)            # [] = 실선


class RoadStyle(_Strict):
    """v7.4.0 D-0229 §2.1-2 — 도로 한 등급(단일 stroke, casing·glow 없음 — 가이드 23 §15). 설계 px(480p)."""

    rgb: RGB
    width: float = Field(gt=0)
    alpha: float = Field(gt=0, le=1)


class MapRoads(_Strict):
    motorway: RoadStyle
    trunk: RoadStyle
    primary: RoadStyle


class MapRivers(_Strict):
    """v7.4.0 D-0229 §2.1-2 — 강(큰 강 = NE scalerank ≤ geo.river_major_scalerank_max). 설계 px(480p)."""

    rgb: RGB
    width_major: float = Field(gt=0)
    width_minor: float = Field(gt=0)
    alpha_major: float = Field(gt=0, le=1)
    alpha_minor: float = Field(gt=0, le=1)


class CityDot(_Strict):
    fill: RGB
    edge: RGB
    edge_alpha: float = Field(ge=0, le=1)


class RouteCasing(_Strict):
    """v5.18.0 D-0161 §2 — 경로 선 아래 밝은 테두리(지도 선 대비 보조). width_add = 선 양쪽에 더하는 폭(설계 px)."""

    rgb: RGB
    alpha: float = Field(ge=0, le=1)
    width_add: float = Field(gt=0)


class ThemeBorderGlow(_Strict):
    """v5.18.0 D-0161 §2 — 테마별 국경 글로우. enabled false = 이 테마에선 끈다(direction 이 켜도). 값이 없으면 공통 border_glow."""

    enabled: bool = True
    rgb: Optional[RGB] = None
    halo: Optional[list[tuple[float, float]]] = None
    run_layers: Optional[list[tuple[float, float]]] = None


class RouteLabelTheme(_Strict):
    """v5.21.11 D-0191 §1-3·D-0192 — 경로 라벨 글자 모양. color = 경로 색 글자(dark 종전), ink = 테마 글자 톤 + 테마 halo,
    경로 색은 글자 앞 짧은 색 표시(mark)로만."""

    style: Literal["color", "ink"]
    halo: Optional[float] = None           # ink: 글자 테두리 두께(없으면 color 와 같은 3)
    mark_w: float = Field(default=0, ge=0)
    mark_h: float = Field(default=0, ge=0)
    mark_gap: float = Field(default=0, ge=0)


class LabelContrastFix(_Strict):
    """v5.21.2 D-0186 §2-1 — 국소 대비 보정: 그린 지명의 실제 바탕 대비가 qa_checks.map_contrast_text 미만이면 이 halo 로 다시 그린다."""

    halo: float = Field(gt=0)
    halo_a: float = Field(gt=0, le=1)


class MapTheme(_Strict):
    """렌더가 읽는 지도 선·지명 색(engine/layers/borders·labels)."""

    border: MapLine
    admin: MapLine
    sea_label: str
    country_label: RGB
    admin_label: RGB
    city_dot: CityDot
    city_label: RGB
    halo: RGB
    roads: MapRoads      # v7.4.0 D-0229 §2.1-2(UF-106) — 두 테마 모두 채운다(키 집합 동일, tests/test_v740_map_layers)
    rivers: MapRivers
    # v5.18.0 D-0161 §2(가이드 23 §14) — 해안선 ↔ 국경 분리. 있으면 두 나라가 공유하는 변만 국경(border), 나머지 고리는 해안(coast)으로 긋는다.
    # None = 종전(모든 고리를 국경 스타일로 — dark 골든 바이트 동일)
    coast: Optional[MapLine] = None
    route_casing: Optional[RouteCasing] = None          # v5.18.0 — None = 없음(dark 종전)
    border_glow: Optional[ThemeBorderGlow] = None       # v5.18.0 — None = 공통 rules border_glow(dark 종전)
    label_contrast_fix: Optional[LabelContrastFix] = None   # v5.21.2 — None = 보정 없음
    route_label: Optional[RouteLabelTheme] = None            # v5.21.11 — None = color(dark 종전)


class GeoTheme(_Strict):
    terrain: TerrainTheme
    map: MapTheme


class GeoThemes(_Strict):
    """v5.13.0 D-0153 Q0-2 — 지도 테마 시안. 기본 테마 자산 = assets/, 그 밖 = assets/theme_<이름>/."""

    default: str
    dark: GeoTheme
    light: GeoTheme

    @model_validator(mode="after")
    def _default(self) -> "GeoThemes":
        if self.default not in self.names():
            raise ValueError(f"geo.themes.default {self.default!r} 는 {self.names()} 중 하나")
        return self

    @staticmethod
    def names() -> list[str]:
        return ["dark", "light"]

    def get(self, name: str) -> GeoTheme:
        if name not in self.names():
            raise ValueError(f"지도 테마 {name!r} 없음 — rules geo.themes: {self.names()}")
        return getattr(self, name)


class GeoRules(_Strict):
    land_miss_allow_px2: float
    land_fill_min_ratio: float = Field(gt=0, le=1)   # v4.1.0 D-0078
    boundary_names: list[str] = Field(min_length=1)   # v4.7.0 D-0107 D2(b) — checks [boundary-as-route]
    gazetteer: GazetteerRules                         # v4.10.0 D-0116 — checks [geo-mismatch]
    themes: GeoThemes                                 # v5.13.0 D-0153 Q0-2 — 지도 테마(시안)
    map_layers_default: list[Literal["roads", "rivers"]]   # v7.4.0 D-0231 — stage_config.mercator.map_layers 기본값
    country_polygons: str = "data/geo_flat/ne_110m_countries.json"   # v7.4.0 D-0241 §2 — 국가 폴리곤 자료(flag_territory·sea_only_frame)
    river_major_scalerank_max: int = Field(ge=0)      # v7.4.0 D-0229 §2.1-2 — NE 강 scalerank 이 값 이하 = 큰 강(geo.prep_geometry.load_rivers)


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


class BgmFloor(_Strict):
    """v7.2.0 UF-100 D-0222 — BGM 등록 실측 하한(audio.bgm_measure)."""

    beat_clarity_min: float = Field(gt=0)      # 템포그램 명확도(시간 평균 템포그램의 최대 ÷ 평균, 0 지연 제외)
    onsets_per_min_min: float = Field(gt=0)    # 온셋 밀도(librosa onset_detect 개수 ÷ 분)
    voice_band_max: float = Field(gt=0, lt=1)  # 내레이션 대역 파워 비중 상한
    voice_band_hz: tuple[float, float]
    window_sec: float = Field(gt=0)            # 측정 구간 0~window_sec(영상은 곡을 0초부터 5~6분 쓴다)
    sr: int = Field(gt=0)
    n_fft: int = Field(gt=0)


class AudioClip(_Strict):
    """v7.4.0 D-0274 §2③·D-0276 — 클립 원음 트랙 이득(dB)."""

    main_gain_db: float = Field(le=0)
    broll_gain_db: float = Field(le=0)
    narration_duck_db: float = Field(le=0)
    bed_duck_db: float = Field(le=0)
    duck_fade_sec: float = Field(gt=0)


class AudioRules(_Strict):
    bed_gain: float
    bgm_floor: BgmFloor
    bgm_default: list[str] = Field(min_length=1)
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
    clip: AudioClip
    fx_duck: float
    crossfade_sec: float = Field(gt=0)
    qa: AudioQARules
    norm_eps: float
    bed_bass: BedBass
    sfx: SfxRules


class RouteMissingRules(_Strict):
    """v5.21.14 D-0195·D-0197 — 문장에 이동·공격 동사 + 그 문장이 부르는 마커가 있으면 그 마커에 닿는 경로가 문장 구간에 있어야 한다."""

    move_verbs: list[str] = Field(min_length=1)
    attack_verbs: list[str] = Field(min_length=1)
    endpoint_tol_deg: float = Field(gt=0)     # 경로 끝점 ↔ 마커 월드 거리(경도·메르카토르 도)


class FrameMissingRules(_Strict):
    """v5.21.14 D-0199 — 문장이 부르는 나라(라벨 점)·마커가 문장 구간 표본 시각 모두에서 화면 밖이면."""

    margin_px: float = Field(ge=0)            # 화면 가장자리 안쪽 여백(이만큼 안에 들어와야 '보인다')
    sample_sec: float = Field(gt=0)


class BattleGeoRules(_Strict):
    """v5.22.0 D-0200 UF-08 — 전황 동사(점령·탈환·공세 등) 문장 구간에 지도 마커·경로가 하나도 없으면 warning(battle_geo)."""

    verbs: list[str] = Field(min_length=1)


class OutletNames(_Strict):
    """v7.4.0 D-0250(UF-130) — 매체 표기(원고 문장에서 찾는 이름)와 url 도메인."""

    names: list[str] = Field(min_length=1)
    domains: list[str] = Field(default_factory=list)


class CardOverPanel(_Strict):
    """v7.4.0 D-0248(UF-129) — 패널 위 카드 겹침 검사 임계."""

    min_overlap_sec: float = Field(gt=0)
    panel_pad_px: float = Field(ge=0)
    cover_types: list[str] = Field(min_length=1)               # 모든 패널 위 덮개(D-0249)
    cover_types_on_data_panels: list[str] = Field(default_factory=list)   # 데이터 패널(series record) 위에서만 더 세는 덮개
    timeline_frame_cover_types: list[str] = Field(default_factory=list)   # v7.4.0 D-0259 — 시간축 틀 안 시리즈 레인 위에서 세는 덮개(사건 레인 허용)


class ChartOnlyRun(_Strict):
    """v7.4.0 D-0251 §6.2-3·D-0252(UF-135 ① "너무 차트만") — 차트·카드만 보이는 구간 상한. 모든 무대·장르, 콘티 판·프리뷰·전편 같은 키.
    차트 요소 = chart_types(+ island kind chart_island_kinds, primitive id chart_primitives). neutral_types 는 판정에 넣지 않는다.
    그 밖 등록 요소와 map_stages 무대가 패널 덮개 없이 보이는 순간 = 비차트(지도는 장소다). 타이틀·엔딩 카드 구간 제외."""

    max_sec: float = Field(gt=0)
    step_sec: float = Field(gt=0)
    chart_types: list[str] = Field(min_length=1)
    chart_island_kinds: list[str] = Field(default_factory=list)
    chart_primitives: list[str] = Field(default_factory=list)
    neutral_types: list[str] = Field(default_factory=list)
    map_stages: list[str] = Field(min_length=1)


class QAChecks(_Strict):
    overlap_core_elements: int
    chart_only_run: ChartOnlyRun                      # v7.4.0 D-0252 — [chart-only-run] hard
    card_over_panel: Optional[CardOverPanel] = None   # v7.4.0 D-0248(UF-129)
    outlet_min_overlap_sec: float = 0.5               # v7.4.0 D-0250(UF-130)
    outlet_names: dict[str, OutletNames] = Field(default_factory=dict)
    offscreen_clip: int
    missing_glyphs: int
    labels_per_frame_max: int
    subtitle_lines_max: int
    rights_missing: int
    forbidden_components: int
    glyph_size_exempt: list[Literal["end_card", "media_meta"]]   # v3.6.0 D-0069 — 역할 레지스트리(엔진 text(role=) 와 같은 이름)
    label_hidden_max_ratio: float = Field(gt=0, le=1)   # v3.6.0 D-0068
    route_missing: "RouteMissingRules"   # v5.21.14 D-0195·D-0197 — 이동·공격 문장의 경로 누락
    frame_missing: "FrameMissingRules"   # v5.21.14 D-0199 — 문장이 부르는 지명이 화면 밖
    battle_geo: "BattleGeoRules"         # v5.22.0 D-0200 UF-08 — 전황 문장에 지명·경로 없음(warning)
    card_full_exposure_min_sec: float = Field(gt=0)   # v5.21.10 D-0191 §1-2 — 기사·인용 카드 완전 불투명 구간 하한(hard card_exposure)
    restate_overlap_max: float = Field(default=0.6, gt=0, le=1)   # v7.4.0 D-0306 §1.2 — [text-restates-narration] 어절 겹침 상한
    restate_min_words: int = Field(default=4, ge=1)   # 이 어절 미만 화면 글자(이름표)는 보지 않는다
    restate_particles: list[str] = Field(default_factory=list)   # v7.4.0 D-0316 ② — 어절 끝 조사(떼고 비교)
    # v7.4.0 D-0311 — 회귀 기준 프로젝트 id → 사유, 그리고 hard 만 면제하는 검사 id(검사는 돌고 provenance regression_waived 기록)
    regression_refs: dict[str, str] = Field(default_factory=dict)
    # v7.4.0 D-0312 §1-1 — [scene-visual-void] hard: 요소 없는 구간 상한(초)·표본 간격·요소로 치는 이벤트 종류
    visual_void_max_sec: float = Field(default=5.0, gt=0)
    visual_void_step_sec: float = Field(default=0.1, gt=0)
    visual_void_types: list[str] = Field(default_factory=list)
    regression_ref_checks: list[str] = Field(default_factory=list)
    ratio_patterns: list[str] = Field(min_length=1)       # v7.4.0 D-0229 §2.6(UF-113) — "N 중 M" 문형(warning ratio_graphic)
    ratio_graphic_kinds: list[str] = Field(min_length=1)  # 그 문장 구간에 있어야 할 패널 종류(series 이벤트도 인정)
    cutaway_full_types: list[str] = Field(min_length=1)   # v7.4.0 D-0229 §2.3(UF-110) — 화면 전체를 덮는 컷어웨이 이벤트(hard cutaway_churn). 지도 복귀 ≥ shot_min_hold_sec
    label_jump_px: float = Field(gt=0)   # v5.22.7 D209 — 경로 이름표 수명 중 자리 이동 상한(hard label_jump)
    camera_bounds_rel_tol: float = Field(gt=0)   # v7.1.0 UF-99 D-0220 — 요청 ≠ 화면 카메라(경계 클램프) 허용 오차 ÷ w(hard camera_bounds)
    label_slot_sample_sec: float = Field(gt=0)   # v5.22.7 D210 — 이름표 수명 표본 간격(route_label_slots)
    map_contrast_text: float = Field(default=4.5, gt=1)    # v5.18.0 D-0161 §4 — 지도 위 필수 글자 ↔ 합성 배경(hard)
    map_contrast_shape: float = Field(default=3.0, gt=1)   # 지도 위 경로 선 ↔ 주변(warning)
    map_contrast_min_alpha: float = Field(default=0.8, gt=0, le=1)   # 이 알파 이상으로 다 나타난 요소만 잰다(페이드 중·카드 뒤 흐린 라벨 제외)
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
    bound_pad: float = Field(gt=0)   # v7.1.0 D-0220 — 제안 w 상한 여유(경계 안 키만)
    center_grid: int = Field(ge=1)
    date_reserve_chars: float = Field(gt=0)
    cover_samples: int = Field(ge=2)
    verify_rounds: int = Field(ge=1)
    path_w_step: float = Field(gt=1)
    context_w_min: dict[str, float]   # v3.3.0 D-0058 — shot_grammar.w_guide 분류 → w 하한(키 집합 = w_guide, VideoRules 가 검사)
    marker_px: PxBox
    badge_px: BadgePx
    point_px: PxBox


class StaticEps(_Strict):
    w_rel: float = Field(gt=0)
    center_rel: float = Field(gt=0)


class DriftSpeedMax(_Strict):
    pan_w_per_sec: float = Field(gt=0)
    zoom_per_sec: float = Field(gt=0)


class CameraRules(_Strict):
    """v3.3.0 D-0056 — 카메라 자동화 보조(05 §7). v7.4.0 D-0241·D-0242 — 정지 카메라·drift·육지 비율."""

    framing: FramingRules
    static_max_sec: float = Field(default=20.0, gt=0)
    static_eps: StaticEps = Field(default_factory=lambda: StaticEps(w_rel=0.01, center_rel=0.005))
    drift_speed_max: DriftSpeedMax = Field(default_factory=lambda: DriftSpeedMax(pan_w_per_sec=0.02, zoom_per_sec=0.01))
    land_min_ratio: float = Field(default=0.35, ge=0, le=1)
    land_sample_sec: float = Field(default=1.0, gt=0)


class RouteSpeed(_Strict):
    """v7.4.0 D-0241 §4(UF-123) — 경로 grow 속도 상한(설계 px/초)."""

    grow_speed_max_px_s: float = Field(gt=0)


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
    placeholder: AnimaticPlaceholder
    band: AnimaticBand
    missing_license: str               # 권리 레지스트리(생성 자산)가 없는 환경의 엔딩 카드 license_ref 자리 문구(전편은 오류 그대로)
    checks_skip: list[str] = Field(min_length=1)   # 콘티 판에서 건너뛰는 checks id(provenance animatic.checks_skipped)
    cost_target_sec_per_300s: float = Field(gt=0)   # 5분 영상 콘티 판 목표 시간(4코어, run_log 실측과 비교)


class CatalogLines(_Strict):
    """카탈로그 라벨 줄 틀 — {자리}는 코드가 채운다(.replace, C2). 값의 출처는 config tts·rules fonts·registries(P5)."""

    stage: str = Field(min_length=1)        # {stage} {theme}
    elements: str = Field(min_length=1)     # {items}
    fonts: str = Field(min_length=1)        # {items}
    voice: str = Field(min_length=1)        # {backend} {style} {speed} {suffix} {span} {semitones}
    voice_flat: str = Field(min_length=1)   # 끝 억양 꺼짐(final_fall.enabled false) — {backend} {style} {speed}


class CatalogLabel(_Strict):
    """카탈로그 라벨(480p 설계 px) — 왼쪽 위. 날짜 뱃지·자막과 교차하면 checks [catalog-label-overlap] hard(카탈로그 산출물만)."""

    font: str
    size: float = Field(gt=0)
    pos: tuple[float, float]                # 글자 블록 좌상단
    max_w: float = Field(gt=0)
    alpha: float = Field(gt=0, le=1)
    color: Color4
    plate: Color4                           # 바탕판
    pad: float = Field(ge=0)
    line_gap: float = Field(gt=0)
    max_lines: int = Field(ge=3)            # 무대 1 + 요소 ≥ 1 + 음성 1
    font_keys: list[str] = Field(min_length=1)   # 글꼴 줄에 쓰는 rules fonts 키(순서 = 표기 순서)
    sep: str
    indent: str
    more: str = Field(min_length=1)         # 넘친 요소 수 {n}
    no_theme: str = Field(min_length=1)     # 지도 무대가 없을 때 테마 자리
    lines: CatalogLines


class CatalogRules(_Strict):
    """v7.4.0 back_and_forth D-0251 §1.1 — 카탈로그 판(`engine.render --catalog`). 전편 레이어 전부 + 라벨 층. final.mp4 에는 들어가지 않는다."""

    profile: str                            # config engine.output 프로파일 이름 또는 별칭(trial·final)
    output: str                             # out/ 아래 파일 이름(영상 + 음성)
    preset: str                             # x264 preset(카탈로그 인코딩만)
    mp4_comment: str = Field(min_length=1)  # mp4 메타데이터 표식 — deliver(engine.mux)가 보면 거부
    sample_every_sec: float = Field(gt=0)   # 요소 표(out/catalog_frames.json) 표본 간격
    label: CatalogLabel


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
    stop_at_source: Literal["source_band", "through"]   # v7.4.0 D-0321 §4 — 세로 격자선을 출처 줄 띠 위에서 끊는다


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
    axis_label_min_gap_px: float = Field(gt=0)   # v7.4.0 D-0268 §2 — 축 값 라벨 사이 화면 간격 하한. 미만이면 중간 라벨 생략(눈금선만)
    source_dy: float
    source_step: float
    source_size: float
    source_font: str
    source_halo: float
    end_label_min_gap_px: float = Field(gt=0)   # v7.4.0 D-0256 — 같은 레인 끝값 라벨 세로 최소 간격(기준선 사이)
    end_label_plate: "EndLabelPlate"   # v7.4.0 D-0277 §2 — 끝값 라벨 뒤 판(바탕 bg_rgb)
    pin_label_rows: int = Field(ge=1)              # v7.4.0 D-0274 §1② — 값 레인 위 핀 라벨 단 수(선 위·아래 각)
    pin_label_first_dy_px: float = Field(gt=0)     # 점 → 가장 가까운 단 라벨 상자 가장자리
    pin_label_row_gap_px: float = Field(gt=0)      # 한 줄 라벨 단 간격(글자 + 여백)
    pin_leader_w: float = Field(gt=0)
    pin_leader_alpha: float = Field(gt=0, le=1)
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
    daily_note_outlier: str = Field(min_length=1)   # v7.4.0 D-0319 ③ — 일별 계열 missing 은 출처 줄 한 줄({n} = 날 수)
    daily_note: str = Field(min_length=1)


class TimelineBars(_Strict):
    """v7.4.0 D-0278 §4.1·D-0308·D-0309 — series bars·stack(분기 캡슐, 0 에서 자란다, 잉크 사다리·직접 라벨)."""

    w_ratio: float = Field(gt=0, le=1)
    top_radius: float = Field(ge=0)          # D-0310 §1-2 — 바깥 끝 모서리만(0 쪽은 각)
    hollow_w: float = Field(gt=0)
    ink: str
    ladder: list[float] = Field(min_length=1)
    stack_ladder: list[float] = Field(min_length=1)
    stack_sep_w: float = Field(ge=0)
    negative_fill: Literal["muted_fill", "ink_light"]   # v7.4.0 D-0328 — 손실 = 채도 낮춘 면 | 잉크 사다리 가장 옅은 면(값이 손실을 말한다). 테두리 없음
    neg_fill_mix: float = Field(gt=0, le=1)
    neg_ink_step: int = Field(ge=0)   # v7.4.0 D-0330 — ink_light 사다리 단
    loss_color: str
    neg_fill_alpha: float = Field(gt=0, le=1)
    neg_outline_w: float = Field(gt=0)
    label_contrast_min: float = Field(gt=1)
    zero_alpha: float = Field(gt=0, le=1)
    zero_w: float = Field(gt=0)
    lane_pad_top: float = Field(ge=0, lt=0.5)
    lane_pad_bottom: float = Field(ge=0, lt=0.5)
    value_size: float = Field(gt=0)
    value_font: str
    value_gap: float = Field(ge=0)
    value_halo: float = Field(ge=0)
    part_label_size: float = Field(gt=0)
    part_label_font: str
    part_label_dx: float
    part_label_min_h: float = Field(ge=0)
    leader_len: float = Field(ge=0)
    total_dot_r: float = Field(gt=0)
    total_line_w: float = Field(gt=0)
    total_alpha: float = Field(gt=0, le=1)
    sum_tol_pct: float = Field(gt=0)
    pair_w_ratio: float = Field(gt=0, le=1)      # v7.4.0 D-0315 §1-3 — dumbbell·diverging 부문 묶음 폭
    pair_dot_r: float = Field(gt=0)
    pair_line_w: float = Field(gt=0)
    pair_line_alpha: float = Field(gt=0, le=1)
    diverging_w_ratio: float = Field(gt=0, le=1)
    guide_band_alpha: float = Field(gt=0, le=1)   # v7.4.0 D-0321 §2-1
    guide_tick_ratio: float = Field(gt=0, le=1)


class TimelineSecondary(_Strict):
    """v7.4.0 D-0309 §1-4 — 같은 레인 보조 축 계열(하나)."""

    line_w: float = Field(gt=0)
    alpha: float = Field(gt=0, le=1)
    dot_r: float = Field(ge=0)
    axis_label_margin_px: float = Field(ge=0)


class TimelineBand(_Strict):
    """v4.4.0 D-0090 작업 2 — series band(목표 범위 띠)."""

    fill_alpha: float = Field(gt=0, le=1)
    edge_alpha: float = Field(gt=0, le=1)
    edge_w: float = Field(gt=0)
    sep: str = Field(min_length=1)


class EndLabelPlate(_Strict):
    """v7.4.0 back_and_forth D-0277 §2 — 끝값 라벨 뒤 판. 색 = stage_timeline.bg_rgb, 글자 상자 + pad_px."""

    alpha: float = Field(gt=0, le=1)
    pad_px: float = Field(ge=0)
    descent: float = Field(ge=0, lt=1)   # 글자 내림 ÷ 글자 크기


class TimelineLaneRange(_Strict):
    """v7.4.0 back_and_forth D-0263(사용자 의견 UF-140 "변동이 크지 않은 데이터… 가로로 펼쳐진 직선으로밖에 안보인다") — 시간축 레인 값 범위.
    fit = [min − pad, max + pad](무대 기간 안 레코드 전체, 영상당 한 번), 최소 폭 하한(단위별), 끝 값 반올림(end_round, D-0277 §3 정정). 막대는 0 기준(chart_honesty) 그대로."""

    mode: Literal["fit", "zero"]
    pad_ratio: float = Field(ge=0, lt=0.5)
    nice_mantissas: list[float] = Field(min_length=1)
    ticks_max: int = Field(ge=0)              # 위·아래 끝 사이 중간 눈금 최대 수
    end_round: Literal["step", "half_step"] = "step"   # v7.4.0 D-0277 §3 정정 — 끝 값 내림·올림 단위(간격 / 간격의 절반)
    min_span: dict[str, float]                # 단위 → 최소 폭(없는 단위 = 데이터 폭)
    flat_lane_min_ratio: float = Field(gt=0, lt=1)   # [flat-lane] hard — 그려진 세로 폭 ÷ 레인 값 영역 높이 하한
    empty_band_max_ratio: float = Field(gt=0, lt=0.5)   # v7.4.0 D-0277 §3 [axis-empty-band] hard — 데이터 극값 밖 빈 띠(한쪽) ÷ 축 범위 상한
    axis_range_note: str = Field(pattern=r"\{lo\}.*\{hi\}")   # 0 이 아닌 곳에서 시작하면 출처 줄 끝에 붙는 표기


class TimelineProjection(_Strict):
    """v7.4.0 back_and_forth D-0260 §2·D-0264 — 시간축 레인 위 전망 점(series style projection, scatter 레코드)."""

    column_date: Literal["year_end"]
    longer_run_gap_days: int = Field(gt=0)
    column_stagger_sec: float = Field(ge=0)
    band_alpha: float = Field(ge=0, le=1)
    median_alpha: float = Field(gt=0, le=1)
    label_dy: float = Field(gt=0)
    hold_clip: Literal["hard", "off"] = "hard"   # v7.4.0 D-0277 §1 — 카메라가 머무는 창에서 전망 열 반쯤 잘림·마지막 실측 점 없음 = [chart-edge-bleed]


class TimelineAxisScale(_Strict):
    """v5.1.0 D-0121 §A(사용자 피드백 D105) — 시간축 축 스케일(카메라 w) 고정. checks timeline_rescale(hard)·provenance timeline.w_changes[].
    grammar 의 {max}·{ratio} 는 같은 블록 값(프롬프트 {{RULES.stage_timeline.axis_scale}})."""

    w_changes_per_video_max: int = Field(ge=0)
    w_change_ratio_min: float = Field(gt=1)
    scene_fixed: bool
    grammar: str = Field(pattern=r"\{max\}")


class TimelineFrame(_Strict):
    """v7.4.0 back_and_forth D-0257(UF-137) — 시간축 주 무대 틀: 화면 안쪽 안전 영역 [x, y, 폭, 높이](설계 px). 레인·눈금·글자는 이 안에만.
    상자 모양(그림자·바탕·테두리·모서리)과 레인 영역 패딩은 차트 아일랜드와 같은 값(rules island·island.chart)."""

    box: tuple[float, float, float, float]

    @model_validator(mode="after")
    def _inside(self) -> "TimelineFrame":
        x, y, w, h = self.box
        if x <= 0 or y <= 0 or w <= 0 or h <= 0:
            raise ValueError("stage_timeline.frame.box 는 화면 가장자리에서 떨어진 양의 상자")
        return self


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
    bars: TimelineBars             # v7.4.0 — D-0278 §4.1 스케치
    secondary: TimelineSecondary   # v7.4.0 — D-0309 §1-4 스케치
    missing_mark: TimelineMissingMark
    axis_scale: TimelineAxisScale  # v5.1.0 — D-0121 §A
    lane_range: TimelineLaneRange  # v7.4.0 — D-0263(UF-140)
    projection: TimelineProjection  # v7.4.0 — D-0260 §2·D-0264
    frame: TimelineFrame           # v7.4.0 — D-0257(UF-137)


class ChartWorldRules(_Strict):
    """v7.4.0 D-0251 §6.2-4 — 차트 연속 세계 연출 문법(연출·수정 프롬프트 {{RULES.chart_world}})."""

    grammar: list[str] = Field(min_length=1)


class ReferenceClipRules(_Strict):
    """v7.4.0 D-0274 §2⑤ — 레퍼런스 영상 문법(연출·원고 프롬프트)."""

    director: list[str] = Field(min_length=1)
    script: list[str] = Field(min_length=1)


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
    lane_h_max: float = Field(gt=0)   # v7.4.0 D-0269 — 아일랜드 시간축 레인 높이 상한(fit_island 만, 레인 둘 이상일 때만 — D-0274)
    plot_min_ratio: float = Field(gt=0, le=1)   # v7.4.0 D-0274 §1① — [plot-height] 플롯 세로 합 ÷ 액자 안쪽 높이 하한


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
    date_font: str      # v5.14.0 V2 — engine.style.FONT 키
    title_font: str
    line_font: str


class CascadeFrame(_Strict):
    """v5.14.0 V2 — 상자 모서리·테두리 폭·가림 여유(가이드 23 §6)."""

    radius: float = Field(ge=0)
    edge_w: float = Field(gt=0)
    occluder_pad: float = Field(ge=0)


class CascadeSurface(_Strict):
    """v5.14.0 V2(D-0157 보강 3) — cascade 전용 표면·글자색, RGB 0~1."""

    bg: RGB
    front: RGB
    back: RGB
    text: RGB
    text_sub: RGB
    edge: RGB

    @model_validator(mode="after")
    def _unit(self) -> "CascadeSurface":
        for k, v in self.model_dump().items():
            if not all(0 <= c <= 1 for c in v):
                raise ValueError(f"cascade.surface.{k} 는 RGB 0~1: {v}")
        return self


class QuotePairSlot(_Strict):
    """v5.3.1 맞선 인용 자리 — portrait = 초상 중심 [x, y], text_x = 글자 시작(upper, 왼쪽 정렬)·끝(lower, 오른쪽 정렬), quote_y = 첫 줄 기준선."""

    portrait: tuple[float, float]
    text_x: float
    quote_y: float


class QuoteCenterRules(_Strict):
    """v5.3.1 인물 발언 중앙 인용(시안 — 사용자 제안 2026-10-02, valdai-2026 한정). 설계 px(480p)."""

    status: Literal["prototype", "adopted"]
    scrim_rgb: tuple[float, float, float]
    scrim_alpha: float = Field(ge=0, le=1)
    portrait_R: float = Field(gt=0)
    portrait_y: float
    quote_y: float
    quote_size: float = Field(gt=0)
    quote_line_h: float = Field(gt=0)
    quote_max_w: float = Field(gt=0)
    quote_max_lines: int = Field(ge=1, le=3)
    mark_size: float = Field(gt=0)
    mark_alpha: float = Field(ge=0, le=1)
    who_size: float = Field(gt=0)
    who_dy: float
    src_size: float = Field(gt=0)
    src_dy: float
    rise_px: float = Field(ge=0)
    fade_sec: float = Field(gt=0)
    pair_R: float = Field(gt=0)
    pair_max_w: float = Field(gt=0)
    upper: QuotePairSlot
    lower: QuotePairSlot


class FlightTrail(_Strict):
    width: float = Field(gt=0)
    dash: tuple[float, float]
    alpha: float = Field(ge=0, le=1)
    fade_sec: float = Field(gt=0)


class FlightOriginGlow(_Strict):
    r_px: float = Field(gt=0)
    alpha: float = Field(ge=0, le=1)
    pulse_sec: float = Field(gt=0)
    out_sec: float = Field(gt=0)
    fade_in_sec: float = Field(gt=0)
    breath: float = Field(ge=0, le=1)


class FlightLine(_Strict):
    width: float = Field(gt=0)
    alpha: float = Field(ge=0, le=1)


class FlightIcon(_Strict):
    size_px: dict[Literal["drone", "missile", "jet"], float]
    halo: float = Field(ge=0)
    halo_alpha: float = Field(ge=0, le=1)
    body_line: FlightLine
    shapes: dict[Literal["drone", "missile", "jet"], list[tuple[float, float]]]
    body_lines: dict[Literal["drone", "missile", "jet"], list[tuple[tuple[float, float], tuple[float, float]]]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _kinds(self) -> "FlightIcon":
        if set(self.size_px) != set(self.shapes) or any(len(v) < 3 for v in self.shapes.values()):
            raise ValueError("flight.icon: size_px 와 shapes 의 종류가 같아야 하고 다각형은 꼭짓점 3개 이상")
        return self


class FlightInsetRules(_Strict):
    shape: Literal["circle"]   # UF-103 — 원형만(사각 금지)
    w_px: float = Field(gt=0)
    gap_px: float = Field(ge=0)
    lead_sec: float = Field(ge=0)
    hold_sec: float = Field(gt=0)
    fade: tuple[float, float]
    frame: FlightLine
    caption_dy: float
    caption_size: float = Field(gt=0)
    caption_halo: float = Field(ge=0)
    # v7.4.0 D-0229 §2.7(UF-107 "라잔 타격 설명이 나오는데 라잔 위성사진이 좀 보이면") — inset.place 를 준 인셋은 착탄 문장부터
    # 그 장소 이름을 말하는 연속 문장 끝까지 유지(engine.direction.build). inset.hold_until 명시가 우선
    hold_same_place: bool = False
    safe_margin_px: float = Field(default=0.0, ge=0)   # v7.4.0 D-0240 §2 — 안전 영역 여백(날짜 배지 아래·자막 띠 위)
    side_order: list[Literal["right", "left", "up", "down", "up_left", "up_right", "down_left", "down_right"]] = Field(default_factory=list)
    # v7.4.0 D-0300(UF-146 "위성사진을 보여주는 동그라미가 한순간 위치를 옮기고 사라져") — 자리는 등장 때 한 번 정해 고정, 옮겨야 하면 보간
    sticky_side: bool = False
    move_sec: float = Field(default=0.6, gt=0)       # 자리 옮김 보간 길이(ease in-out)
    jump_px_max: float = Field(default=24.0, gt=0)   # [inset-jump] hard — 원 중심 프레임 간 이동 상한
    move_headroom: float = Field(default=0.75, gt=0, le=1)   # 보간 최고 속도 ≤ jump_px_max × 이 값(나머지는 카메라가 표적을 미는 몫)
    predict_keyframes: bool = False   # v7.4.0 D-0305 ② — 인셋 생애 전 구도에 맞는 자리를 미리 골라 처음부터 고정(옮김 0), 없을 때만 보간


class FlightRules(_Strict):
    """v7.3.0 back_and_forth D-0206 — 비행 이벤트(flight). 설계 px(480p). engine/layers/flight.py 만 읽는다."""

    dur_sec: float = Field(gt=0)
    impact_sec: float = Field(gt=0)
    bulge_ratio: float
    samples: int = Field(ge=2)
    heading_du: float = Field(gt=0, lt=1)
    trail: FlightTrail
    origin: FlightOriginGlow
    icon: FlightIcon
    inset: FlightInsetRules


class BorderGlowRules(_Strict):
    """v5.3.1 국경선 글로우(시안 — 사용자 제안 2026-10-02, valdai-2026 한정). 설계 px."""

    status: Literal["prototype", "adopted"]
    rgb: tuple[float, float, float]
    halo: list[tuple[float, float]]
    run_seg_px: float = Field(gt=0)
    run_period_px: float = Field(gt=0)
    run_speed_px: float = Field(gt=0)
    run_layers: list[tuple[float, float]] = Field(min_length=1)
    default_on: bool = False   # v5.4.0 — 지도 무대 기본 켜짐(direction stage_config.mercator.border_glow 로 덮는다)

    @model_validator(mode="after")
    def _seg(self) -> "BorderGlowRules":
        if self.run_seg_px >= self.run_period_px:
            raise ValueError("border_glow: run_seg_px 는 run_period_px 보다 짧아야 한다(빛 조각 사이 간격)")
        return self


class CascadeRules(_Strict):
    """v5.2.0 겹침 카드(cascade — 사용자 재구성 2026-10-01, v5.3.0 D-0139 채택). 설계 px(480p). 상자 모양은 rules island 재사용.
    최악 폭 (max_back + 1) × step + front.w ≤ width_cap 을 여기서 검증하고, 실제 폭은 checks cascade 가 잰다."""

    status: Literal["prototype", "adopted"]
    x0: float
    y0: float
    dx: float = Field(gt=0)                # v5.14.0 V2 — 슬롯 간격(오른쪽 아래, 가이드 23 §6)
    dy: float = Field(gt=0)
    flag_R: float
    front: CascadeFrontRules
    back_scale: float = Field(gt=0, lt=1)
    back_h_drop: float = Field(ge=0)       # v5.14.0 V2 — 뒤 카드 높이 = (front.h − back_h_drop·back) × scale
    back_text_alpha: float = Field(gt=0, le=1)
    back_fade_px: float = Field(ge=0)      # D-0138 — 덮이는 경계 글자 알파 그라데이션 폭
    back_dim: float = Field(ge=0, lt=1)    # D-0138 — 층마다 어두워짐
    max_back: int = Field(ge=1)
    focus_sec: float = Field(gt=0)
    shift_sec: float = Field(gt=0)
    width_cap: float
    frame: CascadeFrame                     # v5.14.0 V2
    surface: CascadeSurface                 # v5.14.0 V2(D-0157 보강 3)

    @model_validator(mode="after")
    def _fits(self) -> "CascadeRules":
        need = (self.max_back + 1) * self.dx + self.front.w
        if need > self.width_cap:
            raise ValueError(f"cascade: (max_back+1)×dx+front.w = {need} > width_cap {self.width_cap}")
        if self.dx >= self.front.w * self.back_scale:
            raise ValueError("cascade: dx 가 뒤 카드 폭 이상이면 겹치지 않는다")
        if self.dy >= (self.front.h - self.back_h_drop) * self.back_scale:
            raise ValueError("cascade: dy 가 뒤 카드 높이 이상이면 겹치지 않는다")
        return self


class IslandColumnDetail(_Strict):
    """v7.4.0 D-0318·D-0319 ④ — 열 확대 인셋(island kind column_detail)."""

    w_ratio: float = Field(gt=0, lt=1)
    h_ratio: float = Field(gt=0, le=1)
    margin_px: float = Field(ge=0)
    side_order: list[Literal["left", "right"]] = Field(min_length=1)
    never_cover_focus_column: bool
    radius: float = Field(ge=0)
    fill_alpha: float = Field(gt=0, le=1)
    edge_alpha: float = Field(ge=0, le=1)
    pad_px: float = Field(ge=0)
    head_size: float = Field(ge=12)
    head_font: str
    text_size: float = Field(ge=12)
    text_font: str
    value_font: str
    dot_r: float = Field(ge=5)
    line_w: float = Field(gt=0)
    bar_w_ratio: float = Field(gt=0, le=1)
    band_alpha: float = Field(gt=0, le=1)
    band_ink_alpha: float = Field(gt=0, le=1)   # v7.4.0 — 무대 표면 열 띠(text 잉크)
    leader_w: float = Field(gt=0)
    leader_alpha: float = Field(gt=0, le=1)
    fade: tuple[float, float]
    slide_px: float = Field(ge=0)
    grow_sec: float = Field(ge=0)
    guide_bar_ratio: float = Field(gt=0, lt=1)   # v7.4.0 D-0321 §2-2
    label_gap_ratio: float = Field(ge=1)          # v7.4.0 D-0321 §3


class IslandStageSurface(_Strict):
    """v7.4.0 D-0328 — 팔레트 surface: stage(차트 = 무대, 테두리·머리 띠 없음)."""

    lane_label_size: float = Field(gt=0)
    lane_label_font: str
    end_pin_size: float = Field(gt=0)
    end_pin_font: str
    end_pin_dx: float = Field(ge=0)
    end_pin_r: float = Field(gt=0)
    plate_pad: float = Field(ge=0)
    source_lines: int = Field(ge=1)


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
    source_wrap_lines_max: int = Field(ge=1)   # v7.4.0 D-0265 §3 — 시간축 레인 출처 줄이 틀·상자 폭을 넘으면 " · " 경계에서 접는 최대 줄 수
    main_kinds: list[Literal["chart", "primitive", "photo", "clip", "article", "panel"]] = Field(min_length=1)
    card_only_max_sec: float = Field(gt=0)   # 주 아일랜드 없는 구간 상한(전환 허용)
    column_detail: IslandColumnDetail        # v7.4.0 D-0318 — 열 확대 인셋
    stage_surface: IslandStageSurface        # v7.4.0 D-0328 — 차트 = 무대



class GenrePromptRules(_Strict):
    """v4.4.0 D-0090 작업 1 — 장르 프롬프트 층(docs/handoff/20 §5·§6·§7·§9). 문장은 여기, 켜고 끄는 것은 장르 프로필."""

    base_genre: str
    narration: dict[str, str] = Field(min_length=1)
    acts_head: str = ""                                            # v7.4.0 D-0278 §3 — 템플릿 고정 막 머리 줄
    acts: dict[str, list[str]] = Field(default_factory=dict)       # v7.4.0 D-0278 §3 — 장르 이름 → 막 줄
    data_sources_by_genre: dict[str, list[str]] = Field(default_factory=dict)   # v7.4.0 D-0304 ② — 공통 data_sources 뒤 장르 보충 줄
    data_sources: list[str] = Field(min_length=1)
    rubric_extra: list[str] = Field(min_length=1)
    stage_grammar: dict[str, list[str]] = Field(min_length=1)


class FilingScale(_Strict):
    """v7.4.0 D-0278 §4.2(E3) — 공시 원단위 → 화면 단위 환산(값 = round(원값 × factor, digits))."""

    to: str
    factor: float = Field(gt=0)
    digits: int = Field(ge=0, le=4)


class DataRules(_Strict):
    """v4.3.0 D-0084 작업 1 — 데이터 레코드 허용 목록(docs/handoff/20 §5.1, schemas/data_models.py)."""

    units: list[str] = Field(min_length=1)
    licenses_allowed: list[str] = Field(min_length=1)
    unit_ton_pattern: str = ""   # v7.4.0 D-0241 §3(UF-122) — 화면 문자열에 남으면 [unit-ton-glyph] hard(빈 값 = 검사 안 함)
    unit_prefixes: list[str] = Field(min_length=1)   # v4.3.0 D-0087 보정 1
    sources_allowed: list[str] = Field(min_length=1)
    frequencies: list[Literal["monthly", "release", "quarterly", "daily"]] = Field(min_length=1)   # release = v4.4.0 scatter · quarterly·daily = v7.4.0 D-0278 §4.2
    transforms: dict[str, str] = Field(min_length=1)
    source_kinds: list[Literal["fetched", "press_cited", "filing"]] = Field(min_length=1)   # v7.3.0 D232 U4 · filing = v7.4.0 D-0278 §4.2(E3)
    filing_scales: dict[str, FilingScale] = Field(default_factory=dict)   # v7.4.0 D-0278 §4.2 — 공시 원단위 → 화면 단위
    price_outlier_pct: float = Field(default=10.0, gt=0)   # v7.4.0 — 일별 시세 하루 변동 상한(넘으면 cited 필수, [price-outlier])
    chart_null_note: str = Field(min_length=1)   # v7.4.0 D-0319 ① — 일별 종가 null → missing 사유
    series_dir: str

    @model_validator(mode="after")
    def _scales_to_units(self) -> "DataRules":
        bad = sorted(k for k, v in self.filing_scales.items() if v.to not in self.units)
        if bad:
            raise ValueError(f"data.filing_scales 의 to 단위가 data.units 에 없다: {bad}")
        if "filing" in self.source_kinds and ("filing" not in self.transforms or not self.filing_scales):
            raise ValueError("source_kinds filing 은 transforms.filing·filing_scales 가 있어야 한다")
        return self


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
    fade_sec: float = Field(ge=0.6, le=0.9)   # 20 §4.2 등장 0.4~0.6초 → v7.4.0 UF-159(D-0325) ×1.5 = 0.6~0.9초
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
    fade_sec: float = Field(ge=0.6, le=0.9)   # v7.4.0 UF-159(D-0325) ×1.5 — 옛 0.4~0.6초
    slide_px: float
    dot_stagger_sec: float = Field(ge=0)


class SiteDiagramLayout(_Strict):
    """v4.4.0 dmz_mine_2026 — site_diagram(사건 현장 개념도, 벡터) 레이아웃 토큰(설계 px·비율)."""

    x: float
    y: float
    w: float = Field(gt=0)
    h: float = Field(gt=0)
    radius: float
    fade_sec: float = Field(ge=0.6, le=0.9)   # v7.4.0 UF-159(D-0325) ×1.5 — 옛 0.4~0.6초
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


# ---------------------------------------------------------------- v5.7.0 스케치 계층(sketch/, D-0140 D130)


class SketchText(_Strict):
    """글자 한 종류 — 크기·글꼴(engine.style.FONT 키)·후광, 쓰는 곳에 따라 위치·간격."""

    size: float = Field(gt=0)
    font: str
    halo: Optional[float] = Field(default=None, ge=0)
    dx: Optional[float] = None
    dy: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    y0: Optional[float] = None
    alpha: Optional[float] = Field(default=None, gt=0, le=1)


class SketchCamera(_Strict):
    push_in: dict[str, float] = Field(min_length=1)   # spec kind → 숏 안 푸시인 비율
    hold_min_sec: float = Field(gt=0)
    move_min_sec: float = Field(gt=0)


class SketchFade(_Strict):
    open_sec: float = Field(gt=0)
    close_sec: float = Field(gt=0)
    black_min: float = Field(ge=0)
    min_alpha: float = Field(ge=0)
    win_in: float = Field(gt=0)
    win_out: float = Field(gt=0)
    note_in: float = Field(gt=0)
    note_out: float = Field(gt=0)
    end_dim_alpha: float = Field(gt=0, le=1)
    end_bg: RGB
    end_in_sec: float = Field(gt=0)
    date_in_t: float = Field(ge=0)
    date_alpha: float = Field(gt=0, le=1)
    date_line_alpha: float = Field(gt=0, le=1)
    date_halo: float = Field(ge=0)
    date_hide_lead_sec: float = Field(ge=0)
    date_hide_sec: float = Field(gt=0)


class SketchTextRules(_Strict):
    label: SketchText
    label_sub: SketchText
    label_edge_margin: float = Field(ge=0)
    label_reserve_pad: tuple[float, float, float, float]
    place: SketchText
    eez_name: SketchText
    hud: SketchText
    hud_value: SketchText
    hud_range: SketchText
    hud_note: SketchText
    ref_name: SketchText
    ref_distance: SketchText
    source: SketchText
    end_title: SketchText
    end_line: SketchText
    end_note: SketchText


class SketchTag(_Strict):
    size: float = Field(gt=0)
    font: str
    pad_w: float
    text_dx: float
    box_dy: float
    box_h: float = Field(gt=0)
    radius: float = Field(ge=0)
    fill_alpha: float = Field(ge=0, le=1)
    edge_alpha: float = Field(ge=0, le=1)
    edge_w: float = Field(gt=0)
    halo: float = Field(ge=0)
    reserve: tuple[float, float, float]
    reserve_min_alpha: float = Field(ge=0, le=1)


class SketchUnit(_Strict):
    prefix: str = ""
    suffix: str = ""
    check: bool

    @model_validator(mode="after")
    def _one(self) -> "SketchUnit":
        if not (self.prefix or self.suffix):
            raise ValueError("단위는 prefix 나 suffix 중 하나가 필요하다")
        return self


class SketchNumbers(_Strict):
    """화면 숫자 포맷터(SK-H1, D-0142 §1)."""

    approx_prefix: str
    range_sep: str
    clock_prefix: str
    units: dict[str, SketchUnit] = Field(min_length=1)


class SketchRights(_Strict):
    """SK-R1 허용 라이선스(D133)."""

    allowed_licenses: list[str] = Field(min_length=1)


class SketchEez(_Strict):
    appear_sec: float = Field(gt=0)
    min_alpha: float = Field(ge=0)
    fill_alpha: float = Field(ge=0, le=1)
    pulse_fill_alpha: float = Field(ge=0, le=1)
    edge_alpha: float = Field(ge=0, le=1)
    pulse_edge_alpha: float = Field(ge=0, le=1)
    edge_w: float = Field(gt=0)
    pulse_edge_w: float = Field(ge=0)
    dash: list[float] = Field(min_length=2)
    min_edge_len_deg: float = Field(ge=0)
    min_edge_step_deg: float = Field(ge=0)
    hatch_gap: float = Field(gt=0)
    hatch_w: float = Field(gt=0)
    hatch_alpha: float = Field(ge=0, le=1)
    dots_gap: float = Field(gt=0)
    dots_r: float = Field(gt=0)
    dots_row: float = Field(gt=0)
    dots_alpha: float = Field(ge=0, le=1)
    overlap_edge_alpha: float = Field(ge=0, le=1)
    overlap_edge_w: float = Field(gt=0)
    focus_in: float = Field(gt=0)
    focus_out: float = Field(gt=0)
    claim_grow_sec: float = Field(gt=0)
    claim_dense: int = Field(ge=2)
    claim_w: tuple[float, float]
    claim_ext_alpha: float = Field(ge=0, le=1)
    claim_ext_dash: list[float] = Field(min_length=2)
    vertex_half: float = Field(gt=0)
    label_delay: float = Field(ge=0)
    label_in: float = Field(gt=0)
    label_out: float = Field(gt=0)
    region_label_delay: float = Field(ge=0)
    claim_label_delay: float = Field(ge=0)
    ext_tag_delay: float = Field(ge=0)
    ext_tag_dx: float
    ext_tag_dy: float
    leader_alpha: float = Field(ge=0, le=1)
    leader_w: float = Field(gt=0)
    leader_dx: float
    leader_dy: float
    place_dot_r: float = Field(gt=0)
    place_box: tuple[float, float, float]


class SketchSensors(_Strict):
    grow_sec: float = Field(gt=0)
    appear_sec: float = Field(gt=0)
    sector_points: int = Field(ge=3)
    fill_alpha: tuple[float, float]
    edge_alpha: float = Field(ge=0, le=1)
    edge_w: float = Field(gt=0)
    tick_fracs: list[float]
    tick_points: int = Field(ge=2)
    tick_alpha: float = Field(ge=0, le=1)
    tick_w: float = Field(gt=0)
    tick_dash: list[float] = Field(min_length=2)
    scan_rate: float = Field(gt=0)
    scan_alpha: float = Field(ge=0, le=1)
    scan_w: float = Field(gt=0)
    site_r: float = Field(gt=0)
    site_w: float = Field(gt=0)
    undisclosed_offsets: list[tuple[float, float]] = Field(min_length=2)
    undisclosed_fill_alpha: float = Field(ge=0, le=1)
    undisclosed_edge_alpha: float = Field(ge=0, le=1)
    undisclosed_edge_w: float = Field(gt=0)
    undisclosed_dash: list[float] = Field(min_length=2)
    undisclosed_glow_r: float = Field(gt=0)
    undisclosed_glow_alpha: float = Field(ge=0, le=1)
    focus_dim: float = Field(ge=0, le=1)
    label_delay: float = Field(ge=0)
    label_in: float = Field(gt=0)
    label_out: float = Field(gt=0)
    full_out: float = Field(gt=0)
    full_min: float = Field(ge=0, lt=0.5)
    short_alpha: float = Field(ge=0, le=1)
    tag_dy: float
    ship_rings: int = Field(ge=1)
    ship_ring: tuple[float, float]
    ship_ring_rate: float = Field(gt=0)
    ship_ring_alpha: float = Field(ge=0, le=1)
    ship_ring_w: float = Field(gt=0)
    ship_shape: list[tuple[float, float]] = Field(min_length=3)
    ship_bridge: tuple[float, float, float, float]
    ship_label_delay: float = Field(ge=0)
    ship_label: tuple[float, float, float]


class SketchLaunchTrackImpact(_Strict):
    min_alpha: float = Field(ge=0)
    launch_appear: float = Field(gt=0)
    launch_rings: int = Field(ge=1)
    launch_ring: tuple[float, float]
    launch_ring_rate: float = Field(gt=0)
    launch_ring_alpha: float = Field(ge=0, le=1)
    launch_ring_w: float = Field(gt=0)
    launch_tri: tuple[float, float, float]
    launch_tri_w: float = Field(gt=0)
    launch_label_delay: float = Field(ge=0)
    launch_label_in: float = Field(gt=0)
    launch_label: tuple[float, float, float, float]
    track_w: float = Field(gt=0)
    track_points: int = Field(ge=2)
    head_r: float = Field(gt=0)
    head_stops: tuple[float, float, float]
    hud_x: float
    hud_y: tuple[float, float, float, float]
    hud_in: float = Field(gt=0)
    hud_out: float = Field(gt=0)
    hud_range_in: float = Field(gt=0)
    range_color: str
    impact_color: str
    impact_appear: float = Field(gt=0)
    flash_r: float = Field(gt=0)
    flash_decay: float = Field(gt=0)
    flash_min: float = Field(ge=0)
    flash_alpha: float = Field(ge=0, le=1)
    flash_rgb: RGB
    impact_grow_sec: float = Field(gt=0)
    impact_ring_step_deg: float = Field(gt=0)
    impact_fill_alpha: float = Field(ge=0, le=1)
    impact_edge_alpha: float = Field(ge=0, le=1)
    impact_dash: list[float] = Field(min_length=2)
    impact_edge_w: float = Field(gt=0)
    ref_delay: float = Field(ge=0)
    ref_in: float = Field(gt=0)
    ref_grow_sec: float = Field(gt=0)
    ref_line_points: int = Field(ge=3)
    ref_line_alpha: float = Field(ge=0, le=1)
    ref_line_w: float = Field(gt=0)
    ref_line_dash: list[float] = Field(min_length=2)
    ref_dot_r: float = Field(gt=0)
    ref_mid_delay: float = Field(ge=0)
    ref_mid_in: float = Field(gt=0)
    impact_label_delay: float = Field(ge=0)
    impact_label_in: float = Field(gt=0)
    impact_label: tuple[float, float, float]
    impact_tag_delay: float = Field(ge=0)
    impact_tag_in: float = Field(gt=0)
    pulse: tuple[float, float, float, float]


class SketchProfileText(_Strict):
    title: SketchText
    sub: SketchText
    tick: SketchText
    axis: SketchText
    ref: SketchText
    apex: SketchText
    note: SketchText
    who: SketchText
    row: SketchText


class SketchProfile(_Strict):
    rect: tuple[float, float, float, float]
    in_sec: float = Field(gt=0)
    min_alpha: float = Field(ge=0)
    slide_px: float = Field(ge=0)
    dim_alpha: float = Field(ge=0, le=1)
    bg: Color4
    radius: float = Field(ge=0)
    pad_x: float
    plot_inset: tuple[float, float, float, float]
    grid_w: float = Field(gt=0)
    zero_alpha: float = Field(ge=0, le=1)
    grid_alpha: float = Field(ge=0, le=1)
    alt_max_km: float = Field(gt=0)
    alt_ticks_km: list[float] = Field(min_length=2)
    range_ticks_km: list[float] = Field(min_length=2)
    range_max_km: float = Field(gt=0)
    tick_dx: float
    tick_dy: float
    axis_title_dy: float
    range_tick_dy: float
    axis_label_dy: float
    ref_color: str
    ref_alpha: float = Field(ge=0, le=1)
    ref_dash: list[float] = Field(min_length=2)
    ref_label_dx: float
    ref_label_dy: float
    grow_delay: float = Field(ge=0)
    grow_sec: float = Field(gt=0)
    curve_points: int = Field(ge=2)
    curve_w: float = Field(gt=0)
    apex_delay: float = Field(ge=0)
    apex_in: float = Field(gt=0)
    apex_r: float = Field(gt=0)
    apex_dx: float
    apex_dy: float
    rows_delay: float = Field(ge=0)
    rows_in: float = Field(gt=0)
    rows_dy: tuple[float, float, float]
    text: SketchProfileText


class SketchCard(_Strict):
    rect: tuple[float, float, float, float]
    fade_sec: float = Field(gt=0)
    min_alpha: float = Field(ge=0)
    slide_px: float = Field(ge=0)
    radius: float = Field(ge=0)
    inner_pad: float = Field(ge=0)
    inner_bottom: float = Field(ge=0)
    inner_radius: float = Field(ge=0)
    inner_bg: Color4
    img_pad: float = Field(ge=0)
    text_dx: float
    title: SketchText
    sub: SketchText
    credit: SketchText


class SketchGlobeKey(_Strict):
    pos_km: tuple[float, float, float]
    target_km: tuple[float, float, float]


class SketchGlobe(_Strict):
    """3D 지구본 전환편(D-0143). 글자·배치 = 설계 px, 선 굵기·대시·head_r = px_ref_height 장치 px 기준, 거리 km."""

    px_ref_height: float = Field(gt=0)
    k_max: float = Field(gt=1)
    fov_deg: float = Field(gt=0, lt=180)
    fov_side_deg: float = Field(gt=0, lt=180)
    km_per_deg: float = Field(gt=0)
    key_b: SketchGlobeKey
    key_c: SketchGlobeKey
    side_drift_km: float
    up_switch_sec: float = Field(ge=0)
    up_parallel: float = Field(gt=0, lt=1)
    z_eps: float = Field(gt=0)
    z_near_km: float = Field(gt=0)
    occlusion_margin_km: tuple[float, float]
    light: tuple[float, float, float]
    shade: tuple[float, float, float, float, float]
    rim_pow: float = Field(gt=0)
    rim_rgb: RGB
    rim_alpha: float = Field(ge=0, le=1)
    space_rgb: RGB
    atmos_rgb: RGB
    atmos_alpha: float = Field(ge=0, le=1)
    atmos_height: float = Field(gt=0)
    atmos_pow: float = Field(gt=0)
    texture_tiers: list[str] = Field(min_length=1)
    tex_lat_clip: float = Field(gt=0, lt=90)
    tex_edge_deg: float = Field(ge=0)
    glow_layers: list[tuple[float, float]] = Field(min_length=1)
    plain_alpha: float = Field(ge=0, le=1)
    border_lon: tuple[float, float]
    border_lat: tuple[float, float]
    border_cut_box: tuple[float, float, float, float]
    border_cut_eps: float = Field(gt=0)
    border_max_pts: int = Field(ge=2)
    border_rgb: RGB
    border_alpha: float = Field(ge=0, le=1)
    border_w: float = Field(gt=0)
    eez_min_pts: int = Field(ge=2)
    eez_alpha: float = Field(ge=0, le=1)
    eez_w: float = Field(gt=0)
    eez_dash: list[float] = Field(min_length=2)
    volume_az_n: int = Field(ge=2)
    volume_el_n: int = Field(ge=2)
    north_ref_deg: float = Field(gt=0)
    volume_in: tuple[float, float]
    volume_lower_alpha: tuple[float, float]
    volume_upper_alpha: tuple[float, float]
    volume_edge_alpha: tuple[float, float]
    volume_edge_w: float = Field(gt=0)
    volume_mid_alpha: float = Field(ge=0, le=1)
    volume_mid_w: float = Field(gt=0)
    volume_mid_dash: list[float] = Field(min_length=2)
    fade_open: float = Field(gt=0)
    fade_close: float = Field(gt=0)
    handoff_rate: float = Field(ge=0)
    track_w: tuple[float, float]
    track_alpha_side: float = Field(ge=0, le=1)
    alt_delay: float = Field(ge=0)
    alt_in: float = Field(gt=0)
    curtain_step: int = Field(ge=1)
    curtain_alpha: float = Field(ge=0, le=1)
    curtain_w: float = Field(gt=0)
    preview_alpha: float = Field(ge=0, le=1)
    preview_w: float = Field(gt=0)
    preview_dash: list[float] = Field(min_length=2)
    flown_w: float = Field(gt=0)
    head_r: float = Field(gt=0)
    label_delay: float = Field(ge=0)
    label_in: float = Field(gt=0)
    label: SketchText
    label_sub: SketchText
    label_launch: tuple[float, float]
    label_impact: tuple[float, float]
    label_apex: tuple[float, float]
    radar_label: tuple[float, float, float, float]
    panel_rect: tuple[float, float, float, float, float, float]
    panel_radius: float = Field(ge=0)
    panel_alpha: float = Field(ge=0, le=1)
    panel_in: tuple[float, float]
    panel_title: SketchText
    panel_rows: tuple[float, float]
    panel_dot: tuple[float, float, float]
    panel_name: SketchText
    panel_dist: SketchText
    panel_alt: SketchText
    panel_note: SketchText
    panel_note2: SketchText
    hud_x: float
    hud_y: tuple[float, float]
    hud_in: tuple[float, float]
    notes_x: float
    notes_y: tuple[float, float]
    notes_alpha: float = Field(ge=0, le=1)
    notes_in: float = Field(gt=0)
    notes_halo: float = Field(ge=0)


class SketchSymbol(_Strict):
    w: float = Field(gt=0)
    h: float = Field(gt=0)
    fill_alpha: float = Field(ge=0, le=1)
    edge_alpha: float = Field(ge=0, le=1)
    edge_w: float = Field(gt=0)
    mark_w: float = Field(gt=0)
    armor_rx: float = Field(gt=0)
    armor_ry: float = Field(gt=0)
    pop: float = Field(ge=0)
    pop_sec: float = Field(gt=0)


class SketchCampaignRiver(_Strict):
    rgb: RGB
    minor: tuple[float, float]
    major: tuple[float, float]


class SketchFront(_Strict):
    axis_color: str
    soviet_color: str
    axis_w: float = Field(gt=0)
    soviet_w: float = Field(gt=0)
    offset_px: float
    dash: list[float] = Field(min_length=2)


class SketchPocket(_Strict):
    color: str
    fill_alpha: float = Field(ge=0, le=1)
    hatch_alpha: float = Field(ge=0, le=1)
    hatch_gap: float = Field(gt=0)
    hatch_w: float = Field(gt=0)


class SketchArrow(_Strict):
    spline: int = Field(ge=2)
    half: tuple[float, float]          # 꼬리 반폭, 머리 쪽 추가 반폭
    tip: float = Field(gt=0)
    wing: float = Field(gt=0)
    alpha: tuple[float, float]         # 꼬리, 머리
    edge_rgb: RGB
    edge_alpha: float = Field(ge=0, le=1)
    edge_w: float = Field(gt=0)
    appear: float = Field(gt=0)
    label_from: float = Field(ge=0, le=1)
    label_in: float = Field(gt=0)
    label_out: float = Field(gt=0)
    max_step_px: float = Field(ge=0)   # v5.12.0 — 성장 끝점 이동 상한 여유(호 길이 보간, D-0154)


class SketchPlace(_Strict):
    size: float = Field(gt=0)
    font: str
    halo: float = Field(ge=0)
    alpha: float = Field(ge=0, le=1)
    dot_r: float = Field(gt=0)
    dx: float
    dy: float
    in_sec: float = Field(gt=0)
    probe: tuple[float, float]


class SketchRiverLabel(_Strict):
    size: float = Field(gt=0)
    font: str
    alpha: float = Field(ge=0, le=1)
    spacing: float = Field(ge=0)


class SketchCampaignTag(_Strict):
    size: float = Field(gt=0)
    font: str
    pad_w: float
    text_dx: float
    text_dy: float
    box_dy: float
    box_h: float = Field(gt=0)
    radius: float = Field(ge=0)
    bg_alpha: float = Field(ge=0, le=1)
    edge_alpha: float = Field(ge=0, le=1)
    edge_w: float = Field(gt=0)


class SketchLegend(_Strict):
    x: float
    y: float
    box: tuple[float, float, float, float]
    radius: float = Field(ge=0)
    alpha: float = Field(ge=0, le=1)
    col_dx: float
    row_dy: float
    sym_dx: float
    sym_dy: float
    symbol_scale: float = Field(gt=0)
    label_dx: float
    caption_dy: float


class SketchPincer(_Strict):
    flash_r: float = Field(gt=0)
    flash_decay: float = Field(gt=0)
    flash_rgb: RGB
    flash_alpha: float = Field(ge=0, le=1)
    rings: int = Field(ge=1)
    ring: tuple[float, float]
    ring_rate: float = Field(gt=0)
    ring_alpha: float = Field(ge=0, le=1)
    ring_w: float = Field(gt=0)
    ring_color: str
    ring_in: float = Field(gt=0)
    ring_out: float = Field(gt=0)
    tag_dy: float
    tag_in: float = Field(gt=0)
    tag_out: float = Field(gt=0)
    tag_color: str
    box: tuple[float, float, float]


class SketchCampaignEnd(_Strict):
    x: float
    line_size: float = Field(gt=0)
    note_y: float


class SketchCampaign(_Strict):
    terrain_dim: Color4
    river: SketchCampaignRiver
    front: SketchFront
    pocket: SketchPocket
    symbol: SketchSymbol
    echelon: SketchText
    unit_name: SketchText
    light_name_rgb: RGB
    unit_in: float = Field(gt=0)
    unit_fade_sec: float = Field(gt=0)
    offscreen_px: float = Field(ge=0)
    unit_box: tuple[float, float, float]
    arrow: SketchArrow
    arrow_label: SketchText
    arrow_label_rgb: RGB
    place: SketchPlace
    place_sub: SketchText
    river_label: SketchRiverLabel
    tag: SketchCampaignTag
    legend: SketchLegend
    legend_label: SketchText
    legend_caption: SketchText
    pincer: SketchPincer
    source_alpha: float = Field(ge=0, le=1)
    end: SketchCampaignEnd
    date_delay: float = Field(ge=0)


class SketchChecks(_Strict):
    """D-0140 §4 · D-0141 — 스케치 결정적 검사 임계."""

    max_dlogw_per_frame: float = Field(gt=0)
    max_d2logw_per_frame: float = Field(gt=0)
    max_d3_per_frame: float = Field(gt=0)   # v5.21.9 D-0191 §1-1 — |Δ³| 꺾임(본 엔진 camera_continuity 도 같은 키)
    georef_residual_deg: float = Field(gt=0)
    georef_city_deg: float = Field(ge=0)
    horizon_tol_km: float = Field(ge=0)
    label_overlap_px: float = Field(ge=0)
    approx_word: str = Field(min_length=1)
    approx_note_end_gap_sec: float = Field(ge=0)
    pocket_sliver_ratio: float = Field(ge=0, lt=1)
    seam_px: float = Field(gt=0)


class SketchRules(_Strict):
    """스케치 계층 화면 수치(D-0140 §3, D130). 사실·연출 값은 spec — 여기는 화면 수치만."""

    camera: SketchCamera
    fade: SketchFade
    text: SketchTextRules
    tag: SketchTag
    numbers: SketchNumbers
    rights: SketchRights
    eez: SketchEez
    sensors: SketchSensors
    launch_track_impact: SketchLaunchTrackImpact
    profile: SketchProfile
    card: SketchCard
    globe: SketchGlobe
    campaign: SketchCampaign
    checks: SketchChecks

    def fonts_used(self) -> set[str]:
        """규칙 안의 글꼴 이름 전부(engine.style.FONT 키 대조 — tests/test_sketch_rules)."""
        out: set[str] = set()

        def walk(m: BaseModel) -> None:
            for name in type(m).model_fields:
                v = getattr(m, name)
                if isinstance(v, BaseModel):
                    walk(v)
                elif name == "font" and isinstance(v, str):
                    out.add(v)
        walk(self)
        return out

class Palette(_Strict):
    """v7.4.0 D-0310 §1-1(UF-155) — 장르 화면 팔레트(rules palettes.<이름>). 값은 #RRGGBB."""

    bg: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    island: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    border: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    text: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    muted: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    accent: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    up: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    down: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    surface: Optional[Literal["stage"]] = None   # v7.4.0 D-0328 — 차트 = 무대(rules island.stage_surface)
    island_deep: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")   # v7.4.0 D-0322 정정 — 르포 card_deep(열 확대 인셋 바탕)
    grid_alpha: Optional[float] = Field(default=None, gt=0, le=1)   # 시간축 격자선 알파 상한(르포 ≤ 0.06)
    zero_alpha: Optional[float] = Field(default=None, gt=0, le=1)   # 막대·쌓임 레인 0 기준선 알파(르포 0.55)
    map_land: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    map_water: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    map_boundary: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")


class VideoRules(_Strict):
    """`rules/video_rules.yaml` 최상위 모델."""

    schema_version: int
    rules_version: str
    banned_phrases: BannedPhrases
    balance_principles: list[str]
    direction_grammar: list[str] = Field(min_length=1)   # v4.7.0 D-0104 D2(a) — 연출 문법(프롬프트 {{RULES.direction_grammar}})
    script_grammar: ScriptGrammar          # v5.5.0 — 원고 서술 규약
    transition: TransitionRules            # v7.4.0 D-0229 §2.2(UF-105) — 시점 전환 장치
    tempo: TempoRules                      # v7.4.0 D-0229 §2.9(UF-104·115) — 템포·막 구조
    script_vocab: ScriptVocab              # v7.4.0 D-0229 §2.8(UF-108·114) — 원고 어휘 린트
    source_note: SourceNote                # v5.6.0 — 참조 출처 화면 표기
    route_frame: RouteFrame = Field(default_factory=RouteFrame)   # v5.6.0 RENDER-AP-012
    route_speed: RouteSpeed = Field(default_factory=lambda: RouteSpeed(grow_speed_max_px_s=45.0))   # v7.4.0 D-0241 §4
    opening: OpeningRules                  # v5.6.0 RENDER-AP-016
    weapon_photo: WeaponPhotoRules         # v5.6.0 RENDER-AP-017
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
    palettes: dict[str, Palette] = Field(default_factory=dict)   # v7.4.0 D-0310(UF-155)
    fonts: Fonts
    labels: LabelRules
    geo: GeoRules
    credits: CreditRules
    registries: Registries
    audio: AudioRules
    preview: PreviewRules          # v3.3.0 — D-0056 F6
    animatic: AnimaticRules        # v4.9.0 — D-0108 콘티 판
    catalog: CatalogRules          # v7.4.0 — D-0251 카탈로그 판
    golden: GoldenRules            # v3.6.0 — D-0066 작업 4
    camera: CameraRules            # v3.3.0 — D-0056 작업 2
    stage: StageRules              # v4.1.0 — D-0076 작업 5
    qa_checks: QAChecks
    primitives: PrimitivesRules = Field(default_factory=PrimitivesRules)   # v4.2.0 D-0081
    stage_timeline: StageTimelineRules   # v4.3.0 — D-0084 작업 3·D-0085
    stage_backdrop: StageBackdropRules   # v5.1.0 — D-0121 §B·D-0123
    chart_world: ChartWorldRules   # v7.4.0 — D-0251 §6.2-4
    reference_clip: ReferenceClipRules   # v7.4.0 — D-0274 §2⑤
    island: IslandRules                  # v5.1.0 — D-0123 §1·D-0126
    cascade: CascadeRules                # v5.2.0 — 겹침 카드(사용자 재구성 2026-10-01, v5.3.0 D-0139 채택)
    quote_center: QuoteCenterRules       # v5.3.1 — 인물 발언 중앙 인용(시안, valdai-2026 한정)
    flight: FlightRules                  # v7.3.0 — 비행·착탄·위성 인셋(D-0206)
    border_glow: BorderGlowRules         # v5.3.1 — 국경선 글로우(시안, direction stage_config.mercator.border_glow)
    data: DataRules                # v4.3.0 — D-0084 작업 1
    genre_prompt: GenrePromptRules  # v4.4.0 — D-0090 작업 1
    bundle: BundleRules            # v3.5.0 — D-0063 작업 4
    provenance: ProvenanceRules
    sketch: SketchRules                  # v5.7.0 — 스케치 계층 화면 수치(D-0140 D130)

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
