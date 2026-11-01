"""[connective-repeat]·[attribution-repeat] 린트 경고(v7.4.0 back_and_forth D-0608, D-0609 §1-2).

규칙 키 = rules script_grammar.connective_repeat_max · attribution_repeat_max_per_min. 경고만(영상을 막지 않음), 면제 목록(lint_waivable)에 있다.
"""

from __future__ import annotations

import unittest

from rules import load_rules
from script.lint import repeat_issues
from script.schema import Script


def _script(*texts: str) -> Script:
    return Script.model_validate({"title": "t", "subtitle": "s", "date": "2026.09.18", "scenes": [
        {"id": "a", "sentences": [{"date": "2026", "text": t, "sources": ["c1"]} for t in texts]}]})


def _kinds(sc: Script) -> list[str]:
    return [i.kind for i in repeat_issues(sc)]


class ConnectiveRepeatTest(unittest.TestCase):
    def test_rule_keys(self) -> None:
        sg = load_rules().script_grammar
        self.assertEqual((sg.connective_repeat_max, sg.attribution_repeat_max_per_min), (1, 4))
        self.assertTrue({"connective-repeat", "attribution-repeat"} <= set(sg.lint_waivable))

    def test_same_connective_twice_in_a_row_warns_once(self) -> None:
        sc = _script("가는 왔습니다.", "그래서 나는 갔습니다.", "그래서 다는 멈췄습니다.", "그래서 라는 섰습니다.")
        got = repeat_issues(sc)
        self.assertEqual([(i.kind, i.severity, i.sid) for i in got], [("connective-repeat", "warning", "a_2")])

    def test_alternating_or_separated_is_fine(self) -> None:
        self.assertEqual(_kinds(_script("그래서 가는 왔습니다.", "하지만 나는 갔습니다.", "그래서 다는 멈췄습니다.")), [])
        self.assertEqual(_kinds(_script("그래서 가는 왔습니다.", "나는 갔습니다.", "그래서 다는 멈췄습니다.")), [])


class AttributionRepeatTest(unittest.TestCase):
    def test_five_in_a_minute_warns(self) -> None:
        sc = _script(*[f"{n}는 그렇게 말했습니다." for n in ("가", "나", "다", "라", "마")])
        self.assertEqual(_kinds(sc), ["attribution-repeat"])

    def test_four_is_fine_and_spread_out_is_fine(self) -> None:
        self.assertEqual(_kinds(_script(*[f"{n}는 그렇게 말했습니다." for n in ("가", "나", "다", "라")])), [])
        filler = "평야에는 바람이 오래 불었고 강물은 낮게 흘렀으며 병사들은 진영 앞에서 오래 기다렸습니다" * 2   # 약 100자 ≈ 19초
        texts = []
        for n in ("가", "나", "다", "라", "마", "바"):
            texts += [f"{n}는 그렇게 말했습니다.", filler + "."]
        self.assertEqual(_kinds(_script(*texts)), [])


if __name__ == "__main__":
    unittest.main()
