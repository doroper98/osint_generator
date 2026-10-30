"""v7.4.0 back_and_forth D-0316 — ① [flight-unsourced] hard ② [text-restates-narration] 조사 떼기·패널 items.

① showcase_geo act1 "봄부터 이어진 정유소 타격" 총괄 문장에 붙은 랴잔 드론 비행이 특정 타격처럼 읽혔다 → 비행은 원고가 인용한 claim 이 있는 특정 타격에만.
② GL135 체크리스트 패널(부제 "러시아산 경유 · 미국 재무부", 목록 판매·운송·수입)이 원고 "재무부는 러시아산 경유의 판매와 운송, 수입을…" 을
   되풀이했는데 검사가 못 잡았다 — 조사 붙은 어절("경유의")과 맨 단어("경유")를 다르게 봤고, items 를 보지 않았다.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

from engine import checks

GL135 = "이어서 재무부는 러시아산 경유의 판매와 운송, 수입을 허용하는 일반허가 135호를 내놨습니다."


class FlightUnsourcedTest(unittest.TestCase):
    def _P(self, events: list[dict]) -> NS:  # noqa: N802
        d = Path(tempfile.mkdtemp())
        (d / "script.yaml").write_text("scenes:\n- id: cold\n  sentences:\n  - text: x\n    sources: [clm_0099]\n", encoding="utf-8")
        return NS(root=d, events=events)

    def test_missing_or_uncited_claim_is_hard(self) -> None:
        fl = {"type": "flight", "kind": "drone", "t0": 1.0, "lon": 39.7, "lat": 54.62}
        self.assertEqual(len(checks.check_flight_unsourced(self._P([fl]))), 1)
        self.assertIn("claim 없음", checks.check_flight_unsourced(self._P([fl]))[0])
        self.assertIn("인용하지 않은", checks.check_flight_unsourced(self._P([{**fl, "claim": "clm_9999"}]))[0])
        self.assertEqual(checks.check_flight_unsourced(self._P([{**fl, "claim": "clm_0099"}])), [])
        self.assertIn("flight_unsourced", checks.HARD)

    def test_showcase_geo_single_sourced_flight(self) -> None:
        import yaml  # noqa: PLC0415

        root = Path(__file__).resolve().parents[1] / "projects" / "showcase_geo"
        evs = [e for e in yaml.safe_load((root / "direction.yaml").read_text(encoding="utf-8"))["events"] if e["type"] == "flight"]
        self.assertEqual([e.get("claim") for e in evs], ["clm_0099"])
        self.assertIn("clm_0099", checks.cited_claims(root))


class RestateParticleTest(unittest.TestCase):
    def _P(self, ev: dict) -> NS:  # noqa: N802
        return NS(events=[ev], plan=NS(sentences=[NS(t0=0.0, t1=6.0, sid="act5_3", text=GL135)]))

    def test_gl135_checklist_caught(self) -> None:
        ev = {"type": "panel", "t0": 1.0, "t1": 5.0,
              "data": {"title": "일반허가 135호", "subtitle": "러시아산 경유 · 미국 재무부", "items": ["판매", "운송", "수입"]}}
        self.assertEqual(len(checks.check_text_restates_narration(self._P(ev))), 1)

    def test_stem_and_items(self) -> None:
        self.assertEqual(checks._stem("경유의"), "경유")
        self.assertEqual(checks._stem("재무부는"), "재무부")
        self.assertEqual(checks._stem("러시아에서"), "러시아")   # 긴 조사 먼저
        self.assertEqual(checks._screen_texts({"items": ["판매", "운송", "수입", "허용"]}), ["판매 운송 수입 허용"])
        ev = {"type": "cascade", "t0": 1.0, "t1": 5.0, "items": ["러시아산 경유의 판매", "운송과 수입"]}
        self.assertEqual(len(checks.check_text_restates_narration(self._P(ev))), 1)   # 목록 4어절 이상 → 대상

    def test_new_fact_passes(self) -> None:
        ev = {"type": "marker", "t0": 1.0, "t1": 5.0, "label": "일반허가 135호", "sub": "2026. 10. 9 발급 · 2027. 4. 7까지"}
        self.assertEqual(checks.check_text_restates_narration(self._P(ev)), [])


if __name__ == "__main__":
    unittest.main()
