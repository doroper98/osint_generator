"""G12 backdrop 무대(v5.1.0, back_and_forth D-0121 §B·D-0123 §1~§3, 사용자 결정 D106·D108).

- 무대 레지스트리 세 곳(rules registries.stages · STAGE_CLASSES · 프리뷰 예제) + 이벤트 backdrop 세 곳(P10).
- 빈 카메라 {} 는 backdrop 무대에만. backdrop 이벤트는 backdrop 무대에만.
- 권리: 레지스트리 photo·rights_clear·파일만(C9·G4-10) — 아니면 RightsError·checks backdrop_rights.
- 연속 같은 사진·서로 다른 사진 수 → checks backdrop_repeat. 전환 = crossfade(알파 연속, 줌 범프 없음).
- 장르 기본 무대(default_stage = stage.primary)와 다르면 stage_reason 없을 때 stage_choice warning.
- 콘티 판 자리표시 [배경: id].
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace as NS

import cairo
import yaml
from PIL import Image

from engine import checks
from engine.credits import RightsError
from engine.direction import Direction
from engine.layers import backdrop as B
from engine.registry import REGISTRY, validate_events
from engine.stage import STAGE_CLASSES, StageSet
from engine.style import BACKDROP, H_OUT, W_OUT
from rules import load_rules
from tests.anti_inertia._ast_util import REPO

PREVIEW = REPO / "tests" / "fixtures" / "preview"


def _asset(kind: str = "photo", status: str = "rights_clear", file: str | None = "x.jpg") -> NS:
    return NS(kind=kind, rights_status=status, file=file)


def _ev(img: str, t0: float, t1: float) -> dict:
    return {"type": "backdrop", "t0": t0, "t1": t1, "img": img}


REG = {"a": _asset(), "b": _asset(), "c": _asset(), "vid": _asset("video"), "tbd": _asset(status="pending_review")}


class RegistryTest(unittest.TestCase):
    def test_stage_and_event_three_places(self) -> None:
        R = load_rules().registries  # noqa: N806
        self.assertIn("backdrop", R.stages)
        self.assertIn("backdrop", STAGE_CLASSES)
        self.assertTrue((PREVIEW / "stage_backdrop.yaml").exists())
        self.assertIn("backdrop", R.event_types)
        self.assertIn("backdrop", REGISTRY)
        ex = yaml.safe_load((PREVIEW / "backdrop.yaml").read_text(encoding="utf-8"))["event"]
        self.assertEqual(validate_events([ex])[0]["img"], "hormuz_transit")

    def test_empty_camera_only_on_backdrop(self) -> None:
        raw = yaml.safe_load((PREVIEW / "stage_backdrop.yaml").read_text(encoding="utf-8"))["direction"]
        doc = Direction.model_validate(raw)
        self.assertEqual(doc.main_stage(), "backdrop")
        st = StageSet().get("backdrop")
        self.assertEqual(st.to_world(), (W_OUT / 2, H_OUT / 2))
        with self.assertRaises(ValueError):
            st.to_world(lon=1.0, lat=2.0)
        with self.assertRaises(ValueError):
            StageSet().get("mercator").to_world()   # 지도 숏의 빈 카메라 = 오류(P10)


class RightsTest(unittest.TestCase):
    def test_registry_rights_gate(self) -> None:
        self.assertIs(B.validate_backdrop(_ev("a", 0, 5), REG), REG["a"])
        for bad in ("nope", "vid", "tbd"):
            with self.assertRaises(RightsError, msg=bad):
                B.validate_backdrop(_ev(bad, 0, 5), REG)
        with self.assertRaises(RightsError):
            B.validate_backdrop(_ev("f", 0, 5), {"f": _asset(file=None)})

    def test_report_rights_hard(self) -> None:
        rep = B.backdrop_report([_ev("a", 0, 5), _ev("nope", 6, 9), _ev("b", 10, 12)], REG)
        self.assertEqual(len(rep["rights"]), 1)
        self.assertTrue(rep["rights"][0].startswith("[backdrop-rights]"))
        self.assertIn("backdrop_rights", checks.HARD)


class RepeatTest(unittest.TestCase):
    def test_consecutive_same_photo(self) -> None:
        rep = B.backdrop_report([_ev("a", 0, 5), _ev("a", 6, 9), _ev("b", 10, 12), _ev("c", 13, 15)], REG)
        self.assertEqual([r.split(" ")[0] for r in rep["repeat"]], ["[backdrop-repeat]"])
        self.assertIn("backdrop_repeat", checks.HARD)

    def test_photo_count_range(self) -> None:
        few = B.backdrop_report([_ev("a", 0, 5), _ev("b", 6, 9), _ev("a", 10, 12)], REG)
        self.assertTrue(any(r.startswith("[backdrop-photos] 서로 다른 배경 사진 2장") for r in few["repeat"]))
        ok = B.backdrop_report([_ev("a", 0, 5), _ev("b", 6, 9), _ev("c", 10, 12)], REG)
        self.assertEqual((ok["repeat"], ok["unique"]), ([], 3))
        self.assertEqual(B.backdrop_report([{"type": "card", "t0": 0, "t1": 1}], REG), {})


class CrossfadeTest(unittest.TestCase):
    def test_alpha_crossfade_only(self) -> None:
        e = _ev("a", 10.0, 20.0)
        xf = BACKDROP.crossfade_sec
        self.assertEqual(B.backdrop_alpha(10.0, e), 0.0)
        self.assertEqual(B.backdrop_alpha(10.0 + xf, e), 1.0)
        self.assertEqual(B.backdrop_alpha(20.0, e), 1.0)
        self.assertEqual(B.backdrop_alpha(20.0 + xf, e), 0.0)
        vals = [B.backdrop_alpha(10.0 + i * 0.05, e) for i in range(int(xf / 0.05) + 1)]
        self.assertEqual(vals, sorted(vals))   # 단조 증가(튀는 값 없음)

    def test_draw_blurred_dimmed_photo(self) -> None:
        im = Image.new("RGB", (400, 300), (250, 250, 250))
        R = NS(out=NS(k=1), cache={}, assets=NS(media_assets={"a": NS(file="x.jpg")}, img={"media:x.jpg": im},  # noqa: N806
                                                   load_image=lambda key: None))
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT)
        ctx = cairo.Context(surf)
        B.draw_backdrop(ctx, R, None, 15.0, _ev("a", 0.0, 30.0))
        surf.flush()
        px = surf.get_data()[(H_OUT // 2 * W_OUT + W_OUT // 2) * 4:][:3]
        want = round(250 * (1 - BACKDROP.dim))
        self.assertTrue(all(abs(v - want) <= 3 for v in px), (list(px), want))   # 덮개(dim) 한 번만


class StageChoiceTest(unittest.TestCase):
    def _doc(self, **kw: object) -> Direction:
        raw = yaml.safe_load((PREVIEW / "stage_timeline.yaml").read_text(encoding="utf-8"))["direction"]
        return Direction.model_validate({**raw, **kw})

    def test_default_stage_and_warning(self) -> None:
        d = self._doc()
        self.assertEqual(d.default_stage(), "backdrop")   # macro_monetary 기본 = backdrop(D-0123 §2)
        self.assertEqual(len(d.stage_choice()), 1)
        self.assertTrue(d.stage_choice()[0].startswith("[stage-choice]"))
        self.assertEqual(self._doc(stage_reason="순수 차트 검증용 데모").stage_choice(), [])
        self.assertIn("stage_choice", checks.WARN)


class AnimaticTest(unittest.TestCase):
    def test_placeholder_label(self) -> None:
        from engine.layers import animatic  # noqa: PLC0415

        self.assertEqual(animatic.label("backdrop", "fed_presser_0916"), "[배경: fed_presser_0916]")
        self.assertIs(animatic.resolve_animatic("backdrop").render, animatic.draw_backdrop)


if __name__ == "__main__":
    unittest.main()
