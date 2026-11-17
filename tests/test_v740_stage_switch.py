"""한 영상 안 렌더 무대 전환 — 지도(mercator) ↔ 스튜디오(studio) (v7.4.0 R9, 사용자 의견 UF-902 "꼭 굳이 뒤에 지도를 띄울 필요가 없는 씬이라면…").

- 규칙: rules stage.switch(전환 가능한 무대 짝)·skin.dip(밝은 암전) — strict 모델.
- 연출: 아일랜드 숏은 그때 렌더 무대가 화면 공간 무대일 때만(shot_roles), 지도 키는 지도 숏에서만(stage_keys), 전환점(stage_track).
- 실제 엔진 경로(합성 지도 자산 + studio_showcase 사본, 콘티 판 load_project → render_frame): 프레임마다 렌더 무대, 스튜디오 구간 차트 아일랜드,
  skin 영상의 dip 은 밝은 판, 지도 이벤트가 스튜디오 구간에 걸치면 오류(P6), 옛 지도 테마 + 스튜디오 = 오류, dip 없는 전환 = 연속성 위반.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import numpy as np
import yaml
from PIL import Image
from pydantic import ValidationError

import geo.prep_tiers as pt
from engine import project as EP
from engine import skin
from engine.assets import Assets
from engine.direction import Direction, DirectionError, build, rendered_stages, shot_roles, stage_at, stage_track
from engine.stage import MercatorStage, ym
from engine.style import FPS, SKIN, apply_palette
from engine.timebase import Timebase
from rules import load_rules
from schemas.rules_models import SkinDip, StageSwitchRules
from tests.test_direction_schema import _plan
from tests.test_v740_skin import showcase_project

T_IN, T_OUT = 20.0, 28.0   # 지도 → 스튜디오, 스튜디오 → 지도 (dip 한가운데)


def _ring(lon0: float, lat0: float, lon1: float, lat1: float) -> np.ndarray:
    return np.array([[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]], float)


class _SynthAssets(Assets):
    """지형 티어·지오메트리 = 합성(경도 40~56 땅, 그 동쪽 바다, 나라 AA·BB) — 저장소 밖 geo.prep 자산 없이 실제 load_project 경로."""

    def _load_geo(self, a: Path) -> None:
        lv = 6
        T = {"lon0": 40.0, "lat0": 15.0, "lon1": 70.0, "lat1": 40.0, "levels": [lv], "z": 5, "ppd": lv, "tiles": "synthetic"}  # noqa: N806
        h = int(round((ym(40.0) - ym(15.0)) * lv))
        tt = pt.terrain_theme(self.theme)
        base = np.empty((h, 30 * lv, 3), np.uint8)
        base[:] = pt.hexc(tt.sea_stops[0][1])
        base[:, : 16 * lv] = pt.hexc(tt.land_stops[0][1])
        self.tiers = {"W": T}
        self.base = {("W", lv): Image.fromarray(base)}
        rings = {"AA": [_ring(50, 25, 56, 31)], "BB": [_ring(40, 25, 50, 31)]}
        place = {"lon": 48.0, "lat": 27.0, "rank": 1, "pop": 1_000_000, "cap": True, "cap0": True, "ko": "가나시", "name": "Gana"}
        self.geo = {"coarse": rings, "fine": rings, "admin1": {}, "meta": {"AA": {"ko": "가나", "lx": 53.0, "ly": 29.0, "rank": 1}},
                    "places": [place], "roads": {k: {c: [] for c in ("motorway", "trunk", "primary")} for k in ("coarse", "fine")},
                    "rivers": {k: {"major": [], "minor": []} for k in ("coarse", "fine")}}
        self.plc = [place]
        self.plc_rank, self.plc_pop = np.array([1]), np.array([1_000_000])
        self.plc_cap, self.plc_cap0 = np.array([True]), np.array([True])


def _direction(raw: dict[str, Any], **over: Any) -> dict[str, Any]:
    """studio_showcase 연출(시간축 설정·시리즈) → 지정학 지도 주 무대 + 스튜디오 구간(차트 아일랜드) + 지도 복귀."""
    end = {"card": "end", "edge": "start", "off": 0.4}
    d = {k: v for k, v in raw.items() if k not in ("stage", "stage_reason", "opening_exempt", "events", "shots")}
    d.update(genre="geopolitics", stage="mercator", opening_exempt="R9 시험 — 합성 지도", shots=[
        {"at": 0, "mode": "cut", "dur": 0, "camera": {"lon": 50.0, "lat": 28.0, "w": 16}},
        {"at": T_IN, "mode": "dip", "stage": "studio", "camera": {}},
        {"at": T_IN, "mode": "cut", "dur": 0, "stage": "timeline", "camera": {"date": "2026-03-15", "w": 640}},
        {"at": T_OUT, "mode": "dip", "camera": {"lon": 52.0, "lat": 28.0, "w": 14}},
    ], events=[
        {"type": "country", "start": 0.2, "end": T_IN - 0.2, "codes": ["AA"], "col": "ru", "a": 0.1},
        {"type": "island", "kind": "chart", "box": "left", "start": T_IN + 0.6, "end": T_OUT - 0.6},
        {"type": "series", "start": T_IN + 0.7, "end": T_OUT - 0.7, "lane": "op", "series_id": "INTC_OP_Q", "style": "bars", "col": "gold",
         "accent": "latest"},
        {"type": "marker", "start": T_OUT + 0.3, "end": end, "lon": 53.0, "lat": 28.0, "label": "가나"},
    ])
    d.update(over)
    return d


class SwitchRulesTest(unittest.TestCase):
    def test_strict_models(self) -> None:
        self.assertEqual(load_rules().stage.switch.stages, ["mercator", "studio"])
        self.assertLessEqual(SKIN.dip.peak_alpha, 1.0)
        with self.assertRaises(ValidationError):
            StageSwitchRules.model_validate({"stages": ["mercator", "studio"], "x": 1})
        with self.assertRaises(ValidationError):
            SkinDip.model_validate({"peak_alpha": 1.2})

    def test_map_genres_list_studio_secondary(self) -> None:
        from genres.load import load_genre  # noqa: PLC0415

        for g in ("geopolitics", "political_history"):
            self.assertIn("studio", load_genre(g).stage.secondary)

    def test_grammar_rule_present(self) -> None:
        self.assertTrue(any("지도와 스튜디오를 오갈" in r and "dip" in r for r in load_rules().direction_grammar))


class DirectionSwitchTest(unittest.TestCase):
    """연출만(자산 없음) — 역할·트랙·키."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = yaml.safe_load((Path(__file__).resolve().parent.parent / "projects" / "studio_showcase" / "direction.yaml").read_text(encoding="utf-8"))

    def test_roles_track_keys(self) -> None:
        doc = Direction.model_validate(_direction(self.raw))
        self.assertEqual(shot_roles(doc), ["mercator", "studio", None, "mercator"])
        self.assertEqual(rendered_stages(doc), ["mercator", "studio"])
        tb = Timebase(_plan())
        tr = stage_track(doc, tb)
        self.assertEqual(tr, [(T_IN, "mercator", "studio"), (T_OUT, "studio", "mercator")])
        self.assertEqual([stage_at(tr, "mercator", t) for t in (0.0, T_IN - 0.01, T_IN, 24.0, T_OUT - 0.01, T_OUT, 40.0)],
                         ["mercator", "mercator", "studio", "studio", "studio", "mercator", "mercator"])
        keys, events, _ = build(doc, tb, MercatorStage())
        self.assertEqual([k.t for k in keys], [0.0, T_OUT])   # 지도 키는 지도 숏에서만 — 스튜디오 구간에 지도 카메라 키 없음
        self.assertEqual([(e["t0"], e["t1"]) for e in events if e["type"] == "dip"], [(T_IN - 0.5, T_IN + 0.5), (T_OUT - 0.5, T_OUT + 0.5)])

    def test_single_stage_roles_unchanged(self) -> None:
        """한 무대 영상 — studio 주 무대의 timeline 숏은 아일랜드(옛 판정 그대로), 트랙 없음."""
        doc = Direction.model_validate(self.raw)
        self.assertEqual(shot_roles(doc), ["studio", None])
        self.assertEqual(stage_track(doc, Timebase(_plan())), [])

    def test_unsupported_pair_is_error(self) -> None:
        doc = Direction.model_validate(_direction(self.raw, shots=[{"at": 0, "mode": "cut", "dur": 0, "camera": {"lon": 50.0, "lat": 28.0, "w": 16}},
                                                                    {"at": T_IN, "mode": "dip", "stage": "timeline",
                                                                     "camera": {"date": "2026-03-15", "w": 640}}]))
        with self.assertRaises(DirectionError):
            rendered_stages(doc)


