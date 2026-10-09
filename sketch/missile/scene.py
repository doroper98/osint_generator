"""미사일 2D 장면 — 층 순서·초점(dim)·날짜·출처 줄·엔딩 자료 카드. 원본: 4d9dc65 `sketch_d1.render`.

층 순서(원본 그대로): 지형 → EEZ → 탐지 자산 → 발사 → 궤적 → EEZ 라벨 → 착탄 → 엔진 지명 라벨(새 라벨 예약 상자를 피함)
→ 새 라벨 → 도해 카드 → 고도 단면 → 출처 줄 → 날짜 → 엔딩 → 열림·닫힘 검정.
"""

from __future__ import annotations

from pathlib import Path

import cairo
import numpy as np

from engine.assets import Assets, load_labels
from engine.projection import View
from engine.stage import MercatorStage
from engine.style import C, DATE_BADGE, W_OUT, Output, output_profile
from engine.timebase import smooth, window
from engine.typography import text
from sketch.common.camera import CameraPath
from sketch.common.draw import SK, WHITE, Overlay
from sketch.missile.card import CardLayer
from sketch.missile.eez import EezLayer
from sketch.missile.launch import LaunchLayer
from sketch.missile.numbers import Numbers
from sketch.missile.profile import ProfileLayer
from sketch.missile.sensors import SensorLayer
from sketch.missile.spec import DimKey, MissileSpec

F, T = SK.fade, SK.text
LABELS_FILE = "labels.yaml"


def dim_at(keys: list[DimKey], t: float) -> float:
    return 1 + sum(k.d * smooth((t - k.t) / k.sec) for k in keys)


class MissileScene:
    def __init__(self, spec: MissileSpec, project: Path, res: str) -> None:
        self.spec = spec
        self.out: Output = output_profile(res)
        default = output_profile(None).name
        assets = Assets(project, load_labels(project / LABELS_FILE), None if self.out.name == default else self.out.name)
        self.stage = MercatorStage(assets, out=self.out)
        self.nums = Numbers(spec)
        self.eez = EezLayer(spec, project)
        self.sensors = SensorLayer(spec, self.nums)
        self.launch = LaunchLayer(spec, self.nums)
        self.card = CardLayer(spec, project)
        self.profile = ProfileLayer(spec, self.nums)
        cam = SK.camera
        self.camera = CameraPath(tuple(spec.shots), spec.duration_sec, cam.push_in[spec.kind], cam.hold_min_sec)
        self.overlap_boxes: list[tuple[float, list]] = []   # SK-C2 입력(시각, 예약 상자)

    def features_drawn(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for layer in (self.eez, self.sensors, self.launch, self.card, self.profile):
            for k, v in layer.drawn.items():
                out[k] = out.get(k, 0) + v
        return out

    def frame(self, t: float) -> bytes:
        sp, OP = self.spec, self.out
        view = View(self.stage, np.array(self.camera.at(t)))
        buf = bytearray(OP.width * OP.height * 4)
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, OP.width, OP.height, OP.width * 4)
        ctx = cairo.Context(surf)
        ctx.translate(OP.pad_x, 0)
        ctx.scale(OP.k, OP.k)
        self.stage.render_base(ctx, view)
        ov = Overlay(ctx)
        eez_dim = dim_at(sp.dim.eez, t)
        sens_dim = dim_at(sp.dim.sensors, t)
        self.eez.draw(ctx, view, t, eez_dim, self.launch.pulse(t))
        self.sensors.draw(ctx, view, t, sens_dim, ov)
        self.launch.draw_launch(ctx, view, t, 1, ov)
        self.launch.draw_track(ctx, view, t, 1)
        self.eez.labels(ctx, view, t, eez_dim if t < sp.dim.eez_labels_off else 0, ov)
        self.launch.draw_impact(ctx, view, t, 1, ov)
        self.overlap_boxes.append((t, list(ov.reserved)))
        self.stage.draw_labels(ctx, view, list(ov.reserved), 1)
        ov.flush()
        self.card.draw(ctx, t)
        self.profile.draw(ctx, t)
        self._source_lines(ctx, t)
        self._date(ctx, t)
        self._end(ctx, t)
        fa = 1 - min(smooth(t / F.open_sec), smooth((sp.duration_sec - t) / F.close_sec))
        if fa > F.black_min:
            ctx.set_source_rgba(0, 0, 0, fa)
            ctx.paint()
        surf.flush()
        return bytes(buf)

    def _source_lines(self, ctx: cairo.Context, t: float) -> None:
        S = T.source
        for n in self.spec.notes.source_lines:
            a = window(t, n.t0, n.t1, F.note_in, F.note_out)
            text(ctx, n.text, S.x, S.y, S.size, S.font, C["muted"], S.alpha * a, S.halo, role="source")

    def _end_t0(self) -> float:
        return self.spec.duration_sec - self.spec.notes.end_sec

    def _date(self, ctx: cairo.Context, t: float) -> None:
        B = DATE_BADGE
        k = smooth((t - F.date_in_t) / B.slide_sec)
        a = F.date_alpha * k * (1 - smooth((t - (self._end_t0() - F.date_hide_lead_sec)) / F.date_hide_sec))
        w = text(ctx, self.spec.date, W_OUT - B.x_right, B.y - (1 - k) * B.slide_px, B.size, B.font, WHITE, a, F.date_halo, "r")
        ctx.set_source_rgba(*C["gold"], F.date_line_alpha * a)
        ctx.rectangle(W_OUT - B.x_right - w * k, B.underline_y, w * k, B.underline_w)
        ctx.fill()

    def _end(self, ctx: cairo.Context, t: float) -> None:
        a = smooth((t - self._end_t0()) / F.end_in_sec)
        if a <= F.min_alpha:
            return
        ctx.set_source_rgba(*F.end_bg, F.end_dim_alpha * a)
        ctx.paint()
        Tt, Ln, Nt = T.end_title, T.end_line, T.end_note
        text(ctx, self.spec.notes.end_title, Tt.x, Tt.y, Tt.size, Tt.font, WHITE, a, Tt.halo)
        for i, s in enumerate(self.spec.sources):
            text(ctx, s.text, Ln.x, Ln.y0 + i * Ln.dy, Ln.size, Ln.font, C["muted"], a, Ln.halo, role="credit")
        text(ctx, self.spec.notes.end_note, Nt.x, Nt.y, Nt.size, Nt.font, C["muted"], Nt.alpha * a, Nt.halo, role="credit")
