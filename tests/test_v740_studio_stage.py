"""v7.4.0 UF-902·UF-903(D910) — 스튜디오 무대 `studio`(engine/stage_studio.py) + 사용자 지시 2026-11-17(공간의 느린 흐름).

- 레지스트리 세 곳: rules registries.stages ↔ engine.stage.STAGE_CLASSES ↔ 프리뷰 예제(tests/fixtures/preview/stage_studio.yaml).
- rules stage_studio 는 엄격(모르는 키 = 오류), 조명은 더하기만(amp < 0 = 오류 — 비네팅 아님). stage_config·앵커 = 오류, 시각 없는 그리기 = 오류(P6).
- 배경: 같은 t = 같은 바이트, 1초 뒤 = 다름(공간이 흐른다), 30 fps 한 프레임 이동 < 1 장치 px(튀지 않음), 흐름은 전역 t 의 함수(숏 카메라와 무관).
- 밝기: 바닥 카메라 쪽 < 모서리 쪽, 벽 빛 웅덩이 > 벽 모서리, 네 귀퉁이 ≥ 바탕 톤 하한(가장자리 어둡게 없음 — C0), 평균 = 밝은 회색(흰색 아님).
- 점: 있고, 멀수록 작다. 흐름 진폭은 rules 에서(0 이면 멈춘다).
- 실제 엔진 경로(합성 사본 + 콘티 판 load_project): studio 주 무대 + 차트 아일랜드가 뜨고, 내용물 카메라는 고정, 사진 배경 검사는 하나도 걸리지 않는다.
  backdrop 이벤트를 studio 에 쓰면 분명한 오류.
"""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

import cairo
import numpy as np
import yaml
from pydantic import ValidationError

from engine.projection import View
from engine.stage import STAGE_CLASSES, make_stage, photo_stage, screen_stage, stage_class
from engine.stage_studio import StudioError, StudioStage, drift_at, tone_of
from engine.style import FPS, H_OUT, STUDIO, W_OUT
from rules import load_rules
from schemas.rules_models import StageStudioRules
from tests.anti_inertia._ast_util import REPO

PREVIEW = REPO / "tests" / "fixtures" / "preview"
K_1080 = 1080 / H_OUT


def _render(st: StudioStage, t: float, w: int = W_OUT, h: int = H_OUT) -> np.ndarray:
    """무대 배경만 장치 크기 w×h 로(렌더 진입과 같은 변환) → RGB 0~1."""
    k = h / H_OUT
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    c = cairo.Context(s)
    if k != 1:
        c.translate((w - W_OUT * k) / 2, 0)
        c.scale(k, k)
    st.render_base(c, View(st, np.array([W_OUT / 2, H_OUT / 2, W_OUT]), t=t))
    s.flush()
    return np.frombuffer(bytes(s.get_data()), np.uint8).reshape(h, s.get_stride() // 4, 4)[:, :w, 2::-1] / 255.0


def _dot_xy(st: StudioStage, t: float, j: int) -> tuple[float, float]:
    """점 줄 j 의 가운데 열(x = 0 m) 점 화면 위치(설계 px)."""
    cam = drift_at(t)
    y2, z2 = st._cam_space(cam, st._dot_y[j:j + 1], st._dot_z[j:j + 1])
    f = st._f_px()
    return W_OUT / 2 + f * (0.0 - cam[0]) / z2[0], H_OUT / 2 - f * y2[0] / z2[0]


def _nearest_row(st: StudioStage, t: float) -> int:
    """화면 안에 보이는 가장 가까운 점 줄 번호."""
    cam = drift_at(t)
    y2, z2 = st._cam_space(cam, st._dot_y, st._dot_z)
    f = st._f_px()
    return min((d, j) for j, (yy, d) in enumerate(zip(y2, z2)) if d > 0 and 0 <= H_OUT / 2 - f * yy / d <= H_OUT)[1]


class RegistryTest(unittest.TestCase):
    def test_three_places(self) -> None:
        self.assertIn("studio", load_rules().registries.stages)
        self.assertIs(STAGE_CLASSES["studio"], StudioStage)
        self.assertIs(stage_class("studio"), StudioStage)
        self.assertEqual(sorted(load_rules().registries.stages), sorted(STAGE_CLASSES))
        ex = yaml.safe_load((PREVIEW / "stage_studio.yaml").read_text(encoding="utf-8"))
        self.assertEqual((ex["key"], ex["anchor_keys"]), ("studio", []))

    def test_screen_and_photo_stage_flags(self) -> None:
        self.assertEqual([screen_stage(n) for n in ("backdrop", "studio", "mercator", "timeline", "structure")], [True, True, False, False, False])
        self.assertEqual([photo_stage(n) for n in ("backdrop", "studio", "mercator")], [True, False, False])

    def test_config_and_anchor_rejected(self) -> None:
        with self.assertRaises(StudioError):
            make_stage("studio", config={"theme": "dark"})
        st = make_stage("studio")
        self.assertEqual(st.to_world(), (W_OUT / 2, H_OUT / 2))
        with self.assertRaises(StudioError):
            st.to_world(lon=1.0, lat=2.0)

    def test_no_time_is_error(self) -> None:
        st = make_stage("studio")
        s = cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT)
        with self.assertRaises(StudioError):
            st.render_base(cairo.Context(s), View(st, np.array([W_OUT / 2, H_OUT / 2, W_OUT])))


