"""post 카드(v3.2.0, 18 §5, back_and_forth D-0051 작업 9) — 문구는 소스 레코드에서, 쓸 수 없는 소스는 오류."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import cairo

from engine.layers.post import PostSourceError, post_geom, post_text
from engine.registry import validate_events
from engine.reserved import card_zones
from rules import load_rules
from schemas.source_models import SourcesFile

FIX = Path(__file__).resolve().parent / "fixtures" / "intake" / "post_sources.json"


def _src(mut=None) -> dict:  # noqa: ANN001
    raw = json.loads(FIX.read_text(encoding="utf-8"))
    if mut:
        mut(raw["sources"])
    return SourcesFile.model_validate(raw).by_id()


def _ev(**kw) -> dict:  # noqa: ANN003
    return validate_events([{"type": "post", "t0": 1.0, "t1": 5.0, "src": "src_x_0001"} | kw])[0]


class PostCardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))

    def test_official_chip_and_no_label_when_verified(self) -> None:
        d = post_text(_ev(), _src())
        self.assertTrue(d["official"])
        self.assertIsNone(d["label"])
        self.assertEqual(d["foot"], "X 게시물 · 번역")

    def test_unverified_label_from_rules(self) -> None:
        d = post_text(_ev(src="src_x_0002"), _src())
        self.assertEqual(d["label"], load_rules().script_schema.labels["unverified"])
        self.assertFalse(d["official"])

    def test_private_masked_and_deleted_marked(self) -> None:
        d = post_text(_ev(src="src_x_0003"), _src())
        self.assertEqual((d["name"], d["handle"], d["initial"]), ("개인 계정", "", ""))
        self.assertIn("삭제된 게시물", d["deleted"])

    def test_unusable_sources_are_errors(self) -> None:
        with self.assertRaises(PostSourceError):
            post_text(_ev(src="src_x_0009"), _src())                       # 없음

        def unconfirm(ss: list) -> None:
            ss[0].pop("confirmed_by")
            ss[0].pop("confirmed_at")
        with self.assertRaises(PostSourceError):
            post_text(_ev(), _src(unconfirm))                               # 미확인(18 §7)
        with self.assertRaises(PostSourceError):
            post_text(_ev(hl="없는 구절"), _src())                           # 형광펜이 번역문에 없음

        def long_orig(ss: list) -> None:
            ss[0]["text_original"] = " ".join(["word"] * 16)
        with self.assertRaises(PostSourceError):
            post_text(_ev(quote=True), _src(long_orig))                     # 15단어 이상 원문 인용

    def test_geometry_and_reserved_zone(self) -> None:
        ev = _ev()
        x, y, w, h, lines = post_geom(self.ctx, ev, _src())
        pc = load_rules().layout_480p.post_card
        self.assertEqual((w, y), (pc.w, pc.y))
        self.assertLessEqual(len(lines), pc.body_max_lines)
        ev["post_box"] = (x, y, w, h)
        zones = card_zones(self.ctx, [ev], 3.0)
        self.assertEqual([z.ref for z in zones], ["post:src_x_0001"])
        panel = _ev(at="panel")
        self.assertEqual(post_geom(self.ctx, panel, _src())[1], pc.panel_y)

    def test_model_rejects_bad_src(self) -> None:
        from engine.registry import RegistryError  # noqa: PLC0415

        with self.assertRaises((RegistryError, ValueError)):
            validate_events([{"type": "post", "t0": 0, "t1": 1, "src": "src_art_0001"}])


class DirectorInputTest(unittest.TestCase):
    def test_media_text_lists_confirmed_verified_posts_only(self) -> None:
        import shutil  # noqa: PLC0415
        import tempfile  # noqa: PLC0415

        from workers.direction_io import media_text  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "intake").mkdir()
            shutil.copy(FIX, p / "intake" / "sources.json")
            txt = media_text(p)
            self.assertIn("type: post", txt)
            self.assertIn("- src_x_0001:", txt)
            self.assertIn("- src_x_0003: 개인 계정", txt)     # 개인 계정은 이름을 연출가에게도 보이지 않는다
            self.assertNotIn("홍길동", txt)
            self.assertNotIn("type: post", media_text(None))


class PostProjectTest(unittest.TestCase):
    def test_post_without_sources_file_is_project_error(self) -> None:
        from engine.project import ProjectError, _attach_posts  # noqa: PLC0415
        from engine.context import RenderCtx  # noqa: PLC0415
        import tempfile  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as td:
            R = RenderCtx.__new__(RenderCtx)  # noqa: N806
            R.cache = {}
            with self.assertRaises(ProjectError):
                _attach_posts(Path(td), R, [copy.deepcopy(_ev())])


if __name__ == "__main__":
    unittest.main()
