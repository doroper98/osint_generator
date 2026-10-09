"""EEZ 다각형 준비 CLI — Marine Regions WFS GeoJSON → `projects/<pid>/<spec.eez.file>`(D-0140 §3).

    curl -o /tmp/eez.json "<spec.eez.prep.wfs_url>"
    python -m sketch.missile.prep_eez /tmp/eez.json projects/<pid> [--fetched 2026-10-09]

각 EEZ·중첩·공동관리 다각형을 화면 권역(prep.clip)으로 자르고 단순화한다. `lines` = 바다 쪽 경계(해안선과 겹치는 구간을 뺀 선).
육지 = Natural Earth 10m 국가(data/geo/ne). **서해 남북**: Marine Regions 남북 등거리선은 NLL 도 북한 주장선도 아니라 쓰지 않는다 —
prep.west_box 안의 남북 EEZ 를 NLL(개략)·북한 1999 선으로 다시 나누고 두 선 사이를 중첩(KR_KP overlap)으로 둔다(docs/handoff/22 §2.5).
사실 값(mrgid·좌표)은 spec.eez.prep, 기하 처리 공차는 아래 상수(데이터 준비 — 화면 수치가 아니다). 원본: 4d9dc65 `prep_eez.py`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon, box, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

from sketch.common.spec import load_spec
from sketch.missile.spec import EezPrep, MissileSpec

ROOT = Path(__file__).resolve().parents[2]
NE_COUNTRIES = ROOT / "data/geo/ne/ne_10m_admin_0_countries.geojson"
LAND_BOX = (108, 20, 162, 54)       # 육지 마스크를 만드는 넓은 상자(clip 보다 크게)
LAND_BUFFER, LAND_SIMPLIFY = 0.04, 0.01
SIMPLIFY_1, SIMPLIFY_2 = 0.01, 0.02
MIN_PART_AREA, MIN_OVERLAP_AREA = 0.01, 0.005
MIN_LINE_LEN = 0.05
WEST_INSET = 0.02                    # 서해 북부 새 경계는 주장선이 그린다 — 테두리에서 뺀다
ROUND = 3
SOURCE = "Marine Regions EEZ (VLIZ) WFS MarineRegions:eez, {license}, fetched {date}"
CLAIM_NAMES = {"KR_KP": "West Sea: NLL vs DPRK 1999 claim (approx.)", "NLL": "NLL 1953 (approx. reconstruction)",
               "NK1999": "DPRK West Sea MDL 1999"}


def dms(d: float, m: float, s: float) -> float:
    return d + m / 60 + s / 3600


def nk1999(p: EezPrep) -> list[tuple[float, float]]:
    """북한 1999 선 = 동쪽 공통 시작점 + 발표 꼭짓점(경위도 DMS)."""
    return [tuple(p.anchor)] + [(dms(*lo), dms(*la)) for lo, la in p.nk1999_dms]   # type: ignore[misc]


def nk_extension(p: EezPrep) -> tuple[float, float]:
    """마지막 꼭짓점 뒤 '중국과의 해상경계선까지' — 방향 미발표. 마지막 두 점 방향 그대로 west_box 아래 변까지 연장(화면에 표기)."""
    pts = nk1999(p)
    (x2, y2), (x3, y3) = pts[-2], pts[-1]
    y0 = p.west_box[1]
    k = (y3 - y0) / (y2 - y3)
    return (x3 - (x2 - x3) * k, y0)


def west_sea_split(p: EezPrep) -> tuple[Polygon, Polygon]:
    """west_box 를 NLL 북쪽(N)·북한 주장선 남쪽(S)으로 나눈다. 둘 다 아닌 곳 = 두 주장의 중첩."""
    west = box(*p.west_box)
    x0, y0, x1, y1 = p.west_box
    nll = sorted(p.nll_approx)
    north = Polygon([(x0, nll[0][1])] + nll + [(x1, nll[-1][1]), (x1, y1), (x0, y1)])
    nk = [nk_extension(p)] + nk1999(p)[::-1]
    south = Polygon(nk + [(x1, nk[-1][1]), (x1, y0), nk[0]])
    return north.intersection(west), south.intersection(west)


def rnd(coords) -> list:  # noqa: ANN001
    return [[round(x, ROUND), round(y, ROUND)] for x, y in coords]


def build(src: dict, p: EezPrep, fetched: str) -> dict:
    ne = json.loads(NE_COUNTRIES.read_text(encoding="utf-8"))
    big = box(*LAND_BOX)
    land = unary_union([shape(f["geometry"]).intersection(big) for f in ne["features"] if shape(f["geometry"]).intersects(big)])
    land_b = land.buffer(LAND_BUFFER).simplify(LAND_SIMPLIFY)
    clip, west = box(*p.clip), box(*p.west_box)
    south_id, north_id = p.west_codes
    raw = {f["properties"]["mrgid"]: make_valid(shape(f["geometry"])).intersection(clip) for f in src["features"]
           if f["properties"]["mrgid"] in p.west_codes}
    missing = [m for m in p.west_codes if m not in raw]
    if missing:
        raise ValueError(f"WFS 원본에 서해 남북 mrgid {missing} 가 없다")
    north, south = west_sea_split(p)
    korea = unary_union([raw[south_id], raw[north_id]]).intersection(west)
    over = korea.difference(north).difference(south)
    fixed = {south_id: raw[south_id].difference(west).union(korea.intersection(south)),    # 남: 서해 북부는 북한 주장선 남쪽만
             north_id: raw[north_id].difference(west).union(korea.intersection(north))}    # 북: 서해 북부는 NLL 북쪽만
    out = []
    seen = set()
    for f in src["features"]:
        m = f["properties"]["mrgid"]
        if m not in p.keep:
            continue
        seen.add(m)
        g = fixed.get(m, shape(f["geometry"]))
        parts = [g] if g.geom_type == "Polygon" else [q for q in g.geoms if q.intersects(clip)]
        g = make_valid(MultiPolygon(parts).simplify(SIMPLIFY_1)).intersection(clip).simplify(SIMPLIFY_2, preserve_topology=True)
        ps = [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]
        ps = [q for q in ps if q.area > MIN_PART_AREA]
        polys = [[rnd(q.exterior.coords)] + [rnd(i.coords) for i in q.interiors] for q in ps]
        edge = MultiPolygon(ps).boundary.difference(land_b)
        if m in fixed:   # 서해 북부의 새 경계는 NLL·북한 주장선으로 따로 그린다
            edge = edge.difference(west.buffer(-WEST_INSET))
        ls = [edge] if edge.geom_type == "LineString" else list(getattr(edge, "geoms", []))
        code, kind = p.keep[m]
        out.append(dict(mrgid=m, code=code, kind=kind, name=f["properties"]["geoname"], polys=polys,
                        lines=[rnd(ln.coords) for ln in ls if ln.length > MIN_LINE_LEN],
                        rep=list(g.representative_point().coords[0]), area=round(g.area, 2)))
        print(m, code, kind, len(polys), len(out[-1]["lines"]), flush=True)
    lost = sorted(set(p.keep) - seen)
    if lost:
        raise ValueError(f"WFS 원본에 spec keep mrgid {lost} 가 없다 — 조용히 빼지 않는다")
    ps = [q for q in getattr(over, "geoms", [over]) if q.geom_type == "Polygon" and q.area > MIN_OVERLAP_AREA]
    nll = sorted(p.nll_approx)
    nk = nk1999(p)
    out.append(dict(mrgid=None, code="KR_KP", kind="overlap", name=CLAIM_NAMES["KR_KP"],
                    polys=[[rnd(q.exterior.coords)] + [rnd(i.coords) for i in q.interiors] for q in ps], lines=[],
                    rep=list(over.representative_point().coords[0]), area=round(over.area, 2)))
    out.append(dict(mrgid=None, code="NLL", kind="claim_line", name=CLAIM_NAMES["NLL"], polys=[], lines=[rnd(nll)],
                    rep=list(p.nll_approx[3]), area=0))
    out.append(dict(mrgid=None, code="NK1999", kind="claim_line", name=CLAIM_NAMES["NK1999"], polys=[],
                    lines=[rnd(nk[::-1]), rnd([nk[-1], nk_extension(p)])], rep=list(nk[1]), area=0))
    print("KR_KP overlap", len(ps), round(over.area, 2))
    return dict(schema_version=1, source=SOURCE.replace("{license}", p.license).replace("{date}", fetched), features=out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m sketch.missile.prep_eez", description="Marine Regions WFS GeoJSON → eez.json")
    ap.add_argument("wfs", type=Path, help="WFS GeoJSON(spec eez.prep.wfs_url 로 받은 파일)")
    ap.add_argument("project", type=Path)
    ap.add_argument("--fetched", default=dt.date.today().isoformat(), help="받은 날짜(provenance 출처 문구)")
    args = ap.parse_args(argv)
    spec = load_spec(args.project, MissileSpec)
    doc = build(json.loads(args.wfs.read_text(encoding="utf-8")), spec.eez.prep, args.fetched)
    dest = args.project / spec.eez.file
    dest.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
