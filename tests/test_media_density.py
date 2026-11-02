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

    def test_backdrop_counts_as_one_photo(self) -> None:   # D-0265 §5
        self.assertEqual(checks.media_density([{"type": "backdrop"}, {"type": "photo"}, {"type": "article"}], 60.0), (2, 2.0))

    def test_exempt_scope_is_regression_fixtures_only(self) -> None:
        """v7.4.0 D-0311 — 면제는 qa_checks.regression_refs 한 목록(범위 = tests/test_regression_refs.py). 검사 함수 자신은 늘 돈다."""
        self.assertEqual(MB.min_density_per_min, 1.5)
        self.assertEqual(len(checks.check_media_density(_P("hormuz_korea", []))), 1)   # 면제는 run_checks 의 waive_regression 에서

    def test_provenance_records_exempt_too(self) -> None:
        """D-0262 ② — 면제 프로젝트도 검사는 돌고 provenance media_density {count, value, min, exempt} 로 남는다(조용히 건너뛰지 않는다)."""
        import inspect  # noqa: PLC0415

        from engine import mux  # noqa: PLC0415

        src = inspect.getsource(mux)
        self.assertIn('prov["media_density"]', src)
        self.assertIn('"exempt": prov["regression_ref"] is not None', src)   # v7.4.0 D-0311
        self.assertEqual(checks.media_density([{"type": "photo"}, {"type": "clip"}], 120.0), (2, 1.0))

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


class WarHistoryDensityTest(unittest.TestCase):
    """v7.4.0 D-0618 — 고대·근세 전쟁사는 사료 인용 카드(quote.source)를 기록으로 센다. 패널은 세지 않는다. 몫 상한."""

    @staticmethod
    def _p(events: list[dict], date: str = "-216", total: float = 120.0) -> NS:
        return NS(root=Path("/x/war"), events=events, plan=NS(total=total, sentences=[NS(date=date)]),
                  R=NS(cache={"genre": {"name": "war_history"}}))

    def test_quote_source_counts_ancient(self) -> None:
        ev = [{"type": "photo"}] * 2 + [{"type": "quote", "source": {"author": "a"}}]   # 3 / 2분 = 1.5
        self.assertEqual(checks.check_media_density(self._p(ev)), [])

    def test_panel_and_modern_quote_not_counted(self) -> None:
        ev = [{"type": "photo"}] * 2 + [{"type": "panel"}, {"type": "quote", "flag": "us"}]
        self.assertTrue(checks.check_media_density(self._p(ev)))

    def test_modern_era_does_not_count_quote_source(self) -> None:
        ev = [{"type": "photo"}] * 2 + [{"type": "quote", "source": {"author": "a"}}]
        self.assertTrue(checks.check_media_density(self._p(ev, date="1950.09.15")))

    def test_share_cap(self) -> None:
        ev = [{"type": "photo"}] + [{"type": "quote", "source": {"author": "a"}}] * 2   # 2/3 > 0.34
        out = checks.check_media_density(self._p(ev, total=60.0))
        self.assertTrue(any("몫 상한" in x for x in out))
