"""관성 방지 테스트 공용 AST 헬퍼 (v2.0.0, docs/handoff/19 부록 B)."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# 검사에서 빼는 경로 — 핸드오프 참고 코드(동작 원본·이력)와 VCS·캐시
EXCLUDED_PARTS: tuple[str, ...] = (".git", "__pycache__", ".venv", "node_modules")
EXCLUDED_PREFIXES: tuple[str, ...] = ("docs/handoff/",)


def iter_py(*roots: str) -> Iterator[Path]:
    bases = [REPO / r for r in roots] if roots else [REPO]
    for base in bases:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.py")):
            rel = p.relative_to(REPO).as_posix()
            if any(part in EXCLUDED_PARTS for part in p.parts):
                continue
            if rel.startswith(EXCLUDED_PREFIXES):
                continue
            yield p


def docstring_nodes(tree: ast.AST) -> set[int]:
    """모듈·클래스·함수 docstring Constant 노드의 id 집합 (문서는 코드 참조가 아니다)."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def code_strings(tree: ast.AST) -> Iterator[ast.Constant]:
    """docstring 을 뺀 문자열 리터럴."""
    skip = docstring_nodes(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            yield node


def parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
