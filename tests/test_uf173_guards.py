"""UF-173(사용자 의견 "처음부터 사진을 띄워서 뒤에 지도가 안보이게 … 무지성으로 그냥 늘리면") 장치 + RIGHTS-AP-002 [credit-garbled] (v7.4.0 D-0466 §6·D-0470).

고정본: tests/fixtures/uf173/ — iran_ceasefire_2026 연출 v9(교체 완성본 final_v2, 사용자 탈락)·v10(final_v3, 감독 통과)의
덮는 요소·패널·문장 날짜(렌더 슬롯 폭 포함). v9 는 세 검사에 모두 걸리고 v10 은 모두 통과해야 한다.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from engine import checks
from engine.checks import credit_garbled_hits, map_cover_share_worst, map_opening_hits, media_sentence_span_hits
from rules import load_rules

FIX = Path(__file__).parent / "fixtures" / "uf173"
REPO = Path(__file__).resolve().parent.parent
TITLE_END = 28.42   # plan.json cards[title].t1(두 판 같은 음성)


def _load(name: str) -> tuple[list[dict], list[tuple], float]:
    fx = json.loads((FIX / name).read_text(encoding="utf-8"))
    return fx["events"], [(s["sid"], s["t0"], s["t1"], s["date"]) for s in fx["sentences"]], fx["total"]


class RuleTest(unittest.TestCase):
    def test_rules_present(self) -> None:
        q = load_rules().qa_checks
        self.assertEqual(q.media_sentence_span.tol_sec, 0.5)
        self.assertEqual(q.map_cover_share.max_share, 0.5)
        self.assertEqual(q.map_cover_share.window_sec, 30)
        self.assertEqual(q.map_opening.after_first_sentence_sec, 0.0)
        self.assertGreater(q.credit_garbled.max_len, 0)


class V9FailsTest(unittest.TestCase):
    """사용자 탈락 판(v9) — 문장 넘어감·첫 화면 사진·1막 지도 매몰을 그대로 잡는다."""

    def setUp(self) -> None:
        self.ev, self.ss, self.total = _load("iran_v9_final_v2.json")

    def test_sentence_span(self) -> None:
        hits = media_sentence_span_hits(self.ev, self.ss)
        self.assertGreaterEqual(len(hits), 5)
        self.assertTrue(any("iran_ceasefire_2026_art_0038" in h for h in hits))   # 6/18 기사가 7/7 문장 위

    def test_opening(self) -> None:
        hits = map_opening_hits(self.ev, self.ss[0][2])
        self.assertTrue(any("iran_doha_skyline" in h for h in hits))

    def test_cover_share(self) -> None:
        share, at = map_cover_share_worst(self.ev, self.total, TITLE_END)
        self.assertGreater(share, load_rules().qa_checks.map_cover_share.max_share)
        self.assertTrue(30 <= at <= 112)   # 1막


class V10PassesTest(unittest.TestCase):
    """감독 통과 판(v10, D-0470) — 세 검사 모두 0."""

    def setUp(self) -> None:
        self.ev, self.ss, self.total = _load("iran_v10_final_v3.json")

    def test_all_pass(self) -> None:
        self.assertEqual(media_sentence_span_hits(self.ev, self.ss), [])
        self.assertEqual(map_opening_hits(self.ev, self.ss[0][2]), [])
        share, _ = map_cover_share_worst(self.ev, self.total, TITLE_END)
        self.assertLessEqual(share, load_rules().qa_checks.map_cover_share.max_share)

    def test_half_slot_counts_partial(self) -> None:
        """반쪽 자리(376)를 가운데(461)로 바꾸면 act5 창이 상한을 넘는다 — 폭 가중이 실제로 작동."""
        ev = [dict(e, w=461) if e.get("w") == 376 else e for e in self.ev]
        share, _ = map_cover_share_worst(ev, self.total, TITLE_END)
        self.assertGreater(share, load_rules().qa_checks.map_cover_share.max_share)


class CreditGarbledTest(unittest.TestCase):
    def test_commons_notice_fails(self) -> None:
        raw = ("This image is available from the United States Library of Congress's Prints and Photographs division under the digital ID "
               "ppbd.00608.This tag does not indicate the copyright status of the attached work. See Commons:Licensing.")
        self.assertEqual(len(credit_garbled_hits([("people.trump", raw)])), 1)

    def test_url_fails(self) -> None:
        self.assertEqual(len(credit_garbled_hits([("people.khamenei", "http://farsi.khamenei.ir/photo-album?id=36022#i")])), 1)

    def test_author_passes(self) -> None:
        self.assertEqual(credit_garbled_hits([("people.trump", "Shealeah Craighead (백악관)"), ("people.khamenei", "khamenei.ir")]), [])

    def test_library_clean(self) -> None:
        """공용 초상 라이브러리 credit 칸 전수(RIGHTS-AP-002) — 원문은 credit_raw 에만."""
        lib = json.loads((REPO / "assets" / "library" / "library_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(credit_garbled_hits([(p["person_id"], p["source"].get("credit", "")) for p in lib["people"]]), [])


class WiredTest(unittest.TestCase):
    def test_registered_in_run(self) -> None:
        """검사 표(docstring)·실행 표·HARD 에 모두 있다 — 콘티 판·프리뷰·전편이 같은 run 을 쓴다(C12-3)."""
        src = open(checks.__file__, encoding="utf-8").read()
        for cid in ("media_sentence_span", "map_opening", "map_cover_share", "credit_garbled"):
            self.assertIn(f'"{cid}": lambda:', src)
            self.assertIn(f"| {cid} | hard |", src)
            self.assertIn(cid, checks.HARD)


if __name__ == "__main__":
    unittest.main()
