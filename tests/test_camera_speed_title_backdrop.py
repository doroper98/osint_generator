"""v6.0.2 사용자 의견 UF-97(오프닝 카메라 급격, recurs_of UF-02)·UF-98(제목 직전 지도 깜박임) — D-0216 최소 장치.

- camera_speed(hard): engine.camera.speed 로 pan(화면 폭/초)·zoom(|d ln w/dt|) 상한, 제목 카드 전은 더 낮은 상한. 스케치 SK-C1 같은 함수.
- title_backdrop(hard): 제목 카드 직전 1초 장면 = 제목 바탕.
"""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from engine import checks as C
from engine.camera import speed
from engine.style import FPS
from rules import load_rules

CS = load_rules().shot_grammar.camera_speed


def _ease(n: int) -> np.ndarray:
    u = np.linspace(0, 1, n)
    return u ** 3 * (u * (u * 6 - 15) + 10)   # 5차(move_ease quintic)


def _track(w0: float, w1: float, t0: float, dur: float, total: float) -> np.ndarray:
    n = int(total * FPS)
    w = np.full(n, float(w0))
    a, b = int(t0 * FPS), int((t0 + dur) * FPS)
    w[a:b] = np.exp(np.log(w0) + (np.log(w1) - np.log(w0)) * _ease(b - a))
    w[b:] = w1
    return np.column_stack([np.full(n, 50.0), np.full(n, 25.0), w])


def _P(track: np.ndarray, title_t0: float | None, events: list | None = None) -> SimpleNamespace:  # noqa: N802
    cards = [SimpleNamespace(kind="title", t0=title_t0, t1=title_t0 + 5.6)] if title_t0 is not None else []
    return SimpleNamespace(cams=track, keys=[], plan=SimpleNamespace(cards=cards), events=events or [],
                           R=SimpleNamespace(stage=SimpleNamespace(name="mercator")))


class CameraSpeedTest(unittest.TestCase):
    def test_speed_measures(self) -> None:
        tr = np.array([[0.0, 0.0, 10.0], [1.0, 0.0, 10.0], [1.0, 0.0, 20.0]])
        sp = speed(tr, (), 24)
        self.assertAlmostEqual(sp["pan"][0], 1.0 / 10 * 24)
        self.assertAlmostEqual(sp["zoom"][1], np.log(2) * 24)
        self.assertEqual(speed(tr, (2,), 24)["zoom"][1], 0.0)   # 컷으로 들어가는 차분은 0

    def test_gulf_v5224_opening_fails_slowed_passes(self) -> None:
        """v5.22.4 오프닝: w 88→34 를 4.4초(6.0초 시작) — 제목 13.4초 전 → 오프닝 상한 위반. 7초로 늘리면 통과."""
        fast = C.check_camera_speed(_P(_track(88, 34, 6.0, 4.4, 20), 13.4))
        self.assertTrue(fast and "오프닝" in fast[0], fast)
        self.assertEqual(C.check_camera_speed(_P(_track(88, 34, 1.5, 7.0, 20), 13.4)), [])

    def test_general_cap_after_title(self) -> None:
        self.assertEqual(C.check_camera_speed(_P(_track(88, 34, 20.0, 4.4, 30), 13.4)), [])   # 제목 뒤 같은 이동 = 일반 상한 안
        self.assertTrue(C.check_camera_speed(_P(_track(88, 8, 20.0, 1.0, 30), 13.4)))       # 1초 11배 줌 = 일반 상한 위반

    def test_timeline_stage_zoom_only(self) -> None:
        """v7.0.1 D-0218 A — 시간축 무대는 zoom 상한만(pan 은 지도 무대만), 규칙에 없는 무대는 검사 안 함."""
        self.assertEqual(CS.stages["timeline"], ["zoom"])
        P = _P(_track(1300, 40, 20.0, 4.0, 40), 12.1)   # noqa: N806 — fed_timeline_demo 옛 확대(4초 32배)
        P.R.stage.name = "timeline"
        out = C.check_camera_speed(P)
        self.assertTrue(out and all("zoom" in o for o in out), out)
        P.cams = _track(1300, 40, 20.0, 5.2, 40)
        self.assertEqual(C.check_camera_speed(P), [])
        P.cams[:, 0] = np.linspace(0, 40 * 30, len(P.cams))   # 화면 기준 빠른 pan — 시간축은 재지 않음
        self.assertEqual(C.check_camera_speed(P), [])
        P.R.stage.name = "other"
        P.cams = _track(1300, 40, 20.0, 1.0, 40)
        self.assertEqual(C.check_camera_speed(P), [])

    def test_fed_timeline_demo_passes(self) -> None:
        from engine.project import load_project  # noqa: PLC0415

        pd = Path(__file__).resolve().parents[1] / "projects" / "fed_timeline_demo"
        if not (pd / "plan.json").exists():
            self.skipTest("fed_timeline_demo plan 없음")
        P = load_project(pd)   # noqa: N806
        self.assertEqual(C.check_camera_speed(P), [])

    def test_registered_and_shared_with_sketch(self) -> None:
        self.assertIn("camera_speed", C.HARD)
        self.assertIn("title_backdrop", C.HARD)
        from sketch.common import checks as SK  # noqa: PLC0415

        self.assertIn("speed(track", inspect.getsource(SK.check_camera))
        self.assertLess(CS.opening_max_zoom_per_sec, CS.max_zoom_per_sec)


