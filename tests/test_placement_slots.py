"""engine/placement — 배치 슬롯(17 §2 `place:`) → 좌표 (v3.1.0, back_and_forth D-0047 작업 5·9)."""

from __future__ import annotations

import unittest

import numpy as np

from engine.placement import PlacementError, resolve_places
from engine.projection import View, ym
from rules import load_rules

PL = load_rules().placement
TIERS = {"W": {"lon0": 20.0, "lon1": 150.0, "lat0": -10.0, "lat1": 60.0, "levels": []}}


def view(_t: float) -> View:
    return View(np.array([56.0, ym(26.0), 14.0]), TIERS, {})


class SlotTest(unittest.TestCase):
    def test_box_slot(self) -> None:
        ev = [{"type": "photo", "t0": 1, "t1": 5, "mid": "rok_iraq", "place": "panel_gap"}]
        rec = resolve_places(ev, view)
        self.assertEqual((ev[0]["x"], ev[0]["y"], ev[0]["w"]), PL.slots["panel_gap"].box)
        self.assertNotIn("place", ev[0])
        self.assertEqual(rec["rok_iraq"], "slot:panel_gap")

    def test_point_slot_inverse_projects(self) -> None:
        ev = [{"type": "badge", "t0": 3, "t1": 8, "label": "서울", "place": "map_upper_right"}]
        resolve_places(ev, view)
        x, y = view(3).xy(ev[0]["lon"], ev[0]["lat"])
        self.assertAlmostEqual(x, PL.slots["map_upper_right"].point[0], places=6)
        self.assertAlmostEqual(y, PL.slots["map_upper_right"].point[1], places=6)

    def test_card_slot_default_y(self) -> None:
        ev = [{"type": "card", "t0": 1, "t1": 2, "place": "card_right"}]
        resolve_places(ev, view)
        self.assertNotIn("y", ev[0])   # null = 렌더러 기본

    def test_wrong_kind_and_unknown_slot(self) -> None:
        with self.assertRaises(PlacementError):
            resolve_places([{"type": "badge", "t0": 0, "t1": 1, "place": "panel_gap"}], view)
        with self.assertRaises(PlacementError):
            resolve_places([{"type": "photo", "t0": 0, "t1": 1, "mid": "x", "place": "nowhere"}], view)

    def test_auto_media_is_v3_slots(self) -> None:
        self.assertEqual(PL.slots[PL.auto_media["clip"]["map"]].box, (40, 150, 300))
        self.assertEqual(PL.slots[PL.auto_media["photo"]["map"]].box, (560, 196, 262))


def _timeline(t0: float = 0, t1: float = 20) -> dict:
    """왼쪽(2~4월)에 사건이 몰린 연표 — hormuz_ai timeline_4 와 같은 모양(D-0050 NB9)."""
    evs = [("2026-02-28", "미국·이스라엘, 이란 공습", -1), ("2026-03-15", "트럼프, 해협 방어 요구", -2),
           ("2026-04-13", "미국 해상 봉쇄", -1), ("2026-07-08", "휴전 붕괴", -1)]
    return {"type": "panel", "kind": "timeline", "t0": t0, "t1": t1, "title": "연표", "start": "2026-02-01", "end": "2026-09-30",
            "events": [{"date": d, "label": lb, "col": "us", "side": sd, "t": t0 + 1 + i} for i, (d, lb, sd) in enumerate(evs)]}


def _ext(h: float = 145, text_w: float = 190):  # noqa: ANN202
    return lambda e, w: (h, max(w, text_w))


