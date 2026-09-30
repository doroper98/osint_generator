"""저장소의 장르 프로필 파일이 스키마를 통과한다 (v4.2.0, back_and_forth D-0081 작업 2·9)."""

from __future__ import annotations

import unittest

from genres.load import DEFAULT_GENRE, genre_names, load_genre
from rules import load_rules


class GenreFilesTest(unittest.TestCase):
    def test_all_files_load(self) -> None:
        names = genre_names()
        self.assertIn(DEFAULT_GENRE, names)
        for n in names:
            with self.subTest(genre=n):
                self.assertEqual(load_genre(n).genre, n)

    def test_geopolitics_declares_current_pipeline(self) -> None:
        p = load_genre("geopolitics")
        reg = load_rules().registries
        self.assertEqual(p.status, "approved")
        self.assertEqual(p.stage.primary, "mercator")
        self.assertEqual(p.primitives.new, ["site_diagram"])   # v4.4.0 dmz_mine_2026 사용자 요청(현장 개념도) — 그 전까지 []
        carriers = {"primitive", "series"}   # 프리미티브 이벤트는 id 로 센다(checks genre_elements). series = 시간축 무대 전용(v4.3.0) — 지도 장르 밖
        self.assertEqual(set(p.primitives.reuse), (set(reg.event_types) - carriers) | set(reg.panel_kinds) | set(reg.badge_kinds))
        self.assertEqual(set(p.color_semantics.values()), set(reg.accents))   # 09 §7 색 토큰 전부에 의미가 있다

    def test_macro_monetary_is_section3_proposed(self) -> None:
        """20 §3 예시 그대로(D-0081 작업 2) + D-0082 두 대응(timeline_panel → timeline, new 의 planned)."""
        from engine.primitives import style_for  # noqa: PLC0415

        p = load_genre("macro_monetary")
        reg = load_rules().registries
        self.assertEqual(p.status, "proposed")
        self.assertEqual(p.stage.names(), ["backdrop", "timeline"])   # v5.1.0 D-0123 §2 — 기본 무대 backdrop, 보조 timeline(차트 아일랜드·순수 차트)
        self.assertTrue(set(p.stage.names()) <= set(reg.stages))   # 둘 다 등록됨(chart_wall 은 보조 상한 1 때문에 뺐다 — registries.stages_planned 그대로)
        self.assertIn("chart_wall", reg.stages_planned)
        self.assertEqual(p.primitives.new, ["rate_step_line", "dot_plot", "yield_curve_shift", "statement_diff", "target_band"])
        self.assertEqual(set(p.primitives.new) - set(reg.primitives), set(reg.primitives_planned))
        self.assertIn("timeline", p.primitives.reuse)
        self.assertEqual(set(style_for("statement_diff", p.color_semantics).colors), {"added", "removed"})


if __name__ == "__main__":
    unittest.main()
