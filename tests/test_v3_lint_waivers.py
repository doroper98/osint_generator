"""원고 린트 면제 목록 (v5.17.0, back_and_forth D-0168, DECISIONS D162).

정확 일치만 통과 / 목록 밖 오류 = 실패 / 낡은 면제(원고 변경·오류 없음) = 오류 / 면제 불가 kind = 로드 오류 /
승인일 ≥ 규칙 날짜 = 로드 오류 / provenance `features.lint.waived` / 호르무즈 실제 목록.
기준 원고 = 골든 `projects/hormuz_korea/script.yaml`(git 추적) — 오류 2건(uncertain-phrase now_3, flow-sparse -).
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from script import lint_waivers as LW
from script.lint import lint, load_claims_for
from script.plan import load_script
from script.schema import Plan

REPO = Path(__file__).resolve().parent.parent
HORMUZ = REPO / "projects" / "hormuz_korea"


def _waiver(script, kind: str, sid: str, **kw) -> dict:  # noqa: ANN001
    return {"kind": kind, "sid": sid, "text_sha1": LW.text_sha1(script, sid), "rule_since": "v5.5.0",
            "script_approved": "2026-09-28", "reason": "테스트", "decided_by": "D-0168", **kw}


class WaiverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.proj = Path(self.tmp.name)
        shutil.copy(HORMUZ / "script.yaml", self.proj / "script.yaml")
        self.script = load_script(self.proj)
        self.rep = lint(self.script, load_claims_for(HORMUZ))
        self.assertEqual({(i.kind, i.sid) for i in self.rep.errors}, {("uncertain-phrase", "now_3"), ("flow-sparse", "-")})

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, waivers: list[dict]) -> None:
        (self.proj / LW.FILE).write_text(yaml.safe_dump({"schema_version": 1, "waivers": waivers}, allow_unicode=True),
                                         encoding="utf-8")

    def test_exact_match_passes(self) -> None:
        self._write([_waiver(self.script, "uncertain-phrase", "now_3"), _waiver(self.script, "flow-sparse", "-")])
        rep, waived = LW.apply(self.rep, LW.load(self.proj), self.script)
        self.assertEqual(rep.errors, [])
        self.assertEqual(waived, [{"kind": "flow-sparse", "sid": "-", "decided_by": "D-0168"},
                                  {"kind": "uncertain-phrase", "sid": "now_3", "decided_by": "D-0168"}])
        self.assertEqual(len(rep.warnings), len(self.rep.warnings))   # 경고는 그대로 남는다

    def test_error_outside_list_still_fails(self) -> None:
        self._write([_waiver(self.script, "flow-sparse", "-")])
        rep, _ = LW.apply(self.rep, LW.load(self.proj), self.script)
        self.assertEqual([(i.kind, i.sid) for i in rep.errors], [("uncertain-phrase", "now_3")])

    def test_stale_waiver_is_error(self) -> None:
        w = _waiver(self.script, "uncertain-phrase", "now_3")
        self._write([w | {"text_sha1": "0" * 40}, _waiver(self.script, "flow-sparse", "-")])   # 원고가 바뀐 것과 같다
        with self.assertRaises(LW.LintWaiverError):
            LW.apply(self.rep, LW.load(self.proj), self.script)
        self._write([w, _waiver(self.script, "flow-sparse", "-"), _waiver(self.script, "uncertain-phrase", "open_0")])
        with self.assertRaises(LW.LintWaiverError):   # 일치하는 오류가 없는 면제
            LW.apply(self.rep, LW.load(self.proj), self.script)

    def test_unwaivable_kind_is_load_error(self) -> None:
        self._write([_waiver(self.script, "banned-phrase", "now_3")])
        with self.assertRaises(LW.LintWaiverError):
            LW.load(self.proj)

    def test_approval_after_rule_is_load_error(self) -> None:
        self._write([_waiver(self.script, "flow-sparse", "-", script_approved="2026-10-02")])
        with self.assertRaises(LW.LintWaiverError):
            LW.load(self.proj)
        self._write([_waiver(self.script, "flow-sparse", "-", rule_since="v0.0.99")])
        with self.assertRaises(LW.LintWaiverError):   # CHANGELOG 태그가 아니다
            LW.load(self.proj)

    def test_hormuz_real_list(self) -> None:
        rep, waived = LW.apply(self.rep, LW.load(HORMUZ), self.script)
        self.assertEqual(rep.errors, [])
        self.assertEqual({x["decided_by"] for x in waived}, {"D-0168"})


class ProvenanceTest(unittest.TestCase):
    def test_lint_waived_recorded_only_when_present(self) -> None:
        from engine import provenance  # noqa: PLC0415

        base = {"sentences": [], "cards": [], "scene_start": {}, "total": 1.0, "voice": "v", "title": "t", "subtitle": "", "date": ""}
        with_w = provenance.build(Plan.model_validate(base | {"lint_waived": [{"kind": "flow-sparse", "sid": "-", "decided_by": "D-0168"}]}),
                                  [], [], "0", {})
        without = provenance.build(Plan.model_validate(base), [], [], "0", {})
        feats = next(v for k, v in with_w.items() if isinstance(v, dict) and "at_word" in v)
        self.assertEqual(feats["lint"], {"waived": [{"kind": "flow-sparse", "sid": "-", "decided_by": "D-0168"}]})
        self.assertNotIn("lint", next(v for k, v in without.items() if isinstance(v, dict) and "at_word" in v))


if __name__ == "__main__":
    unittest.main()
