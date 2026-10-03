"""Phase 2 엔진 계약 테스트 (v2.1.0, D-0010 §1-14).

자산 없이 도는 순수 함수만 검사한다: timebase, ym↔lat 왕복, 카메라 보간(로그 줌·cut·드리프트),
강조 구간 분할, 레지스트리·스키마 거부, 자막·설명문, 타임라인 배치.
"""

from __future__ import annotations

import math
import unittest
from unittest import mock

import numpy as np
from pydantic import ValidationError

from engine import camera as camera_mod
from engine.camera import Director, build_camera, cam
from engine.events import BadgeEvent, CardEvent, PanelVersus
from engine.mux import Chapter, Description, build_description, build_srt, srt_time
from engine.stage import MercatorStage, lat_of, ym, ymv
from engine.registry import RegistryError, validate_events
from engine.subtitles import emphasis_flags, split_runs
from engine.timebase import Timebase, clamp01, ease_io, smooth, window
from rules import load_rules
from script.schema import Plan, Sentence
from script.timeline import layout, split_emphasis


def _plan() -> Plan:
    sents = []
    t = 1.2
    for sc, n in (("open", 2), ("route", 2)):
        for k in range(n):
            sents.append(dict(sid=f"{sc}_{k}", scene=sc, date="2026.09.18", text="가나다 라마바", tts="가나다 라마바",
                              segments=[["가나다 라마바", 0]], mp3="x.mp3", npy="x.npy", dur=2.0, t0=t, t1=t + 2.0))
            t += 2.5
    return Plan(sentences=sents, cards=[dict(kind="title", t0=6.0, t1=11.6), dict(kind="end", t0=20.0, t1=31.0)],
                scene_start={"open": 1.2, "route": 12.0}, total=31.5, voice="edge-tts test", title="T", subtitle="S",
                date="2026.09.26")


class TimebaseTest(unittest.TestCase):
    def test_easing_bounds(self) -> None:
        for f in (smooth, ease_io):
            self.assertEqual(f(-1), 0.0)
            self.assertEqual(f(2), 1.0)
            self.assertAlmostEqual(f(0.5), 0.5)
        self.assertEqual(clamp01(3), 1.0)

    def test_window(self) -> None:
        self.assertEqual(window(0.0, 1.0, 3.0), 0.0)
        self.assertEqual(window(2.0, 1.0, 3.0), 1.0)
        self.assertEqual(window(4.0, 1.0, 3.0), 0.0)

    def test_anchors(self) -> None:
        tb = Timebase(_plan())
        self.assertEqual(tb.S("open_1", 0.1), 3.7 + 0.1)
        self.assertEqual(tb.E("open_0"), 3.2)
        self.assertEqual(tb.SC("route"), 12.0)
        self.assertAlmostEqual(tb.SC_END("open"), 12.0 - 0.35)
        self.assertEqual(tb.SC_END("route"), 31.5)
        self.assertAlmostEqual(tb.at_word("open_0", "라마바"), 1.2 + 4 / 7 * 2.0)
        with self.assertRaises(KeyError):
            tb.S("nope")
        self.assertIsNone(tb.cur_sentence(0.0))
        self.assertEqual(tb.cur_sentence(3.5), "open_1")
        self.assertTrue(tb.in_fullcard(8.0))


class ProjectionTest(unittest.TestCase):
    def test_ym_roundtrip(self) -> None:
        for lat in (-60.0, -12.0, 0.0, 26.55, 37.57, 80.0):
            self.assertAlmostEqual(lat_of(ym(lat)), lat, places=9)
        self.assertAlmostEqual(ym(0.0), 0.0, places=12)
        self.assertAlmostEqual(float(ymv(np.array([37.57]))[0]), ym(37.57), places=12)


class CameraTest(unittest.TestCase):
    def test_move_log_zoom_and_drift(self) -> None:
        fps = 10
        keys = [cam(0, 0.0, 0.0, 10.0, 0, "cut"), cam(1.0, 10.0, 0.0, 40.0, 2.0)]
        c = build_camera(keys, 50, fps)
        mid = c[20]  # t=2.0 → 이동 중간(ease_io(0.5)=0.5)
        w_from = c[9][2]  # 이동 시작 직전 프레임(첫 cut 이후 드리프트가 이미 조금 들어가 있다 — v3 동작)
        self.assertLess(w_from, 10.0)
        self.assertAlmostEqual(mid[2], math.sqrt(w_from * 40.0))  # 로그 보간 = 기하 평균
        # v5.5.0 move_path fixed_point — 중심은 폭과 같은 비율로 움직인다(RENDER-AP-007). 선형(e) 이면 5.0
        self.assertAlmostEqual(mid[0], 10.0 * (mid[2] - w_from) / (40.0 - w_from))
        with mock.patch.object(camera_mod, "_PATH", "linear"):
            self.assertAlmostEqual(build_camera(keys, 50, fps)[20][0], 5.0)
        d = load_rules().shot_grammar.drift
        t_after = 4.9 - 3.0
        self.assertAlmostEqual(c[49][2], 40.0 * (1 - d.amount * (1 - math.exp(-t_after / d.tau_sec))))
        self.assertLess(c[49][2], 40.0)

    def test_cut_is_instant(self) -> None:
        keys = [cam(0, 0.0, 0.0, 10.0, 0, "cut"), cam(1.0, *MercatorStage().to_world(lon=50.0, lat=20.0), 5.0, 0, "cut")]
        c = build_camera(keys, 20, 10)
        self.assertAlmostEqual(c[10][0], 50.0)
        self.assertAlmostEqual(c[10][1], ym(20.0))

    def test_dip_argument_form(self) -> None:
        d = Director(MercatorStage())
        d.dip(10.0, 88.5, 21.5, 92)
        self.assertEqual(d.events, [{"type": "dip", "t0": 9.5, "t1": 10.5}])
        k = d.keys[0]
        self.assertEqual((k.t, k.x, k.w, k.dur, k.mode), (10.0, 88.5, 92, 0, "cut"))
        d.dip(3.0, 1.0, 2.0, 3.0, under=True)
        self.assertTrue(d.events[-1]["under"])


