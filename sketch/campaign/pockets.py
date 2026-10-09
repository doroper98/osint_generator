"""포위망 — spec 레시피(조각·직접 점)를 순서대로 이어 붙인 다각형, 세력 색 옅은 채움 + 한 색 사선(SK-G2).
원본: 4d9dc65 `uranus_sketch.pocket_1123`·`pocket_1130`·`draw_pocket`.
"""

from __future__ import annotations

import cairo
import numpy as np

from engine.projection import View
from engine.style import C
from sketch.campaign.fronts import FrontData, ramps
from sketch.campaign.spec import CampaignSpec, Pocket
from sketch.common.draw import SK, hatch_mono, polyline, world

PK, F = SK.campaign.pocket, SK.fade


def build_polygon(p: Pocket, data: FrontData) -> np.ndarray:
    """레시피 → 다각형 꼭짓점(경위도 n×2). 조각 단계: lon_min(_of) 로 거르고, start_near 로 자르고, reverse."""
    parts = []
    for st in p.build:
        if st.points is not None:
            parts.append(np.array(st.points, float))
            continue
        P = data.piece(st.piece)   # type: ignore[arg-type]
        lo = st.lon_min if st.lon_min is not None else (data.piece(st.lon_min_of)[0, 0] if st.lon_min_of else None)
        if lo is not None:
            P = P[P[:, 0] >= lo]
        if st.start_near:
            target = data.piece(st.start_near)[-1]
            P = P[int(np.argmin(np.linalg.norm(P - target, axis=1))):]
        if st.reverse:
            P = P[::-1]
        parts.append(P)
    return np.vstack(parts)


class PocketLayer:
    def __init__(self, spec: CampaignSpec, data: FrontData) -> None:
        self.spec = spec
        self.polys = [build_polygon(p, data) for p in spec.pockets]
        self.drawn: dict[str, int] = {}

    def draw(self, ctx: cairo.Context, view: View, t: float) -> None:
        col = C[PK.color]
        for p, P in zip(self.spec.pockets, self.polys):
            a = ramps(p.show, t)
            if a <= F.min_alpha:
                continue
            ctx.save()
            ctx.new_path()
            polyline(ctx, view.to_screen_arr(world(P)), close=True)
            ctx.set_source_rgba(*col, PK.fill_alpha * a)
            ctx.fill_preserve()
            ctx.clip()
            hatch_mono(ctx, col, PK.hatch_alpha * a, PK.hatch_gap, PK.hatch_w)
            ctx.restore()
            self.drawn[f"pocket:{p.name}"] = self.drawn.get(f"pocket:{p.name}", 0) + 1
