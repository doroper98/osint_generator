"""차트는 하나의 세계 — [chart-only-run]·[chart-world-split] (v7.4.0, back_and_forth D-0251 §6.2·D-0252, 사용자 의견 UF-135).

UF-135 원문: "너무 차트만 나오기도 하고, 여러 맥락의 차트들이 나오는데, 그게 같은 축척 혹은 같은 차트 안에서 움직이거나 보여주는게
아니니까 전혀 눈에 들어오거나 맥락을 파악하기가 어려웠어."
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest import mock

from engine import checks
from rules import load_rules

C = load_rules().qa_checks.chart_only_run


def _P(events: list[dict], stage: str = "backdrop", shots: list | None = None, total: float = 60.0,  # noqa: N802
       fullcard: tuple[float, float] | None = None, series_range: dict | None = None) -> NS:
    tb = NS(in_fullcard=lambda t: fullcard is not None and fullcard[0] <= t <= fullcard[1])
    return NS(events=events, shots=shots or [], plan=NS(total=total),
              R=NS(tb=tb, stage=NS(name=stage), cache={"series_range": series_range or {}}))


def _hard(P: NS) -> list[str]:  # noqa: N803
    return [f"x{b - a}" for a, b in checks.chart_only_runs(P) if b - a > C.max_sec]


class ChartOnlyRunTest(unittest.TestCase):
    def test_long_chart_only_fails(self) -> None:
        """fed v16 구성(backdrop + 차트 아일랜드만 20초) → hard."""
        ev = [{"type": "island", "kind": "chart", "t0": 5.0, "t1": 25.0}, {"type": "series", "t0": 5.0, "t1": 25.0}]   # v7.4.0 D-0306 — card 폐지
        runs = checks.chart_only_runs(_P(ev))
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0][1] - runs[0][0], 20.0, delta=0.2)
        self.assertEqual(len(_hard(_P(ev))), 1)

    def test_event_pin_breaks_run(self) -> None:
        """사건 핀(marker)·사진이 한 번 끼면 구간이 끊긴다."""
        ev = [{"type": "island", "kind": "chart", "t0": 5.0, "t1": 25.0}, {"type": "series", "t0": 5.0, "t1": 25.0},
              {"type": "marker", "t0": 14.0, "t1": 16.0}]
        self.assertEqual(_hard(_P(ev)), [])

    def test_map_is_not_chart(self) -> None:
        """지도 무대(덮개 없음) 위 카드는 차트-only 가 아니다 — 지도는 장소다. 패널이 지도를 덮으면 차트-only."""
        self.assertEqual(checks.chart_only_runs(_P([{"type": "card", "t0": 0.0, "t1": 30.0}], stage="mercator")), [])
        runs = checks.chart_only_runs(_P([{"type": "panel", "kind": "dots", "t0": 0.0, "t1": 30.0}], stage="mercator"))
        self.assertEqual(len(runs), 1)

    def test_timeline_axis_is_chart(self) -> None:
        """timeline 무대의 시간축은 차트다(D-0252 확인 ②) — series 만 있는 시간축 20초 = hard."""
        self.assertEqual(len(_hard(_P([{"type": "series", "t0": 0.0, "t1": 20.0}], stage="timeline"))), 1)

    def test_fullcard_and_neutral(self) -> None:
        """타이틀·엔딩 카드 구간은 끊는다. dip 은 판정에 넣지 않는다."""
        ev = [{"type": "series", "t0": 0.0, "t1": 20.0}, {"type": "dip", "t0": 0.0, "t1": 20.0}]
        self.assertEqual(_hard(_P(ev, stage="timeline", fullcard=(8.0, 12.0))), [])
        self.assertEqual(len(_hard(_P(ev, stage="timeline"))), 1)

    def test_exempt_regression_only(self) -> None:
        """D-0271 — 면제는 회귀 기준 hormuz_korea 하나(시험 고정). 면제 프로젝트도 구간은 계산·기록하고 hard 만 뺀다."""
        from pathlib import Path  # noqa: PLC0415

        self.assertEqual(sorted(C.exempt_projects), ["hormuz_korea"])
        src = (Path(checks.__file__).parent / "mux.py").read_text(encoding="utf-8")
        self.assertIn("P.root.name not in QA.chart_only_run.exempt_projects", Path(checks.__file__).read_text(encoding="utf-8"))
        self.assertIn('prov["chart_only_exempt"] = P.root.name in load_rules().qa_checks.chart_only_run.exempt_projects', src)
        ev = [{"type": "series", "t0": 0.0, "t1": 20.0}]
        for name, n in (("hormuz_korea", 0), ("showcase_econ", 1)):
            P = _P(ev, stage="timeline")  # noqa: N806
            P.root = Path(name)
            runs = checks.chart_only_runs(P)
            self.assertEqual(len(runs), 1)   # 구간 기록은 면제와 무관
            hard = [r for r in runs if r[1] - r[0] > C.max_sec and P.root.name not in C.exempt_projects]
            self.assertEqual(len(hard), n)

    def test_rules_key(self) -> None:
        self.assertEqual(C.max_sec, 12)   # D-0252 Fable 결정 — 바꾸면 결정 기록과 함께
        self.assertIn("chart_only_run", checks.HARD)


class ChartWorldSplitTest(unittest.TestCase):
    def _rec(self, unit: str) -> NS:
        return NS(unit=unit)

    def test_same_unit_different_lanes_fail(self) -> None:
        ev = [{"type": "island", "kind": "chart", "t0": 0.0, "t1": 5.0}, {"type": "island", "kind": "chart", "t0": 6.0, "t1": 9.0},
              {"type": "series", "series_id": "A", "lane": "policy_rate", "style": "step", "t0": 0.0, "t1": 5.0},
              {"type": "series", "series_id": "B", "lane": "inflation", "style": "line", "t0": 6.0, "t1": 9.0}]
        P = _P(ev, series_range={"policy_rate": (0.0, 5.5), "inflation": (0.0, 9.1)})  # noqa: N806
        with mock.patch("data.series.load_series", lambda sid: self._rec("%")):
            out = checks.check_chart_world_split(P)
        self.assertEqual(len(out), 1)
        self.assertIn("[chart-world-split]", out[0])
        with mock.patch("data.series.load_series", lambda sid: self._rec("%" if sid == "A" else "pt")):
            self.assertEqual(checks.check_chart_world_split(P), [])

    def test_single_island_or_none_passes(self) -> None:
        ev = [{"type": "island", "kind": "chart", "t0": 0.0, "t1": 9.0},
              {"type": "series", "series_id": "A", "lane": "a", "style": "step", "t0": 0.0, "t1": 9.0},
              {"type": "series", "series_id": "B", "lane": "b", "style": "line", "t0": 0.0, "t1": 9.0}]
        with mock.patch("data.series.load_series", lambda sid: self._rec("%")):
            self.assertEqual(checks.check_chart_world_split(_P(ev, series_range={"a": (0, 1), "b": (0, 2)})), [])


class ChartWorldPromptTest(unittest.TestCase):
    def test_director_prompt_has_rule_lines(self) -> None:
        from workers.prompt_loader import load_prompt

        rules = load_rules()
        for name in ("director", "revise_direction"):
            s = load_prompt(name, rules)
            self.assertIn(rules.chart_world.grammar[0], s)
            self.assertIn(f"{C.max_sec:g}초 이하", s)
            self.assertNotIn("{max_sec}", s)


if __name__ == "__main__":
    unittest.main()
