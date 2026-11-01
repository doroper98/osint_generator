"""v7.4.0 back_and_forth D-0336 T3·D-0339 — 경제 템플릿 등록과 사용자 의견 장치(UF-149·151~157·202).

- 팔레트: princess 삭제(UF-156, P2) · 경제 장르 기본 = noturno + 무대 표면(D-0330·D-0336) · 손실 막대 = A(muted_fill, UF-204) 하나만.
- 르포는 느낌만(UF-157·UF-202, LLM-AP-022): 르포 카드·캡션 조판 코드가 엔진에 없다.
- 새 검사(event 수준): [chart-overload](UF-154) · [chart-layers-min](UF-151) · [secondary-axis-single](UF-152) ·
  [bars-from-zero] · [estimate-actual-pair](T3) · [grid-text-cross](UF-155) · [bar-border](UF-202).
"""

from __future__ import annotations

import re
import unittest

import numpy as np
import yaml

from engine import checks
from rules import RULES_PATH, load_rules
from tests.anti_inertia._ast_util import REPO


def _s(t0: float, t1: float, lane: str = "rev", sid: str = "INTC_REV_Q", style: str = "bars", **kw) -> dict:  # noqa: ANN003
    return {"type": "series", "t0": t0, "t1": t1, "lane": lane, "series_id": sid, "style": style, **kw}


class PaletteTest(unittest.TestCase):
    def test_princess_deleted(self) -> None:
        """UF-156 "princess 컨셉 너무 구리다 갈아엎어" — 팔레트·장르·엔진 어디에도 princess 가 없다(다시 들여오면 실패)."""
        self.assertNotIn("princess", load_rules().palettes)
        hits = [str(p.relative_to(REPO)) for root in ("engine", "genres", "schemas", "rules") for p in (REPO / root).rglob("*")
                if p.suffix in (".py", ".yaml") and p.name != "user_feedback.yaml"
                and re.search(r"^\s*princess\s*:|['\"]princess['\"]", p.read_text(encoding="utf-8"), re.M)]
        self.assertEqual(hits, [])

    def test_earnings_default_is_noturno_stage(self) -> None:
        """D-0330·D-0336 — 경제 장르 기본 = noturno 토큰 + surface stage(차트 = 무대)."""
        g = yaml.safe_load((REPO / "genres" / "earnings.yaml").read_text(encoding="utf-8"))
        self.assertEqual(g["palette"], "noturno")
        self.assertEqual(load_rules().palettes["noturno"].surface, "stage")

    def test_loss_fill_is_a_only(self) -> None:
        """UF-204 "A" — 손실 막대 = muted_fill 하나. ink_light 대안 키·손실 윤곽 키는 삭제(P2)."""
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))["stage_timeline"]["bars"]
        self.assertEqual(raw["negative_fill"], "muted_fill")
        for k in ("neg_ink_step", "neg_outline_w", "neg_fill_alpha", "edge_w", "edge_alpha"):
            self.assertNotIn(k, raw, k)
        src = (REPO / "engine" / "layers" / "series.py").read_text(encoding="utf-8")
        self.assertNotIn("ink_light", src)
        self.assertNotIn("neg_outline_w", src)


class ReportageFeelOnlyTest(unittest.TestCase):
    def test_no_reportage_card_code(self) -> None:
        """UF-157·UF-202 "르포는 느낌만 … 바닥에서 새로 조판" — 르포 카드·캡션 조판 이식 코드가 엔진·규칙에 없다(LLM-AP-022)."""
        pat = re.compile(r"reportage_card|report_card|reportage_caption|def _draw_card_head|card_head_band")
        hits = [str(p.relative_to(REPO)) for p in (REPO / "engine").rglob("*.py") if pat.search(p.read_text(encoding="utf-8"))]
        self.assertEqual(hits, [])
        S = load_rules().island.stage_surface  # noqa: N806
        self.assertEqual(S.source_lines, 1)   # 출처 한 줄(카드 출처 표 이식 금지)


class BarVocabularyTest(unittest.TestCase):
    def test_vocabulary_keys(self) -> None:
        """UF-149 어휘(속빈/채움·잉크 사다리·직접 라벨) · UF-155 막대 모양(바닥 각·위 3px)."""
        B = load_rules().stage_timeline.bars  # noqa: N806
        self.assertEqual(B.top_radius, 3)
        self.assertGreater(B.hollow_w, 0)
        self.assertEqual(list(B.ladder), sorted(B.ladder, reverse=True))


