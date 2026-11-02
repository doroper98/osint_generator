"""v7.4.0 back_and_forth D-1000 S3 — 탈락 유형 hard 검사(사용자 UF-171·172·173, D-0462·D-0466 의 일반화).

[map-event-covered] 지도 사건이 자라나거나 나타나는 창에서 덮개에 가림 — 실패·통과 픽스처.
(media_date_cross·media_burst 는 D-1001 로 삭제 — 같은 개념은 D-0470 의 media_sentence_span·map_cover_share 가 정본.)
무대는 항등 투영(월드 = 화면, y 뒤집기)인 가짜 지도 무대 — 상자 계산만 본다.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from engine import checks
from engine.checks import HARD, check_map_event_covered
from engine.style import FPS, H_OUT, W_OUT
from rules import load_rules

QA = load_rules().qa_checks


class _TB:
    def __init__(self, sents: list[tuple[str, float, float, str]]) -> None:
        self.order = [s[0] for s in sents]
        self.sent = {s[0]: SimpleNamespace(t0=s[1], t1=s[2], date=s[3]) for s in sents}
        self.scenes = ["s"]

    def in_fullcard(self, t: float) -> bool:
        return False

    def SC(self, s: str) -> float:  # noqa: N802
        return 0.0


def _P(events: list[dict], total: float = 120.0, sents: list | None = None, keys: list | None = None) -> SimpleNamespace:  # noqa: N802
    n = int(total * FPS) + 1
    stage = SimpleNamespace(name="mercator", bounds=(0.0, 0.0, float(W_OUT), float(H_OUT)))
    R = SimpleNamespace(stage=stage, tb=_TB(sents or [("a", 0.0, total, "2026.01.01")]),  # noqa: N806
                        assets=SimpleNamespace(media_assets={"p": object(), "q": object()}))
    return SimpleNamespace(events=events, R=R, cams=np.tile([W_OUT / 2, H_OUT / 2, float(W_OUT)], (n, 1)), n_frames=n,
                           keys=keys or [], plan=SimpleNamespace(total=total))


def _route(t0: float, grow: float = 4.0) -> dict:
    # 화면 (100, 240) → (700, 240) 가로 경로(월드 y = 480 − 화면 y)
    return {"type": "route", "t0": t0, "t1": t0 + 10, "grow": grow, "label": "R", "world_pts": [[100.0, 240.0], [400.0, 240.0], [700.0, 240.0]]}


def _article(t0: float, t1: float, mid: str = "art") -> dict:
    return {"type": "article", "t0": t0, "t1": t1, "mid": mid}


def _photo(t0: float, t1: float, mid: str = "p", box: tuple = (196, 70, 657, 371)) -> dict:
    return {"type": "photo", "t0": t0, "t1": t1, "mid": mid, "x": box[0], "y": box[1], "w": box[2] - box[0], "_box": box}


def _media_box(e: dict, assets: dict) -> tuple:
    return e["_box"]


class RuleTest(unittest.TestCase):
    def test_registered_hard_and_rule_keys(self) -> None:
        src = open(checks.__file__, encoding="utf-8").read()
        for cid in ("map_event_covered",):
            self.assertIn(cid, HARD)
            self.assertIn(f'"{cid}": lambda: check_{cid}(P)', src)   # 콘티 판·프리뷰·전편·카탈로그가 같은 run_checks(C12-3)
            self.assertIn(f"| {cid} | hard |", src)
        self.assertEqual(QA.map_event_covered.max_ratio, 0.25)
        for gone in ("media_date_cross", "media_burst"):   # D-1001 — D-0470 장치(media_sentence_span·map_cover_share)가 정본, 이 둘은 삭제(P2)
            self.assertNotIn(gone, HARD)
            self.assertFalse(hasattr(QA, gone))


class MapEventCoveredTest(unittest.TestCase):
    def test_route_grow_under_article_fails(self) -> None:
        out = check_map_event_covered(_P([_route(10.0), _article(11.0, 20.0)]))   # UF-173 — 경로가 자라는 동안 전면 기사
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("[map-event-covered] route 'R'"))

    def test_route_grow_then_article_passes(self) -> None:
        self.assertEqual(check_map_event_covered(_P([_route(10.0), _article(15.0, 24.0)])), [])   # 다 자란 뒤(14초) 기사

    def test_corner_photo_not_overlapping_passes(self) -> None:
        corner = _photo(9.0, 18.0, box=(600, 300, 840, 400))   # 경로 상자(y 234~246) 밖 구석
        with mock.patch("engine.media_plan.media_box", _media_box):
            self.assertEqual(check_map_event_covered(_P([_route(10.0), corner])), [])

    def test_center_photo_over_route_fails(self) -> None:
        center = _photo(9.0, 18.0)   # 가운데 큰 사진 x 196~657 — 경로 상자 폭 600 중 461 이 가려짐
        with mock.patch("engine.media_plan.media_box", _media_box):
            out = check_map_event_covered(_P([_route(10.0), center]))
        self.assertEqual(len(out), 1)

    def test_camera_move_under_center_photo_fails(self) -> None:
        keys = [SimpleNamespace(t=30.0, dur=4.0, mode="move")]
        with mock.patch("engine.media_plan.media_box", _media_box):
            self.assertEqual(len(check_map_event_covered(_P([_photo(29.0, 40.0)], keys=keys))), 1)
            self.assertEqual(check_map_event_covered(_P([_photo(35.0, 45.0)], keys=keys)), [])   # 이동이 끝난 뒤(34초 + 페이드)


if __name__ == "__main__":
    unittest.main()
