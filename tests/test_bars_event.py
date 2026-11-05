"""bars 이벤트 — 후보별 득표율 막대 (v7.4.0, back_and_forth D-0303 §3, 사용자 의견 UF-170).

스키마(rows 2~3·src·status), 1프레임 렌더 뒤 막대 길이 비율 = pct 비율(같은 축척), 자리(side_order — 화면 밖이면 다음 자리),
정직성 검사 4종(src·data-mismatch·hold·overlap) 실패 재현, 데이터 파일 names_ko·parties 모델. 주 이름 표기 모드(UF-167) 설정 검사.
"""

from __future__ import annotations

import types
import unittest

import cairo
import numpy as np
from pydantic import ValidationError

from engine import checks
from engine.events import BarsEvent
from engine.layers.bars import bars_box, draw_bars
from engine.projection import View
from engine.registry import MAP_LAYER_ORDER, REGISTRY
from engine.stage import MercatorStage, StageError
from engine.style import H_OUT, W_OUT, map_c
from rules import load_rules
from schemas.election_models import StateResultsFile


def ev(**kw: object) -> dict:
    base = dict(type="bars", t0=0.0, t1=6.0, lon=-99.0, lat=31.5, side="right", race="senate", code="US-TX", status="called",
                src="엔비씨 집계 · 2026-11-05", rows=[dict(name="탈라리코", col="dem", pct=55.1), dict(name="팩스턴", col="rep", pct=43.0)])
    base.update(kw)
    return base


def results(**race: object) -> StateResultsFile:
    r = dict(winner="James Talarico", winner_party="dem", loser="Ken Paxton", pct=[55.1, 43.0], status="called", called_by="AP",
             source_url="https://example.com/tx", retrieved_at="2026-11-05", names_ko=["탈라리코", "팩스턴"], parties=["dem", "rep"])
    r.update(race)
    return StateResultsFile.model_validate(dict(schema_version=1, as_of="2026-11-05T09:30", states={"US-TX": dict(name="텍사스", senate=r)}))


def stage(theme: str = "light", **cfg: object) -> MercatorStage:
    return MercatorStage(tiers={"W": dict(lon0=-130.0, lat0=15.0, lon1=-60.0, lat1=55.0)}, config={"theme": theme, **cfg})


def view(st: MercatorStage, lon: float = -99.0, lat: float = 31.5, w: float = 16.0) -> View:
    return View(st, np.array([lon, st.to_world(lon=lon, lat=lat)[1], w]))


class BarsSchemaTest(unittest.TestCase):
    def test_valid_and_registered(self) -> None:
        BarsEvent.model_validate(ev())
        self.assertIn("bars", REGISTRY)
        self.assertIn("bars", load_rules().registries.event_types)
        self.assertLess(MAP_LAYER_ORDER.index("marker"), MAP_LAYER_ORDER.index("bars"))
        self.assertLess(MAP_LAYER_ORDER.index("bars"), MAP_LAYER_ORDER.index("badge"))

    def test_required_and_literals(self) -> None:
        for bad in (dict(src=" "), dict(rows=[dict(name="가", col="dem", pct=50.0)]), dict(race="house"), dict(status="maybe"),
                    dict(code="TX"), dict(side="middle"), dict(rows=[dict(name="가", col="purple", pct=1.0)] * 2),
                    dict(rows=[dict(name="가", col="dem", pct=101.0)] * 2), dict(rows=[dict(name="가", col="dem", pct=1.0)] * 4)):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                BarsEvent.model_validate(ev(**bad))


