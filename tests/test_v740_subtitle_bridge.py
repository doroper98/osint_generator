"""v7.4.0 사용자 의견 UF-911 "저 짧은 영상에서도 자막이 깜빡거리는 현상이 나오노"(D927, RENDER-AP-035).

원인 둘: ① 문장이 바뀔 때마다 앞 자막(과 뒤 흰 번짐)이 완전히 꺼졌다가 다음 자막이 켜졌다 ② 무대 전환 dip(밝은 판)이 자막 위에 칠해졌다.
- 디자인 시스템 무대: 쉼이 rules skin.subtitle.bridge_gap_sec 이하면 자막이 꺼지는 순간이 없다(한 프레임도). 쉼이 더 길면 종전처럼 사라진다.
- 어느 시각에도 문장은 하나만 보인다(바로 교체 — 두 문장이 겹쳐 뭉개지는 프레임 없음).
- 실제 엔진 경로(시연 프로젝트): 첫 문장 등장 뒤 둘째 문장 끝까지 모든 프레임에 자막 글자가 있다.
- dip 은 날짜·자막 아래에 칠한다(디자인 시스템 무대).
- 디자인 시스템이 꺼진 무대는 종전 시간 모델 그대로(바이트 동일은 ident 대조).
"""

from __future__ import annotations

import inspect
import tempfile
import types
import unittest
from pathlib import Path

import numpy as np

from engine import skin
from engine.style import FPS, SKIN, SUBTITLE
from engine.subtitles import LEAD_SEC, OUT_HOLD_SEC, bridged_sentences


def _tb(spans: list[tuple[float, float]]) -> types.SimpleNamespace:
    sent = {f"s{i}": types.SimpleNamespace(t0=a, t1=b, segments=[("가나다", 0)]) for i, (a, b) in enumerate(spans)}
    return types.SimpleNamespace(order=list(sent), sent=sent)


class BridgeModelTest(unittest.TestCase):
    def test_no_off_moment_inside_bridge_gap(self) -> None:
        gap = SKIN.subtitle.bridge_gap_sec
        tb = _tb([(1.0, 3.0), (3.0 + gap * 0.5, 6.0), (6.0, 8.0)])   # 쉼 = 절반, 0
        t = 1.0 + 0.3
        while t <= 8.0:
            vis = bridged_sentences(tb, t)
            self.assertEqual(len(vis), 1, t)                       # 한 시각에 한 문장(겹쳐 뭉개지지 않는다)
            self.assertAlmostEqual(vis[0][1], 1.0, msg=str(t))     # 꺼지거나 흐려지는 순간이 없다
            t += 1 / (FPS * 4)

    def test_long_gap_still_fades_out(self) -> None:
        gap = SKIN.subtitle.bridge_gap_sec
        tb = _tb([(1.0, 3.0), (3.0 + gap + 2.0, 9.0)])
        self.assertEqual(bridged_sentences(tb, 3.0 + OUT_HOLD_SEC + 0.2), [])   # 긴 쉼(타이틀 카드·장면 사이)은 비운다
        self.assertEqual([s for s, _ in bridged_sentences(tb, 3.0 + gap + 2.0 - LEAD_SEC + 0.3)], ["s1"])

    def test_rule_values(self) -> None:
        self.assertGreaterEqual(SKIN.subtitle.bridge_gap_sec, 1.0)   # 내레이션의 보통 쉼(0.3~0.7초)을 다 덮는다


class EngineTest(unittest.TestCase):
    def test_showcase_subtitle_never_blinks_between_sentences(self) -> None:
        from tests.test_v740_skin import showcase_project  # noqa: PLC0415
        import engine.project as EP  # noqa: N812, PLC0415
        from engine.render import render_frame  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            P = EP.load_project(showcase_project(Path(d) / "s"), animatic=True)  # noqa: N806
            try:
                self.assertTrue(skin.active())
                s0, s1 = P.plan.sentences[0], P.plan.sentences[1]
                self.assertLessEqual(s1.t0 - s0.t1, SKIN.subtitle.bridge_gap_sec)
                w, h = P.R.out.width, P.R.out.height
                y0, y1 = int((SUBTITLE.last_line_y - SUBTITLE.size * 2.2) * P.R.out.k), int((SUBTITLE.last_line_y + SUBTITLE.size * 0.4) * P.R.out.k)
                off = []
                for i in range(int((s0.t0 + 0.4) * FPS), int(s1.t1 * FPS)):
                    _, buf = render_frame(P, i)
                    band = np.frombuffer(bytes(buf), np.uint8).reshape(h, w, 4)[y0:y1, :, :3].mean(-1)
                    if int((band < 90).sum()) < 40:   # 자막 띠에 짙은 글자 화소가 없다 = 자막이 꺼진 프레임
                        off.append(i)
                self.assertEqual(off, [], "문장 사이에 자막이 꺼진 프레임")
            finally:
                skin.apply(None)

    def test_dip_is_painted_below_date_and_subtitle_under_skin(self) -> None:
        from engine import render  # noqa: PLC0415

        src = inspect.getsource(render._render_frame)
        below = src.index("dip_below = skin.active()")
        self.assertLess(below, src.index("draw_date(ctx, R, t)"))
        self.assertLess(src.index('if e["type"] == "dip" and not e.get("under")', below), src.index("draw_subtitle(ctx, R, t)"))


if __name__ == "__main__":
    unittest.main()
