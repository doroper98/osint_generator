"""미디어 배치·밀도·제안 (D-0036 작업 6·8, 14 §5·§10)."""

from __future__ import annotations

import copy
import unittest

from pydantic import ValidationError

from engine.media_plan import density_report, fill_placement, placement_warnings
from engine.media_registry import load_media_registry
from rules import load_rules
from script.schema import MediaCue, Sentence


class _TB:
    """Timebase 대역 — 장면 시작만."""

    def __init__(self, starts: dict[str, float]) -> None:
        self.scenes = list(starts)
        self._s = starts

    def SC(self, s: str) -> float:  # noqa: N802
        return self._s[s]


HORMUZ_SCENES = {"open": 0.0, "war": 45.0, "ask": 68.0, "timeline": 110.0, "cost": 150.0, "review": 161.0,
                 "past": 186.0, "debate": 210.0, "decision": 242.0, "now": 255.0}
HORMUZ_MEDIA = [("clip", "niovi", 58.95), ("clip", "strikes", 134.48), ("article", "reuters_0904", 162.09),
                ("cutout", "p8", 168.12), ("photo", "rok_iraq", 191.32), ("article", "herald_0907", 211.75),
                ("photo", "hormuz_transit", 256.11)]


def _ev(typ: str, mid: str, t0: float, dur: float = 5.0) -> dict:
    return {"type": typ, "mid": mid, "t0": t0, "t1": t0 + dur}


class DensityTest(unittest.TestCase):
    def test_hormuz_v3_clean(self) -> None:
        r = density_report([_ev(*m) for m in HORMUZ_MEDIA], _TB(HORMUZ_SCENES), 292.439)
        self.assertEqual(r["warnings"], [])
        self.assertEqual(r["count"], 7)
        self.assertEqual(r["sec_per_item"], 41.8)

    def test_three_in_one_scene_warns(self) -> None:
        evs = [_ev("photo", "a", 10), _ev("clip", "b", 30), _ev("cutout", "c", 50)]   # 60초 안 3개, 한 장면
        r = density_report(evs, _TB({"s1": 0.0, "s2": 70.0}), 180.0)
        self.assertTrue(any("media-per-scene" in w for w in r["warnings"]))

    def test_too_dense_and_too_sparse(self) -> None:
        tb = _TB({"s1": 0.0, "s2": 30.0, "s3": 60.0})
        dense = density_report([_ev("photo", "a", 5), _ev("clip", "b", 35), _ev("cutout", "c", 65)], tb, 90.0)
        self.assertTrue(any("media-density-high" in w for w in dense["warnings"]))
        sparse = density_report([_ev("photo", "a", 5)], tb, 90.0)
        self.assertTrue(any("media-density-low" in w for w in sparse["warnings"]))

    def test_article_exempt_per_scene(self) -> None:
        evs = [_ev("article", "x", 10), _ev("cutout", "c", 20)]
        r = density_report(evs, _TB({"s1": 0.0}), 90.0)
        self.assertFalse(any("media-per-scene" in w for w in r["warnings"]))

    def test_adjacent_same_kind(self) -> None:
        tb = _TB({"s1": 0.0, "s2": 50.0})
        r = density_report([_ev("photo", "a", 10), _ev("photo", "b", 60)], tb, 100.0)
        self.assertTrue(any("media-same-kind-adjacent" in w for w in r["warnings"]))


class PlacementTest(unittest.TestCase):
    V3 = {"niovi": (40, 150, 300), "strikes": (207, 112, 440), "rok_iraq": (292, 138, 280), "hormuz_transit": (560, 196, 262)}

    def _events(self) -> list[dict]:
        panels = [{"type": "panel", "t0": 110.0, "t1": 150.0}, {"type": "panel", "t0": 186.0, "t1": 208.0}]
        return panels + [dict(_ev("clip", "niovi", 58.95)), dict(_ev("clip", "strikes", 134.48)),
                         dict(_ev("photo", "rok_iraq", 191.32, 10.8)), dict(_ev("photo", "hormuz_transit", 256.11, 10.0))]

    def test_defaults_reproduce_v3(self) -> None:
        evs = self._events()
        rec = fill_placement(evs)
        for e in evs[2:]:
            self.assertEqual((e["x"], e["y"], e["w"]), self.V3[e["mid"]], e["mid"])
            self.assertTrue(rec[e["mid"]].startswith("auto:"))

    def test_explicit_kept(self) -> None:
        evs = self._events()
        evs[2].update(x=10.0, y=20.0, w=100.0)
        self.assertEqual(fill_placement(evs)["niovi"], "explicit")
        self.assertEqual(evs[2]["x"], 10.0)

    def test_subtitle_overlap_warns(self) -> None:
        reg = load_media_registry()
        evs = self._events()
        fill_placement(evs)
        self.assertEqual(placement_warnings(evs, reg), [])
        low = copy.deepcopy(evs)
        low[5]["y"] = 300.0   # 사진+캡션이 자막(y ≥ 410)을 덮는다
        self.assertTrue(any("media-over-subtitle" in w for w in placement_warnings(low, reg)))

    def test_card_overlap_warns(self) -> None:
        reg = load_media_registry()
        evs = self._events()
        fill_placement(evs)
        card = {"type": "card", "t0": 256.0, "t1": 266.0, "tag": "태그", "lines": ["한 줄", "두 줄", "세 줄", "네 줄", "다섯"],
                "accent": "gold"}
        self.assertTrue(any("media-over-card" in w for w in placement_warnings(evs + [card], reg)))


class SuggestAndCueTest(unittest.TestCase):
    def test_triggers_in_rules(self) -> None:
        trig = load_rules().media_beats.triggers
        self.assertEqual(set(trig), {"clip", "photo", "cutout", "article"})

    def test_media_cue(self) -> None:
        s = Sentence(date="2026.09.18", text="해상초계기와 군수지원함이 거론됐습니다.", media=MediaCue(kind="cutout", asset_id="p8", at="해상초계기"))
        self.assertEqual(s.media.kind, "cutout")
        with self.assertRaises(ValidationError):
            MediaCue(kind="photo")                                  # asset_id·query 둘 다 없음
        with self.assertRaises(ValidationError):
            Sentence(date="2026", text="문장", media=MediaCue(kind="photo", query="x", at="없는 단어"))

    def test_suggest_from_plan(self) -> None:
        from script.media_suggest import suggest_media
        from script.schema import Plan

        mk = lambda sid, sc, text, t0: dict(sid=sid, scene=sc, date="2026", text=text, tts=text, segments=[],  # noqa: E731
                                            mp3="x", npy="x", dur=3.0, t0=t0, t1=t0 + 3)
        plan = Plan.model_validate(dict(sentences=[mk("a", "s", "로이터는 이렇게 보도했습니다.", 0.0),
                                                   mk("b", "s", "미군이 공습을 이어갔습니다.", 3.0),
                                                   mk("c", "s", "평범한 문장입니다.", 6.0)],
                                        cards=[], scene_start={"s": 0.0}, total=9.0, voice="x", title="t", subtitle="s",
                                        date="2026"))
        got = {(s.sid, s.kind) for s in suggest_media(plan)}
        self.assertEqual(got, {("a", "article"), ("b", "clip")})
        forced = suggest_media(plan, {"c": {"kind": "photo", "asset_id": "rok_iraq"}})
        self.assertIn(("c", "photo", "script"), {(s.sid, s.kind, s.source) for s in forced})


if __name__ == "__main__":
    unittest.main()
