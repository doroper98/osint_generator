"""v7.4.0 back_and_forth D-0229 §2.2(UF-105) — 시점 전환 장치: bridge 문장 앞 호흡(타임라인), plan transitions, 전환 지점 판정."""

from __future__ import annotations

import unittest

from rules import load_rules
from script.lint import transition_points
from script.schema import Script
from script.timeline import layout, sentence_rows

T = load_rules().transition


def _script(bridge: bool) -> Script:
    s = lambda d, t, **k: dict(date=d, text=t, sources=["c1"], **k)  # noqa: E731
    return Script.model_validate(dict(
        title="t", subtitle="s", date="2026.10.18",
        scenes=[dict(id="act1", stage="러시아", sentences=[s("2026.10.01", "가."), s("2026.10.02", "나.")]),
                dict(id="act2", stage="걸프", sentences=[s("2026.06.13", "시점을 올해 6월, 페르시아만으로 옮깁니다.", **({"role": "bridge"} if bridge else {})),
                                                        s("2026.06.13", "다.")])]))


class TransitionPointTest(unittest.TestCase):
    def test_stage_and_date_jump(self) -> None:
        pts = transition_points(_script(True))
        self.assertEqual([(i, k) for i, k, _ in pts], [(2, ["stage", "date_jump"])])

    def test_within_scene_small_jump_no_point(self) -> None:
        self.assertEqual(transition_points(_script(True))[0][0], 2)   # act1 안의 하루 차이는 전환이 아니다


class TimelinePauseTest(unittest.TestCase):
    def _rows(self, bridge: bool) -> tuple[list[dict], list]:
        rows = sentence_rows(_script(bridge))
        for x in rows:
            x["dur"] = 2.0
        tr: list = []
        layout(rows, tr)
        return rows, tr

    def test_bridge_pause_inserted(self) -> None:
        with_b, tr = self._rows(True)
        without, tr0 = self._rows(False)
        self.assertEqual(tr0, [])
        self.assertEqual(len(tr), 1)
        self.assertEqual(tr[0].sid, "act2_0")
        self.assertAlmostEqual(with_b[2]["t0"] - without[2]["t0"], T.bridge_pause_sec)
        self.assertAlmostEqual(tr[0].pause_t0 + tr[0].pause_sec, with_b[2]["t0"])
        self.assertEqual(with_b[2]["role"], "bridge")

    def test_no_bridge_layout_unchanged(self) -> None:
        rows = sentence_rows(_script(False))
        for x in rows:
            x["dur"] = 2.0
        a = layout([dict(r) for r in rows])
        b = layout([dict(r) for r in rows], [])
        self.assertEqual(a[2], b[2])


if __name__ == "__main__":
    unittest.main()
