"""v7.4.0 D-0245(사용자 의견 UF-126 "그래프들 왜 다 사라졌어?") — 지정 시리즈·이전 승인 데이터 패널의 조용한 드롭 금지(P6).

재현: diesel_road_2026 v2 연출 초안(direction.v1.yaml, AI director)에는 track_v1 의 dual_line 3종이 없다 →
[series-unused](order.yaml data.series)·[panel-dropped](track_v1) 가 각각 실패. 복원한 현재 연출(direction.yaml)은 둘 다 0.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from engine import checks as C

REPO = Path(__file__).resolve().parents[2]
PROJ = REPO / "projects" / "diesel_road_2026"
WANT = {"RU_REFINERY_RUNS_2026", "RU_DIESEL_SEABORNE_EXPORTS_2026", "GULF_DIESEL_NET_EXPORTS_2026"}


def _events(p: Path) -> list[dict]:
    return yaml.safe_load(p.read_text(encoding="utf-8"))["events"]


class SeriesPanelsKeptTest(unittest.TestCase):
    def test_order_declares_series(self) -> None:
        self.assertEqual(set(C.order_series(PROJ)), WANT)   # 구조 필드 order.yaml data.series(문장 파싱 아님)

    def test_v2_draft_fails_both(self) -> None:
        draft = _events(PROJ / "direction.v1.yaml")
        self.assertEqual(set(C.series_unused(C.order_series(PROJ), draft, [])), WANT)
        self.assertEqual(set(C.panels_dropped(C.prior_panel_records(PROJ), draft, [])), WANT)
        self.assertIn("series_unused", C.HARD)
        self.assertIn("panel_dropped", C.HARD)

    def test_restored_passes(self) -> None:
        cur = _events(PROJ / "direction.yaml")
        self.assertEqual(C.series_unused(C.order_series(PROJ), cur, []), [])
        self.assertEqual(C.panels_dropped(C.prior_panel_records(PROJ), cur, []), [])

    def test_drop_reason_is_the_only_exception(self) -> None:
        draft = _events(PROJ / "direction.v1.yaml")
        drops = [{"record": r, "reason": "시험 사유"} for r in WANT]
        self.assertEqual(C.series_unused(C.order_series(PROJ), draft, drops), [])
        self.assertEqual(C.panels_dropped(C.prior_panel_records(PROJ), draft, drops), [])


if __name__ == "__main__":
    unittest.main()
