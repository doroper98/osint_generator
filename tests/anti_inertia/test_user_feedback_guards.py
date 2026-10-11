"""사용자 의견 원장 장치 강제(v5.22.0, back_and_forth D-0200 — "내가 코멘트 한 사항들은 모두 기록되고 재발이 되면 안돼").

- 원장(rules/user_feedback.yaml)이 모델을 통과하고, 문서 표가 생성 결과와 같다(값 이중 관리 금지).
- 모든 장치가 실제로 있다: check = engine.checks HARD·WARN(스케치 SK-* 는 sketch CHECK_IDS), test = 수집되는 테스트 함수,
  rule = 규칙 파일 경로, code = import 되는 함수. 없는 장치 = 실패.
- 한 트랙에만 걸린 장치 금지(UF-02 교훈): 스케치 SK-* 장치만 있는 항목은 본 엔진 check 장치도 있어야 한다.
"""

from __future__ import annotations

import ast
import importlib
import unittest

import yaml

from engine import checks
from rules import RULES_PATH, load_user_feedback
from sketch.common.checks import CHECK_IDS
from tests.anti_inertia._ast_util import REPO
from tools.feedback_ledger import DOC, render_doc


def _test_exists(ref: str) -> bool:
    path, *names = ref.split("::")
    f = REPO / path
    if not f.exists() or not names:
        return False
    tree = ast.parse(f.read_text(encoding="utf-8"))
    scope: list[ast.stmt] = tree.body
    for n in names:
        hit = next((x for x in scope if isinstance(x, (ast.ClassDef, ast.FunctionDef)) and x.name == n), None)
        if hit is None:
            return False
        scope = hit.body if isinstance(hit, ast.ClassDef) else []
    return names[-1].startswith("test")


def _rule_exists(ref: str, raw: dict) -> bool:
    cur: object = raw
    for k in ref.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return False
        cur = cur[k]
    return True


def _doc_exists(ref: str) -> bool:
    """v5.22.4 D-0205 — 프로세스 항목 장치: "경로#문구" — 그 문서에 그 문구가 그대로 있다."""
    path, _, frag = ref.partition("#")
    f = REPO / path
    return bool(frag) and f.exists() and frag in f.read_text(encoding="utf-8")


def _code_exists(ref: str) -> bool:
    mod, _, name = ref.rpartition(".")
    try:
        return callable(getattr(importlib.import_module(mod), name, None))
    except ImportError:
        return False


class UserFeedbackGuardsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.led = load_user_feedback()
        self.raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))

    def test_doc_table_is_generated(self) -> None:
        cur = DOC.read_text(encoding="utf-8")
        self.assertEqual(render_doc(cur, self.led), cur, "python tools/feedback_ledger.py --write")

    def test_every_guard_exists(self) -> None:
        engine_ids = set(checks.HARD) | set(checks.WARN)
        bad = []
        for e in self.led.entries:
            for g in e.guards:
                ok = {"check": lambda r: r in engine_ids or r in CHECK_IDS,
                      "test": _test_exists,
                      "rule": lambda r: _rule_exists(r, self.raw),
                      "code": _code_exists,
                      "doc": _doc_exists}[g.kind](g.ref)
                if not ok:
                    bad.append(f"{e.id} {g.kind}:{g.ref}")
        self.assertEqual(bad, [], "원장 장치가 저장소에 없다")

    def test_no_single_track_guard(self) -> None:
        """스케치 검사만 걸린 항목 = 본편 경로 미보호(UF-02 재발 원인)."""
        engine_ids = set(checks.HARD) | set(checks.WARN)
        bad = [e.id for e in self.led.entries
               if any(g.kind == "check" and g.ref in CHECK_IDS for g in e.guards)
               and not any(g.kind == "check" and g.ref in engine_ids for g in e.guards)
               and e.project not in ("sketch",) and not e.category.startswith("스케치")]
        self.assertEqual(bad, [])

    def test_doc_guards_only_for_process_items(self) -> None:
        """doc 장치는 프로세스 항목(분류에 '작업 순서'·'전달')만, 그리고 doc 하나만으로 보호하지 않는 항목은 다른 장치도 둔다."""
        bad = [e.id for e in self.led.entries if any(g.kind == "doc" for g in e.guards)
               and not any(w in e.category for w in ("작업 순서", "전달", "영상 문법"))]
        self.assertEqual(bad, [])

    def test_no_open_entries(self) -> None:
        """D-0205 §3 — 소급 open 15건을 닫았다. 새 의견은 장치와 함께 들어온다(게이트 ② 정상 통과)."""
        self.assertEqual([e.id for e in self.led.open_entries()], [])

    def test_gulf_round_all_guarded(self) -> None:
        """D-0200 §5 — gulf 재렌더 전 UF-01~12 전부 보호."""
        first = {e.id: e for e in self.led.entries if int(e.id[3:]) <= 12}
        self.assertEqual(sorted(first), [f"UF-{i:02d}" for i in range(1, 13)])
        self.assertEqual([i for i, e in first.items() if e.status != "guarded"], [])


if __name__ == "__main__":
    unittest.main()
