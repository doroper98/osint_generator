"""v4.11.0 G10 §2 — 음악 상한 +2 dB, norm_ref 재탐색 (back_and_forth D-0118 §2, 사용자 위임 D103)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from rules import load_rules

REPO = Path(__file__).resolve().parent.parent
AU = load_rules().audio
SWEEP = REPO / "docs" / "handoff" / "reports" / "phaseG10" / "norm_ref_sweep.jsonl"
MARGIN_DB = 0.3   # D-0102 절차 — 범위 안 여유


class MusicCeilingTest(unittest.TestCase):
    def test_range_is_v3_plus_2db(self) -> None:
        self.assertEqual(tuple(AU.qa.music_under_narration_db), (-13.0, -9.0))   # v3 [-15, -11] + 2 dB
        self.assertEqual(AU.post_limiter_dbfs, -2.0)                             # 다른 오디오 값 무변경
        self.assertEqual(tuple(AU.qa.bed_bass_rise_db), (4, 8))

    def test_norm_ref_is_minimum_with_margin(self) -> None:
        """norm_ref = 스윕(두 편, 0.1 단위)에서 모든 프로젝트 음악 레벨이 [lo+0.3, hi−0.3] 안인 최소값."""
        rows = [json.loads(x) for x in SWEEP.read_text(encoding="utf-8").splitlines() if x.strip()]
        self.assertEqual({r["project"] for r in rows}, {"hormuz", "fed"})
        lo, hi = AU.qa.music_under_narration_db
        ok: dict[float, bool] = {}
        for r in rows:
            k = round(r["norm_ref"], 2)
            ok[k] = ok.get(k, True) and lo + MARGIN_DB <= r["music_under_narration_db"] <= hi - MARGIN_DB
        self.assertEqual(min(k for k, v in ok.items() if v), AU.bed_bass.norm_ref)
        self.assertFalse(ok[round(AU.bed_bass.norm_ref - 0.1, 2)])   # 한 칸 아래는 여유 밖(hormuz 0.3 = −9.26)
        self.assertEqual({r["bed_bass_rise_db"] for r in rows if r["project"] == "hormuz"}, {5.35})   # 정규화는 비율을 바꾸지 않는다


if __name__ == "__main__":
    unittest.main()
