"""숏 단위 지명 라벨 일정 — 깜빡임 제거 (v7.4.0, back_and_forth D-0311, 사용자 의견 UF-175).

"지도가 확대 되거나 축소 될때 도시 이름이 나왔다 사라지거나 없던게 나온다거나 깜빡깜빡 거리는거 … 없애라고 했잖아."
- 옛 방식(프레임별 선택)으로 만든 열은 [label-flicker] 가 잡는다(장치 증명).
- 새 일정(build_plan)은 같은 카메라 경로에서 재등장 0·최소 유지 충족, 새 라벨은 카메라가 멈춘 뒤에만 들어온다.
가짜 무대: 경계만 있는 무대 + 후보 함수 대역(LOD 문턱에서 켜졌다 꺼지는 도시 하나).
"""

from __future__ import annotations

import types
import unittest
from unittest import mock

import numpy as np

from engine import labels_plan as lp
from engine.camera import CamKey
from rules import load_rules

FPS = 24


class _Stage:
    name = "mercator"
    bounds = (-180.0, -80.0, 180.0, 80.0)


def _cand(cid: str, kind: str = "city") -> object:
    return types.SimpleNamespace(id=cid, kind=kind, test=(100.0, 100.0, 40.0, 12.0) if cid == "city:A" else (300.0, 300.0, 40.0, 12.0),
                                 placed=(0, 0, 1, 1), draw=lambda la: None, blocks=True, name=cid)


def fake_candidates(ctx: object, stage: object, view: object, lod_w: "float | None" = None) -> list:
    """도시 A 는 LOD 폭 < 30 일 때만 후보(문턱에서 켜졌다 꺼진다), B 는 늘 후보."""
    w = view.w if lod_w is None else lod_w
    return ([_cand("city:A")] if w < 30 else []) + [_cand("city:B")]


def _cams(ws: list[float]) -> np.ndarray:
    return np.array([[0.0, 0.0, w] for w in ws])


def zoom_wobble() -> list[float]:
    """w 32 ↔ 28 를 오가는 줌(문턱 30 을 여러 번 넘는다) 뒤 w 25 에서 멈춤."""
    ws = []
    for k in range(6):
        ws += list(np.linspace(32, 28, 12)) if k % 2 == 0 else list(np.linspace(28, 32, 12))
    return ws + [25.0] * 72


class LegacyFlickerProvenTest(unittest.TestCase):
    def test_per_frame_selection_flickers(self) -> None:
        ws = zoom_wobble()
        sel = [{c.id for c in fake_candidates(None, None, types.SimpleNamespace(w=w))} for w in ws]
        plan = lp.plan_from_frames(sel, [(0, len(ws))], FPS)
        hard, _ = lp.flicker_report(plan)
        self.assertTrue(any("city:A" in h for h in hard), hard)


class PlanStableTest(unittest.TestCase):
    def test_build_plan_no_flicker_and_waits_for_still(self) -> None:
        ws = zoom_wobble()
        keys = [CamKey(t=0.0, x=0.0, y=0.0, w=ws[0], dur=0.0, mode="cut")]
        with mock.patch("engine.layers.labels.label_candidates", fake_candidates), \
             mock.patch("engine.layers.labels.city_cap", lambda st: 6), \
             mock.patch.object(lp, "_reserved_at", lambda *a, **k: []):
            plan = lp.build_plan(_Stage(), _cams(ws), keys, [], len(ws), FPS)
        hard, _ = lp.flicker_report(plan)
        self.assertEqual(hard, [])
        a = plan.spans.get("city:A", [])
        self.assertEqual(len(a), 1)   # 한 번만 나타난다
        self.assertGreaterEqual(a[0].t_in, 72 / FPS - 0.2)   # 흔들리는 줌이 끝나고 멈춘 뒤에 들어온다
        self.assertEqual(len(plan.spans["city:B"]), 1)

    def test_active_fades(self) -> None:
        S = load_rules().labels.stability  # noqa: N806
        plan = lp.LabelPlan(spans={"x": [lp.Span(1.0, 5.0, True, True, 0)]}, shots=[(0.0, 9.0)], hard_end=[True], fade_sec=S.fade_sec)
        self.assertNotIn("x", plan.active(0.5))
        self.assertAlmostEqual(plan.active(1.0 + S.fade_sec / 2)["x"], 0.5, places=2)
        self.assertEqual(plan.active(3.0)["x"], 1.0)

    def test_shot_ranges_soft_and_hard(self) -> None:
        keys = [CamKey(t=0.0, x=0, y=0, w=10, dur=0, mode="cut"), CamKey(t=2.0, x=0, y=0, w=10, dur=1, mode="move"),
                CamKey(t=4.0, x=0, y=0, w=10, dur=0, mode="cut")]
        self.assertEqual(lp.shot_ranges(keys, 6 * FPS, FPS), [(0, 48, False), (48, 96, True), (96, 144, True)])


class StageSignatureTest(unittest.TestCase):
    """engine/render.py 가 모든 무대에 draw_labels(ctx, view, reserved, alpha, t) 로 부른다 — 무대 하나라도 t 를 못 받으면 그 장르 영상 렌더가 TypeError
    (v7.4.0 전체 pytest 에서 timeline 무대로 발견)."""

    def test_all_stages_accept_t(self) -> None:
        import inspect  # noqa: PLC0415

        from engine import stage, stage_backdrop, stage_timeline  # noqa: PLC0415

        classes = [c for m in (stage, stage_backdrop, stage_timeline) for _, c in inspect.getmembers(m, inspect.isclass)
                   if c.__module__ == m.__name__ and "draw_labels" in c.__dict__]
        classes += [c for c in stage.STAGE_CLASSES.values() if c not in classes]   # 등록된 무대 전부(RENDER-AP-032)
        self.assertGreaterEqual(len(classes), 3)
        for c in classes:
            self.assertIn("t", inspect.signature(c.draw_labels).parameters, c.__name__)


if __name__ == "__main__":
    unittest.main()
