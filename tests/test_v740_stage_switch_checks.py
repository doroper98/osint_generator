"""무대 전환 영상(지도 ↔ 스튜디오, v7.4.0 R9·UF-902)의 검사 — 검사는 그 시각 화면에 그려진 무대만 본다(engine.stage_spans).

- (i)  지도 주 무대 → 스튜디오 30초 → 지도: 스튜디오 구간 동안 멈춰 있는 지도 카메라(바다 위)로 [sea-only-frame]·[static-camera]·
       [camera-continuity] 를 내지 않는다.
- (ii) 지도 구간 안의 진짜 정지 카메라(> rules camera.static_max_sec)는 그대로 [static-camera].
- (iii) 지도 주 무대 영상의 스튜디오 구간 안 아일랜드 겹침·자막 구역 침범은 [island-overlap](옛 판정은 지도 무대 규칙 — 패널만).
- (iv) 한 무대 영상 = 구간 하나(주 무대).
- 스튜디오 주 무대 + 지도 보조 무대: 읽기 · 무대마다 프레임 · 검사 전체가 돈다, 지도 구간 카메라 이동이 정지 판정에 들어간다.
"""

from __future__ import annotations

import copy
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import numpy as np
import yaml

from engine import checks
from engine import project as EP
from engine import skin
from engine.stage_spans import layer_stage_name, rendered_view, stage_name_at, stage_spans
from engine.style import FPS, ISLAND, SKIN, apply_palette
from rules import load_rules
from tests.test_v740_skin import SHOWCASE
from tests.test_v740_stage_switch import _SynthAssets

END = {"card": "end", "edge": "start", "off": 0.4}
SCALE = 3.0   # 문장 길이 배수 — 제목 카드 27.1~32.7초, 엔딩 카드 80.2초~(본문이 스튜디오 25초 이상을 담게)
LAND = {"lon": 50.0, "lat": 28.0, "w": 16}
SEA = {"lon": 64.0, "lat": 19.0, "w": 8}   # 아라비아해(합성 지형 범위 안) — 육지 비율 < camera.land_min_ratio


def _scaled_showcase(dst: Path) -> Path:
    """tests.test_v740_skin.showcase_project 와 같은 합성 plan(TTS 없음)을 문장 길이 SCALE 배로."""
    from script.plan import load_script  # noqa: PLC0415
    from script.schema import Plan  # noqa: PLC0415
    from script.timeline import layout, sentence_rows  # noqa: PLC0415
    from tests.test_g8_animatic import write_synthetic_alignment  # noqa: PLC0415

    shutil.copytree(SHOWCASE, dst, ignore=shutil.ignore_patterns("out", "tts", "plan.json", "assets", "__pycache__"))
    sc = load_script(dst)
    rows = sentence_rows(sc)
    for x in rows:
        x["mp3"] = str(dst / "tts" / f"{x['sid']}.mp3")
        x["npy"] = x["mp3"] + ".npy"
        x["dur"] = round((0.8 + 0.085 * len(x["text"])) * SCALE, 3)
        x["trim_offset"] = 0.0
    write_synthetic_alignment(rows)
    cards, ss, total = layout(rows)
    plan = Plan(sentences=rows, cards=cards, scene_start=ss, total=total, voice="synthetic", title=sc.title,
                subtitle=sc.subtitle, date=sc.date)
    (dst / "plan.json").write_text(plan.model_dump_json(), encoding="utf-8")
    return dst


def _series(t0: float, t1: float) -> dict[str, Any]:
    return {"type": "series", "start": t0, "end": t1, "lane": "op", "series_id": "INTC_OP_Q", "style": "bars", "col": "gold", "accent": "latest"}


def _island(t0: float, t1: float) -> dict[str, Any]:
    return {"type": "island", "kind": "chart", "box": "left", "start": t0, "end": t1}


