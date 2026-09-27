"""지오 자산 단계 CLI (v2.2.0, D-0015 §1-4, 16 §4).

    python -m geo.prep <proj>   → <proj>/assets/{geo.pkl, tiers.pkl, base_*.png, geo_report.json}

프로젝트 `geo.yaml`(권역·admin1 대상국·크림 재분류·티어)을 읽어 Natural Earth·지형 타일을 캐시(`data/geo/`)에
받고(`tools/fetch_data.py`의 다운로드 재사용), 지오메트리와 티어를 만든다. 마지막 줄 StageResult JSON.
land-miss(대표점이 육지로 칠해지지 않은 국가)는 `geo_report.json`에 남기고 drops 로 올린다.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from geo.prep_geometry import build_geo
from geo.prep_tiers import TierSpec, build_tier, tier_record, tile_path, tile_range

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / "data" / "geo"
NE_FILES = ("ne_10m_admin_0_countries", "ne_10m_admin_1_states_provinces", "ne_10m_populated_places")
DOWNLOAD_WORKERS = 8


class TierConf(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    ppd: int = Field(gt=0)
    z: int = Field(ge=0, le=15)
    bbox: tuple[float, float, float, float]  # lon0, lat0, lon1, lat1

    def spec(self) -> TierSpec:
        return TierSpec.parse(f"{self.name}:{self.ppd}:{self.z}:{','.join(repr(v) for v in self.bbox)}")


class GeoConf(BaseModel):
    """프로젝트 geo.yaml."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    bbox: tuple[float, float, float, float]
    admin1: list[str] = Field(default_factory=list)
    crimea_to_ua: bool = False
    tiers: list[TierConf] = Field(min_length=1)

    @field_validator("tiers")
    @classmethod
    def _unique(cls, v: list[TierConf]) -> list[TierConf]:
        names = [t.name for t in v]
        if len(names) != len(set(names)):
            raise ValueError(f"티어 이름 중복: {names}")
        return v


def load_conf(proj: Path) -> GeoConf:
    p = proj / "geo.yaml"
    if not p.exists():
        raise FileNotFoundError(f"geo.yaml 없음: {p}")
    return GeoConf.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))


def _fetch():  # noqa: ANN202 — tools/fetch_data 모듈
    sys.path.insert(0, str(REPO))
    import tools.fetch_data as fd  # noqa: PLC0415

    return fd


def ensure_ne(ne_dir: Path) -> None:
    fd = _fetch()
    for name in NE_FILES:
        if fd.download(fd.NE_URL.replace("{name}", name), ne_dir / f"{name}.geojson"):
            print(f"ne {name}", file=sys.stderr, flush=True)


def ensure_tiles(tiles_dir: Path, T: TierSpec) -> int:  # noqa: N803
    fd = _fetch()
    xr, yr = tile_range(T)
    jobs = [(x, y) for x in xr for y in yr]

    def one(xy: tuple[int, int]) -> bool:
        x, y = xy
        url = fd.TILE_URL.replace("{z}", str(T.z)).replace("{x}", str(x)).replace("{y}", str(y))
        return fd.download(url, tile_path(tiles_dir, T.z, x, y))

    with ThreadPoolExecutor(DOWNLOAD_WORKERS) as ex:
        got = sum(ex.map(one, jobs))
    print(f"tiles {T.name} z{T.z} {len(jobs)}장 (새로 받음 {got})", file=sys.stderr, flush=True)
    return len(jobs)


def prep(proj: Path, cache: Path = CACHE) -> dict:
    conf = load_conf(proj)
    ne_dir, tiles_dir, out = cache / "ne", cache / "tiles", proj / "assets"
    ensure_ne(ne_dir)
    geo, G = build_geo(ne_dir, conf.bbox, set(conf.admin1), conf.crimea_to_ua)  # noqa: N806
    out.mkdir(parents=True, exist_ok=True)
    pickle.dump(geo, open(out / "geo.pkl", "wb"))
    tiers, report = {}, {}
    for tc in conf.tiers:
        T = tc.spec()  # noqa: N806
        n = ensure_tiles(tiles_dir, T)
        lv, miss = build_tier(T, G, tiles_dir, out)
        tiers[T.name] = tier_record(T, tiles_dir, lv)
        report[T.name] = dict(tiles=n, levels=lv, land_miss=miss)
    pickle.dump(tiers, open(out / "tiers.pkl", "wb"))
    rep = dict(schema_version=1, bbox=list(conf.bbox), countries=len(geo["coarse"]),
               admin1={k: len(v) for k, v in geo["admin1"].items()}, places=len(geo["places"]),
               crimea_to_ua=conf.crimea_to_ua, tiers=report)
    (out / "geo_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main(argv: list[str] | None = None) -> int:
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="geo.prep")
    ap.add_argument("proj", type=Path)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    try:
        rep = prep(proj)
        drops = [dict(stage="geo", tier=n, land_miss=r["land_miss"]) for n, r in rep["tiers"].items() if r["land_miss"]]
        res = StageResult(ok=not drops, stage="geo", artifacts={"assets": str(proj / "assets"),
                                                                "report": str(proj / "assets" / "geo_report.json")},
                          drops=drops)
    except (OSError, ValueError) as ex:
        res = StageResult(ok=False, stage="geo", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
