"""RENDER-AP-032 — 표준 글꼴 렌더 설정 장치(v7.4.0, back_and_forth D-0624).

컨테이너 재시작으로 셸의 FONTCONFIG_FILE 이 사라져 렌더·시험이 힌팅 꺼진 화소를 조용히 냈다(R-0329, 골든 25컷 0/25).
장치: 저장소 추적 설정 파일(config.yaml engine.fontconfig.file) + engine.style import 맨 앞의 engine.fontenv.ensure()
(FONTCONFIG_FILE 지정 + 주 글꼴 hinting·hintstyle 점검, 다르면 FontRenderConfigError). 이 시험은
① 설정 파일이 저장소 안·컨테이너 경로 없음 ② 표준 파일로 점검 통과 ③ 비표준 설정(힌팅 끔·hintstyle 0)이면 점검 실패
④ 모든 글자 그리는 경로가 그 한 곳을 지난다(engine.style 맨 앞 호출·conftest·엔진 밖 글자 도구)를 강제한다.
"""

from __future__ import annotations

import ast
import os
import re
import tempfile
import unittest
from pathlib import Path

from engine import fontenv
from orchestrator.config import load_config

REPO = Path(__file__).resolve().parents[2]
TEXT_CALLS = re.compile(r"\b(show_text|text_path|select_font_face|PangoCairo)\b")
SCAN = ("engine", "sketch", "tools", "orchestrator", "script", "audio")


def _env(conf: Path) -> dict[str, str]:
    return {**os.environ, "FONTCONFIG_FILE": str(conf)}


class FontconfigGuardTest(unittest.TestCase):
    def test_config_file_tracked_and_portable(self) -> None:
        fc = load_config().engine.fontconfig
        self.assertIsNotNone(fc)
        path = REPO / fc.file
        self.assertTrue(path.is_file(), path)
        self.assertFalse(Path(fc.file).is_absolute(), "설정 경로는 저장소 기준 상대 경로")
        body = path.read_text(encoding="utf-8")
        self.assertIn("/etc/fonts/fonts.conf", body)   # 시스템 설정을 include 한 뒤 덮어쓴다
        self.assertNotRegex(body, r"/root/|/home/|\.config/")   # 컨테이너 고유 경로 금지
        for prop in ("antialias", "hinting", "hintstyle", "autohint", "rgba", "lcdfilter", "embeddedbitmap"):
            self.assertRegex(body, rf'<edit name="{prop}" mode="assign">', prop)

    def test_standard_file_passes(self) -> None:
        path = fontenv.config_file()
        got = fontenv.check(_env(path))
        self.assertEqual(got, load_config().engine.fontconfig.expect.model_dump())

    def test_nonstandard_fails(self) -> None:
        """힌팅 끈 설정(재시작 뒤 사고 상태와 같은 값)이면 점검이 멈춘다."""
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "fonts.conf"
            bad.write_text(fontenv.config_file().read_text(encoding="utf-8")
                           .replace("<bool>true</bool></edit>\n    <edit name=\"hintstyle\"", "<bool>false</bool></edit>\n    <edit name=\"hintstyle\"")
                           .replace("hintslight", "hintnone"), encoding="utf-8")
            self.assertIn("hintnone", bad.read_text(encoding="utf-8"))
            with self.assertRaises(fontenv.FontRenderConfigError):
                fontenv.check(_env(bad))

    def test_ensure_overrides_env(self) -> None:
        self.assertEqual(os.environ.get("FONTCONFIG_FILE"), str(fontenv.config_file()))   # conftest·engine.style 가 이미 지정

    def test_style_calls_ensure_first(self) -> None:
        """engine.style 의 첫 실행 문이 ensure() — 규칙·글꼴을 읽기 전."""
        tree = ast.parse((REPO / "engine" / "style.py").read_text(encoding="utf-8"))
        calls = [n for n in tree.body if isinstance(n, (ast.Expr, ast.Assign))
                 and not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
        first = calls[0]
        self.assertIsInstance(first, ast.Expr)
        self.assertEqual(getattr(first.value.func, "id", None), "_ensure_fontconfig")
        self.assertIn("ensure()", (REPO / "tests" / "conftest.py").read_text(encoding="utf-8"))

    def test_text_drawers_pass_through(self) -> None:
        """글자를 그리는 모듈은 engine(→ engine.style) 을 import 하거나 fontenv.ensure 를 직접 부른다(C12 ③)."""
        miss = []
        for top in SCAN:
            for p in (REPO / top).rglob("*.py"):
                s = p.read_text(encoding="utf-8")
                if TEXT_CALLS.search(s) and not re.search(r"^\s*(from engine[ .]|import engine)", s, re.M):
                    miss.append(str(p.relative_to(REPO)))
        self.assertEqual(miss, [])


if __name__ == "__main__":
    unittest.main()
