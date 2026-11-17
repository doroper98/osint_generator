"""v7.4.0 UF-900 R2·UF-901(D904) — country 이벤트 국기 채움(fill: flag, 레퍼런스 실측 benchmark_wartech_2026-11-17.md §2.3·§2.7).

- 스키마: fill flag = flag 필수·col·a 금지, fill color = col·a 필수·flag 금지. 단색 채움 dict 는 옛 모양 그대로(fill 칸 없음).
- 규칙 블록 rules flag_fill 이 로드되고 strict(모르는 키 = 오류).
- 예제(prompts/examples/events/country_flag.yaml) = 프리뷰 예제(tests/fixtures/preview/country_flag.yaml), 모델 통과(15 P4).
- 국기 파일이 없으면 파일 경로를 밝힌 오류(단색으로 대신 칠하지 않는다, P6). 렌더 전 점검(preflight)은 4:3 국기를 찾는다.
- UF-901(사용자 원문 "분쟁지역 국기 채움은 내가 허용한다. 받아들여."): 대만·여러 나라 합집합 국기 채움이 통과하고 막는 검사가 없다.
- 합성 무대(네트워크 자산 없음) 렌더: 나라 안은 국기 색 × 지형, 윤곽은 흰색, 등장 중에는 더 어둡다. 같은 입력 = 같은 바이트.
"""

from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path

import cairo
import numpy as np
import pydantic
from PIL import Image

from engine.assets import AssetError, Assets
from engine.events import CountryEvent
from engine.layers.areas import draw_country
from engine.layers.flag_fill import FlagFillError
from engine.projection import View
from engine.registry import validate_events
from engine.stage import MercatorStage, ym
from rules import load_rules
from schemas.rules_models import FlagFillRules

REPO = Path(__file__).resolve().parent.parent
COLOR = {"type": "country", "t0": 1.0, "t1": 9.0, "codes": ["IR"], "col": "ru", "a": 0.07}
FLAG = {"type": "country", "t0": 1.0, "t1": 9.0, "codes": ["IR"], "fill": "flag", "flag": "ir"}


class FlagFillSchemaTest(unittest.TestCase):
    def test_color_dict_unchanged(self) -> None:
        self.assertEqual(validate_events([COLOR]), [{"type": "country", "t0": 1.0, "t1": 9.0, "codes": ["IR"], "col": "ru", "a": 0.07}])
        self.assertEqual(validate_events([{**COLOR, "fill": "color"}]), validate_events([COLOR]))

    def test_flag_dict(self) -> None:
        self.assertEqual(validate_events([FLAG]), [{"type": "country", "t0": 1.0, "t1": 9.0, "codes": ["IR"], "fill": "flag", "flag": "ir"}])

    def test_rules(self) -> None:
        bad = [{**FLAG, "flag": None}, {**FLAG, "col": "ru"}, {**FLAG, "a": 0.5},
               {k: v for k, v in COLOR.items() if k != "col"}, {k: v for k, v in COLOR.items() if k != "a"},
               {**COLOR, "flag": "ir"}, {**FLAG, "fill": "pattern"}]
        for d in bad:
            with self.subTest(d=d), self.assertRaises(pydantic.ValidationError):
                CountryEvent.model_validate(d)

    def test_examples_match_and_validate(self) -> None:
        import yaml  # noqa: PLC0415

        a = yaml.safe_load((REPO / "prompts/examples/events/country_flag.yaml").read_text(encoding="utf-8"))["event"]
        b = yaml.safe_load((REPO / "tests/fixtures/preview/country_flag.yaml").read_text(encoding="utf-8"))["event"]
        self.assertEqual(a, b)
        self.assertEqual(validate_events([a])[0]["fill"], "flag")
        old = yaml.safe_load((REPO / "tests/fixtures/preview/country.yaml").read_text(encoding="utf-8"))["event"]
        self.assertNotIn("fill", validate_events([old])[0])   # 기존 예제 = 옛 dict


