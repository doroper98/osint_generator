"""프로젝트 로드 — plan·라벨·크레딧·자산·연출을 읽고 렌더 전 검사를 끝낸다 (v2.1.0).

프로젝트 폴더 구성(16 §4):
- 입력(추적): `script.yaml`, `direction.py`, `labels.yaml`, `credits.yaml`
- 생성물(gitignore): `plan.json`, `tts/`, `assets/`, `media/`, `prev/`, `out/`
검사 실패(레지스트리·스키마·권리·자산)는 렌더 시작 전 오류다(15 P6·P10, C9).
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import numpy as np

from engine.assets import Assets, load_labels
from engine.camera import CamKey, build_camera
from engine.context import RenderCtx
from engine.credits import load_credits
from engine.registry import validate_events
from engine.style import FPS
from engine.timebase import Timebase
from script.schema import Plan


class ProjectError(RuntimeError):
    pass


def load_direction(proj: Path) -> ModuleType:
    p = proj / "direction.py"
    if not p.exists():
        raise ProjectError(f"연출 파일 없음: {p}")
    spec = importlib.util.spec_from_file_location(f"direction_{proj.name}", p)
    if spec is None or spec.loader is None:
        raise ProjectError(f"연출 파일을 불러올 수 없음: {p}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "direct"):
        raise ProjectError(f"{p}: direct(tb) 함수가 없다")
    return mod


def load_plan(proj: Path) -> Plan:
    p = proj / "plan.json"
    if not p.exists():
        raise ProjectError(f"plan.json 없음 — 먼저 `python -m script.plan {proj}`")
    return Plan.model_validate(json.loads(p.read_text(encoding="utf-8")))


def _walk(o: object):  # noqa: ANN202
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from _walk(v)


def preflight(R: RenderCtx, events: list[dict]) -> list[str]:  # noqa: N803
    """권리·자산 점검. 문제 목록을 돌려준다(빈 목록 = 통과)."""
    A = R.assets  # noqa: N806
    errs: list[str] = []
    keys: set[str] = set()
    for e in events:
        for d in _walk(e):
            if "pid" in d and d["pid"] is not None:
                keys |= {f"portrait:{d['pid']}", f"flag43:{d['flag']}"}
                if d["pid"] not in A.rights.get("people", {}):
                    errs.append(f"권리 레지스트리에 인물 없음: {d['pid']} ({e['type']} t0={e['t0']:.2f})")
            elif "flag" in d and d["flag"] is not None:
                keys.add(f"flag11:{d['flag']}")
        if e["type"] == "badge" and e["kind"] == "emblem":
            keys.add(f"emblem:{e['img']}")
            if e["img"] not in A.rights.get("emblems", {}):
                errs.append(f"권리 레지스트리에 휘장 없음: {e['img']}")
        if e["type"] in ("photo", "cutout"):
            keys.add(f"media:{e['img']}")
        if e["type"] in ("photo", "clip", "cutout") and e["mid"] not in A.media:
            errs.append(f"미디어 레지스트리에 없음: mid={e['mid']} ({e['type']})")
    for k in sorted(keys):
        try:
            A.load_image(k)
        except Exception as ex:  # noqa: BLE001 — 모아서 한 번에 보고
            errs.append(str(ex))
    for e in events:
        if e["type"] == "clip":
            try:
                A.load_clip(e["clip"])
            except Exception as ex:  # noqa: BLE001
                errs.append(str(ex))
    return errs


@dataclass
class Project:
    root: Path
    plan: Plan
    R: RenderCtx
    keys: list[CamKey]
    events: list[dict]
    cams: np.ndarray
    n_frames: int


def load_project(proj: Path) -> Project:
    proj = proj.resolve()
    plan = load_plan(proj)
    tb = Timebase(plan)
    assets = Assets(proj, load_labels(proj / "labels.yaml"))
    R = RenderCtx(assets=assets, tb=tb, credits=load_credits(proj / "credits.yaml"))  # noqa: N806
    d = load_direction(proj).direct(tb)
    events = validate_events(d.events)
    errs = preflight(R, events)
    if errs:
        raise ProjectError("렌더 전 점검 실패:\n" + "\n".join(errs))
    if not d.keys:
        raise ProjectError("카메라 키가 없다")
    n = int(plan.total * FPS)
    return Project(proj, plan, R, d.keys, events, build_camera(d.keys, n, FPS), n)