def _map_main(raw: dict[str, Any], t_in: float, t_out: float, first: dict[str, Any], allow_sea: bool) -> dict[str, Any]:
    """지도 주 무대 → (t_in) 스튜디오(차트 아일랜드 둘 — 새 요소가 static_max_sec 안에 나온다) → (t_out) 지도."""
    d = {k: v for k, v in raw.items() if k not in ("stage", "stage_reason", "opening_exempt", "events", "shots")}
    s0: dict[str, Any] = {"at": 0, "mode": "cut", "dur": 0, "camera": dict(first)}
    if allow_sea:
        s0["allow_sea"] = "R9 시험 — 바다 구도(전환 전 지도 숏만)"
    mid = (t_in + t_out) / 2
    d.update(genre="geopolitics", stage="mercator", opening_exempt="R9 시험 — 합성 지도", shots=[
        s0,
        {"at": t_in, "mode": "dip", "stage": "studio", "camera": {}},
        {"at": t_in, "mode": "cut", "dur": 0, "stage": "timeline", "camera": {"date": "2026-03-15", "w": 500}},
        {"at": t_out, "mode": "dip", "camera": {"lon": 52.0, "lat": 28.0, "w": 14}},
    ], events=[
        {"type": "country", "start": 0.2, "end": t_in - 0.6, "codes": ["AA"], "col": "ru", "a": 0.1},
        {"type": "marker", "start": 12.0, "end": t_in - 0.6, "lon": first["lon"], "lat": first["lat"], "label": "가나"},
        _island(t_in + 0.6, mid), _island(mid + 0.2, t_out - 0.6), _series(t_in + 0.7, t_out - 0.7),
        {"type": "marker", "start": t_out + 0.3, "end": END, "lon": 53.0, "lat": 28.0, "label": "가나"},
    ])
    return d


def _studio_main(raw: dict[str, Any], t_in: float, t_out: float) -> dict[str, Any]:
    """스튜디오 주 무대(차트 아일랜드) → (t_in) 지도 보조 무대(이동 숏 하나) → (t_out) 스튜디오."""
    d = {k: v for k, v in raw.items() if k not in ("events", "shots", "opening_exempt")}
    d.update(shots=[
        {"at": 0, "mode": "cut", "dur": 0, "camera": {}},
        {"at": 0, "mode": "cut", "dur": 0, "stage": "timeline", "camera": {"date": "2026-03-15", "w": 500}},
        {"at": t_in, "mode": "dip", "stage": "mercator", "camera": dict(LAND)},
        {"at": t_in + 12.0, "mode": "move", "dur": 4.0, "stage": "mercator", "camera": {"lon": 52.0, "lat": 27.0, "w": 12}},
        {"at": t_out, "mode": "dip", "stage": "studio", "camera": {}},
    ], events=[
        _island(0.2, t_in - 0.6), _series(0.3, t_in - 0.7),
        {"type": "marker", "start": t_in + 0.6, "end": t_out - 0.6, "lon": 53.0, "lat": 28.0, "label": "가나"},
    ])
    return d


