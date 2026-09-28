"""NB27 — 글꼴 없는 환경의 CLI 서브프로세스 테스트는 사유 있는 skip (v4.0.0, back_and_forth D-0072 §0)."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path
from unittest import mock

from tests import _fonts

REPO = Path(__file__).resolve().parent.parent
TARGETS = {("test_engine_service.py", "test_real_cli_direction_validate"),
           ("test_gates_pipeline.py", "test_script_gate_view_sections")}


class FontsReadyTest(unittest.TestCase):
    def test_no_fc_match_means_not_ready(self) -> None:
        _fonts.fonts_ready.cache_clear()
        try:
            with mock.patch.object(_fonts.shutil, "which", return_value=None):
                self.assertFalse(_fonts.fonts_ready())
        finally:
            _fonts.fonts_ready.cache_clear()

    def test_missing_family_means_not_ready(self) -> None:
        _fonts.fonts_ready.cache_clear()
        try:
            with mock.patch.object(_fonts.shutil, "which", return_value="/usr/bin/fc-match"), \
                 mock.patch("engine.typography.family_found", return_value=False):
                self.assertFalse(_fonts.fonts_ready())
        finally:
            _fonts.fonts_ready.cache_clear()

    def test_subprocess_tests_carry_skip(self) -> None:
        """두 서브프로세스 테스트에 fonts_ready skip 장식이 붙어 있다(사유 문자열 포함)."""
        found = set()
        for fname, test in TARGETS:
            tree = ast.parse((REPO / "tests" / fname).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == test:
                    src = [ast.unparse(d) for d in node.decorator_list]
                    if any("skipUnless(fonts_ready(), NO_FONTS_REASON)" in d for d in src):
                        found.add((fname, test))
        self.assertEqual(found, TARGETS)


if __name__ == "__main__":
    unittest.main()
