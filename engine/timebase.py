"""문장 앵커 시간축과 이징 (v2.1.0, v2.3.0 at_word 정렬 경로, 19 부록 D `S, E, SC, SC_END, at_word, clamp01…window`).

모든 연출 시각은 문장 앵커로만 계산한다(02 §1). 절대 초를 하드코딩하지 않는다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Optional

from script.schema import Plan, PlanSentence

WordAnchorMode = Literal["aligned", "ratio"]


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
        self.word_anchors: list[dict] = []   # at_word 호출 기록 → provenance(15 P5)
        self._align: dict[str, Optional[dict]] = {}

    def S(self, sid: str, off: float = 0.0) -> float:  # noqa: N802 — v3 앵커 이름 유지
        return self.sent[sid].t0 + off

    def E(self, sid: str, off: float = 0.0) -> float:  # noqa: N802
        return self.sent[sid].t1 + off

    def SC(self, scene: str) -> float:  # noqa: N802
        return self.scene_start[scene]

    def SC_END(self, scene: str) -> float:  # noqa: N802
        i = self.scenes.index(scene)
        return self.scene_start[self.scenes[i + 1]] - 0.35 if i + 1 < len(self.scenes) else self.total

    def alignment(self, sid: str) -> Optional[dict]:
        """`{mp3}.align.json`(ElevenLabs with-timestamps 의 alignment). 없으면 None."""
        if sid not in self._align:
            p = Path(self.sent[sid].mp3 + ".align.json")
            self._align[sid] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        return self._align[sid]

    def at_word(self, sid: str, word: str) -> float:
        """문장 안 단어의 발음 시작 시각 (03 §6.3).

        정렬이 있으면 발음 텍스트에서 단어를 찾아 `t0 + start − trim_offset`(aligned).
        정렬이 없거나 단어가 발음 텍스트에 없으면 자막 글자 비율 추정(ratio). 어느 쪽인지 word_anchors 에 남긴다.
        """
        x = self.sent[sid]
        mode, t, note = self._aligned(x, word)
        if t is None:
            i = x.text.find(word)
            t = x.t0 + max(0, i) / len(x.text) * x.dur
            mode = "ratio"
        self.word_anchors.append(dict(sid=sid, word=word, mode=mode, t=round(t, 3), **({"note": note} if note else {})))
        return t

    def _aligned(self, x: PlanSentence, word: str) -> tuple[WordAnchorMode, Optional[float], str]:
        al = self.alignment(x.sid)
        if al is None:
            return "ratio", None, ""
        chars = "".join(al["characters"])
        i = chars.find(word)
        if i < 0:
            return "ratio", None, "단어가 발음 텍스트에 없음"
        start = float(al["character_start_times_seconds"][i]) - (x.trim_offset or 0.0)
        return "aligned", x.t0 + min(max(start, 0.0), x.dur), ""

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
