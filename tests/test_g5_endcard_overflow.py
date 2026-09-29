"""G5(v4.5.0, back_and_forth D-0098 §2·§4, D-0099 A) — 엔딩 카드 크레딧 넘침 = 오류, 같은 크레딧 줄 한 번만.

- 두 열의 마지막 기준선 > 하단 구분선(H−44) − rules end_card.bottom_margin → draw_endcard 가 EndCardOverflowError,
  checks offscreen `[endcard-overflow]`(같은 함수). 조용한 넘침 금지(15 P6).
- 실프로젝트 4편(fed_policy·hormuz·랫클리프·데모) 넘침 0. fed_policy 는 D-0099 A 배치(왼쪽 415, 오른쪽 423) → v4.6.0 D-0102 3-A 배치(음악 줄 추가, 왼쪽 418, 오른쪽 420).
- credit_sections: 같은 (문구, 라이선스) 행은 한 번만(fed_policy 자료 절 4줄 → 3줄), 다른 세 편은 합칠 줄이 없어 무변경.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

import cairo

from engine import fullcards
from engine.style import END_CARD, H_OUT

REPO = Path(__file__).resolve().parent.parent
LIMIT = H_OUT - 44 - END_CARD.bottom_margin
PROJECTS = ("fed_policy_2026", "hormuz_korea", "ratcliffe2026", "fed_timeline_demo")


def _fake_secs(n: int) -> list[tuple[str, list[tuple[str, str]]]]:
    return [(f"절{i}", [("항목", "라이선스")] * 3) for i in range(n)]


def _project(name: str):  # noqa: ANN202
    proj = REPO / "projects" / name
    missing = [p for p in ("plan.json", "tts") if not (proj / p).exists()]
    if missing:
        raise RuntimeError(f"{name} 자산 없음 {missing} — artifacts 복원(docs/handoff/reports/phaseG4/run_log.md §0)")
    from engine.project import load_project  # noqa: PLC0415

    return load_project(proj)


class RuleTest(unittest.TestCase):
    def test_bottom_margin_rule(self) -> None:
        self.assertEqual(END_CARD.bottom_margin, 8)
        self.assertEqual(LIMIT, 428)


class OverflowTest(unittest.TestCase):
    def test_fake_overflow_raises(self) -> None:
        secs = _fake_secs(6)                      # 한 열에 절 6개(각 제목 15 + 23×3 + 간격 10) → 한도 초과
        place = [1] * len(secs)
        over = fullcards.endcard_overflow(secs, place)
        self.assertEqual(len(over), 1)
        self.assertTrue(over[0].startswith("[endcard-overflow] 크레딧 오른쪽 열"))
        R = NS(tb=NS(plan=NS(date="2026.09.29"), order=[]), credits=NS(sections=[NS(column=c) for c in place]),  # noqa: N806
               assets=NS(rights={}, media={}), cache={})
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480))
        with mock.patch.object(fullcards, "credit_sections", return_value=secs):
            with self.assertRaises(fullcards.EndCardOverflowError):
                fullcards.draw_endcard(ctx, R, 5.0, NS(t0=0.0), 1.0)

    def test_layout_last_baseline(self) -> None:
        secs = [("가", [("a", "l"), ("b", "")]), ("나", [("c", "l")])]
        placed, last = fullcards.endcard_layout(secs, [0, 1])
        self.assertEqual([p[3] for p in placed], [158, 158])           # 절 제목 기준선
        self.assertEqual([r[2] for r in placed[0][4]], [173, 196])     # 항목 기준선: 제목 + 15, 라이선스 있으면 + 23
        self.assertEqual(last, [196, 184])                             # 라이선스 없는 마지막 항목 = 그 줄, 있으면 + 11

    def test_real_projects_no_overflow(self) -> None:
        from engine.checks import check_endcard_overflow  # noqa: PLC0415

        lasts = {}
        for name in PROJECTS:
            P = _project(name)  # noqa: N806
            secs = fullcards.project_credit_sections(P.R)
            place = [s.column for s in P.R.credits.sections]
            self.assertEqual(fullcards.endcard_overflow(secs, place), [], name)
            self.assertEqual(check_endcard_overflow(P), [], name)
            lasts[name] = fullcards.endcard_layout(secs, place)[1]
        self.assertEqual(lasts["fed_policy_2026"], [418, 420])          # v4.6.0 D-0102 3-A 실측(D-0099 A 415·423 에서 음악 줄 추가)


class UniqueLineTest(unittest.TestCase):
    def test_same_line_once(self) -> None:
        from engine.credits import _unique  # noqa: PLC0415

        rows = [("FRED", "PD · 9월"), ("BLS", "PD · 8월"), ("FRED", "PD · 9월"), ("FRED", "PD · 8월")]
        self.assertEqual(_unique(rows), [("FRED", "PD · 9월"), ("BLS", "PD · 8월"), ("FRED", "PD · 8월")])

    def test_real_projects(self) -> None:
        from engine.credits import _credit_sections, credit_sections  # noqa: PLC0415

        for name in PROJECTS:
            P = _project(name)  # noqa: N806
            R = P.R  # noqa: N806
            args = (R.credits, R.assets.rights, R.assets.media, R.cache.get("credit_refs"), R.cache.get("cited_sources"),
                    R.cache.get("series_records"))
            raw, merged = _credit_sections(*args), credit_sections(*args)
            if name == "fed_policy_2026":
                raw_d, merged_d = dict(raw), dict(merged)
                self.assertEqual((len(raw_d["자료"]), len(merged_d["자료"])), (4, 3))
                self.assertEqual(len(set(merged_d["자료"])), 3)
                self.assertIn("사진 · 기사 카드 · 국기", merged_d)   # v4.6.0 D-0102 3-A(D-0099 A "사진 · 기사 카드" + 국기)
            else:
                self.assertEqual(raw, merged, name)   # 합칠 줄 없음 → 무변경


if __name__ == "__main__":
    unittest.main()
