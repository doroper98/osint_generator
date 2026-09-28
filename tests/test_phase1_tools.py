"""Phase 1 골든 재현 도구 단위 테스트 (v2.0.1, back_and_forth D-0002 합격 조건).

- 타일 범위: 19a §H 값(W z5 x18–28/y11–17 등, 합계 135장 — 19 §6)
- 앵커 재계산: reference plan.json 으로 골든 25 시각 재현(±0.006초, 골든 파일은 소수 둘째 자리)
- MAD 계산, 렌더 조각 분할, SRT·설명문 생성(골든과 동일), 전환 시트 시각

v2.3.0(D32): 옛 실행기(tools 의 v3 러너) 삭제에 따라 조각 분할·SRT·설명문 테스트 대상을 새 엔진 동명 함수
(`engine.render.chunk_ranges`, `engine.mux.{srt_time, build_srt, build_description}`)로 바꿨다. 테스트는 삭제하지 않았다.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from contact_sheet import transition_times  # noqa: E402
from fetch_data import TIERS, tile_range  # noqa: E402
import golden_compare  # noqa: E402
from golden_compare import anchor_time, load_expected_deltas, load_golden, mad  # noqa: E402
from engine.mux import build_description, build_srt, load_description, srt_time  # noqa: E402
from engine.render import chunk_ranges  # noqa: E402
from script.schema import Plan  # noqa: E402

REF_PLAN = json.loads((REPO / "docs/handoff/reference_code/v3_hormuz_korea/plan.json").read_text(encoding="utf-8"))
REF_PLAN_MODEL = Plan.model_validate(REF_PLAN)
GOLDEN = REPO / "docs/handoff/golden"


def _tr(name: str) -> tuple[range, range]:
    T = TIERS[name]
    return tile_range(float(T["lon0"]), float(T["lat0"]), float(T["lon1"]), float(T["lat1"]), int(T["z"]))


class TileRangeTest(unittest.TestCase):
    def test_w_tier_matches_19a(self) -> None:
        xr, yr = _tr("W")
        self.assertEqual((xr.start, xr.stop - 1, yr.start, yr.stop - 1), (18, 28, 11, 17))

    def test_g_and_k_tiers(self) -> None:
        self.assertEqual(tuple((r.start, r.stop - 1) for r in _tr("G")), ((80, 86), (51, 56)))
        self.assertEqual(tuple((r.start, r.stop - 1) for r in _tr("K")), ((107, 110), (48, 51)))

    def test_total_135_tiles(self) -> None:
        self.assertEqual(sum(len(x) * len(y) for x, y in (_tr(n) for n in TIERS)), 135)


class AnchorTest(unittest.TestCase):
    def test_reference_plan_reproduces_golden_times(self) -> None:
        for f in load_golden()["frames"]:
            self.assertAlmostEqual(anchor_time(f["anchor"], float(f["offset"]), REF_PLAN), f["t"], delta=0.006, msg=f["anchor"])

    def test_unknown_anchor_fails_loud(self) -> None:
        with self.assertRaises(KeyError):
            anchor_time("nope_9", 0.0, REF_PLAN)


class MadTest(unittest.TestCase):
    def test_identical_zero_and_uniform_shift(self) -> None:
        import numpy as np

        a = np.zeros((4, 4, 3), np.uint8)
        self.assertEqual(mad(a, a), 0.0)
        self.assertAlmostEqual(mad(a, a + 3), 3.0)

    def test_shape_mismatch_raises(self) -> None:
        import numpy as np

        with self.assertRaises(ValueError):
            mad(np.zeros((2, 2, 3)), np.zeros((3, 2, 3)))


class RunnerTest(unittest.TestCase):
    def test_chunk_ranges_cover_without_gap(self) -> None:
        r = chunk_ranges(7018, 4)
        self.assertEqual(r[0][0], 0)
        self.assertEqual(r[-1][1], 7018)
        self.assertTrue(all(a[1] == b[0] for a, b in zip(r, r[1:])))

    def test_srt_time(self) -> None:
        self.assertEqual(srt_time(235.9996), "00:03:56,000")
        self.assertEqual(srt_time(1.2), "00:00:01,200")

    def test_srt_matches_golden_numerically(self) -> None:
        # 골든 SRT 39번은 "00:03:55,1000"(원본 반올림 버그) — 문자열이 아니라 시각 값으로 비교한다
        def times(text: str) -> list[float]:
            return [int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
                    for h, m, s, ms in re.findall(r"(\d\d):(\d\d):(\d\d),(\d{3,4})", text)]

        golden = (GOLDEN / "hormuz_korea_ko.srt").read_text(encoding="utf-8")
        ours = build_srt(REF_PLAN_MODEL)
        self.assertEqual(len(times(ours)), 90)
        for a, b in zip(times(ours), times(golden)):
            self.assertAlmostEqual(a, b, delta=0.0015)
        self.assertEqual(re.sub(r"[\d:,>\- ]+\n", "", ours), re.sub(r"[\d:,>\- ]+\n", "", golden))

    def test_description_equals_golden(self) -> None:
        golden = (GOLDEN / "youtube_description.txt").read_text(encoding="utf-8")
        ours = build_description(REF_PLAN_MODEL, load_description(REPO / "projects/hormuz_korea"))
        self.assertEqual(ours.rstrip("\n"), golden.rstrip("\n"))

    def test_transition_times_centered(self) -> None:
        ts = transition_times(100.0)
        self.assertEqual(len(ts), 8)
        self.assertAlmostEqual(sum(ts) / 8, 100.0)
        self.assertAlmostEqual(ts[1] - ts[0], 0.3)


class ExpectedDeltasTest(unittest.TestCase):
    """D34 — 골든 의도된 차이 등재 파일(골든 PNG 는 그대로)."""

    def test_missing_file_is_empty(self) -> None:
        import tempfile  # noqa: PLC0415
        from unittest import mock  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d, mock.patch.object(golden_compare, "GOLDEN_DIR", Path(d)):
            self.assertEqual(load_expected_deltas(), {})

    def test_fields_required(self) -> None:
        import tempfile  # noqa: PLC0415
        from unittest import mock  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d, mock.patch.object(golden_compare, "GOLDEN_DIR", Path(d)):
            (Path(d) / "expected_deltas.json").write_text(json.dumps({"deltas": {"09_ask_1": {"reason": "x"}}}))
            with self.assertRaises(ValueError):
                load_expected_deltas()
            (Path(d) / "expected_deltas.json").write_text(json.dumps({"deltas": {"09_ask_1": {
                "reason": "x", "decision": "D-0026", "old_t": 1.0, "new_t": 1.5}}}))
            self.assertIn("09_ask_1", load_expected_deltas())


if __name__ == "__main__":
    unittest.main()
