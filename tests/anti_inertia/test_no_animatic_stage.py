"""콘티 판 단계·사용자 원고 승인 폐지(v7.4.0 사용자 결정 UF-914 "콘티 단계 없애. 그냥 바로 영상 제작으로 간다",
UF-915 "원고 승인도 없앤다") — 옛 게이트 ② 콘티 판 강제가 다시 들어오지 않게 한다(15 P2 — 플래그가 아니라 삭제).

- orchestrator/ 에 require_animatic · AnimaticMissingError 가 없다(게이트 ② 근거는 require_preview).
- WORKFLOWS.md W0 에 콘티 판 단계가 없고, 게이트 ① 에서 사용자 원고 승인을 기다리라고 하지 않는다.
렌더 모드(`engine.render --animatic`) 자체는 남아 있다(이 시험은 그것을 막지 않는다).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _w0() -> str:
    text = (REPO / "WORKFLOWS.md").read_text(encoding="utf-8")
    a = text.index("## W0.")
    b = text.index("### W0.1", a)   # W0.1 = 콘티 판 렌더 모드(선택 도구) 설명 — 단계 목록 밖
    return text[a:b]


class NoAnimaticStageTest(unittest.TestCase):
    def test_no_animatic_gate_symbols_in_orchestrator(self) -> None:
        bad = re.compile(r"\b(require_animatic|AnimaticMissingError|_require_animatic_packet)\b")
        hits = [f"{p.relative_to(REPO)}:{i}" for p in sorted((REPO / "orchestrator").rglob("*.py"))
                for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if bad.search(ln)]
        self.assertEqual(hits, [])
        import orchestrator.project_manager as pm

        self.assertFalse(hasattr(pm, "require_animatic"))
        self.assertFalse(hasattr(pm, "AnimaticMissingError"))
        self.assertTrue(callable(pm.require_preview))

    def test_w0_lists_no_animatic_step(self) -> None:
        w0 = _w0()
        self.assertNotIn("--animatic", w0)
        self.assertNotIn("animatic.mp4", w0)
        self.assertNotIn("require_animatic", w0)
        self.assertIn("콘티 판은 만들지 않는다", w0)
        self.assertIn("require_preview", w0)

    def test_w0_does_not_wait_for_user_script_approval(self) -> None:
        w0 = _w0()
        gate1 = next(ln for ln in w0.splitlines() if "게이트 ①(" in ln)
        self.assertIn("사용자에게 묻지 않", gate1)
        self.assertNotIn("자막 점검**을 요청", w0)
        self.assertNotIn("사용자 승인 →", w0)


if __name__ == "__main__":
    unittest.main()
