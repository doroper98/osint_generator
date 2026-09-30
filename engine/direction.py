"""연출 결과물 `direction.yaml` — 스키마·로더 (v3.1.0, docs/handoff/17 §2, back_and_forth D-0047 작업 2).

선언형 YAML 이다. **코드를 실행하지 않는다**(옛 direction.py 의 exec_module 대체, 17 §2).
시각은 전부 앵커로 쓴다(02 §1). 앵커는 plan 이 바뀌면(목소리 교체 등) 따라 움직인다(D31).

앵커 문법 (17 §2 + 저장소 확장):
    {sid: open_0, off: 0.2}                 문장 시작 + off
    {sid: open_2, off: 0.6, edge: end}      문장 끝 + off
    {scene_start: ask, off: -0.2}           장면 시작
    {scene_end: open, off: 0}               장면 끝(다음 장면 시작 − 0.35, 마지막은 total)
    {word: {sid: ask_1, text: 독일}, off: 0} 단어 발음 시작(at_word, 03 §6.3)
    {card: title, edge: start, off: 2.9}    타이틀·엔딩 카드
    {total: true, off: 0}                   영상 끝
    {span: [A, B]}                          B − A (초, 길이 — 예: route grow)
    숫자                                      절대 초(쓰지 않는 것이 기본)
`off` 는 숫자 또는 숫자 목록(목록이면 앞에서부터 차례로 더한다 — 옛 연출의 식 순서를 그대로 보존).

문서 구성:
    version: 1
    places: {hormuz: [56.35, 26.55], …}           이름표 좌표. 이벤트에서 `at_place: hormuz` → lon·lat
    paths:  {route: [[56.2, 26.45], …], …}        이름표 경로. 값 자리에 `{path: route}`
    genre:  geopolitics                             v4.2.0(D-0081 작업 3) — 장르 프로필(genres/<genre>.yaml). 없으면 geopolitics(provenance genre.declared false)
    stage_config: {timeline: {start, end, lanes?, compress?}}   v4.3.0(D-0084 작업 3) — 무대 설정. 레인 기본값 = 장르 프로필 stage.timeline.lanes
    stage:  mercator                                v4.1.0(D-0076 작업 4) — 주 무대. 없으면 장르 프로필의 stage.primary(provenance stage.declared false).
            있으면(숏 단위 stage 도) 장르 프로필 stage.primary·secondary 안이어야 한다(아니면 스키마 오류)
    shots:  [{at, mode: cut|move|dip, dur?, camera: {lon, lat, w}, under?, stage?}]   (dip = 1초 암전 + 한가운데 cut)
            shots[].stage = 이 숏의 무대(없으면 최상위 stage, D-0077). 등록 안 된 무대 이름 = 스키마 오류(P10)
    events: [{type, start, end, …필드}]           필드 값 어디든 앵커를 둘 수 있다(패널 내부 시각 등)
            패널은 17 §2 예시대로 내용 필드를 `data: {…}` 아래에 둔다(타임라인 패널의 start·end 날짜가 시각 키와 겹치지 않게).
            로더가 data 를 이벤트 필드로 펼친다. data 안 start·end 는 내용(날짜)이다. 그 밖에 바깥 키와 겹치면 오류.
    sound:  {bgm, intensity: [[앵커, 값], …], cues: [{kind, t: 앵커, v}]}   (D-0047 §0-2 — 17 §2 공백 보완)
이벤트 필드 검증은 `engine.registry.validate_events`(레지스트리·모델)가 하고, 엔티티·예약 영역·권리 점검은
`engine.project.load_project` 가 그대로 한다.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engine.camera import CamKey, cam
from engine.shots import ShotStage
from engine.timebase import Timebase

if TYPE_CHECKING:
    from collections.abc import Callable

    from engine.stage import Stage
    from schemas.genre_models import GenreProfile

ANCHOR_BASES: tuple[str, ...] = ("sid", "scene_start", "scene_end", "word", "card", "total", "span")
ANCHOR_KEYS: frozenset[str] = frozenset(ANCHOR_BASES) | {"off", "edge"}
DIP_HALF_SEC = 0.5   # Director.dip 과 같은 1초 암전(05 §2 dip_total_sec) — 한가운데 cut


class DirectionError(ValueError):
    """direction.yaml 문법·참조 오류(15 P6 — 조용히 넘기지 않는다)."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


