"""test_no_code_direction — 연출은 선언형 direction.yaml 뿐, 코드 실행 경로 없음 (v3.1.0, D-0047 §0-1·작업 4, 15 P2).

(a) projects/ 아래 direction.py 가 없다 (a2) projects/ 아래 .py 가 하나도 없다 — 화면 스케치도 패키지 CLI + spec(D-0145 §9) (b) 저장소 코드(테스트 제외)에 동적 모듈 실행(exec_module·spec_from_file_location·exec·eval) 호출이 없다.
"""

from __future__ import annotations

import ast
import unittest

from tests.anti_inertia._ast_util import REPO, iter_py

BANNED_ATTRS = {"exec_module", "spec_from_file_location"}
BANNED_NAMES = {"exec", "eval"}


class NoCodeDirectionTest(unittest.TestCase):
    def test_no_direction_py(self) -> None:
        self.assertEqual(sorted(str(p.relative_to(REPO)) for p in (REPO / "projects").rglob("direction.py")), [])

    def test_no_py_in_projects(self) -> None:
        self.assertEqual(sorted(p.relative_to(REPO).as_posix() for p in (REPO / "projects").rglob("*.py")), [])

    def test_no_dynamic_module_execution(self) -> None:
        hits: list[str] = []
        for p in iter_py():
            rel = p.relative_to(REPO).as_posix()
            if rel.startswith("tests/"):
                continue
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call):
                    f = node.func
                    if (isinstance(f, ast.Attribute) and f.attr in BANNED_ATTRS) or (isinstance(f, ast.Name) and f.id in BANNED_NAMES):
                        hits.append(f"{rel}:{node.lineno}")
        self.assertEqual(hits, [], "코드 실행 경로가 남았다:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
