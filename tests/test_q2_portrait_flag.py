"""인물 뱃지·국기 물결 V2(v5.15.0 back_and_forth D-0153 §5·D-0158, 사용자 결정 D148, 가이드 23 §10).

띠 수(장치 폭 기반)·정수 열 분할(겹침·빈 줄 0)·물결 위상/진폭·작업 표면 재사용, 초상 정수리 배치(−0.83R, 알파 > 20)·한 번만 재기·
배치 문턱 ≠ 정규화 문턱, 링(바깥 어두운·안쪽 accent), 코드 리터럴 → 규칙 키.
"""

from __future__ import annotations

import ast
import math
import tempfile
import unittest
from pathlib import Path

import cairo
import numpy as np
from PIL import Image

from engine.assets import Assets, Labels
from engine.context import RenderCtx
from engine.layers import badges
from engine.layers.badges import badge_at, flag_wave, portrait_alpha_top, strip_columns, wave_strips
from engine.style import BADGE, C, output_profile
from tests.anti_inertia._ast_util import REPO

FW, PT, RING = BADGE.flag_wave, BADGE.portrait, BADGE.ring


def _project(d: Path, top_frac: float = 0.2, top_alpha: int = 255) -> Path:
    """합성 초상(위 top_frac 투명, 그 아래 흰 불투명 — 맨 윗줄 알파 top_alpha) + 합성 국기(빨강 불투명 4:3)."""
    (d / "assets" / "portraits").mkdir(parents=True)
    (d / "assets" / "flags").mkdir(parents=True)
    w, h = 420, 512
    a = np.zeros((h, w, 4), np.uint8)
    y0 = int(h * top_frac)
    a[y0:, :, :3] = 255
    a[y0:, :, 3] = 255
    a[y0, :, 3] = top_alpha
    Image.fromarray(a, "RGBA").save(d / "assets" / "portraits" / "p.png")
    f = np.zeros((300, 400, 4), np.uint8)
    f[..., 0], f[..., 3] = 220, 255
    Image.fromarray(f, "RGBA").save(d / "assets" / "flags" / "zz_4x3.png")
    return d


def _ctx(d: Path, res: str = "480p") -> RenderCtx:
    return RenderCtx(assets=Assets(d, Labels(), geo=False), tb=None, out=output_profile(res))  # type: ignore[arg-type]


def _badge(R: RenderCtx, Rr: float = 56, t: float = 3.0, size: int = 300) -> np.ndarray:  # noqa: N803
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surf)
    badge_at(ctx, R, size / 2, size / 2, dict(kind="person", pid="p", flag="zz", t0=0.0, t1=10.0, R=Rr, label="", accent="us"), t, 1.0)
    surf.flush()
    return np.ndarray((size, size, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1)).copy()


