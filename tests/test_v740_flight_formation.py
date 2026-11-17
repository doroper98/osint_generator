"""v7.4.0 UF-900 R7a — flight 기체 모델 모양(look: model)·편대(count·formation)·새 종류(bomber·fighter).
레퍼런스 실측 benchmark_wartech_2026-11-17.md §2.7(포르도 폭격 장면).

- 스키마: 기본값(look glyph·count 1·formation 없음)은 dict 에 남지 않는다(옛 dict·키 순서·조각 캐시 키 그대로). count > 1 ↔ formation 필수.
- 규칙 블록 rules flight.model·flight.formation 이 로드되고 strict. 새 윤곽은 꼭짓점 ≤ 40, 종류 목록 = 이벤트 Literal.
- 예제(prompts/examples/events/flight_formation.yaml) = 프리뷰 예제(tests/fixtures/preview/flight_formation.yaml), 모델 통과(15 P4).
- 렌더: model = 회색 몸체 + 오른쪽 아래 그림자, count 5 = 몸체 다섯. glyph 1대(옛 이벤트) = HEAD(f3f06b3a) 코드와 같은 바이트. 같은 입력 = 같은 바이트.
"""

from __future__ import annotations

import hashlib
import types
import typing
import unittest
from pathlib import Path

import cairo
import numpy as np
import pydantic
import yaml

from engine.events import FlightEvent
from engine.layers import flight as fl
from engine.provenance import features
from engine.registry import validate_events
from rules import load_rules
from schemas.rules_models import FlightFormation, FlightModel

REPO = Path(__file__).resolve().parent.parent
F = load_rules().flight
BASE = dict(type="flight", t0=10.0, t1=20.0, kind="jet", origin={"lon": 35.0, "lat": 50.5}, lon=39.74, lat=54.63)
OLD_DICT = {"type": "flight", "t0": 10.0, "t1": 20.0, "kind": "jet", "origin": {"lon": 35.0, "lat": 50.5}, "lon": 39.74, "lat": 54.63,
            "col": "amber", "impact": True, "claim": None}
# HEAD(f3f06b3a) 코드로 같은 합성 프레임을 그린 md5 — glyph 1대 경로는 바이트 불변
HEAD_MD5 = {("drone", 0.3): "5d084811c4bfa2bc389605e73a530563", ("drone", 0.7): "5bad8e39e2abc60c37dab6567934c05c",
            ("missile", 0.3): "899630fb6db6165b7b1433541a540f20", ("missile", 0.7): "9daa70f696615e6319f5537b3f5837ed",
            ("jet", 0.3): "7c384450440fb35c2310fc542a29391a", ("jet", 0.7): "2977288a0678a40a979139b547e7266f"}
W, H = 400, 300
DARK = (0.18, 0.22, 0.27)


def _surface(e: dict, t: float, bg: bool = False, size: tuple[int, int] = (200, 200)) -> cairo.ImageSurface:
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, *size)
    ctx = cairo.Context(surf)
    if bg:
        ctx.set_source_rgb(*DARK)
        ctx.paint()
    view = types.SimpleNamespace(stage=types.SimpleNamespace(theme_name=None), to_screen=lambda x, y: (x, y))
    fl.draw_flight(ctx, types.SimpleNamespace(reserved=[]), view, t, e)
    surf.flush()
    return surf


