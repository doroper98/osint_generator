"""사건 띠 v2 "접히는 띠"(v5.2.0, back_and_forth D-0135) — 폭 상한·칩 상한·접힘 단조·골든 무영향·글자 넘침 오류."""

from __future__ import annotations

import unittest
from pathlib import Path

import cairo
import yaml

from engine.chain import ChainError, chain_width, check_text, chip_count, draw_chain, layout
from engine.style import CHAIN
from tests._fonts import NO_FONTS_REASON, fonts_ready

REPO = Path(__file__).resolve().parent.parent
STEP = 0.05


def _event(n: int = 7, gap: float = 6.0) -> dict:
    items = [dict(at=1.0 + i * gap, flag="ir", date="09. 2" + str(i % 10), title=f"사건 {i}", line="부제", accent="ru") for i in range(n)]
    return {"type": "chain", "t0": 0.8, "t1": 1.0 + n * gap + 3.0, "items": items}


def _times(e: dict) -> list[float]:
    out, t = [], e["t0"]
    while t <= e["t1"]:
        out.append(t)
        t += STEP
    return out


class ChainV2GeometryTest(unittest.TestCase):
    def test_width_never_exceeds_cap(self) -> None:
        """어느 순간에도 띠 폭 ≤ width_cap(560), 정상 상태(칩 3 + 카드) = 3 × (112 + 8) + 196 = 556."""
        e = _event()
        widths = [chain_width(t, e) for t in _times(e)]
        self.assertLessEqual(max(widths), CHAIN.width_cap)
        steady = CHAIN.max_chips * (CHAIN.chip.w + CHAIN.gap) + CHAIN.card.w
        self.assertAlmostEqual(chain_width(e["items"][4]["at"] + 3.0, e), steady, places=3)
        self.assertEqual(steady, 556)

    def test_chips_never_exceed_max(self) -> None:
        e = _event()
        self.assertLessEqual(max(chip_count(t, e) for t in _times(e)), CHAIN.max_chips)
        self.assertEqual(chip_count(e["items"][-1]["at"] + 3.0, e), CHAIN.max_chips)

    def test_fold_width_monotonic(self) -> None:
        """직전 카드가 칩으로 접히는 동안 폭이 단조 감소(196 → 112), 중간값은 그 사이 — 튐 없음(C0)."""
        e = _event()
        t1 = e["items"][1]["at"]
        ws = []
        t = t1
        while t <= t1 + CHAIN.fold_sec + STEP:
            s0 = next(s for s in layout(t, e) if s.i == 0)
            ws.append(s0.w)
            t += STEP / 5
        self.assertTrue(all(b <= a + 1e-9 for a, b in zip(ws, ws[1:])))
        self.assertAlmostEqual(ws[0], CHAIN.card.w)
        self.assertAlmostEqual(ws[-1], CHAIN.chip.w)
        mid = next(s for s in layout(t1 + CHAIN.fold_sec / 2, e) if s.i == 0).w
        self.assertTrue(CHAIN.chip.w < mid < CHAIN.card.w)

    def test_new_card_waits_for_fold(self) -> None:
        """새 카드는 접기·밀기가 끝난 뒤 나타난다 — 그 전에는 상자가 없다(폭 상한의 근거)."""
        e = _event()
        t = e["items"][2]["at"] + min(CHAIN.fold_sec, CHAIN.shift_sec) / 2
        self.assertNotIn(2, [s.i for s in layout(t, e)])

    def test_rules_cap_validator(self) -> None:
        from schemas.rules_models import ChainRules  # noqa: PLC0415

        raw = CHAIN.model_dump()
        raw["width_cap"] = 500
        with self.assertRaises(ValueError):
            ChainRules.model_validate(raw)


@unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)
class ChainV2TextTest(unittest.TestCase):
    def test_overflow_is_error(self) -> None:
        """칩 제목이 한 줄 폭을 넘으면 오류 — 말줄임표·자름 없음(15 P6)."""
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = _event(2)
        self.assertEqual(check_text(ctx, e), [])
        e["items"][1]["title"] = "아주 긴 제목이라 칩 한 줄에 들어가지 않는다"
        bad = check_text(ctx, e)
        self.assertTrue(any("[chain-overflow] 칩 제목" in b for b in bad))
        with self.assertRaises(ChainError):
            draw_chain(ctx, None, e["items"][1]["at"] + 1.0, e)  # type: ignore[arg-type]


class GoldenUntouchedTest(unittest.TestCase):
    def test_hormuz_korea_has_no_chain(self) -> None:
        """골든 hormuz_korea 는 chain 이벤트가 없다 — 사건 띠 코드 경로(그리기·예약·검사)는 chain 이 있을 때만 돈다."""
        doc = yaml.safe_load((REPO / "projects" / "hormuz_korea" / "direction.yaml").read_text(encoding="utf-8"))
        self.assertFalse(any(e.get("type") == "chain" for e in doc["events"]))


if __name__ == "__main__":
    unittest.main()
