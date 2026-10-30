"""레퍼런스 영상 = 액자 주 요소 (v7.4.0, back_and_forth D-0274 §2①②·D-0276, 사용자 의견 UF-141).

UF-141 원문: "영상이 나올 때는 한쪽 구석에 몰아서 그 영상을 보여주지 말고 … 배경을 우리가 블러 처리 해놨잖아? 그 안에 액자 형식으로
보일 수 있게 꽉 채워서. 그러니까 영상도 메인 요소야."
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

from engine import checks
from engine.placement import resolve_places
from rules import load_rules

R = load_rules()


def _clip(**kw: object) -> dict:
    return {"type": "clip", "mid": "niovi", "t0": 10.0, "t1": 18.0, **kw}


class ClipFrameTest(unittest.TestCase):
    def test_slot_values(self) -> None:
        s = R.placement.slots["clip_frame"]
        self.assertEqual((s.box, s.frame, s.kinds), ((68.0, 38.0, 717.0), True, ["clip"]))
        self.assertAlmostEqual(s.box[2] / 854, 0.84, places=2)   # 화면 폭 84 %(D-0276 A)
        self.assertEqual(R.media_beats.clip_show_sec, {"main": (5.0, 20.0), "broll": (3.0, 6.0)})
        self.assertTrue(R.layout_480p.subtitle.over_clip_frame and R.hud.date_badge_over_clip_frame)

    def test_main_clip_goes_to_frame(self) -> None:
        ev = [_clip()]
        rec = resolve_places(ev, lambda t: None, stage_name="backdrop")
        self.assertEqual((ev[0]["x"], ev[0]["y"], ev[0]["w"], ev[0]["frame"]), (68.0, 38.0, 717.0, "clip_frame"))
        self.assertEqual(rec["niovi"], "role:clip_frame")
        self.assertEqual(checks.check_clip_frame(NS(events=ev)), [])
        from engine.events import ClipEvent  # noqa: PLC0415 — 배치된 이벤트가 이벤트 모델을 통과한다(econ 콘티 판 v3 에서 frame 키 거부로 드러남)

        ClipEvent.model_validate(ev[0])

    def test_main_clip_in_corner_is_hard(self) -> None:
        ev = [_clip(place="map_left")]
        resolve_places(ev, lambda t: None, stage_name="mercator")
        self.assertTrue(checks.check_clip_frame(NS(events=ev))[0].startswith("[clip-frame]"))
        self.assertIn("clip_frame", checks.HARD)

    def test_broll_corner_ok_but_length_bounded(self) -> None:
        ev = [_clip(role="broll", t1=14.0, place="map_left")]
        resolve_places(ev, lambda t: None, stage_name="mercator")
        self.assertEqual(checks.check_clip_frame(NS(events=ev)), [])
        ev[0]["t1"] = 20.0   # broll 3~6초 초과
        self.assertTrue(checks.check_clip_frame(NS(events=ev)))


if __name__ == "__main__":
    unittest.main()
