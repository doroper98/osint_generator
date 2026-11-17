"""v7.4.0 C0.0 3b(UF-906·UF-907·UF-908) — 겹침 카드·게시물·사진/영상 액자·뱃지 이름표·아일랜드 마커(rules skin.cascade·post·media·badge·marker).

- 규칙: 엄격 모델(모르는 키·잘못된 그림자 이름·credit_dy ≤ caption_dy = 오류).
- skin: 카드·액자·이름표 상자 안 평균 밝기 ≥ 0.85(어두운 판 없음), 카드 모서리 직각, 글자 = 잉크(짙고 테두리 없음), 핀 = 강조 점 + 흰 고리.
- 상자 함수: media_box 가 흰 여백(mat)·캡션 칸까지 보고(그린 흰 면 ⊆ 상자), badge_box ⊇ 흰 알약 이름표, post_geom 상자 = 그린 카드.
- 비 skin: skin 경로를 부르지 않는다(바이트 동일은 감독 identity 스크립트가 HEAD 와 대조).
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest import mock

import cairo
import numpy as np
from pydantic import ValidationError

from engine import cascade as cascade_mod
from engine import skin
from engine.layers import badges as badges_mod
from engine.layers import markers as markers_mod
from engine.layers import media as media_mod
from engine.layers import post as post_mod
from engine.style import CASCADE, H_OUT, SKIN, W_OUT, apply_palette, hexc
from rules import load_rules
from schemas.rules_models import SkinBadge, SkinCascade, SkinMarker, SkinMedia, SkinPost
from schemas.source_models import SourcesFile
from tests.anti_inertia._ast_util import REPO

BG = 0.92
FIX = REPO / "tests" / "fixtures" / "intake" / "post_sources.json"
CASCADE_EV = dict(type="cascade", t0=0.0, t1=30.0, items=[
    dict(at=0.5, flag="kr", date="09. 18", title="파병 불가 발표", line="기자회견 · 대통령실", accent="gold"),
    dict(at=3.0, flag="us", date="09. 19", title="미국, 동맹 협력 요청", line="국무부 논평", accent="us")])
POST_EV = dict(type="post", t0=0.0, t1=10.0, src="src_x_0001", hl="해군 호위", quote=True)
BADGE_EV = dict(type="badge", t0=0.0, t1=10.0, kind="flag", flag="kr", R=30.0, label="대한민국", role="정부", accent="gold")
MARKER_EV = dict(type="marker", t0=0.0, t1=10.0, label="2025년 3분기", sub="영업이익 6억 8300만 달러", side="right", hl=True, world=(0.0, 0.0))


def _on() -> None:
    skin.apply("studio")
    apply_palette(SKIN.palette)


def _off() -> None:
    skin.apply(None)
    apply_palette(None)


def _canvas() -> tuple[cairo.ImageSurface, cairo.Context]:
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT)
    c = cairo.Context(s)
    c.set_source_rgb(BG, BG, BG)
    c.paint()
    return s, c


def _rgb(s: cairo.ImageSurface) -> np.ndarray:
    s.flush()
    return np.ndarray((H_OUT, s.get_stride() // 4, 4), np.uint8, buffer=s.get_data())[:, :W_OUT, 2::-1].astype(np.float64) / 255.0


def _lum(s: cairo.ImageSurface) -> np.ndarray:
    return _rgb(s) @ np.array([0.2126, 0.7152, 0.0722])


def _flag_surface(w: float, k: float) -> cairo.ImageSurface:
    n = max(2, int(w * k))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, n, n)
    c = cairo.Context(s)
    c.set_source_rgb(0.8, 0.2, 0.25)
    c.paint()
    return s


def _R(**cache: object) -> SimpleNamespace:  # noqa: N802
    def raster(key: str, w: float, k: float) -> tuple[cairo.ImageSurface, float, float]:
        s = _flag_surface(w, k)
        return s, s.get_width() / k, s.get_height() / k

    assets = SimpleNamespace(raster=raster, emblem_flag=lambda eid: None)
    return SimpleNamespace(cache=dict(cache), out=SimpleNamespace(k=1.0), reserved=[], zones=[], assets=assets)


def _box_mean(lum: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> float:
    return float(lum[int(y0):int(y1), int(x0):int(x1)].mean())


class RulesTest(unittest.TestCase):
    def test_strict_models(self) -> None:
        raw = load_rules().skin.model_dump()
        for key, model in (("cascade", SkinCascade), ("post", SkinPost), ("media", SkinMedia), ("badge", SkinBadge), ("marker", SkinMarker)):
            model.model_validate(raw[key])
            with self.assertRaises(ValidationError, msg=key):
                model.model_validate({**raw[key], "unknown_key": 1})
        with self.assertRaises(ValidationError):
            SkinCascade.model_validate({**raw["cascade"], "level_front": "heavy"})
        with self.assertRaises(ValidationError):
            SkinMedia.model_validate({**raw["media"], "credit_dy": raw["media"]["caption_dy"]})


class CascadeTest(unittest.TestCase):
    def setUp(self) -> None:
        _on()

    def tearDown(self) -> None:
        _off()

    def _draw(self, t: float) -> tuple[cairo.ImageSurface, list]:
        s, c = _canvas()
        R = _R(badge_placeholder=lambda *a: None)  # noqa: N806 — 국기 원은 뱃지 테스트가 본다
        cascade_mod.draw_cascade(c, R, t, CASCADE_EV)
        return s, cascade_mod.layout(t, CASCADE_EV)

    def test_white_square_cards_ink_text(self) -> None:
        s, cards = self._draw(6.0)
        lum, rgb = _lum(s), _rgb(s)
        front = cards[-1]
        x, y, w, h = front.box
        self.assertGreaterEqual(_box_mean(lum, x, y, x + w, y + h), 0.85)
        self.assertGreater(lum[int(y + h) - 2, int(x + w) - 2], 0.95, "직각 모서리 — 오른쪽 아래 모서리 화소까지 흰 면")
        F = CASCADE.front  # noqa: N806
        tl = lum[int(y + F.title_dy - F.title_size):int(y + F.title_dy + 2), int(x + F.pad_x):int(x + w - F.pad_x)]
        self.assertLess(tl.min(), 0.2, "제목 = 짙은 잉크")
        top = rgb[int(y), int(x + w / 2)]
        self.assertGreater(top[0] - top[2], 0.3, "앞 카드 윗변 = 강조 선")
        back = cards[0]
        bx, by = back.x, back.y
        self.assertGreaterEqual(_box_mean(lum, bx, by, bx + CASCADE.dx - 2, by + back.h), 0.85, "뒤 카드 보이는 띠도 밝다")

    def test_boxes_unchanged(self) -> None:
        """skin 은 모양만 — 보이는 영역(검사·회피 상자)은 같은 기하."""
        on = cascade_mod.cascade_boxes(6.0, CASCADE_EV)
        _off()
        self.assertEqual(on, cascade_mod.cascade_boxes(6.0, CASCADE_EV))


class PostTest(unittest.TestCase):
    def setUp(self) -> None:
        _on()
        self.src = SourcesFile.model_validate(json.loads(FIX.read_text(encoding="utf-8"))).by_id()

    def tearDown(self) -> None:
        _off()

    def test_white_card_soft_highlight(self) -> None:
        s, c = _canvas()
        post_mod.draw_post(c, _R(sources=self.src), 5.0, POST_EV)
        x, y, w, h, _ = post_mod.post_geom(c, POST_EV, self.src)
        lum, rgb = _lum(s), _rgb(s)
        self.assertGreaterEqual(_box_mean(lum, x, y, x + w, y + h), 0.85)
        self.assertGreater(lum[int(y + h) - 2, int(x + w) - 2], 0.95, "직각 모서리")
        self.assertLess(lum[int(y):int(y + h), int(x):int(x + w)].min(), 0.2, "글자 = 짙은 잉크")
        soft = np.array(hexc(SKIN.accent.soft))
        hit = (np.abs(rgb[int(y):int(y + h), int(x):int(x + w)] - soft).max(axis=2) < 0.02).sum()
        self.assertGreater(hit, 50, "형광펜 = 옅은 강조 띠(accent.soft)")


class MediaTest(unittest.TestCase):
    def tearDown(self) -> None:
        _off()

    def test_box_reports_mat_and_caption(self) -> None:
        from engine.media_plan import media_box  # noqa: PLC0415
        from engine.media_registry import credit_line, load_media_registry  # noqa: PLC0415

        reg = load_media_registry()
        e = dict(type="photo", mid="rok_iraq", x=292.0, y=138.0, w=280.0)
        off = media_box(e, reg)
        _on()
        on = media_box(e, reg)
        m = SKIN.media.mat
        self.assertEqual((on[0], on[1], on[2]), (off[0] - m, off[1] - m, off[2] + m))
        cap = media_mod.caption_bar_h(reg["rok_iraq"].caption, credit_line(reg["rok_iraq"]), e["w"])
        self.assertEqual(cap, SKIN.media.credit_dy + SKIN.media.bottom)
        # 그린 흰 면(액자 + 캡션 칸)이 media_box 안이다 — 사진 높이 = media_box 의 사진 비율
        ph = on[3] - cap - e["y"]
        s, c = _canvas()
        media_mod.skin_frame(c, e["x"], e["y"], e["w"], ph, cap, 1.0)
        media_mod.skin_caption(c, e["x"], e["y"] + ph, e["w"], reg["rok_iraq"].caption, credit_line(reg["rok_iraq"]), 1.0)
        lum = _lum(s)
        ys, xs = np.where(lum > 0.97)
        self.assertGreaterEqual(xs.min(), int(on[0]) - 1)
        self.assertLessEqual(xs.max(), int(on[2]) + 1)
        self.assertGreaterEqual(ys.min(), int(on[1]) - 1)
        self.assertLessEqual(ys.max(), int(on[3]) + 1)
        self.assertGreaterEqual(_box_mean(lum, on[0], e["y"] + ph, on[2], on[3]), 0.85, "캡션 칸 = 흰 여백(어두운 바 없음)")
        self.assertLess(lum[int(e["y"] + ph):int(on[3]), int(on[0]):int(on[2])].min(), 0.25, "캡션 = 잉크")

    def test_tag_is_white_pill(self) -> None:
        _on()
        s, c = _canvas()
        media_mod.skin_tag(c, 100.0, 100.0, "PHOTO", 1.0)
        T = SKIN.media.tag  # noqa: N806
        lum = _lum(s)
        y0, x0 = 100 + T.inset, 100 + T.inset
        self.assertGreaterEqual(_box_mean(lum, x0 + T.h / 2, y0, x0 + T.h, y0 + T.h), 0.85)


class BadgeTest(unittest.TestCase):
    def setUp(self) -> None:
        _on()

    def tearDown(self) -> None:
        _off()

    def test_white_plate_inside_box(self) -> None:
        s, c = _canvas()
        R = _R()  # noqa: N806
        x, y = 400.0, 200.0
        badges_mod.badge_at(c, R, x, y, BADGE_EV, 5.0, 1.0)
        lum = _lum(s)
        px0, py0, px1, py1 = badges_mod.plate_rect(c, BADGE_EV, x, y, BADGE_EV["R"], 1.0)
        bx0, by0, bx1, by1 = badges_mod.badge_box(c, BADGE_EV, x, y, 5.0)
        self.assertTrue(bx0 <= px0 and by0 <= py0 and bx1 >= px1 and by1 >= py1, "badge_box ⊇ 흰 알약 이름표")
        mid = (py0 + py1) / 2
        self.assertGreaterEqual(_box_mean(lum, px0 + (py1 - py0) / 2, py0 + 1, px1 - (py1 - py0) / 2, py1 - 1), 0.75)
        self.assertGreater(lum[int(mid), int(px0 + 1)], BG - 0.05, "알약 = 둥근 끝(왼쪽 끝 화소는 바탕)")
        self.assertLess(lum[int(py0):int(py1), int(px0):int(px1)].min(), 0.2, "이름 = 짙은 잉크")
        ring = lum[int(y - BADGE_EV["R"]) - 1:int(y - BADGE_EV["R"]) + 2, int(x) - 1:int(x) + 2]
        self.assertGreater(ring.max(), 0.9, "고리 = 흰 고리(어두운 바깥 고리 없음)")


class MarkerTest(unittest.TestCase):
    def setUp(self) -> None:
        _on()

    def tearDown(self) -> None:
        _off()

    def test_pin_and_ink_label(self) -> None:
        s, c = _canvas()
        markers_mod.skin_pin(c, 300.0, 200.0, 2.0, 1.0, True, "dot")
        markers_mod.skin_text(c, [("2025년 3분기", 312.0, 204.0, 13.0, "sansb", skin.INK)], "l", 1.0)
        rgb, lum = _rgb(s), _lum(s)
        self.assertTrue(np.allclose(rgb[200, 300], skin.ACCENT_SHAPE, atol=0.02), "핀 점 = 강조색")
        r = SKIN.marker.dot_r + SKIN.marker.ring_w / 2
        self.assertGreater(lum[200, int(300 + r)], 0.97, "점 둘레 흰 고리")
        lab = lum[190:208, 312:400]
        self.assertLess(lab.min(), 0.2, "라벨 = 짙은 잉크")
        self.assertGreater(lum[185, 312:400].min(), BG, "글자 둘레 = 흰 번짐(어두운 테두리 없음)")

    def test_map_marker_not_skinned(self) -> None:
        view = SimpleNamespace(stage=SimpleNamespace(name="mercator"))
        self.assertFalse(markers_mod.skin_marker(view, dict(MARKER_EV)))
        self.assertTrue(markers_mod.skin_marker(view, dict(MARKER_EV, in_island=True)))
        self.assertTrue(markers_mod.skin_marker(SimpleNamespace(stage=SimpleNamespace(name="studio")), dict(MARKER_EV)))


class OffSkinTest(unittest.TestCase):
    """비 skin — skin 경로를 부르지 않는다."""

    def test_no_skin_calls(self) -> None:
        _off()
        src = SourcesFile.model_validate(json.loads(FIX.read_text(encoding="utf-8"))).by_id()
        with mock.patch.object(cascade_mod, "skin_frame") as cf, mock.patch.object(post_mod, "draw_post_skin") as pf, \
                mock.patch.object(badges_mod, "skin_ring") as br, mock.patch.object(badges_mod, "skin_label") as bl:
            s, c = _canvas()
            cascade_mod.draw_cascade(c, _R(badge_placeholder=lambda *a: None), 6.0, CASCADE_EV)
            post_mod.draw_post(c, _R(sources=src), 5.0, POST_EV)
            badges_mod.badge_at(c, _R(), 400.0, 200.0, BADGE_EV, 5.0, 1.0)
        for m in (cf, pf, br, bl):
            m.assert_not_called()
        self.assertEqual(media_mod.mat_pad(), 0.0)
        self.assertFalse(markers_mod.skin_marker(SimpleNamespace(stage=SimpleNamespace(name="studio")), dict(MARKER_EV)))


if __name__ == "__main__":
    unittest.main()
