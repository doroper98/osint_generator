"""겹침 카드(cascade, v5.2.0 사용자 재구성 2026-10-01) — 폭 상한·뒤 카드 상한·물러남 단조·덮인 부분 미그림·골든 무영향·글자 넘침 오류."""

from __future__ import annotations

import unittest
from pathlib import Path

import cairo
import yaml

from engine.cascade import CascadeError, back_count, cascade_boxes, cascade_width, check_text, draw_cascade, layout, visible_rects
from engine.style import CASCADE
from tests._fonts import NO_FONTS_REASON, fonts_ready

REPO = Path(__file__).resolve().parent.parent
STEP = 0.05


def _event(n: int = 7, gap: float = 6.0) -> dict:
    items = [dict(at=1.0 + i * gap, flag="ir", date=f"09. 2{i % 10}", title=f"사건 {i}", line="부제", accent="ru") for i in range(n)]
    return {"type": "cascade", "t0": 0.8, "t1": 1.0 + n * gap + 3.0, "items": items}


def _times(e: dict) -> list[float]:
    out, t = [], e["t0"]
    while t <= e["t1"]:
        out.append(t)
        t += STEP
    return out


class CascadeGeometryTest(unittest.TestCase):
    def test_width_never_exceeds_cap(self) -> None:
        e = _event()
        self.assertLessEqual(max(cascade_width(t, e) for t in _times(e)), CASCADE.width_cap)
        steady = CASCADE.max_back * CASCADE.dx + CASCADE.front.w
        self.assertAlmostEqual(cascade_width(e["items"][-1]["at"] + 3.0, e), steady, places=3)

    def test_back_never_exceeds_max(self) -> None:
        e = _event()
        self.assertLessEqual(max(back_count(t, e) for t in _times(e)), CASCADE.max_back)
        self.assertEqual(back_count(e["items"][-1]["at"] + 3.0, e), CASCADE.max_back)

    def test_recede_monotonic(self) -> None:
        """앞 카드가 물러나는 동안 크기가 단조 감소(1 → back_scale), 중간값은 그 사이 — 튐 없음(C0)."""
        e = _event()
        t1 = e["items"][1]["at"]
        sc, t = [], t1
        while t <= t1 + CASCADE.focus_sec + STEP:
            sc.append(next(c for c in layout(t, e) if c.i == 0).scale)
            t += STEP / 5
        self.assertTrue(all(b <= a + 1e-9 for a, b in zip(sc, sc[1:])))
        self.assertAlmostEqual(sc[0], 1.0)
        self.assertAlmostEqual(sc[-1], CASCADE.back_scale)

    def test_front_on_top_and_back_clipped(self) -> None:
        """정상 상태: 맨 앞 = 마지막 사건(크기 1), 뒤 카드 글자는 다음 카드 왼쪽 끝까지(clip_x1).
        v5.14.0 V2: 보이는 영역 = 왼쪽 dx 폭(전체 높이) + 다음 카드 위로 드러난 윗띠(전체 폭) — 상자 가림은 앞 카드 실제 모양."""
        e = _event(3)
        t = e["items"][2]["at"] + 3.0
        cards = layout(t, e)
        self.assertEqual(cards[-1].i, 2)
        self.assertAlmostEqual(cards[-1].scale, 1.0)
        for c, nxt in zip(cards, cards[1:]):
            self.assertAlmostEqual(c.clip_x1, nxt.x)
        vis = visible_rects(cards[0], cards[1:])
        c0, c1 = cards[0], cards[1]
        def covered(x: float, y: float) -> bool:
            return any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in vis)

        for f in (0.01, 0.5, 0.99):
            self.assertTrue(covered(c0.x + (c1.x - c0.x) * f, c0.y + c0.h * 0.99))     # 왼쪽 dx 폭(전체 높이)
            self.assertTrue(covered(c0.x + c0.w * (0.4 + 0.59 * f), c0.y + 1))         # 윗띠(전체 폭)
        self.assertFalse(covered(c1.x + 20, c1.y + 20))                               # 다음 카드 밑은 보이지 않음
        self.assertEqual(cascade_boxes(t, e)[0], (c0.x - c0.flag_r, c0.y - c0.flag_r, c0.x + c0.flag_r, c0.y + c0.flag_r))

    def test_no_text_overlap_during_transition(self) -> None:
        """D-0138 ③ — 전환 중 물러나는 카드 글자와 새 카드 글자가 같은 자리에서 비치는 순간 0:
        새 카드 글자가 보이면 물러나는 카드는 새 카드 왼쪽 끝까지만 그린다, 앞 절반에는 새 카드 글자가 없다."""
        e = _event()
        for k in range(1, len(e["items"])):
            t0 = e["items"][k]["at"]
            t = t0
            while t <= t0 + CASCADE.focus_sec + STEP:
                cards = {c.i: c for c in layout(t, e)}
                new, old = cards.get(k), cards.get(k - 1)
                if new and old and new.title_a > 0.01:
                    self.assertLessEqual(old.clip_x1, new.x + 1e-6, (k, t))
                if t < t0 + CASCADE.focus_sec / 2 - 1e-6 and new:
                    self.assertLessEqual(new.title_a, 1e-9, (k, t))
                t += STEP / 5

    def test_depth_monotonic(self) -> None:
        """D-0138 ② — 뒤로 갈수록(오래된 카드일수록) 깊이(어두움)가 단조 증가, 맨 앞은 깊이 0.
        v5.14.0 V2: 위치는 깊이와 무관 — y = y0 + dy·slot(오래된 카드가 위, 시간 순서대로 오른쪽 아래)."""
        e = _event(5)
        cards = layout(e["items"][-1]["at"] + 3.0, e)
        depths = [c.depth for c in cards]
        self.assertTrue(all(a > b for a, b in zip(depths, depths[1:])))
        self.assertAlmostEqual(depths[-1], 0.0)
        for a, b in zip(cards, cards[1:]):
            self.assertAlmostEqual(b.y - a.y, CASCADE.dy)
            self.assertAlmostEqual(b.x - a.x, CASCADE.dx)

    def test_rules_validator(self) -> None:
        from schemas.rules_models import CascadeRules  # noqa: PLC0415

        raw = CASCADE.model_dump()
        raw["width_cap"] = 400
        with self.assertRaises(ValueError):
            CascadeRules.model_validate(raw)


@unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)
class CascadeTextTest(unittest.TestCase):
    def test_overflow_is_error(self) -> None:
        """앞 카드 제목이 넘치거나, 뒤 카드에서 보이는 폭에 날짜가 안 들어가면 오류 — 자름·말줄임 없음(15 P6)."""
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = _event(2)
        self.assertEqual(check_text(ctx, e), [])
        e["items"][0]["date"] = "2026. 09. 16"
        self.assertTrue(any("뒤 카드 날짜" in b for b in check_text(ctx, e)))
        e["items"][0]["date"] = "09. 16"
        e["items"][1]["title"] = "아주 긴 제목이라 앞 카드 한 줄에 절대로 들어가지 않는 문구"
        self.assertTrue(any("앞 카드 제목" in b for b in check_text(ctx, e)))
        with self.assertRaises(CascadeError):
            draw_cascade(ctx, None, e["items"][1]["at"] + 1.0, e)  # type: ignore[arg-type]


class GoldenUntouchedTest(unittest.TestCase):
    def test_hormuz_korea_has_no_cascade(self) -> None:
        doc = yaml.safe_load((REPO / "projects" / "hormuz_korea" / "direction.yaml").read_text(encoding="utf-8"))
        self.assertFalse(any(e.get("type") == "cascade" for e in doc["events"]))


if __name__ == "__main__":
    unittest.main()