class ChartOverloadTest(unittest.TestCase):
    def test_too_many_visible(self) -> None:
        evs = [_s(0, 30, sid=f"S{i}", style="line", lane="a") for i in range(5)]
        self.assertTrue(any("[chart-overload]" in w and "보이는 층" in w for w in checks.chart_overload(evs)))

    def test_layers_too_fast(self) -> None:
        evs = [_s(0, 30), _s(1.5, 30, sid="INTC_PX_D", style="line", secondary=True)]
        self.assertTrue(any("간격" in w for w in checks.chart_overload(evs)))

    def test_paced_and_continuation_pass(self) -> None:
        """층마다 문장 하나(≥ dwell) · 같은 층을 문장 경계에서 이어 붙인 것(accent 이동)은 새 층이 아니다."""
        evs = [_s(0, 10, accent="latest"), _s(10, 30, accent="none", grow=False), _s(6, 30, sid="INTC_PX_D", style="line", secondary=True)]
        self.assertEqual(checks.chart_overload(evs), [])

    def test_detail_inset_not_counted(self) -> None:
        evs = [_s(0, 30), _s(1.0, 30, style="range", sid="INTC_GUIDE_REV_LO", detail=True, title="t")]
        self.assertEqual(checks.chart_overload(evs), [])


class ChartLayersMinTest(unittest.TestCase):
    def test_single_layer_econ_fails(self) -> None:
        self.assertTrue(checks.chart_layers_min([_s(0, 30)], "earnings"))

    def test_three_layers_pass(self) -> None:
        evs = [_s(0, 30, estimate_id="INTC_REV_Q_EST"), _s(6, 30, sid="INTC_PX_D", style="line", secondary=True)]
        self.assertEqual(checks.chart_layers_min(evs, "earnings"), [])

    def test_other_genre_skipped(self) -> None:
        self.assertEqual(checks.chart_layers_min([_s(0, 30)], "macro_monetary"), [])


class SecondaryAxisTest(unittest.TestCase):
    def test_two_secondary_same_lane(self) -> None:
        evs = [_s(0, 30, sid="A", style="line", secondary=True), _s(5, 30, sid="B", style="line", secondary=True)]
        self.assertTrue(checks.secondary_axis_single(evs))
        self.assertEqual(checks.secondary_axis_single(evs[:1]), [])


class BarsFromZeroTest(unittest.TestCase):
    def test_range_without_zero(self) -> None:
        self.assertTrue(checks.bars_from_zero([_s(0, 30)], {"rev": (5.0, 20.0)}))
        self.assertEqual(checks.bars_from_zero([_s(0, 30)], {"rev": (0.0, 20.0)}), [])


class EstimatePairTest(unittest.TestCase):
    def test_same_unit_overlapping(self) -> None:
        self.assertEqual(checks.estimate_actual_pair([_s(0, 30, estimate_id="INTC_REV_Q_EST")]), [])

    def test_unit_mismatch(self) -> None:
        self.assertTrue(checks.estimate_actual_pair([_s(0, 30, estimate_id="INTC_EPS_Q_EST")]))


class BarBorderPixelTest(unittest.TestCase):
    def _img(self, border: bool) -> np.ndarray:
        img = np.zeros((40, 40, 4), np.uint8)
        img[10:30, 10:30, :3] = 200
        if border:
            img[10:30, 10:12, :3] = 255
            img[10:30, 28:30, :3] = 255
        return img

    def test_border_detected(self) -> None:
        self.assertTrue(checks.bar_border_hits(self._img(True), [(10, 10, 30, 30)], 1.0))

    def test_solid_passes(self) -> None:
        self.assertEqual(checks.bar_border_hits(self._img(False), [(10, 10, 30, 30)], 1.0), [])


class GridTextCrossTest(unittest.TestCase):
    """UF-155 "선과 글씨가 겹치는 부분은 적용하지 말고" — 세로 격자선(레인 위 끝 ~ 출처 띠 위) ↔ 글자 상자."""

    def _world(self):  # noqa: ANN202
        from types import SimpleNamespace as NS  # noqa: PLC0415

        stage = NS(n=1, ticks=lambda v: [("2026-01-01", "year")], x_of=lambda d: 100.0, lane_screen=lambda v, i: (50.0, 250.0))
        view = NS(ox=0.0, right=854.0, to_screen=lambda x, y: (x, y))
        return stage, view

    def test_crossing_detected(self) -> None:
        stage, v = self._world()
        out = checks.grid_text_crossings(stage, v, [], 1.0, {}, [("레인 이름", (90.0, 55.0, 160.0, 70.0))])
        self.assertTrue(out and "[grid-text-cross]" in out[0])

    def test_clear_text_passes(self) -> None:
        stage, v = self._world()
        self.assertEqual(checks.grid_text_crossings(stage, v, [], 1.0, {}, [("레인 이름", (110.0, 55.0, 160.0, 70.0))]), [])


class RegisteredHardTest(unittest.TestCase):
    def test_new_checks_hard(self) -> None:
        for cid in ("chart_overload", "chart_layers_min", "secondary_axis_single", "bars_from_zero", "estimate_actual_pair",
                    "grid_text_cross", "bar_border"):
            self.assertIn(cid, checks.HARD, cid)
        self.assertNotIn("bars_from_zero", load_rules().qa_checks.planned)


if __name__ == "__main__":
    unittest.main()
