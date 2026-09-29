"""시간축 전용 영상의 자산·권리·엔딩 카드 (v4.3.0, back_and_forth D-0084 작업 6).

지도를 쓰지 않으면 지형 자산을 읽지 않고(geo.prep 불필요) 지도 권리도 요구하지 않는다. 데이터 레코드를 그리면
엔딩 크레딧에 auto: series 절(레코드 출처·라이선스 표기 원문·기준 시점)이 있어야 한다(C9, 20 §5.1).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from data.series import load_series
from engine.assets import Assets, AssetError, Labels
from engine.credits import Credits, RightsError, check_credits, credit_sections, required_refs

RIGHTS = {"fonts": {"ibm": {"name": "IBM Plex Sans KR", "license": "SIL OFL 1.1"}},
          "map": {"natural_earth": {"name": "Natural Earth", "license": "Public domain"}},
          "narration": {"tts": {"name": "내레이션", "license": "AI 음성 합성"}}}


class TimelineAssetsTest(unittest.TestCase):
    def test_no_geo_needed_without_map(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            a = Assets(Path(d), Labels(), geo=False)
            self.assertEqual((a.tiers, a.geo), ({}, {}))
            with self.assertRaises(AssetError):
                Assets(Path(d), Labels())   # 지도 무대면 지형 티어 필수(옛 동작 그대로)

    def test_map_rights_only_with_map(self) -> None:
        with_map = required_refs([], RIGHTS, lambda _: None, set())
        without = required_refs([], RIGHTS, lambda _: None, set(), uses_map=False)
        self.assertIn("map.natural_earth", with_map)
        self.assertNotIn("map.natural_earth", without)
        self.assertIn("narration.tts", without)


class SeriesCreditsTest(unittest.TestCase):
    CR = {"sections": [{"title": "글꼴", "column": 1, "auto": "fonts"},
                       {"title": "음성", "column": 1, "items": [{"main": "내레이션", "license": "AI 음성 합성", "rights": ["narration.tts"]}]}]}

    def test_series_requires_auto_series_section(self) -> None:
        req = required_refs([], RIGHTS, lambda _: None, set(), uses_map=False)
        cr = Credits.model_validate(self.CR)
        with self.assertRaisesRegex(RightsError, "auto: series"):
            check_credits(cr, RIGHTS, {}, req, series_ids={"FEDFUNDS"})
        cr2 = Credits.model_validate({"sections": [{"title": "자료", "column": 0, "auto": "series"}, *self.CR["sections"]]})
        check_credits(cr2, RIGHTS, {}, req, series_ids={"FEDFUNDS"})

    def test_card_lines_from_records(self) -> None:
        cr = Credits.model_validate({"sections": [{"title": "자료", "column": 0, "auto": "series"}]})
        recs = [load_series("FEDFUNDS"), load_series("CPIAUCSL")]
        (title, items), = credit_sections(cr, RIGHTS, {}, set(), None, recs)
        self.assertEqual(title, "자료")
        self.assertEqual([m for m, _ in items], [r.source for r in recs])
        self.assertTrue(all("Public Domain" in lic and "기준" in lic for _, lic in items))


if __name__ == "__main__":
    unittest.main()
