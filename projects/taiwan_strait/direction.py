"""대만해협 예시 연출 (v2.2.0, D-0015 §1-6) — 카메라 하나, 마커 하나."""

from __future__ import annotations

from engine.camera import Director
from engine.timebase import Timebase


def direct(tb: Timebase) -> Director:
    S, SC_END = tb.S, tb.SC_END  # noqa: N806
    d = Director()
    d.cam(0, 120.3, 24.2, 9.0, 0, "cut")
    d.ev("marker", S("open_0", 0.3), SC_END("open"), lon=121.56, lat=25.04, label="타이베이", sub="대만 수도", side="right", hl=True)
    return d
