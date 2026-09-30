"""장르 프롬프트 층 (v4.4.0, back_and_forth D-0090 작업 1·8, docs/handoff/20 §5·§6·§7·§9, 15 P3·P4).

- 기본 장르(지정학)·장르 미지정 = 추가 문단 0 → 프롬프트 바이트 동일.
- 비기본 장르 = `prompts/genre_<이름>.md` 를 장르 프로필 + `rules genre_prompt` 로 채운 문단. 코드 문장 0.
- 주문(order.yaml)이 장르의 단일 출처(원고·리서치 단계엔 direction 이 없다).
"""

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from pydantic import ValidationError

from engine.qa import QAVerdict
from genres.load import GenreError, load_genre, load_order, project_genre
from rules import load_rules
from schemas.order_models import Order
from workers import prompt_loader
from workers.prompt_loader import GENRE_BLOCK, PromptTemplateError, genre_block, load_prompt

MAIN = ("research", "script", "director", "revise_direction", "visual_qa")
ORDER = {
    "topic": "연방준비제도의 최근 금리 정책", "genre": "macro_monetary",
    "instructions": ["불변 층(20 §1.1)은 모두 지킨다."],
    "data": {"series": ["FEDFUNDS"]},
    "media": {"wanted": ["기사 카드"], "rights": "권리 레지스트리 확인, 불확실하면 쓰지 않는다"},
}


def write_order(pdir: Path, **over: object) -> None:
    d = {**ORDER, **over}
    (pdir / "order.yaml").write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")


class GeopoliticsByteIdenticalTest(unittest.TestCase):
    def test_base_genre_adds_nothing(self) -> None:
        r = load_rules()
        geo = load_genre(r.genre_prompt.base_genre)
        for name in MAIN:
            with self.subTest(name=name):
                self.assertIn(GENRE_BLOCK, prompt_loader.prompt_path(name).read_text(encoding="utf-8"))
                self.assertEqual(load_prompt(name, r), load_prompt(name, r, geo))
                self.assertNotIn("장르 규칙", load_prompt(name, r))

    def test_marker_is_last_so_removal_is_exact(self) -> None:
        # 표지는 파일 맨 끝(마지막 줄바꿈 뒤, 줄바꿈 없음) — 빈 문자열로 바뀌면 개편 전 파일과 같은 바이트
        for name in MAIN:
            with self.subTest(name=name):
                raw = prompt_loader.prompt_path(name).read_text(encoding="utf-8")
                self.assertTrue(raw.endswith("\n" + GENRE_BLOCK))
                self.assertEqual(raw.count(GENRE_BLOCK), 1)


class MacroGenreBlockTest(unittest.TestCase):
    def setUp(self) -> None:
        self.r = load_rules()
        self.g = load_genre("macro_monetary")

    def test_every_main_prompt_gets_block(self) -> None:
        for name in MAIN:
            with self.subTest(name=name):
                out = load_prompt(name, self.r, self.g)
                self.assertNotIn("{{", out)
                self.assertIn("장르 규칙 — 이 영상은 지정학이 아니다 (장르 macro_monetary, 프로필 proposed)", out)
                self.assertTrue(out.startswith(load_prompt(name, self.r)))   # 기본 문단 뒤에 덧붙을 뿐

    def test_stage_grammar_from_rules(self) -> None:
        for name in ("director", "revise_direction", "visual_qa"):
            out = load_prompt(name, self.r, self.g)
            for line in self.r.genre_prompt.stage_grammar["backdrop"]:   # v5.1.0 D-0123 — macro_monetary 주 무대 = backdrop
                self.assertIn(line, out)

    def test_narration_switches_and_n(self) -> None:
        out = load_prompt("script", self.r, self.g)
        self.assertIn(self.r.genre_prompt.narration["define_terms_once"], out)
        self.assertIn(self.r.genre_prompt.narration["numbers_per_sentence_max"].replace("{n}", "2"), out)
        self.assertIn("투자 권유, 가격 예측 단정", out)
        off = self.g.model_copy(update={"narration": self.g.narration.model_copy(update={"attribute_causality": False})})
        self.assertNotIn(self.r.genre_prompt.narration["attribute_causality"], load_prompt("script", self.r, off))

    def test_visual_qa_rubric_seven(self) -> None:
        out = load_prompt("visual_qa", self.r, self.g)
        for i, item in enumerate(self.r.genre_prompt.rubric_extra, 1):
            self.assertIn(f"{i}. {item}", out)
        self.assertEqual(len(self.r.genre_prompt.rubric_extra), 7)

    def test_director_lists_elements_and_colors(self) -> None:
        out = load_prompt("director", self.r, self.g)
        self.assertIn("statement_diff", out)
        self.assertIn("hike: #ff7a59", out)
        self.assertIn("policy_rate — 기준금리 (step, 단위 %)", out)

    def test_missing_genre_template_fails_loud(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, "x.md").write_text("본문\n" + GENRE_BLOCK, encoding="utf-8")
            with mock.patch.object(prompt_loader, "PROMPTS_DIR", Path(td)):
                self.assertEqual(load_prompt("x", self.r), "본문\n")
                with self.assertRaises(PromptTemplateError):
                    load_prompt("x", self.r, self.g)

    def test_primary_stage_without_grammar_fails(self) -> None:
        gp = self.r.genre_prompt.model_copy(update={"stage_grammar": {"mercator": ["x"]}})
        r2 = self.r.model_copy(update={"genre_prompt": gp})
        with self.assertRaises(PromptTemplateError):
            genre_block("director", r2, self.g)

    def test_narration_key_without_rules_text_fails(self) -> None:
        nar = dict(self.r.genre_prompt.narration)
        nar.pop("forecast_attribution")
        r2 = self.r.model_copy(update={"genre_prompt": self.r.genre_prompt.model_copy(update={"narration": nar})})
        with self.assertRaises(PromptTemplateError):
            genre_block("script", r2, self.g)

    def test_rules_reject_unknown_stage_grammar(self) -> None:
        from schemas.rules_models import VideoRules  # noqa: PLC0415

        raw = self.r.model_dump(mode="json")
        raw["genre_prompt"]["stage_grammar"]["nowhere"] = ["x"]
        with self.assertRaises(ValidationError):
            VideoRules.model_validate(raw)


