"""v7.4.0 사용자 의견 UF-400 — 레퍼런스 영상 분석에서 나온 템플릿 보완·신설 (분석 보고 docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md).

① 문장 단위 변화 검사 [sentence-still] — 요소 등장만 센다(카메라는 세지 않는다, C0 "문장마다 카메라 이동" 금지)
② 지도형 장르 프롬프트 층 — 주 무대가 mercator 인 비기본 장르는 genre_map_<name>.md(지도 문법 유지 + 장르 요소 문법)
③ 장르 프로필 political_history(proposed) — 새 요소 process_lane·doc_excerpt, 설명 모형 되부르기(recurring_model)
"""

from __future__ import annotations

import copy
import unittest
from types import SimpleNamespace as NS

import yaml
from pydantic import ValidationError

from engine.checks import WARN
from engine.pacing import still_sentences
from genres.load import load_genre
from rules import RULES_PATH, load_rules
from schemas.rules_models import VideoRules
from workers.prompt_loader import genre_block, load_prompt


def _s(sid: str, t0: float, t1: float) -> NS:
    return NS(sid=sid, t0=t0, t1=t1)


class SentenceStillTest(unittest.TestCase):
    def test_registered_as_warning(self) -> None:
        self.assertIn("sentence_still", WARN)

    def test_element_change_counts_camera_does_not(self) -> None:
        ss = [_s("a_0", 0.0, 4.0), _s("a_1", 4.0, 8.0), _s("a_2", 8.0, 12.0)]
        ev = [{"type": "badge", "t0": 1.0}, {"type": "dip", "t0": 5.0}, {"type": "primitive", "t0": 4.2}]
        self.assertEqual([x["sid"] for x in still_sentences(ss, ev)], ["a_2"])

    def test_lead_and_short_sentences(self) -> None:
        sc = load_rules().pacing.sentence_change
        ss = [_s("a_0", 2.0, 6.0), _s("a_1", 6.0, 6.0 + sc.min_sentence_sec / 2)]
        self.assertEqual(still_sentences(ss, [{"type": "marker", "t0": 2.0 - sc.lead_sec / 2}]), [])

    def test_camera_kind_rejected_by_rules(self) -> None:
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
        raw["pacing"]["sentence_change"]["change_kinds"] = ["camera", "badge"]
        with self.assertRaises(ValidationError):
            VideoRules.model_validate(raw)


class MapGenrePromptTest(unittest.TestCase):
    def test_political_history_profile(self) -> None:
        g = load_genre("political_history")
        self.assertEqual(g.status, "proposed")
        self.assertEqual(g.stage.primary, "mercator")
        self.assertTrue({"process_lane", "doc_excerpt"} <= set(g.primitives.new))
        self.assertTrue(g.narration is not None and g.narration.recurring_model)

    def test_map_genre_uses_map_template_with_element_grammar(self) -> None:
        r, g = load_rules(), load_genre("political_history")
        for name in ("director", "revise_direction", "research", "script", "visual_qa"):
            with self.subTest(prompt=name):
                block = genre_block(name, r, g)
                self.assertIn("지도 위 장르 political_history", block)
                self.assertNotIn("{{", block)
                self.assertNotIn("이 영상의 주 무대에 쓰지 않는다", block)   # 지도형 장르에 비지도 문단이 붙지 않는다
        d = genre_block("director", r, g)
        self.assertIn("process_lane", d)
        self.assertIn("doc_excerpt", d)
        self.assertIn("설명 모형", genre_block("script", r, g))

    def test_base_genre_unchanged(self) -> None:
        r = load_rules()
        self.assertEqual(genre_block("director", r, load_genre("geopolitics")), "")
        self.assertNotIn("지도 위 장르", load_prompt("director", r, load_genre("macro_monetary")))

    def test_element_grammar_keys_must_be_registered(self) -> None:
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
        raw = copy.deepcopy(raw)
        raw["genre_prompt"]["element_grammar"]["gauge"] = "계기판"
        with self.assertRaises(ValidationError):
            VideoRules.model_validate(raw)


if __name__ == "__main__":
    unittest.main()
