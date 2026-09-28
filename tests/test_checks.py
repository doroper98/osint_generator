"""engine/checks — 결정적 사전 검사 17 §3 (v3.1.0, back_and_forth D-0047 작업 6·9). 가짜 프로젝트 객체로 항목별 검사."""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

import numpy as np

from engine import checks
from engine.camera import CamKey
from engine.projection import ym
from rules import load_rules

SG = load_rules().shot_grammar
_MISSING_FONTS = checks.missing_fonts()
TIERS = {"W": {"lon0": 20.0, "lon1": 150.0, "lat0": -10.0, "lat1": 60.0, "levels": []}}


def _sent(sid: str, scene: str, t0: float, text: str = "문장입니다", date: str = "2026.09.18") -> NS:
    return NS(sid=sid, scene=scene, t0=t0, t1=t0 + 3, text=text, date=date)


def _P(events: list[dict] | None = None, keys: list[CamKey] | None = None, sentences: list[NS] | None = None) -> NS:  # noqa: N802
    sents = sentences or [_sent("a_0", "a", 1.0)]
    n = 24 * 60
    cams = np.tile(np.array([56.0, ym(26.0), 14.0]), (n, 1))
    tb = NS(total=60.0, in_fullcard=lambda t: False)
    return NS(events=events or [], keys=keys or [], n_frames=n, cams=cams,
              plan=NS(sentences=sents, title="제목", subtitle="부제", date="2026.09", total=60.0),
              R=NS(tb=tb, assets=NS(tiers=TIERS, base={})))


class ChecksTest(unittest.TestCase):
    def test_date_format(self) -> None:
        P = _P(sentences=[_sent("a_0", "a", 1.0, date="2026/09")])  # noqa: N806
        self.assertEqual(len([s for s in P.plan.sentences if not checks.DATE_RE.match(s.date)]), 1)

    def test_subtitle_lines(self) -> None:
        P = _P(sentences=[_sent("a_0", "a", 1.0, text="아주 긴 자막 " * 30)])  # noqa: N806
        self.assertEqual(len(checks.check_subtitles(P)), 1)
        self.assertEqual(checks.check_subtitles(_P()), [])

    @unittest.skipIf(bool(_MISSING_FONTS), f"프로젝트 글꼴 없음 {_MISSING_FONTS} — `python tools/fetch_data.py fonts` 필요(D-0050 NB10)")
    def test_glyphs(self) -> None:
        self.assertEqual(checks.check_glyphs(_P(events=[{"type": "card", "tag": "정상 문자열 123"}])), [])
        miss = checks.check_glyphs(_P(events=[{"type": "card", "tag": "쐐기 𓀀"}]))   # 이집트 상형문자 — 프로젝트 글꼴에 없음
        self.assertEqual(len(miss), 1)
        self.assertIn("U+13000", miss[0])

    def test_frames_sid_only_while_speaking(self) -> None:
        """문장이 끝난 뒤(엔딩 카드)에는 sid 를 비우고 after_sid·card 로 적는다(v3.2.0 taiwan_ai 거짓 hard)."""
        sent = NS(t0=1.0, t1=4.0, text="문장입니다")
        tb = NS(cur_sentence=lambda t: "a_0" if t >= 0.7 else None, sent={"a_0": sent})
        P = NS(R=NS(tb=tb), events=[], plan=NS(cards=[NS(kind="end", t0=10.0, t1=20.0)]))  # noqa: N806
        rows = checks.frames_info(P, [2.0, 7.0, 12.0], ["a", "b", "c"])["frames"]
        self.assertEqual([r["sid"] for r in rows], ["a_0", None, None])
        self.assertEqual([r["after_sid"] for r in rows], [None, "a_0", "a_0"])
        self.assertEqual([r["card"] for r in rows], [None, None, "end"])

    def test_missing_font_is_loud(self) -> None:
        """대체 글꼴로 조용히 검사하지 않는다 — 없는 패밀리는 FontMissingError(P6, NB10)."""
        with self.assertRaises(checks.FontMissingError):
            checks._cmap("NoSuchFamily Zz9")  # noqa: SLF001

    def test_shots(self) -> None:
        keys = [CamKey(t=0, x=0, y=0, w=10, dur=0, mode="cut"), CamKey(t=5, x=1, y=1, w=10, dur=3, mode="move"),
                CamKey(t=9, x=2, y=2, w=10, dur=3, mode="move")]   # 두 번째 이동 전 머무름 1초 + 한 장면 이동 2회
        P = _P(keys=keys, sentences=[_sent("a_0", "a", 0.0)])  # noqa: N806
        out = checks.check_shots(P)
        self.assertTrue(any("머무름" in o for o in out))
        self.assertTrue(any("카메라 이동 2" in o for o in out))

    def test_dip_frequency(self) -> None:
        dips = [{"type": "dip", "t0": t, "t1": t + 1} for t in (5, 15, 25)]
        out = checks.check_shots(_P(events=dips))
        self.assertTrue(any("암전 3회" in o for o in out))

    def test_offscreen_badge(self) -> None:
        low = {"type": "badge", "t0": 0.0, "t1": 5.0, "lon": 56.0, "lat": 21.5, "kind": "flag", "flag": "cn", "R": 17, "label": "중국"}
        ok = dict(low, lat=26.0, label="가운데")
        out = checks.check_offscreen(_P(events=[low, ok]))
        self.assertEqual(len(out), 1)
        self.assertIn("중국", out[0])

    def test_offscreen_marker_label(self) -> None:
        """D-0049 쟁점 4 — 지점 마커 라벨도 잘림 0(hard). 왼쪽 끝 마커의 left 라벨은 잘린다."""
        cam_x = 56.0
        edge = {"type": "marker", "t0": 0.0, "t1": 5.0, "lon": cam_x - 6.6, "lat": 26.0, "label": "호르무즈 해협", "side": "left"}
        right = dict(edge, side="right", label="오른쪽 라벨")
        out = checks.check_offscreen(_P(events=[edge, right]))
        self.assertEqual(len(out), 1)
        self.assertIn("마커 호르무즈 해협", out[0])

    def test_marker_reserved_box_label_only(self) -> None:
        """예약 영역 상자는 v3 그대로 라벨 폭만 — 부제 폭은 화면 밖 검사에만(골든 route 컷 불변, v3.1.0 실측 회귀)."""
        import cairo  # noqa: PLC0415

        from engine.layers.markers import marker_box  # noqa: PLC0415

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = {"label": "해협", "sub": "페르시아만에서 먼바다로 나가는 유일한 바닷길", "side": "right"}
        self.assertEqual(marker_box(ctx, e, 100, 100), marker_box(ctx, {**e, "sub": None}, 100, 100))
        self.assertGreater(marker_box(ctx, e, 100, 100, with_sub=True)[2], marker_box(ctx, e, 100, 100)[2])

    def test_offscreen_ignored_when_covered(self) -> None:
        low = {"type": "badge", "t0": 0.0, "t1": 5.0, "lon": 56.0, "lat": 21.5, "kind": "flag", "flag": "cn", "R": 17, "label": "중국"}
        panel = {"type": "panel", "t0": 0.0, "t1": 5.0}
        self.assertEqual(checks.check_offscreen(_P(events=[low, panel])), [])

    def test_forbidden(self) -> None:
        self.assertEqual(checks.check_forbidden(_P(), {"features_used": {"vignette": False}}), [])
        self.assertEqual(len(checks.check_forbidden(_P(), {"features_used": {"vignette": True}})), 1)
        self.assertEqual(len(checks.check_forbidden(_P(events=[{"type": "stamp"}]), {})), 1)

    def test_severity_table(self) -> None:
        self.assertEqual(set(checks.HARD) | set(checks.WARN),
                         {"overlap", "offscreen", "glyphs", "shots", "media_beats", "labels", "date", "subtitles", "rights", "forbidden"})
        self.assertEqual(set(checks.WARN), {"shots", "media_beats"})   # D-0047 §0-4 숏 규칙 = warning