class RulesTest(unittest.TestCase):
    def test_strict_block(self) -> None:
        raw = load_rules().stage_studio.model_dump()
        StageStudioRules.model_validate(raw)
        with self.assertRaises(ValidationError):
            StageStudioRules.model_validate({**raw, "theme": "dark"})          # 테마·변형 없음(UF-903)
        with self.assertRaises(ValidationError):
            StageStudioRules.model_validate({**raw, "light_pool": {**raw["light_pool"], "amp": -0.05}})   # 조명은 더하기만(비네팅 아님)

    def test_drift_from_rules(self) -> None:
        d = STUDIO.drift
        for t in (0.0, 3.7, 41.0, 100.0):
            x, y, z = drift_at(t)
            self.assertAlmostEqual(x, d.truck_m * math.sin(math.tau * t / d.truck_period_sec + math.radians(d.truck_phase_deg)))
            self.assertAlmostEqual(z, STUDIO.camera.z_m + d.dolly_m * math.sin(math.tau * t / d.dolly_period_sec + math.radians(d.dolly_phase_deg)))
            self.assertAlmostEqual(y, STUDIO.camera.height_m + d.rise_m * math.sin(math.tau * t / d.rise_period_sec + math.radians(d.rise_phase_deg)))
        still = d.model_copy(update={"truck_m": 0.0, "dolly_m": 0.0, "rise_m": 0.0})
        object.__setattr__(STUDIO, "drift", still)   # 규칙 모델은 frozen — 시험 안에서만 바꿨다 되돌린다
        try:
            st = StudioStage()
            self.assertTrue(np.array_equal(_render(st, 0.0), _render(st, 7.0)))   # 진폭 0 = 멈춘 공간(값은 rules 에서만)
        finally:
            object.__setattr__(STUDIO, "drift", d)


class BackgroundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.st = StudioStage()
        cls.img = _render(cls.st, 12.0)

    def test_deterministic_same_t(self) -> None:
        self.assertTrue(np.array_equal(self.img, _render(StudioStage(), 12.0)))
        self.assertTrue(np.array_equal(_render(self.st, 12.0, 1920, 1080), _render(StudioStage(), 12.0, 1920, 1080)))

    def test_space_moves(self) -> None:
        self.assertGreater(np.abs(self.img - _render(self.st, 13.0)).max(), 0.05)

    def test_smooth_motion(self) -> None:
        """가까운 바닥 점의 한 프레임 이동(1080p 장치 px) < 1 — 24·30 fps, 240초 훑기. 흐름은 전역 t 의 연속 함수."""
        for fps in (FPS, 30):
            worst = 0.0
            for k in range(0, 240 * fps, fps // 3):
                j = _nearest_row(self.st, k / fps)   # 같은 점(같은 줄·열)을 두 프레임에서 잰다
                a, b = _dot_xy(self.st, k / fps, j), _dot_xy(self.st, (k + 1) / fps, j)
                worst = max(worst, math.hypot(b[0] - a[0], b[1] - a[1]) * K_1080)
            self.assertLess(worst, 1.0, fps)
            self.assertGreater(worst, 0.1, fps)   # 그래도 움직인다

    def test_independent_of_content_camera(self) -> None:
        """배경은 전역 t 만의 함수 — 숏(내용물) 카메라가 바뀌어도 같은 t 면 같은 배경(무대를 오가도 흐름이 이어진다)."""
        s1 = cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT)
        s2 = cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT)
        self.st.render_base(cairo.Context(s1), View(self.st, np.array([100.0, 50.0, 400.0]), t=5.5))
        self.st.render_base(cairo.Context(s2), View(self.st, np.array([W_OUT / 2, H_OUT / 2, W_OUT]), t=5.5))
        self.assertEqual(bytes(s1.get_data()), bytes(s2.get_data()))

    def test_luminance_profile(self) -> None:
        bg = self.st.background(12.0)[..., 0]
        col = bg[:, bg.shape[1] // 2]
        tn = STUDIO.tone
        rows = np.arange(len(col))
        fillet_row = int(np.argmax(np.where(rows > len(col) // 3, col, 0)))   # 바닥 위쪽 끝(모서리 앞) 밝은 띠
        self.assertLess(col[-1], col[fillet_row] - 0.03)                      # 바닥 카메라 쪽 < 모서리 쪽
        top = bg[: len(col) // 3]
        self.assertGreater(top[:, top.shape[1] // 2].max(), top[0, 0] + 0.03)   # 벽 빛 웅덩이 > 벽 모서리
        img = self.img.mean(-1)
        floor = min(tn.floor_near, tn.floor_fillet - tn.fillet_dip - tn.wall_top_drop) - 0.01
        for y, x in ((0, 0), (0, -1), (-1, 0), (-1, -1)):                    # 가장자리 어둡게(비네팅) 없음 — 귀퉁이 ≥ 바탕 톤 하한
            self.assertGreaterEqual(float(img[y, x]), floor, (y, x))
        self.assertTrue(0.78 < float(img.mean()) < 0.9, float(img.mean()))   # 밝은 회색(흰색 아님)
        self.assertAlmostEqual(float(self.img[..., 2].mean() / self.img[..., 0].mean()), tn.blue_gain, delta=0.004)   # 아주 약한 따뜻한 기
        self.assertTrue(np.all(np.diff(tone_of(np.linspace(*STUDIO.arc_range_m, 50))[:10]) > 0))

    def test_dots_present_and_shrink(self) -> None:
        rows = self.st.dots(12.0)
        self.assertGreater(sum(len(r[3]) for r in rows), 1000)
        inside = [r for r in rows if 0 <= r[0] <= H_OUT - 4]
        near, far = max(inside, key=lambda r: r[0]), min(inside, key=lambda r: r[0])   # 화면 아래 = 가까운 바닥, 위 = 벽
        self.assertGreater(near[1], far[1])
        self.assertGreater(near[2], far[2])
        img = _render(self.st, 12.0, 1920, 1080).mean(-1)
        y = int(round(near[0] * K_1080))
        x = int(round(near[3][len(near[3]) // 2] * K_1080 + (1920 - W_OUT * K_1080) / 2))
        self.assertLess(float(img[y, x]), float(img[y, x + 20]) - 0.1)   # 점이 실제로 찍혔다

    def test_wall_moves_less_than_floor(self) -> None:
        """시차 — 같은 시간에 가까운 바닥 점이 벽 점보다 많이 움직인다."""
        cam0, cam1 = drift_at(10.0), drift_at(12.0)
        f = self.st._f_px()

        def sx(cam: tuple, z_m: float, y_m: float) -> float:
            y2, d = self.st._cam_space(cam, np.array([y_m]), np.array([z_m]))
            return float(W_OUT / 2 + f * (0.0 - cam[0]) / d[0])

        wall_z = STUDIO.fillet_z_m + STUDIO.fillet_radius_m
        self.assertGreater(abs(sx(cam1, -2.0, 0.0) - sx(cam0, -2.0, 0.0)), 2 * abs(sx(cam1, wall_z, 5.0) - sx(cam0, wall_z, 5.0)))


class EnginePathTest(unittest.TestCase):
    """합성 사본(fed_timeline_demo git 추적 파일 + 합성 plan) → 콘티 판 load_project(권리 점검 없음). 사진 배경 검사는 studio 에 걸리지 않는다."""

    @classmethod
    def setUpClass(cls) -> None:
        from tests.test_g8_animatic import synthetic_project  # noqa: PLC0415

        cls.tmp = tempfile.TemporaryDirectory()
        cls.proj = synthetic_project("fed_timeline_demo", Path(cls.tmp.name) / "s")
        cls.base = cls._direction(cls.proj)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    @staticmethod
    def _direction(proj: Path) -> dict:
        from engine.direction import load_direction_doc  # noqa: PLC0415

        d = load_direction_doc(proj / "direction.yaml").model_dump(mode="json", by_alias=True)
        d.update(stage="studio", stage_reason="시험 — 스튜디오 무대 위 차트 아일랜드", opening_exempt="시험 사본")
        d["shots"] = [{"at": 0, "mode": "cut", "dur": 0, "camera": {}},
                      {"at": 0, "stage": "timeline", "mode": "cut", "dur": 0, "camera": {"date": "2022-06-15", "w": 2600}}]
        ser = [{**e, "start": 0.3} for e in d["events"] if e["type"] == "series"]
        d["events"] = [{"type": "island", "kind": "chart", "box": "left", "start": 0.2, "end": {"card": "end", "edge": "start", "off": 0.4}}] + ser
        return d

    def _load(self, d: dict):  # noqa: ANN202
        from engine.project import load_project  # noqa: PLC0415

        (self.proj / "direction.yaml").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return load_project(self.proj, animatic=True)

    def test_island_on_studio_and_no_photo_checks(self) -> None:
        from engine import checks  # noqa: PLC0415
        from engine.island import ISLAND, island_box  # noqa: PLC0415
        from engine.render import render_frame  # noqa: PLC0415

        P = self._load(self.base)  # noqa: N806
        self.assertEqual(P.R.stage.name, "studio")
        self.assertEqual(P.R.cache["stage"]["instances"], {"studio": 1, "timeline": 1})
        self.assertEqual(P.R.cache["backdrop"], {})                       # 사진 배경 없음 → backdrop_rights·backdrop_repeat 0
        self.assertEqual(checks.check_main_missing(P), [])
        self.assertEqual(checks.check_data_stage_bare_on_backdrop(P), [])
        self.assertEqual(checks.check_island_text_contrast(P), [])
        self.assertEqual(checks.check_backdrop_subject(P), [])
        self.assertEqual(checks.check_island_overlap(P), [])
        isl = next(e for e in P.events if e["type"] == "island")
        s = P.plan.sentences[3]
        i = int((s.t0 + s.t1) / 2 * FPS)
        _, b1 = render_frame(P, i)
        _, b2 = render_frame(P, i + FPS)
        w, h = P.R.out.width, P.R.out.height
        f1 = np.frombuffer(bytes(b1), np.uint8).reshape(h, w, 4)[..., :3].mean(-1)
        f2 = np.frombuffer(bytes(b2), np.uint8).reshape(h, w, 4)[..., :3].mean(-1)
        x, y, bw, bh = (int(v * P.R.out.k) for v in island_box(isl))
        inner = f1[y + bh // 2 - 5:y + bh // 2 + 5, x + 10:x + 30]
        self.assertLess(float(inner.mean()), 120)                         # 아일랜드 상자(판)가 밝은 무대 위에 그려졌다
        bg_strip = (slice(int(430 * P.R.out.k), int(440 * P.R.out.k)), slice(int(700 * P.R.out.k), int(840 * P.R.out.k)))
        self.assertGreater(float(f1[bg_strip].mean()), 180)               # 아일랜드 밖은 밝은 회색 스튜디오
        self.assertGreater(float(np.abs(f1[bg_strip] - f2[bg_strip]).max()), 0)   # 1초 뒤 공간은 흘렀다
        self.assertTrue(ISLAND.fill_alpha > 0)

        def plate(f: np.ndarray) -> tuple[int, int, int, int]:   # 상자 판(어두운 면)의 화면 범위 — 자막 구역 위만
            ys, xs = np.nonzero(f[: int(400 * P.R.out.k)] < 90)
            return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())

        self.assertEqual(plate(f1), plate(f2))   # 내용물은 화면 자리 그대로 — 흐르는 것은 뒤의 공간뿐

    def test_backdrop_event_on_studio_rejected(self) -> None:
        from engine.project import ProjectError  # noqa: PLC0415

        d = json.loads(json.dumps(self.base))
        d["events"].append({"type": "backdrop", "start": 0.0, "end": 5.0, "img": "fed_presser_0916"})
        with self.assertRaises(ProjectError) as cm:
            self._load(d)
        self.assertIn("studio", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
