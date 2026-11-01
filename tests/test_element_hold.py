"""v7.4.0 back_and_forth D-0462 — 사용자 의견 UF-171("뱃지나 사진이나 기사 조판이나 너무 빨리 사라져") · UF-172("사진 템플릿이 … 제목에 묻혀 사라졌어").

[element-hold] 요소 종류별 완전 노출(페이드 뺀 구간) ≥ qa_checks.element_hold.min_full_sec,
[media-overlap] 앞 요소가 그 하한 전에 덮이거나 전면 카드가 떠 있는 동안 시작하면 hard.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from engine import checks
from engine.checks import HARD, check_element_hold, check_media_overlap, element_full_span
from engine.style import ELEM
from rules import load_rules

QA = load_rules().qa_checks
MIN = QA.element_hold.min_full_sec


def _P(*events: dict) -> SimpleNamespace:  # noqa: N802
    return SimpleNamespace(events=list(events))


def _photo(t0: float, t1: float, mid: str = "p", x: float = 196, y: float = 70, w: float = 461) -> dict:
    return {"type": "photo", "t0": t0, "t1": t1, "mid": mid, "x": x, "y": y, "w": w}


class RuleTest(unittest.TestCase):
    def test_rule_values(self) -> None:
        self.assertEqual(MIN, 6.0)   # 감독 제안 값(D-0462 §2-1) ≥ cold_1 아라그치 인용 완전 노출 4.21초
        self.assertEqual(set(QA.element_hold.types), {"badge", "photo", "clip", "cutout", "article", "quote"})
        self.assertIn("element_hold", HARD)
        self.assertIn("media_overlap", HARD)
        self.assertIn("element_hold", QA.regression_ref_checks)   # 회귀 기준(골든)만 면제 — 사용자 영상은 waive_regression 이 그대로 둔다

    def test_clip_show_range_fits_hold(self) -> None:
        """broll 클립 상한이 완전 노출 하한 + 등장·퇴장보다 길어야 한다(둘이 서로를 막지 않게)."""
        lo, hi = load_rules().media_beats.clip_show_sec["broll"]
        self.assertGreaterEqual(hi, MIN + sum(ELEM["clip"]))


class ElementHoldTest(unittest.TestCase):
    def test_full_span_excludes_fades(self) -> None:
        a, b = element_full_span(_photo(10.0, 20.0))
        self.assertAlmostEqual(a, 10.0 + ELEM["photo"][0])
        self.assertAlmostEqual(b, 20.0 - ELEM["photo"][1])

    def test_short_photo_fails(self) -> None:
        out = check_element_hold(_P(_photo(10.0, 12.4)))   # UF-172 뉴올리언스 사진 2.4초
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("[element-hold] photo"))

    def test_long_enough_passes(self) -> None:
        need = MIN + sum(ELEM["photo"]) + 0.05
        self.assertEqual(check_element_hold(_P(_photo(10.0, 10.0 + need))), [])

    def test_badge_and_quote_and_article(self) -> None:
        short = [{"type": "badge", "t0": 0.0, "t1": 0.8, "label": "sharif"},          # UF-171 샤리프 뱃지 0.8초
                 {"type": "quote", "t0": 1.0, "t1": 6.0, "speaker": "x"},
                 {"type": "article", "t0": 10.0, "t1": 15.0, "mid": "a"}]
        self.assertEqual(len(check_element_hold(_P(*short))), 3)

    def test_other_types_ignored(self) -> None:
        self.assertEqual(check_element_hold(_P({"type": "marker", "t0": 0.0, "t1": 0.5, "label": "m"})), [])


class MediaOverlapTest(unittest.TestCase):
    def test_photo_started_under_article(self) -> None:
        """UF-172 — 기사 카드(72.7초) 0.1초 뒤에 시작한 사진은 카드 아래에 깔린다."""
        art = {"type": "article", "t0": 72.7, "t1": 81.5, "mid": "a"}
        out = check_media_overlap(_P(art, _photo(72.8, 80.5)))
        self.assertTrue(any(x.startswith("[media-overlap] photo") for x in out))

    def test_photo_covered_early_by_article(self) -> None:
        out = check_media_overlap(_P(_photo(10.0, 18.0), {"type": "article", "t0": 12.0, "t1": 20.0, "mid": "a"}))
        self.assertEqual(len(out), 1)

    def test_box_overlap_only_when_boxes_touch(self) -> None:
        clip_far = {"type": "clip", "t0": 12.0, "t1": 20.0, "mid": "c", "x": 700, "y": 400, "w": 100}
        clip_on = {"type": "clip", "t0": 12.0, "t1": 20.0, "mid": "c", "x": 40, "y": 150, "w": 300}
        self.assertEqual(check_media_overlap(_P(_photo(10.0, 18.0), clip_far)), [])
        self.assertEqual(len(check_media_overlap(_P(_photo(10.0, 18.0), clip_on))), 1)

    def test_sequential_passes(self) -> None:
        p = _photo(10.0, 17.6)
        a, b = element_full_span(p)
        art = {"type": "article", "t0": b + 0.01, "t1": b + 9.0, "mid": "a"}
        self.assertEqual(check_media_overlap(_P(p, art)), [])


class WiredTest(unittest.TestCase):
    def test_registered_in_run(self) -> None:
        """검사 표(docstring)와 실행 표에 둘 다 있다 — 콘티 판·프리뷰·전편이 같은 run 을 쓴다(C12-3)."""
        src = open(checks.__file__, encoding="utf-8").read()
        for cid in ("element_hold", "media_overlap"):
            self.assertIn(f'"{cid}": lambda: check_{cid}(P)', src)
            self.assertIn(f"| {cid} | hard |", src)


if __name__ == "__main__":
    unittest.main()
