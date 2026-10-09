"""MissileSpec — 미사일 발사 사건 스케치의 사실·연출 값(D-0140 §3, D-0142 §1).

화면 수치(px·알파·초 간격)는 `rules sketch:` 에 있고, 여기에는 좌표·시각·발표 수치·문구만 있다.
발표 수치는 `announced` 에 **숫자 + 단위**로 둔다. 화면 문자열은 `{기관.키}` 자리표시를 `sketch.missile.numbers` 의
포맷터 하나가 채운다(SK-H1 구현 지점). 스키마 단계 검사: SK-H2(approx → 불확실성 > 0), SK-H3(비공개 자산 태그·범위),
SK-H4(중첩 수역 청구국 색 ≥ 2).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field, model_validator

from sketch.common.spec import SketchSpec, _Strict

Anchor = Literal["l", "r", "c"]
LonLat = tuple[float, float]


class Num(_Strict):
    """발표·사양 수치 하나 — 값·단위(rules sketch.numbers.units 키)·'약' 여부."""

    v: float
    unit: str = Field(min_length=1)
    approx: bool = False


class Agency(_Strict):
    """발표 기관 — 고도 단면 패널에 나란히 같은 무게로(CONVENTIONS §2)."""

    who: str = Field(min_length=1)
    color: str = Field(min_length=1)               # engine.style 색 토큰 이름
    values: dict[str, Num] = Field(min_length=1)
    rows: list[str] = Field(min_length=1)          # 자리표시 문자열("거리 {jcs.range_km}")


class Launch(_Strict):
    label: str
    sub: str
    lon: float
    lat: float
    t: float = Field(ge=0)
    color: str


class RefPoint(_Strict):
    name: str
    lon: float
    lat: float


class TrackHud(_Strict):
    label: str                 # "비행 경과"
    range_line: str            # 착탄 뒤 발표 거리 줄(자리표시)
    note: str                  # 지상 투영 주석
    hold_sec: float = Field(ge=0)


class Impact(_Strict):
    label: str
    sub: str                   # 자리표시 허용
    tag: str
    tag_color: str


class Track(_Strict):
    """궤적·착탄. 착탄점 = 기준점에서 bearing_deg 방향 distance_km(발표). approx 이면 점이 아니라 반경 uncertainty_km 영역(SK-H2)."""

    ref: RefPoint
    bearing_deg: float
    distance_km: float = Field(gt=0)
    approx: bool
    uncertainty_km: float = Field(ge=0)
    flight_sec: float = Field(gt=0)
    t0: float = Field(ge=0)
    t1: float = Field(ge=0)
    hud: TrackHud
    impact: Impact

    @model_validator(mode="after")
    def _h2(self) -> "Track":
        if self.approx and self.uncertainty_km <= 0:
            raise ValueError("SK-H2 track.approx 인데 uncertainty_km ≤ 0 — 착탄은 점이 아니라 영역으로 그린다")
        if self.t1 <= self.t0:
            raise ValueError(f"track t1({self.t1}) ≤ t0({self.t0})")
        return self


class Sensor(_Strict):
    """탐지 자산. radar = 고정 레이더, ship = 이동 자산(위치는 예시, 범위 비공개). CONVENTIONS §3."""

    name: str
    sub: Optional[str] = None
    kind: Literal["radar", "ship"]
    lon: float
    lat: float
    location_public: bool
    range_km: Optional[float] = Field(default=None, gt=0)
    range_approx: bool = False
    az_width_deg: Optional[float] = Field(default=None, gt=0, le=360)
    bearing_deg: Optional[float] = None      # None = 발사 지점 방향
    el_deg: Optional[tuple[float, float]] = None   # 3D(S2)
    tag: Optional[str] = None
    color: str
    t: float = Field(ge=0)
    label_at: Optional[LonLat] = None        # radar 라벨 위치(ship 은 기호 옆)
    side: Literal["l", "r"] = "l"

    @model_validator(mode="after")
    def _h3(self) -> "Sensor":
        if self.kind == "radar" and not self.location_public and not self.tag:
            raise ValueError(f"SK-H3 {self.name}: 위치 비공개 레이더는 tag(예: '위치 비공개 · 범위는 개념도') 필수")
        if self.kind == "ship":
            if not self.tag:
                raise ValueError(f"SK-H3 {self.name}: 이동 자산은 tag(위치 예시·거리 비공개) 필수")
            if self.range_km is not None:
                raise ValueError(f"SK-H3 {self.name}: 이동 자산은 범위를 그리지 않는다(range_km: null)")
        if self.range_km is None and self.az_width_deg is not None:
            raise ValueError(f"SK-H3 {self.name}: range_km null 인데 az_width_deg 가 있다 — 범위 도형 없음")
        if self.kind == "radar" and self.range_km is not None and self.az_width_deg is None:
            raise ValueError(f"{self.name}: range_km 가 있으면 az_width_deg 필요")
        if self.kind == "radar" and self.label_at is None:
            raise ValueError(f"{self.name}: radar 는 label_at 필요")
        return self


class Nation(_Strict):
    color: str
    label: str
    label_at: LonLat
    t: float = Field(ge=0)


class Region(_Strict):
    """중첩 주장(overlap — 청구국 두 색 사선, SK-H4) 또는 공동 관리(joint — 합의 색 점무늬)."""

    code: str
    kind: Literal["overlap", "joint"]
    claimants: list[str] = Field(default_factory=list)
    color: Optional[str] = None              # joint 색
    t: float = Field(ge=0)
    label_t: Optional[float] = None          # 설명 라벨 시작(없으면 t)
    end: float
    label: str
    sub: str
    at: LonLat
    anchor: Anchor
    edge: bool = True                        # 테두리(서해 남북은 두 주장선이 경계를 그린다 → false)
    focus: Optional[tuple[float, float]] = None


class ExtTag(_Strict):
    text: str
    color: str


class ClaimLine(_Strict):
    code: str
    color: str
    dash: Optional[list[float]] = None
    t: float = Field(ge=0)
    end: float
    label: str
    sub: str
    at: LonLat
    anchor: Anchor
    approx: bool = False                     # SK-H5 — 보이는 동안 출처 줄 '개략'
    vertices: bool = False                   # 발표 꼭짓점 표시
    ext_tag: Optional[ExtTag] = None         # 연장선 끝 태그
    focus: Optional[tuple[float, float]] = None


class Place(_Strict):
    name: str
    lon: float
    lat: float


class Places(_Strict):
    t0: float
    t1: float
    items: list[Place] = Field(min_length=1)


class EezPrep(_Strict):
    """prep_eez 입력 — Marine Regions mrgid → (code, kind), 서해 남북 재분할 사실 값(개략, 사용자 확정 대기)."""

    wfs_url: str
    license: str
    keep: dict[int, tuple[str, Literal["eez", "overlap", "joint"]]]
    clip: tuple[float, float, float, float]
    west_box: tuple[float, float, float, float]
    west_codes: tuple[int, int]              # (남, 북) mrgid
    nll_approx: list[LonLat] = Field(min_length=2)
    nk1999_dms: list[tuple[tuple[float, float, float], tuple[float, float, float]]] = Field(min_length=2)
    anchor: LonLat


class Eez(_Strict):
    file: str
    nations: dict[str, Nation] = Field(min_length=1)
    labels_end: float
    regions: list[Region] = Field(default_factory=list)
    claim_lines: list[ClaimLine] = Field(default_factory=list)
    places: Optional[Places] = None
    pulse: Optional[str] = None              # 착탄 뒤 강조할 EEZ 나라 코드
    prep: EezPrep

    @model_validator(mode="after")
    def _h4(self) -> "Eez":
        for r in self.regions:
            if r.kind == "overlap":
                missing = [c for c in r.claimants if c not in self.nations]
                if missing:
                    raise ValueError(f"{r.code}: 청구국 {missing} 가 nations 에 없다")
                cols = {self.nations[c].color for c in r.claimants}
                if len(cols) < 2:
                    raise ValueError(f"SK-H4 {r.code}: 중첩 주장 수역은 청구국 색 ≥ 2 의 사선 — 지금 색 {sorted(cols)}")
            elif not r.color:
                raise ValueError(f"{r.code}: joint 는 color 필요")
        if self.pulse is not None and self.pulse not in self.nations:
            raise ValueError(f"pulse {self.pulse} 가 nations 에 없다")
        return self


class DimKey(_Strict):
    t: float
    d: float              # 더하는 양(음수 = 물러남)
    sec: float = Field(gt=0)


class Dim(_Strict):
    """장면별 초점 — 지금 이야기하는 층이 밝고 나머지는 물러난다."""

    eez: list[DimKey] = Field(default_factory=list)
    eez_labels_off: float
    sensors: list[DimKey] = Field(default_factory=list)
    sensors_focus_end: float
    sensors_labels_end: float


class Card(_Strict):
    media: str
    title: str
    sub: str
    t0: float
    t1: float
    crop: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)   # 비율 [x0, y0, x1, y1]
    rotate_deg: float = 0.0


class ProfileRef(_Strict):
    label: str            # 자리표시 {profile.ref_km}
    km: Num


class Profile(_Strict):
    t0: float
    t1: float
    title: str
    sub: str
    alt_axis: str
    range_axis: str
    curve: str            # 곡선 거리·정점을 가져올 announced 기관 키
    apex_label: str
    note: str
    reference: ProfileRef


class SourceNote(_Strict):
    text: str
    t0: float
    t1: float


class Notes(_Strict):
    source_lines: list[SourceNote] = Field(default_factory=list)
    end_title: str
    end_note: str
    end_sec: float = Field(gt=0)          # 엔딩 자료 카드 길이(끝에서)


class MissileSpec(SketchSpec):
    kind: Literal["missile"]
    launch: Launch
    track: Track
    announced: dict[str, Agency] = Field(min_length=1)
    sensors: list[Sensor] = Field(default_factory=list)
    eez: Eez
    card: Optional[Card] = None
    profile: Optional[Profile] = None
    dim: Dim
    notes: Notes
    sheet_times: list[float] = Field(min_length=1)

    @model_validator(mode="after")
    def _refs(self) -> "MissileSpec":
        if self.profile and self.profile.curve not in self.announced:
            raise ValueError(f"profile.curve {self.profile.curve} 가 announced 에 없다")
        if self.card and self.card.media not in {m.file for m in self.media}:
            raise ValueError(f"card.media {self.card.media} 가 media 목록에 없다(권리 기록 SK-R1)")
        bad = [s for s in self.sheet_times if not 0 <= s < self.duration_sec]
        if bad:
            raise ValueError(f"sheet_times {bad} 가 영상 길이 밖")
        return self