class StripTest(unittest.TestCase):
    def test_strip_count_follows_device_width(self) -> None:
        """띠 수 = clamp(ceil(장치 폭 ÷ strip_px), 14, 96): 480p solo(R56) 96, group(R30) = 장치 폭, 1080p solo 상한 96, 아주 작으면 14."""
        w480 = lambda r, k=1.0: max(8, int(round(r * FW.width * k / 3.0) * 3))  # noqa: E731 — Assets.scaled 의 폭 양자화
        self.assertEqual(wave_strips(w480(56)), 96)
        g = wave_strips(w480(30))
        self.assertTrue(FW.strips_min < g < FW.strips_max, g)
        self.assertEqual(g, math.ceil(w480(30) / FW.strip_px))
        self.assertEqual(wave_strips(w480(56, 2.25)), 96)
        self.assertEqual(wave_strips(5), FW.strips_min)

    def test_columns_partition_without_overlap_or_gap(self) -> None:
        for dw in (9, 69, 129, 290):
            for n in (14, 50, 96):
                cols = strip_columns(dw, n)
                seen = np.zeros(dw, int)
                for c0, c1 in cols:
                    seen[c0:c1] += 1
                self.assertTrue((seen == 1).all(), (dw, n))

    def test_wave_surface_full_columns_single_alpha(self) -> None:
        """작업 표면: 국기 가운데 줄은 모든 열이 불투명(빈 줄 0), 결과는 알파 한 번(겹침 진해짐 0) — a = 0.5 면 국기 안 알파 ≈ 128 일정."""
        with tempfile.TemporaryDirectory() as d:
            R = _ctx(_project(Path(d)))  # noqa: N806
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 300, 300)
            flag_wave(cairo.Context(surf), R, "flag43:zz", 150, 150, 120, 0.5, 1.3)
            surf.flush()
            px = np.ndarray((300, 300, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1))
            (off,) = R.cache["flag_wave"].values()
            o = np.ndarray((off.get_height(), off.get_width(), 4), np.uint8, off.get_data(), strides=(off.get_stride(), 4, 1))
            mid = o.shape[0] // 2
            self.assertTrue((o[mid, :, 3] == 255).all())
            inner = px[130:170, 100:200, 3]
            self.assertLessEqual(int(inner.max()) - int(inner.min()), 1)
            self.assertAlmostEqual(float(inner.mean()), 127.5, delta=1.5)

    def test_wave_phase_amplitude_and_surface_reuse(self) -> None:
        """띠 i 의 국기 윗변 = pad + sin(t·speed + (i/n)·phase_span)·amp·폭(±1px). 같은 국기·크기면 작업 표면 하나를 다시 쓴다."""
        with tempfile.TemporaryDirectory() as d:
            R = _ctx(_project(Path(d)))  # noqa: N806
            ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 300, 300))
            t = 2.7
            flag_wave(ctx, R, "flag43:zz", 150, 150, 129, 1.0, t)
            (off,) = R.cache["flag_wave"].values()
            dw = off.get_width()
            amp = FW.amp * dw
            pad = math.ceil(amp) + 1
            n = wave_strips(dw)
            o = np.ndarray((off.get_height(), dw, 4), np.uint8, off.get_data(), strides=(off.get_stride(), 4, 1))[..., 3]
            for i, (c0, _) in enumerate(strip_columns(dw, n)):
                top = int(np.argmax(o[:, c0] > 127))
                self.assertAlmostEqual(top, pad + math.sin(t * FW.speed + i / n * FW.phase_span) * amp, delta=1.0)
            flag_wave(ctx, R, "flag43:zz", 150, 150, 129, 1.0, t + 0.04)
            self.assertEqual(len(R.cache["flag_wave"]), 1)
            self.assertIs(next(iter(R.cache["flag_wave"].values())), off)