class EmphasisTest(unittest.TestCase):
    def test_split(self) -> None:
        segs = split_emphasis("이란은 곧바로 호르무즈 해협을 닫았습니다.", ["해협을 닫았습니다"])
        self.assertEqual(segs, [["이란은 곧바로 호르무즈 ", 0], ["해협을 닫았습니다", 1], [".", 0]])
        self.assertEqual(split_emphasis("abc", []), [["abc", 0]])
        self.assertEqual(split_emphasis("abcabc", ["abc"]), [["abc", 1], ["abc", 0]])

    def test_runs(self) -> None:
        txt, flags = emphasis_flags([("가나 ", 0), ("다라", 1), ("마", 0)])
        self.assertEqual(txt, "가나 다라마")
        self.assertEqual(split_runs("나 다라", 1, flags), [("나 ", 0), ("다라", 1)])

    def test_schema_rejects_missing_emphasis(self) -> None:
        with self.assertRaises(ValidationError):
            Sentence(date="2026.09", text="가나다", emphasis=["라"])
        with self.assertRaises(ValidationError):
            Sentence(date="2026-09", text="가나다")


class RegistrySchemaTest(unittest.TestCase):
    def test_unregistered_type_before_render(self) -> None:
        with self.assertRaises(RegistryError):
            validate_events([{"type": "marker", "t0": 0, "t1": 1, "lon": 0, "lat": 0, "label": "a"},
                             {"type": "stamp", "t0": 0, "t1": 1}])

    def test_missing_and_unknown_fields(self) -> None:
        with self.assertRaises(RegistryError):
            validate_events([{"type": "marker", "t0": 0, "t1": 1, "lon": 0, "lat": 0}])  # label 없음
        with self.assertRaises(RegistryError):
            validate_events([{"type": "boom", "t0": 0, "t1": 1, "lon": 0, "lat": 0, "zoom": 2}])  # 모르는 필드
        with self.assertRaises(RegistryError):
            validate_events([{"type": "panel", "t0": 0, "t1": 1, "kind": "gantt", "title": "x"}])  # planned 패널

    def test_model_rules(self) -> None:
        with self.assertRaises(ValidationError):
            BadgeEvent(type="badge", t0=0, t1=1, lon=0, lat=0, kind="person", flag="kr")  # pid 없음
        with self.assertRaises(ValidationError):
            CardEvent(type="card", t0=0, t1=1, tag="x", accent="pink")  # 레지스트리 밖 accent
        with self.assertRaises(ValidationError):
            PanelVersus(type="panel", kind="versus", t0=0, t1=1, title="x",
                        sides=[dict(title="a", src="s", items=[dict(text="t", t=0)])])  # 한쪽만
        with self.assertRaises(ValidationError):
            CardEvent(type="card", t0=2, t1=1, tag="x", accent="gold")  # t1 < t0

    def test_validated_defaults_match_v3(self) -> None:
        out = validate_events([{"type": "marker", "t0": 0, "t1": 1, "lon": 0, "lat": 0, "label": "a"}])[0]
        self.assertEqual((out["side"], out["icon"], out["hl"], out["sub"]), ("right", "dot", False, ""))


class TimelineMuxTest(unittest.TestCase):
    def test_layout(self) -> None:
        rows = [dict(sid=f"{s}_0", scene=s, dur=2.0) for s in ("open", "route", "war")]
        cards, starts, total = layout(rows)
        g = load_rules().layout_480p
        self.assertEqual(starts["open"], g.timeline_gaps.lead_sec)
        title = cards[0]
        self.assertEqual(title.kind, "title")
        self.assertAlmostEqual(title.t0, rows[0]["t1"] + g.timeline_gaps.gap_sec + 0.2)
        self.assertAlmostEqual(starts["route"], title.t0 - 0.2 + g.title_card.dur_sec + 0.6)
        self.assertAlmostEqual(starts["war"], rows[1]["t1"] + g.timeline_gaps.gap_sec + g.timeline_gaps.scene_gap_sec)
        self.assertEqual(cards[-1].kind, "end")
        self.assertAlmostEqual(total, cards[-1].t1 + 0.5)

    def test_srt_and_description(self) -> None:
        p = _plan()
        self.assertEqual(srt_time(3661.5), "01:01:01,500")
        srt = build_srt(p)
        self.assertTrue(srt.startswith("1\n00:00:01,200 --> 00:00:03,350\n가나다 라마바\n"))
        d = Description(headline="H", summary="S", chapters=[Chapter(at="open", label="a"), Chapter(at="TITLE", label="b"),
                                                                 Chapter(at="route", label="c")], footer=["f"])
        self.assertEqual(build_description(p, d), "H\n\nS\n\n챕터\n0:00 a\n0:06 b\n0:12 c\n\nf")


if __name__ == "__main__":
    unittest.main()
