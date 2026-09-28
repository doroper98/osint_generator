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
    shots:  [{at, mode: cut|move|dip, dur?, camera: {lon, lat, w}, under?}]   (dip = 1초 암전 + 한가운데 cut)
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
from typing import Any, Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engine.camera import CamKey, cam
from engine.timebase import Timebase

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
    lon: Optional[float] = None
    lat: Optional[float] = None
    place: Optional[str] = None
    w: float = Field(gt=0)

    @model_validator(mode="after")
    def _where(self) -> "Camera":
        if (self.place is None) == (self.lon is None or self.lat is None):
            raise ValueError("camera 는 lon·lat 또는 place 중 하나")
        return self


class Shot(_Strict):
    at: Union[float, dict[str, Any]]
    mode: Literal["cut", "move", "dip"]
    dur: float = 3.0
    camera: Camera
    under: bool = False
    scene: Optional[str] = None   # 읽는 사람용 표시(검증 안 함)

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


class Sound(_Strict):
    bgm: str
    intensity: list[tuple[Union[float, dict[str, Any]], float]]
    cues: list[SoundCue] = Field(default_factory=list)


class Direction(_Strict):
    """direction.yaml 최상위 모델(17 §2)."""

    version: Literal[1] = 1
    places: dict[str, tuple[float, float]] = Field(default_factory=dict)
    paths: dict[str, list[tuple[float, float]]] = Field(default_factory=dict)
    shots: list[Shot] = Field(min_length=1)
    events: list[dict[str, Any]]
    sound: Optional[Sound] = None

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


def _where(c: Camera, doc: Direction) -> tuple[float, float]:
    if c.place is not None:
        lon, lat = doc.places[c.place]
        return lon, lat
    assert c.lon is not None and c.lat is not None
    return c.lon, c.lat


def build(doc: Direction, tb: Timebase) -> tuple[list[CamKey], list[dict], Optional[dict]]:
    """Direction → (카메라 키, 이벤트 dict, sound dict). 옛 Director 와 같은 모양."""
    keys: list[CamKey] = []
    dips: list[dict] = []
    for s in doc.shots:
        t = resolve_anchor(s.at, tb)
        lon, lat = _where(s.camera, doc)
        if s.mode == "dip":
            dips.append(dict(type="dip", t0=t - DIP_HALF_SEC, t1=t + DIP_HALF_SEC, **({"under": True} if s.under else {})))
            keys.append(cam(t, lon, lat, s.camera.w, 0, "cut"))
        else:
            keys.append(cam(t, lon, lat, s.camera.w, s.dur, s.mode))
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
        sound = dict(bgm=sd.bgm, intensity=[(resolve_anchor(t, tb), v) for t, v in sd.intensity],
                     cues=[dict(kind=c.kind, t=resolve_anchor(c.t, tb), v=c.v) for c in sd.cues])
    return keys, events + dips, sound


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


__all__ = ["Direction", "DirectionError", "Shot", "Sound", "build", "is_anchor", "load_direction_doc", "resolve_anchor",
           "yaml_load"]
