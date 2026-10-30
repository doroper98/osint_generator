"""발언 자리 clip_hold (v7.4.0, back_and_forth D-0274 §2③·D-0276, 사용자 의견 UF-141) — 문장 뒤 내레이션 없는 구간 + 번역 자막 + {hold: sid} 앵커."""

from __future__ import annotations

import unittest

import cairo

from engine.direction import resolve_anchor
from engine.subtitles import subtitle_boxes
from engine.timebase import Timebase
from rules import load_rules
from script.schema import Plan, Script
from script.timeline import layout, sentence_rows

G = load_rules().layout_480p.timeline_gaps


def _plan(hold: bool = True) -> Plan:
    s = lambda t, **kw: dict(date="2026.09.16", text=t, sources=["c1"], **kw)  # noqa: E731
    h = {"hold_after": {"mid": "fed_clip_0916_decision", "sec": 16.5, "subtitle": ["연방공개시장위원회는 기준금리 목표 범위를", "0.25%p 올린 3.75~4%로 정했습니다."],
                        "sources": ["clm_q1"]}} if hold else {}
    sc = Script.model_validate(dict(title="t", subtitle="s", date="2026.10.30", scenes=[
        dict(id="a", sentences=[s("가.", **h), s("나.")])]))
    rows = sentence_rows(sc)
    for i, r in enumerate(rows):
        r.update(mp3="x.mp3", npy="x.npy", dur=2.0, tts=r["tts"])
    holds: list = []
    cards, ss, total = layout(rows, None, None, holds)
    return Plan(sentences=rows, cards=cards, scene_start=ss, total=total, voice="v", title="t", subtitle="s", date="d", holds=holds)


class ClipHoldTest(unittest.TestCase):
    def test_layout_inserts_gap(self) -> None:
        p, q = _plan(True), _plan(False)
        h = p.holds[0]
        self.assertEqual((h.sid, h.mid), ("a_0", "fed_clip_0916_decision"))
        self.assertAlmostEqual(h.t0, p.sentences[0].t1 + G.gap_sec)
        self.assertAlmostEqual(h.t1 - h.t0, 16.5)
        self.assertAlmostEqual(p.sentences[1].t0 - q.sentences[1].t0, 16.5 + G.gap_sec)   # 다음 문장은 자리만큼 밀린다

    def test_hold_anchor(self) -> None:
        tb = Timebase(_plan(True))
        h = tb.plan.holds[0]
        self.assertEqual(resolve_anchor({"hold": "a_0"}, tb), h.t0)
        self.assertEqual(resolve_anchor({"hold": "a_0", "edge": "end"}, tb), h.t1)

    def test_subtitle_during_hold(self) -> None:
        tb = Timebase(_plan(True))
        h = tb.plan.holds[0]
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        self.assertEqual(len(subtitle_boxes(ctx, tb, (h.t0 + h.t1) / 2)), 2)   # 번역 두 줄
        nxt = tb.plan.sentences[1].t0
        self.assertEqual(subtitle_boxes(ctx, tb, (h.t1 + 0.25 + nxt - 0.05) / 2), [])   # 자리 끝 뒤 ~ 다음 문장 전 = 자막 없음


if __name__ == "__main__":
    unittest.main()
