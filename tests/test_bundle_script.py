"""번들 → 원고 초안(v3.5.0, D-0063 작업 3, D-0064 쟁점 4) — 장면 경계 규칙·12막 금지·금지 문구 표시·P4·날짜 출처·ScriptWorker 초안 블록."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from bundle.entities import join_entities
from bundle.load import corpus_files, load_report_bundle
from bundle.to_script import build_draft, dump_draft_yaml
from engine.entities import load_entities
from rules import load_rules
from schemas.models import ReportBundle
from script.schema import Script

REPO = Path(__file__).resolve().parents[1]
REG = load_entities()


def _sec(i: int, lines: list[str], charts: list[str] | None = None, tts: list[str] | None = None) -> dict:
    return {"section_id": f"s{i}", "heading": f"제목{i}", "chart_refs": charts or [],
            "video": {"narration": lines, "narration_tts": tts or [], "emphasis": []}}


def _bundle(sections: list[dict], **extra: object) -> ReportBundle:
    return ReportBundle.model_validate({
        "schema_version": 1, "producer": {"system": "agents_reviewer", "version": "v8"}, "generated_at": "2026-08-29T10:00:00+09:00",
        "report": {"report_id": "r1", "headline": "헤드라인", "deck": "덱"}, "sections": sections,
        "charts": [{"chart_id": "ch-1", "type": "gantt", "provenance": {"origin": "narrative_inference"}},
                   {"chart_id": "ch-2", "type": "dot_matrix", "provenance": {"origin": "narrative_inference"}}],
        "map": {"markers": [{"id": "moscow", "name": "모스크바", "lng": 37.6, "lat": 55.7},
                            {"id": "hormuz", "name": "호르무즈 해협", "lng": 56.4, "lat": 26.6}]}, **extra})


def _draft(b: ReportBundle):  # noqa: ANN202
    return build_draft(b, join_entities(b, REG), REG)


class BoundaryTest(unittest.TestCase):
    def test_merge_same_space_and_plain_sections(self) -> None:
        b = _bundle([_sec(1, ["모스크바에 내렸습니다."]), _sec(2, ["아무 장소도 없는 문장입니다."]), _sec(3, ["모스크바는 조용했습니다."])])
        sc, n = _draft(b)
        self.assertEqual(n.scenes, 1)                                        # 같은 공간 + 공간 없음 → 합침
        self.assertEqual(n.boundaries[0].sections, ["s1", "s2", "s3"])

    def test_split_on_space_and_chart_change(self) -> None:
        b = _bundle([_sec(1, ["모스크바에 내렸습니다."]), _sec(2, ["호르무즈 해협이 막혔습니다."]),
                     _sec(3, ["일정을 겹쳐 봅니다."], ["ch-1"]), _sec(4, ["비율을 봅니다."], ["ch-2"]), _sec(5, ["이어지는 말입니다."])])
        _, n = _draft(b)
        self.assertEqual([bd.sections for bd in n.boundaries], [["s1"], ["s2"], ["s3"], ["s4", "s5"]])
        self.assertIn("공간 바뀜", n.boundaries[1].reason)
        self.assertIn("차트 종류 바뀜", n.boundaries[3].reason)

    def test_heading_never_on_screen(self) -> None:
        sc, n = _draft(_bundle([_sec(1, ["첫 문장입니다."]), _sec(2, ["둘째 문장입니다."])]))
        texts = [s.text for scene in sc.scenes for s in scene.sentences]
        self.assertFalse(any("제목" in t for t in texts))
        self.assertEqual([c.title for c in n.chapters], ["제목1", "제목2"])   # 챕터명 후보로만


class DraftRulesTest(unittest.TestCase):
    def test_banned_phrase_marked_not_rewritten(self) -> None:
        pat = load_rules().banned_phrases.patterns[1]                        # '한\\s?번에 흔들'
        bad = "이 일이 시장을 한번에 흔들었습니다."
        self.assertTrue(re.search(pat, bad))
        sc, n = _draft(_bundle([_sec(1, ["괜찮은 문장입니다.", bad])]))
        self.assertEqual(sc.scenes[0].sentences[1].text, bad)                # 어댑터는 다시 쓰지 않는다(P8)
        self.assertEqual([m.sid for m in n.rewrite_required], ["sc01_1"])
        self.assertIn("# rewrite_required: true", dump_draft_yaml(sc, n))

    def test_tts_bundle_verbatim_else_rule(self) -> None:
        sc, n = _draft(_bundle([_sec(1, ["8월 23일에 떠났습니다."], tts=["팔월 이십삼일에 떠났습니다."]),
                                _sec(2, ["18개월 동안 1% 움직였습니다."])]))
        s = [x for scene in sc.scenes for x in scene.sentences]
        self.assertEqual(s[0].tts, "팔월 이십삼일에 떠났습니다.")
        self.assertEqual([t.source for t in n.tts], ["bundle", "rule"])
        self.assertIsNone(re.search(load_rules().tts_rules.forbidden_chars_regex, s[1].tts or s[1].text))

    def test_timeline_date_else_report(self) -> None:
        b = _bundle([_sec(1, ["8월 23일, 수송기가 떠납니다.", "이유는 곧 보입니다."])],
                    timeline={"points": [{"date": "2026-08-23", "label": "출발"}]})
        sc, n = _draft(b)
        self.assertEqual([s.date for s in sc.scenes[0].sentences], ["2026.08.23", "2026.08.29"])
        self.assertEqual(n.date_sources, {"sc01_0": "timeline", "sc01_1": "report"})

    def test_no_narration_is_error(self) -> None:
        with self.assertRaises(ValueError):
            _draft(_bundle([{"section_id": "s1", "heading": "h"}]))


class CorpusDraftTest(unittest.TestCase):
    def test_corpus_drafts_pass_script_and_scenes_differ(self) -> None:
        """코퍼스 전부: 초안 YAML(주석 포함)이 Script 그대로 통과(P4), 장면 수 ≠ 섹션 수가 다수(12막 1:1 금지)."""
        made = differ = 0
        for f in corpus_files([REPO / "json", REPO / "samples"]):
            b = load_report_bundle(f)
            try:
                sc, n = _draft(b)
            except ValueError:
                continue                                                     # 문장 없는 번들 = 명시 오류
            Script.model_validate(yaml.safe_load(dump_draft_yaml(sc, n)))
            made += 1
            differ += n.scenes != n.sections
        self.assertGreaterEqual(made, 60)
        self.assertGreater(differ / made, 0.8)


class ScriptWorkerDraftBlockTest(unittest.TestCase):
    def _prompt(self, pdir: Path) -> str:
        from workers.script_worker import ScriptWorker  # noqa: PLC0415

        (pdir / "project_manifest.json").write_text(json.dumps({"project_id": pdir.name, "title": "t", "category": "geopolitics"}), encoding="utf-8")
        (pdir / "facts.json").write_text((REPO / "tests/fixtures/facts_minimal.json").read_text(encoding="utf-8"), encoding="utf-8")
        (pdir / "intake").mkdir(exist_ok=True)
        (pdir / "intake/claims.json").write_text(json.dumps({"claims": []}), encoding="utf-8")
        args = argparse.Namespace(project_id=pdir.name, task_id="t", projects_root=str(pdir.parent))
        w = ScriptWorker()
        with mock.patch.object(ScriptWorker, "project_dir", return_value=pdir):
            return w.build_user_prompt(args, None)  # type: ignore[arg-type]

    def test_block_only_with_draft_file(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d) / "p"
            pdir.mkdir()
            plain = self._prompt(pdir)
            self.assertNotIn("{draft_block}", plain)
            self.assertNotIn("원고 초안 (script.draft.yaml", plain)
            sc, n = _draft(_bundle([_sec(1, ["첫 문장입니다."])]))
            text = dump_draft_yaml(sc, n)
            (pdir / "script.draft.yaml").write_text(text, encoding="utf-8")
            got = self._prompt(pdir)
            self.assertIn("rewrite_required", got)
            self.assertIn(text.strip(), got)
            Script.model_validate(yaml.safe_load(text))                      # 블록 속 초안도 Script 그대로


if __name__ == "__main__":
    unittest.main()
