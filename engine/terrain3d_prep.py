"""terrain3d 구간 준비 — 미리 렌더한 3D 프레임·라벨 좌표 manifest(v7.4.0 back_and_forth D-0614·D-0615).

    python -m engine.terrain3d_prep projects/<pid> [--res 480p|720p|…] [--animatic]

구간 = direction 의 연속한 `stage: terrain3d` 숏들 [들어감, 나옴). 주 무대는 mercator 그대로(D-0615 ① 가).
- 들어가는 첫 프레임 = 그 시각 mercator 화면(같은 View — 같은 중심·같은 화면 폭)을 고도각 90°·북쪽 위로 내려다본 3D.
- 구간 안 `mode: drift` 숏부터 다음 숏까지만 천천히 기울어 궤도를 돈다(장면 단위 — 문장마다 회전 금지, C0·D-0614 ③).
  기울기·되돌리기 = rules stage_terrain3d.tilt_sec(이징), 궤도 속도 = rules sketch.war.terrain3d.camera.period_sec(스케치와 같은 모양).
- 나오는 끝 프레임 = 다시 90°·북쪽 위·같은 화면 폭 → 다음 mercator 숏과 이어진다.
- 부대 = stage_config.terrain3d.forces(schemas.war_units.WarForces) 키프레임을 프레임 시각에 보간(engine.stage_terrain3d.key_at).
- 글자·병종 그림은 그리지 않는다(text_in_engine) — 프레임마다 화면 좌표를 labels.json 으로 내고 엔진이 그린다(D-0614 ①).

산출(프로젝트 prev/terrain3d/<프로파일>/<구간 id>/): frames/f_0000.png… · frames/labels.json · scene.json · height.json · texture.png ·
manifest.json {schema_version, segment, inputs_sha1, frames, size, i0, i1, renderer}. 렌더는 inputs_sha1 이 지금 입력과 같을 때만
프레임을 쓴다(다르거나 없으면 렌더 전 오류, D-0615 §1 — 옛 프레임 재사용 금지, P6).
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from engine.stage_terrain3d import Terrain3DError, build_scene
from engine.style import FPS
from engine.timebase import smooth
from rules import load_rules as _load_rules_uncached
from schemas.war_units import UnitKey, WarForces, WarUnit

if TYPE_CHECKING:
    from engine.project import Project

# 규칙은 프로세스마다 한 번(load_rules 한 번 ≈ 0.3초 — 프레임·부대마다 부르면 수천 번)
load_rules = functools.lru_cache(maxsize=1)(_load_rules_uncached)

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "terrain3d"
STAGE = "terrain3d"
PREV_DIR = ("prev", "terrain3d")
TOOL_FILES = ("render.js", "view.html")


@dataclass
class Segment:
    """terrain3d 구간 한 개 — 시각은 영상 초, 프레임은 [i0, i1)."""

    sid: str
    t_in: float
    t_out: float
    orbits: list[tuple[float, float]] = field(default_factory=list)   # (시작, 되돌리기 시작) — drift 숏마다
    shot_index: list[int] = field(default_factory=list)


def segments(doc: Any, tb: Any, total: float) -> list[Segment]:
    """direction 숏 → terrain3d 구간. 들어감 = 첫 terrain3d 숏 at(+ move 면 dur — 카메라가 도착한 뒤), 나옴 = 다음 다른 무대 숏 at."""
    from engine.direction import resolve_anchor  # noqa: PLC0415

    shots = list(doc.shots)
    ts = [resolve_anchor(s.at, tb) for s in shots]
    out: list[Segment] = []
    i = 0
    while i < len(shots):
        if doc.shot_stage(shots[i]) != STAGE:
            i += 1
            continue
        j = i
        while j + 1 < len(shots) and doc.shot_stage(shots[j + 1]) == STAGE:
            j += 1
        first = shots[i]
        if first.mode == "drift":
            raise Terrain3DError(f"terrain3d 구간 첫 숏(at {first.at!r})은 cut·move — 내려다보기(90°)로 들어간 뒤 drift 숏에서 궤도")
        t_in = ts[i] + (first.dur if first.mode == "move" else 0.0)
        t_out = ts[j + 1] if j + 1 < len(shots) else total
        if doc.main_stage() == STAGE:
            raise Terrain3DError("terrain3d 는 주 무대가 될 수 없다 — 주 무대(mercator) 위의 구간(D-0615 ①)")
        orbits = []
        for k in range(i + 1, j + 1):
            if shots[k].mode == "drift":
                end = ts[k + 1] if k + 1 <= j else t_out
                orbits.append((ts[k], end))
        out.append(Segment(sid=f"seg{len(out):02d}", t_in=t_in, t_out=t_out, orbits=orbits, shot_index=list(range(i, j + 1))))
        i = j + 1
    T = load_rules().stage_terrain3d  # noqa: N806
    for s in out:
        if s.t_out - s.t_in < 2 * T.tilt_sec:
            raise Terrain3DError(f"terrain3d 구간 {s.sid} 길이 {s.t_out - s.t_in:.1f}s < 2 × tilt_sec {T.tilt_sec}")
        for a, b in s.orbits:
            if a < s.t_in or b + T.tilt_sec > s.t_out + 1e-6:
                raise Terrain3DError(f"terrain3d 구간 {s.sid} 궤도 [{a:.1f}, {b:.1f}] — 되돌리기(tilt_sec {T.tilt_sec})가 구간 안에 끝나야 한다")
    return out


def load_forces(proj: Path, rel: str) -> WarForces:
    p = (proj / rel).resolve()
    if not p.is_file() or proj.resolve() not in p.parents:
        raise Terrain3DError(f"forces 파일 없음(프로젝트 안): {rel}")
    f = WarForces.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
    sets = load_rules().war_history.symbol_sets
    known = {u for name in ("ancient", "early_modern", "modern") for u in getattr(sets, name).units}
    bad = sorted({u.symbol for u in f.units} - known)
    if bad:   # D-0615 §2-2 — 병종은 규칙 부호 세트 안만(P10)
        raise Terrain3DError(f"forces 병종 {bad} 는 rules war_history.symbol_sets 밖")
    return f


def resolved_units(f: WarForces, tb: Any) -> list[WarUnit]:
    """키프레임 앵커(at) → 초. 앵커를 푼 뒤 시각 순서·중복을 검사한다."""
    from engine.direction import resolve_anchor  # noqa: PLC0415

    out = []
    for u in f.units:
        ks = [UnitKey(t=k.t if k.t is not None else resolve_anchor(k.at, tb), lon=k.lon, lat=k.lat, heading=k.heading,
                      length_km=k.length_km, depth_km=k.depth_km) for k in u.keys]
        t_out = resolve_anchor(u.out_at, tb) if u.out_at is not None else u.t_out
        out.append(WarUnit(faction=u.faction, symbol=u.symbol, name=u.name, keys=ks, t_out=t_out))
    return out


def _hermite(p0: float, p1: float, v0: float, v1: float, d: float, u: float) -> float:
    """3차 에르미트(위치·속도 연속) — 궤도 방위 되돌리기."""
    h00, h10, h01, h11 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u, -2 * u**3 + 3 * u**2, u**3 - u**2
    return h00 * p0 + h10 * d * v0 + h01 * p1 + h11 * d * v1


NORTH_UP_AZ = 180.0   # tools/terrain3d view.html 방위 규약에서 카메라가 목표점 남쪽에 있을 때 화면 위 = 북(90° 내려다보기의 mercator 와 같은 방향)


def camera_at(t: float, seg: Segment) -> tuple[float, float]:
    """구간 시각 t 의 (방위°, 고도각°) — 방위는 NORTH_UP_AZ 기준. 90° 내려다보기(북쪽 위) ↔ 규칙 고도각·궤도. 위치·속도 연속(이징)."""
    az, el = _camera_rel(t, seg)
    return (az + NORTH_UP_AZ) % 360.0, el


def _camera_rel(t: float, seg: Segment) -> tuple[float, float]:
    T = load_rules().stage_terrain3d  # noqa: N806
    C = load_rules().sketch.war.terrain3d.camera  # noqa: N806
    rate = 360.0 / C.period_sec
    tilt = T.tilt_sec
    for a, b in seg.orbits:
        if t < a:
            break
        if t < a + tilt:   # 기울기 + 방위 가속(속도 0 → rate)
            u = (t - a) / tilt
            return rate * tilt * (u**3 - u**4 / 2), 90.0 + (C.elev_deg - 90.0) * smooth(u)
        if t < b:
            return rate * (tilt / 2 + (t - a - tilt)), C.elev_deg
        if t < b + tilt:   # 되돌리기 — 방위는 같은 방향으로 다음 0° 까지(속도 rate → 0), 고도각 90°
            A = rate * (tilt / 2 + (b - a - tilt))  # noqa: N806
            target = 360.0 * math.ceil((A + rate * tilt / 3) / 360.0)
            u = (t - b) / tilt
            return _hermite(A, target, rate, 0.0, tilt, u) % 360.0, C.elev_deg + (90.0 - C.elev_deg) * smooth(u)
    return 0.0, 90.0


def inputs_sha1(proj: Path, rel: str, seg: Segment, view_rows: list[list[float]], size: tuple[int, int], theme: str) -> str:
    """미리 렌더 프레임이 무엇으로 만들어졌는지 — forces 파일·구간 시각·mercator 카메라·크기·테마·규칙·렌더 도구. 렌더가 같은 값을 다시 잰다."""
    R = load_rules()  # noqa: N806
    h = hashlib.sha1()
    h.update((proj / rel).read_bytes())
    for tp in sorted(proj.glob(f"assets/theme_{theme}/tiers.pkl")) + sorted(proj.glob("assets/tiers.pkl")):   # 지형·텍스처 원천(geo.prep) — 다시 만들면 프레임도
        h.update(tp.read_bytes())
    h.update(json.dumps([(p.name, p.stat().st_size) for p in sorted(proj.glob(f"assets/theme_{theme}/base_*.png"))]).encode())
    for f in TOOL_FILES:
        h.update((TOOL / f).read_bytes())
    h.update(json.dumps({"seg": [seg.sid, round(seg.t_in, 4), round(seg.t_out, 4), [[round(a, 4), round(b, 4)] for a, b in seg.orbits]],
                         "cams": [[round(v, 6) for v in r] for r in view_rows], "size": list(size), "theme": theme,
                         "rules": {"stage_terrain3d": R.stage_terrain3d.model_dump(), "terrain3d": R.sketch.war.terrain3d.model_dump(),
                                   "unit": R.sketch.war.unit.model_dump(), "symbols": R.war_history.symbol_sets.model_dump()}},
                        sort_keys=True, default=str).encode())
    return h.hexdigest()


def seg_dir(proj: Path, profile: str, seg: Segment) -> Path:
    return proj.joinpath(*PREV_DIR) / profile / seg.sid


def view_rows(P: "Project", seg: Segment) -> list[list[float]]:  # noqa: N803
    fps = FPS
    i0, i1 = int(round(seg.t_in * fps)), int(round(seg.t_out * fps))
    return [list(map(float, P.cams[i])) for i in range(i0, max(i0 + 1, i1))]   # 구간 전 프레임 — 3D 카메라가 따르는 mercator 카메라(D-0617)


def forces_rel(P: "Project") -> str:  # noqa: N803
    cfg = P.R.cache.get("stage", {}).get("configs", {}).get(STAGE) or {}
    if not cfg.get("forces"):
        raise Terrain3DError("terrain3d 구간에는 stage_config.terrain3d.forces 가 필요하다(D-0615 §2)")
    return str(cfg["forces"])


def prepare(P: "Project", segs: list[Segment]) -> list[dict]:  # noqa: N803
    rel = forces_rel(P)
    forces = load_forces(P.root, rel)
    theme = P.R.stage.theme_name
    size = (P.R.out.width, P.R.out.height)
    three = json.loads((TOOL / "node_modules" / "three" / "package.json").read_text(encoding="utf-8"))
    npm_root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    out = []
    for seg in segs:
        d = seg_dir(P.root, P.R.out.name, seg)
        want = inputs_sha1(P.root, rel, seg, view_rows(P, seg), size, theme)
        man_p = d / "manifest.json"
        if man_p.is_file() and json.loads(man_p.read_text(encoding="utf-8")).get("inputs_sha1") == want:   # 입력 지문이 같으면 다시 그리지 않는다
            out.append(json.loads(man_p.read_text(encoding="utf-8")))
            print(f"terrain3d {seg.sid}: 입력 지문 같음 — 그대로 둔다({d})", flush=True)
            continue
        shutil.rmtree(d, ignore_errors=True)
        info = build_scene(P, seg, forces, d)
        subprocess.run(["node", str(TOOL / "render.js"), str(d.resolve())], check=True, cwd=TOOL, env={**os.environ, "NODE_PATH": npm_root})
        n = len(list((d / "frames").glob("f_*.png")))
        if n != info["i1"] - info["i0"]:
            raise Terrain3DError(f"{seg.sid}: 렌더 프레임 {n} ≠ 구간 프레임 {info['i1'] - info['i0']}")
        man = {"schema_version": 1, "segment": seg.sid, "t_in": seg.t_in, "t_out": seg.t_out, "orbits": seg.orbits,
               "inputs_sha1": want, "frames": n, "size": list(size), **info,
               "renderer": f"three.js {three['version']} ({three['license']}) · headless Chromium(playwright) swiftshader"}
        (d / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
        out.append(man)
        print(f"terrain3d {seg.sid}: {n} 프레임 [{seg.t_in:.2f}, {seg.t_out:.2f}) → {d}", flush=True)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m engine.terrain3d_prep", description="terrain3d 구간 3D 프레임 미리 렌더(D-0615)")
    ap.add_argument("project", type=Path)
    ap.add_argument("--res", default=None, help="출력 프로파일(렌더와 같아야 한다)")
    ap.add_argument("--animatic", action="store_true", help="콘티 판 프로파일로(rules animatic.profile)")
    a = ap.parse_args(argv)
    from engine.project import load_project  # noqa: PLC0415
    from engine.style import output_profile  # noqa: PLC0415

    P = load_project(a.project, out=output_profile(a.res) if a.res else None, animatic=a.animatic)  # noqa: N806
    segs = P.R.cache.get("terrain3d_segments") or []
    if not segs:
        print("terrain3d 구간 없음 — 할 일 없음", file=sys.stderr)
        return 0
    prepare(P, segs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
