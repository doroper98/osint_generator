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


class EndCardRollTest(unittest.TestCase):
    """D-0106 1-C — 넘치면 롤, 속도 상한 초과만 오류, 상한 안 롤은 warning·provenance 기록."""

    @staticmethod
    def _secs(n: int) -> list:
        return [(f"절{i}", [("항목", "라이선스")] * 3) for i in range(n)]

    def _draw(self, secs: list) -> None:
        from types import SimpleNamespace as NS  # noqa: PLC0415
        from unittest import mock  # noqa: PLC0415

        import cairo  # noqa: PLC0415

        from engine import fullcards  # noqa: PLC0415

        place = [1] * len(secs)
        R = NS(tb=NS(plan=NS(date="2026.09.29"), order=[]), credits=NS(sections=[NS(column=c) for c in place]),  # noqa: N806
               assets=NS(rights={}, media={}), cache={})
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480))
        with mock.patch.object(fullcards, "credit_sections", return_value=secs):
            for t in (1.0, 5.0, 10.9):
                fullcards.draw_endcard(ctx, R, t, NS(t0=0.0, t1=load_rules().layout_480p.end_card.dur_sec), 1.0)

    def test_roll_within_limit(self) -> None:
        from engine import fullcards  # noqa: PLC0415

        E = load_rules().layout_480p.end_card  # noqa: N806
        secs = self._secs(5)                                   # 오른쪽 열 약 200px 넘침
        place = [1] * len(secs)
        dist, v = fullcards.endcard_roll(secs, place)
        self.assertTrue(150 < dist < 300 and 0 < v <= E.scroll_max_px_per_sec, (dist, v))
        self.assertEqual(fullcards.endcard_overflow(secs, place), [])
        self.assertEqual(len(fullcards.endcard_roll_note(secs, place)), 1)
        self._draw(secs)                                       # 오류 없이 그린다

    def test_roll_over_limit_raises(self) -> None:
        from engine import fullcards  # noqa: PLC0415

        secs = self._secs(16)                                  # 약 1000px 넘침
        place = [1] * len(secs)
        self.assertGreater(fullcards.endcard_roll(secs, place)[0], 900)
        self.assertEqual(len(fullcards.endcard_overflow(secs, place)), 1)
        self.assertEqual(fullcards.endcard_roll_note(secs, place), [])
        with self.assertRaises(fullcards.EndCardOverflowError):
            self._draw(secs)

    def test_no_overflow_no_roll(self) -> None:
        from engine import fullcards  # noqa: PLC0415

        secs = self._secs(1)
        place = [1]
        self.assertEqual(fullcards.endcard_roll(secs, place), (0.0, 0.0))
        self.assertEqual(fullcards.endcard_roll_note(secs, place), [])


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
