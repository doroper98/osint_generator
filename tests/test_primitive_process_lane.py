"""프리미티브 process_lane — 과정 도식 (v7.4.0, 사용자 의견 UF-400 · 영상 분석 보고 §4 D5).

불변 층: 출처·날짜 필수. 단계 수·이름 길이·줄 수·단계 번호는 규칙 범위 안(벗어나면 렌더 전 오류, P6).
표지는 moves 시각 전에는 움직이지 않고, 이동은 5차 이징으로 끝 단계에 정확히 선다. 상자는 매 프레임 같은 자리(예약 영역 고정).
"""

from __future__ import annotations

import copy
import unittest

import cairo
from pydantic import ValidationError

from engine.primitives import PrimitiveError, event_model, module, style_for
from engine.primitives.process_lane import token_pos
from engine.style import PRIMITIVES
from genres.load import load_genre

MOD = module("process_lane")
FX = MOD.PREVIEW_FIXTURE
L = PRIMITIVES["process_lane"]


def _data(**over: object) -> dict:
    d = {k: copy.deepcopy(v) for k, v in FX.items() if k not in ("type", "id", "t0", "t1")}
    d.update(over)
    return d


def _style(genre: str = "political_history"):  # noqa: ANN202
    return style_for("process_lane", load_genre(genre).color_semantics)


def _render(t: float, e: dict) -> bytes:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
    MOD.draw(cairo.Context(surf), None, t, e, _style())
    return bytes(surf.get_data())


class ProcessLaneDataTest(unittest.TestCase):
    def test_fixture_passes_schema(self) -> None:
        event_model("process_lane", MOD.SCHEMA).model_validate(FX)

    def test_invalid_data_is_error(self) -> None:
        bad = {
            "empty source": _data(source=" "),
            "bad date": _data(date="11월"),
            "too few steps": _data(steps=["가", "나"], gate_after=0),
            "too many steps": _data(steps=[f"단계{i}" for i in range(L.steps_max + 1)]),
            "long step": _data(steps=["가" * (L.step_chars_max + 1), "나", "다"]),
            "gate at end": _data(gate_after=len(FX["steps"]) - 1),
            "token beyond steps": _data(rows=[{"token": "가", "at": len(FX["steps"])}]),
            "too many rows": _data(rows=[{"token": f"t{i}"} for i in range(L.rows_max + 1)]),
            "moves out of order": _data(rows=[{"token": "가", "moves": [{"t": 5.0, "at": 1}, {"t": 2.0, "at": 2}]}]),
            "span reversed": _data(rows=[{"token": "가", "span": {"from_step": 2, "to_step": 1, "label": "1년", "t": 1.0}}]),
            "unknown field": _data(color="red"),
        }
        for why, d in bad.items():
            with self.subTest(why=why), self.assertRaises(ValidationError):
                MOD.SCHEMA.model_validate(d)

    def test_genre_without_colors_is_error(self) -> None:
        """색 의미(emphasis·secondary_text)가 없는 장르 = 렌더 전 오류(조용히 기본색으로 그리지 않는다)."""
        with self.assertRaises(PrimitiveError):
            style_for("process_lane", {"emphasis": "gold"})


class ProcessLaneMotionTest(unittest.TestCase):
    def test_token_waits_then_lands(self) -> None:
        r = FX["rows"][0]
        m0 = r["moves"][0]
        self.assertEqual(token_pos(r, m0["t"] - 0.1), r["at"])
        mid = token_pos(r, m0["t"] + L.move_sec / 2)
        self.assertTrue(r["at"] < mid < m0["at"])
        self.assertAlmostEqual(token_pos(r, m0["t"] + L.move_sec), m0["at"])

    def test_second_row_appears_at_its_time(self) -> None:
        """상자는 처음부터 줄 수만큼 높이를 잡는다(나중 줄이 붙어도 상자가 튀지 않게). 둘째 줄 내용은 제 시각 전에는 그리지 않는다."""
        r2_t = FX["rows"][1]["t"]
        other = {**FX, "rows": [FX["rows"][0], {**FX["rows"][1], "token": "다른 표지", "label": "다른 줄"}]}
        self.assertEqual(_render(r2_t - 0.1, FX), _render(r2_t - 0.1, other))
        self.assertNotEqual(_render(r2_t + 2.0, FX), _render(r2_t + 2.0, other))

    def test_box_is_fixed(self) -> None:
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        boxes = {MOD.draw(ctx, None, t, FX, _style()) for t in (0.1, 3.0, 8.9, 20.0)}
        self.assertEqual(len(boxes), 1)
        x0, y0, x1, y1 = boxes.pop()
        self.assertLessEqual(x1, 854)
        self.assertLessEqual(y1, 400, "자막 구역 위에 끝나야 한다")


if __name__ == "__main__":
    unittest.main()
