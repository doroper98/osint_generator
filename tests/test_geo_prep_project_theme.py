"""v5.21.6 D-0190 §3-3 — geo.prep 가 프로젝트 지도 테마 자산도 만든다(테마를 주지 않았을 때). gulf(light) 720p 티어 누락 재발 방지."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from geo import prep as GP

REPO = Path(__file__).resolve().parent.parent


class ProjectThemeTest(unittest.TestCase):
    def test_theme_resolution_order(self) -> None:
        self.assertEqual(GP.project_theme(REPO / "projects" / "gulf_pact_2026"), "light")   # 장르(지정학) 기본값
        self.assertEqual(GP.project_theme(REPO / "projects" / "hormuz_korea"), "dark")      # direction 고정(D-0171)

    def test_main_also_preps_non_default_theme(self) -> None:
        calls: list = []

        def fake(proj, res=None, k=1.0, theme=None):  # noqa: ANN001, ANN202
            calls.append((res, theme))
            return {"tiers": {}}

        proj = REPO / "projects" / "gulf_pact_2026"
        with mock.patch.object(GP, "prep", side_effect=fake), mock.patch("sys.stdout"):
            self.assertEqual(GP.main([str(proj), "--res", "final"]), 0)
            self.assertEqual(calls, [("720p", None), ("720p", "light")])
            calls.clear()
            GP.main([str(proj), "--res", "final", "--theme", "light"])   # 테마를 주면 그 테마만
            self.assertEqual(calls, [("720p", "light")])
        calls.clear()
        with mock.patch.object(GP, "prep", side_effect=fake), mock.patch.object(GP, "project_theme", return_value="dark"), \
                mock.patch("sys.stdout"):
            GP.main([str(proj)])
            self.assertEqual(calls, [(None, None)])   # 기본 테마 프로젝트는 한 번만


if __name__ == "__main__":
    unittest.main()
