"""G5(v4.5.0, 사용자 결정 D85, C9 개정, back_and_forth D-0096) — 검증 라벨은 영상 본문에 그리지 않고 엔딩 카드 마지막 줄 한 줄로만.

- 규칙: 죽은 키 0(label_style·prov_tag.gap_px·claim_color), 새 키 end_card.notice_unverified(가장 작은 글씨, `{n}`).
- 렌더: 엔딩 카드 n>0 → 맨 아래 한 줄, n=0 → 없음. 라벨 문구가 text() 로 가지 않는다(자막·패널·post·실프로젝트 프리뷰).
- 검사: checks forbidden `[label-in-body]`. 기록(script_labels·claims)은 그대로.
- 코드에 라벨 문구·안내 문구 리터럴 0(규칙 SSOT, 15 P3).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

import cairo
import yaml

from engine import typography
from engine.style import END_CARD, H_OUT
from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
RULES = load_rules()
LABELS = [v for v in RULES.script_schema.labels.values() if v]
NOTICE = RULES.layout_480p.end_card.notice_unverified


def _log(fn) -> list[tuple[float, str | None, str]]:  # noqa: ANN001
    """fn() 이 text() 로 그린 (크기, 역할, 문자열)."""
    typography.GLYPH_LOG = []
    try:
        fn()
        return list(typography.GLYPH_LOG)
    finally:
        typography.GLYPH_LOG = None


def _endcard_R(labels: dict[str, str], order: list[str]) -> NS:  # noqa: N802
    plan = NS(date="2026.09.29")
    return NS(tb=NS(plan=plan, order=order), credits=NS(sections=[]),
              assets=NS(rights={}, media={}), cache={"sentence_labels": labels})


def _draw_endcard(R: NS) -> list[tuple[float, str | None, str]]:  # noqa: N803
    from engine import fullcards  # noqa: PLC0415

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480))
    with mock.patch.object(fullcards, "credit_sections", return_value=[]):
        return _log(lambda: fullcards.draw_endcard(ctx, R, 5.0, NS(t0=0.0, t1=11.0), 1.0))   # t1: v4.7.0 hold_black_after(카드 끝 시각)


class RulesTest(unittest.TestCase):
    def test_dead_label_keys_removed(self) -> None:
        raw = yaml.safe_load((REPO / "rules" / "video_rules.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("label_style", raw["layout_480p"]["subtitle"])
        self.assertFalse({"gap_px", "claim_color"} & set(raw["panels"]["prov_tag"]))

    def test_notice_is_smallest_end_card_text(self) -> None:
        self.assertIn("{n}", NOTICE.template)
        self.assertEqual(NOTICE.size, END_CARD.license_size)
        self.assertLessEqual(NOTICE.size, min(END_CARD.item_size, END_CARD.license_size))
        self.assertFalse([lab for lab in LABELS if lab in NOTICE.template])   # 안내 줄에도 라벨 문구는 없다

    def test_label_table_kept_for_records(self) -> None:
        self.assertEqual(RULES.script_schema.labels["unverified"], "<미검증>")
        self.assertEqual(RULES.script_schema.labels["disputed"], "<논쟁>")


class EndCardNoticeTest(unittest.TestCase):
    def test_count_only_sentences_in_video(self) -> None:
        from engine.fullcards import unverified_notice  # noqa: PLC0415

        R = _endcard_R({"a_0": "<미검증>", "a_1": "<논쟁>", "cut_0": "<미검증>"}, ["a_0", "a_1", "a_2"])  # noqa: N806
        self.assertEqual(unverified_notice(R), NOTICE.template.replace("{n}", "2"))   # 게이트에서 빠진 cut_0 은 세지 않는다
        self.assertIsNone(unverified_notice(_endcard_R({}, ["a_0"])))

    def test_one_line_at_bottom_when_n_positive(self) -> None:
        drawn = _draw_endcard(_endcard_R({"a_0": "<미검증>"}, ["a_0", "a_1"]))
        want = NOTICE.template.replace("{n}", "1")
        hits = [d for d in drawn if d[2] == want]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][:2], (NOTICE.size, "end_card"))
        self.assertEqual(min(d[0] for d in drawn), NOTICE.size)   # 가장 작은 글씨
        self.assertFalse([d for d in drawn if any(lab in d[2] for lab in LABELS)])

    def test_no_line_when_n_zero(self) -> None:
        with_n = _draw_endcard(_endcard_R({"a_0": "<미검증>"}, ["a_0"]))
        without = _draw_endcard(_endcard_R({}, ["a_0"]))
        self.assertEqual(len(with_n), len(without) + 1)
        self.assertFalse([d for d in without if "{n}" in NOTICE.template and d[2].startswith(NOTICE.template.split("{n}")[0])])

    def test_notice_is_last_line_below_date(self) -> None:
        """맨 마지막 줄 — 기준선이 날짜·안내 줄(H−26)보다 아래, 화면 안."""
        from engine import fullcards  # noqa: PLC0415

        ys: list[float] = []
        real = fullcards.text

        def spy(ctx, s, x, y, *a, **k):  # noqa: ANN001, ANN002, ANN003, ANN202
            ys.append((y, s))
            return real(ctx, s, x, y, *a, **k)

        with mock.patch.object(fullcards, "text", spy):
            _draw_endcard(_endcard_R({"a_0": "<논쟁>"}, ["a_0"]))
        last_y, last_s = max(ys)
        self.assertEqual(last_s, NOTICE.template.replace("{n}", "1"))
        self.assertLess(last_y, H_OUT)
        self.assertGreater(last_y, H_OUT - 26)


class BodyDrawsNoLabelTest(unittest.TestCase):
    def test_checks_flag_label_in_body(self) -> None:
        from engine.checks import check_label_glyphs  # noqa: PLC0415

        self.assertEqual(check_label_glyphs([("c1", 19.0, None, "평범한 자막"), ("c9", NOTICE.size, "end_card",
                                                                                 NOTICE.template.replace("{n}", "3"))]), [])
        bad = check_label_glyphs([("c2", 13.7, None, "<미검증>"), ("c3", 10.0, None, "<논쟁> 무엇")])
        self.assertEqual(len(bad), 2)
        self.assertTrue(all(b.startswith("[label-in-body]") for b in bad))

    def test_no_label_literals_in_engine_code(self) -> None:
        """라벨 문구·안내 문구는 규칙에서만(15 P3) — 엔진 코드 문자열 리터럴 0(주석·docstring 제외 판정은 따옴표 기준)."""
        needles = [f'"{lab}"' for lab in LABELS] + [f"'{lab}'" for lab in LABELS] + [NOTICE.template.split("{n}")[0].strip()]
        hits = [(p.relative_to(REPO).as_posix(), n) for p in (REPO / "engine").rglob("*.py")
                for n in needles if n in p.read_text(encoding="utf-8")]
        self.assertEqual(hits, [])

    def test_post_card_and_panel_tag_have_no_label(self) -> None:
        from engine.panels.base import tag_boxes  # noqa: PLC0415
        from engine.registry import validate_events  # noqa: PLC0415

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        for st in ("unverified", "disputed"):
            ev = yaml.safe_load((REPO / "prompts" / "examples" / "panels" / "gantt.yaml").read_text(encoding="utf-8"))["event"]
            ev["provenance"] = {"verification": "verified", "sources": ["s1"], "claim_status": st}
            e = validate_events([ev])[0]
            self.assertEqual(tag_boxes(ctx, e), [])   # verified + 출처 = 추정 태그도 없음, 검증 라벨 상자 없음


PROJECTS = {"fed_policy_2026": True, "ratcliffe2026": True, "hormuz_korea": False}


class ProjectPreviewNoLabelTest(unittest.TestCase):
    """실프로젝트 — 라벨 문장이 있는 영상(fed_policy·랫클리프)도 본문 text() 에 라벨 0, 엔딩 카드 안내 줄은 n>0 일 때만."""

    def _project(self, name: str):  # noqa: ANN202
        proj = REPO / "projects" / name
        missing = [p for p in ("plan.json", "tts") if not (proj / p).exists()]
        if missing:
            raise RuntimeError(f"{name} 자산 없음 {missing} — artifacts 복원(docs/handoff/reports/phaseG4/run_log.md §0)")
        from engine.project import load_project  # noqa: PLC0415

        return load_project(proj)

    def test_sentence_label_counts(self) -> None:
        from engine.project import sentence_labels  # noqa: PLC0415

        for name, has in PROJECTS.items():
            self.assertEqual(bool(sentence_labels(REPO / "projects" / name)), has, name)

    def test_body_frames_and_end_card(self) -> None:
        from engine.style import FPS  # noqa: PLC0415
        from engine.render import auto_preview_times, render_frame  # noqa: PLC0415

        for name, has in PROJECTS.items():
            P = self._project(name)  # noqa: N806
            labs = P.R.cache.get("sentence_labels") or {}
            times = [P.R.tb.sent[sid].t0 + 0.5 for sid in P.R.tb.order if sid in labs][:4]   # 라벨 문장 자막 구간
            times += auto_preview_times(P)[-1:]                                             # 엔딩 카드
            drawn: list[str] = []
            for t in times:
                drawn += [s for _, _, s in _log(lambda t=t: render_frame(P, min(P.n_frames - 1, int(t * FPS))))]
            self.assertFalse([s for s in drawn if any(lab in s for lab in LABELS)], name)
            notice = [s for s in drawn if s.startswith(NOTICE.template.split("{n}")[0])]
            self.assertEqual(len(notice), 1 if has else 0, name)
            if has:
                self.assertEqual(notice[0], NOTICE.template.replace("{n}", str(sum(1 for s in P.R.tb.order if labs.get(s)))))


if __name__ == "__main__":
    unittest.main()
