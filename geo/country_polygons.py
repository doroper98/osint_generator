"""국가 폴리곤(NE 110m) — v7.4.0 back_and_forth D-0241 §2: 콘티 막지도 삭제 뒤 검사(flag_territory·sea_only_frame)가 쓰는 육지·국가 자료."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rules import load_rules

REPO = Path(__file__).resolve().parent.parent


def load_country_polygons(crimea_to_ua: bool) -> dict[str, list]:
    """저장소 국가 폴리곤 자료(rules geo.country_polygons, tools/build_flat_map.py) → 국가 키 → 폴리곤 [[바깥, 구멍…]…]. crimea_to_ua 면 크림을 RU → UA(04 §3.2)."""
    doc = json.loads((REPO / load_rules().geo.country_polygons).read_text(encoding="utf-8"))
    polys: dict[str, list] = doc["countries"]
    if crimea_to_ua:
        from shapely.geometry import MultiPolygon, Polygon  # noqa: PLC0415
        from shapely.ops import unary_union  # noqa: PLC0415

        from geo.prep_geometry import CRIMEA_GAP, polys as flat  # noqa: PLC0415

        def geom(v: list) -> Any:
            return MultiPolygon([Polygon(p[0], p[1:]) for p in v]).buffer(0)

        def back(g: Any) -> list:
            return [[[list(c) for c in q.exterior.coords], *[[list(c) for c in r.coords] for r in q.interiors]] for q in flat(g)]

        cr = geom(doc["crimea"])
        polys = dict(polys, UA=back(unary_union([geom(polys["UA"]), cr])), RU=back(geom(polys["RU"]).difference(cr.buffer(CRIMEA_GAP))))
    return polys

