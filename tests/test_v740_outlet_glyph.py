"""v7.4.0 back_and_forth D-0250(사용자 의견 UF-130 "기사 조판과 자막 나래이션이 다름"·UF-131 "특수문자 에러") —
[article-outlet-mismatch] hard 와 글리프 대체 사슬(rules fonts.glyph_fallback). 재현 = 현재 diesel 연출(사용자 결정 D262 로 재렌더 없음)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

import yaml

from engine import checks as C
from engine import typography as T
from engine.media_registry import cached_registry

REPO = Path(__file__).resolve().parent.parent
PROJ = REPO / "projects" / "diesel_road_2026"


def _sents() -> list[tuple[str, float, float, str]]:
    plan = json.loads((PROJ / "plan.json").read_text(encoding="utf-8"))
    return [(s["sid"], s["t0"], s["t1"], s["text"]) for s in plan["sentences"]]


def _events() -> list[dict]:
    """연출 이벤트 시각 — 앵커 sid 의 plan 시각(+off)으로 근사(기사 카드만)."""
    plan = {s["sid"]: s for s in json.loads((PROJ / "plan.json").read_text(encoding="utf-8"))["sentences"]}
    out = []
    for e in yaml.safe_load((PROJ / "direction.yaml").read_text(encoding="utf-8"))["events"]:
        if e["type"] != "article":
            continue
        a, b = e["start"], e["end"]
        t0 = plan[a["sid"]]["t0"] + (a.get("off") or 0.0)
        t1 = plan[b["sid"]]["t1" if b.get("edge") == "end" else "t0"] + (b.get("off") or 0.0)
        out.append({**e, "t0": t0, "t1": t1})
    return out


class OutletMismatchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reg = {k: v.model_dump() for k, v in cached_registry().items()}

    def test_current_diesel_fails(self) -> None:
        hits = C.outlet_mismatches(_events(), _sents(), self.reg)
        got = {(e["mid"], sid) for e, sid, _, _ in hits}
        self.assertIn(("diesel_road_2026_art_0001", "act3_5"), got)   # Kyiv Independent 카드 ↔ "가디언도 …"
        self.assertIn(("diesel_road_2026_art_0002", "act2_19"), got)   # UNITED24 카드 ↔ "이후 가디언이 …"
        self.assertIn("article_outlet", C.HARD)

    def test_matching_or_unnamed_passes(self) -> None:
        ev = [{"type": "article", "mid": "diesel_road_2026_art_0005", "t0": 0.0, "t1": 5.0}]   # IEA 카드
        self.assertEqual(C.outlet_mismatches(ev, [("s", 0.0, 5.0, "국제에너지기구는 경유 부족을 경고했습니다.")], self.reg), [])
        self.assertEqual(C.outlet_mismatches(ev, [("s", 0.0, 5.0, "경유 부족이 이어졌습니다.")], self.reg), [])
        self.assertEqual(len(C.outlet_mismatches(ev, [("s", 0.0, 5.0, "로이터는 경유 부족을 보도했습니다.")], self.reg)), 1)

    def test_outlet_ids(self) -> None:
        self.assertEqual(C.outlet_of(self.reg["diesel_road_2026_art_0001"]), "kyiv_independent")
        self.assertEqual(C.outlets_named("그래서 가디언은 이번 선적이"), {"guardian"})
        self.assertEqual(C.outlets_named("APEC 회의"), set())   # 라틴 이름은 낱말 경계


class GlyphFallbackTest(unittest.TestCase):
    def test_minus_in_display_font(self) -> None:
        s = "−3.4%"   # act3_11 카드(UF-131)
        self.assertNotIn(ord("−"), T.font_cmap("disp"))
        self.assertEqual(T.drawn_missing(s, "disp"), [])            # 대체 사슬(rules fonts.glyph_fallback)로 그린다
        with mock.patch.dict(T.GLYPH_FALLBACK, {}, clear=True):
            self.assertEqual(T.drawn_missing(s, "disp"), ["−"])     # 대체가 없으면 실제 그리는 글꼴 기준 누락(hard)

    def test_card_string_in_diesel(self) -> None:
        d = yaml.safe_load((PROJ / "direction.yaml").read_text(encoding="utf-8"))
        bigs = [b[0] for e in d["events"] if e["type"] == "card" for b in e.get("bigs") or []]
        self.assertIn("−3.4%", bigs)


if __name__ == "__main__":
    unittest.main()
