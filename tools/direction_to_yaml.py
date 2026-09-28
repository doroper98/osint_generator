"""옛 direction.py → direction.yaml 1회용 변환기 (v3.1.0, back_and_forth D-0047 작업 3, reports/phase6_9/inventory.md §2).

    python tools/direction_to_yaml.py <proj> [--out <proj>/direction.yaml] [--check]

direction.py 를 **기록용 Timebase**(앵커 호출을 기호로 돌려준다)로 실행해 `cam`·`dip`·`ev`·`sound` 호출을 앵커 식 그대로 옮긴다.
- 앵커 + 숫자 → `off` 목록(더한 순서 보존 — 부동소수 결과가 옛 연출과 비트 단위로 같다)
- 앵커 − 앵커 → `{span: [A, B]}`(길이)
- 모듈 상수 `PL`(이름 → 좌표) → `places`, 좌표 목록 상수(ROUTE 등) → `paths`, 이벤트 lon·lat 가 place 와 같으면 `at_place`
- 앵커끼리 곱셈·비교 등 다른 연산이 나오면 오류(사람 판단)
`--check`: 옛 연출과 새 YAML 을 같은 plan 으로 풀어 카메라 키·이벤트(타입별 순서)·sound 가 dict 단위로 같은지 본다.
옛 direction.py 실행 경로는 이 변환 뒤 삭제된다(D-0047 §0-1). 그 뒤 이 도구는 이력으로만 남는다.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


class ConvertError(RuntimeError):
    pass


class A:
    """기호 앵커: base(dict) + 차례로 더할 off 목록."""

    def __init__(self, base: dict, offs: list[float] | None = None) -> None:
        self.base, self.offs = base, list(offs or [])

    def __add__(self, x: object) -> "A":
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            return A(self.base, self.offs + [float(x)])
        raise ConvertError(f"앵커 + {x!r} 는 옮길 수 없다")

    __radd__ = __add__

    def __sub__(self, x: object) -> "A | Span":
        if isinstance(x, A):
            return Span(x, self)
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            return A(self.base, self.offs + [-float(x)])
        raise ConvertError(f"앵커 - {x!r} 는 옮길 수 없다")

    def __float__(self) -> float:
        raise ConvertError("앵커를 숫자로 쓰는 연산 — 옮길 수 없다(사람 판단)")

    def __lt__(self, other: object) -> bool:
        raise ConvertError("앵커 비교 연산 — 옮길 수 없다")

    __gt__ = __le__ = __ge__ = __lt__

    def dump(self) -> dict:
        d = dict(self.base)
        offs = [o for o in self.offs]
        if len(offs) == 1 and offs[0] != 0.0:
            d["off"] = offs[0]
        elif len(offs) > 1:
            d["off"] = offs
        return d


class Span:
    def __init__(self, a: A, b: A) -> None:
        self.a, self.b = a, b

    def dump(self) -> dict:
        return {"span": [self.a.dump(), self.b.dump()]}


class _Card:
    def __init__(self, kind: str) -> None:
        self.t0 = A({"card": kind})
        self.t1 = A({"card": kind, "edge": "end"})


class SymTimebase:
    """engine.timebase.Timebase 의 앵커 함수와 같은 이름·인자. 값 대신 기호를 돌려준다."""

    def __init__(self, scenes: list[str]) -> None:
        self.total = A({"total": True})
        self.scene_start = {s: A({"scene_start": s}) for s in scenes}

    def S(self, sid: str, off: float = 0.0) -> A:  # noqa: N802
        return A({"sid": sid}, [off])

    def E(self, sid: str, off: float = 0.0) -> A:  # noqa: N802
        return A({"sid": sid, "edge": "end"}, [off])

    def SC(self, scene: str) -> A:  # noqa: N802
        return A({"scene_start": scene})

    def SC_END(self, scene: str) -> A:  # noqa: N802
        return A({"scene_end": scene})

    def at_word(self, sid: str, word: str) -> A:
        return A({"word": {"sid": sid, "text": word}})

    def card(self, kind: str) -> _Card:
        return _Card(kind)


class RecDirector:
    """Director 와 같은 호출(cam·ev·dip)을 순서대로 기록한다."""

    def __init__(self) -> None:
        self.shots: list[dict] = []
        self.events: list[dict] = []

    def cam(self, t: object, lon: float, lat: float, w: float, dur: float = 3.0, mode: str = "move") -> None:
        self.shots.append(dict(at=t, mode=mode, dur=dur, camera=dict(lon=lon, lat=lat, w=w)))

    def ev(self, typ: str, t0: object, t1: object, **kw: object) -> dict:
        d: dict = dict(type=typ, start=t0, end=t1)
        if typ == "panel" or {"start", "end", "type"} & set(kw):   # 17 §2 — 패널 내용은 data 아래
            data = {k: v for k, v in kw.items() if k != "kind"}
            d.update({"kind": kw["kind"]} if "kind" in kw else {})
            d["data"] = data
        else:
            d.update(kw)
        self.events.append(d)
        return d

    def dip(self, t: object, lon: float, lat: float, w: float, under: bool = False) -> None:
        self.shots.append(dict(at=t, mode="dip", camera=dict(lon=lon, lat=lat, w=w), **({"under": True} if under else {})))


def _load_module(p: Path):  # noqa: ANN202
    spec = importlib.util.spec_from_file_location(f"direction_conv_{p.parent.name}", p)
    if spec is None or spec.loader is None:
        raise ConvertError(f"불러올 수 없음: {p}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)   # 1회용 변환 — 이 경로는 변환 뒤 저장소에서 사라진다(D-0047 §0-1)
    return mod


def _is_pt(v: object) -> bool:
    return isinstance(v, (tuple, list)) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)


def _dump(v: object, paths: dict[str, list]) -> Any:
    if isinstance(v, (A, Span)):
        return v.dump()
    if isinstance(v, (list, tuple)):
        if paths and all(_is_pt(x) for x in v) and v:
            for name, pts in paths.items():
                if [tuple(x) for x in v] == [tuple(p) for p in pts]:
                    return {"path": name}
        return [_dump(x, paths) for x in v]
    if isinstance(v, dict):
        return {k: _dump(x, paths) for k, x in v.items()}
    return v


def convert(proj: Path) -> dict:
    from script.plan import load_script  # noqa: PLC0415

    mod = _load_module(proj / "direction.py")
    scenes = [s.id for s in load_script(proj).scenes]
    tb = SymTimebase(scenes)
    d = RecDirector()
    import engine.camera as ec  # noqa: PLC0415 — direction.py 가 Director() 를 만든다 → 기록용으로 바꿔 끼운다
    orig = mod.Director
    mod.Director = RecDirector
    try:
        d = mod.direct(tb)
    finally:
        mod.Director = orig
    del ec
    places = {k: list(v) for k, v in getattr(mod, "PL", {}).items()}
    paths = {k.lower(): [list(p) for p in v] for k, v in vars(mod).items()
             if k.isupper() and k != "PL" and isinstance(v, list) and v and all(_is_pt(p) for p in v)}
    events = []
    for e in d.events:
        out = {}
        for k, v in e.items():
            out[k] = _dump(v, paths)
        pl = next((n for n, xy in places.items() if "lon" in e and "lat" in e and [e["lon"], e["lat"]] == xy), None)
        if pl is not None:
            out = {k: v for k, v in out.items() if k not in ("lon", "lat")}
            keys = list(out)
            i = keys.index("end") + 1
            out = dict(list(out.items())[:i] + [("at_place", pl)] + list(out.items())[i:])
        events.append(out)
    doc: dict = {"version": 1, "places": places, "paths": paths,
                 "shots": [_dump(s, {}) for s in d.shots], "events": events}
    if hasattr(mod, "sound"):
        doc["sound"] = _dump(mod.sound(tb), {})
    return doc


HEADER = """# direction.yaml — {name} 연출 (v3.1.0, docs/handoff/17 §2 문법, back_and_forth D-0047).
# 옛 direction.py 를 tools/direction_to_yaml.py 로 옮겼다(앵커 식·더한 순서 보존 → 옛 연출과 dict 단위 동일).
# 시각은 앵커로만 쓴다. `off` 가 목록이면 앞에서부터 차례로 더한다. `{{span: [A, B]}}` = B − A(초).
"""


def dump_yaml(doc: dict, name: str) -> str:
    from engine.direction import _Loader  # noqa: PLC0415 — 같은 bool 규칙(true/false 만)으로 써야 `off` 에 따옴표가 안 붙는다

    class _D(yaml.SafeDumper):
        pass

    _D.yaml_implicit_resolvers = _Loader.yaml_implicit_resolvers

    def _flow_small(dumper: yaml.SafeDumper, data: dict) -> yaml.Node:
        flow = all(not isinstance(v, (dict, list)) for v in data.values()) or set(data) <= {"sid", "off", "edge", "scene_start",
                                                                                           "scene_end", "word", "card", "total", "span"}
        return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=flow)

    def _flow_list(dumper: yaml.SafeDumper, data: list) -> yaml.Node:
        flow = all(not isinstance(v, (dict, list)) for v in data) or all(isinstance(v, list) and len(v) == 2 for v in data)
        return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=flow)

    _D.add_representer(dict, _flow_small)
    _D.add_representer(list, _flow_list)
    body = yaml.dump(doc, Dumper=_D, allow_unicode=True, sort_keys=False, width=160)
    return HEADER.format(name=name) + body


def check(proj: Path, yaml_path: Path) -> list[str]:
    """옛 연출과 새 YAML 을 같은 plan 으로 풀어 비교. 다른 곳 목록(없으면 [])."""
    from engine.direction import build, load_direction_doc  # noqa: PLC0415
    from engine.project import load_plan  # noqa: PLC0415
    from engine.registry import validate_events  # noqa: PLC0415
    from engine.timebase import Timebase  # noqa: PLC0415

    plan = load_plan(proj)
    mod = _load_module(proj / "direction.py")
    tb_old, tb_new = Timebase(plan), Timebase(plan)
    old = mod.direct(tb_old)
    keys, events, sound = build(load_direction_doc(yaml_path), tb_new)
    diffs: list[str] = []
    if old.keys != keys:
        diffs += [f"camera[{i}]: {a} ≠ {b}" for i, (a, b) in enumerate(zip(old.keys, keys)) if a != b] or ["카메라 키 개수"]
    ov, nv = validate_events(old.events), validate_events(events)
    for typ in sorted({e["type"] for e in ov} | {e["type"] for e in nv}):
        a = [e for e in ov if e["type"] == typ]
        b = [e for e in nv if e["type"] == typ]
        if a != b:
            diffs.append(f"events[{typ}]: " + next((f"#{i} {json.dumps(x, ensure_ascii=False, default=str)[:200]} ≠ {json.dumps(y, ensure_ascii=False, default=str)[:200]}"
                                                   for i, (x, y) in enumerate(zip(a, b)) if x != y), f"개수 {len(a)} ≠ {len(b)}"))
    if hasattr(mod, "sound"):
        so = mod.sound(tb_old)
        if so != sound:
            diffs.append(f"sound: {so} ≠ {sound}")
    if tb_old.word_anchors != tb_new.word_anchors:
        diffs.append("word_anchors 기록 순서·값이 다르다")
    return diffs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("proj", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    out = args.out or proj / "direction.yaml"
    if not args.check:
        out.write_text(dump_yaml(convert(proj), proj.name), encoding="utf-8")
        print(f"ok {out}")
    diffs = check(proj, out)
    print(json.dumps({"project": proj.name, "same": not diffs, "diffs": diffs}, ensure_ascii=False))
    return 0 if not diffs else 1


if __name__ == "__main__":
    raise SystemExit(main())
