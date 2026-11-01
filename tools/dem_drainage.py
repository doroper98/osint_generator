"""고도 타일에서 수계(와디·개울) 선 뽑기 (v7.4.0 전쟁사 구상 컷 A, back_and_forth D-0604 §1-A, UF-250).

    python tools/dem_drainage.py projects/<pid> [--tier K]
        → projects/<pid>/drainage.json(경위도 선 목록, 저장소 미추적) + drainage_sources.json

geo.prep 가 받아 둔 Terrarium 고도 타일(같은 출처·같은 고지)로 D8 흐름 방향·흐름 누적을 계산하고,
누적 셀 수가 임계 이상인 셀을 하류로 이어 선을 만든다. 임계·내려 받기 배수는 rules geo.drainage(코드 상수 없음, 15 P3).
평탄지(이웃이 모두 같거나 높음)는 흐름이 끊긴다 — 강이 지어내지지 않는다(평야에 선이 적은 것은 자료 그대로).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from geo.prep import CACHE, load_conf  # noqa: E402
from geo.prep_tiers import TILE, TierSpec, mosaic  # noqa: E402
from rules import load_rules  # noqa: E402

OUT_FILE = "drainage.json"
SRC_FILE = "drainage_sources.json"
NEIGHBORS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def pixel_lonlat(px: float, py: float, z: int, x0: int, y0: int) -> tuple[float, float]:
    """모자이크 픽셀 → 경위도(웹 메르카토르 역변환)."""
    n = TILE * 2 ** z
    gx, gy = x0 * TILE + px, y0 * TILE + py
    lon = gx / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * gy / n))))
    return lon, lat


def receivers(h: np.ndarray) -> np.ndarray:
    """D8 — 셀마다 가장 가파르게 내려가는 이웃의 1차원 번호(없으면 −1)."""
    H, W = h.shape  # noqa: N806
    best = np.zeros_like(h)
    rec = np.full(h.shape, -1, np.int64)
    pad = np.pad(h, 1, constant_values=np.inf)
    idx = np.arange(H * W).reshape(H, W)
    pidx = np.pad(idx, 1, constant_values=-1)
    for dy, dx in NEIGHBORS:
        nb = pad[1 + dy:1 + dy + H, 1 + dx:1 + dx + W]
        drop = (h - nb) / math.hypot(dy, dx)
        better = drop > best
        best = np.where(better, drop, best)
        rec = np.where(better, pidx[1 + dy:1 + dy + H, 1 + dx:1 + dx + W], rec)
    return rec.ravel()


def accumulate(h: np.ndarray, rec: np.ndarray) -> np.ndarray:
    acc = np.ones(h.size, np.int64)
    for i in np.argsort(-h.ravel(), kind="stable"):
        r = rec[i]
        if r >= 0:
            acc[r] += acc[i]
    return acc


def trace(acc: np.ndarray, rec: np.ndarray, thr: int) -> list[list[int]]:
    """임계 이상 셀을 머리(위쪽에 임계 이상 셀이 없는 셀)부터 하류로 잇는다. 이미 지난 셀에 닿으면 그 셀에서 끊는다(합류)."""
    on = acc >= thr
    has_up = np.zeros(acc.size, bool)
    src = np.flatnonzero(on & (rec >= 0))
    has_up[rec[src][on[rec[src]]]] = True
    seen = np.zeros(acc.size, bool)
    lines = []
    for head in np.flatnonzero(on & ~has_up):
        ln, c = [int(head)], int(head)
        while not seen[c]:
            seen[c] = True
            r = int(rec[c])
            if r < 0:
                break
            ln.append(r)
            c = r
        if len(ln) > 1:
            lines.append(ln)
    return lines


def run(project: Path, tier: str) -> dict:
    D = load_rules().geo.drainage  # noqa: N806
    conf = load_conf(project)
    tc = next(t for t in conf.tiers if t.name == tier)
    T = TierSpec(tc.name, tc.ppd, D.z if D.z is not None else tc.z, *tc.bbox)  # noqa: N806
    M, x0, y0 = mosaic(CACHE / "tiles", T)
    k = D.downsample
    h = M[: M.shape[0] // k * k, : M.shape[1] // k * k].reshape(M.shape[0] // k, k, M.shape[1] // k, k).mean(axis=(1, 3))
    h = np.where(h < D.sea_level_m, np.inf, h)   # 바다는 흐름의 끝(셀 자신은 선이 되지 않는다)
    rec = receivers(h)
    acc = accumulate(np.where(np.isinf(h), -1e9, h), rec)
    W_ = h.shape[1]
    lines = []
    for ln in trace(acc, rec, D.min_cells):
        pts = [pixel_lonlat((i % W_ + 0.5) * k, (i // W_ + 0.5) * k, T.z, x0, y0) for i in ln[:: D.step]]
        if len(pts) >= 2:
            lines.append([[round(a, 5), round(b, 5)] for a, b in pts])
    (project / OUT_FILE).write_text(json.dumps(lines), encoding="utf-8")
    rec_ = {"schema_version": 1, "tier": tier, "z": T.z, "downsample": k, "min_cells": D.min_cells, "lines": len(lines),
            "source": "Terrarium 고도 타일(geo.prep 와 같은 출처 — tools/fetch_data.TILE_URL)", "rule": "rules geo.drainage"}
    (project / SRC_FILE).write_text(json.dumps(rec_, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec_


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="고도 타일 → 수계 선(D8 흐름 누적, rules geo.drainage)")
    ap.add_argument("project", type=Path)
    ap.add_argument("--tier", default="K")
    a = ap.parse_args(argv)
    print(json.dumps(run(a.project, a.tier), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
