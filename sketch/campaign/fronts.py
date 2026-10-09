"""전선·강 — 날짜별 전선은 추축(파랑) 선과 그 선을 화면에서 옮긴 소련(빨강) 선의 이중선(원 지도 범례 방식), 강은 정합한 물길.
원본: 4d9dc65 `uranus_sketch.front_line`·`draw_rivers`. 수치 = rules sketch.campaign.front·river, 데이터 = fronts.json(prep_georef).
"""

from __future__ import annotations

import json
from pathlib import Path

import cairo
import numpy as np

from engine.layers.routes import glow_line
from engine.projection import View
from engine.style import C
from engine.timebase import clamp01, ease_io, smooth
from sketch.campaign.spec import CampaignSpec, Ramp
from sketch.common.draw import SK, polyline, world
from sketch.common.geodesy import NORMAL_EPS

CA, F = SK.campaign, SK.fade


def ramps(keys: list[Ramp], t: float) -> float:
    """Ramp 목록의 곱(없으면 1)."""
    v = 1.0
    for k in keys:
        v *= k.from_ + (k.to - k.from_) * smooth((t - k.t) / k.sec)
    return v


class FrontData:
    """fronts.json — 층 → 편 → 조각, 강, 정합 계수·잔차."""

    def __init__(self, path: Path) -> None:
        d = json.loads(path.read_text(encoding="utf-8"))
        self.raw = d
        self.layers: dict = d["layers"]
        self.rivers: dict = d["rivers"]
        self.residual_deg: float = d["residual_deg"]
        self.coef: dict[str, list[float]] = d["coef"]
        self.source: str = d["source"]

    def piece(self, ref: str) -> np.ndarray:
        """'층:편:번호' → 경위도 배열. 없으면 오류."""
        date, side, idx = ref.split(":")
        try:
            return np.array(self.layers[date][side][int(idx)], float)
        except (KeyError, IndexError) as e:
            raise KeyError(f"전선 조각 {ref} 가 fronts.json 에 없다") from e


def front_line(ctx: cairo.Context, view: View, P: np.ndarray, prog: float, a: float, dashed: bool) -> None:
    """전선 이중선. 소련 선 = 추축 선을 화면 법선 방향으로 offset_px 옮긴 같은 모양."""
    if a <= F.min_alpha or prog <= 0:
        return
    Fr = CA.front
    S = view.to_screen_arr(world(P))
    n = max(2, int(len(S) * prog))
    S = S[:n]
    d = np.gradient(S, axis=0)
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), NORMAL_EPS)
    dash = Fr.dash if dashed else None
    glow_line(ctx, S, C[Fr.axis_color], a, Fr.axis_w, dash=dash)
    glow_line(ctx, S + nrm * Fr.offset_px, C[Fr.soviet_color], a, Fr.soviet_w, dash=dash)


class FrontLayer:
    def __init__(self, spec: CampaignSpec, data: FrontData) -> None:
        self.spec, self.data = spec, data
        self.pieces = [[data.piece(r) for r in L.pieces] for L in spec.fronts.layers]
        self.drawn: dict[str, int] = {}

    def draw_rivers(self, ctx: cairo.Context, view: View) -> None:
        R = CA.river
        for kind, (wd, al) in (("minor", R.minor), ("major", R.major)):
            for r in self.data.rivers.get(kind, []):
                ctx.new_path()
                polyline(ctx, view.to_screen_arr(world(np.array(r))))
                ctx.set_source_rgba(*R.rgb, al)
                ctx.set_line_width(wd)
                ctx.set_line_join(cairo.LINE_JOIN_ROUND)
                ctx.stroke()

    def draw(self, ctx: cairo.Context, view: View, t: float) -> None:
        for L, ps in zip(self.spec.fronts.layers, self.pieces):
            t0, sec = L.grow
            prog = ease_io(clamp01((t - t0) / sec))
            a = ramps(L.dim, t)
            for P in ps:
                front_line(ctx, view, P, prog, a, L.dashed)
            if prog > 0:
                self.drawn[f"front:{L.date}"] = self.drawn.get(f"front:{L.date}", 0) + 1
