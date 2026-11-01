"""전쟁사 픽토그램·부호 세트·휘장 재작도 — 본편 marker·badge 경로 등록(v7.4.0 back_and_forth D-0608 §1-3, 15 P10).

세 곳 동시: 스키마(engine.events MarkerEvent.glyph · BadgeEvent.emblem) = 렌더러(engine.glyphs.arms.GLYPHS · engine.glyphs.emblems.EMBLEMS,
engine.layers.markers·badges) = 프리뷰 예제(tests/fixtures/preview/war/). 규칙 부호 세트(war_history.symbol_sets.*.glyphs)에 있는데
렌더러가 없거나, 렌더러에만 있는 픽토그램 = 실패. 휘장 재작도 레코드(assets/emblems/registry.json reconstructions)의 glyph 도 같다.
"""

from __future__ import annotations

import unittest
from unittest import mock

import cairo
import yaml
from pydantic import ValidationError

from engine.entities import load_emblem_registry
from engine.events import BadgeEvent, MarkerEvent
from engine.glyphs.arms import GLYPHS
from engine.glyphs.emblems import EMBLEMS
from engine.provenance import emblem_usage
from engine.refs import recon_emblem_ids
from engine.registry import validate_events
from rules import load_rules
from tests.anti_inertia._ast_util import REPO

FIX = REPO / "tests" / "fixtures" / "preview" / "war"


def _fx(name: str) -> dict:
    return yaml.safe_load((FIX / name).read_text(encoding="utf-8"))["event"]


class WarSymbolRegistryTest(unittest.TestCase):
    def test_rule_glyphs_equal_renderers(self) -> None:
        self.assertEqual(load_rules().war_history.symbol_sets.glyph_names(), set(GLYPHS))

    def test_reconstructions_have_renderer(self) -> None:
        rec = load_emblem_registry().reconstructions
        self.assertTrue(rec)
        for k, r in rec.items():
            self.assertIn(r.glyph, EMBLEMS, k)

    def test_fixtures_validate_and_cover(self) -> None:
        m, b = _fx("marker_glyph.yaml"), _fx("badge_emblem.yaml")
        self.assertEqual(len(validate_events([m, b])), 2)
        self.assertIn(m["glyph"], GLYPHS)
        self.assertIn(b["emblem"], load_emblem_registry().reconstructions)
        self.assertEqual(recon_emblem_ids(b), [b["emblem"]])

    def test_bad_values_are_errors(self) -> None:
        m = _fx("marker_glyph.yaml")
        with self.assertRaises(ValidationError):
            MarkerEvent.model_validate({**m, "glyph": "tank"})              # 세트 밖
        with self.assertRaises(ValidationError):
            MarkerEvent.model_validate({**m, "icon": "boom"})               # boom 과 함께 금지
        b = _fx("badge_emblem.yaml")
        with self.assertRaises(ValidationError):
            BadgeEvent.model_validate({**b, "img": "x"})                    # img·emblem 둘 다
        with self.assertRaises(ValidationError):
            BadgeEvent.model_validate({k: v for k, v in b.items() if k != "emblem"})   # 둘 다 없음
        with self.assertRaises(ValidationError):
            BadgeEvent.model_validate({**b, "kind": "flag", "flag": "it"})  # emblem 은 kind emblem 만

    def test_old_events_unchanged(self) -> None:
        """새 필드는 쓰지 않으면 dict 에 남지 않는다(기존 영상 이벤트 dict·provenance 그대로)."""
        old = {"type": "marker", "t0": 0, "t1": 1, "lon": 1.0, "lat": 2.0, "label": "x"}
        self.assertNotIn("glyph", validate_events([old])[0])
        self.assertEqual(emblem_usage([old], lambda _i: None), {"used": [], "flag_fallback": {}})

    def test_provenance_records_war_symbols(self) -> None:
        ev = validate_events([_fx("marker_glyph.yaml"), _fx("badge_emblem.yaml")])
        u = emblem_usage(ev, lambda _i: None)
        self.assertEqual((u["marker_glyphs"], u["reconstructed"]), (["heavy_inf"], ["carthage_tanit"]))

    def test_marker_glyph_renders_ink(self) -> None:
        from engine.layers import markers  # noqa: PLC0415

        ev = validate_events([_fx("marker_glyph.yaml")])[0]
        ev["world"] = (0.0, 0.0)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 120, 80)
        ctx = cairo.Context(surf)
        from engine.stage import MercatorStage  # noqa: PLC0415

        view = mock.Mock(ox=0.0, oy=0.0, vw=120, vh=80, stage=MercatorStage(config={"theme": "relief"}))
        view.to_screen.return_value = (40.0, 40.0)
        R = mock.Mock(reserved=[])  # noqa: N806
        with mock.patch.object(markers, "icon") as dot:
            try:
                markers.draw_marker(ctx, R, view, 4.0, ev)
            except Exception:  # noqa: BLE001 — 라벨 조판 단계(목 R)는 이 시험 밖. 픽토그램은 그 전에 그려진다
                pass
            dot.assert_not_called()   # 점 대신 픽토그램
        surf.flush()
        data = surf.get_data()
        self.assertTrue(any(data[i + 3] for i in range(((40 - 4) * 120 + 34) * 4, ((40 - 4) * 120 + 46) * 4, 4)))


if __name__ == "__main__":
    unittest.main()
