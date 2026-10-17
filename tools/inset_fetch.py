"""inset_fetch — 위성 인셋 원본(정사각 png) 받기 (v7.3.0, 사용자 결정 D234 · back_and_forth D-0225 §8 경로 ①).

Esri World Imagery 타일(z/y/x, 키 불필요)을 N×N 모자이크로 받아 시설 좌표가 가운데 오도록 정사각으로 자른다.
가공은 자르기뿐(색·합성 없음). 원형 클립은 렌더러가 한다(UF-103). 출력은 공용 보관본 assets/library/insets/,
출처 기록은 같은 폴더 inset_sources.json 에 덧붙인다. 권리 = 비공개 시청 한정(rules media_beats.inset_licenses private_only).

    python tools/inset_fetch.py esri ryazan_esri 54.5624 39.7496 --z 14 --size 640 --out-px 512
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
INSETS = REPO / "assets" / "library" / "insets"
ESRI_TILE = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
TILE = 256


def _get(url: str, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "osint_generator inset_fetch"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:   # 네트워크 재시도(2·4·8초) 뒤 실패는 그대로 올린다(P6)
            if i == tries - 1:
                raise
            print(f"retry {url} {e}", flush=True)
            time.sleep(2 ** (i + 1))
    raise RuntimeError("unreachable")


def _world_px(lat: float, lon: float, z: int) -> tuple[float, float]:
    n = TILE * 2 ** z
    x = (lon + 180.0) / 360.0 * n
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return x, y


def esri(name: str, lat: float, lon: float, z: int, size: int, out_px: int) -> dict[str, object]:
    cx, cy = _world_px(lat, lon, z)
    x0, y0 = cx - size / 2, cy - size / 2
    tx0, ty0 = int(x0 // TILE), int(y0 // TILE)
    tx1, ty1 = int((x0 + size) // TILE), int((y0 + size) // TILE)
    mosaic = Image.new("RGB", ((tx1 - tx0 + 1) * TILE, (ty1 - ty0 + 1) * TILE))
    tiles: list[str] = []
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            url = ESRI_TILE.format(z=z, y=ty, x=tx)
            tiles.append(url)
            mosaic.paste(Image.open(io.BytesIO(_get(url))).convert("RGB"), ((tx - tx0) * TILE, (ty - ty0) * TILE))
    ox, oy = round(x0 - tx0 * TILE), round(y0 - ty0 * TILE)
    out = mosaic.crop((ox, oy, ox + size, oy + size)).resize((out_px, out_px), Image.LANCZOS)   # 화면 원 지름(720p ≈ 177px)보다 넉넉한 보관 크기
    INSETS.mkdir(parents=True, exist_ok=True)
    fname = f"inset_{name}.png"
    out.save(INSETS / fname)
    m_per_px = 156543.03392 * math.cos(math.radians(lat)) / 2 ** z
    rec: dict[str, object] = {
        "file": fname,
        "source": "Esri World Imagery (server.arcgisonline.com World_Imagery MapServer tiles)",
        "center_lat_lon": [lat, lon],
        "zoom": z,
        "tiles": tiles,
        "request_url": ESRI_TILE.format(z=z, y=int(cy // TILE), x=int(cx // TILE)),
        "crop": f"{len(tiles)}-tile mosaic, square center crop {size}x{size} px at facility point, resized to {out_px}x{out_px} (Lanczos), no other processing",
        "ground_m_per_px": round(m_per_px, 2),
        "ground_width_km": round(m_per_px * size / 1000, 2),
        "rights": "Esri World Imagery (Maxar et al.) — private viewing only (user decision D234); replace with NASA GIBS/Sentinel before any public release",
        "scope": "private_only",
        "fetched": time.strftime("%Y-%m-%d"),
        "md5": hashlib.md5((INSETS / fname).read_bytes()).hexdigest(),
    }
    src = INSETS / "inset_sources.json"
    data = json.loads(src.read_text(encoding="utf-8")) if src.exists() else {}
    data[name] = rec
    src.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("esri")
    e.add_argument("name")
    e.add_argument("lat", type=float)
    e.add_argument("lon", type=float)
    e.add_argument("--z", type=int, default=15)
    e.add_argument("--size", type=int, default=640)
    e.add_argument("--out-px", type=int, default=512)
    a = ap.parse_args(argv)
    rec = esri(a.name, a.lat, a.lon, a.z, a.size, a.out_px)
    print(json.dumps({k: rec[k] for k in ("file", "zoom", "ground_width_km", "md5")}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
