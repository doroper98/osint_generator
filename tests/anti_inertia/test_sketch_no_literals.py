"""test_sketch_no_literals — 스케치 계층(sketch/)의 화면 수치·색·import 방향 (D-0140 §3, D130, 15 P1·P3).

스케치는 엔진 밖 독립 패키지라 test_stage_isolation·test_device_space 대상이 아니다. 대신 같은 강도로:
(a) 그리기 모듈의 `text(`·`tw(` 글자 크기 인자 리터럴 0 — 크기는 rules sketch.text·tag 에서
(b) 그리기 모듈의 숫자 리터럴은 허용 집합뿐(test_no_magic_numbers 와 같은 AST 방식). 수식 모듈(geodesy·svg_georef)은 대상 밖
(c) sketch/ 전체에 hex 색 리터럴 0 — 색은 engine.style 토큰 이름
(d) sketch/ 는 orchestrator·workers·engine.render·engine.project 를 import 하지 않는다(P1 방향 고정 — 본편 경로와 섞지 않는다, D128)
검사기 자신이 위반을 잡는지는 합성 소스로 따로 확인한다(빈 패키지에서 통과만 보면 검사기가 죽어 있어도 모른다).
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from tests.anti_inertia._ast_util import REPO, code_strings, docstring_nodes, iter_py

SKETCH_ROOT = "sketch"
DRAW_MODULES: frozenset[str] = frozenset({   # (a)(b) 대상 — 모듈 이름(stem). 패키지 어디에 있든
    "draw", "eez", "sensors", "launch", "profile", "card", "globe", "globe_scene", "fronts", "units", "arrows", "pockets", "scene",
})
FORMULA_MODULES: frozenset[str] = frozenset({"geodesy", "svg_georef"})   # (e) 수식 — (b) 면제
ALLOWED_NUMBERS: frozenset[float] = frozenset({0, 1, 2, 3, 0.5, 90, 180, 360})
SIZE_ARG: dict[str, int] = {"text": 4, "tw": 2}   # 함수 이름 → 글자 크기 위치 인자 번호(engine.typography)
FORBIDDEN_IMPORTS: tuple[str, ...] = ("orchestrator", "workers", "engine.render", "engine.project")
HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")


def _call_name(node: ast.Call) -> str | None:
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _is_number(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)


def size_literals(tree: ast.AST) -> list[int]:
    """(a) text(·)·tw(·) 의 글자 크기 인자가 숫자 리터럴인 줄."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) in SIZE_ARG:
            i = SIZE_ARG[_call_name(node)]   # type: ignore[index]
            args = [node.args[i]] if len(node.args) > i else []
            args += [k.value for k in node.keywords if k.arg == "size"]
            out += [a.lineno for a in args if _is_number(a)]
    return out


def number_literals(tree: ast.AST) -> list[tuple[int, float]]:
    """(b) 허용 집합 밖 숫자 리터럴."""
    skip = docstring_nodes(tree)
    return [(n.lineno, n.value) for n in ast.walk(tree)   # type: ignore[attr-defined]
            if _is_number(n) and id(n) not in skip and n.value not in ALLOWED_NUMBERS]   # type: ignore[attr-defined]


def hex_literals(tree: ast.AST) -> list[tuple[int, str]]:
    """(c) 문자열 리터럴 안 hex 색."""
    return [(c.lineno, m.group(0)) for c in code_strings(tree) for m in HEX.finditer(c.value)]


def bad_imports(tree: ast.AST) -> list[tuple[int, str]]:
    """(d) 금지 import."""
    out = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        hit = [n for n in names if any(n == f or n.startswith(f + ".") for f in FORBIDDEN_IMPORTS)]
        if hit:
            out.append((node.lineno, hit[0]))
    return out


def scan(path: Path) -> list[str]:
    rel = path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else path.name
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    v: list[str] = []
    if path.stem in DRAW_MODULES:
        v += [f"{rel}:{ln} (a) 글자 크기 리터럴" for ln in size_literals(tree)]
        v += [f"{rel}:{ln} (b) 숫자 {val!r}" for ln, val in number_literals(tree)]
    v += [f"{rel}:{ln} (c) hex 색 {h}" for ln, h in hex_literals(tree)]
    v += [f"{rel}:{ln} (d) import {n}" for ln, n in bad_imports(tree)]
    return v


class SketchNoLiteralsTest(unittest.TestCase):
    def test_package_exists(self) -> None:
        self.assertTrue((REPO / SKETCH_ROOT / "__init__.py").is_file())
        self.assertTrue(FORMULA_MODULES.isdisjoint(DRAW_MODULES))

    def test_sketch_package_clean(self) -> None:
        violations = [x for p in iter_py(SKETCH_ROOT) for x in scan(p)]
        self.assertEqual(violations, [], "스케치 화면 수치는 rules sketch:, 색은 토큰, import 는 본편 경로 밖(D128·D130):\n"
                         + "\n".join(violations))

    def test_checker_catches_violations(self) -> None:
        """합성 소스 — 네 가지 위반이 각각 잡혀야 한다(검사기가 살아 있음)."""
        import tempfile

        src = (
            "from engine.render import render_video\n"
            "import orchestrator.config\n"
            "def f(ctx):\n"
            "    text(ctx, 's', 0, 0, 13, 'sansb')\n"
            "    tw(ctx, 's', size=11.5)\n"
            "    ctx.set_line_width(1.6)\n"
            "    return '#ff5566'\n"
        )
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "draw.py"
            p.write_text(src, encoding="utf-8")
            got = scan(p)
        kinds = {x.split(" ")[1] for x in got}
        self.assertEqual(kinds, {"(a)", "(b)", "(c)", "(d)"}, got)
        self.assertEqual(sum(1 for x in got if "(a)" in x), 2)
        self.assertEqual(sum(1 for x in got if "(d)" in x), 2)


if __name__ == "__main__":
    unittest.main()
