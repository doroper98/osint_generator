"""지오 자산 단계 CLI (v2.2.0, D-0015 §1-4, 16 §4).

    python -m geo.prep <proj>   → <proj>/assets/{geo.pkl, tiers.pkl, base_*.png, geo_report.json}
    python -m geo.prep <proj> --res 1080p   → <proj>/assets/res_1080p/{tiers.pkl, base_*.png, geo_report.json}
        (v3.6.0 D-0066 작업 3, 19 §6 "티어 ppd 2.25배": ppd × k, 타일 줌 + round(log2 k). 480p 자산은 건드리지 않는다)

프로젝트 `geo.yaml`(권역·admin1 대상국·크림 재분류·티어)을 읽어 Natural Earth·지형 타일을 캐시(`data/geo/`)에
받고(`tools/fetch_data.py`의 다운로드 재사용), 지오메트리와 티어를 만든다. 마지막 줄 StageResult JSON.
land-miss(대표점이 육지로 칠해지지 않은 국가)는 `geo_report.json`에 남긴다. 티어 픽셀 면적이
`rules geo.land_miss_allow_px2` 미만이면 small(허용), 이상이면 drops 로 올려 ok=false(D29, P6).
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator
from shapely.geometry import box

from geo.prep_geometry import build_geo, coverage_reference
from geo.prep_tiers import TierSpec, build_tier, tier_record, tile_path, tile_range
from rules import load_rules

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


def classify_miss(miss: list[str], G: dict, ppd: int, ref: dict | None = None) -> dict:  # noqa: N803
    """land-miss 를 small(허용)·drops 로 가른다 — 면적(deg²) × ppd² < rules geo.land_miss_allow_px2 (D29).
    ref(원본 피처 합집합)가 있으면 그 면적으로 잰다 — G 가 국가 일부를 잃은 경우 잃은 면적까지 센다(v4.1.0 D-0078)."""
    thr = load_rules().geo.land_miss_allow_px2
    area = {k: (ref[k] if ref is not None and k in ref else G[k]).area for k in miss}
    px2 = {k: round(float(area[k]) * ppd * ppd, 2) for k in miss}
    return dict(small=[k for k in miss if px2[k] < thr], drops=[k for k in miss if px2[k] >= thr], px2=px2,
                allow_px2=thr)


def res_spec(tc: TierConf, k: float) -> TierSpec:
    """출력 프로파일 배율 k 의 장치 티어 — ppd × k(정수 반올림), 줌 + round(log2 k)(타일 해상도 ≈ ppd 관계 유지)."""
    if k == 1:
        return tc.spec()
    z = min(15, tc.z + round(math.log2(k)))
    return TierConf(name=tc.name, ppd=round(tc.ppd * k), z=z, bbox=tc.bbox).spec()


def assets_dir(proj: Path, res: str | None) -> Path:
    """480p(기본 프로파일)는 assets/, 그 밖은 assets/res_<프로파일>/ — engine.assets 가 같은 규칙으로 읽는다."""
    return proj / "assets" if res is None else proj / "assets" / f"res_{res}"


def prep(proj: Path, cache: Path = CACHE, res: str | None = None, k: float = 1.0) -> dict:
    conf = load_conf(proj)
    ne_dir, tiles_dir, out = cache / "ne", cache / "tiles", assets_dir(proj, res)
    ensure_ne(ne_dir)
    geo, G = build_geo(ne_dir, conf.bbox, set(conf.admin1), conf.crimea_to_ua)  # noqa: N806
    ref = coverage_reference(ne_dir, box(*conf.bbox))   # 면적 커버리지 기준(G 조립과 따로, D-0078)
    out.mkdir(parents=True, exist_ok=True)
    if res is None:
        pickle.dump(geo, open(out / "geo.pkl", "wb"))   # 지오메트리는 설계 좌표(도) — 해상도와 무관, 한 벌
    tiers, report = {}, {}
    for tc in conf.tiers:
        T = res_spec(tc, k)  # noqa: N806
        t0 = time.time()
        n = ensure_tiles(tiles_dir, T)
        t1 = time.time()
        ratios: dict[str, float] = {}
        lv, miss = build_tier(T, G, tiles_dir, out, k, ref, ratios)
        tiers[T.name] = tier_record(T, tiles_dir, lv)
        low = {k_: r for k_, r in sorted(ratios.items(), key=lambda kv: kv[1])[:5]}
        report[T.name] = dict(tiles=n, levels=lv, land_miss=classify_miss(miss, G, tc.ppd, ref), ppd=T.ppd, z=T.z,
                              fill_ratio=dict(checked=len(ratios), min_allowed=load_rules().geo.land_fill_min_ratio, lowest=low),
                              fetch_sec=round(t1 - t0, 1), build_sec=round(time.time() - t1, 1),
                              bytes=sum((out / f"base_{T.name}_{v}.png").stat().st_size for v in lv))
    pickle.dump(tiers, open(out / "tiers.pkl", "wb"))
    rep = dict(schema_version=1, bbox=list(conf.bbox), countries=len(geo["coarse"]),
               admin1={k_: len(v) for k_, v in geo["admin1"].items()}, places=len(geo["places"]),
               crimea_to_ua=conf.crimea_to_ua, res=res or "480p", k=k, tiers=report,
               country_area_deg2={k_: round(float(g.area), 3) for k_, g in G.items()})
    (out / "geo_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main(argv: list[str] | None = None) -> int:
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="geo.prep")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--res", default=None, help="출력 프로파일(config engine.output) — 기본 프로파일이 아니면 ppd × k 티어를 assets/res_<이름>/ 에")
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    try:
        from orchestrator.config import load_config  # noqa: PLC0415

        eng = load_config().engine
        name, prof = eng.profile(args.res)
        rname = None if name == eng.profile(None)[0] else name
        rep = prep(proj, res=rname, k=prof.height / load_rules().layout_480p.base.h)
        drops = [dict(stage="geo", tier=n, land_miss=r["land_miss"]["drops"], px2=r["land_miss"]["px2"])
                 for n, r in rep["tiers"].items() if r["land_miss"]["drops"]]
        res = StageResult(ok=not drops, stage="geo", artifacts={"assets": str(assets_dir(proj, rname)),
                                                                "report": str(assets_dir(proj, rname) / "geo_report.json")},
                          drops=drops)
    except (OSError, ValueError) as ex:
        res = StageResult(ok=False, stage="geo", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
