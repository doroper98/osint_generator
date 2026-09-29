"""test_no_font_literals — 화면 글자 크기 리터럴 금지 (v4.8.0, back_and_forth D-0101 §1·§2·§3, 15 P3).

`text(ctx, s, x, y, size, …)`·`tw(ctx, s, size, …)`·`wrap(ctx, s, maxw, size, …)` 의 size 가 숫자 리터럴이면
규칙(`rules/video_rules.yaml`)을 바꿔도 화면 글자가 그대로다(D-0101 배경 — 기사 카드 헤드라인 13.5 < 자막 19).
대상 모듈은 G7 에서 규칙화한 것부터 늘려 간다.
"""

from __future__ import annotations

import ast
import unittest

from tests.anti_inertia._ast_util import REPO, parse

SIZE_ARG: dict[str, int] = {"text": 4, "tw": 2, "wrap": 3}
MODULES: tuple[str, ...] = (
    "engine/layers/badges.py",      # v4.8.0 D-0101 §1 — 이름표 label_solo·label_group·label_side
    "engine/layers/media.py",       # v4.8.0 D-0101 §2·§3 — article_card·media_caption
    "engine/layers/markers.py",     # v4.8.0 D-0101 §3 — marker
    "engine/layers/routes.py",      # v4.8.0 D-0101 §3 — route_label
    "engine/cards.py",              # v4.8.0 D-0101 §3 — card.cap_size
    "engine/panels/precedent.py",   # v4.8.0 D-0101 §3 — panels.precedent
    "engine/panels/versus.py",      # v4.8.0 D-0101 §3 — panels.versus
)


def font_literals(rel: str) -> list[str]:
    out: list[str] = []
    for node in ast.walk(parse(REPO / rel)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in SIZE_ARG:
            i = SIZE_ARG[node.func.id]
            if len(node.args) > i and isinstance(node.args[i], ast.Constant):
                out.append(f"{rel}:{node.lineno} {node.func.id}(… {node.args[i].value!r} …)")
    return out


class NoFontLiteralsTest(unittest.TestCase):
    def test_no_font_size_literals(self) -> None:
        bad = [v for rel in MODULES for v in font_literals(rel)]
        self.assertEqual(bad, [], "글자 크기는 rules/video_rules.yaml 에:\n" + "\n".join(bad))

    def test_badge_default_radius_not_literal(self) -> None:
        """옛 `e.get("R") or 30` — 기본 R 은 rules badge.R_other·적응 크기(D-0101 §1 R_default 리터럴 삭제)."""
        src = (REPO / "engine/layers/badges.py").read_text(encoding="utf-8")
        self.assertNotIn('or 30', src)


if __name__ == "__main__":
    unittest.main()
