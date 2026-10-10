"""V3 호르무즈 Supertonic + MMS 재현 (v5.17.0, back_and_forth D-0167 §3-6).

도구(자산 없이): 컷 대응표 25행(옛/새 시각·이동·파일 이름 규칙), 클릭음 표본 구간 선택(문장 안 10·쉼 뒤 5)·클릭 모양.
호르무즈 V3 산출물(프로젝트 음성·전편이 있어야 한다 — 없으면 skip 이 아니라 실패, test_provenance_e2e 와 같은 규약):
plan 의 정렬이 전부 MMS(`at_word` 가 새 정렬을 씀), 전편 믹스 측정이 audio/qa 허용 범위 안.
V3 기준선 25컷 픽셀 대조는 `tests/anti_inertia/test_provenance_e2e.py`(phaseV3 기준선).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from engine.golden import load_golden
from tools import click_sample as CS
from tools import v3_cut_table as CT


def _plan(scale: float) -> dict:
    """골든 앵커 문장마다 t0 = 기준 × scale 인 합성 plan(dict)."""
    sids = [f["anchor"] for f in load_golden()["frames"] if f["anchor"] not in ("TITLE", "END")]
    rows = [{"sid": sid, "t0": (5.0 + 10.0 * k) * scale, "dur": 4.0 * scale, "text": "가", "tts": "가"} for k, sid in enumerate(sids)]
    return {"sentences": rows, "cards": [{"kind": "title", "t0": 3.0 * scale, "t1": 6.0 * scale}],
            "total": (10.0 * len(sids) + 20.0) * scale, "voice": f"v{scale}"}


class CutTableTest(unittest.TestCase):
    def test_25_rows_shift_and_names(self) -> None:
        old, new = _plan(1.0), _plan(0.9)
        rows = CT.cut_rows(old, new)
        self.assertEqual(len(rows), 25)
        self.assertEqual(len(rows), len(load_golden()["frames"]))
        for r in rows:
            self.assertAlmostEqual(r["shift"], r["new_t"] - r["old_t"], places=3)
            self.assertEqual(r["new_png"], CT.png_name(r["new_t"]))
            self.assertEqual(r["old_dur"] is None, r["anchor"] in ("TITLE", "END"))
        self.assertEqual(CT.png_name(7.824), "p_0007.82.png")   # engine.render 프리뷰 이름 규칙과 같아야 한다

    def test_summary_counts_alignment_sources(self) -> None:
        old, new = _plan(1.0), _plan(0.9)
        for s in new["sentences"]:
            s["alignment"] = {"source": "mms_forced_alignment"}
        summ = CT.summary(old, new, None, {"features_used": {"at_word": {"aligned": 7, "ratio": 0}}})
        self.assertEqual(summ["new_alignment_sources"], {"mms_forced_alignment": len(new["sentences"])})
        self.assertEqual(summ["new_at_word"], {"aligned": 7, "ratio": 0})


class ClickSampleTest(unittest.TestCase):
    def _anchors(self) -> list[dict]:
        out = []
        for k in range(40):
            out.append({"t": 1.0 + k * 1.5, "sid": f"s{k // 4}", "word": "w", "kind": "pause" if k % 4 == 0 else "in", "text": "t"})
        return out

    def test_window_has_10_in_and_5_after_pause(self) -> None:
        a, picks = CS.choose_window(self._anchors(), 70.0, None)
        self.assertEqual(sum(p["kind"] == "in" for p in picks), CS.N_IN)
        self.assertEqual(sum(p["kind"] == "pause" for p in picks), CS.N_PAUSE)
        self.assertTrue(all(a <= p["t"] <= a + CS.WINDOW_SEC for p in picks))
        self.assertEqual([p["t"] for p in picks], sorted(p["t"] for p in picks))

    def test_no_window_is_error(self) -> None:
        with self.assertRaises(ValueError):
            CS.choose_window([a for a in self._anchors() if a["kind"] == "in"], 70.0, None)

    def test_click_shape(self) -> None:
        c = CS.click()
        self.assertEqual(len(c), int(CS.CLICK_SEC * CS.SR))
        self.assertLessEqual(float(np.abs(c).max()), CS.CLICK_AMP)
        self.assertLess(float(np.abs(c[-20:]).max()), 0.05 * CS.CLICK_AMP)   # 끝은 거의 0(감쇠)


REPO = Path(__file__).resolve().parent.parent
HORMUZ = REPO / "projects" / "hormuz_korea"
PREP = "호르무즈 V3 산출물이 없다 — python -m script.plan projects/hormuz_korea → audio.mix → engine.render --res final → engine.mux"


class HormuzV3Test(unittest.TestCase):
    def test_alignment_is_mms_everywhere(self) -> None:
        from engine.project import load_plan  # noqa: PLC0415
        from engine.timebase import Timebase  # noqa: PLC0415

        plan = load_plan(HORMUZ)
        self.assertTrue(plan.voice.startswith("supertonic"), PREP)
        self.assertEqual({s.alignment.source for s in plan.sentences if s.alignment}, {"mms_forced_alignment"})
        self.assertTrue(all(s.alignment is not None for s in plan.sentences))
        tb = Timebase(plan)
        for s in plan.sentences:
            self.assertEqual(tb.alignment(s.sid)["alignment_source"], "mms_forced_alignment", s.sid)
        t = tb.at_word("ask_1", "독일")
        self.assertEqual(tb.word_anchors[-1]["alignment_source"], "mms_forced_alignment")
        self.assertGreaterEqual(t, tb.S("ask_1"))

    def test_final_mix_within_audio_qa_range(self) -> None:
        p = HORMUZ / "out" / "audio_qa.json"
        self.assertTrue(p.exists(), PREP)
        qa = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(qa["hard"], [])
        self.assertTrue(qa["peak_ok"])


if __name__ == "__main__":
    unittest.main()