class BesidePanelSlotTest(unittest.TestCase):
    """패널 옆 미디어 슬롯(v3.2.0, D-0050 NB9) — 패널이 차지한 상자·자막·날짜를 피한다. 자리가 없으면 오류(P6)."""

    def _boxes(self, tl: dict, t: float) -> list:
        import cairo  # noqa: PLC0415

        from engine.panels import timeline  # noqa: PLC0415

        return timeline.occupied(cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)), tl, t)

    def test_picks_free_corner_outside_timeline(self) -> None:
        tl = _timeline()
        clip = {"type": "clip", "t0": 5, "t1": 10, "mid": "strikes", "place": "clip_panel_side"}
        rec = resolve_places([tl, clip], view, _ext())
        self.assertEqual(rec["strikes"], "slot:clip_panel_side")
        b = (clip["x"], clip["y"], clip["x"] + 190, clip["y"] + 145)
        for o in self._boxes(tl, clip["t1"]):
            self.assertFalse(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3], (b, o))
        self.assertEqual(clip["w"], PL.slots["clip_panel_side"].beside_panel.w)

    def test_caption_text_width_counts(self) -> None:
        """출처 줄이 바보다 길면 그 끝까지 화면 안 — 첫 후보(오른쪽 끝)가 밀려난다."""
        cands = PL.slots["clip_panel_side"].beside_panel.candidates
        clip = {"type": "clip", "t0": 5, "t1": 10, "mid": "strikes", "place": "clip_panel_side"}
        resolve_places([_timeline(), clip], view, _ext(text_w=275))
        self.assertNotEqual((clip["x"], clip["y"]), tuple(cands[0]))
        self.assertLessEqual(clip["x"] + 275, 854)

    def test_no_panel_is_error(self) -> None:
        with self.assertRaises(PlacementError):
            resolve_places([{"type": "clip", "t0": 0, "t1": 1, "mid": "strikes", "place": "clip_panel_side"}], view, _ext())

    def test_all_blocked_is_error(self) -> None:
        with self.assertRaises(PlacementError) as cm:
            resolve_places([_timeline(), {"type": "clip", "t0": 5, "t1": 10, "mid": "strikes", "place": "clip_panel_side"}],
                           view, _ext(h=400))
        self.assertIn("후보", str(cm.exception))

    def test_panel_kind_without_occupancy_is_error(self) -> None:
        panel = {"type": "panel", "kind": "versus", "t0": 0, "t1": 20}
        with self.assertRaises(PlacementError) as cm:
            resolve_places([panel, {"type": "photo", "t0": 5, "t1": 10, "mid": "rok_iraq", "place": "clip_panel_side"}],
                           view, _ext())
        self.assertIn("OCCUPIED", str(cm.exception))

    def test_prompt_describes_slot_form(self) -> None:
        from workers.prompt_loader import load_prompt  # noqa: PLC0415

        txt = load_prompt("director", load_rules())
        line = next(ln for ln in txt.splitlines() if "clip_panel_side" in ln)
        self.assertIn("패널 위 미디어", line)


if __name__ == "__main__":
    unittest.main()


REPO_HZ = __import__("pathlib").Path(__file__).resolve().parent.parent / "projects" / "hormuz_korea"


@unittest.skipUnless((REPO_HZ / "plan.json").exists(), "hormuz_korea plan.json(로컬 생성물) 없음")
class CheckDirectionPlaceTest(unittest.TestCase):
    """연출 워커의 저장 전 점검은 렌더와 같은 경로 — place 로 둔 뱃지는 좌표 없이도 통과해야 한다(v3.1.0 hormuz_ai 실측 버그)."""

    def test_badge_place_passes(self) -> None:
        from engine.direction import load_direction_doc  # noqa: PLC0415
        from workers.direction_io import check_direction  # noqa: PLC0415

        doc = load_direction_doc(REPO_HZ / "direction.yaml")
        badge = next(e for e in doc.events if e.get("type") == "badge")
        placed = {k: v for k, v in badge.items() if k not in ("lon", "lat", "at_place")} | {"place": "map_upper_right"}
        doc = doc.model_copy(update={"events": [*doc.events, placed]})
        check_direction(doc, REPO_HZ)

    def test_bad_slot_is_value_error(self) -> None:
        from engine.direction import load_direction_doc  # noqa: PLC0415
        from workers.direction_io import check_direction  # noqa: PLC0415

        doc = load_direction_doc(REPO_HZ / "direction.yaml")
        badge = next(e for e in doc.events if e.get("type") == "badge")
        bad = {k: v for k, v in badge.items() if k not in ("lon", "lat", "at_place")} | {"place": "nowhere"}
        with self.assertRaises(ValueError):
            check_direction(doc.model_copy(update={"events": [*doc.events, bad]}), REPO_HZ)
