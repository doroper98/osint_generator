"""v7.4.0 사용자 의견 UF-400 — 레퍼런스 영상 분석에서 나온 템플릿 보완·신설 (분석 보고 docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md).

① 문장 단위 변화 검사 [sentence-still] — 요소 등장만 센다(카메라는 세지 않는다, C0 "문장마다 카메라 이동" 금지)
② 지도형 장르 프롬프트 층 — 주 무대가 mercator 인 비기본 장르는 genre_map_<name>.md(지도 문법 유지 + 장르 요소 문법)
③ 장르 프로필 political_history(UF-401 승인 → approved) — 새 요소 process_lane·doc_excerpt, 설명 모형 되부르기(recurring_model)
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
        self.assertEqual(g.status, "approved")
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
        full = load_prompt("director", r, g)   # v7.4.0 UF-403 — 요소 안내는 공통 연출 규칙(본문)으로 옮겼다
        self.assertIn("process_lane", full)
        self.assertIn("doc_excerpt", full)
        self.assertIn("설명 모형", genre_block("script", r, g))

    def test_base_genre_unchanged(self) -> None:
        r = load_rules()
        self.assertEqual(genre_block("director", r, load_genre("geopolitics")), "")
        self.assertNotIn("지도 위 장르", load_prompt("director", r, load_genre("macro_monetary")))

    def test_element_grammar_removed(self) -> None:
        """v7.4.0 UF-403 — 장르별 요소 안내(element_grammar)는 삭제(P2). 다시 넣으면 규칙 로드 오류(extra forbid)."""
        raw = copy.deepcopy(yaml.safe_load(RULES_PATH.read_text(encoding="utf-8")))
        raw["genre_prompt"]["element_grammar"] = {"process_lane": "x"}
        with self.assertRaises(ValidationError):
            VideoRules.model_validate(raw)


class CommonGrammarTest(unittest.TestCase):
    """v7.4.0 UF-402("둘다 진행해") — 범용 장치(뱃지 신호·열린 가설 칸·점선 원·흐르는 점·내림선·점 고리) 사용 안내는 모든 장르의
    연출 프롬프트(direction_grammar)에, 정치사 전용 요소 안내만 장르 문단(element_grammar)에. 같은 줄이 두 번 들어가지 않는다."""

    MARKS = ("pulse", "style open", "spot(", "flow: true", "shape drop", "crowd: true")

    def test_geopolitics_director_gets_device_lines(self) -> None:
        r = load_rules()
        for genre in ("geopolitics", "macro_monetary"):
            text = load_prompt("director", r, load_genre(genre))
            for m in self.MARKS:
                with self.subTest(genre=genre, mark=m):
                    self.assertIn(m, text)

    def test_genre_element_lines_are_common_too(self) -> None:
        """v7.4.0 UF-403 — 정치사에서 시작한 요소(process_lane·doc_excerpt·era_numeral·statement_diff) 안내도 모든 장르 프롬프트에."""
        text = load_prompt("director", load_rules(), load_genre("geopolitics"))
        for m in ("process_lane", "doc_excerpt", "era_numeral", "statement_diff 로"):
            with self.subTest(mark=m):
                self.assertIn(m, text)

    def test_no_duplicate_in_map_genre(self) -> None:
        text = load_prompt("director", load_rules(), load_genre("political_history"))
        for m in self.MARKS:
            with self.subTest(mark=m):
                self.assertEqual(text.count(m), 1)


class LookAndFeelTest(unittest.TestCase):
    """v7.4.0 UF-403(사용자 "나는 룩앤필을 만들어 두는거지 거기에 우겨넣는걸 원하는건 아니거든") — 장르 = 톤 프리셋.
    ① 요소는 등록 요소 전부(장르 목록 = 추천) ② 고정 막 없음(흔한 흐름 = 참고) ③ 서술 구조 스위치는 조건부 ④ 무대도 등록 무대 전부(장르 = 기본값)."""

    def test_elements_not_whitelisted_by_genre(self) -> None:
        from engine.checks import check_genre_elements  # noqa: PLC0415
        from genres.elements import used_elements  # noqa: PLC0415

        ev = [{"type": "primitive", "id": "process_lane"}, {"type": "primitive", "id": "era_numeral"}, {"type": "panel", "kind": "checklist"}]
        for genre in ("geopolitics", "macro_monetary", "earnings"):
            with self.subTest(genre=genre):
                P = NS(R=NS(cache={"genre": {"name": genre, "elements_used": used_elements(ev)}}))  # noqa: N806
                self.assertEqual(check_genre_elements(P), [])

    def test_acts_are_reference_not_fixed(self) -> None:
        head = load_rules().genre_prompt.acts_head
        self.assertIn("고정 막이 아니다", head)
        self.assertIn("따르지 않는다", head)
        self.assertIn(head, load_prompt("script", load_rules(), load_genre("earnings")))

    def test_structure_switch_is_conditional(self) -> None:
        t = load_rules().genre_prompt.narration["recurring_model"]
        self.assertIn("되풀이될 때만", t)
        self.assertIn("모형을 만들지 않는다", t)

    def test_any_registered_stage_with_genre_default_theme(self) -> None:
        """무대는 장르로 막지 않는다 — 어떤 장르든 지도 무대를 고를 수 있게 모든 프로필이 지도 기본 테마를 갖는다(D154)."""
        from genres.load import genre_names  # noqa: PLC0415

        for g in genre_names():
            with self.subTest(genre=g):
                self.assertIn("theme", load_genre(g).stage.settings().get("mercator") or {})


if __name__ == "__main__":
    unittest.main()
