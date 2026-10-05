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

from shapely.geometry import LineString, MultiPolygon, Polygon, box, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

PROJ = Path(__file__).resolve().parent
ROOT = PROJ.parents[1]
KEEP = {8327: ("KR", "eez"), 8328: ("KP", "eez"), 8487: ("JP", "eez"), 8486: ("CN", "eez"), 5690: ("RU", "eez"),
        48955: ("KR_JP", "overlap"), 21796: ("KR_JP", "joint"), 48950: ("JP_RU", "overlap")}
CLIP = box(110, 22, 160, 52)

# ---- 서해 남북 경계: Marine Regions 의 남북 공유 경계(등거리 계산선)는 NLL 도 북한 주장선도 아니다 → 쓰지 않고 두 주장 사이를 중첩으로 그린다
WEST = box(123.0, 36.5, 126.8, 38.6)   # 서해 북부 — 이 안의 남북 EEZ 는 아래 두 선으로 다시 나눈다
E_ANCHOR = (126.17, 37.72)             # 한강 하구 서쪽 — 두 선의 동쪽 공통 시작점(개략)
# NLL(1953, 유엔군사령부). 공식 좌표 목록 미확보 → "서해 5도와 북측 해안의 중간점"(설정 원칙, 위키백과·정책브리핑) 으로 개략 재구성.
# 화면에 반드시 "개략" 표기. 본편 전 공식 좌표(국방부 자료·해도)로 교체 대상
NLL_APPROX = [(123.0, 38.05), (124.10, 38.05), (124.62, 38.05), (124.79, 38.01), (124.86, 37.96), (124.87, 37.80),
              (124.88, 37.70), (125.20, 37.69), (125.55, 37.70), (125.66, 37.71), (125.80, 37.69), (125.99, 37.71), E_ANCHOR]


def dms(d: int, m: int, s_: float) -> float:
    return d + m / 60 + s_ / 3600


# 북한 '조선 서해 해상군사분계선'(1999.9.2 총참모부 특별보도) — 한국일보 1999.9.3 인용 좌표.
# 2점 위도는 보도마다 1'02"(한국일보)·1'12"(KCNA 영문 인용)로 다르다 — 화면 축척(약 300m 차)에서는 같다. 여기서는 1'12"
NK1999 = [E_ANCHOR, (dms(125, 31, 0), dms(37, 18, 30)), (dms(124, 55, 0), dms(37, 1, 12)), (dms(124, 32, 30), dms(36, 50, 45))]


def nk_extension() -> tuple[float, float]:
    """3점 뒤 '중국과의 해상경계선까지' — 방향 미발표. 2→3점 방향 그대로 WEST 아래 변까지 연장(화면에 '연장 방향 미발표' 표기)."""
    (x2, y2), (x3, y3) = NK1999[2], NK1999[3]
    k = (y3 - WEST.bounds[1]) / (y2 - y3)
    return (x3 - (x2 - x3) * k, WEST.bounds[1])


def west_sea_split() -> tuple[Polygon, Polygon]:
    """WEST 를 NLL 북쪽(N)·북한 주장선 남쪽(S)으로 나눈다. 둘 다 아닌 곳 = 두 주장의 중첩."""
    x0, y0, x1, y1 = WEST.bounds
    nll = sorted(NLL_APPROX)
    north = Polygon([(x0, nll[0][1])] + nll + [(x1, nll[-1][1]), (x1, y1), (x0, y1)])
    nk = [nk_extension()] + NK1999[::-1]
    south = Polygon(nk + [(x1, nk[-1][1]), (x1, y0), nk[0]])
    return north.intersection(WEST), south.intersection(WEST)


def rnd(coords) -> list:  # noqa: ANN001
    return [[round(x, 3), round(y, 3)] for x, y in coords]


def main(src: str) -> int:
    d = json.loads(Path(src).read_text(encoding="utf-8"))
    ne = json.loads((ROOT / "data/geo/ne/ne_10m_admin_0_countries.geojson").read_text(encoding="utf-8"))
    big = box(108, 20, 162, 54)
    land = unary_union([shape(f["geometry"]).intersection(big) for f in ne["features"] if shape(f["geometry"]).intersects(big)])
    land_b = land.buffer(0.04).simplify(0.01)
    out = []
    raw = {f["properties"]["mrgid"]: make_valid(shape(f["geometry"])).intersection(CLIP) for f in d["features"]
           if f["properties"]["mrgid"] in (8327, 8328)}
    north, south = west_sea_split()
    korea = unary_union([raw[8327], raw[8328]]).intersection(WEST)
    over = korea.difference(north).difference(south)
    fixed = {8327: raw[8327].difference(WEST).union(korea.intersection(south)),       # 한국 EEZ: 서해 북부는 북한 주장선 남쪽만
             8328: raw[8328].difference(WEST).union(korea.intersection(north))}       # 북한 EEZ: 서해 북부는 NLL 북쪽만
    for f in d["features"]:
        m = f["properties"]["mrgid"]
        if m not in KEEP:
            continue
        g = fixed.get(m, shape(f["geometry"]))
        parts = [g] if g.geom_type == "Polygon" else [q for q in g.geoms if q.intersects(CLIP)]
        g = make_valid(MultiPolygon(parts).simplify(0.01)).intersection(CLIP).simplify(0.02, preserve_topology=True)
        ps = [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]
        ps = [q for q in ps if q.area > 0.01]
        polys = [[rnd(q.exterior.coords)] + [rnd(i.coords) for i in q.interiors] for q in ps]
        edge = MultiPolygon(ps).boundary.difference(land_b)
        if m in fixed:   # 서해 북부의 새 경계는 NLL·북한 주장선으로 따로 그린다
            edge = edge.difference(WEST.buffer(-0.02))
        ls = [edge] if edge.geom_type == "LineString" else list(getattr(edge, "geoms", []))
        code, kind = KEEP[m]
        out.append(dict(mrgid=m, code=code, kind=kind, name=f["properties"]["geoname"], polys=polys,
                        lines=[rnd(ln.coords) for ln in ls if ln.length > 0.05],
                        rep=list(g.representative_point().coords[0]), area=round(g.area, 2)))
        print(m, code, kind, len(polys), len(out[-1]["lines"]), flush=True)
    ps = [q for q in getattr(over, "geoms", [over]) if q.geom_type == "Polygon" and q.area > 0.005]
    out.append(dict(mrgid=None, code="KR_KP", kind="overlap", name="West Sea: NLL vs DPRK 1999 claim (approx.)",
                    polys=[[rnd(q.exterior.coords)] + [rnd(i.coords) for i in q.interiors] for q in ps], lines=[],
                    rep=list(over.representative_point().coords[0]), area=round(over.area, 2)))
    out.append(dict(mrgid=None, code="NLL", kind="claim_line", name="NLL 1953 (approx. reconstruction)", polys=[], lines=[rnd(sorted(NLL_APPROX))],
                    rep=list(NLL_APPROX[3]), area=0))
    out.append(dict(mrgid=None, code="NK1999", kind="claim_line", name="DPRK West Sea MDL 1999", polys=[],
                    lines=[rnd(NK1999[::-1]), rnd([NK1999[-1], nk_extension()])], rep=list(NK1999[1]), area=0))
    print("KR_KP overlap", len(ps), round(over.area, 2))
    doc = dict(schema_version=1, source="Marine Regions EEZ (VLIZ) WFS MarineRegions:eez, CC BY 4.0, fetched 2026-10-05", features=out)
    (PROJ / "eez.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
