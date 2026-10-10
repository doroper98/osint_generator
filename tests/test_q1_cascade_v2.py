"""cascade V2(v5.14.0 back_and_forth D-0153 §4·D-0157, 사용자 결정 D148, 가이드 23 §6).

slot 방향·같은 변위 밀기·폭·뒤 카드 수, 가림 합집합(겹친 가림 영역 알파 0)·노출 테두리 연속, 회피 상자 ⊇ 그린 픽셀,
글자 앞/뒤 절반 순서, 넘침 오류, 항목 변형, 출력 프로파일, draw_frame 기본 호출 바이트 동일, V2 규칙 값·표면 토큰.
"""

from __future__ import annotations

import ast
import unittest
from unittest import mock

import cairo
import numpy as np
from pydantic import ValidationError

from engine.cascade import (CascadeError, back_count, cascade_boxes, cascade_width, check_text, draw_cascade, frame_style, layout,
                            occluder_boxes, text_sec)
from engine.events import CascadeItem
from engine.island import draw_frame
from engine.style import CASCADE, ISLAND, TIMELINE, output_profile
from engine.typography import rrect
from tests._fonts import NO_FONTS_REASON, fonts_ready
from tests.anti_inertia._ast_util import REPO

AT = [.5, 2.6, 4.7, 6.8, 8.9, 11, 13.1, 15.2]                      # 가이드 §6 가상 기관 8항목 앵커
TITLES = ["발표", "협의", "조치", "후속 대응", "재협의", "추가 조치", "재검토", "후속 발표"]
HZ = 120


def _demo(at: list[float] = AT, titles: list[str] = TITLES, line: str | None = "기관 A가 계획을 공개") -> dict:
    items = [dict(at=a, flag="eu", date=f"10. {i + 1:02d}", title=titles[i % len(titles)], line=line, accent="gold")
             for i, a in enumerate(at)]
    return {"type": "cascade", "t0": max(0.0, at[0] - 0.2), "t1": at[-1] + 2.8, "items": items}


def _times(e: dict, hz: int = HZ) -> list[float]:
    return [e["t0"] + i / hz for i in range(int((e["t1"] - e["t0"]) * hz) + 1)]