class SwitchRenderTest(unittest.TestCase):
    """실제 load_project(콘티 판 — 권리 점검 없음) → render_frame."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = showcase_project(Path(cls.tmp.name) / "base")
        cls.raw = yaml.safe_load((cls.base / "direction.yaml").read_text(encoding="utf-8"))
        cls.P = cls._load(_direction(cls.raw), "main")

    @classmethod
    def tearDownClass(cls) -> None:
        skin.apply(None)
        cls.tmp.cleanup()

    def setUp(self) -> None:
        """skin 은 프로세스 전역(영상마다 load_project 가 켜고 끈다) — 다른 사본을 읽은 시험 뒤에도 주 사본 상태로."""
        skin.apply(self.P.R.stage.name, self.P.R.cache["skin"]["map_theme"])
        apply_palette(self.P.R.cache["palette"])

    @classmethod
    def _load(cls, d: dict[str, Any], name: str) -> Any:
        proj = Path(cls.tmp.name) / name
        if not proj.exists():
            shutil.copytree(cls.base, proj)
        (proj / "direction.yaml").write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
        with mock.patch.object(EP, "Assets", _SynthAssets):
            return EP.load_project(proj, animatic=True)

    def _frame(self, t: float) -> np.ndarray:
        from engine.render import render_frame  # noqa: PLC0415

        P = self.P  # noqa: N806
        _, buf = render_frame(P, int(round(t * FPS)))
        OP = P.R.out  # noqa: N806
        return np.frombuffer(bytes(buf), np.uint8).reshape(OP.height, OP.width, 4)[..., [2, 1, 0]].astype(float) / 255

    def test_loads_with_provenance(self) -> None:
        st = self.P.R.cache["stage"]
        self.assertEqual(st["name"], "mercator")
        self.assertEqual(st["switches"], [{"t": T_IN, "from": "mercator", "to": "studio"}, {"t": T_OUT, "from": "studio", "to": "mercator"}])
        self.assertEqual(st["instances"], {"mercator": 1, "studio": 1, "timeline": 1})
        self.assertTrue(skin.active())
        self.assertIsNotNone(self.P.R.cache.get("island_chart"))
        ev = {e["type"]: e.get("on_stage") for e in self.P.events if e["type"] in ("country", "marker", "island")}
        self.assertEqual(ev, {"country": "mercator", "marker": "mercator", "island": "studio"})

    def test_active_stage_per_frame(self) -> None:
        """스튜디오 구간 = 스튜디오 배경(지도 없음) + 차트 아일랜드, 지도 구간 = 지도. 렌더 뒤 R.stage 는 주 무대로 돌아온다."""
        from engine.stage_studio import StudioStage  # noqa: PLC0415

        studio_only = self._frame(24.0)
        self.assertEqual(self.P.R.stage.name, "mercator")
        map_frame = self._frame(5.0)
        self.assertGreater(np.abs(studio_only - map_frame).mean(), 0.01)
        self.assertIsInstance(self.P.R.cache["stage_switch"]["alt"]["studio"][0], StudioStage)
        before_island = self._frame(T_IN + 0.55)   # 아일랜드 전(dip 끝난 뒤) — 스튜디오 배경만
        self.assertGreater(np.abs(studio_only - before_island).max(), 0.3)   # 아일랜드가 그려졌다
        self.assertGreater(before_island.mean(), 0.85)   # 밝은 스튜디오(지도 땅·바다 아님)

    def test_dip_is_light_under_skin(self) -> None:
        for t in (T_IN, T_OUT):
            f = self._frame(t)
            self.assertGreater(f.mean(), 0.95, t)
            self.assertLess(np.abs(f.mean(axis=(0, 1)) - np.array(SKIN.fade_rgb)).max(), 0.03)

    def test_map_event_over_studio_is_error(self) -> None:
        d = _direction(self.raw)
        d["events"][0]["end"] = 24.0   # 나라 채움이 스튜디오 구간 안까지
        with self.assertRaises(EP.ProjectError) as cm:
            self._load(d, "span")
        self.assertIn("country", str(cm.exception))
        self.assertIn("studio", str(cm.exception))

    def test_island_on_map_is_error(self) -> None:
        d = _direction(self.raw)
        d["events"][1]["end"] = T_OUT + 3.0
        with self.assertRaises(EP.ProjectError) as cm:
            self._load(d, "isl")
        self.assertIn("island", str(cm.exception))

    def test_legacy_theme_with_studio_is_error(self) -> None:
        d = _direction(self.raw, stage_config={**self.raw["stage_config"], "mercator": {"theme": "light", "theme_reason": "R9 시험"}})
        with self.assertRaises(EP.ProjectError) as cm:
            self._load(d, "legacy")
        self.assertIn("skin", str(cm.exception))

    def test_switch_without_dip_fails_continuity(self) -> None:
        from engine.shots import stage_continuity  # noqa: PLC0415

        d = _direction(self.raw)
        d["shots"][1] = {"at": T_IN, "mode": "cut", "dur": 0, "stage": "studio", "camera": {}}
        P = self._load(d, "nodip")  # noqa: N806
        self.assertIn("switch_without_dip", [k for k, _ in stage_continuity(P.shots)])
        self.assertEqual(stage_continuity(self.P.shots), [])


if __name__ == "__main__":
    unittest.main()