class FlagFillRulesTest(unittest.TestCase):
    def test_loads(self) -> None:
        ff = load_rules().flag_fill
        self.assertIsInstance(ff, FlagFillRules)
        self.assertTrue(ff.shade.lo <= ff.shade.base <= ff.shade.hi)
        self.assertLess(ff.rise.brightness_from, 1)

    def test_strict(self) -> None:
        d = load_rules().flag_fill.model_dump()
        with self.assertRaises(pydantic.ValidationError):
            FlagFillRules.model_validate({**d, "vignette": True})


class DisputedNotBlockedTest(unittest.TestCase):
    """UF-901 — 분쟁 지역 국기 채움을 막는 검사를 두지 않는다(사용자 결정 D904)."""

    def test_validates(self) -> None:
        evs = validate_events([{**FLAG, "codes": ["TW"], "flag": "tw"}, {**FLAG, "codes": ["RU", "UA"], "flag": "ru"},
                               {**FLAG, "codes": ["MA", "EH"], "flag": "ma"}])
        self.assertEqual(len(evs), 3)

    def test_no_check_on_flag_fill(self) -> None:
        from engine.checks import check_flag_territory  # noqa: PLC0415

        st = MercatorStage.__new__(MercatorStage)
        evs = validate_events([{**FLAG, "codes": ["TW"], "flag": "tw"}, {**FLAG, "codes": ["RU", "UA"], "flag": "ru"}])
        P = types.SimpleNamespace(events=evs, R=types.SimpleNamespace(stage=st, cache={}))  # noqa: N806
        self.assertEqual(check_flag_territory(P), [])
        src = (REPO / "engine" / "checks.py").read_text(encoding="utf-8")
        for needle in ('"fill"', "flag_fill", "disputed", "분쟁"):
            self.assertNotIn(needle, src, f"engine.checks 가 국기 채움·분쟁 지역을 본다({needle}) — UF-901 위반")


def _ring(lon0: float, lat0: float, lon1: float, lat1: float) -> np.ndarray:
    return np.array([[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]], dtype=float)


