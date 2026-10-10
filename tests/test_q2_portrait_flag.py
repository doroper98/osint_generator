"""인물 뱃지·국기 물결 V2(v5.15.0 back_and_forth D-0153 §5·D-0158, 사용자 결정 D148, 가이드 23 §10).

띠 수(장치 폭 기반)·정수 열 분할(겹침·빈 줄 0)·물결 위상/진폭·작업 표면 재사용, 초상 정수리 배치(−0.83R, 알파 > 20)·한 번만 재기·
배치 문턱 ≠ 정규화 문턱, 링(이전 두께 그대로, D152)·머리 우선 축소(D-0159), 코드 리터럴 → 규칙 키.
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
from pydantic import ValidationError

from engine.assets import Assets, Labels
from engine.context import RenderCtx
from engine.layers import badges
from engine.layers.badges import badge_at, flag_wave, portrait_alpha_top, strip_columns, wave_strips
from engine.style import BADGE, C, output_profile
from tests.anti_inertia._ast_util import REPO

FW, PT, RING = BADGE.flag_wave, BADGE.portrait, BADGE.ring


def _project(d: Path, top_frac: float = 0.2, top_alpha: int = 255, shape: str = "head") -> Path:
    """합성 초상 + 합성 국기(빨강 불투명 4:3). shape head = 위 top_frac 투명 아래 타원 머리(폭 200/420)와 어깨(흰 불투명) — 맨 윗줄 알파 top_alpha.
    shape rect = top_frac 아래 꽉 찬 사각형(아주 넓은 머리 — 맞출 수 없는 초상)."""
    (d / "assets" / "portraits").mkdir(parents=True)
    (d / "assets" / "flags").mkdir(parents=True)
    w, h = 420, 512
    a = np.zeros((h, w, 4), np.uint8)
    y0 = int(h * top_frac)
    if shape == "rect":
        a[y0:] = 255
    else:
        yy, xx = np.mgrid[0:h, 0:w]
        head = ((xx - 210) / 100) ** 2 + ((yy - (y0 + 130)) / 130) ** 2 <= 1
        a[head | (yy >= y0 + 240)] = 255
        a[y0, a[y0, :, 3] > 0, 3] = top_alpha
        a[y0, 210] = (255, 255, 255, top_alpha)
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

    def test_ring_same_thickness_as_before(self) -> None:
        """링 = v5.14.0 그대로(사용자 지시 D152): 같은 원(R)에 어두운 3.2 위 accent 1.5 — R 위 픽셀은 accent, R + 1.4 는 어두움."""
        self.assertEqual((RING.outer_w, RING.inner_w), (3.2, 1.5))
        with tempfile.TemporaryDirectory() as d:
            R = _ctx(_project(Path(d)))  # noqa: N806
            px = _badge(R, 56)
            out = px[round(150 + 56 + 1.4), 150, :3].astype(int)
            self.assertLess(out.sum(), 60)
            inn = px[150 + 56, 150, 2::-1].astype(float) / 255
            self.assertGreater(float(inn[2]), float(inn[0]) + 0.2)   # us = 파란 accent


class FitTest(unittest.TestCase):
    PEOPLE = ("lee_jae_myung", "khamenei", "trump", "roh_moo_hyun")
    HORMUZ = REPO / "projects" / "hormuz_korea"

    @unittest.skipUnless((REPO / "projects" / "hormuz_korea" / "assets" / "portraits" / "lee_jae_myung.png").exists(),
                         "hormuz 초상 자산 없음(projects/hormuz_korea/assets/portraits)")
    def test_four_people_head_inside_circle(self) -> None:
        """4명 × R56·R30: 머리 상자(정수리 ~ 턱 줄 × 머리 열)가 원(R − 여유) 안, 정수리는 여전히 중심 위 0.83R — 내리지 않고 줄인다."""
        from engine.layers.badges import _head_fits, portrait_fit  # noqa: PLC0415

        R = RenderCtx(assets=Assets(self.HORMUZ, Labels(), geo=False), tb=None, out=output_profile("480p"))  # type: ignore[arg-type]  # noqa: N806
        widths = {}
        for pid in self.PEOPLE:
            key = f"portrait:{pid}"
            R.assets.load_image(key)
            mask = np.asarray(R.assets.img[key])[..., 3] > PT.alpha_thr
            for Rr in (56, 30):  # noqa: N806
                w = portrait_fit(R, key, Rr)
                widths[(pid, Rr)] = w
                self.assertTrue(PT.min_width <= w <= PT.width, (pid, Rr, w))
                self.assertTrue(_head_fits(mask, portrait_alpha_top(R, key), w, Rr), (pid, Rr))
        self.assertEqual(widths[("trump", 56)], PT.width)               # 들어가는 초상은 그대로
        old = self.HORMUZ / "assets" / "portraits_archive" / "lee_jae_myung_v01_whitehouse.png"   # 사용자 지적(D152) 당시 사진 — 줄어든다
        if old.exists():
            with tempfile.TemporaryDirectory() as d:
                (Path(d) / "assets" / "portraits").mkdir(parents=True)
                Image.open(old).save(Path(d) / "assets" / "portraits" / "p.png")
                self.assertLess(portrait_fit(_ctx(Path(d)), "portrait:p", 56), PT.width)

    def test_too_wide_head_shrinks_or_errors(self) -> None:
        """머리가 넓은 합성 초상은 폭이 줄고(정수리 자리 그대로), min_width 로도 안 들면 PortraitFitError(조용한 잘림 없음)."""
        from engine.layers.badges import PortraitFitError, portrait_fit  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            R = _ctx(_project(Path(d), top_frac=0.0, shape="rect"))  # noqa: N806 — 맨 위부터 꽉 찬 사각형 = 아주 넓은 머리
            with self.assertRaises(PortraitFitError):
                portrait_fit(R, "portrait:p", 56)
        with tempfile.TemporaryDirectory() as d:
            p = _project(Path(d))
            a = np.zeros((512, 420, 4), np.uint8)
            yy, xx = np.mgrid[0:512, 0:420]
            a[((xx - 210) / 175) ** 2 + ((yy - 230) / 230) ** 2 <= 1] = 255   # 타원 머리(폭 350/420)
            Image.fromarray(a, "RGBA").save(p / "assets" / "portraits" / "p.png")
            R = _ctx(p)  # noqa: N806
            w = portrait_fit(R, "portrait:p", 56)
            self.assertTrue(PT.min_width <= w < PT.width, w)
            px = _badge(R, 56)
            white = np.where(px[:, 150, :3].min(axis=1) > 200)[0]
            self.assertAlmostEqual(int(white.min()), 150 - PT.alpha_top * 56, delta=1.5)


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
        self.assertFalse(pnums & {0.032, 2.6, 0.16, 0.25, 2.3, 1.72, 0.92}, pnums)
        self.assertNotIn("head_inside_max", BADGE.model_dump())
        self.assertEqual((PT.width, PT.alpha_top, PT.alpha_thr), (2.04, 0.83, 20))
        self.assertEqual((FW.cx, FW.cy, FW.width, FW.amp, FW.strips_min, FW.strips_max), (0.16, -0.05, 2.3, 0.018, 14, 96))
        self.assertEqual((RING.outer_w, RING.inner_w, PT.shadow_alpha), (3.2, 1.5, 0.16))   # 링 = 이전 그대로(D152)

    def test_ring_one_path_for_all_badges(self) -> None:
        """링은 모든 뱃지가 rules badge.ring 한 경로(리터럴 3.2·1.5 없음) — 값이 같아 국기·휘장 뱃지 출력은 그대로(골든 08컷 무변경)."""
        src = ast.unparse(next(n for n in ast.walk(ast.parse((REPO / "engine" / "layers" / "badges.py").read_text(encoding="utf-8")))
                               if isinstance(n, ast.FunctionDef) and n.name == "badge_at"))
        self.assertNotIn("set_line_width(3.2)", src)
        self.assertNotIn("set_line_width(1.5)", src)
        self.assertEqual(src.count("RING.outer_w"), 1)
        self.assertIs(badges.FW, BADGE.flag_wave)


class RightsExceptionTest(unittest.TestCase):
    """D-0160(사용자 결정 D153) — 인물 사용자 예외: 등록된 예외만 restricted 를 넘고, 보이게 기록된다(P6)."""

    ENTRY = dict(src="president_go_kr", license="공공누리 제4유형", artist="대통령실", url="https://www.president.go.kr/greeting",
                 rights_status="restricted", user_exception="U20261010", exception="사용자 결정 D153")

    def test_registry_accepts_only_listed_exception(self) -> None:
        from schemas.engine_models import RightsRegistry  # noqa: PLC0415

        RightsRegistry.model_validate({"people": {"lee_jae_myung": self.ENTRY}})
        with self.assertRaises(ValidationError):
            RightsRegistry.model_validate({"people": {"trump": self.ENTRY}})            # 예외 목록 밖 인물
        with self.assertRaises(ValidationError):
            RightsRegistry.model_validate({"people": {"lee_jae_myung": {**self.ENTRY, "exception": None}}})   # 사유 없음

    def test_credit_check_and_provenance(self) -> None:
        """restricted + 등록 예외 = 통과·provenance 에 1건, 예외 없는 restricted = RightsError(조용히 통과 금지)."""
        from engine.credits import RightsError, rights_exception, rights_exceptions  # noqa: PLC0415

        self.assertEqual(rights_exception("people.lee_jae_myung", self.ENTRY), "U20261010")
        self.assertIsNone(rights_exception("people.lee_jae_myung", {**self.ENTRY, "user_exception": None}))
        self.assertIsNone(rights_exception("people.trump", self.ENTRY))
        exc = rights_exceptions({"people.lee_jae_myung", "people.trump"},
                                {"people": {"lee_jae_myung": self.ENTRY, "trump": {"rights_status": "rights_clear"}}})
        self.assertEqual([(e["ref"], e["rights_status"], e["user_exception"]) for e in exc],
                         [("people.lee_jae_myung", "restricted", "U20261010")])
        self.assertTrue(issubclass(RightsError, Exception))

    def test_library_v02_and_fetch_keep_restricted(self) -> None:
        """라이브러리 이재명 = v02 공식 초상(restricted·예외 기록·파일 있음), fetch_data 는 라이브러리에서 받고 restricted 를 덮지 않는다."""
        import json  # noqa: PLC0415

        import tools.fetch_data as fd  # noqa: PLC0415
        from schemas.models import AssetLibraryManifest  # noqa: PLC0415

        lib = json.loads((REPO / "assets" / "library" / "library_manifest.json").read_text(encoding="utf-8"))
        AssetLibraryManifest.model_validate(lib)
        lee = next(p for p in lib["people"] if p["person_id"] == "lee_jae_myung")
        self.assertEqual(lee["source"]["rights_status"], "restricted")
        self.assertEqual(lee["source"]["user_exception"], "U20261010")
        self.assertTrue(lee["variants"][0]["path"].endswith("lee_jae_myung_mono_v02.png"))
        self.assertTrue((REPO / lee["variants"][0]["path"]).exists())
        self.assertIn("lee_jae_myung", fd.LIBRARY_PEOPLE)
        self.assertNotIn("lee_jae_myung", fd.COMMONS_PEOPLE)
        src = (REPO / "tools" / "fetch_data.py").read_text(encoding="utf-8")
        self.assertIn('rights_status="restricted" if src.get("user_exception")', src)


if __name__ == "__main__":
    unittest.main()
