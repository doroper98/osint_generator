"""미디어 권리 게이트 (D-0036 작업 3·7·8, C9, 15 P3·P6)."""

from __future__ import annotations

import unittest

from engine.credits import RightsError
from engine.layers.media import validate_media
from engine.media_registry import load_media_registry
from engine.registry import RegistryError, validate_events


class MediaGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reg = load_media_registry()

    def test_no_registry_ref(self) -> None:
        with self.assertRaises(RightsError):
            validate_media({"type": "photo", "t0": 1.0, "img": "x.jpg"}, self.reg)

    def test_unknown_mid(self) -> None:
        with self.assertRaises(RightsError):
            validate_media({"type": "photo", "t0": 1.0, "mid": "nope"}, self.reg)

    def test_kind_mismatch(self) -> None:
        with self.assertRaises(RightsError):
            validate_media({"type": "photo", "t0": 1.0, "mid": "strikes"}, self.reg)   # 영상을 사진 카드로

    def test_unverified_rights_blocks_render(self) -> None:
        reg = dict(self.reg)
        reg["hormuz_transit"] = reg["hormuz_transit"].model_copy(update={"rights_status": "unverified"})
        with self.assertRaises(RightsError):
            validate_media({"type": "photo", "t0": 1.0, "mid": "hormuz_transit"}, reg)

    def test_clear_passes(self) -> None:
        self.assertEqual(validate_media({"type": "clip", "t0": 1.0, "mid": "strikes"}, self.reg).segment, (1.5, 6.5))

    def test_direction_cannot_supply_caption(self) -> None:
        """화면 문구는 레지스트리에서만 — 연출이 캡션·출처 줄을 주면 모델 오류(P3)."""
        for ev in ({"type": "photo", "t0": 1, "t1": 5, "mid": "rok_iraq", "x": 1, "y": 1, "w": 100, "caption": "딴 캡션"},
                   {"type": "clip", "t0": 1, "t1": 5, "mid": "strikes", "x": 1, "y": 1, "w": 100, "credit": "x"},
                   {"type": "cutout", "t0": 1, "t1": 5, "mid": "p8", "lon": 1, "lat": 1, "w": 100, "label": "x"},
                   {"type": "article", "t0": 1, "t1": 5, "mid": "reuters_0904", "headline": "다른 헤드라인"}):
            with self.assertRaises(RegistryError):
                validate_events([ev])


class MediaCreditLinkTest(unittest.TestCase):
    def test_every_media_in_card_and_articles_required(self) -> None:
        """미디어 7종이 엔딩 카드 행(rights 참조)에 모두 걸린다 — 기사도(v2.5.5)."""
        from pathlib import Path

        from engine.credits import load_credits, required_refs

        cr = load_credits(Path("projects/hormuz_korea/credits.yaml"))
        refs = {r for s in cr.sections for it in s.items for r in it.refs()}
        v3 = {"hormuz_transit", "rok_iraq", "p8", "strikes", "niovi", "reuters_0904", "herald_0907"}   # v4.4.0 — 레지스트리의 hormuz(v3) 자산만(다른 프로젝트 자산은 그 프로젝트 카드)
        for mid in load_media_registry():
            if mid in v3:
                self.assertIn(f"media.{mid}", refs, mid)
        evs = [{"type": "article", "mid": "reuters_0904"}]
        self.assertEqual(required_refs(evs, {}, lambda _: None, set(), music_ids=set()) & {"media.reuters_0904"},
                         {"media.reuters_0904"})


if __name__ == "__main__":
    unittest.main()
