"""G13 backdrop 전용 사진 슬롯(v5.2.0, back_and_forth D-0132 A).

- 슬롯 `backdrop_right_low` = 레지스트리(rules)·렌더러(engine.placement 무대 전용 판정 → media_box)·프리뷰 예제 세 곳(C7).
- backdrop 주 무대에서만 쓴다 — 다른 무대에서 쓰면 배치 오류(P10). 코드가 다른 슬롯으로 옮기지 않는다(P8).
- 실제 높이(가공 크롭 비율 + 캡션 바)로 카드 예약 구역·자막 구역·left 차트 아일랜드와 교차 0.
"""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace as NS

import yaml

from engine.direction import Direction
from engine.island import _inter
from engine.media_plan import media_box
from engine.placement import PlacementError, resolve_places
from rules import load_rules
from tests.anti_inertia._ast_util import REPO
from workers.prompt_loader import _rules_placeholders

R = load_rules()
SLOT = "backdrop_right_low"
PREVIEW = REPO / "tests" / "fixtures" / "preview"


def _photo() -> dict:
    return {"type": "photo", "t0": 1.0, "t1": 5.0, "mid": "p", "place": SLOT}


def _asset(crop: tuple[int, int]) -> NS:
    return NS(tool=NS(params={"crop": list(crop)}))


class SlotRegistryTest(unittest.TestCase):
    def test_slot_exists_backdrop_only(self) -> None:
        s = R.placement.slots[SLOT]
        self.assertEqual(list(s.box), [594, 212, 236])
        self.assertEqual(s.stages, ["backdrop"])
        self.assertTrue(set(s.stages) <= set(R.registries.stages))
        self.assertEqual(sorted(s.kinds), ["clip", "photo"])
        ev = [_photo()]
        rec = resolve_places(ev, lambda t: None, stage_name="backdrop")
        self.assertEqual(rec["p"], f"slot:{SLOT}")
        self.assertEqual([ev[0]["x"], ev[0]["y"], ev[0]["w"]], [594, 212, 236])
        for other in ("timeline", "mercator", None):
            with self.assertRaises(PlacementError, msg=other):
                resolve_places([_photo()], lambda t: None, stage_name=other)

    def test_preview_example_and_prompt(self) -> None:
        raw = yaml.safe_load((PREVIEW / "stage_backdrop.yaml").read_text(encoding="utf-8"))["direction"]
        doc = Direction.model_validate(raw)
        self.assertIn(SLOT, [e.get("place") for e in doc.events])
        line = [ln for ln in _rules_placeholders(R)["{{RULES.placement_slots}}"].splitlines() if ln.startswith(f"- {SLOT} ")]
        self.assertEqual(len(line), 1)
        self.assertIn("backdrop 무대 전용", line[0])
        self.assertIn(SLOT, _rules_placeholders(R)["{{RULES.backdrop_island}}"])


class SlotGeometryTest(unittest.TestCase):
    def test_no_cross_card_subtitle_left_island(self) -> None:
        z = R.layout_480p.reserved_zones
        W = R.layout_480p.base.w  # noqa: N806
        card = (W - z.card.x_from_right, z.card.y[0], z.card.x_from_right, z.card.y[1] - z.card.y[0])
        left = tuple(R.island.boxes["left"])
        reg = json.loads((REPO / "assets" / "media" / "media_registry.json").read_text(encoding="utf-8"))
        items = reg.get("assets", reg) if isinstance(reg, dict) else {a["id"]: a for a in reg}
        crops = {tuple(v["tool"]["params"]["crop"]) for k, v in items.items()
                 if k.startswith("fed_") and v.get("kind") == "photo" and v["tool"]["params"].get("crop")}
        self.assertTrue(crops)
        for crop in crops | {(16, 9)}:
            ev = [_photo()]
            resolve_places(ev, lambda t: None, stage_name="backdrop")
            x0, y0, x1, y1 = media_box(ev[0], {"p": _asset(crop)})
            b = (x0, y0, x1 - x0, y1 - y0)
            self.assertEqual(_inter(b, card), 0.0, crop)
            self.assertEqual(_inter(b, left), 0.0, crop)
            self.assertLessEqual(y1, z.subtitle.y_from, crop)
            self.assertLessEqual(x1, W, crop)


if __name__ == "__main__":
    unittest.main()
