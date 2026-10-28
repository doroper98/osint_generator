"""카탈로그 판(catalog) 관성 방지 (v7.4.0, back_and_forth D-0251 §1.1).

① 카탈로그 판 mp4 는 deliver(engine.mux)가 거부한다 — 라벨 층은 final.mp4 에 들어가지 않는다(GOAL 불변 6).
② rules `catalog:` 스키마 — 라벨 글자 ≥ 최소 글자, 화면 안, 프로파일이 config 에 있다.
③ 라벨은 날짜 뱃지·자막과 교차하지 않는다(가장 큰 라벨 상자 기준 — 검사 [catalog-label-overlap] 의 기하 하한).
④ 전편 프레임 md5 는 카탈로그 판을 같은 프로세스에서 그린 뒤에도 같다. 카탈로그 프레임은 라벨 상자 밖이 전편과 같다.
그리고 라벨이 레지스트리 밖 이름을 내면 오류(P10), 요소 표는 catalog_frames.json 에서만 만든다(P12).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest

from rules import load_rules

REPO = Path(__file__).resolve().parents[2]
CT = load_rules().catalog


def _mp4(path: Path, comment: str | None) -> Path:
    meta = ["-metadata", f"comment={comment}"] if comment else []
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x36:d=0.2", *meta, str(path)], check=True)
    return path


class CatalogDeliverRefusedTest(unittest.TestCase):
    def test_deliver_refuses_catalog_mp4(self) -> None:
        from engine.mux import AnimaticDeliverError, main, refuse_animatic

        with tempfile.TemporaryDirectory() as d:
            cat = _mp4(Path(d) / "catalog.mp4", CT.mp4_comment)
            with self.assertRaises(AnimaticDeliverError):
                refuse_animatic(cat)
            refuse_animatic(_mp4(Path(d) / "clean.mp4", None))   # 표식 없음 = 통과
            proj = Path(d) / "p"
            (proj / "out").mkdir(parents=True)
            shutil.copy(cat, proj / "out" / "video_noaudio.mp4")   # 이름을 바꿔도 표식으로 잡는다
            from unittest import mock

            with mock.patch("builtins.print") as pr:
                self.assertEqual(main([str(proj)]), 1)
            self.assertIn("카탈로그 판", json.loads(pr.call_args[0][0])["errors"][0])

    def test_markers_differ(self) -> None:
        self.assertNotEqual(CT.mp4_comment, load_rules().animatic.mp4_comment)


class CatalogRulesSchemaTest(unittest.TestCase):
    def test_schema_and_bounds(self) -> None:
        from schemas.rules_models import CatalogRules

        from engine.style import FONT, W_OUT, output_profile

        lb = CT.label
        self.assertGreaterEqual(lb.size, load_rules().layout_480p.min_font_px)
        self.assertIn(lb.font, FONT)
        self.assertLess(lb.pos[0] + lb.max_w + lb.pad, W_OUT)
        output_profile(CT.profile)   # config engine.output 에 없으면 오류
        self.assertTrue(set(lb.font_keys) <= set(load_rules().fonts.model_dump()))
        bad = CT.model_dump()
        bad["label"]["max_lines"] = 2
        with self.assertRaises(Exception):
            CatalogRules.model_validate(bad)
        bad = CT.model_dump()
        bad["extra"] = 1
        with self.assertRaises(Exception):
            CatalogRules.model_validate(bad)

    def test_every_font_maps_to_rules_key(self) -> None:
        from engine.layers.catalog import FONT_KEY
        from engine.style import FONT

        self.assertEqual(set(FONT_KEY), set(FONT))
        self.assertEqual(set(FONT_KEY.values()), set(CT.label.font_keys))


class CatalogLabelClearTest(unittest.TestCase):
    def test_largest_label_clear_of_date_badge_and_subtitles(self) -> None:
        """max_lines 줄 × max_w 폭(가장 큰 라벨)이 날짜 뱃지 상자·자막 띠(최대 줄 수)와 교차하지 않는다."""
        from engine.hud import date_box
        from engine.style import SUBTITLE

        lb = CT.label
        box = (lb.pos[0] - lb.pad, lb.pos[1] - lb.pad, lb.pos[0] + lb.max_w + lb.pad, lb.pos[1] + lb.line_gap * lb.max_lines + lb.pad)
        db = date_box()
        self.assertFalse(box[0] < db[2] and db[0] < box[2] and box[1] < db[3] and db[1] < box[3], (box, db))
        sub_lines = load_rules().script_schema.subtitle_max_lines
        sub_top = SUBTITLE.last_line_y - (sub_lines - 1) * SUBTITLE.line_gap - SUBTITLE.size
        self.assertLess(box[3], sub_top)

    def test_hidden_on_title_and_end_cards(self) -> None:
        """타이틀·엔딩 카드(전면 카드) 구간에는 라벨을 그리지 않는다 — 전면 카드 상자와 교차 0(D-0252). 기록(요소)은 남는다."""
        from types import SimpleNamespace

        import cairo

        from engine.layers.catalog import draw_label

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 64, 36)
        ev = [{"type": "marker", "t0": 0.0, "t1": 9.0}]
        for full, want in ((True, 0), (False, 1)):
            R = SimpleNamespace(tb=SimpleNamespace(in_fullcard=lambda t, f=full: f), stage=SimpleNamespace(name="mercator"),  # noqa: N806
                                cache={"catalog": {"events": ev, "shots": [], "voice": "v"}, "map_theme": {"effective": "light"}})
            draw_label(cairo.Context(surf), R, 1.0)
            last = R.cache["catalog"]["last"]
            self.assertEqual(last["elements"], ["marker"])
            self.assertEqual(bool(last["lines"]), bool(want))

    def test_label_box_matches_drawn_lines(self) -> None:
        from engine.layers.catalog import label_box

        lb = CT.label
        x0, y0, x1, y1 = label_box(["a"] * 3)
        self.assertEqual((x0, y0), (lb.pos[0] - lb.pad, lb.pos[1] - lb.pad))
        self.assertAlmostEqual(y1 - y0, lb.line_gap * 3 + 2 * lb.pad)


class CatalogRegistryNamesTest(unittest.TestCase):
    def test_names_from_registry(self) -> None:
        from engine.layers.catalog import element_name
        from engine.registry import RegistryError

        self.assertEqual(element_name({"type": "panel", "kind": "dots"}), "panel:dots")
        self.assertEqual(element_name({"type": "badge", "kind": "person"}), "badge:person")
        self.assertEqual(element_name({"type": "marker"}), "marker")
        with self.assertRaises(RegistryError):
            element_name({"type": "stamp"})
        with self.assertRaises(RegistryError):
            element_name({"type": "panel", "kind": "gauge"})

    def test_voice_line_from_config(self) -> None:
        from engine.layers.catalog import voice_line
        from orchestrator.config import load_config

        tts = load_config().tts
        s = voice_line()
        self.assertIn(tts.backend_default, s)
        self.assertIn(tts.supertonic.voice_style, s)


class CatalogTableTest(unittest.TestCase):
    def test_table_from_frames_only(self) -> None:
        from tools.catalog_table import build_table

        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "p"
            (proj / "out").mkdir(parents=True)
            with self.assertRaises(FileNotFoundError):
                build_table(proj)
            fr = [{"t": 0.0, "lines": [], "elements": ["marker"], "fonts": ["sans"]},
                  {"t": 1.0, "lines": [], "elements": ["marker"], "fonts": ["sans"]},
                  {"t": 2.0, "lines": [], "elements": ["panel:dots", "card"], "fonts": ["sans", "display"]}]
            (proj / "out" / "catalog_frames.json").write_text(json.dumps({"schema_version": 1, "sample_every_sec": 1.0, "frames": fr}),
                                                              encoding="utf-8")
            md = build_table(proj)
        self.assertIn("| 0:00–0:02 | marker | sans |", md)
        self.assertIn("| 0:02–0:03 | panel:dots · card | sans · display |", md)
        self.assertIn("card · marker · panel:dots", md)


@pytest.mark.slow   # C8.3(D187) — 골든 자산이 필요한 느린 묶음
class CatalogFinalUnchangedTest(unittest.TestCase):
    """전편 프레임은 카탈로그 판과 무관 — 같은 프로세스에서 카탈로그 프레임을 그린 뒤 전편을 다시 그려도 md5 가 같고,
    카탈로그 프레임은 라벨 상자 밖 화소가 전편과 같다(라벨 층은 맨 위 덧그림뿐)."""

    def test_full_frame_md5_independent(self) -> None:
        import numpy as np

        from engine.layers.catalog import label_box
        from engine.project import load_project
        from engine.render import render_frame
        from engine.style import FPS, output_profile

        proj = REPO / "projects" / "hormuz_korea"
        missing = [p for p in ("plan.json", "tts", "assets") if not (proj / p).exists()]
        if missing:
            raise RuntimeError(f"hormuz 자산이 없다(test_provenance_e2e 준비 절차) — 없는 것: {', '.join(missing)}")
        out = output_profile(CT.profile)
        full = load_project(proj, out=out)
        cat = load_project(proj, catalog=True)
        t = full.plan.sentences[len(full.plan.sentences) // 2].t0 + 0.5
        i = int(t * FPS)
        _, a = render_frame(full, i)
        h0 = hashlib.md5(bytes(a)).hexdigest()
        _, c = render_frame(cat, i)
        _, b = render_frame(full, i)
        self.assertEqual(hashlib.md5(bytes(b)).hexdigest(), h0)
        fa = np.frombuffer(bytes(a), np.uint8).reshape(out.height, out.width, 4)
        fc = np.frombuffer(bytes(c), np.uint8).reshape(out.height, out.width, 4).copy()
        x0, y0, x1, y1 = label_box(cat.R.cache["catalog"]["last"]["lines"])
        k = out.k
        fc[max(0, int(y0 * k) - 2):int(y1 * k) + 3, max(0, int(x0 * k + out.pad_x) - 2):int(x1 * k + out.pad_x) + 3] = \
            fa[max(0, int(y0 * k) - 2):int(y1 * k) + 3, max(0, int(x0 * k + out.pad_x) - 2):int(x1 * k + out.pad_x) + 3]
        self.assertTrue(np.array_equal(fa, fc), "라벨 상자 밖 화소가 전편과 다르다")
        self.assertFalse(np.array_equal(np.frombuffer(bytes(a), np.uint8), np.frombuffer(bytes(c), np.uint8)), "라벨이 그려지지 않았다")


if __name__ == "__main__":
    unittest.main()
