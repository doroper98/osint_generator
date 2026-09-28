"""골든 PNG 는 사료 — 바이트 고정 + KZ 결함 9컷 등재 (v4.1.0, back_and_forth D-0079, DECISIONS D70).

골든 25장(v3 최종본 mp4 프레임)은 결함(KZ 키 충돌, PIPELINE-AP-011)이 있어도 고치지 않고 `expected_deltas.json` 에 기록한다.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLDEN = REPO / "docs" / "handoff" / "golden"
sys.path.insert(0, str(REPO / "tools"))
from golden_compare import load_expected_deltas  # noqa: E402

FROZEN_MD5: dict[str, str] = {
    "frame_0007.82.png": "d8c2a604f3e51461f4864bedd807b9d9",
    "frame_0022.27.png": "a70db3eaeef4fa8223a4247f1490e44b",
    "frame_0028.77.png": "5b9ee865b2e17337a6561128a212569f",
    "frame_0038.45.png": "b5005b08e986049304f1ad446e1e3628",
    "frame_0045.03.png": "e0d1b37e36ea2f83702fe790f775b81f",
    "frame_0056.21.png": "16a01c2b6ab3e0838e84efca3e7472e8",
    "frame_0061.25.png": "9d5849b3f5bb22150f3cc458c78ecaf7",
    "frame_0065.13.png": "d73d243386ac595f369852a7713eff34",
    "frame_0080.70.png": "83a0348083f768bd43452cd2dae0986a",
    "frame_0087.06.png": "ee0194977d81ff1f0bdac7e882650566",
    "frame_0105.28.png": "a733e5758f3f6299c01cc61e8b860d7c",
    "frame_0124.25.png": "649f245f0cb8a61d343ec7b009635ed5",
    "frame_0136.97.png": "df9d48edbe498ee6f7452ab01737ef64",
    "frame_0157.38.png": "00de752b9ca5bee987201f5f51cc3634",
    "frame_0164.59.png": "2ae80b3a05dbe6f280a702533813a5ff",
    "frame_0170.52.png": "3b5cb105fc8043648d7b9a9255efaf94",
    "frame_0193.22.png": "f6841dae1465a3e1d152a37a771f8b36",
    "frame_0207.40.png": "454d5a6cd9f348c9744f6637fff3a32e",
    "frame_0214.45.png": "71d2511c1286f12f6101f822244a0422",
    "frame_0220.96.png": "d17629b57af63882edba0625153ea3db",
    "frame_0238.00.png": "6ab40aa4612cd2eef70d9c79801f32f5",
    "frame_0245.55.png": "e603ef5186a05433736dc481301b64c7",
    "frame_0258.61.png": "3a539d724ca4bde3854793c3e174bc17",
    "frame_0276.44.png": "21f6b5541fd81d16968cdf7d9e2c9f5c",
    "frame_0288.44.png": "db426bf465db4006500aadbf59ffbc1b",
}
KZ_CUTS = ["04_route_2", "05_route_3", "15_review_0", "16_review_1", "17_past_1", "18_past_3", "23_now_0", "24_now_3", "25_END"]


class GoldenFrozenTest(unittest.TestCase):
    def test_golden_png_bytes_unchanged(self) -> None:
        now = {p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in sorted(GOLDEN.glob("frame_*.png"))}
        self.assertEqual(now, FROZEN_MD5)

    def test_kz_cuts_are_intended_deltas(self) -> None:
        """golden_compare 가 묶음 항목 geo_kz_d0078 의 9컷을 의도된 차이로 뺀다(D34·D36 선례)."""
        d = load_expected_deltas()
        for c in KZ_CUTS:
            self.assertIn(c, d, c)
        self.assertEqual(d["geo_kz_d0078"]["cuts"], KZ_CUTS)
        self.assertNotIn("06_war_1", d)   # KZ 가 안 보이는 컷은 등재하지 않는다

    def test_delta_frames_exist(self) -> None:
        raw = json.loads((GOLDEN / "expected_deltas.json").read_text(encoding="utf-8"))["deltas"]["geo_kz_d0078"]
        for c in raw["cuts"]:
            p = REPO / "docs" / "handoff" / "reports" / "phaseG1" / "golden_delta" / f"{c}.png"
            self.assertEqual(hashlib.md5(p.read_bytes()).hexdigest(), raw["cut_detail"][c]["md5"], c)


if __name__ == "__main__":
    unittest.main()
