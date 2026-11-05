"""v7.4.0 D-0632 — terrain3d '개략' 출처 줄 글꼴(rules source_note.approx_font)이 사료 서명 글리프를 덮는다.

칸나이 720p 프리뷰에서 이 줄을 버전 도장 글꼴(mono)로 그려 『』 가 [glyphs] hard 로 걸렸다(mono 에 없음).
"""

from __future__ import annotations

import inspect
import unittest

from engine import typography
from engine.layers import terrain3d
from rules import load_rules


class ApproxFontTest(unittest.TestCase):
    def test_font_covers_source_titles(self) -> None:
        key = load_rules().source_note.approx_font
        cmap = typography.font_cmap(key)
        miss = [ch for ch in "『』「」가힣·—~()" if ord(ch) not in cmap]
        self.assertEqual(miss, [], f"source_note.approx_font={key} 에 없는 글리프")

    def test_draw_labels_uses_rule_font(self) -> None:
        src = inspect.getsource(terrain3d.draw_labels)
        self.assertIn("R.source_note.approx_font", src)
        self.assertNotIn("STAMP.font", src)


if __name__ == "__main__":
    unittest.main()