if __name__ == "__main__":
    unittest.main()


class PreviewHardFailTest(unittest.TestCase):
    """17 §3·D-0048 — checks hard 가 있으면 preview 단계 StageResult ok=False(시각 검수로 가지 않는다)."""

    def test_hard_fails_stage(self) -> None:
        import io  # noqa: PLC0415
        import json  # noqa: PLC0415
        import tempfile  # noqa: PLC0415
        from contextlib import redirect_stdout  # noqa: PLC0415
        from pathlib import Path  # noqa: PLC0415
        from unittest import mock  # noqa: PLC0415

        from engine import render  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "prev").mkdir()
            fake = NS(root=root, warnings=[])

            def fake_preview(P, times, labels=None):  # noqa: ANN001, ANN202, N803
                (root / "prev" / "checks.json").write_text(json.dumps({"passed": False, "items": [
                    {"id": "offscreen", "severity": "hard", "details": ["뱃지 x 화면 밖"]}]}), encoding="utf-8")
                return []

            buf = io.StringIO()
            with mock.patch.object(render, "load_project", return_value=fake), \
                 mock.patch.object(render, "preview_times", return_value=[("t=1.00", 1.0)]), \
                 mock.patch.object(render, "preview", side_effect=fake_preview), redirect_stdout(buf):
                rc = render.main([str(root), "--preview", "auto"])
            res = json.loads(buf.getvalue().strip().splitlines()[-1])
        self.assertEqual(rc, 1)
        self.assertFalse(res["ok"])
        self.assertIn("offscreen", res["errors"][0])