class FlagFillRenderTest(unittest.TestCase):
    """합성 무대 — 나라 AA(정사각 본토 + 섬), 이웃 BB. 지형 = 결정적 잡음 회색. 설계 해상도(854×480, k=1)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        (root / "assets" / "flags").mkdir(parents=True)
        fl = np.zeros((90, 120, 3), np.uint8)
        fl[:30] = (0, 160, 60)
        fl[30:60] = (255, 255, 255)
        fl[60:] = (220, 0, 0)
        Image.fromarray(fl).save(root / "assets" / "flags" / "aa_4x3.png")
        A = Assets(root, types.SimpleNamespace(seas=[]), geo=False)  # noqa: N806
        lv = 6
        T = {"lon0": 40.0, "lat0": 15.0, "lon1": 70.0, "lat1": 40.0, "levels": [lv], "z": 5}  # noqa: N806
        h = int(round((ym(40.0) - ym(15.0)) * lv))
        g = np.random.default_rng(7).normal(0, 1, (h, 30 * lv)).cumsum(axis=1)
        g = 90 + 25 * (g - g.mean()) / g.std()
        A.tiers = {"W": T}
        A.base = {("W", lv): Image.fromarray(np.repeat(np.clip(g, 0, 255).astype(np.uint8)[..., None], 3, axis=2))}
        rings = {"AA": [_ring(50, 25, 56, 31), _ring(57, 23.5, 57.6, 24.1)], "BB": [_ring(44, 25, 50, 31)]}
        A.geo = {"coarse": rings, "fine": rings, "admin1": {}, "meta": {}, "places": [],
                 "roads": {lod_: {c: [] for c in ("motorway", "trunk", "primary")} for lod_ in ("coarse", "fine")},
                 "rivers": {lod_: {"major": [], "minor": []} for lod_ in ("coarse", "fine")}}
        A.theme = "slate"
        cls.A = A
        cls.st = MercatorStage(A, config={"theme": "slate", "theme_reason": "시험"})
        cls.view = View(cls.st, np.array([53.0, ym(27.0), 24.0]))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def _render(self, e: dict, t: float) -> np.ndarray:
        buf = bytearray(854 * 480 * 4)
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, 854, 480, 854 * 4)
        ctx = cairo.Context(surf)
        self.st.render_base(ctx, self.view)
        draw_country(ctx, types.SimpleNamespace(assets=self.A, cache={}), self.view, t, e)
        surf.flush()
        return np.frombuffer(bytes(buf), np.uint8).reshape(480, 854, 4)[..., [2, 1, 0]].astype(int)

    def _px(self, lon: float, lat: float) -> tuple[int, int]:
        x, y = self.view.to_screen(lon, ym(lat))
        return int(y), int(x)

    def _ev(self, **kw: object) -> dict:
        return validate_events([{**FLAG, "codes": ["AA"], "flag": "aa", **kw}])[0]

    def test_bands_and_outline(self) -> None:
        im = self._render(self._ev(), 5.0)
        top, mid, bot = im[self._px(53, 30.3)], im[self._px(53, 28)], im[self._px(53, 25.7)]
        self.assertGreater(top[1], top[0] + 40)                      # 위 = 녹색
        self.assertTrue(abs(mid[0] - mid[1]) < 12 and mid[0] > 110)  # 가운데 = 흰색(지형에 눌림)
        self.assertGreater(bot[0], bot[1] + 60)                      # 아래 = 빨강
        self.assertLess(mid.max(), 255)                              # 지형 음영이 곱해진다(base < 1)
        r, c = self._px(56, 28)
        self.assertGreater(im[r, c - 2:c + 3].min(axis=1).max(), 230)   # 흰 윤곽
        r, c = self._px(53, 28)
        self.assertGreater(im[r - 30:r + 30, c + 40:c + 100].std(), 4)   # 지형이 비친다(흰 띠 안 휘도 변화)

    def test_fade_in_darker(self) -> None:
        e = self._ev()
        full = self._render(e, 5.0)[self._px(53, 28)].sum()
        early = self._render(e, e["t0"] + load_rules().transition.element["country"][0] * 0.35)[self._px(53, 28)].sum()
        self.assertLess(early, full)

    def test_deterministic(self) -> None:
        e = self._ev()
        self.assertEqual(self._render(e, 4.2).tobytes(), self._render(e, 4.2).tobytes())

    def test_color_path_still_draws(self) -> None:
        base = self._render(validate_events([{**COLOR, "codes": ["AA"], "a": 0.0}])[0], 5.0)
        col = self._render(validate_events([{**COLOR, "codes": ["AA"]}])[0], 5.0)
        self.assertFalse(np.array_equal(base, col))

    def test_missing_flag_raises(self) -> None:
        with self.assertRaises(AssetError) as cm:
            self._render(self._ev(flag="zz"), 5.0)
        self.assertIn("zz_4x3.png", str(cm.exception))

    def test_unknown_code_raises(self) -> None:
        with self.assertRaises(FlagFillError):
            self._render(self._ev(codes=["QQ"]), 5.0)

    def test_preflight_wants_4x3(self) -> None:
        from engine.project import preflight  # noqa: PLC0415

        errs = preflight(types.SimpleNamespace(assets=self.A), [self._ev(flag="zz")])
        self.assertTrue(any("zz_4x3.png" in x for x in errs), errs)
        self.assertFalse(any("zz_1x1.png" in x for x in errs), errs)
        self.assertEqual(preflight(types.SimpleNamespace(assets=self.A), [self._ev()]), [])


if __name__ == "__main__":
    unittest.main()
