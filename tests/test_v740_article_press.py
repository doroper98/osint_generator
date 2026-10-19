"""v7.4.0 back_and_forth D-0229 §6(UF-109) — [article-press-missing] warning: 인물 발언 보도 문장의 기사 카드에 press 사진이 없다."""

from __future__ import annotations

import types
import unittest

from engine.checks import check_article_press_missing


def _P(events: list[dict], text: str) -> types.SimpleNamespace:  # noqa: N802
    s = types.SimpleNamespace(sid="cold_3", t0=16.0, t1=22.0, text=text)
    return types.SimpleNamespace(events=events, plan=types.SimpleNamespace(sentences=[s]))


ART = dict(type="article", t0=15.0, t1=30.0, mid="art_0032")


class PressTest(unittest.TestCase):
    def test_statement_without_press_warns(self) -> None:
        self.assertEqual(len(check_article_press_missing(_P([ART], "트럼프 대통령이 발표했던 에너지 휴전이 끝났다고 AP통신은 보도했습니다."))), 1)

    def test_with_press_ok(self) -> None:
        self.assertEqual(check_article_press_missing(_P([dict(ART, press="trump_wh")], "트럼프 대통령은 휴전을 발표했습니다.")), [])

    def test_no_person_ok(self) -> None:
        self.assertEqual(check_article_press_missing(_P([ART], "정유소 처리량이 줄었다고 로이터는 보도했습니다.")), [])


if __name__ == "__main__":
    unittest.main()
