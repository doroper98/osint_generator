"""문장 앵커 시간축과 이징 (v2.1.0, 19 부록 D `S, E, SC, SC_END, at_word, clamp01…window`).

모든 연출 시각은 문장 앵커로만 계산한다(02 §1). 절대 초를 하드코딩하지 않는다.
"""

from __future__ import annotations

from typing import Optional

from script.schema import Plan


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def smooth(x: float) -> float:
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_io(x: float) -> float:
    x = clamp01(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x: float) -> float:
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_back(x: float) -> float:
    x = clamp01(x)
    c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def window(t: float, t0: float, t1: float, fin: float = 0.5, fout: float = 0.5) -> float:
    if t < t0 or t > t1:
        return 0.0
    return min(smooth((t - t0) / fin) if fin > 0 else 1, smooth((t1 - t) / fout) if fout > 0 else 1)


class Timebase:
    """plan.json 에 묶인 앵커 함수. 없는 문장 id 는 KeyError(조용한 폴백 금지)."""

    def __init__(self, plan: Plan) -> None:
        self.plan = plan
        self.total = plan.total
        self.sent = {s.sid: s for s in plan.sentences}
        self.order = [s.sid for s in plan.sentences]
        self.scene_start = plan.scene_start
        self.scenes = list(plan.scene_start)

    def S(self, sid: str, off: float = 0.0) -> float:  # noqa: N802 — v3 앵커 이름 유지
        return self.sent[sid].t0 + off

    def E(self, sid: str, off: float = 0.0) -> float:  # noqa: N802
        return self.sent[sid].t1 + off

    def SC(self, scene: str) -> float:  # noqa: N802
        return self.scene_start[scene]

    def SC_END(self, scene: str) -> float:  # noqa: N802
        i = self.scenes.index(scene)
        return self.scene_start[self.scenes[i + 1]] - 0.35 if i + 1 < len(self.scenes) else self.total

    def at_word(self, sid: str, word: str) -> float:
        """문장 안 단어 시각 추정(글자 비율). ElevenLabs 정렬 사용은 Phase 4."""
        x = self.sent[sid]
        i = x.text.find(word)
        return x.t0 + max(0, i) / len(x.text) * x.dur

    def card(self, kind: str):  # noqa: ANN201 — Card
        return next(c for c in self.plan.cards if c.kind == kind)

    def cur_sentence(self, t: float) -> Optional[str]:
        cur = None
        for sid in self.order:
            if self.sent[sid].t0 - 0.3 <= t:
                cur = sid
        return cur

    def in_fullcard(self, t: float) -> bool:
        return any(c.t0 - 0.3 <= t <= c.t1 + 0.3 for c in self.plan.cards)
