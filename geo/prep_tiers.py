"""지형 티어 래스터 (v2.2.0, prep3 `mosaic, lerp_col, build_tier`, 04 §1·§3.4).

    python -m geo.prep_tiers --geo assets/geo.pkl --tiles-dir data/geo/tiles --out assets --tier W:24:5:28,-12,140,48 [--tier …]

팔레트·힐셰이드·과장·블러 수치는 v3 사용자 합격 값 그대로다(19a §H, D27 — 새 리터럴 추가 없음).
- 타일 모자이크는 티어 박스가 덮는 타일 범위만 쓴다. 범위 안 타일이 하나라도 없으면 오류(15 P6).
- 박스 클램프: 경도 ±180, 위도 ±85.0511(웹 메르카토르 한계)로 자른다(부동소수 초과 방지).
- 커버리지 검사: 대표점이 티어 안에 있는 국가의 육지 마스크가 비면 `land-miss`로 돌려준다.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from geo.prep_geometry import rings

MERC_LAT_MAX = 85.0511287798
TILE = 256


def ym(lat: "np.ndarray | float") -> "np.ndarray":
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


@dataclass(frozen=True)
class TierSpec:
    name: str
    ppd: int
    z: int
    lon0: float
    lat0: float
    lon1: float
    lat1: float

    @classmethod
    def parse(cls, s: str) -> "TierSpec":
        """NAME:ppd:z:lon0,lat0,lon1,lat1"""
        try:
            name, ppd, z, bb = s.split(":")
            lon0, lat0, lon1, lat1 = (float(x) for x in bb.split(","))
        except ValueError as ex:
            raise ValueError(f"티어 형식은 NAME:ppd:z:lon0,lat0,lon1,lat1: {s!r}") from ex
        return clamp_box(cls(name, int(ppd), int(z), lon0, lat0, lon1, lat1))


def clamp_box(T: TierSpec) -> TierSpec:  # noqa: N803
    lon0, lon1 = max(-180.0, T.lon0), min(180.0, T.lon1)
    lat0, lat1 = max(-MERC_LAT_MAX, T.lat0), min(MERC_LAT_MAX, T.lat1)
    if not (lon0 < lon1 and lat0 < lat1):
        raise ValueError(f"티어 {T.name} 박스가 비었다: {T}")
    return TierSpec(T.name, T.ppd, T.z, lon0, lat0, lon1, lat1)


def lonlat_to_tile(lon: float, lat: float, z: int) -> tuple[int, int]:
    """웹 메르카토르 타일 좌표. 경계(lon=180, lat=±85.05)는 마지막 타일로 클램프한다."""
    n = 2 ** z
    x = int(math.floor((lon + 180.0) / 360.0 * n))
    lat_r = math.radians(max(-MERC_LAT_MAX, min(MERC_LAT_MAX, lat)))
    y = int(math.floor((1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n))
    return max(0, min(n - 1, x)), max(0, min(n - 1, y))


def tile_range(T: TierSpec) -> tuple[range, range]:  # noqa: N803
    x0, y0 = lonlat_to_tile(T.lon0, T.lat1, T.z)
    x1, y1 = lonlat_to_tile(T.lon1, T.lat0, T.z)
    return range(x0, x1 + 1), range(y0, y1 + 1)


def tile_path(tiles_dir: Path, z: int, x: int, y: int) -> Path:
    return tiles_dir / f"z{z}" / f"{x}_{y}.png"


def mosaic(tiles_dir: Path, T: TierSpec) -> tuple[np.ndarray, int, int]:  # noqa: N803
    """terrarium RGB → 고도(m). 범위 밖 타일은 읽지 않고, 범위 안 타일이 없으면 오류."""
    xr, yr = tile_range(T)
    missing = [(x, y) for x in xr for y in yr
               if not tile_path(tiles_dir, T.z, x, y).exists() or tile_path(tiles_dir, T.z, x, y).stat().st_size <= 100]
    if missing:
        raise FileNotFoundError(f"티어 {T.name} z{T.z} 타일 {len(missing)}장 없음(예 {missing[:3]}) — `python -m geo.prep` 가 받는다")
    M = np.zeros((len(yr) * TILE, len(xr) * TILE), np.float32)  # noqa: N806
    for x in xr:
        for y in yr:
            a = np.asarray(Image.open(tile_path(tiles_dir, T.z, x, y)).convert("RGB"), np.float32)
            M[(y - yr.start) * TILE:(y - yr.start + 1) * TILE, (x - xr.start) * TILE:(x - xr.start + 1) * TILE] = \
                a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    return M, xr.start, yr.start


def lerp_col(stops: list, v: np.ndarray) -> np.ndarray:
    v = np.clip(v, stops[0][0], stops[-1][0])
    out = np.zeros(v.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(stops[:-1], stops[1:]):
        m = (v >= a) & (v <= b)
        f = ((v - a) / (b - a))[m][:, None]
        out[m] = np.array(ca, np.float32) * (1 - f) + np.array(cb, np.float32) * f
    return out


def hexc(h: str) -> list[int]:
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


# v3 팔레트 (19a §H, 사용자 합격 값)
LAND_STOPS = [(0, "#2b313a"), (400, "#30353c"), (1500, "#3b3a3a"), (4000, "#4b4640")]
SEA_STOPS = [(0, "#1c4a66"), (60, "#18415c"), (400, "#11304a"), (2000, "#0c2236"), (6000, "#081626")]
COAST_GLOW = "#3a9cb8"


def rasterize_land(G: dict, T: TierSpec, W: int, H: int, dppd: float | None = None) -> tuple[Image.Image, list[str]]:  # noqa: N803
    """육지 마스크(L) + 커버리지 누락 국가 목록. dppd = 설계 ppd(단순화 허용 오차 구간, 기본 T.ppd)."""
    tol = 0.02 if (T.ppd if dppd is None else dppd) < 64 else 0.003
    mimg = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(mimg)
    top = ym(T.lat1)
    for g in G.values():
        for r in rings(g, tol):
            xs = (r[:, 0] - T.lon0) * T.ppd
            ys = (top - ym(r[:, 1])) * T.ppd
            if xs.max() < 0 or xs.min() > W or ys.max() < 0 or ys.min() > H:
                continue
            dr.polygon(list(zip(xs.tolist(), ys.tolist())), fill=255)
    miss = []
    for k, g in G.items():
        rp = g.representative_point()
        x = (rp.x - T.lon0) * T.ppd
        y = (top - ym(rp.y)) * T.ppd
        if 0 <= x < W and 0 <= y < H and mimg.getpixel((int(x), int(y))) < 128:
            miss.append(k)
    return mimg, miss


def build_tier(T: TierSpec, G: dict, tiles_dir: Path, out_dir: Path, k: float = 1.0) -> tuple[list[int], list[str]]:  # noqa: N803
    """base_{name}_{ppd}.png + 반·4분의 1 해상도 2단. (levels, land-miss).

    k ≠ 1(v3.6.0 D-0066 작업 3, 출력 프로파일 k = H/480): T 는 이미 ppd × k·확대 줌으로 만든 장치 티어다. 설계 ppd(= T.ppd / k)
    구간으로 고르는 값(단순화 허용 오차·지형 과장)은 480p 와 같게, 화소 단위 반경(육지 가장자리·해안 광채 블러)은 × k 로 —
    축소하면 480p 베이스와 같은 모양이 되게 한다. k=1 이면 종전과 같은 계산."""
    t0 = time.time()
    dppd = T.ppd / k                      # 설계(480p) ppd
    M, x0, y0 = mosaic(tiles_dir, T)  # noqa: N806
    S = TILE * 2 ** T.z  # noqa: N806
    ppd = T.ppd
    W = int(round((T.lon1 - T.lon0) * ppd))  # noqa: N806
    H = int(round((ym(T.lat1) - ym(T.lat0)) * ppd))  # noqa: N806
    ext = ((T.lon0 + 180) / 360 * S - x0 * TILE, (1 - ym(T.lat1) / 180) / 2 * S - y0 * TILE,
           (T.lon1 + 180) / 360 * S - x0 * TILE, (1 - ym(T.lat0) / 180) / 2 * S - y0 * TILE)
    E = np.asarray(Image.fromarray(M, "F").transform((W, H), Image.EXTENT, ext, Image.BICUBIC), np.float32)  # noqa: N806
    lat_rows = np.degrees(2 * np.arctan(np.exp(np.radians(ym(T.lat1) - (np.arange(H) + 0.5) / ppd))) - np.pi / 2)
    mpp = (111320 * np.cos(np.radians(lat_rows)) / ppd)[:, None]
    mimg, miss = rasterize_land(G, T, W, H, dppd)
    land = np.asarray(mimg.filter(ImageFilter.GaussianBlur(0.6 * k)), np.float32) / 255
    ex = 2.8 if dppd < 64 else 2.0
    gy, gx = np.gradient(np.maximum(E, 0) * ex)
    gx /= mpp
    gy /= mpp
    az, alt = math.radians(315), math.radians(42)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    hs = np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    lc = lerp_col([(v, hexc(c)) for v, c in LAND_STOPS], np.clip(E, 0, 4000))
    lc = lc * np.clip((0.58 + 0.95 * (hs - np.sin(alt)))[..., None], 0.5, 1.5)
    sc = lerp_col([(v, hexc(c)) for v, c in SEA_STOPS], np.clip(-E, 0, 6000))
    glow = np.asarray(mimg.filter(ImageFilter.GaussianBlur((3 if dppd < 64 else 8) * k)), np.float32)[..., None] / 255
    sc = sc + np.array(hexc(COAST_GLOW), np.float32) * glow * 0.2
    out = sc * (1 - land[..., None]) + lc * land[..., None]
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    out_dir.mkdir(parents=True, exist_ok=True)
    lv = [ppd]
    img.save(out_dir / f"base_{T.name}_{ppd}.png")
    cur = img
    for k in range(2):
        cur = cur.resize((cur.width // 2, cur.height // 2), Image.LANCZOS)
        cur.save(out_dir / f"base_{T.name}_{ppd // 2 ** (k + 1)}.png")
        lv.append(ppd // 2 ** (k + 1))
    print(f"tier {T.name} {W}x{H} {time.time() - t0:.0f}s  land-miss={miss}", file=sys.stderr, flush=True)
    return lv, miss


def tier_record(T: TierSpec, tiles_dir: Path, levels: list[int]) -> dict:  # noqa: N803
    """tiers.pkl 한 항목(02 §2.5, schemas.engine_models.Tier)."""
    return dict(lon0=T.lon0, lon1=T.lon1, lat0=T.lat0, lat1=T.lat1, ppd=T.ppd, tiles=str(tiles_dir / f"z{T.z}"), z=T.z,
                levels=levels)


def main(argv: list[str] | None = None) -> int:
    import pickle  # noqa: PLC0415

    from geo.prep_geometry import build_geo, parse_bbox  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="geo.prep_tiers")
    ap.add_argument("--tier", action="append", required=True, help="NAME:ppd:z:lon0,lat0,lon1,lat1 (반복)")
    ap.add_argument("--bbox", required=True, help="국가 지오메트리 권역")
    ap.add_argument("--ne-dir", type=Path, required=True)
    ap.add_argument("--tiles-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    _, G = build_geo(args.ne_dir, parse_bbox(args.bbox), set())  # noqa: N806
    tiers = {}
    for s in args.tier:
        T = TierSpec.parse(s)  # noqa: N806
        lv, _ = build_tier(T, G, args.tiles_dir, args.out)
        tiers[T.name] = tier_record(T, args.tiles_dir, lv)
    pickle.dump(tiers, open(args.out / "tiers.pkl", "wb"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
