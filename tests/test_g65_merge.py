"""G6.5(v4.7.0, back_and_forth D-0104) — dmz_mine 브랜치 병합 뒤 반영한 결정(D2(a) 연출 문법 등)."""

from __future__ import annotations

import unittest

from rules import load_rules


class DirectionGrammarTest(unittest.TestCase):
    def test_director_prompts_carry_direction_grammar(self) -> None:
        """D2(a) — 발언 주체 인물 문장 → 초상 뱃지 또는 기사 카드(규칙 SSOT, 연출·수정 프롬프트 둘 다)."""
        from workers.prompt_loader import load_prompt  # noqa: PLC0415

        R = load_rules()  # noqa: N806
        self.assertTrue(any("발언 주체" in g for g in R.direction_grammar))
        for name in ("director", "revise_direction"):
            text = load_prompt(name, R)
            self.assertNotIn("{{RULES.direction_grammar}}", text)
            for g in R.direction_grammar:
                self.assertIn(g, text, name)


if __name__ == "__main__":
    unittest.main()


class ReopenTest(unittest.TestCase):
    """D4 — 렌더 이후 → direction 되돌림(사유 필수, manifest.reopens 에 사유·연출 판 번호)."""

    def setUp(self) -> None:
        from tests.test_gates_pipeline import _Proj  # noqa: PLC0415

        self.p = _Proj("setUp")
        self.p.setUp()

    def tearDown(self) -> None:
        self.p.tearDown()

    def _to_render(self) -> None:
        from orchestrator.project_manager import approve_gate  # noqa: PLC0415
        from schemas.models import ProjectState as S  # noqa: N817, PLC0415

        p = self.p
        p.to_gate1()
        p.m = approve_gate(p.m, "script_approval", by="t", cfg=p.cfg)
        p.to(S.ASSETS, S.DIRECTION, S.PREVIEW_QA, S.PREVIEW_APPROVAL)
        p.m = approve_gate(p.m, "preview_approval", by="t", cfg=p.cfg)

    def test_reopen_after_render_records_reason_and_version(self) -> None:
        from orchestrator.project_manager import load_manifest, reopen  # noqa: PLC0415

        self._to_render()
        (self.p.root / "p" / "direction.v3.yaml").write_text("{}", encoding="utf-8")
        (self.p.root / "p" / "direction.v12.yaml").write_text("{}", encoding="utf-8")
        m = reopen(self.p.m, "direction", by="user", reason="사고 지점 좌표 비공개로", cfg=self.p.cfg)
        self.assertEqual(m.current_state, "direction")
        r = load_manifest("p", self.p.cfg).reopens[-1]
        self.assertEqual((r.from_state, r.to_state, r.reason, r.direction_version), ("render", "direction", "사고 지점 좌표 비공개로", 12))

    def test_reopen_rules(self) -> None:
        from orchestrator.project_manager import reopen  # noqa: PLC0415

        self.p.to_gate1()
        with self.assertRaises(ValueError):   # 렌더 전(게이트 ①)에서는 안 된다 — 반려(reject) 길을 쓴다
            reopen(self.p.m, "direction", by="u", reason="x", cfg=self.p.cfg)
        self._to_render_from_gate1()
        with self.assertRaises(ValueError):   # 사유 필수
            reopen(self.p.m, "direction", by="u", reason="  ", cfg=self.p.cfg)
        with self.assertRaises(ValueError):   # direction 으로만
            reopen(self.p.m, "script_draft", by="u", reason="x", cfg=self.p.cfg)

    def _to_render_from_gate1(self) -> None:
        from orchestrator.project_manager import approve_gate  # noqa: PLC0415
        from schemas.models import ProjectState as S  # noqa: N817, PLC0415

        p = self.p
        p.m = approve_gate(p.m, "script_approval", by="t", cfg=p.cfg)
        p.to(S.ASSETS, S.DIRECTION, S.PREVIEW_QA, S.PREVIEW_APPROVAL)
        p.m = approve_gate(p.m, "preview_approval", by="t", cfg=p.cfg)
