"""v7.4.0 사용자 지시 UF-906 ① "저놈에 금리 차트좀 예시에서 빼"(CLAUDE.md C0.0 §5) — 사용자에게 보이는 시연 프로젝트에는 연준 금리 차트가 없다.

시연 프로젝트 = `projects/studio_showcase*`(디자인 시스템 시연 고정물). 연출·원고·시리즈 어디에도 연준 금리 레코드·문구가 없어야 한다.
"""

from __future__ import annotations

import re
import unittest

from tests.anti_inertia._ast_util import REPO

BANNED_SERIES = ("FEDFUNDS", "DFEDTARU", "DFEDTARL", "CPIAUCSL")          # 연준 금리·물가 차트 레코드(data/series)
BANNED_WORDS = re.compile("연방기금|기준금리|연준|FOMC|fed_", re.I)


class DemoNoRateChartTest(unittest.TestCase):
    def test_showcase_projects_have_no_fed_rate_chart(self) -> None:
        projs = sorted(p for p in (REPO / "projects").glob("studio_showcase*") if p.is_dir())
        self.assertTrue(projs, "시연 프로젝트(projects/studio_showcase*)가 없다")
        for p in projs:
            for f in sorted(p.rglob("*.yaml")):
                s = f.read_text(encoding="utf-8")
                body = "\n".join(ln for ln in s.splitlines() if not ln.lstrip().startswith("#"))   # 주석(지시 인용)은 본다 대상 아님
                for sid in BANNED_SERIES:
                    self.assertNotIn(sid, body, f"{f.relative_to(REPO)} 에 금리 차트 레코드 {sid}")
                self.assertIsNone(BANNED_WORDS.search(body), f"{f.relative_to(REPO)} 에 연준 금리 문구")


if __name__ == "__main__":
    unittest.main()
