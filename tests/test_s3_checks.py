"""v7.4.0 back_and_forth D-1000 S3 — 탈락 유형 hard 검사(사용자 UF-171·172·173, D-0462·D-0466 의 일반화).

[map-event-covered] 지도 사건이 자라나거나 나타나는 창에서 덮개에 가림 · [media-date-cross] 보이는 동안 날짜 HUD 가 바뀜 ·
[media-burst-window]·[map-cover-share] 밀집(옛 경고 → hard). 검사마다 실패 픽스처 1·통과 픽스처 1.
무대는 항등 투영(월드 = 화면, y 뒤집기)인 가짜 지도 무대 — 상자 계산만 본다.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from engine import checks
from engine.checks import HARD, check_map_event_covered, check_media_burst, check_media_date_cross
from engine.style import FPS, H_OUT, W_OUT
from rules import load_rules

QA = load_rules().qa_checks
D = load_rules().media.density


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
        for cid in ("map_event_covered", "media_date_cross", "media_burst"):
            self.assertIn(cid, HARD)
            self.assertIn(f'"{cid}": lambda: check_{cid}(P)', src)   # 콘티 판·프리뷰·전편·카탈로그가 같은 run_checks(C12-3)
            self.assertIn(f"| {cid} | hard |", src)
        self.assertEqual(QA.map_event_covered.max_ratio, 0.25)
        self.assertEqual(QA.media_burst.max_cover_ratio, 0.5)
        self.assertEqual(D.window_sec, 40)
        self.assertIn("backdrop", QA.media_date_cross.exempt_types)


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


class MediaDateCrossTest(unittest.TestCase):
    SENTS = [("a", 0.0, 10.0, "2026.06.17"), ("b", 10.5, 20.0, "2026.07.07"), ("c", 20.5, 30.0, "2026.07.07")]

    def test_article_across_date_fails(self) -> None:
        out = check_media_date_cross(_P([_article(4.0, 15.0)], total=30.0, sents=self.SENTS))   # 6/18 기사가 7/7 문장 위로(D-0466)
        self.assertEqual(len(out), 1)
        self.assertIn("2026.06.17 → 2026.07.07", out[0])

    def test_same_date_window_passes(self) -> None:
        # 같은 날짜 연속 문장(b·c)은 한 창 — 날짜가 바뀌지 않는다
        self.assertEqual(check_media_date_cross(_P([_article(11.0, 29.0)], total=30.0, sents=self.SENTS)), [])

    def test_grace_at_boundary_passes(self) -> None:
        tc = 10.5 - 0.3
        e = _article(1.0, tc + 0.3 + 1.5)   # 보이는 끝(퇴장 페이드 절반)이 바뀐 시각 + grace 안
        _, vb = checks._vis_span(e)
        self.assertLessEqual(vb - tc, QA.media_date_cross.grace_sec + 1.0)
        out = check_media_date_cross(_P([e], total=30.0, sents=self.SENTS))
        self.assertEqual(out != [], vb - tc > QA.media_date_cross.grace_sec)

    def test_exempt_type(self) -> None:
        self.assertEqual(check_media_date_cross(_P([{"type": "backdrop", "t0": 0.0, "t1": 30.0, "mid": "b"}], total=30.0, sents=self.SENTS)), [])


class MediaBurstTest(unittest.TestCase):
    def test_four_in_40s_fails(self) -> None:
        evs = [_photo(t, t + 7.5, mid=f"m{k}") for k, t in enumerate((5.0, 15.0, 25.0, 35.0))]   # D-0466 "40초에 4개"
        with mock.patch("engine.media_plan.media_box", _media_box):
            out = check_media_burst(_P(evs, total=120.0))
        ids = [o.split("]")[0] + "]" for o in out]
        self.assertIn("[media-burst-window]", ids)
        self.assertIn("[map-cover-share]", ids)   # 5~42.5초 거의 내내 덮임

    def test_spaced_passes(self) -> None:
        evs = [_photo(t, t + 7.5, mid=f"m{k}") for k, t in enumerate((5.0, 50.0, 95.0))]   # 40초 창에 하나씩, 덮임 ≤ 7.5/40
        with mock.patch("engine.media_plan.media_box", _media_box):
            self.assertEqual(check_media_burst(_P(evs, total=140.0)), [])

    def test_cover_share_alone(self) -> None:
        evs = [_article(0.0, 12.0, "a1"), _article(13.0, 25.0, "a2")]   # 기사는 창 개수 밖, 그러나 40초 중 24초 덮임 > 50%
        out = check_media_burst(_P(evs, total=60.0))
        self.assertEqual([o.split("]")[0] + "]" for o in out], ["[map-cover-share]"])


if __name__ == "__main__":
    unittest.main()
