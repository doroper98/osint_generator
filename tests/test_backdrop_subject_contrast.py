"""v7.4.0 감독 D621 ②③ — 배경 사진(backdrop) 피사체 대조(D616 ④)와 사진 배경 위 아일랜드 글자 대비 측정(D619).

② for(장면 주제)가 레지스트리 main_subject 에 없으면 hard — 콘티 판 v1 의 지하철·아파트 배경이 개관·쟁점 막에 깔린 사고(D616 ③).
③ 렌더 경로(backdrop_surface → draw_frame boxed)로 상자 안 바탕을 합성해 rules island.text_colors 대비 < qa_checks.map_contrast_text 면 hard.
   R-0618 상태(상자 없음) 재현 = 실패, 덮개(dim)를 거친 가장 밝은 사진(흰 면) + 상자 = 통과.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest import mock

import cairo

from engine import checks
from rules import load_rules

R = load_rules()


def _subject_P(for_: str | None) -> NS:  # noqa: N802
    a = NS(main_subject=["국회의사당"], background=["잔디밭", "하늘"])
    e = {"type": "backdrop", "img": "bud_assembly_ext_2014", "t0": 0.0, "t1": 30.0}
    if for_ is not None:
        e["for"] = for_
    return NS(R=NS(assets=NS(media_assets={"bud_assembly_ext_2014": a})), events=[e])


class BackdropSubjectTest(unittest.TestCase):
    def test_main_subject_passes(self) -> None:
        self.assertEqual(checks.check_backdrop_subject(_subject_P("국회의사당")), [])

    def test_background_only_fails(self) -> None:
        out = checks.check_backdrop_subject(_subject_P("잔디밭"))
        self.assertTrue(out and out[0].startswith("[backdrop-subject-background]"))

    def test_missing_or_unknown_fails(self) -> None:
        for f in (None, "지하철"):
            out = checks.check_backdrop_subject(_subject_P(f))
            self.assertTrue(out and out[0].startswith("[backdrop-subject-unmatched]"), f)

    def test_registered_hard(self) -> None:
        self.assertIn("backdrop_subject", checks.HARD)
        self.assertIn("island_text_contrast", checks.HARD)

    def test_budget_direction_declares_for(self) -> None:
        """예산안 연출 — 배경 6개 모두 for 가 레지스트리 main_subject 에 있다(이번 장치의 첫 적용)."""
        import yaml  # noqa: PLC0415

        from engine.media_registry import load_media_registry  # noqa: PLC0415

        mr = load_media_registry()
        doc = yaml.safe_load(open(checks.__file__.replace("engine/checks.py", "projects/budget_2027/direction.yaml"), encoding="utf-8"))
        bds = [e for e in doc["events"] if e["type"] == "backdrop"]
        self.assertEqual(len(bds), 6)
        for e in bds:
            self.assertIn(e.get("for"), mr[e["img"]].main_subject, e["img"])


def _surface(v: float, k: float = 1.0) -> tuple[cairo.ImageSurface, float]:
    """균일한 회색 면(sRGB v) — backdrop_surface 대역. 화면보다 크게(ken_burns 여유)."""
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, 900, 520)
    c = cairo.Context(s)
    c.set_source_rgb(v, v, v)
    c.paint()
    return s, k


def _contrast_P() -> NS:  # noqa: N802
    isl = {"type": "island", "kind": "structure", "box": "center_tall", "t0": 1.0, "t1": 9.0}
    bd = {"type": "backdrop", "img": "x", "t0": 0.0, "t1": 10.0}
    return NS(R=NS(stage=NS(name="backdrop")), events=[bd, isl])


class IslandTextContrastTest(unittest.TestCase):
    def test_boxed_on_brightest_dimmed_photo_passes(self) -> None:
        with mock.patch("engine.layers.backdrop.backdrop_surface", return_value=_surface(1 - R.stage_backdrop.dim)):
            ms = checks.island_text_contrast(_contrast_P())
            self.assertEqual(checks.check_island_text_contrast(_contrast_P()), [])
        self.assertEqual(len(ms), 1)
        self.assertGreaterEqual(ms[0]["worst"], R.qa_checks.map_contrast_text)

    def test_bare_island_fails(self) -> None:
        """R-0618 상태 — 무대 표면 팔레트(noturno)가 상자를 지워 밝은 사진 위에 글자가 바로 놓인다."""
        from engine.style import apply_palette  # noqa: PLC0415

        apply_palette("noturno")
        self.addCleanup(apply_palette, None)
        with mock.patch("engine.layers.backdrop.backdrop_surface", return_value=_surface(1 - R.stage_backdrop.dim)), \
             mock.patch("engine.island.on_backdrop", return_value=False):
            out = checks.check_island_text_contrast(_contrast_P())
        self.assertTrue(out and out[0].startswith("[island-text-contrast]"))

    def test_not_backdrop_stage_not_checked(self) -> None:
        P = _contrast_P()
        P.R.stage.name = "timeline"
        self.assertEqual(checks.island_text_contrast(P), [])


if __name__ == "__main__":
    unittest.main()