def is_anchor(v: object) -> bool:
    return isinstance(v, dict) and bool(v) and set(v) <= ANCHOR_KEYS and sum(k in v for k in ANCHOR_BASES) == 1


class Camera(_Strict):
    """지도: lon·lat 또는 place. 시간축(v4.3.0 D-0085): date(YYYY-MM-DD) + 선택 lane(레인 id), w = 화면이 덮는 일수.
    어느 키를 쓸 수 있는지는 숏의 무대가 정한다(Direction 검사 — 다른 무대의 키 = 오류, P10)."""

    lon: Optional[float] = None
    lat: Optional[float] = None
    place: Optional[str] = None
    date: Optional[str] = None
    lane: Optional[str] = None
    w: Optional[float] = Field(default=None, gt=0)   # v5.1.0 D-0123 — backdrop 무대 카메라 `{}`(이동 없음)는 w 도 없다

    @model_validator(mode="after")
    def _where(self) -> "Camera":
        kinds = [self.place is not None, self.lon is not None or self.lat is not None, self.date is not None]
        if sum(kinds) == 0 and self.w is None and self.lane is None:
            return self   # backdrop 무대 `{}` — 무대 앵커 키 검사(Direction)가 다른 무대의 빈 카메라를 막는다(P10)
        if sum(kinds) != 1:
            raise ValueError("camera 는 lon·lat · place · date(시간축) 중 하나(backdrop 무대는 빈 카메라 {})")
        if self.w is None:
            raise ValueError("camera w 가 없다(backdrop 무대의 빈 카메라 {} 만 w 없음)")
        if kinds[1] and (self.lon is None or self.lat is None):
            raise ValueError("camera lon·lat 은 둘 다")
        if self.lane is not None and self.date is None:
            raise ValueError("camera lane 은 date 와 함께(시간축)")
        return self

    def keys(self) -> set[str]:
        """이 카메라가 쓴 앵커 키(place 는 지도 lon·lat, 빈 카메라 = 없음)."""
        if self.w is None:
            return set()
        if self.date is not None:
            return {"date"} | ({"lane"} if self.lane is not None else set())
        return {"lon", "lat"}


def _registered_stage(v: Optional[str]) -> Optional[str]:
    if v is not None:
        from engine.stage import stage_class  # noqa: PLC0415

        stage_class(v)   # 미등록·미구현 = StageError(ValueError) → 스키마 오류(P10)
    return v


class Shot(_Strict):
    at: Union[float, dict[str, Any]]
    mode: Literal["cut", "move", "dip"]
    dur: float = 3.0
    camera: Camera
    under: bool = False
    scene: Optional[str] = None   # 읽는 사람용 표시(검증 안 함)
    stage: Optional[str] = None   # v4.1.0 D-0077 — 이 숏의 무대(없으면 최상위 stage)
    reason: Optional[str] = None  # v4.3.0 D-0084 작업 3 — 시간축에서 왼쪽으로 되돌아가는 이유(있으면 timeline_backtrack 경고 없음, 20 §6)

    @field_validator("stage")
    @classmethod
    def _stage(cls, v: Optional[str]) -> Optional[str]:
        return _registered_stage(v)

    @field_validator("at")
    @classmethod
    def _anchor(cls, v: object) -> object:
        if not isinstance(v, (int, float)) and not is_anchor(v):
            raise ValueError(f"shot.at 은 앵커 또는 숫자: {v!r}")
        return v


class SoundCue(_Strict):
    kind: str
    t: Union[float, dict[str, Any]]
    v: float