def _rgb(surf: cairo.ImageSurface) -> np.ndarray:
    a = np.frombuffer(bytes(surf.get_data()), np.uint8).reshape(surf.get_height(), surf.get_stride() // 4, 4)
    return a[:, : surf.get_width(), [2, 1, 0]].astype(int)


def _horizontal(**kw: object) -> dict:
    """왼쪽 → 오른쪽 거의 수평 비행(합성 화면 좌표)."""
    d = validate_events([{**BASE, "t1": 30.0, "col": "amber", **kw}])[0]
    d.update(world=(W - 20.0, H / 2), world_origin=(20.0, H / 2))
    return d


class FlightFormationSchemaTest(unittest.TestCase):
    def test_defaults_dropped(self) -> None:
        self.assertEqual(validate_events([BASE]), [OLD_DICT])
        self.assertEqual(list(validate_events([{**BASE, "look": "glyph", "count": 1}])[0]), list(OLD_DICT))
        self.assertEqual(validate_events([{**BASE, "look": "glyph", "count": 1}]), [OLD_DICT])

    def test_new_fields_dict(self) -> None:
        d = validate_events([{**BASE, "kind": "bomber", "look": "model", "count": 7, "formation": "vee"}])[0]
        self.assertEqual(list(d)[-3:], ["look", "count", "formation"])
        self.assertEqual((d["kind"], d["look"], d["count"], d["formation"]), ("bomber", "model", 7, "vee"))
        d = validate_events([{**BASE, "kind": "fighter", "look": "model"}])[0]
        self.assertEqual(d["look"], "model")
        self.assertNotIn("count", d)
        self.assertNotIn("formation", d)

    def test_count_formation_rules(self) -> None:
        bad = [{"count": 3}, {"formation": "vee"}, {"count": 1, "formation": "line"}, {"count": 0},
               {"count": F.formation.max_count + 1, "formation": "vee"}, {"formation": "box", "count": 2}, {"look": "3d"}, {"kind": "b52"}]
        for kw in bad:
            with self.subTest(kw=kw), self.assertRaises(pydantic.ValidationError):
                FlightEvent.model_validate({**BASE, **kw})
        for f in ("vee", "line", "echelon"):
            FlightEvent.model_validate({**BASE, "count": F.formation.max_count, "formation": f})

    def test_kinds_match_rules(self) -> None:
        kinds = set(typing.get_args(FlightEvent.model_fields["kind"].annotation))
        self.assertEqual(kinds, set(F.icon.shapes))
        self.assertEqual(kinds, set(F.icon.size_px))
        self.assertTrue({"bomber", "fighter"} <= kinds)

    def test_examples_match_and_validate(self) -> None:
        a = yaml.safe_load((REPO / "prompts/examples/events/flight_formation.yaml").read_text(encoding="utf-8"))["event"]
        b = yaml.safe_load((REPO / "tests/fixtures/preview/flight_formation.yaml").read_text(encoding="utf-8"))["event"]
        self.assertEqual(a, b)
        d = validate_events([a])[0]
        self.assertEqual((d["look"], d["formation"]), ("model", "vee"))
        self.assertIsNotNone(d["claim"])
        old = yaml.safe_load((REPO / "tests/fixtures/preview/flight.yaml").read_text(encoding="utf-8"))["event"]
        self.assertFalse({"look", "count", "formation"} & set(validate_events([old])[0]))

    def test_grammar_line(self) -> None:
        g = [x for x in load_rules().direction_grammar if "UF-900 R7a" in x]
        self.assertEqual(len(g), 1)
        for needle in ("look: model", "count", "claim", "개략"):
            self.assertIn(needle, g[0])

    def test_provenance_only_when_used(self) -> None:
        old = features([], validate_events([BASE]))["flight"]
        self.assertEqual(set(old), {"count", "kinds", "insets"})
        new = features([], validate_events([BASE, {**BASE, "kind": "bomber", "look": "model", "count": 7, "formation": "vee"}]))["flight"]
        self.assertEqual((new["model_look"], new["formations"]), (1, {"vee": 1}))


class FlightFormationRulesTest(unittest.TestCase):
    def test_loads(self) -> None:
        self.assertIsInstance(F.model, FlightModel)
        self.assertIsInstance(F.formation, FlightFormation)
        self.assertGreater(F.model.shadow.offset[0], 0)
        self.assertGreater(F.model.shadow.offset[1], 0)   # 오른쪽 아래

    def test_strict(self) -> None:
        for cls, d in ((FlightModel, F.model.model_dump()), (FlightFormation, F.formation.model_dump())):
            with self.subTest(cls=cls.__name__), self.assertRaises(pydantic.ValidationError):
                cls.model_validate({**d, "vignette": True})

    def test_new_shapes(self) -> None:
        for k in ("bomber", "fighter"):
            pts = F.icon.shapes[k]
            self.assertLessEqual(len(pts), 40, k)
            self.assertEqual(sorted((round(x, 6), y) for x, y in pts), sorted((round(-x, 6), y) for x, y in pts), f"{k} 좌우 대칭")
        b, f = F.icon.shapes["bomber"], F.icon.shapes["fighter"]
        self.assertGreater(max(abs(x) for x, _ in b), max(abs(y) for _, y in b))   # 전익기 = 날개폭이 긴 변
        self.assertGreater(max(abs(y) for _, y in f), max(abs(x) for x, _ in f))   # 전투기 = 길이가 긴 변


class FlightFormationRenderTest(unittest.TestCase):
    def test_glyph_unchanged_vs_head(self) -> None:
        for (kind, frac), md5 in HEAD_MD5.items():
            e = dict(type="flight", t0=10.0, t1=20.0, kind=kind, origin={"lon": 0, "lat": 0}, lon=0, lat=0, col="amber", impact=True,
                     world=(150.0, 60.0), world_origin=(30.0, 160.0))
            with self.subTest(kind=kind, frac=frac):
                self.assertEqual(hashlib.md5(bytes(_surface(e, 10.0 + F.dur_sec * frac).get_data())).hexdigest(), md5)

    def test_model_gray_body_and_shadow(self) -> None:
        e = _horizontal(kind="fighter", look="model")
        t = 10.0 + F.dur_sec * 0.5
        img = _rgb(_surface(e, t, bg=True, size=(W, H)))
        s, end = e["world_origin"], e["world"]
        x, y = fl.bezier(s, fl.control(s, end), end, fl.ease_out(0.5))
        body = img[int(y) - 2:int(y) + 3, int(x) - 2:int(x) + 3].reshape(-1, 3)
        gray = np.array(F.model.body_rgb) * 255
        self.assertLess(np.abs(body.mean(axis=0) - gray).max(), 255 * F.model.shade * 2, "몸체 = 회색(col 무관)")
        self.assertLess(np.ptp(body.mean(axis=0)), np.ptp(gray) + 6, "무채색(호박색 col 이 몸체에 안 묻는다)")
        bg = np.array(DARK) * 255
        dark = (img.sum(axis=2) < bg.sum() - 15)
        ys, xs = np.nonzero(dark)
        self.assertGreater(len(xs), 0, "그림자 없음")
        self.assertGreater(xs.mean(), x)   # 오른쪽
        self.assertGreater(ys.mean(), y)   # 아래

    def test_count_five_bodies(self) -> None:
        e = _horizontal(kind="bomber", look="model", count=5, formation="vee")
        t = 10.0 + F.dur_sec * 0.5
        img = _rgb(_surface(e, t, bg=True, size=(W, H)))
        s, end = e["world_origin"], e["world"]
        c = fl.control(s, end)
        offs = fl.formation_offsets(e)
        self.assertEqual(len(offs), 5)
        self.assertEqual(len(set(offs)), 5)
        gray = np.array(F.model.body_rgb) * 255
        for o in offs:
            px, py, _ = fl._place(s, c, end, fl.ease_out(0.5), o)
            v = img[int(round(py)), int(round(px))]
            with self.subTest(off=o):
                self.assertLess(np.abs(v - gray).max(), 255 * F.model.shade * 2)
        # 같은 편대 안 기체 사이 거리 ≥ 기체 크기(겹치지 않는다)
        sz = fl.model_size("bomber")
        for i, a in enumerate(offs):
            for b in offs[i + 1:]:
                self.assertGreaterEqual(np.hypot(a[0] - b[0], a[1] - b[1]), sz * min(F.formation.vee.lateral, F.formation.vee.back))

    def test_formation_shapes(self) -> None:
        line = fl.formation_offsets({"kind": "fighter", "look": "model", "count": 3, "formation": "line"})
        self.assertEqual([o[0] for o in line], [0.0, 0.0, 0.0])
        ech = fl.formation_offsets({"kind": "fighter", "look": "model", "count": 3, "formation": "echelon"})
        self.assertTrue(all(o[0] >= 0 for o in ech))
        vee = fl.formation_offsets({"kind": "bomber", "look": "model", "count": 3, "formation": "vee"})
        self.assertEqual(vee[1][0], -vee[2][0])
        self.assertEqual(vee[1][1], vee[2][1])

    def test_deterministic(self) -> None:
        e = _horizontal(kind="bomber", look="model", count=7, formation="vee")
        t = 10.0 + F.dur_sec * 0.6
        a = bytes(_surface(e, t, bg=True, size=(W, H)).get_data())
        b = bytes(_surface(dict(e), t, bg=True, size=(W, H)).get_data())
        self.assertEqual(hashlib.md5(a).hexdigest(), hashlib.md5(b).hexdigest())

    def test_glyph_formation_draws(self) -> None:
        """look glyph + 편대 — 색 부호 count 대(그림자·비행운 없음)."""
        e = _horizontal(kind="drone", count=3, formation="line")
        img = _rgb(_surface(e, 10.0 + F.dur_sec * 0.5, bg=True, size=(W, H)))
        self.assertGreater(int((np.abs(img - np.array(DARK) * 255).sum(axis=2) > 30).sum()), 0)


if __name__ == "__main__":
    unittest.main()
