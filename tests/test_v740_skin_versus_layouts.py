"""v7.4.0 UF-912·UF-913("세가지 다 적용해") — versus 패널 skin 배치 셋(axis·sheets·piles).

- 규칙: rules skin.panel.versus 엄격 모델(모르는 키·차례 어김·모르는 기본 배치 = 오류).
- 스키마: PanelVersus.layout 선택, 없으면 dict 에 없다(옛 모양). 모델 Literal = 규칙 배치 셋. 옛 테마 영상 + layout = 오류(조용한 무시 없음, P6).
- 배치마다(실제 패널 렌더러, 스튜디오 skin): 판 흰 카드 없음(axis 는 면 자체 없음 — 두 기둥 사이 화소 = 바탕), 두 옆 제목 같은 크기(G4),
  항목이 t 순서로 나타나고 강조 항목은 지금 항목 하나, 넘침 = VersusOverflowError(자름 없음), sheets·piles 면은 직각·밝다.
- layout 없음 = axis.
"""

from __future__ import annotations

import copy
import unittest
from types import SimpleNamespace
from typing import get_args
from unittest import mock

import cairo
import numpy as np
import yaml
from pydantic import ValidationError

from engine import registry, skin
from engine.events import PanelVersus
from engine.panels import versus as versus_mod
from engine.panels import versus_layouts as vl
from engine.project import ProjectError, check_versus_layout
from engine.style import H_OUT, ISLAND, SKIN, W_OUT, apply_palette
from rules import load_rules
from schemas.rules_models import SkinPanelVersus, VersusLayout
from tests.anti_inertia._ast_util import REPO

PREVIEW = REPO / "tests" / "fixtures" / "preview"
LAYOUTS = ("axis", "sheets", "piles")
BG = 0.92
LUM = np.array([0.2126, 0.7152, 0.0722])


def _on() -> None:
    skin.apply("studio")
    apply_palette(SKIN.palette)


def _off() -> None:
    skin.apply(None)
    apply_palette(None)


def _event(name: str = "panel_versus") -> dict:
    doc = yaml.safe_load((PREVIEW / f"{name}.yaml").read_text(encoding="utf-8"))
    return registry.validate_events([doc["event"]])[0]


