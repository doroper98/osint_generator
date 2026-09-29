"""콘티 판 막지도 자료 만들기 (v4.9.0, back_and_forth D-0108·R-0135 A).

    python tools/build_flat_map.py [--ne-dir data/geo/ne] [--out data/geo_flat/ne_110m_countries.json]

Natural Earth 110m 국가(퍼블릭 도메인)를 받아 콘티 판(`engine.render --animatic`)의 막지도 한 벌을 저장소 추적 파일로 만든다.
자산 없는 환경(geo.prep 을 돌리지 않은 곳)에서도 막지도를 그리기 위해서다(D-0108 합격 조건).

- 국가 키 = `geo.prep_geometry.country_key`(ISO_A2_EH, 없거나 −99 면 ADMIN) — 10m geo.pkl 과 같은 키(country 이벤트 codes).
- 좌표는 소수 2자리(약 1km — 110m 축척 정밀도 안). 폴리곤 = [바깥 고리, 구멍…].
- 크림 고리 = NE 10m admin1(Autonomous Republic of Crimea·Sevastopol) 합집합을 단순화(tol CRIMEA_TOL). 110m 국가 파일은
  크림을 RU 에 넣는다(실측) — 프로젝트 `geo.yaml crimea_to_ua: true` 면 렌더가 로드할 때 UA 로 옮긴다(04 §3.2).
- 기록: 원본 URL·md5·라이선스를 파일 `source` 에 남긴다(C9 권리 기록).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import unary_union

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from geo.prep_geometry import CRIMEA_NAMES, country_key, polys  # noqa: E402

NE_110M_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
LICENSE = "Natural Earth — public domain (naturalearthdata.com/about/terms-of-use)"
DIGITS = 2
CRIMEA_TOL = 0.02


def _poly_rings(g: object) -> list[list[list[list[float]]]]:
    out = []
    for p in polys(g):   # type: ignore[arg-type]
        rings = [p.exterior.coords, *(r.coords for r in p.interiors)]
        out.append([[[round(x, DIGITS), round(y, DIGITS)] for x, y in r] for r in rings])
    return out


def build(ne110: bytes, admin1_path: Path) -> dict:
    src = json.loads(ne110)
    countries: dict[str, list] = {}
    for f in src["features"]:
        countries.setdefault(country_key(f["properties"]), []).extend(_poly_rings(shape(f["geometry"]).buffer(0)))
    adm = json.loads(admin1_path.read_text(encoding="utf-8"))
    parts = [shape(f["geometry"]).buffer(0) for f in adm["features"]
             if f["properties"].get("name_en") in CRIMEA_NAMES or f["properties"].get("name") in CRIMEA_NAMES]
    if not parts:
        raise ValueError("admin1 에서 크림반도 행정구역을 찾지 못했다")
    crimea = unary_union(parts).simplify(CRIMEA_TOL, preserve_topology=True)
    return {"schema_version": 1,
            "source": {"countries": NE_110M_URL, "countries_md5": hashlib.md5(ne110).hexdigest(),
                       "crimea": f"{admin1_path.name} {sorted(CRIMEA_NAMES)} simplify {CRIMEA_TOL}",
                       "crimea_md5": hashlib.md5(admin1_path.read_bytes()).hexdigest(),
                       "license": LICENSE, "digits": DIGITS},
            "countries": dict(sorted(countries.items())), "crimea": _poly_rings(crimea)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="tools.build_flat_map")
    ap.add_argument("--ne-dir", type=Path, default=REPO / "data" / "geo" / "ne")
    ap.add_argument("--out", type=Path, default=REPO / "data" / "geo_flat" / "ne_110m_countries.json")
    args = ap.parse_args(argv)
    admin1 = args.ne_dir / "ne_10m_admin_1_states_provinces.geojson"
    if not admin1.exists():
        print(f"없음: {admin1} — `python tools/fetch_data.py ne` 먼저", file=sys.stderr)
        return 1
    with urllib.request.urlopen(NE_110M_URL, timeout=60) as r:   # noqa: S310 — 고정 URL
        ne110 = r.read()
    doc = build(ne110, admin1)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{args.out}: 국가 {len(doc['countries'])} · 크림 폴리곤 {len(doc['crimea'])} · {args.out.stat().st_size} B", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