def _render(t: float, e: dict, w: int = 854, h: int = 480, k: float = 1.0) -> np.ndarray:
    """국기(badge_at)는 빼고 그린다 — 상자·글자 기하만 본다. RGBA(프리멀티플라이) 배열."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surf)
    ctx.scale(k, k)
    with mock.patch("engine.layers.badges.badge_at"):
        draw_cascade(ctx, None, t, e)  # type: ignore[arg-type]
    surf.flush()
    return np.ndarray((h, w, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1)).copy()


def _old_draw_frame(ctx: cairo.Context, box: tuple, a: float) -> None:
    """v5.13.0 island.draw_frame 그대로(기본 호출 바이트 동일 대조 기준)."""
    x, y, w, h = box
    r = ISLAND.radius
    for d_, al in ISLAND.shadow:
        rrect(ctx, x - d_, y - d_ + d_ / 2, w + d_ * 2, h + d_ * 2, r + d_)
        ctx.set_source_rgba(0, 0, 0, al * a)
        ctx.fill()
    rrect(ctx, x, y, w, h, r)
    ctx.set_source_rgba(*TIMELINE.bg_rgb, ISLAND.fill_alpha * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, ISLAND.edge_alpha * a)
    ctx.set_line_width(ISLAND.edge_w)
    ctx.stroke()


class SlotGeometryTest(unittest.TestCase):
    def test_anchor_direction_every_frame(self) -> None:
        """8항목·120Hz 전 시점: 이웃 카드 Δx = dx·Δi, Δy = dy·Δi(dx·dy > 0, 오른쪽 아래), 오차 ≤ 1e-9 — 순서 역전 0."""
        e = _demo()
        self.assertGreater(CASCADE.dx, 0)
        self.assertGreater(CASCADE.dy, 0)
        err = 0.0
        for t in _times(e):
            cs = layout(t, e)
            for a, b in zip(cs, cs[1:]):
                self.assertGreater(b.i, a.i)
                err = max(err, abs(b.x - a.x - CASCADE.dx * (b.i - a.i)), abs(b.y - a.y - CASCADE.dy * (b.i - a.i)))
        self.assertLessEqual(err, 1e-9)

    def test_shift_moves_all_cards_equally(self) -> None:
        """밀기(가장 오래된 카드가 나감) 동안 모든 카드의 변위가 같다 — 좌상단 방향(−dx, −dy) 비율."""
        e = _demo()
        k = CASCADE.max_back + 1
        t0, t1 = e["items"][k]["at"] + 0.1, e["items"][k]["at"] + CASCADE.shift_sec - 0.1
        a = {c.i: c for c in layout(t0, e)}
        b = {c.i: c for c in layout(t1, e)}
        moves = {(round(b[i].x - a[i].x, 9), round(b[i].y - a[i].y, 9)) for i in a if i in b}
        self.assertEqual(len(moves), 1)
        mx, my = moves.pop()
        self.assertLess(mx, 0)
        self.assertAlmostEqual(my / mx, CASCADE.dy / CASCADE.dx)

    def test_width_and_back_count_8_items(self) -> None:
        """최대폭 ≤ width_cap(가이드 실측 549.429), 뒤 카드 ≤ max_back(4)."""
        e = _demo()
        ts = _times(e)
        mw = max(cascade_width(t, e) for t in ts)
        self.assertLessEqual(mw, CASCADE.width_cap)
        self.assertAlmostEqual(mw, 549.429, places=2)
        self.assertEqual(max(back_count(t, e) for t in ts), CASCADE.max_back)


class OcclusionTest(unittest.TestCase):
    def _alpha(self, paint) -> np.ndarray:  # noqa: ANN001
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 120)
        paint(cairo.Context(surf))
        surf.flush()
        return np.ndarray((120, 200, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1))[..., 3].copy()

    def test_occluders_are_union_not_xor(self) -> None:
        """겹친 두 가림 상자의 공통 영역도 알파 0(EVEN_ODD 단일 마스크면 다시 열린다). 반투명 가림 = 1 − 가림 알파 배."""
        st = frame_style(layout(1.0, _demo())[0])
        box = (10.0, 10.0, 180.0, 100.0)
        occ = (((60.0, 30.0, 80.0, 60.0), 3.0, 1.0), ((90.0, 50.0, 80.0, 60.0), 3.0, 1.0))
        a = self._alpha(lambda c: draw_frame(c, box, 1.0, st, occ))
        self.assertEqual(a[70, 120], 0)            # 두 가림의 공통 영역
        self.assertEqual(a[40, 80], 0)
        self.assertGreater(a[20, 30], 0)
        half = self._alpha(lambda c: draw_frame(c, box, 1.0, st, (((60.0, 30.0, 80.0, 60.0), 3.0, 0.5),)))
        full = self._alpha(lambda c: draw_frame(c, box, 1.0, st))
        self.assertAlmostEqual(int(half[50, 100]), full[50, 100] * 0.5, delta=2)

    def test_back_card_hidden_under_front_and_border_continuous(self) -> None:
        """가이드 §6 입력(8항목, t = 5.8): '발표' 상자는 '협의'·'조치' 밑에서 알파 0, 드러난 테두리(윗변·오른변·아랫변 왼쪽)는 이어진다.
        표본 4곳 = 윗변 (150, 60)·(200, 60), 오른변 (219, 66), 아랫변 (50, 135) — v5.13.0 은 x ≥ 86 윗띠가 통째로 잘렸다."""
        e = _demo()
        cs = layout(5.8, e)
        c0 = cs[0]
        self.assertEqual([c.i for c in cs], [0, 1, 2])
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480)
        draw_frame(cairo.Context(surf), c0.box, 1.0, frame_style(c0), occluder_boxes(cs[1:]))
        surf.flush()
        px = np.ndarray((480, 854, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1))
        self.assertEqual(px[100, 120, 3], 0)       # '협의' 밑
        self.assertEqual(px[140, 170, 3], 0)       # '조치' 밑
        inner = px[66, 150, :3].astype(int).sum()  # 윗띠 안쪽 바탕
        for x, y in ((150, 60), (200, 60), (219, 66), (50, 135)):
            self.assertGreater(px[y, x, 3], 100, (x, y))
            self.assertGreater(px[y, x, :3].astype(int).sum(), inner + 20, (x, y))   # 테두리(#4D5851)가 바탕보다 밝다

    def test_boxes_cover_drawn_pixels(self) -> None:
        """그린 상자 픽셀(알파 > 0.6 — 옅은 그림자 제외)은 모두 cascade_boxes(+1px) 안 — 복원된 윗띠도 회피 상자에 들어간다."""
        e = _demo()
        for t in (1.0, 3.0, 4.9, 5.8, 9.2, 11.3, 13.4, 17.0):
            a = _render(t, e)[..., 3]
            m = np.zeros_like(a, bool)
            for x0, y0, x1, y1 in cascade_boxes(t, e):
                m[max(0, int(y0) - 1):int(y1) + 2, max(0, int(x0) - 1):int(x1) + 2] = True
            self.assertEqual(int(((a > 153) & ~m).sum()), 0, t)


class TextTest(unittest.TestCase):
    def test_text_half_order(self) -> None:
        """전환마다 물러나는 카드 제목과 새 카드 제목이 동시에 보이는 시점 0, 새 글자는 text_sec 뒤 절반에만."""
        e = _demo()
        for k in range(1, len(AT)):
            t = AT[k]
            while t <= AT[k] + text_sec(k) + 0.02:
                cs = {c.i: c for c in layout(t, e)}
                if k in cs and k - 1 in cs and cs[k - 1].title_a > CASCADE.back_text_alpha + 1e-9 and cs[k].title_a > 1e-9:
                    self.fail(f"k={k} t={t:.3f} 두 제목 동시")
                if t < AT[k] + text_sec(k) / 2 - 1e-6 and k in cs:
                    self.assertLessEqual(cs[k].title_a, 1e-9)
                t += 1 / HZ

    @unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)
    def test_overflow_is_error_v2_sizes(self) -> None:
        """V2 글꼴·크기(제목 18 Bold)로 넘침 검사 — 데모 문구는 통과, 긴 제목·긴 날짜는 오류(자름 없음)."""
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = _demo()
        self.assertEqual(check_text(ctx, e), [])
        e["items"][3]["title"] = "아주 긴 제목이라 앞 카드 한 줄에 절대로 들어가지 않는 문구"
        self.assertTrue(any("앞 카드 제목" in b for b in check_text(ctx, e)))
        with self.assertRaises(CascadeError):
            draw_cascade(ctx, None, 6.0, e)  # type: ignore[arg-type]
        e = _demo()
        e["items"][0]["date"] = "2026. 10. 01"
        self.assertTrue(any("뒤 카드 날짜" in b for b in check_text(ctx, e)))

    def test_missing_flag_is_schema_error(self) -> None:
        """국기 없는 항목 = 연출 모델 오류(조용히 빈 원으로 그리지 않음)."""
        with self.assertRaises(ValidationError):
            CascadeItem.model_validate(dict(at=1.0, date="10. 01", title="발표"))


@unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)
class VariantsTest(unittest.TestCase):
    def test_item_counts_long_title_empty_line_dense(self) -> None:
        """3/5/6/8항목·한계 길이 제목·빈 부제·촘촘한 앵커(0.6초) — 폭·뒤 카드·방향 불변, 그리기 오류 0."""
        cases = {f"n{n}": _demo(AT[:n]) for n in (3, 5, 6, 8)}
        cases["long"] = _demo(AT[:5], ["재검토 결과를 다시 발표함"])
        cases["no_line"] = _demo(AT[:5], line=None)
        cases["empty_line"] = _demo(AT[:5], line="")
        cases["dense"] = _demo([0.5 + 0.6 * i for i in range(8)])
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        for name, e in cases.items():
            self.assertEqual(check_text(ctx, e), [], name)
            for t in _times(e, 24):
                self.assertLessEqual(cascade_width(t, e), CASCADE.width_cap, name)
                self.assertLessEqual(back_count(t, e), CASCADE.max_back, name)
                cs = layout(t, e)
                for a, b in zip(cs, cs[1:]):
                    self.assertGreater(b.x, a.x, name)
                    self.assertGreater(b.y, a.y, name)
            for t in (e["items"][-1]["at"] + 0.3, e["t1"] - 0.5):
                self.assertGreater(int(_render(t, e)[..., 3].max()), 0, name)

    def test_output_profiles(self) -> None:
        """480/720/1080: 장치 크기·ARGB32 픽셀 형식, 1초 = fps 프레임 모두 그림 있음, 그림 범위가 k 배(설계 좌표 그대로)."""
        e = _demo(AT[:4])
        ref = None
        for name in ("480p", "720p", "1080p"):
            out = output_profile(name)
            frames = [_render(6.8 + i / out.fps, e, out.width, out.height, out.k) for i in range(out.fps)]
            self.assertEqual(len(frames), out.fps)
            for f in frames:
                self.assertEqual(f.shape, (out.height, out.width, 4))
                self.assertGreater(int(f[..., 3].max()), 0)
            ys, xs = np.nonzero(frames[-1][..., 3] > 153)
            ext = np.array([xs.min(), ys.min(), xs.max(), ys.max()]) / out.k
            if ref is None:
                ref = ext
            self.assertTrue(np.allclose(ext, ref, atol=2.0), (name, ext, ref))


class DefaultFrameUnchangedTest(unittest.TestCase):
    def test_default_draw_frame_bytes_equal(self) -> None:
        """draw_frame 선택 인자 없이 = v5.13.0 그리기와 바이트 동일 — 아일랜드 상자 3종·패널 상자, 알파 3가지."""
        boxes = [tuple(ISLAND.boxes[k]) for k in ("center", "left", "right")] + [tuple(ISLAND.panel_box)]
        for box in boxes:
            for a in (1.0, 0.63, 0.2):
                got, want = (cairo.ImageSurface(cairo.FORMAT_ARGB32, 854, 480) for _ in range(2))
                draw_frame(cairo.Context(got), box, a)
                _old_draw_frame(cairo.Context(want), box, a)
                self.assertEqual(bytes(got.get_data()), bytes(want.get_data()), (box, a))

    def test_only_cascade_passes_frame_options(self) -> None:
        """draw_frame 을 부르는 곳 중 style·occluders 를 넘기는 곳은 engine/cascade.py 하나(아일랜드·패널은 3인자 그대로, AST)."""
        calls = []
        for p in (REPO / "engine").rglob("*.py"):
            tree = ast.parse(p.read_text(encoding="utf-8"))
            inner = {id(n) for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) and f.name == "draw_frame" for n in ast.walk(f)}
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and id(n) not in inner and getattr(n.func, "id", getattr(n.func, "attr", "")) == "draw_frame":
                    calls.append((p.relative_to(REPO).as_posix(), len(n.args) + len(n.keywords)))
        self.assertTrue(calls)
        self.assertEqual({f for f, n in calls if n > 3}, {"engine/cascade.py"})
        self.assertTrue(any(f == "engine/panels/base.py" for f, _ in calls))


class RulesV2Test(unittest.TestCase):
    def test_v2_values_and_surface_tokens(self) -> None:
        """V2 값 = 가이드 23 §6 표, 표면 토큰 = 가이드 hex(RGB 0~1, 반올림 4자리)."""
        c = CASCADE
        self.assertEqual((c.x0, c.y0, c.dx, c.dy), (22, 60, 64, 12))
        f = c.front
        self.assertEqual((f.w, f.h, f.pad_x, f.date_dy, f.title_dy, f.line_dy, c.flag_R + f.date_dx), (230, 108, 14, 19, 56, 82, 18))
        self.assertEqual((f.title_size, f.line_size, f.date_size, f.accent_w), (18, 11.5, 10.5, 1.8))
        self.assertEqual((c.back_scale, c.back_h_drop, c.frame.radius, c.frame.edge_w, c.frame.occluder_pad), (0.86, 20, 3, 0.65, 0.325))
        self.assertEqual((c.focus_sec, c.shift_sec, c.back_fade_px, c.max_back, c.width_cap), (0.5, 0.6, 12, 4, 560))
        want = {"bg": "#111514", "front": "#1B211D", "back": "#171C19", "text": "#EDF0E9", "text_sub": "#A2AAA5", "edge": "#4D5851"}
        for k, h in want.items():
            rgb = tuple(round(int(h[i:i + 2], 16) / 255, 4) for i in (1, 3, 5))
            self.assertEqual(tuple(getattr(c.surface, k)), rgb, k)
        self.assertNotIn("back_dy", c.model_dump())
        self.assertNotIn("step", c.model_dump())

    def test_validator_rejects_no_overlap(self) -> None:
        from schemas.rules_models import CascadeRules  # noqa: PLC0415

        raw = CASCADE.model_dump()
        raw["dy"] = 80
        with self.assertRaises(ValueError):
            CascadeRules.model_validate(raw)
        raw = CASCADE.model_dump()
        raw["surface"]["edge"] = [77, 88, 81]
        with self.assertRaises(ValueError):
            CascadeRules.model_validate(raw)


if __name__ == "__main__":
    unittest.main()