class _Base(unittest.TestCase):
    tmp: tempfile.TemporaryDirectory
    base: Path
    raw: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.base = _scaled_showcase(Path(cls.tmp.name) / "base")
        cls.raw = yaml.safe_load((cls.base / "direction.yaml").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        skin.apply(None)
        apply_palette(None)
        cls.tmp.cleanup()

    @classmethod
    def _load(cls, d: "dict[str, Any] | None", name: str) -> Any:
        proj = Path(cls.tmp.name) / name
        shutil.copytree(cls.base, proj)
        if d is not None:
            (proj / "direction.yaml").write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
        with mock.patch.object(EP, "Assets", _SynthAssets):
            return EP.load_project(proj, animatic=True)

    @staticmethod
    def _activate(P: Any) -> None:  # noqa: N803
        """skin 은 프로세스 전역 — 검사·렌더 전에 이 영상 상태로."""
        sk = P.R.cache.get("skin") or {}
        skin.apply(P.R.stage.name, sk.get("map_theme"))
        apply_palette(P.R.cache["palette"])


class MapMainSwitchTest(_Base):
    T_IN, T_OUT = 40.0, 70.0   # 스튜디오 30초

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.P = cls._load(_map_main(cls.raw, cls.T_IN, cls.T_OUT, SEA, allow_sea=True), "clean")

    def setUp(self) -> None:
        self._activate(self.P)

    def test_spans_follow_render_frame(self) -> None:
        P = self.P  # noqa: N806
        self.assertEqual([(a, b, n) for a, b, n in stage_spans(P)],
                         [(0.0, self.T_IN, "mercator"), (self.T_IN, self.T_OUT, "studio"), (self.T_OUT, P.plan.total, "mercator")])
        self.assertEqual(layer_stage_name(P), "mercator")
        for t in (5.0, self.T_IN, 55.0, self.T_OUT - 1.0 / FPS, self.T_OUT, 75.0):
            self.assertEqual(rendered_view(P, t).stage.name, stage_name_at(P, t))
        self.assertEqual(stage_name_at(P, 55.0), "studio")

    def test_no_findings_from_parked_map_camera(self) -> None:
        """스튜디오 구간의 지도 카메라 = 바다 위에 멈춤(allow_sea 는 그 숏 구간 = 전환 전까지) — 화면에 지도가 없으니 판정하지 않는다."""
        P = self.P  # noqa: N806
        self.assertEqual(checks.check_sea_only(P), [])
        self.assertEqual(checks.check_static_camera(P), [])
        self.assertEqual(checks.check_camera_continuity(P), [])
        self.assertEqual(checks.check_camera_bounds(P), [])
        self.assertTrue(all(t < self.T_IN or t >= self.T_OUT for t, _ in checks.land_ratios(P)))

    def test_run_checks_no_stage_findings(self) -> None:
        with mock.patch.object(checks, "profile_skips", lambda P: set()):  # noqa: N803
            res = checks.run_checks(self.P, [5.0, 55.0, 75.0], {}, [])
        by = {i["id"]: i for i in res["items"]}
        for cid in ("static_camera", "sea_only_frame", "camera_continuity", "camera_speed", "camera_bounds", "island_overlap", "labels"):
            self.assertEqual(by[cid]["count"], 0, (cid, by[cid]["details"]))

    def test_island_overlap_inside_studio_span(self) -> None:
        """(iii) 스튜디오 구간 = 화면 공간 무대 규칙(아일랜드·패널 상자) — 옛 판정(지도 skin = 패널만)은 놓쳤다."""
        P2 = copy.copy(self.P)  # noqa: N806
        P2.events = self.P.events + [{"type": "panel", "kind": "dots", "title": "겹침", "t0": 45.0, "t1": 50.0}]
        lines = checks.check_island_overlap(P2)
        self.assertTrue(any("island chart left" in s and "panel dots" in s for s in lines), lines)
        P3 = copy.copy(self.P)  # noqa: N806
        P3.events = self.P.events + [{"type": "island", "kind": "chart", "box": "low", "t0": 58.0, "t1": 60.0}]
        with mock.patch.dict(ISLAND.boxes, {"low": (94.0, 300.0, 666.0, 150.0)}):
            lines = checks.check_island_overlap(P3)
        self.assertTrue(any("자막 구역" in s and "t=58.00" in s for s in lines), lines)
        P4 = copy.copy(self.P)  # noqa: N806 — 같은 패널이 지도 구간이면 스튜디오 아일랜드와 겹칠 일이 없다
        P4.events = self.P.events + [{"type": "panel", "kind": "dots", "title": "지도", "t0": 33.0, "t1": 38.0}]
        self.assertEqual(checks.check_island_overlap(P4), [])


class MapSpanViolationTest(_Base):
    T_IN, T_OUT = 55.0, 79.0

    def test_static_map_before_switch_reported(self) -> None:
        """(ii) 제목 카드 끝(32.7초) ~ 전환 dip(54.5초) 지도 카메라 정지 + 새 요소 없음 > static_max_sec — 그대로 [static-camera]."""
        P = self._load(_map_main(self.raw, self.T_IN, self.T_OUT, LAND, allow_sea=False), "static")  # noqa: N806
        self._activate(P)
        lines = checks.check_static_camera(P)
        lim = load_rules().camera.static_max_sec
        self.assertEqual(len(lines), 1, lines)
        a, b = (float(x) for x in lines[0].split()[1].split("초")[0].split("~"))
        self.assertGreaterEqual(a, 32.0)
        self.assertLessEqual(b, self.T_IN)
        self.assertGreaterEqual(b - a, lim)


class StudioMainMapSecondaryTest(_Base):
    """스튜디오 주 무대 + 지도 보조 무대(처음 시험되는 조합) — 읽기·무대마다 프레임·검사."""

    T_IN, T_OUT = 40.0, 70.0

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.P = cls._load(_studio_main(cls.raw, cls.T_IN, cls.T_OUT), "studio_main")

    def setUp(self) -> None:
        self._activate(self.P)

    def test_loads_and_renders_each_stage(self) -> None:
        from engine.render import render_frame  # noqa: PLC0415

        P = self.P  # noqa: N806
        self.assertEqual(P.R.stage.name, "studio")
        self.assertEqual(layer_stage_name(P), "mercator")
        self.assertEqual([n for _a, _b, n in stage_spans(P)], ["studio", "mercator", "studio"])
        ev = {e["type"]: e.get("on_stage") for e in P.events if e["type"] in ("marker", "island")}
        self.assertEqual(ev, {"marker": "mercator", "island": "studio"})
        OP = P.R.out  # noqa: N806
        frames = {}
        for t in (20.0, 50.0):
            _, buf = render_frame(P, int(round(t * FPS)))
            frames[t] = np.frombuffer(bytes(buf), np.uint8).reshape(OP.height, OP.width, 4)[..., [2, 1, 0]].astype(float) / 255
        self.assertEqual(P.R.stage.name, "studio")   # 렌더 뒤 주 무대로 돌아온다
        self.assertGreater(np.abs(frames[20.0] - frames[50.0]).mean(), 0.01)
        self.assertLess(np.abs(frames[20.0].mean(axis=(0, 1)) - np.array(SKIN.fade_rgb)).max(), 0.2)   # 스튜디오 = 밝은 바탕

    def test_checks_run_and_map_span_moves(self) -> None:
        """지도 구간 카메라 이동(이동 숏)이 정지 판정에 들어간다 — 옛 판정(주 무대 = 고정 스튜디오 카메라)은 지도 구간을 정지로 봤다."""
        P = self.P  # noqa: N806
        self.assertEqual(checks.check_static_camera(P), [])
        with mock.patch.object(checks, "profile_skips", lambda P: set()):  # noqa: N803
            res = checks.run_checks(P, [20.0, 50.0], {}, [])
        by = {i["id"]: i for i in res["items"]}
        for cid in ("static_camera", "sea_only_frame", "camera_continuity", "camera_speed"):
            self.assertEqual(by[cid]["count"], 0, (cid, by[cid]["details"]))


class SingleStageSpanTest(_Base):
    def test_one_span(self) -> None:
        """(iv) 한 무대 영상(스튜디오 주 무대) — 구간 하나, 지도 층 무대 = 주 무대."""
        P = self._load(None, "single")  # noqa: N806
        self.assertEqual(stage_spans(P), [(0.0, P.plan.total, "studio")])
        self.assertEqual(layer_stage_name(P), "studio")
        self.assertEqual(stage_name_at(P, 30.0), "studio")
        self.assertIs(rendered_view(P, 30.0).stage, P.R.stage)


if __name__ == "__main__":
    unittest.main()
