"""test_single_config — 모델명·주요 수치의 리터럴 재정의 금지 (docs/handoff/15 P3, 19 부록 B).

규칙 파일(`rules/video_rules.yaml`)·설정 파일(`config.yaml`)의 값을 코드가 다시 적으면 두 곳이 어긋나
"설정을 바꿨는데 런타임 무변화"(agents_reviewer 패턴 C)가 된다. 허용 목록만 값을 정의할 수 있다.
"""

from __future__ import annotations

import ast
import unittest

from orchestrator.config import load_config
from rules import load_rules
from tests.anti_inertia._ast_util import REPO, code_strings, iter_py, parse

SCANNED_ROOTS: tuple[str, ...] = ("workers", "orchestrator", "engine", "script", "audio")
ALLOWED: frozenset[str] = frozenset({"orchestrator/config.py", "engine/style.py"})
RESOLUTION_TUPLES: frozenset[tuple[int, int]] = frozenset({(854, 480), (1920, 1080), (1080, 1920)})
NUMERIC_NAMES: frozenset[str] = frozenset({"fps", "invoke_timeout_sec", "script_timeout_sec"})


def _forbidden_strings() -> dict[str, str]:
    cfg = load_config()
    rules = load_rules()
    out: dict[str, str] = {
        cfg.tts.eleven_model_default: "config.yaml tts.eleven_model_default",
        cfg.llm.model: "config.yaml llm.model",
        cfg.tts.edge_voice: "config.yaml tts.edge_voice",
    }
    for name, value in rules.colors.model_dump().items():
        if isinstance(value, str):
            out[value.lower()] = f"rules colors.{name}"
    return out


def _target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


class SingleConfigTest(unittest.TestCase):
    def test_no_literal_redefinition(self) -> None:
        forbidden = _forbidden_strings()
        violations: list[str] = []
        for path in iter_py(*SCANNED_ROOTS):
            rel = path.relative_to(REPO).as_posix()
            if rel in ALLOWED:
                continue
            tree = parse(path)
            for const in code_strings(tree):
                low = const.value.lower()
                for needle, origin in forbidden.items():
                    if needle.lower() in low:
                        violations.append(f"{rel}:{const.lineno} 문자열 {needle!r} ({origin})")
            for node in ast.walk(tree):
                if isinstance(node, ast.Tuple) and len(node.elts) == 2 and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, int) for e in node.elts
                ):
                    pair = (node.elts[0].value, node.elts[1].value)  # type: ignore[attr-defined]
                    if pair in RESOLUTION_TUPLES:
                        violations.append(f"{rel}:{node.lineno} 해상도 튜플 {pair}")
                targets: list[ast.AST] = []
                value: ast.AST | None = None
                if isinstance(node, ast.Assign):
                    targets, value = list(node.targets), node.value
                elif isinstance(node, ast.AnnAssign):
                    targets, value = [node.target], node.value
                elif isinstance(node, ast.keyword) and node.arg:
                    if node.arg in NUMERIC_NAMES and isinstance(node.value, ast.Constant) \
                            and isinstance(node.value.value, (int, float)):
                        violations.append(f"{rel}:{node.value.lineno} {node.arg}={node.value.value}")
                    continue
                for t in targets:
                    name = _target_name(t)
                    if name in NUMERIC_NAMES and isinstance(value, ast.Constant) \
                            and isinstance(value.value, (int, float)):
                        violations.append(f"{rel}:{node.lineno} {name} = {value.value}")
        self.assertEqual(violations, [], "규칙/설정 값의 리터럴 재정의:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
