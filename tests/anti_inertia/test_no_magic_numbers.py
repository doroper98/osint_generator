"""test_no_magic_numbers — 데이터화된 패널 모듈에 기하·타이밍 리터럴 금지 (D-0032 작업 2·6, 15 P3).

08 §3 정돈된 관계선 규칙의 수치는 `rules/video_rules.yaml panels.*` 한 곳에만 있다. 모듈이 숫자를 다시 적으면
규칙을 바꿔도 영상이 그대로다(agents_reviewer 패턴 C). 허용: 0·1·2·3(인덱스·반분·RGB 성분 수).
대상 모듈은 Phase 6 에서 데이터화한 것부터 늘려 간다.
"""

from __future__ import annotations

import ast
import unittest

from tests.anti_inertia._ast_util import REPO, parse

DATA_DRIVEN_MODULES: dict[str, frozenset[float]] = {   # 모듈 → 추가 허용(달력 상수 등)
    "engine/panels/relation.py": frozenset(),
    "engine/panels/timeline.py": frozenset({12}),   # 12월 → 다음 해 1월
    "engine/reserved.py": frozenset({0.5}),         # 대각 방향 단위벡터 √0.5
    "engine/panels/dots.py": frozenset(),
    "engine/panels/gantt.py": frozenset(),
    "engine/panels/dual_line.py": frozenset(),
    "engine/panels/fork.py": frozenset(),
    "engine/panels/checklist.py": frozenset(),
    "engine/panels/network.py": frozenset(),
}
ALLOWED_NUMBERS: frozenset[float] = frozenset({0, 1, 2, 3})


class NoMagicNumbersTest(unittest.TestCase):
    def test_no_numeric_literals(self) -> None:
        violations: list[str] = []
        for rel, extra in DATA_DRIVEN_MODULES.items():
            for node in ast.walk(parse(REPO / rel)):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                        and not isinstance(node.value, bool) and node.value not in ALLOWED_NUMBERS | extra:
                    violations.append(f"{rel}:{node.lineno} {node.value!r}")
        self.assertEqual(violations, [], "규칙 값은 rules/video_rules.yaml panels.* 에:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