class BgmSegment(_Strict):
    """곡 교체(v3.4.0 D-0060 작업 5, 10 §7-3): `from` 앵커부터 이 곡. 경계에서 rules audio.crossfade_sec 교차 페이드."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    from_: Union[float, dict[str, Any]] = Field(default=0, alias="from")

    @field_validator("id")
    @classmethod
    def _registered(cls, v: str) -> str:
        from audio.registry import track  # noqa: PLC0415

        track(v)   # 없는 id·파일명 = BgmError(ValueError) → 스키마 오류
        return v


class Sound(_Strict):
    # v3.4.0 — BGM 레지스트리 id(assets/audio/bgm/registry.yaml) 하나 또는 [{id, from: 앵커}] 목록(곡 교체).
    # 문자열 하나 = 목록 하나(from 0)와 같다. 없는 id = 오류(P10). null = 음악 없음(명시 상태, F1)
    bgm: Union[str, list[BgmSegment], None]
    intensity: list[tuple[Union[float, dict[str, Any]], float]]
    cues: list[SoundCue] = Field(default_factory=list)

    @field_validator("bgm")
    @classmethod
    def _registered(cls, v: Union[str, list[BgmSegment], None]) -> Union[str, list[BgmSegment], None]:
        from audio.registry import track  # noqa: PLC0415

        if isinstance(v, str):
            track(v)   # 없는 id·파일명 = BgmError(ValueError) → 스키마 오류
        elif isinstance(v, list):
            if not v:
                raise ValueError("sound.bgm 목록이 비었다 — 음악이 없으면 null")
            if v[0].from_ != 0:
                raise ValueError("sound.bgm 목록의 첫 곡은 from 0(영상 시작)")
        return v

    def segments(self) -> list[BgmSegment]:
        if self.bgm is None:
            return []
        return [BgmSegment(id=self.bgm)] if isinstance(self.bgm, str) else list(self.bgm)

    def music_ids(self) -> set[str]:
        return {s.id for s in self.segments()}


class Direction(_Strict):
    """direction.yaml 최상위 모델(17 §2)."""

    version: Literal[1] = 1
    genre: Optional[str] = None   # v4.2.0 D-0081 작업 3 — 장르 프로필(없으면 genres.load.DEFAULT_GENRE, declared false)
    stage: Optional[str] = None   # v4.1.0 D-0076 작업 4 — 주 무대(없으면 장르 프로필 stage.primary, declared false)
    stage_reason: Optional[str] = None   # v5.1.0 D-0123 §2 — 장르 기본 무대(default_stage)와 다른 무대를 고른 이유(없으면 checks stage_choice warning)
    stage_config: dict[str, dict[str, Any]] = Field(default_factory=dict)   # v4.3.0 D-0084 작업 3 — 무대 이름 → 설정
    places: dict[str, tuple[float, float]] = Field(default_factory=dict)
    paths: dict[str, list[tuple[float, float]]] = Field(default_factory=dict)
    shots: list[Shot] = Field(min_length=1)
    events: list[dict[str, Any]]
    sound: Optional[Sound] = None

    @field_validator("stage")
    @classmethod
    def _stage(cls, v: Optional[str]) -> Optional[str]:
        return _registered_stage(v)

    @field_validator("genre")
    @classmethod
    def _genre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            from genres.load import load_genre  # noqa: PLC0415

            load_genre(v)   # 없는 장르·프로필 오류 = GenreError(ValueError) → 스키마 오류(P10)
        return v

    def genre_name(self) -> str:
        from genres.load import DEFAULT_GENRE  # noqa: PLC0415

        return self.genre or DEFAULT_GENRE

    def genre_profile(self) -> "GenreProfile":
        from genres.load import load_genre  # noqa: PLC0415

        return load_genre(self.genre_name())

    def main_stage(self) -> str:
        return self.stage or self.genre_profile().stage.primary

    def default_stage(self) -> str:
        """장르 기본 무대(v5.1.0 D-0123 §2 `default_stage`) = 장르 프로필 stage.primary — 같은 값을 두 곳에 두지 않는다(P3)."""
        return self.genre_profile().stage.primary

    def stage_choice(self) -> list[str]:
        """주 무대를 장르 기본과 다르게 골랐는데 stage_reason 이 없으면 한 줄(checks stage_choice warning). 코드는 무대를 바꾸지 않는다(P8)."""
        if self.main_stage() != self.default_stage() and not self.stage_reason:
            return [f"[stage-choice] 주 무대 {self.main_stage()!r} ≠ 장르 {self.genre_name()!r} 기본 무대 {self.default_stage()!r} — "
                    "direction stage_reason 에 이유를 적는다"]
        return []

    def shot_stage(self, s: "Shot") -> str:
        return s.stage or self.main_stage()

    def stage_settings(self, name: str) -> Optional[dict[str, Any]]:
        """무대 설정 = 장르 프로필 stage.<이름> 기본값 위에 direction stage_config.<이름>(v4.3.0). 지도는 None."""
        if name == "mercator":
            return self.stage_config.get(name) or None
        prof = self.genre_profile().stage.settings().get(name)
        base = prof.model_dump() if prof is not None and hasattr(prof, "model_dump") else dict(prof or {})
        return {**base, **self.stage_config.get(name, {})}

    def stage_configs(self) -> dict[str, dict[str, Any]]:
        names = {self.main_stage()} | {self.shot_stage(s) for s in self.shots}
        return {n: c for n in names if (c := self.stage_settings(n)) is not None}

    @model_validator(mode="after")
    def _events(self) -> "Direction":
        errs: list[str] = []
        for i, e in enumerate(self.events):
            if "type" not in e or "start" not in e or "end" not in e:
                errs.append(f"events[{i}]: type·start·end 필수")
            if "t0" in e or "t1" in e:
                errs.append(f"events[{i}]: t0·t1 대신 start·end 앵커를 쓴다")
            if "data" in e and (not isinstance(e["data"], dict) or set(e["data"]) & (set(e) - {"data", "start", "end"})):
                errs.append(f"events[{i}]: data 는 dict 이고 바깥 키와 겹치면 안 된다")
            if "at_place" in e and e["at_place"] not in self.places:
                errs.append(f"events[{i}]: at_place {e['at_place']!r} 가 places 에 없다")
        for i, s in enumerate(self.shots):
            if s.camera.place is not None and s.camera.place not in self.places:
                errs.append(f"shots[{i}]: camera.place {s.camera.place!r} 가 places 에 없다")
        allowed = self.genre_profile().stage.names()   # v4.2.0 D-0081 작업 3 — 무대는 장르 프로필 안에서만
        if self.stage is not None and self.stage not in allowed:
            errs.append(f"stage {self.stage!r} 가 장르 {self.genre_name()!r} 프로필 무대 {allowed} 밖이다")
        errs += [f"shots[{i}].stage {s.stage!r} 가 장르 {self.genre_name()!r} 프로필 무대 {allowed} 밖이다"
                 for i, s in enumerate(self.shots) if s.stage is not None and s.stage not in allowed]
        from engine.stage import stage_class  # noqa: PLC0415

        used = {self.main_stage()} | {self.shot_stage(s) for s in self.shots}
        errs += [f"stage_config {k!r} 는 이 연출이 쓰는 무대 {sorted(used)} 밖이다" for k in self.stage_config if k not in used]
        for i, s in enumerate(self.shots):   # v4.3.0 D-0085 — 카메라 앵커 키는 숏 무대가 선언한 것만(P10)
            keys = set(getattr(stage_class(self.shot_stage(s)), "anchor_keys", ()))
            if not s.camera.keys() <= keys:
                errs.append(f"shots[{i}].camera 앵커 {sorted(s.camera.keys())} 가 무대 {self.shot_stage(s)!r} 앵커 {sorted(keys)} 밖이다")
        if errs:
            raise ValueError("; ".join(errs))
        return self


# ------------------------------------------------------------------ 앵커 해석
def _offs(a: dict) -> list[float]:
    off = a.get("off", 0.0)
    return [float(x) for x in off] if isinstance(off, list) else [float(off)]


def resolve_anchor(a: object, tb: Timebase) -> float:
    if isinstance(a, bool):
        raise DirectionError(f"앵커 자리에 bool: {a!r}")
    if isinstance(a, (int, float)):
        return float(a)
    if not is_anchor(a):
        raise DirectionError(f"앵커가 아니다: {a!r}")
    assert isinstance(a, dict)
    edge = a.get("edge", "start")
    if edge not in ("start", "end"):
        raise DirectionError(f"edge 는 start|end: {a!r}")
    if "span" in a:
        pair = a["span"]
        if not (isinstance(pair, list) and len(pair) == 2):
            raise DirectionError(f"span 은 [A, B]: {a!r}")
        return resolve_anchor(pair[1], tb) - resolve_anchor(pair[0], tb)
    try:
        if "sid" in a:
            t = tb.E(a["sid"]) if edge == "end" else tb.S(a["sid"])
        elif "scene_start" in a:
            t = tb.SC(a["scene_start"])
        elif "scene_end" in a:
            t = tb.SC_END(a["scene_end"])
        elif "word" in a:
            w = a["word"]
            t = tb.at_word(w["sid"], w["text"])
        elif "card" in a:
            c = tb.card(a["card"])
            t = c.t1 if edge == "end" else c.t0
        else:
            t = tb.total
    except (KeyError, StopIteration, ValueError) as ex:
        raise DirectionError(f"앵커 참조 오류 {a!r}: {ex}") from ex
    for o in _offs(a):
        t = t + o
    return t


def _resolve(v: object, tb: Timebase, doc: Direction) -> object:
    if is_anchor(v):
        return resolve_anchor(v, tb)
    if isinstance(v, dict):
        if set(v) == {"path"}:
            if v["path"] not in doc.paths:
                raise DirectionError(f"path {v['path']!r} 가 paths 에 없다")
            return [tuple(p) for p in doc.paths[v["path"]]]
        return {k: _resolve(x, tb, doc) for k, x in v.items()}
    if isinstance(v, list):
        return [_resolve(x, tb, doc) for x in v]
    return v


def _where(c: Camera, doc: Direction) -> dict[str, Any]:
    """카메라 앵커 → stage.to_world 인자(지도 lon·lat, 시간축 date·lane?)."""
    if c.place is not None:
        lon, lat = doc.places[c.place]
        return {"lon": lon, "lat": lat}
    if c.date is not None:
        return {"date": c.date, **({"lane": c.lane} if c.lane is not None else {})}
    if c.w is None:
        return {}   # backdrop 빈 카메라(v5.1.0 D-0123)
    assert c.lon is not None and c.lat is not None
    return {"lon": c.lon, "lat": c.lat}


def _cam_w(s: Shot, stage: "Stage") -> float:
    """숏의 카메라 폭 — 빈 카메라(backdrop, v5.1.0 D-0123)는 무대 고정 폭(fixed_w). 다른 무대의 빈 카메라는 앵커 검사가 먼저 막는다."""
    if s.camera.w is not None:
        return s.camera.w
    fw = getattr(stage, "fixed_w", None)
    if fw is None:
        raise DirectionError(f"숏 {s.at!r}: 무대 {stage.name!r} 는 카메라 w 가 필요하다")
    return float(fw)


ISLAND_STAGE = "timeline"   # v5.1.0 D-0126 Q1 A — backdrop 주 무대에서 이 무대의 숏 = 차트 아일랜드 뷰포트 카메라


def is_island_shot(doc: Direction, s: Shot, main: str) -> bool:
    """주 무대 backdrop 의 `stage: timeline` 숏 = 차트 아일랜드 카메라(D-0126 Q1 A — "숏 무대 ≠ 주 무대"를 아일랜드 뷰포트로 좁힌다)."""
    return main == "backdrop" and doc.shot_stage(s) == ISLAND_STAGE


def island_keys(doc: Direction, tb: Timebase, chart_stage: "Stage") -> list[CamKey]:
    """차트 아일랜드 뷰포트 카메라 키(시간축 월드 좌표, w = 뷰포트 폭이 덮는 일수). 주 무대가 backdrop 이 아니면 []."""
    keys: list[CamKey] = []
    for s in doc.shots:
        if not is_island_shot(doc, s, doc.main_stage()):
            continue
        t = resolve_anchor(s.at, tb)
        xy = chart_stage.to_world(**_where(s.camera, doc))
        keys.append(cam(t, *xy, _cam_w(s, chart_stage), 0 if s.mode == "dip" else s.dur, "cut" if s.mode == "dip" else s.mode))
    return keys


def build(doc: Direction, tb: Timebase, stage: "Stage") -> tuple[list[CamKey], list[dict], Optional[dict]]:
    """Direction → (카메라 키, 이벤트 dict, sound dict). 옛 Director 와 같은 모양.
    카메라 앵커(lon·lat)는 stage.to_world 로만 월드 좌표가 된다(v4.1.0 D-0076 작업 3). 이벤트의 앵커는 그대로 두고
    load_project 가 검증 뒤 engine.stage.attach_world 로 월드 좌표를 붙인다."""
    keys: list[CamKey] = []
    dips: list[dict] = []
    for s in doc.shots:
        if is_island_shot(doc, s, stage.name):
            continue   # v5.1.0 D-0126 Q1 A — 차트 아일랜드 뷰포트 카메라(island_keys)
        if doc.shot_stage(s) != stage.name:
            raise DirectionError(f"숏 {s.at!r} 의 무대 {doc.shot_stage(s)!r} ≠ 주 무대 {stage.name!r} — 아일랜드 없는 보조 무대 렌더는 아직 없다"
                                 "(G3·G12 D-0126 Q7, docs/handoff/20 §12). 무대 연속성 검사(checks stage_continuity)는 shot_stages 로 따로 본다")
        t = resolve_anchor(s.at, tb)
        anchor = _where(s.camera, doc)
        if s.mode == "dip":
            dips.append(dict(type="dip", t0=t - DIP_HALF_SEC, t1=t + DIP_HALF_SEC, **({"under": True} if s.under else {})))
            keys.append(cam(t, *stage.to_world(**anchor), _cam_w(s, stage), 0, "cut"))
        else:
            keys.append(cam(t, *stage.to_world(**anchor), _cam_w(s, stage), s.dur, s.mode))
    events: list[dict] = []
    for e in doc.events:
        d: dict = {"type": e["type"], "t0": resolve_anchor(e["start"], tb), "t1": resolve_anchor(e["end"], tb)}
        for k, v in e.items():
            if k in ("type", "start", "end"):
                continue
            if k == "at_place":
                d["lon"], d["lat"] = doc.places[v]
                continue
            if k == "data":
                d.update({dk: _resolve(dv, tb, doc) for dk, dv in v.items()})
                continue
            d[k] = _resolve(v, tb, doc)
        events.append(d)
    sound = None
    if doc.sound is not None:
        sd = doc.sound
        bgm = sd.bgm if not isinstance(sd.bgm, list) else [dict(id=g.id, t=resolve_anchor(g.from_, tb)) for g in sd.bgm]
        sound = dict(bgm=bgm, intensity=[(resolve_anchor(t, tb), v) for t, v in sd.intensity],
                     cues=[dict(kind=c.kind, t=resolve_anchor(c.t, tb), v=c.v) for c in sd.cues])
    return keys, events + dips, sound


def shot_stages(doc: Direction, tb: Timebase, stages: "Callable[[str], Stage]") -> list[ShotStage]:
    """숏마다 (시각, 전환, 무대, 월드 x·y·w) — 무대 연속성 검사 입력(v4.1.0 D-0077). stages(이름) → 그 무대(StageSet.get)."""
    out: list[ShotStage] = []
    for s in doc.shots:
        name = doc.shot_stage(s)
        x, y = stages(name).to_world(**_where(s.camera, doc))
        out.append(ShotStage(t=resolve_anchor(s.at, tb), mode=s.mode, stage=name, x=x, y=y, w=_cam_w(s, stages(name)), reason=s.reason,
                             island=is_island_shot(doc, s, doc.main_stage())))
    return out


def _route_names(e: dict[str, Any]) -> list[str]:
    """route 이벤트가 가진 이름 — label·{path: 이름}(data 아래도)."""
    f = {**e, **(e.get("data") or {})}
    pts = f.get("pts")
    return [str(v) for v in (f.get("label"), pts.get("path") if isinstance(pts, dict) else None) if v]


def boundary_routes(doc: Direction, names: list[str]) -> list[str]:
    """경계선 이름을 단 경로(v4.7.0 back_and_forth D-0107 D2(b), M8 재발 방지) — `[boundary-as-route]` 한 줄씩.
    names = rules geo.boundary_names(부분 일치, 대소문자 무시). 경계선은 지도 경계 레이어가 그린다."""
    low = [n.lower() for n in names]

    def hit(s: str) -> Optional[str]:
        return next((n for n, k in zip(names, low) if k in s.lower()), None)

    out = [f"[boundary-as-route] paths {k!r} — 경계선 이름({n})을 단 경로. 경계선은 지도 경계 레이어가 그린다(route 금지)"
           for k in doc.paths if (n := hit(k))]
    for i, e in enumerate(doc.events):
        if e.get("type") != "route":
            continue
        found = next(((s, n) for s in _route_names(e) if (n := hit(s))), None)   # 이벤트당 한 줄(첫 일치)
        if found:
            out.append(f"[boundary-as-route] events[{i}] route {found[0]!r} — 경계선 이름({found[1]})을 단 route. 지도 경계선이 이미 있다")
    return out


def geo_unsourced(doc: Direction) -> list[dict[str, Any]]:
    """지도 좌표 중 출처(지명 사전·claim 위치)와 대조하지 않은 것(v4.7.0 D-0107 D2(b) — 지금은 warning, 사전·hard 는 G8).
    places(이름·lon·lat), paths(이름·점 수·양 끝), 인라인 좌표 marker·route(events[i]). 지도 무대가 아니면 호출하지 않는다."""
    out: list[dict[str, Any]] = [{"kind": "place", "name": k, "lonlat": [float(v[0]), float(v[1])]} for k, v in doc.places.items()]
    out += [{"kind": "path", "name": k, "points": len(v), "ends": [list(map(float, v[0])), list(map(float, v[-1]))]}
            for k, v in doc.paths.items() if v]
    for i, e in enumerate(doc.events):
        f = {**e, **(e.get("data") or {})}
        if e.get("type") == "marker" and "at_place" not in e and "lon" in f and "lat" in f:
            out.append({"kind": "marker", "name": f"events[{i}] {f.get('label') or ''}".strip(),
                        "lonlat": [float(f["lon"]), float(f["lat"])]})
        elif e.get("type") == "route" and isinstance(f.get("pts"), list) and f["pts"]:
            out.append({"kind": "route", "name": f"events[{i}] {f.get('label') or ''}".strip(), "points": len(f["pts"]),
                        "ends": [list(map(float, f["pts"][0])), list(map(float, f["pts"][-1]))]})
    return out


class _Loader(yaml.SafeLoader):
    """YAML 1.1 의 on/off/yes/no → bool 변환을 끈 안전 로더. 앵커 키 `off`(17 §2)가 False 로 바뀌지 않게 한다.
    true/false 만 bool 이다."""


_Loader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:bool"] for k, v in yaml.SafeLoader.yaml_implicit_resolvers.copy().items()
}
yaml.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
                           list("tTfF"), Loader=_Loader)


def yaml_load(text: str) -> object:
    """direction.yaml 전용 안전 로드(코드 실행 없음, off 키 보존)."""
    return yaml.load(text, Loader=_Loader)  # noqa: S506 — SafeLoader 하위 클래스


def load_direction_doc(path: Path) -> Direction:
    """direction.yaml → Direction. YAML 안전 로드만(코드 실행 없음)."""
    try:
        raw = yaml_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as ex:
        raise DirectionError(f"{path}: {ex}") from ex
    try:
        return Direction.model_validate(raw)
    except ValueError as ex:
        raise DirectionError(f"{path}: {ex}") from ex


__all__ = ["Direction", "DirectionError", "Shot", "Sound", "boundary_routes", "build", "geo_unsourced", "is_anchor", "load_direction_doc",
           "resolve_anchor", "shot_stages", "yaml_load"]
