"""test_no_legacy_imports — 옛 영상 경로가 코드에 남아 있지 않다 (docs/handoff/15 P2, 19 부록 B).

저장소 `*.py`(docs/handoff/ 제외)를 AST로 읽어, import 와 docstring 을 뺀 문자열 리터럴에 옛 경로
이름이 없는지 본다. 보존 브랜치 이름 `archive/hyperframes-briefing` 은 안내 문구로 허용한다.
주석은 검사하지 않는다 — 이관 출처 표시(`# moved from ...`, 19 §5.3)는 코드 참조가 아니다(D12).
"""

from __future__ import annotations

import ast
import re
import unittest

import pytest

from tests.anti_inertia._ast_util import REPO, code_strings, iter_py, parse

LEGACY_NAMES: tuple[str, ...] = (
    "hyperframes", "remotion", "scene_builder", "scene_io", "render_io",
    "audio_service", "audio_io", "audio_demo", "subtitle_align",
)
ALLOWED_MENTION = "archive/hyperframes-briefing"
_TOKEN = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(LEGACY_NAMES) + r")(?![A-Za-z0-9])")


def find_violations() -> list[str]:
    out: list[str] = []
    for path in iter_py():
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith("tests/anti_inertia/"):
            continue  # 검사기 자신은 금지어 목록을 담는다
        tree = parse(path)
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""] + [a.name for a in node.names]
            for m in mods:
                if any(part in LEGACY_NAMES for part in m.split(".")):
                    out.append(f"{rel}:{node.lineno} import {m}")
        for const in code_strings(tree):
            text = const.value.replace(ALLOWED_MENTION, "")
            hit = _TOKEN.search(text)
            if hit:
                out.append(f"{rel}:{const.lineno} 문자열 {hit.group(0)!r}")
    return out


class NoLegacyImportsTest(unittest.TestCase):
    @pytest.mark.xfail(
        strict=True,
        reason="커밋 ②(레거시 삭제) 보류 — DECISIONS D13. 삭제 후 XPASS 가 실패로 잡히면 이 마커를 제거한다",
    )
    def test_no_legacy_references(self) -> None:
        violations = find_violations()
        self.assertEqual(violations, [], "옛 영상 경로 참조:\n" + "\n".join(violations))

    def test_legacy_dirs_absent_is_tracked(self) -> None:
        # 디렉터리 존재 자체는 19 §5.8 셸 검사가 본다. 여기서는 검사기 자체가 동작하는지만 확인.
        self.assertTrue(_TOKEN.search("from orchestrator.scene_builder import x"))
        self.assertIsNone(_TOKEN.search("archive/hyperframes-briefing".replace(ALLOWED_MENTION, "")))


if __name__ == "__main__":
    unittest.main()
