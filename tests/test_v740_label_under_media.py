"""v7.4.0 R-0294 감독 판정(겹침 0 원칙) — 지도 마커 라벨(+부제)이 사진·영상 상자 아래에 깔리면 [label-under-media] hard.
발견: showcase_geo p_0128.00 — 호르무즈 위성 사진(가운데 큰 자리 x 196~657)이 마커 '호르무즈 해협 · 가장 좁은 곳 약 39km' 라벨 왼쪽을 가렸다.
기존 [label-hidden-by-card] 는 card_zones(게시물·프리미티브·겹침 카드)만 보고 사진·영상은 보지 않았다."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest import mock

from engine import checks


def _P(events: list[dict]) -> NS:  # noqa: N802
    assets = {"ph": NS(tool=NS(params={"scale": [16, 9]}))}
    return NS(events=events, R=NS(assets=NS(media_assets=assets), stage=None, tb=NS(in_fullcard=lambda t: False)),
              cams=[None] * 10_000, n_frames=10_000)


def _marker(t0: float, t1: float) -> dict:
    return {"type": "marker", "t0": t0, "t1": t1, "label": "호르무즈 해협", "sub": "가장 좁은 곳 약 39km", "world": (0.0, 0.0)}


def _photo(t0: float, t1: float, x: float) -> dict:
    return {"type": "photo", "t0": t0, "t1": t1, "mid": "ph", "x": x, "y": 70, "w": 461}


class LabelUnderMediaTest(unittest.TestCase):
    def _run(self, events: list[dict]) -> list[str]:
        view = NS(to_screen=lambda lon, lat: (650.0, 160.0))   # 라벨 상자 x 636~ — 가운데 사진(196~657) 오른쪽 끝과 겹친다
        with mock.patch.object(checks, "View", return_value=view):
            return checks.check_label_under_media(_P(events))

    def test_label_under_photo_is_hard(self) -> None:
        out = self._run([_marker(10.0, 16.0), _photo(10.5, 16.8, 196)])
        self.assertEqual(len(out), 1)
        self.assertIn("[label-under-media]", out[0])
        self.assertIn("label_under_media", checks.HARD)

    def test_photo_clear_of_label_passes(self) -> None:
        self.assertEqual(self._run([_marker(10.0, 16.0), {**_photo(10.5, 16.8, 42), "w": 376}]), [])   # map_pair_left(42~418)

    def test_photo_after_marker_passes(self) -> None:
        self.assertEqual(self._run([_marker(10.0, 16.0), _photo(16.5, 20.0, 196)]), [])

    def test_fade_overlap_within_limit(self) -> None:
        # 마커가 사라지는 동안 사진이 뜬다 — 둘 다 알파 ≥ min_alpha 인 표본만 센다
        self.assertEqual(self._run([_marker(10.0, 16.0), _photo(15.7, 20.0, 196)]), [])

    def test_rule_keys(self) -> None:
        cfg = checks.QA.label_under_media
        self.assertEqual((cfg.max_sec, cfg.step_sec, cfg.min_alpha, cfg.media_types), (0.2, 0.1, 0.5, ["photo", "clip"]))


if __name__ == "__main__":
    unittest.main()
