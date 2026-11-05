"""area 이벤트 — 1급 행정구역(주) 채움 (v7.4.0, back_and_forth D-0290 §3-6).

스키마(필수 키·band·status 리터럴), 1프레임 렌더 뒤 주 안 픽셀 색(light·dark), 정직성 검사 5종 각각 실패 재현,
옛 geo.pkl(code 없음) + area → StageError, 데이터 파일 모델.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import cairo
import numpy as np
from pydantic import ValidationError

from engine import checks
from engine.events import AreaEvent
from engine.layers.areas import draw_area
from engine.projection import View
from engine.registry import MAP_LAYER_ORDER, REGISTRY
from engine.stage import MercatorStage, StageError, to_uv
from engine.style import C, C_THEME, H_OUT, W_OUT
from schemas.election_models import StateResultsFile

SQUARE = np.array([[-100.0, 30.0], [-96.0, 30.0], [-96.0, 34.0], [-100.0, 34.0], [-100.0, 30.0]])


def ev(**kw: object) -> dict:
    base = dict(type="area", t0=0.0, t1=10.0, country="US", race="senate", src="에이피 집계 · 2026-11-05",
                items=[dict(code="US-TX", col="dem", band="solid", status="called", delay=0.0)])
    base.update(kw)
    return base


def stage(theme: str = "light", code: "str | None" = "US-TX") -> MercatorStage:
    st = MercatorStage(tiers={"W": dict(lon0=-130.0, lat0=15.0, lon1=-60.0, lat1=55.0)}, config={"theme": theme})
    st.adm = {"US": [dict(name="텍사스", code=code, xy=None, rings=to_uv([SQUARE]))]}
    return st


def render(st: MercatorStage, e: dict, t: float = 5.0) -> np.ndarray:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(1, 1, 1) if st.theme_name == "light" else ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    view = View(st, np.array([-98.0, st.to_world(lon=-98.0, lat=32.0)[1], 20.0]))
    draw_area(ctx, None, view, t, AreaEvent.model_validate(e).model_dump())
    surf.flush()
    a = np.ndarray((H_OUT, W_OUT, 4), np.uint8, surf.get_data())
    x, y = view.to_screen_arr(np.array([[-98.0, st.to_world(lon=-98.0, lat=32.0)[1]]]))[0]
    b, g, r, _ = a[int(y), int(x)]
    return np.array([r, g, b], float) / 255


class AreaSchemaTest(unittest.TestCase):
    def test_valid_and_registered(self) -> None:
        AreaEvent.model_validate(ev())
        self.assertIn("area", REGISTRY)
        self.assertEqual(MAP_LAYER_ORDER[MAP_LAYER_ORDER.index("country") + 1], "area")

    def test_required_and_literals(self) -> None:
        for bad in (dict(src=""), dict(src="   "), dict(items=[]), dict(race="house"), dict(country="usa")):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                AreaEvent.model_validate(ev(**bad))
        for item in (dict(band="huge"), dict(status="maybe"), dict(col="purple"), dict(delay=-1.0), dict(code="TX")):
            it = dict(code="US-TX", col="dem", band="solid", status="called", delay=0.0) | item
            with self.subTest(item=item), self.assertRaises(ValidationError):
                AreaEvent.model_validate(ev(items=[it]))
        e = ev()
        e.pop("src")
        with self.assertRaises(ValidationError):
            AreaEvent.model_validate(e)


class AreaRenderTest(unittest.TestCase):
    def test_fill_turns_party_color(self) -> None:
        for theme in ("light", "dark"):
            for col in ("dem", "rep"):
                with self.subTest(theme=theme, col=col):
                    st = stage(theme)
                    bg = np.ones(3) if theme == "light" else np.zeros(3)
                    px = render(st, ev(items=[dict(code="US-TX", col=col, band="landslide", status="called", delay=0.0)]))
                    want = np.array((C_THEME.get(theme, {}).get(col) or C[col]))
                    self.assertLess(np.abs(px - want).sum(), np.abs(bg - want).sum() * 0.6, (px, want))
                    other = "rep" if col == "dem" else "dem"
                    want_o = np.array((C_THEME.get(theme, {}).get(other) or C[other]))
                    self.assertLess(np.abs(px - want).sum(), np.abs(px - want_o).sum())

    def test_delay_hides_before_start(self) -> None:
        st = stage()
        px = render(st, ev(items=[dict(code="US-TX", col="rep", band="solid", status="called", delay=8.0)]), t=5.0)
        np.testing.assert_allclose(px, np.ones(3), atol=0.01)

    def test_old_geo_pkl_raises(self) -> None:
        with self.assertRaises(StageError):
            render(stage(code=None), ev())

    def test_missing_code_raises(self) -> None:
        with self.assertRaises(StageError):
            render(stage(), ev(items=[dict(code="US-ZZ", col="dem", band="solid", status="called", delay=0.0)]))


def results(**tx: object) -> StateResultsFile:
    race = dict(winner="탈라리코", winner_party="dem", loser="팩스턴", status="called", called_by="AP",
                source_url="https://www.texastribune.org/x", retrieved_at="2026-11-05") | tx
    ms = dict(winner_party="none", leader="콜롬", status="counting", source_url="https://abcnews.com/x", retrieved_at="2026-11-05")
    return StateResultsFile.model_validate(dict(schema_version=1, as_of="2026-11-05T09:00+09:00",
                                                states={"US-TX": dict(name="텍사스", senate=race), "US-MS": dict(name="미시시피", senate=ms)}))


def report(events: list[dict], res: "StateResultsFile | None" = None, codes: "set[str] | None" = None) -> list[str]:
    have = {"US-TX", "US-MS"} if codes is None else codes
    return checks.area_report(events, lambda k: have if k == "US" else None, results() if res is None else res, None)


class AreaChecksTest(unittest.TestCase):
    def tag(self, out: list[str], tag: str) -> None:
        self.assertTrue(any(o.startswith(tag) for o in out), out)

    def test_clean(self) -> None:
        ms = dict(code="US-MS", col="muted", band="lean", status="counting", delay=1.0)
        self.assertEqual(report([ev(items=ev()["items"] + [ms])]), [])

    def test_code_missing(self) -> None:
        self.tag(report([ev()], codes={"US-MS"}), "[area-code-missing]")

    def test_src_missing(self) -> None:
        self.tag(report([ev(src=" ")]), "[area-src-missing]")

    def test_col(self) -> None:
        self.tag(report([ev(items=[dict(code="US-TX", col="gold", band="solid", status="called", delay=0.0)])]), "[area-col]")

    def test_data_mismatch(self) -> None:
        self.tag(report([ev(items=[dict(code="US-TX", col="rep", band="solid", status="called", delay=0.0)])]), "[area-data-mismatch]")
        # 콜 없는 주를 확정처럼 칠함
        self.tag(report([ev(items=[dict(code="US-MS", col="rep", band="lean", status="called", delay=0.0)])]), "[area-data-mismatch]")
        # 데이터 파일 없음
        out = checks.area_report([ev()], lambda k: {"US-TX"}, None, "no file")
        self.tag(out, "[area-data-mismatch]")

    def test_overlap(self) -> None:
        self.tag(report([ev(), ev(t0=5.0, t1=12.0)]), "[area-overlap]")
        self.tag(report([ev(items=ev()["items"] * 2)]), "[area-overlap]")
        self.assertEqual(report([ev(t1=4.0), ev(t0=5.0, t1=12.0)]), [])

    def test_dense_warning_and_severity(self) -> None:
        many = [dict(code=f"US-A{i}", col="dem", band="solid", status="called", delay=0.0) for i in range(45)]
        self.assertTrue(checks.area_dense([dict(type="area", t0=0.0, items=many)]))
        self.assertIn("area", checks.HARD)
        self.assertIn("area_dense", checks.WARN)


class StateResultsModelTest(unittest.TestCase):
    def test_called_needs_winner_and_counting_has_none(self) -> None:
        with self.assertRaises(ValidationError):
            results(called_by=None)
        with self.assertRaises(ValidationError):
            results(status="counting")

    def test_project_file_validates(self) -> None:
        p = Path(__file__).resolve().parent.parent / "projects" / "us_midterms_2026" / "data" / "state_results.yaml"
        if not p.exists():
            raise AssertionError("us_midterms_2026 데이터 파일이 없다")
        from schemas.election_models import load_state_results  # noqa: PLC0415

        load_state_results(p)


if __name__ == "__main__":
    unittest.main()
