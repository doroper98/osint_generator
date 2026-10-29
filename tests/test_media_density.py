"""v7.4.0 back_and_forth D-0261 — 사진·영상 하한(사용자 의견 UF-139, UF-119 재발).

UF-139 원문: "그래프만 주구장창 보여줄꺼면 내가 영상을 왜만들고 왜보냐. 내가 레퍼런스 사진이나 영상 풍부하게 하란 말은 어디다 팔아먹고 저딴식으로 만드는거야"
- [media-density] hard: (photo+clip+cutout) ÷ 분 < rules media_beats.min_density_per_min — 사유로 통과 없음.
- [media-none] hard: 연출 후보 실사 0 이면 연출 착수 거부(workers.direction_io.require_visual_media).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

from engine import checks
from rules import load_rules
from workers import direction_io

MB = load_rules().media_beats


def _P(name: str, events: list[dict], total: float = 150.0) -> NS:  # noqa: N802
    return NS(root=Path("/x") / name, events=events, plan=NS(total=total))


class MediaDensityTest(unittest.TestCase):
    def test_below_min_is_hard(self) -> None:
        ev = [{"type": "photo"}, {"type": "clip"}, {"type": "article"}, {"type": "card"}]   # 실사 2 / 2.5분 = 0.8
        out = checks.check_media_density(_P("showcase_econ", ev))
        self.assertEqual(len(out), 1)
        self.assertIn("[media-density]", out[0])
        self.assertIn("media_density", checks.HARD)

    def test_enough_media_passes(self) -> None:
        n = int(MB.min_density_per_min * 2.5) + 1
        ev = [{"type": "photo"}] * (n - 2) + [{"type": "clip"}, {"type": "cutout"}]
        self.assertEqual(checks.check_media_density(_P("showcase_econ", ev)), [])

    def test_exempt_scope_is_regression_fixtures_only(self) -> None:
        self.assertEqual(MB.min_density_per_min, 1.5)
        self.assertEqual(sorted(MB.density_exempt_projects), ["fed_timeline_demo", "hormuz_korea"])
        self.assertEqual(checks.check_media_density(_P("hormuz_korea", [])), [])

    def test_media_none_refuses_direction(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p"
            p.mkdir()
            reg = {"a": NS(kind="article"), "b": NS(kind="inset")}
            with mock.patch.object(direction_io, "project_media", return_value=(reg, True)):
                with self.assertRaisesRegex(ValueError, r"\[media-none\]"):
                    direction_io.require_visual_media(p)
            reg["c"] = NS(kind="photo")
            with mock.patch.object(direction_io, "project_media", return_value=(reg, True)):
                self.assertEqual(direction_io.require_visual_media(p), ["c"])


if __name__ == "__main__":
    unittest.main()
