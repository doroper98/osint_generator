"""G12 §G(v5.1.0, back_and_forth D-0124, 사용자 결정 D109) — 엔딩 카드 오른쪽 아래 구석 버전 도장 `v{VERSION}`.

- 문자열 = "v" + VERSION 파일(렌더 시점, 다른 출처 금지 P3).
- 위치·크기 = rules end_card.version_stamp(가장 작은 글씨급, 오른쪽 정렬), 안내 줄과 겹치면 dy 만큼 위로.
- 롤(scroll)이 있어도 고정 — 스크롤 오프셋에 실리지 않는다.
- provenance end_card.version_stamp = "v" + repo_version.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

import cairo

from engine import fullcards
from engine.style import END_CARD, H_OUT, W_OUT

REPO = Path(__file__).resolve().parent.parent
STAMP = END_CARD.version_stamp


def _R() -> NS:  # noqa: N802
    return NS(tb=NS(plan=NS(date="2026.09.30"), order=["a_0"]), credits=NS(sections=[]),
              assets=NS(rights={}, media={}), cache={"sentence_labels": {}})


def _drawn(lt: float, roll: tuple[float, float] = (0.0, 0.0)) -> list[tuple[str, float, float, float, str, float]]:
    """draw_endcard 가 text() 로 그린 (문자열, x, y, 크기, 글꼴, 알파)."""
    calls: list[tuple[str, float, float, float, str, float]] = []

    def rec(_ctx, s, x, y, size, name="sansm", col=(1, 1, 1), a=1.0, *args, **kw):  # noqa: ANN001, ANN002, ANN003, ANN202
        calls.append((s, x, y, size, name, a))
        return 0.0

    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480))
    with mock.patch.object(fullcards, "credit_sections", return_value=[]), \
         mock.patch.object(fullcards, "endcard_roll", return_value=roll), \
         mock.patch.object(fullcards, "text", side_effect=rec):
        fullcards.draw_endcard(ctx, _R(), lt, NS(t0=0.0, t1=END_CARD.dur_sec), 1.0)
    return calls


class VersionStampTest(unittest.TestCase):
    def test_string_is_version_file(self) -> None:
        want = "v" + (REPO / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(fullcards.version_stamp(), want)
        with mock.patch.object(fullcards, "VERSION_FILE", NS(read_text=lambda encoding: "9.8.7\n")):
            self.assertEqual(fullcards.version_stamp(), "v9.8.7")   # 렌더 시점에 파일을 읽는다(상수 아님)
        src = (REPO / "engine" / "fullcards.py").read_text(encoding="utf-8")
        self.assertNotIn('"v5.', src)   # 코드 상수 금지(P3)

    def test_position_and_size_from_rules(self) -> None:
        self.assertEqual((STAMP.x_from_right, STAMP.y_from_bottom, STAMP.size, STAMP.font, STAMP.alpha), (12, 10, 7.8, "mono", 0.55))
        self.assertLessEqual(STAMP.size, min(END_CARD.license_size, END_CARD.notice_unverified.size))   # 가장 작은 글씨급
        hits = [c for c in _drawn(5.0) if c[0] == fullcards.version_stamp()]
        self.assertEqual(len(hits), 1)
        s, x, y, size, name, a = hits[0]
        self.assertEqual((x, y, size, name), (W_OUT - STAMP.x_from_right, H_OUT - STAMP.y_from_bottom, STAMP.size, STAMP.font))
        self.assertAlmostEqual(a, STAMP.alpha)
        self.assertEqual(fullcards.version_stamp_overflow(None), [])

    def test_fixed_under_roll(self) -> None:
        stamp = fullcards.version_stamp()
        pos = {(c[1], c[2]) for lt in (1.0, 4.0, 8.0) for c in _drawn(lt, (300.0, 50.0)) if c[0] == stamp}
        self.assertEqual(pos, {(W_OUT - STAMP.x_from_right, H_OUT - STAMP.y_from_bottom)})   # 롤 오프셋에 실리지 않는다

    def test_moves_up_when_notice_overlaps(self) -> None:
        free = fullcards.version_stamp_box(None)
        self.assertEqual(fullcards.version_stamp_box("짧은 안내"), free)   # 안 겹치면 그대로
        long_notice = "가" * 120   # 오른쪽 끝까지 닿는 안내 줄 → 도장이 dy 만큼 위로(notice 우선)
        moved = fullcards.version_stamp_box(long_notice)
        self.assertAlmostEqual(free[1] - moved[1], STAMP.dy)
        self.assertEqual(free[0], moved[0])

    def test_baseline_mask_box_covers_any_version(self) -> None:
        """hormuz 기준선 가림 상자(D-0148, PIPELINE-AP-021) — 오른쪽 끝 고정, 폭 ≥ 'v99.99.99', 현재 도장 상자를 포함."""
        from engine.typography import adv  # noqa: PLC0415

        base = json.loads((REPO / "docs/handoff/reports/phaseQ2/hormuz_baseline.json").read_text(encoding="utf-8"))
        x0, y0, x1, y1 = base["stamp_box"]
        self.assertEqual(x1, W_OUT - STAMP.x_from_right)
        self.assertGreaterEqual(x1 - x0, adv("v99.99.99", STAMP.size, STAMP.font))
        c0, c1, c2, c3 = fullcards.version_stamp_box(None)
        self.assertTrue(x0 <= c0 and y0 <= c1 and c2 <= x1 and c3 <= y1, (base["stamp_box"], (c0, c1, c2, c3)))

    def test_provenance_matches_repo_version(self) -> None:
        from orchestrator import __version__  # noqa: PLC0415

        self.assertEqual(fullcards.version_stamp(), "v" + __version__)
        src = (REPO / "engine" / "mux.py").read_text(encoding="utf-8")
        self.assertIn('prov["end_card"] = {"version_stamp": version_stamp()}', src)


if __name__ == "__main__":
    unittest.main()