def _render(e: dict, t: float) -> np.ndarray:
    """실제 패널 렌더러(스튜디오 이름의 R, 설계 px 1배) → RGB 0~1 배열(H×W×3)."""
    R = SimpleNamespace(stage=SimpleNamespace(name="studio"), cache={})  # noqa: N806
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT)
    c = cairo.Context(s)
    c.set_source_rgb(BG, BG, BG)
    c.paint()
    registry.FULL_LAYERS.resolve(e).render(c, R, t, e)
    s.flush()
    return np.ndarray((H_OUT, s.get_stride() // 4, 4), np.uint8, buffer=s.get_data())[:, :W_OUT, 2::-1].astype(np.float64) / 255.0


def _accent_mask(rgb: np.ndarray) -> np.ndarray:
    return (rgb[..., 0] > 0.75) & (rgb[..., 1] < 0.55) & (rgb[..., 2] < 0.4)


def _items_by_t(e: dict) -> list[tuple[int, dict]]:
    return sorted(((si, it) for si, sd in enumerate(e["sides"]) for it in sd["items"]), key=lambda r: r[1]["t"])


class RulesTest(unittest.TestCase):
    def test_strict(self) -> None:
        raw = load_rules().skin.panel.versus.model_dump()
        SkinPanelVersus.model_validate(raw)
        bad = [{**raw, "nope": 1}, {**raw, "default": "cards"},
               {**raw, "axis": {**raw["axis"], "head": {**raw["axis"]["head"], "min_size": 99}}},
               {**raw, "sheets": {**raw["sheets"], "head": {**raw["sheets"]["head"], "rule_dy": 1}}},
               {**raw, "piles": {**raw["piles"], "card": {**raw["piles"]["card"], "min_pitch": 999}}},
               {**raw, "piles": {**raw["piles"], "src": {**raw["piles"]["src"], "nope": 1}}}]
        for b in bad:
            with self.assertRaises(ValidationError):
                SkinPanelVersus.model_validate(b)

    def test_layout_sets_match(self) -> None:
        self.assertEqual(set(get_args(PanelVersus.model_fields["layout"].annotation.__args__[0])), set(get_args(VersusLayout)))
        self.assertEqual(set(vl._DRAW), set(LAYOUTS))
        self.assertEqual(set(get_args(VersusLayout)), set(LAYOUTS))


class MinFontTest(unittest.TestCase):
    """v7.4.0 D935 — 두 입장 패널 출처 줄·패널 추정 태그는 역할 없이 그리는 글자라 최소 글자(layout_480p.min_font_px) 이상이어야 한다.
    8.5 였을 때 nvidia-chips-china-2026 프리뷰가 [glyph-size] hard 로 떨어졌다(예외 역할은 end_card·media_meta 뿐)."""

    def test_versus_src_and_panel_tag_at_least_min_font(self) -> None:
        r = load_rules()
        lo = r.layout_480p.min_font_px
        for name in LAYOUTS:
            lay = getattr(r.skin.panel.versus, name)
            self.assertGreaterEqual(lay.src.size, lo, name)
            if getattr(lay, "index", None) is not None:   # sheets·piles 의 01·02 번호(8px 였다 — 프리뷰 표본 시각에 따라 뒤늦게 걸렸다)
                self.assertGreaterEqual(lay.index.size, lo, f"{name}.index")
        self.assertGreaterEqual(r.skin.panel.tag.size, lo)


class SchemaTest(unittest.TestCase):
    def test_layout_optional_absent_not_in_dict(self) -> None:
        self.assertNotIn("layout", _event())
        for lay in LAYOUTS:
            with self.subTest(layout=lay):
                self.assertEqual(_event(f"panel_versus_{lay}")["layout"], lay)
        raw = yaml.safe_load((PREVIEW / "panel_versus.yaml").read_text(encoding="utf-8"))["event"]
        with self.assertRaises((ValidationError, ValueError)):
            registry.validate_events([{**raw, "layout": "cards"}])

    def test_fixtures_same_content_plus_layout(self) -> None:
        base = _event()
        for lay in LAYOUTS:
            e = _event(f"panel_versus_{lay}")
            self.assertEqual({k: v for k, v in e.items() if k != "layout"}, base)

    def test_non_skin_layout_is_error(self) -> None:
        _off()
        check_versus_layout([_event()], "test")   # layout 없음 = 통과
        with self.assertRaises(ProjectError):
            check_versus_layout([_event("panel_versus_sheets")], "test")
        e = _event("panel_versus_piles")
        with self.assertRaises(ValueError):
            _render(e, e["t1"] - 1.2)
        _render(_event(), e["t1"] - 1.2)   # 옛 두 기둥 상자 = 그대로

    def test_backing_is_map_veil_of_layout(self) -> None:
        """판 카드 없는 배치의 지도 위 장막 = 배치 자기 값(rules skin.panel.versus.<layout>.map_veil). 글씨가 지도 위에 직접 뜨므로
        판 카드 패널 장막(panel_veil_alpha)·인용 장막보다 짙다 — 감독 실물 판정(국기 채움·지명과 겹쳐 읽히지 않음)."""
        V = SKIN.panel.versus  # noqa: N806
        self.assertEqual(versus_mod.skin_backing(_event()), V.axis.map_veil)
        for lay in LAYOUTS:
            veil = versus_mod.skin_backing(_event(f"panel_versus_{lay}"))
            self.assertEqual(veil, getattr(V, lay).map_veil)
            self.assertGreater(veil, SKIN.map_overlays.quote_veil_alpha)
            self.assertGreater(veil, SKIN.map_overlays.panel_veil_alpha)
        self.assertGreaterEqual(V.axis.map_veil, V.sheets.map_veil)   # 면 없는 글씨만 배치가 가장 짙다

    def test_old_backdrop_stage_keeps_island_frame(self) -> None:
        """판 카드 생략은 skin 무대에서만 — 옛 backdrop 무대(비 skin)의 versus 는 종전대로 아일랜드 상자를 그린다
        (감독 검토 중 동일성 검사가 잡은 회귀: 배치 함수가 있다는 이유만으로 옛 무대 상자가 사라졌다)."""
        _off()
        e = _event()
        R = SimpleNamespace(stage=SimpleNamespace(name="backdrop"), cache={})  # noqa: N806
        c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT))
        with mock.patch("engine.island.draw_frame") as frame:
            registry.FULL_LAYERS.resolve(e).render(c, R, e["t1"] - 1.2, e)
        self.assertEqual(frame.call_count, 1)
        _on()
        try:
            R2 = SimpleNamespace(stage=SimpleNamespace(name="studio"), cache={})  # noqa: N806
            with mock.patch("engine.island.draw_frame") as frame2:
                registry.FULL_LAYERS.resolve(e).render(c, R2, e["t1"] - 1.2, e)
            self.assertEqual(frame2.call_count, 0)
        finally:
            _off()

    def test_map_veil_painted_without_card(self) -> None:
        """skin 지도 무대: 배치마다 자기 장막 알파로 화면 전체를 고르게 덮고 판 흰 카드는 그리지 않는다(구석 화소 = 바탕 × (1 − 장막) + 흰색 × 장막)."""
        _on()
        try:
            for lay in LAYOUTS:
                e = _event(f"panel_versus_{lay}")
                R = SimpleNamespace(stage=SimpleNamespace(name="mercator", theme_name=SKIN.map_themes[0]), cache={})  # noqa: N806
                s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT)
                c = cairo.Context(s)
                c.set_source_rgb(0.2, 0.2, 0.2)
                c.paint()
                with mock.patch("engine.stage.skin_map", return_value=True):
                    registry.FULL_LAYERS.resolve(e).render(c, R, e["t1"] - 1.2, e)
                s.flush()
                px = np.ndarray((H_OUT, s.get_stride() // 4, 4), np.uint8, buffer=s.get_data())[H_OUT - 3, 3, 2::-1].astype(np.float64) / 255.0
                veil = getattr(SKIN.panel.versus, lay).map_veil
                want = 0.2 * (1 - veil) + np.array(skin.FILL) * veil
                with self.subTest(layout=lay):
                    self.assertTrue(np.allclose(px, want, atol=0.02), (px, want))
        finally:
            _off()


class LayoutRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _on()
        cls.ev = {lay: _event(f"panel_versus_{lay}") for lay in LAYOUTS}

    @classmethod
    def tearDownClass(cls) -> None:
        _off()

    def test_default_is_axis(self) -> None:
        e0, e1 = _event(), self.ev["axis"]
        t = e0["t1"] - 1.2
        self.assertTrue(np.array_equal(_render(e0, t), _render(e1, t)))

    def test_no_panel_card_frame(self) -> None:
        """판 흰 카드(island.panel_box) 없음 — 상자 안 빈 자리 = 무대 바탕 그대로. axis 는 두 기둥 사이(오른쪽 첫 줄 빈 자리)."""
        x0, _, _, _ = ISLAND.panel_box
        probes = {"axis": (W_OUT / 2 + 230, SKIN.panel.versus.axis.row.y0 + 10),
                  "sheets": (x0 + 12, 300), "piles": (x0 + 30, 300)}
        for lay, (px, py) in probes.items():
            e = self.ev[lay]
            with self.subTest(layout=lay):
                lum = _render(e, e["t1"] - 1.2) @ LUM
                self.assertAlmostEqual(float(lum[int(py), int(px)]), BG, delta=0.01)

    def test_side_titles_equal_size(self) -> None:
        for lay in LAYOUTS:
            e = self.ev[lay]
            titles = {sd["title"] for sd in e["sides"]}
            with self.subTest(layout=lay), mock.patch.object(vl, "text", wraps=vl.text) as tx:
                _render(e, e["t1"] - 1.2)
                sizes = {c.args[1]: c.args[4] for c in tx.call_args_list if c.args[1] in titles}
                self.assertEqual(set(sizes), titles)
                self.assertEqual(len(set(sizes.values())), 1)

    def test_items_in_t_order(self) -> None:
        """세 번째 항목(t 순서)이 다 들어온 순간 — 앞 셋만 그려지고 나머지는 아직 없다."""
        for lay in LAYOUTS:
            e = self.ev[lay]
            order = _items_by_t(e)
            t = order[2][1]["t"] + 1.0
            with self.subTest(layout=lay), mock.patch.object(vl, "text", wraps=vl.text) as tx:
                _render(e, t)
                drawn = {c.args[1] for c in tx.call_args_list if c.args[7] > 0.01}
                for k, (_, it) in enumerate(order):
                    first_line = it["text"].split(" ")[0]
                    hit = any(s.startswith(first_line) for s in drawn)
                    self.assertEqual(hit, k <= 2, it["text"])

    def test_only_current_item_accent(self) -> None:
        """강조색 화소 = 지금 항목(t ≤ 지금 중 가장 늦은 것) 한 자리뿐 — 그쪽 반쪽, 한 항목 높이 안."""
        for lay in LAYOUTS:
            e = self.ev[lay]
            order = _items_by_t(e)
            for k in (0, 2, len(order) - 1):
                si, it = order[k]
                t = (order[k + 1][1]["t"] - 0.05) if k + 1 < len(order) else e["t1"] - 1.2
                with self.subTest(layout=lay, item=it["text"]):
                    m = _accent_mask(_render(e, t))
                    ys, xs = np.where(m)
                    self.assertGreater(len(ys), 0)
                    self.assertLess(int(ys.max() - ys.min()), 64)
                    if si == 0:
                        self.assertLess(int(xs.max()), W_OUT / 2 + 4)
                    else:
                        self.assertGreater(int(xs.min()), W_OUT / 2 - 4)

    def test_surfaces_square_and_light(self) -> None:
        """sheets·piles 면 — 직각 모서리(기울기를 빼고 그리면 모서리 화소가 흰 면), 면 안 평균 밝기 ≥ 0.85."""
        S, P = SKIN.panel.versus.sheets, SKIN.panel.versus.piles  # noqa: N806
        boxes = {"sheets": [(S.left.x, S.left.y, S.sheet.w, S.sheet.h), (S.right.x, S.right.y, S.sheet.w, S.sheet.h)],
                 "piles": [(P.head.x_left, P.card.y0, P.card.w, P.card.h), (P.head.x_right - P.card.w, P.card.y0, P.card.w, P.card.h)]}
        for lay, bxs in boxes.items():
            e = self.ev[lay]
            with self.subTest(layout=lay), mock.patch.object(vl, "_rotate", lambda *a, **k: None):
                lum = _render(e, e["t1"] - 1.2) @ LUM
                for x, y, w, h in bxs:
                    self.assertGreater(float(lum[int(y) + 1, int(x) + 1]), 0.97)            # 왼쪽 위 모서리
                    self.assertGreater(float(lum[int(y) + 1, int(x + w) - 2]), 0.97)        # 오른쪽 위 모서리
                    self.assertGreaterEqual(float(lum[int(y):int(y + h), int(x):int(x + w)].mean()), 0.85)


class OverflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _on()

    @classmethod
    def tearDownClass(cls) -> None:
        _off()

    def _raises(self, e: dict) -> None:
        with self.assertRaises(versus_mod.VersusOverflowError):
            _render(e, e["t1"] - 1.2)

    def test_too_many_items(self) -> None:
        for lay in LAYOUTS:
            e = copy.deepcopy(_event(f"panel_versus_{lay}"))
            extra = [{"text": f"추가 논거 {i} 번째 항목", "t": e["t1"] - 3} for i in range(8)]
            e["sides"][1]["items"] = e["sides"][1]["items"] + extra
            with self.subTest(layout=lay):
                self._raises(e)

    def test_too_long_title_or_item(self) -> None:
        for lay in LAYOUTS:
            for what in ("title", "item"):
                e = copy.deepcopy(_event(f"panel_versus_{lay}"))
                if what == "title":
                    e["sides"][0]["title"] = "아주 길고 긴 옆 제목이 반쪽을 넘어간다 " * 3
                else:
                    e["sides"][0]["items"][0]["text"] = "아주 긴 항목 문구가 계속 이어진다 " * 6
                with self.subTest(layout=lay, what=what):
                    self._raises(e)

    def test_overflow_reported_before_render(self) -> None:
        """넘침은 렌더 전에 잡힌다 — versus_layouts.overflow(검사 check_panel_overflow 가 부른다)가 렌더와 같은 함수로 문구를 돌려준다. 맞는 예제 = 빈 목록."""
        for lay in LAYOUTS:
            e = _event(f"panel_versus_{lay}")
            with self.subTest(layout=lay):
                self.assertEqual(vl.overflow(e, lay), [])
                bad = copy.deepcopy(e)
                bad["sides"][0]["items"][0]["text"] = "아주 긴 항목 문구가 계속 이어진다 " * 6
                out = vl.overflow(bad, lay)
                self.assertEqual(len(out), 1)
                self.assertIn("[panel-overflow]", out[0])

    def test_check_panel_overflow_covers_versus(self) -> None:
        from engine.checks import check_panel_overflow  # noqa: PLC0415

        bad = copy.deepcopy(_event("panel_versus_piles"))
        bad["sides"][1]["items"] = bad["sides"][1]["items"] + [{"text": f"추가 논거 {i}", "t": bad["t1"] - 3} for i in range(6)]
        P = SimpleNamespace(events=[_event("panel_versus_axis"), bad], root=REPO / "__no_such_project__")  # noqa: N806
        out = check_panel_overflow(P)
        self.assertEqual(len(out), 1)
        self.assertIn("piles", out[0])


class RepeatCheckTest(unittest.TestCase):
    """UF-913 — 세 모양을 다 쓴다: 이웃한 versus 가 같은 layout 이면 hard(기본값만 반복해 한 모양으로 굳지 않게)."""

    def _events(self, *layouts: str | None) -> list[dict]:
        out = []
        for i, lay in enumerate(layouts):
            e = copy.deepcopy(_event())
            shift = i * 100.0
            e["t0"] += shift
            e["t1"] += shift
            if lay is not None:
                e["layout"] = lay
            out.append(e)
        return out

    def test_neighbours_same_layout_fail(self) -> None:
        from engine import checks  # noqa: PLC0415

        self.assertIn("versus_layout_repeat", checks.HARD)
        _on()
        try:
            run = lambda *ls: checks.check_versus_layout_repeat(SimpleNamespace(events=self._events(*ls)))  # noqa: E731
            self.assertEqual(run("axis"), [])
            self.assertEqual(run("axis", "sheets", "piles"), [])
            self.assertEqual(run("axis", "sheets", "axis"), [])          # 이웃만 본다
            self.assertEqual(len(run("sheets", "sheets")), 1)
            out = run(None, None)                                          # 둘 다 기본값(axis) = 반복
            self.assertEqual(len(out), 1)
            self.assertIn("[versus-layout-repeat]", out[0])
            self.assertEqual(len(run(None, "axis")), 1)                    # 기본값 = axis
            self.assertEqual(len(run("piles", "piles", "piles")), 2)
        finally:
            _off()
        self.assertEqual(checks.check_versus_layout_repeat(SimpleNamespace(events=self._events(None, None))), [])   # 옛 테마 영상은 보지 않는다


class WrapTest(unittest.TestCase):
    """두 줄로 접힌 항목 — 끝 낱말 하나만 둘째 줄에 남지 않는다(감독 실물 판정: "… 이 해협 / 경유")."""

    def test_no_orphan_tail(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 8, 8))
        P = SKIN.panel.versus.piles  # noqa: N806
        room = P.card.w - P.item.dx - P.item.pad_r
        s = "원유 61% · 나프타 54%가 이 해협 경유"
        from engine.typography import tw, wrap  # noqa: PLC0415

        greedy = wrap(ctx, s, room, P.item.size, P.item.font)
        self.assertEqual(len(greedy), 2)
        lines = vl._balanced(ctx, s, room, P.item.size, P.item.font)
        self.assertEqual(" ".join(lines), s)   # 낱말을 버리거나 바꾸지 않는다
        self.assertEqual(len(lines), 2)
        w0, w1 = (tw(ctx, ln, P.item.size, P.item.font) for ln in lines)
        self.assertGreaterEqual(w1, w0 * SKIN.panel.versus.tail_min)
        self.assertLessEqual(max(w0, w1), room)
        self.assertEqual(vl._balanced(ctx, "짧은 문구", room, P.item.size, P.item.font), ["짧은 문구"])   # 한 줄은 그대로


if __name__ == "__main__":
    unittest.main()
