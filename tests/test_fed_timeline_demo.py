"""시간축 실증 프로젝트 fed_timeline_demo (v4.3.0, back_and_forth D-0084 작업 6·9, D-0086·D-0088).

연출·원고는 입력 파일 검사(자산 없이), 프리뷰는 plan.json·tts 가 있을 때(artifacts/phaseG3-v4.3.0 에서 복원 — 없으면 환경 오류로 실패).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

from engine.direction import load_direction_doc
from script.lint import lint
from script.schema import Script

REPO = Path(__file__).resolve().parent.parent
PROJ = REPO / "projects" / "fed_timeline_demo"


class DemoInputsTest(unittest.TestCase):
    def test_direction_is_timeline_macro_monetary(self) -> None:
        d = load_direction_doc(PROJ / "direction.yaml")
        self.assertEqual((d.genre_name(), d.main_stage(), d.genre_profile().status), ("macro_monetary", "timeline", "proposed"))
        cfg = d.stage_settings("timeline")
        self.assertEqual([ln["id"] for ln in cfg["lanes"]], ["policy_rate", "inflation", "events"])
        self.assertEqual(cfg["lanes"][0]["label"], "연방기금 실효금리")   # 레코드 = 실효금리(기준금리 목표 범위 아님)
        self.assertEqual({e["series_id"] for e in d.events if e["type"] == "series"}, {"FEDFUNDS", "CPIAUCSL"})
        self.assertTrue(all("value" not in e and "values" not in e for e in d.events))   # 값은 레코드에서만

    def test_script_numbers_match_records(self) -> None:
        sc = Script.model_validate(yaml.safe_load((PROJ / "script.yaml").read_text(encoding="utf-8")))
        self.assertEqual(lint(sc).errors, [])
        self.assertTrue(8 <= sum(len(s.sentences) for s in sc.scenes) <= 10)
        self.assertTrue(all(src.startswith("series:") for s in sc.scenes for x in s.sentences for src in x.sources))

    def test_credits_have_series_and_notice(self) -> None:
        cr = yaml.safe_load((PROJ / "credits.yaml").read_text(encoding="utf-8"))
        self.assertIn("series", [s.get("auto") for s in cr["sections"]])
        self.assertIn("투자 권유가 아닌 정보 제공 목적", json.dumps(cr, ensure_ascii=False))   # 20 §5.2


class DemoPreviewTest(unittest.TestCase):
    def test_preview_checks_and_provenance(self) -> None:
        missing = [p for p in ("plan.json", "tts", "assets/rights_registry.json") if not (PROJ / p).exists()]
        if missing:
            raise RuntimeError(f"fed_timeline_demo 자산 없음 {missing} — artifacts/phaseG3-v4.3.0 복원(run_log §0)")
        from engine.render import main  # noqa: PLC0415

        self.assertEqual(main([str(PROJ), "--preview", "auto"]), 0)
        chk = json.loads((PROJ / "prev" / "checks.json").read_text(encoding="utf-8"))
        self.assertEqual((chk["hard"], len(chk["items"])), (0, 22))   # v4.10.0 D-0116 geo_mismatch, v4.7.0 D-0106 endcard_roll(warning), D-0107 boundary_as_route·geo_unsourced 추가
        prov = json.loads((PROJ / "prev" / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(prov["stage"]["name"], "timeline")
        self.assertEqual(prov["genre"], {"name": "macro_monetary", "declared": True, "status": "proposed"})
        self.assertEqual({s["series_id"] for s in prov["series"]}, {"FEDFUNDS", "CPIAUCSL"})
        self.assertEqual(next(s for s in prov["series"] if s["series_id"] == "CPIAUCSL")["missing"], ["2025-10-01"])


if __name__ == "__main__":
    unittest.main()
