"""GOAL G3 v2 — 합격 기준 표의 "검증 방법" 열이 실제로 있는 것을 가리킨다 (v4.0.0, back_and_forth D-0072 작업 2).

표 형식: `| # | 기준 | 검증 방법 |`. 검증 방법 칸의 백틱 토큰은 네 종류다.
- `tests/…py::test_이름` — 그 파일에 `def test_이름` 이 있다. `tests/폴더/` — 폴더가 있고 test_*.py 가 있다.
- `checks:항목` — `engine.checks.HARD ∪ WARN` 에 있다(프리뷰 결정적 검사).
- `gate:…` — 사람 판정(승인 게이트). 이름은 `schemas.models.ProjectState` 의 게이트 상태여야 한다.
- `pending:…` — 아직 검사가 없다(예정 Phase). 개수를 고정해 몰래 늘지 않게 한다.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOAL = (REPO / "GOAL.md").read_text(encoding="utf-8")
TOKEN = re.compile(r"`([^`]+)`")
KINDS = ("tests/", "checks:", "gate:", "pending:")
GATE_COUNT = 2          # 6번(루프 상한 뒤 게이트 ②), 17번(장르 확장 사람 판정)
PENDING_COUNT = 1       # 17번 무대 연속성 검사(G1~G4 Phase)


def g3_section() -> str:
    start = GOAL.index("## G3. 합격 기준 v2")
    return GOAL[start:GOAL.index("### G3-legacy", start)]


def g3_rows() -> dict[int, list[str]]:
    rows: dict[int, list[str]] = {}
    for line in g3_section().splitlines():
        m = re.match(r"^\| (\d+) \| (.+) \| (.+) \|$", line)
        if m:
            rows[int(m.group(1))] = [t for t in TOKEN.findall(m.group(3)) if t.startswith(KINDS)]
    return rows


class G3TableTest(unittest.TestCase):
    def test_seventeen_rows_in_order(self) -> None:
        self.assertEqual(sorted(g3_rows()), list(range(1, 18)))

    def test_every_row_has_a_method(self) -> None:
        for n, toks in g3_rows().items():
            self.assertTrue(toks, f"G3-{n} 검증 방법 없음")

    def test_major_rule_kept(self) -> None:
        self.assertIn("메이저 버전", g3_section())

    def test_legacy_34_preserved(self) -> None:
        legacy = GOAL[GOAL.index("### G3-legacy"):GOAL.index("## G4.")]
        self.assertIn("[legacy v1 — deprecated v4.0.0]", legacy)
        for n in range(1, 35):
            self.assertIn(f"\n{n}. ", legacy, f"legacy {n} 없음")


class G3MethodsExistTest(unittest.TestCase):
    def test_test_ids_exist(self) -> None:
        missing = []
        for n, toks in g3_rows().items():
            for t in toks:
                if not t.startswith("tests/"):
                    continue
                path, _, name = t.partition("::")
                p = REPO / path
                if path.endswith("/"):
                    if not (p.is_dir() and list(p.glob("test_*.py"))):
                        missing.append((n, t))
                elif not p.is_file() or (name and f"def {name}(" not in p.read_text(encoding="utf-8")):
                    missing.append((n, t))
        self.assertEqual(missing, [])

    def test_checks_items_exist(self) -> None:
        from engine.checks import HARD, WARN  # noqa: PLC0415
        bad = [(n, t) for n, toks in g3_rows().items() for t in toks
               if t.startswith("checks:") and t.split(":", 1)[1] not in HARD + WARN]
        self.assertEqual(bad, [])

    def test_gates_are_states(self) -> None:
        from schemas.models import ProjectState  # noqa: PLC0415
        gates = [t.split(":", 1)[1] for toks in g3_rows().values() for t in toks if t.startswith("gate:")]
        self.assertEqual(len(gates), GATE_COUNT)
        for g in gates:
            self.assertIn(g, ProjectState.__members__)

    def test_pending_count_fixed(self) -> None:
        pend = [t for toks in g3_rows().values() for t in toks if t.startswith("pending:")]
        self.assertEqual(len(pend), PENDING_COUNT, pend)

    def test_rule_keys_exist(self) -> None:
        """본문이 인용한 `rules:키`·`config:키` 가 실제 파일에 있다(값은 복사하지 않고 키로 가리킨다)."""
        from tests._doc_keys import missing_keys  # noqa: PLC0415
        self.assertEqual(missing_keys(g3_section()), [])


if __name__ == "__main__":
    unittest.main()
