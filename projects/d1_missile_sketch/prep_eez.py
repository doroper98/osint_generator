"""Phase D1 스케치 — EEZ 다각형 준비(Marine Regions WFS GeoJSON → eez.json).

    python projects/d1_missile_sketch/prep_eez.py <WFS GeoJSON 경로>

원본: https://geo.vliz.be/geoserver/MarineRegions/wfs?service=WFS&version=1.0.0&request=GetFeature
      &typeName=MarineRegions:eez&outputFormat=application/json&bbox=115,25,150,48  (CC BY 4.0)
각 EEZ·중첩·공동관리 다각형을 화면 권역으로 자르고 단순화한다. `lines` = 바다 쪽 경계(해안선과 겹치는 구간을 뺀 선)로,
EEZ 테두리가 해안선을 따라 지저분하게 그려지지 않게 한다. 육지 = Natural Earth 10m 국가(data/geo/ne).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from shapely.geometry import MultiPolygon, box, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

PROJ = Path(__file__).resolve().parent
ROOT = PROJ.parents[1]
KEEP = {8327: ("KR", "eez"), 8328: ("KP", "eez"), 8487: ("JP", "eez"), 8486: ("CN", "eez"), 5690: ("RU", "eez"),
        48955: ("KR_JP", "overlap"), 21796: ("KR_JP", "joint"), 48950: ("JP_RU", "overlap")}
CLIP = box(110, 22, 160, 52)


def rnd(coords) -> list:  # noqa: ANN001
    return [[round(x, 3), round(y, 3)] for x, y in coords]


def main(src: str) -> int:
    d = json.loads(Path(src).read_text(encoding="utf-8"))
    ne = json.loads((ROOT / "data/geo/ne/ne_10m_admin_0_countries.geojson").read_text(encoding="utf-8"))
    big = box(108, 20, 162, 54)
    land = unary_union([shape(f["geometry"]).intersection(big) for f in ne["features"] if shape(f["geometry"]).intersects(big)])
    land_b = land.buffer(0.04).simplify(0.01)
    out = []
    for f in d["features"]:
        m = f["properties"]["mrgid"]
        if m not in KEEP:
            continue
        g = shape(f["geometry"])
        parts = [g] if g.geom_type == "Polygon" else [q for q in g.geoms if q.intersects(CLIP)]
        g = make_valid(MultiPolygon(parts).simplify(0.01)).intersection(CLIP).simplify(0.02, preserve_topology=True)
        ps = [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]
        ps = [q for q in ps if q.area > 0.01]
        polys = [[rnd(q.exterior.coords)] + [rnd(i.coords) for i in q.interiors] for q in ps]
        edge = MultiPolygon(ps).boundary.difference(land_b)
        ls = [edge] if edge.geom_type == "LineString" else list(getattr(edge, "geoms", []))
        code, kind = KEEP[m]
        out.append(dict(mrgid=m, code=code, kind=kind, name=f["properties"]["geoname"], polys=polys,
                        lines=[rnd(ln.coords) for ln in ls if ln.length > 0.05],
                        rep=list(g.representative_point().coords[0]), area=round(g.area, 2)))
        print(m, code, kind, len(polys), len(out[-1]["lines"]), flush=True)
    doc = dict(schema_version=1, source="Marine Regions EEZ (VLIZ) WFS MarineRegions:eez, CC BY 4.0, fetched 2026-10-05", features=out)
    (PROJ / "eez.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