class TitleBackdropTest(unittest.TestCase):
    def _art(self, t0: float, t1: float) -> dict:
        return {"type": "article", "t0": t0, "t1": t1, "mid": "art_1"}

    def test_card_map_title_flicker_fails(self) -> None:
        P = _P(_track(30, 30, 0, 0.1, 20), 13.42, [self._art(8.72, 13.42)])   # noqa: N806 — v5.22.4 모양
        out = C.check_title_backdrop(P)
        self.assertTrue(out and "map" in out[0] and "article" in out[0], out)

    def test_title_over_card_passes(self) -> None:
        self.assertEqual(C.check_title_backdrop(_P(_track(30, 30, 0, 0.1, 25), 13.42, [self._art(8.72, 19.02)])), [])

    def test_title_over_map_passes(self) -> None:
        self.assertEqual(C.check_title_backdrop(_P(_track(30, 30, 0, 0.1, 25), 13.42, [])), [])   # 골든 모양(지도 → 제목)

    def test_direction_grammar_line(self) -> None:
        """v6.0.3 D-0216 2단계 — 제목 바탕 규칙(오프닝 기사 카드 위에 제목)이 연출 문법 한 줄로 연출·수정 프롬프트에 간다(P3)."""
        lines = [g for g in load_rules().direction_grammar if "[title-backdrop]" in g]
        self.assertEqual(len(lines), 1)
        self.assertIn("{card: title, edge: end}", lines[0])
        for f in ("director.md", "revise_direction.md"):
            self.assertIn("{{RULES.direction_grammar}}", (Path(__file__).resolve().parents[1] / "prompts" / f).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


class TitleOverArticleTest(unittest.TestCase):
    """v6.0.2 D-0216 — 제목이 기사 카드 위에 뜨면 기사 글자는 가라앉고, 제목이 사라지는 동안 다시 떠오르지 않는다."""

    def test_text_sinks_and_stays_down(self) -> None:
        from engine.layers.article import title_over

        R = SimpleNamespace(tb=SimpleNamespace(plan=SimpleNamespace(cards=[SimpleNamespace(kind="title", t0=13.4, t1=19.0)])))  # noqa: N806
        self.assertEqual(title_over(R, 12.0), 0.0)
        self.assertTrue(0.0 < title_over(R, 13.7) < 1.0)
        self.assertEqual(title_over(R, 16.0), 1.0)
        self.assertEqual(title_over(R, 18.8), 1.0)   # 제목 페이드 아웃 중에도 1
        self.assertEqual(title_over(R, 21.0), 0.0)
        self.assertEqual(title_over(SimpleNamespace(), 16.0), 0.0)
