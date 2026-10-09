"""전황 작전도 장면 — 지형(현대 국경·지명 없음) 위에 강·포위망·전선·화살표·부대·집게·지명·태그·범례·출처·날짜·엔딩.
원본: 4d9dc65 `uranus_sketch.Scene.render`(그리는 순서 그대로). 수치 = rules sketch.campaign·fade·text, 사실·연출 = spec.
"""

from __future__ import annotations

import math
from pathlib import Path

import cairo
import numpy as np

from engine.assets import Assets, load_labels
from engine.projection import View
from engine.stage import MercatorStage, ym
from engine.style import C, CARD_BG, DATE_BADGE, H_OUT, W_OUT, Output, output_profile
from engine.timebase import ease_out, smooth, window
from engine.typography import rrect, text, tw
from sketch.campaign.arrows import ArrowLayer
from sketch.campaign.fronts import FrontData, FrontLayer
from sketch.campaign.pockets import PocketLayer
from sketch.campaign.spec import CampaignSpec
from sketch.campaign.units import UnitLayer, unit_symbol
from sketch.common.camera import CameraPath
from sketch.common.draw import SK, WHITE
from sketch.common.render import BGRA

CA, F, T = SK.campaign, SK.fade, SK.text
LABELS_FILE = "labels.yaml"
BGRX = "BGRX"