class BarsRenderTest(unittest.TestCase):
    def _bar_len(self, a: np.ndarray, y: int, col: np.ndarray) -> int:
        row = a[y, :, :3][:, ::-1].astype(float) / 255
        return int((np.abs(row - col).sum(axis=1) < 0.12).sum())

    def test_bar_lengths_share_one_scale(self) -> None:
        """막대 길이 비 = pct 비(모든 주 같은 축척 — 다 자란 뒤)."""
        for theme in ("light", "dark"):
            with self.subTest(theme=theme):
                st = stage(theme)
                v = view(st)
                surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W_OUT, H_OUT)
                ctx = cairo.Context(surf)
                ctx.set_source_rgb(0.9, 0.9, 0.9)
                ctx.paint()
                R = types.SimpleNamespace(reserved=[])  # noqa: N806
                e = BarsEvent.model_validate(ev()).model_dump()
                draw_bars(ctx, R, v, 5.0, e)
                surf.flush()
                a = np.ndarray((H_OUT, W_OUT, 4), np.uint8, surf.get_data())
                (x0, y0, x1, y1), ok = bars_box(v, e)
                self.assertTrue(ok)
                self.assertEqual(R.reserved, [(x0, y0, x1, y1)])
                B = load_rules().bars  # noqa: N806
                lens = []
                for i, r in enumerate(e["rows"]):
                    cy = int(y0 + B.pad + i * B.row_h + B.row_h / 2)
                    lens.append(self._bar_len(a, cy, np.array(map_c(st, r["col"]))))
                bw = B.box_w - B.pad * 2 - B.name_w - B.pct_w
                self.assertAlmostEqual(lens[0], bw * 0.551, delta=2.0)
                self.assertAlmostEqual(lens[1], bw * 0.430, delta=2.0)

    def test_side_falls_back_inside_screen(self) -> None:
        st = stage()
        v = view(st, lon=-99.0, lat=31.5)
        e = ev(lon=-99.0 + 16.0 * (W_OUT / 2 - 20) / W_OUT)   # 앵커가 오른쪽 끝 20px 안 — right 는 화면 밖
        x, y = v.to_screen(*st.to_world(lon=e["lon"], lat=e["lat"]))
        self.assertAlmostEqual(y, H_OUT / 2, delta=1.0)   # 위도 = 메르카토르 월드 좌표로(무대 변환)
        self.assertGreater(x, W_OUT - 30)
        b, ok = bars_box(v, e)
        self.assertTrue(ok)
        self.assertLessEqual(b[2], W_OUT)
        self.assertLess(b[2], x)   # 왼쪽으로 옮겼다


class BarsChecksTest(unittest.TestCase):
    def test_clean(self) -> None:
        self.assertEqual(checks.bars_report([ev()], results(), None), [])

    def test_src_missing(self) -> None:
        self.assertTrue(any("[bars-src-missing]" in x for x in checks.bars_report([ev(src="")], results(), None)))

    def test_hold(self) -> None:
        self.assertTrue(any("[bars-hold]" in x for x in checks.bars_report([ev(t1=2.0)], results(), None)))

    def test_overlap_with_photo(self) -> None:
        ph = dict(type="photo", t0=3.0, t1=8.0)
        self.assertTrue(any("[bars-overlap]" in x for x in checks.bars_report([ev(), ph], results(), None)))

    def test_data_mismatch(self) -> None:
        for bad in (ev(rows=[dict(name="탈라리코", col="dem", pct=55.0), dict(name="팩스턴", col="rep", pct=43.0)]),
                    ev(rows=[dict(name="탈라리코", col="rep", pct=55.1), dict(name="팩스턴", col="rep", pct=43.0)]),
                    ev(rows=[dict(name="다른 이름", col="dem", pct=55.1), dict(name="팩스턴", col="rep", pct=43.0)]),
                    ev(status="counting")):
            with self.subTest(bad=bad["rows"][0]):
                self.assertTrue(any("[bars-data-mismatch]" in x for x in checks.bars_report([bad], results(), None)))
        self.assertTrue(any("[bars-data-mismatch]" in x for x in checks.bars_report([ev()], None, "파일 없음")))
        self.assertTrue(any("[bars-data-mismatch]" in x for x in checks.bars_report([ev()], results(names_ko=None, parties=None), None)))

    def test_name_clip(self) -> None:
        long = ev(rows=[dict(name="아주아주긴후보이름입니다", col="dem", pct=55.1), dict(name="팩스턴", col="rep", pct=43.0)])
        self.assertTrue(any("[bars-name-clip]" in x for x in checks.bars_report([long], None, "x")))

    def test_data_model_pairs(self) -> None:
        with self.assertRaises(ValidationError):
            results(parties=["rep", "dem"])   # 1위 = 승자 정당


class Admin1ModeTest(unittest.TestCase):
    def test_modes(self) -> None:
        L = load_rules().labels  # noqa: N806
        self.assertEqual(L.admin1_mode_default, "subtle")
        sub = L.admin1_modes["subtle"]   # v7.3 값(골든 불변)
        self.assertEqual((sub.below_w, sub.size, sub.font, sub.alpha, sub.halo, sub.halo_a, sub.cities), (8.5, 9.5, "sans", 0.42, 1.8, 0.8, None))
        self.assertEqual(stage().admin1_mode_name, "subtle")
        self.assertEqual(stage(admin1_labels="prominent").admin1_mode.size, 13)
        with self.assertRaises(StageError):
            stage(admin1_labels="loud")


if __name__ == "__main__":
    unittest.main()
