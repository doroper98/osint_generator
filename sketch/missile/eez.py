"""층 1: 해양 경계(EEZ) — 나라 색 옅은 채움 + 바다 쪽 경계 점선, 중첩 주장 두 색 사선(SK-H4), 공동 관리 점무늬,
서해 남북 두 주장선(NLL 개략·북한 1999 선). CONVENTIONS §4. 원본: 4d9dc65 `sketch_d1.EEZ`.

수치 = rules sketch.eez·text·fade, 사실·시각·문구 = spec.eez.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import cairo
import numpy as np
from shapely.geometry import Point, shape

from engine.layers.routes import glow_line
from engine.projection import View
from engine.stage import ym
from engine.style import C, H_OUT, W_OUT
from engine.timebase import clamp01, ease_io, smooth, window
from engine.typography import text
from sketch.common.draw import SK, WHITE, Overlay, dots, hatch, path_rings, world
from sketch.missile.spec import ClaimLine, MissileSpec, Region

E, T, F = SK.eez, SK.text, SK.fade


class EezLayer:
    def __init__(self, spec: MissileSpec, project: Path) -> None:
        self.spec = spec.eez
        path = project / spec.eez.file
        d = json.loads(path.read_text(encoding="utf-8"))
        self.source: str = d["source"]
        self.feat: list[dict] = d["features"]
        keys = {(f["code"], f["kind"]) for f in self.feat}
        need = {(c, "eez") for c in self.spec.nations} | {(r.code, r.kind) for r in self.spec.regions} \
            | {(c.code, "claim_line") for c in self.spec.claim_lines}
        missing = sorted(need - keys)
        if missing:
            raise ValueError(f"{path}: spec 이 부르는 경계가 없다 {missing} — prep_eez 를 다시 돌린다")
        self.regions = {(r.code, r.kind): r for r in self.spec.regions}
        self.claims = {c.code: c for c in self.spec.claim_lines}
        self.label_ll: dict[str, tuple[float, float]] = {}
        for f in self.feat:
            if f["kind"] == "eez" and f["code"] in self.spec.nations:
                geo = shape({"type": "MultiPolygon", "coordinates": f["polys"]})
                p = self.spec.nations[f["code"]].label_at
                self.label_ll[f["code"]] = p if geo.contains(Point(p)) else tuple(f["rep"])
        self.drawn: dict[str, int] = {}

    def _note(self, key: str) -> None:
        self.drawn[key] = self.drawn.get(key, 0) + 1

    @staticmethod
    def _focus(item: Region | ClaimLine, t: float, dim: float) -> float:
        if item.focus is None:
            return dim
        return max(dim, window(t, item.focus[0], item.focus[1], E.focus_in, E.focus_out))

    def _item(self, f: dict) -> tuple[float, Region | ClaimLine | None] | None:
        if f["kind"] == "eez":
            n = self.spec.nations.get(f["code"])
            return (n.t, None) if n else None
        if f["kind"] == "claim_line":
            c = self.claims.get(f["code"])
            return (c.t, c) if c else None
        r = self.regions.get((f["code"], f["kind"]))
        return (r.t, r) if r else None

    def colors(self, r: Region) -> list[tuple[float, float, float]]:
        """중첩 수역 사선 색 = 청구국 나라 색(SK-H4)."""
        return [C[self.spec.nations[c].color] for c in r.claimants]

    def draw(self, ctx: cairo.Context, view: View, t: float, dim: float, pulse: float) -> None:
        for f in self.feat:
            it = self._item(f)
            if it is None:
                continue
            t0, item = it
            d_ = self._focus(item, t, dim) if item is not None else dim
            a = smooth((t - t0) / E.appear_sec) * d_
            if a <= E.min_alpha:
                continue
            if f["kind"] == "claim_line":
                self._claim(ctx, view, t, f, item, a)   # type: ignore[arg-type]
                continue
            ctx.save()
            ctx.new_path()
            path_rings(ctx, view, [r for poly in f["polys"] for r in poly])
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            if f["kind"] == "eez":
                self._eez(ctx, view, f, a, pulse)
            else:
                self._region(ctx, view, f, item, a)   # type: ignore[arg-type]
            ctx.restore()

    def _eez(self, ctx: cairo.Context, view: View, f: dict, a: float, pulse: float) -> None:
        col = C[self.spec.nations[f["code"]].color]
        boost = pulse if f["code"] == self.spec.pulse else 0.0
        ctx.set_source_rgba(*col, (E.fill_alpha + E.pulse_fill_alpha * boost) * a)
        ctx.fill()
        for ln in f["lines"]:   # 바다 쪽 경계만(해안선과 겹치는 구간은 prep_eez 때 뺐다)
            if len(ln) < 2 or math.dist(ln[0], ln[-1]) + len(ln) * E.min_edge_step_deg < E.min_edge_len_deg:
                continue
            S = view.to_screen_arr(world(np.array(ln)))
            ctx.move_to(*S[0])
            for q in S[1:]:
                ctx.line_to(*q)
        ctx.set_source_rgba(*col, (E.edge_alpha + E.pulse_edge_alpha * boost) * a)
        ctx.set_line_width(E.edge_w + E.pulse_edge_w * boost)
        ctx.set_dash(E.dash)
        ctx.stroke()
        ctx.set_dash([])
        self._note("eez_fill")

    def _region(self, ctx: cairo.Context, view: View, f: dict, r: Region, a: float) -> None:
        ctx.clip_preserve()
        ctx.new_path()
        if r.kind == "joint":
            dots(ctx, C[r.color], E.dots_alpha * a)   # type: ignore[index]
            col_line = C[r.color]   # type: ignore[index]
            self._note("joint_dots")
        else:
            cols = self.colors(r)
            hatch(ctx, cols, E.hatch_alpha * a, E.hatch_gap, E.hatch_w)
            col_line = cols[0]
            self._note(f"overlap_hatch_colors:{len(set(cols))}")
        ctx.reset_clip()
        if r.edge:
            path_rings(ctx, view, [rr for poly in f["polys"] for rr in poly])
            ctx.set_source_rgba(*col_line, E.overlap_edge_alpha * a)
            ctx.set_line_width(E.overlap_edge_w)
            ctx.stroke()

    def _claim(self, ctx: cairo.Context, view: View, t: float, f: dict, c: ClaimLine, a: float) -> None:
        col = C[c.color]
        grow = ease_io(clamp01((t - c.t) / E.claim_grow_sec))
        for i, ln in enumerate(f["lines"]):
            S = view.to_screen_arr(world(np.array(ln)))
            dense = np.concatenate([np.linspace(S[j], S[j + 1], E.claim_dense, endpoint=False) for j in range(len(S) - 1)]
                                   + [S[-1:]])
            n = max(2, int(len(dense) * grow))
            glow_line(ctx, dense[:n], col, a * (E.claim_ext_alpha if i else 1), E.claim_w[1] if i else E.claim_w[0],
                      dash=E.claim_ext_dash if i else c.dash)
        if c.vertices:   # 발표 꼭짓점(발표 좌표) 표시
            h = E.vertex_half
            for lon, lat in f["lines"][0][:-1]:
                x, y = view.to_screen(lon, ym(lat))
                ctx.rectangle(x - h, y - h, 2 * h, 2 * h)
                ctx.set_source_rgba(*col, a * grow)
                ctx.fill()
        self._note(f"claim_line:{c.code}")

    def labels(self, ctx: cairo.Context, view: View, t: float, dim: float, ov: Overlay) -> None:
        N = T.eez_name
        for code, (lon, lat) in self.label_ll.items():
            n = self.spec.nations[code]
            a = smooth((t - n.t - E.label_delay) / E.label_in) * dim * (1 - smooth((t - self.spec.labels_end) / E.label_out))
            x, y = view.to_screen(lon, ym(lat))
            if 0 < x < W_OUT and 0 < y < H_OUT:
                text(ctx, n.label, x, y, N.size, N.font, C[n.color], N.alpha * a, N.halo, "c")
        for r in self.spec.regions:
            d_ = self._focus(r, t, dim)
            a = window(t, (r.label_t if r.label_t is not None else r.t) + E.region_label_delay, r.end, F.win_in, F.win_out) * d_
            if a <= E.min_alpha:
                continue
            f = next(f for f in self.feat if (f["code"], f["kind"]) == (r.code, r.kind))
            tx, ty = view.to_screen(r.at[0], ym(r.at[1]))
            px, py = view.to_screen(f["rep"][0], ym(f["rep"][1]))
            ctx.move_to(px, py)
            ctx.line_to(tx + (E.leader_dx if r.anchor == "l" else -E.leader_dx), ty + E.leader_dy)
            ctx.set_source_rgba(*WHITE, E.leader_alpha * a)
            ctx.set_line_width(E.leader_w)
            ctx.stroke()
            ov.label2(tx, ty, a, r.label, r.sub, sub_col=C["muted"], anchor=r.anchor)
        for c in self.spec.claim_lines:
            a = window(t, c.t + E.claim_label_delay, c.end, F.win_in, F.win_out)
            if a > E.min_alpha:
                tx, ty = view.to_screen(c.at[0], ym(c.at[1]))
                ov.label2(tx, ty, a, c.label, c.sub, sub_col=C[c.color], anchor=c.anchor)
            if c.ext_tag:
                f = next(f for f in self.feat if f["code"] == c.code and f["kind"] == "claim_line")
                a = window(t, c.t + E.ext_tag_delay, c.end, F.win_in, F.win_out)
                if a > E.min_alpha and len(f["lines"]) > 1:
                    lon, lat = f["lines"][1][-1]
                    x, y = view.to_screen(lon, ym(lat))
                    ov.tag(c.ext_tag.text, x + E.ext_tag_dx, y + E.ext_tag_dy, C[c.ext_tag.color], a)
        p = self.spec.places
        if p is not None:
            a = window(t, p.t0, p.t1, F.win_in, F.win_out)
            if a > E.min_alpha:
                P = T.place
                hw, top, bot = E.place_box
                for it in p.items:
                    x, y = view.to_screen(it.lon, ym(it.lat))
                    ctx.arc(x, y, E.place_dot_r, 0, 2 * math.pi)
                    ctx.set_source_rgba(*WHITE, a)
                    ctx.fill()
                    ov.defer(lambda x=x, y=y, s=it.name, a=a: text(ctx, s, x, y + P.dy, P.size, P.font, WHITE, a, P.halo, "c"),
                             (x - hw, y + top, x + hw, y + bot))
