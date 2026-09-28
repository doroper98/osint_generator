"""국가·1급 행정구역·도시 지오메트리 (v2.2.0, prep3 `polys, rings, load_countries, load_admin1, load_places`, 04 §3).

    python -m geo.prep_geometry --bbox 20,-20,150,60 --admin1 KR,IR --ne-dir data/geo/ne --out assets/geo.pkl [--crimea-to-ua]

출력 geo.pkl: coarse(tol 0.03)·fine(0.005)·meta·admin1(0.006)·places — 02 §2.5 계약.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import box, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

COARSE_TOL = 0.03
FINE_TOL = 0.005
ADMIN1_TOL = 0.006
CRIMEA_NAMES = ("Autonomous Republic of Crimea", "Sevastopol")  # 04 §3.2, 유엔 총회 결의 68/262
CRIMEA_GAP = 0.001


def polys(g: BaseGeometry | None) -> list:
    """재귀 평탄화 → Polygon 목록. GeometryCollection 안의 MultiPolygon 도 빠뜨리지 않는다(프랑스 버그, 04 §3.3)."""
    if g is None or g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    if hasattr(g, "geoms"):
        out: list = []
        for x in g.geoms:
            out += polys(x)
        return out
    return []


def rings(g: BaseGeometry, tol: float) -> list[np.ndarray]:
    out = []
    for p in polys(g.simplify(tol, preserve_topology=True)):
        out.append(np.asarray(p.exterior.coords, np.float32)[:, :2])
        for r in p.interiors:
            out.append(np.asarray(r.coords, np.float32)[:, :2])
    return out


def parse_bbox(s: str) -> tuple[float, float, float, float]:
    v = tuple(float(x) for x in s.split(","))
    if len(v) != 4 or not (v[0] < v[2] and v[1] < v[3]):
        raise ValueError(f"bbox 는 lon0,lat0,lon1,lat1 (lon0<lon1, lat0<lat1): {s!r}")
    return v  # type: ignore[return-value]


def _read(ne_dir: Path, name: str) -> dict:
    p = ne_dir / f"{name}.geojson"
    if not p.exists():
        raise FileNotFoundError(f"Natural Earth 없음: {p} — `python -m geo.prep` 가 받는다")
    return json.loads(p.read_text(encoding="utf-8"))


def country_key(p: dict) -> str:
    """국가 키 — ISO_A2_EH, 없거나 −99 면 ADMIN(v3 prep3 규칙 그대로)."""
    return p["ISO_A2_EH"] if p.get("ISO_A2_EH") not in (None, "-99") else p["ADMIN"]


def country_parts(ne_dir: Path, bb: BaseGeometry) -> dict[str, list[tuple[dict, BaseGeometry]]]:
    """키 → [(속성, 전체 지오메트리)] — 권역과 겹치는 피처만, 처음 나온 키 순서. 같은 키 피처가 여럿일 수 있다
    (KZ = 카자흐스탄 + 바이코누르, FR = 프랑스 + 클리퍼턴, BR·AU 부속 영토 — v4.1.0 D-0078)."""
    ctry = _read(ne_dir, "ne_10m_admin_0_countries")
    out: dict[str, list[tuple[dict, BaseGeometry]]] = {}
    for f in ctry["features"]:
        p = f["properties"]
        g = shape(f["geometry"]).buffer(0)
        if not g.intersects(bb):
            continue
        out.setdefault(country_key(p), []).append((p, g))
    return out


def load_countries(ne_dir: Path, bb: BaseGeometry) -> tuple[dict, dict]:
    """(G, META). 같은 키 피처는 **합집합**(v4.1.0 D-0078 — 뒤 피처가 앞 피처를 덮어써 카자흐스탄이 바이코누르 조각만 남던 결함,
    PIPELINE-AP-011). META 는 면적이 가장 큰 피처의 것. 피처가 하나인 키는 v3 와 같은 계산(g ∩ 권역) 그대로."""
    G, META = {}, {}  # noqa: N806
    for k, parts in country_parts(ne_dir, bb).items():
        G[k] = parts[0][1].intersection(bb) if len(parts) == 1 else unary_union([g.intersection(bb) for _, g in parts])
        p = max(parts, key=lambda pg: pg[1].area)[0]
        META[k] = dict(name=p["ADMIN"], ko=p.get("NAME_KO") or p["ADMIN"], lx=p.get("LABEL_X"), ly=p.get("LABEL_Y"),
                       minlab=p.get("MIN_LABEL", 5), rank=p.get("LABELRANK", 5))
    return G, META


def coverage_reference(ne_dir: Path, bb: BaseGeometry) -> dict[str, BaseGeometry]:
    """커버리지 검사 기준 — 키별 원본 피처 전부의 합집합 ∩ 권역. G 조립(load_countries·크림 재분류)과 따로 만든다:
    G 가 어떤 이유로 국가 일부를 잃으면 기준 영역 안 육지 화소 비율이 떨어져 잡힌다(geo.prep_tiers.fill_ratios)."""
    return {k: unary_union([g.intersection(bb) for _, g in parts]) for k, parts in country_parts(ne_dir, bb).items()}


def crimea_geometry(ne_dir: Path) -> BaseGeometry:
    adm = _read(ne_dir, "ne_10m_admin_1_states_provinces")
    parts = [shape(f["geometry"]).buffer(0) for f in adm["features"]
             if f["properties"].get("name_en") in CRIMEA_NAMES or f["properties"].get("name") in CRIMEA_NAMES]
    if not parts:
        raise ValueError("admin1 에서 크림반도 행정구역을 찾지 못했다")
    return unary_union(parts)


def reclassify_crimea(G: dict, crimea: BaseGeometry, bb: BaseGeometry) -> None:  # noqa: N803
    """크림반도를 UA 로(04 §3.2). 권역 밖이면 아무것도 하지 않는다."""
    c = crimea.intersection(bb)
    if c.is_empty:
        return
    if "UA" not in G or "RU" not in G:
        raise ValueError("크림 재분류에는 권역 안에 UA·RU 가 모두 있어야 한다")
    G["UA"] = unary_union([G["UA"], c])
    G["RU"] = G["RU"].difference(c.buffer(CRIMEA_GAP))


def load_admin1(ne_dir: Path, codes: set[str], bb: BaseGeometry) -> dict:
    adm = _read(ne_dir, "ne_10m_admin_1_states_provinces")
    out: dict = {}
    for f in adm["features"]:
        p = f["properties"]
        if p.get("iso_a2") not in codes:
            continue
        g = shape(f["geometry"]).buffer(0)
        if not g.intersects(bb):
            continue
        out.setdefault(p["iso_a2"], []).append(dict(name=p.get("name_ko") or p.get("name"), g=g, lx=p.get("longitude"),
                                                     ly=p.get("latitude")))
    return out


def load_places(ne_dir: Path, bb: BaseGeometry) -> list[dict]:
    pp = _read(ne_dir, "ne_10m_populated_places")
    out = []
    for f in pp["features"]:
        p = f["properties"]
        x, y = f["geometry"]["coordinates"][:2]
        if not (bb.bounds[0] <= x <= bb.bounds[2] and bb.bounds[1] <= y <= bb.bounds[3]):
            continue
        ko = p.get("NAME_KO") or p.get("name_ko")
        if not ko:
            continue
        out.append(dict(ko=ko, lon=x, lat=y, rank=p.get("SCALERANK", p.get("scalerank", 9)),
                        cap=("capital" in (p.get("FEATURECLA") or "").lower()) or p.get("ADM0CAP") == 1,
                        iso=p.get("ADM0_A3") or p.get("SOV_A3"), pop=p.get("POP_MAX") or 0))
    return out


def build_geo(ne_dir: Path, bbox: tuple[float, float, float, float], admin1: set[str],
              crimea_to_ua: bool = False) -> tuple[dict, dict]:
    """(geo 딕셔너리, 국가 지오메트리 G). G 는 티어 래스터화에 그대로 쓴다."""
    bb = box(*bbox)
    G, META = load_countries(ne_dir, bb)  # noqa: N806
    if crimea_to_ua:
        reclassify_crimea(G, crimea_geometry(ne_dir), bb)
    ADM = load_admin1(ne_dir, admin1, bb)  # noqa: N806
    geo = dict(coarse={k: rings(g, COARSE_TOL) for k, g in G.items()}, fine={k: rings(g, FINE_TOL) for k, g in G.items()},
               meta=META,
               admin1={k: [dict(name=a["name"], lx=a["lx"], ly=a["ly"], rings=rings(a["g"], ADMIN1_TOL)) for a in v]
                       for k, v in ADM.items()},
               places=load_places(ne_dir, bb))
    return geo, G


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="geo.prep_geometry")
    ap.add_argument("--bbox", required=True)
    ap.add_argument("--admin1", default="")
    ap.add_argument("--ne-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--crimea-to-ua", action="store_true")
    args = ap.parse_args(argv)
    codes = {c for c in args.admin1.split(",") if c}
    geo, _ = build_geo(args.ne_dir, parse_bbox(args.bbox), codes, args.crimea_to_ua)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pickle.dump(geo, open(args.out, "wb"))
    print(f"geo {len(geo['coarse'])} admin1 {({k: len(v) for k, v in geo['admin1'].items()})} places {len(geo['places'])}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