class CampaignScene:
    def __init__(self, spec: CampaignSpec, project: Path, res: str) -> None:
        self.spec = spec
        self.out: Output = output_profile(res)
        default = output_profile(None).name
        assets = Assets(project, load_labels(project / LABELS_FILE), None if self.out.name == default else self.out.name)
        self.stage = MercatorStage(assets, out=self.out)
        self.data = FrontData(project / spec.fronts.file)
        self.fronts = FrontLayer(spec, self.data)
        self.pockets = PocketLayer(spec, self.data)
        self.arrows = ArrowLayer(spec)
        self.units = UnitLayer(spec)
        cam = SK.camera
        self.camera = CameraPath(tuple(spec.shots), spec.duration_sec, cam.push_in[spec.kind], cam.hold_min_sec)
        self.res_boxes: list[tuple[float, list]] = []
        self.drawn: dict[str, int] = {}

    def features_drawn(self) -> dict[str, int]:
        out = dict(self.drawn)
        for layer in (self.fronts, self.pockets, self.arrows, self.units):
            for k, v in layer.drawn.items():
                out[k] = out.get(k, 0) + v
        return out

    def _note(self, key: str) -> None:
        self.drawn[key] = self.drawn.get(key, 0) + 1

    def frame(self, t: float) -> bytes:
        sp, OP = self.spec, self.out
        view = View(self.stage, np.array(self.camera.at(t)))
        im = self.stage.base_image(view, OP)            # 지형만 — 현대 국경·행정구역선·현대 지명은 그리지 않는다
        buf = bytearray(im.tobytes("raw", BGRX))
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, OP.width, OP.height, OP.width * BGRA)
        ctx = cairo.Context(surf)
        ctx.translate(OP.pad_x, 0)
        ctx.scale(OP.k, OP.k)
        ctx.set_source_rgba(*CA.terrain_dim)
        ctx.paint()
        self.fronts.draw_rivers(ctx, view)
        res: list = []
        labels: list = []
        self.pockets.draw(ctx, view, t)
        self.fronts.draw(ctx, view, t)
        self.arrows.draw(ctx, view, t, labels)
        self.units.draw(ctx, view, t, res)
        self._pincer(ctx, view, t, res)
        self._places(ctx, view, t, res)
        L = CA.arrow_label
        for name, (x, y), la in labels:
            text(ctx, name, x, y + L.dy, L.size, L.font, tuple(CA.arrow_label_rgb), la, L.halo, "c")
        for tg in sp.tags:
            a = window(t, tg.t0, tg.t1, tg.fin, tg.fout)
            if a > F.min_alpha:
                for lon, lat in tg.at:
                    x, y = view.to_screen(lon, ym(lat))
                    self._tag(ctx, tg.text, x, y + tg.dy, C[tg.color], a)
        self.res_boxes.append((t, list(res)))
        self._legend(ctx, t)
        self._source(ctx, t)
        self._date(ctx, t)
        self._end(ctx, t)
        fa = 1 - min(smooth(t / F.open_sec), smooth((sp.duration_sec - t) / F.close_sec))
        if fa > F.black_min:
            ctx.set_source_rgba(0, 0, 0, fa)
            ctx.paint()
        surf.flush()
        return bytes(buf)

    # ---------------------------------------------------------------- 요소
    def _tag(self, ctx: cairo.Context, s: str, x: float, y: float, col: tuple, a: float) -> None:
        G = CA.tag
        w = tw(ctx, s, G.size, G.font) + G.pad_w
        xx = x - w / 2
        rrect(ctx, xx, y + G.box_dy, w, G.box_h, G.radius)
        ctx.set_source_rgba(*CARD_BG[:3], G.bg_alpha * a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*col, G.edge_alpha * a)
        ctx.set_line_width(G.edge_w)
        ctx.stroke()
        text(ctx, s, xx + G.text_dx, y + G.text_dy, G.size, G.font, col, a, 0)
        self._note("tag")

    def _pincer(self, ctx: cairo.Context, view: View, t: float, res: list) -> None:
        p = self.spec.pincer
        if p is None:
            return
        lt = t - p.t
        if lt <= 0:
            return
        P = CA.pincer
        x, y = view.to_screen(p.lon, ym(p.lat))
        fl = math.exp(-lt * P.flash_decay)
        g = cairo.RadialGradient(x, y, 0, x, y, P.flash_r)
        g.add_color_stop_rgba(0, *P.flash_rgb, P.flash_alpha * fl)
        g.add_color_stop_rgba(1, *C[self.spec.arrows.color if self.spec.arrows else P.ring_color], 0)
        ctx.set_source(g)
        ctx.arc(x, y, P.flash_r, 0, 2 * math.pi)
        ctx.fill()
        r0, dr = P.ring
        ring_a = window(t, p.t, p.t_end, P.ring_in, P.ring_out)
        for k in range(P.rings):
            f = ((lt * P.ring_rate) + k / P.rings) % 1
            ctx.arc(x, y, r0 + dr * ease_out(f), 0, 2 * math.pi)
            ctx.set_source_rgba(*C[P.ring_color], P.ring_alpha * (1 - f) * ring_a)
            ctx.set_line_width(P.ring_w)
            ctx.stroke()
        ta = window(t, p.tag_t, p.t_end, P.tag_in, P.tag_out)
        self._tag(ctx, p.text, x, y + P.tag_dy, C[P.tag_color], ta)
        hw, top, bot = P.box
        res.append((x - hw, y + top, x + hw, y + bot))
        self._note("pincer")

    def _places(self, ctx: cairo.Context, view: View, t: float, res: list) -> None:
        Pl, Sb, R = CA.place, CA.place_sub, CA.river_label
        a = smooth((t - self.spec.places_t) / Pl.in_sec)
        pw, ph = Pl.probe
        for p in self.spec.places:
            x, y = view.to_screen(p.lon, ym(p.lat))
            if not (0 < x < W_OUT and 0 < y < H_OUT):
                continue
            if any(b[0] < x + pw and b[2] > x and b[1] < y and b[3] > y - ph for b in res):
                continue
            ctx.arc(x, y, Pl.dot_r, 0, 2 * math.pi)
            ctx.set_source_rgba(*WHITE, a)
            ctx.fill()
            text(ctx, p.name, x + Pl.dx, y + Pl.dy, Pl.size, Pl.font, WHITE, Pl.alpha * a, Pl.halo)
            if p.now:
                text(ctx, p.now, x + Pl.dx, y + Sb.dy, Sb.size, Sb.font, C["muted"], Pl.alpha * a, Sb.halo)
        for r in self.spec.rivers_label:
            x, y = view.to_screen(r.lon, ym(r.lat))
            if 0 < x < W_OUT and 0 < y < H_OUT:
                text(ctx, r.name, x, y, R.size, R.font, tuple(CA.river.rgb), R.alpha * a, 0, "c", spacing=R.spacing)

    def _legend(self, ctx: cairo.Context, t: float) -> None:
        lg = self.spec.legend
        if lg is None:
            return
        a = window(t, lg.t0, lg.t1, F.note_in, F.note_out)
        if a <= F.min_alpha:
            return
        Lg, Lb, Cp = CA.legend, CA.legend_label, CA.legend_caption
        x, y = Lg.x, Lg.y
        bx, by, bw, bh = Lg.box
        rrect(ctx, x + bx, y + by, bw, bh, Lg.radius)
        ctx.set_source_rgba(*CARD_BG[:3], Lg.alpha * a)
        ctx.fill()
        for i, code in enumerate(lg.order):
            cx = x + Lg.sym_dx + (i % 2) * Lg.col_dx
            cy = y + (i // 2) * Lg.row_dy
            unit_symbol(ctx, cx, cy + Lg.sym_dy, C[self.spec.nations[code].color], "", "inf", a, Lg.symbol_scale)
            text(ctx, self.spec.nations[code].label, cx + Lg.label_dx, cy, Lb.size, Lb.font, WHITE, a, Lb.halo)
        text(ctx, lg.caption, x, y + Lg.caption_dy, Cp.size, Cp.font, C["muted"], a, Cp.halo)
        self._note("legend")

    def _source(self, ctx: cairo.Context, t: float) -> None:
        S = T.source
        for n in self.spec.notes.source_lines:
            a = window(t, n.t0, n.t1, F.note_in, F.note_out)
            text(ctx, n.text, S.x, S.y, S.size, S.font, C["muted"], CA.source_alpha * a, S.halo, role="source")

    def _end_t0(self) -> float:
        return self.spec.duration_sec - self.spec.notes.end_sec

    def _date(self, ctx: cairo.Context, t: float) -> None:
        B = DATE_BADGE
        cur = [d for d in self.spec.dates if t >= d.t][-1]
        k = smooth((t - cur.t - CA.date_delay) / B.slide_sec)
        a = F.date_alpha * k * (1 - smooth((t - (self._end_t0() - F.date_hide_lead_sec)) / F.date_hide_sec))
        w = text(ctx, cur.text, W_OUT - B.x_right, B.y - (1 - k) * B.slide_px, B.size, B.font, WHITE, a, F.date_halo, "r")
        ctx.set_source_rgba(*C["gold"], F.date_line_alpha * a)
        ctx.rectangle(W_OUT - B.x_right - w * k, B.underline_y, w * k, B.underline_w)
        ctx.fill()

    def _end(self, ctx: cairo.Context, t: float) -> None:
        a = smooth((t - self._end_t0()) / F.end_in_sec)
        if a <= F.min_alpha:
            return
        ctx.set_source_rgba(*F.end_bg, F.end_dim_alpha * a)
        ctx.paint()
        E, Tt, Ln, Nt = CA.end, T.end_title, T.end_line, T.end_note
        text(ctx, self.spec.notes.end_title, E.x, Tt.y, Tt.size, Tt.font, WHITE, a, Tt.halo)
        for i, s in enumerate(self.spec.sources):
            text(ctx, s.text, E.x, Ln.y0 + i * Ln.dy, E.line_size, Ln.font, C["muted"], a, Ln.halo, role="credit")
        text(ctx, self.spec.notes.end_note, E.x, E.note_y, Nt.size, Nt.font, C["muted"], Nt.alpha * a, Nt.halo, role="credit")
