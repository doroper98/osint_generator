"""층 4: 미사일 도해 카드 — 권리가 분명한 도해(SK-R1)를 밝은 안쪽 판에 얹고 이름·설명·크레딧. 원본: 4d9dc65 `sketch_d1.draw_missile_card`."""

from __future__ import annotations

from pathlib import Path

import cairo

from engine.style import C, CARD_BG
from engine.timebase import clamp01, ease_out, window
from engine.typography import rrect, text
from sketch.common.draw import SK, WHITE
from sketch.missile.shape import card_surface
from sketch.missile.spec import MissileSpec

K = SK.card


class CardLayer:
    def __init__(self, spec: MissileSpec, project: Path) -> None:
        self.card = spec.card
        self.surf: cairo.ImageSurface | None = None
        self.credit = ""
        if self.card is not None:
            m = next(m for m in spec.media if m.file == self.card.media)
            self.surf = card_surface(project / "media" / m.file, self.card.crop, self.card.rotate_deg)
            self.credit = f"{m.caption} · {m.credit} · {m.license}" if m.caption else f"{m.credit} · {m.license}"
        self.drawn: dict[str, int] = {}

    def draw(self, ctx: cairo.Context, t: float) -> None:
        c, s = self.card, self.surf
        if c is None or s is None:
            return
        a = window(t, c.t0, c.t1, K.fade_sec, K.fade_sec)
        if a <= K.min_alpha:
            return
        x, y, w, h = K.rect
        x += (1 - ease_out(clamp01((t - c.t0) / K.fade_sec))) * K.slide_px
        rrect(ctx, x, y, w, h, K.radius)
        ctx.set_source_rgba(*CARD_BG[:3], CARD_BG[3] * a)
        ctx.fill()
        p = K.inner_pad
        inner = (x + p, y + p, w - 2 * p, h - K.inner_bottom)
        rrect(ctx, *inner, K.inner_radius)
        ctx.set_source_rgba(*K.inner_bg[:3], K.inner_bg[3] * a)
        ctx.fill()
        m = K.img_pad
        sc = min((inner[2] - m) / s.get_width(), (inner[3] - m) / s.get_height())
        ctx.save()
        ctx.translate(inner[0] + inner[2] / 2 - s.get_width() * sc / 2, inner[1] + inner[3] / 2 - s.get_height() * sc / 2)
        ctx.scale(sc, sc)
        ctx.set_source_surface(s, 0, 0)
        ctx.paint_with_alpha(a)
        ctx.restore()
        self.drawn["card_image"] = self.drawn.get("card_image", 0) + 1
        for st, s_, col, role in ((K.title, c.title, WHITE, None), (K.sub, c.sub, C["gold"], None),
                                  (K.credit, self.credit, C["muted"], "credit")):
            text(ctx, s_, x + K.text_dx, y + h + st.dy, st.size, st.font, col, a, st.halo, role=role)