class OrderTest(unittest.TestCase):
    def test_valid_order(self) -> None:
        o = Order.model_validate(ORDER)
        self.assertEqual(o.genre, "macro_monetary")
        self.assertEqual(o.length, "내용이 정한다")

    def test_unknown_genre_and_extra_field(self) -> None:
        with self.assertRaises((ValidationError, GenreError)):
            Order.model_validate({**ORDER, "genre": "nope"})
        with self.assertRaises(ValidationError):
            Order.model_validate({**ORDER, "acts": 12})
        with self.assertRaises(ValidationError):
            Order.model_validate({**ORDER, "length": "12막"})   # 고정 막 금지

    def test_project_genre(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td)
            self.assertIsNone(load_order(pdir))
            self.assertEqual(project_genre(pdir)[0].genre, "geopolitics")
            self.assertFalse(project_genre(pdir)[1])
            write_order(pdir)
            prof, declared = project_genre(pdir)
            self.assertEqual((prof.genre, declared), ("macro_monetary", True))
            write_order(pdir, genre="nope")
            with self.assertRaises(GenreError):
                project_genre(pdir)


class WorkerWiringTest(unittest.TestCase):
    def _args(self, td: str) -> argparse.Namespace:
        return argparse.Namespace(projects_root=td, project_id="p")

    def test_visual_qa_rubric_required_for_genre(self) -> None:
        from workers.visual_qa_worker import VisualQAWorker  # noqa: PLC0415

        base = {"schema_version": 1, "verdict": "pass"}
        full = {**base, "rubric": [{"item": i, "ok": True, "evidence": "여덟 글자 이상 근거"} for i in range(1, 8)]}
        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td) / "p"
            pdir.mkdir()
            w = VisualQAWorker()
            with mock.patch("workers.base_worker.REPO_ROOT", Path("/")):
                args = self._args(td)
                w.bind_genre(args)
                w.check_parsed(args, None, QAVerdict.model_validate(base))            # 지정학 — 루브릭 없음
                with self.assertRaises(ValueError):
                    w.check_parsed(args, None, QAVerdict.model_validate(full))
                write_order(pdir)
                w.bind_genre(args)
                with self.assertRaises(ValueError):
                    w.check_parsed(args, None, QAVerdict.model_validate(base))
                w.check_parsed(args, None, QAVerdict.model_validate(full))
                prov = w.worker_provenance()
                self.assertEqual((prov.genre, prov.genre_declared), ("macro_monetary", True))
                self.assertIn("장르 루브릭", w.system_prompt())

    def test_rubric_missing(self) -> None:
        v = QAVerdict.model_validate({"verdict": "pass", "rubric": [
            {"item": 1, "ok": True, "evidence": "여덟 글자 이상 근거"}, {"item": 1, "ok": False, "evidence": "여덟 글자 이상 근거"},
            {"item": 9, "ok": True, "evidence": "여덟 글자 이상 근거"}]})
        self.assertEqual(v.rubric_missing(3), [1, 2, 3, 9])

    def test_stage_text(self) -> None:
        from workers.direction_io import series_records_text, stage_text  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td)
            self.assertEqual(series_records_text(pdir), "(없음)")
            write_order(pdir)
            out = stage_text(pdir, load_genre("macro_monetary"))
            self.assertIn("(지도 무대 아님) 주 무대 backdrop", out)
            self.assertIn("차트 아일랜드", out)
            self.assertIn("series:FEDFUNDS · 단위 % ·", out)

    def test_script_series_block_only_with_order(self) -> None:
        from workers.script_worker import ScriptWorker  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td) / "p"
            pdir.mkdir()
            w = ScriptWorker()
            with mock.patch("workers.base_worker.REPO_ROOT", Path("/")):
                self.assertEqual(w._series_block(self._args(td)), "")
                write_order(pdir)
                blk = w._series_block(self._args(td))
            self.assertIn("데이터 레코드 (order.yaml", blk)
            self.assertIn("series:FEDFUNDS", blk)


if __name__ == "__main__":
    unittest.main()
