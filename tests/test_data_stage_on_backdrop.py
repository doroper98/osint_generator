"""v7.4.0 감독 D619(UF-304 "직관적이고 시인성") — 사진 배경(backdrop 주 무대) 위 데이터 무대는 무대 표면 팔레트여도 아일랜드 상자 안에.
R-0618 프리뷰 상태(무대 표면 팔레트가 상자를 지움) 재현 = [data-stage-bare-on-backdrop] 오류."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest import mock

from engine import checks
from engine.style import apply_palette


def _P(stage: str) -> NS:  # noqa: N802
    e = {"type": "island", "kind": "structure", "box": "center_tall", "t0": 1.0, "t1": 9.0}
    return NS(R=NS(stage=NS(name=stage)), events=[e])


class DataStageOnBackdropTest(unittest.TestCase):
    def setUp(self) -> None:
        apply_palette("noturno")   # 무대 표면(surface: stage) 팔레트

    def tearDown(self) -> None:
        apply_palette(None)

    def test_boxed_on_backdrop_passes(self) -> None:
        self.assertEqual(checks.check_data_stage_bare_on_backdrop(_P("backdrop")), [])

    def test_r0618_state_fails(self) -> None:
        with mock.patch("engine.island.on_backdrop", return_value=False):   # 옛 경로: 표면 팔레트면 상자 없음
            out = checks.check_data_stage_bare_on_backdrop(_P("backdrop"))
        self.assertTrue(out and "data-stage-bare-on-backdrop" in out[0])

    def test_not_backdrop_stage_not_checked(self) -> None:
        self.assertEqual(checks.check_data_stage_bare_on_backdrop(_P("timeline")), [])


if __name__ == "__main__":
    unittest.main()
