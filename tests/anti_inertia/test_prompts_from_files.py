"""test_prompts_from_files — 워커 프롬프트는 파일에서 온다 (docs/handoff/15 P3, 19 부록 B).

(1) `workers/*.py` 에 `system_prompt` 문자열 상수가 없다. (2) docstring 이 아닌 200자 이상 문자열
리터럴이 없다(암시적 연결 포함 — AST 에서 한 Constant). (3) `BaseLLMWorker` 하위 클래스마다
`prompt_name` 이 있고 `prompts/{name}.md` 가 존재한다.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import unittest

from tests.anti_inertia._ast_util import REPO, code_strings, iter_py, parse
from workers.base_llm_worker import BaseLLMWorker

MAX_LITERAL_CHARS = 200


class PromptsFromFilesTest(unittest.TestCase):
    def test_no_prompt_constants(self) -> None:
        violations: list[str] = []
        for path in iter_py("workers"):
            rel = path.relative_to(REPO).as_posix()
            tree = parse(path)
            for node in ast.walk(tree):
                target = None
                if isinstance(node, ast.AnnAssign):
                    target, value = node.target, node.value
                elif isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target, value = node.targets[0], node.value
                name = getattr(target, "id", None) or getattr(target, "attr", None)
                if name and "system_prompt" in name.lower() and isinstance(value, ast.Constant) \
                        and isinstance(value.value, str):
                    violations.append(f"{rel}:{node.lineno} {name} 문자열 상수")
            for const in code_strings(tree):
                if len(const.value) >= MAX_LITERAL_CHARS:
                    violations.append(f"{rel}:{const.lineno} {len(const.value)}자 문자열 리터럴")
        self.assertEqual(violations, [], "프롬프트 코드 상수:\n" + "\n".join(violations))

    def test_every_llm_worker_has_prompt_file(self) -> None:
        missing: list[str] = []
        for path in iter_py("workers"):
            mod = importlib.import_module("workers." + path.stem)
            for _, cls in inspect.getmembers(mod, inspect.isclass):
                if not issubclass(cls, BaseLLMWorker) or cls is BaseLLMWorker or inspect.isabstract(cls):
                    continue
                if cls.__module__ != mod.__name__:
                    continue
                name = cls.prompt_name
                if not name:
                    missing.append(f"{cls.__name__}: prompt_name 없음")
                elif not (REPO / "prompts" / f"{name}.md").exists():
                    missing.append(f"{cls.__name__}: prompts/{name}.md 없음")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