class PortraitTest(unittest.TestCase):
    def test_crown_at_alpha_top(self) -> None:
        """초상의 정수리(알파 > 20 맨 윗줄)가 중심 위 0.83R(±1px) — solo R56 과 group R30·34 각각."""
        for Rr in (56, 34, 30):  # noqa: N806
            with tempfile.TemporaryDirectory() as d:
                R = _ctx(_project(Path(d), top_frac=0.2))  # noqa: N806
                px = _badge(R, Rr)
                col = px[:, 150]
                white = np.where((col[:, 0] > 200) & (col[:, 1] > 200) & (col[:, 2] > 200))[0]
                self.assertAlmostEqual(int(white.min()), 150 - PT.alpha_top * Rr, delta=1.5, msg=str(Rr))

    def test_alpha_top_measured_once_and_threshold_separate(self) -> None:
        """정수리 재기는 초상마다 한 번(R.cache). 배치 문턱(20)은 정규화 문턱(40)과 별개 — 알파 30 인 윗줄은 정수리로 센다."""
        import tools.portrait_fallback as pf  # noqa: PLC0415

        src = (REPO / "tools" / "portrait_fallback.py").read_text(encoding="utf-8")
        self.assertIn("40", src)
        self.assertNotEqual(PT.alpha_thr, 40)
        self.assertEqual(pf.PORTRAIT_W, 420)
        with tempfile.TemporaryDirectory() as d:
            R = _ctx(_project(Path(d), top_frac=0.25, top_alpha=30))  # noqa: N806
            f = portrait_alpha_top(R, "portrait:p")
            self.assertAlmostEqual(f, int(512 * 0.25) / 512)
            _badge(R)
            n_sc = len(R.assets._sc)
            for t in (3.5, 4.0, 4.5):
                _badge(R, t=t)
            self.assertEqual(list(R.cache["portrait_alpha_top"]), ["portrait:p"])
            self.assertEqual(len(R.assets._sc), n_sc)   # 얼굴·국기 표면을 프레임마다 다시 만들지 않는다

    def test_ring_outer_dark_inner_accent(self) -> None:
        """링: 원 바깥쪽 어두운 outer_w, 원 안쪽 accent inner_w(설계 px)."""
        with tempfile.TemporaryDirectory() as d:
            R = _ctx(_project(Path(d)))  # noqa: N806
            px = _badge(R, 56)
            y_out = round(150 + 56 + RING.outer_w / 2)
            out = px[y_out, 150, :3].astype(int)
            self.assertLess(out.sum(), 60)
            y_in = int(150 + 56 - RING.inner_w / 2)
            inn = px[y_in, 150, 2::-1].astype(float) / 255
            acc = np.array(C["us"])
            self.assertLess(float(np.abs(inn - acc * RING.inner_alpha - (1 - RING.inner_alpha) * inn).max()), 0.35)
            self.assertGreater(float(inn[2]), float(inn[0]))   # us = 파란 accent


class TokensTest(unittest.TestCase):
    def test_flag_wave_and_person_paths_have_no_magic_numbers(self) -> None:
        """옛 리터럴(14·0.032·2.6·0.16·0.25·2.3·1.72·0.92·3.2·1.5)이 flag_wave 와 인물 경로에 없다 — 값은 rules badge.{flag_wave, portrait, ring}."""
        tree = ast.parse((REPO / "engine" / "layers" / "badges.py").read_text(encoding="utf-8"))
        fw = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "flag_wave")
        nums = {c.value for c in ast.walk(fw) if isinstance(c, ast.Constant) and isinstance(c.value, (int, float))}
        self.assertTrue(nums <= {0, 1, 2, 0.5}, nums)
        ba = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "badge_at")
        person = next(n for n in ast.walk(ba) if isinstance(n, ast.If) and "person" in ast.unparse(n.test)
                      and "portrait" in ast.unparse(n))
        pnums = {c.value for b in person.body for c in ast.walk(b) if isinstance(c, ast.Constant) and isinstance(c.value, float)}
        self.assertFalse(pnums & {0.032, 2.6, 0.16, 0.25, 2.3, 1.72, 0.92, 3.2, 1.5}, pnums)
        self.assertNotIn("head_inside_max", BADGE.model_dump())
        self.assertEqual((PT.width, PT.alpha_top, PT.alpha_thr), (2.04, 0.83, 20))
        self.assertEqual((FW.cx, FW.cy, FW.width, FW.amp, FW.strips_min, FW.strips_max), (0.16, -0.05, 2.3, 0.018, 14, 96))
        self.assertEqual((RING.outer_w, RING.inner_w, PT.shadow_alpha), (2.4, 0.8, 0.16))

    def test_emblem_and_flag_badges_keep_old_ring(self) -> None:
        """국기·휘장 뱃지 경로는 옛 링(3.2/1.5)을 그대로 쓴다 — 인물용 값을 통째로 복사하지 않음(가이드 §10)."""
        src = ast.unparse(next(n for n in ast.walk(ast.parse((REPO / "engine" / "layers" / "badges.py").read_text(encoding="utf-8")))
                               if isinstance(n, ast.FunctionDef) and n.name == "badge_at"))
        self.assertIn("set_line_width(3.2)", src)
        self.assertIn("set_line_width(1.5)", src)
        self.assertIs(badges.FW, BADGE.flag_wave)


if __name__ == "__main__":
    unittest.main()
