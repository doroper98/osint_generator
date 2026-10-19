"""C8.3(사용자 결정 D187, back_and_forth D-0188 §1-4) — 실측 상위 느린 테스트가 `slow` 마커를 달았는지(빠른 묶음 `-m "not slow"` 이 3~5분 안에 끝나게).

목록 = 2026-10-11 전체 pytest `--durations=60` 실측 상위(≥ 25초). 마커가 빠지면 빠른 묶음이 조용히 느려진다 — 그 회귀를 잡는다.
새로 느린 테스트를 만들면 클래스에 `@pytest.mark.slow` 를 달고, 이 목록 갱신은 다음 실측 때(하루 1회 전체 pytest)에 한다.
"""

from __future__ import annotations

import importlib
import tomllib
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MEASURED_SLOW = [   # (모듈, 클래스) — 실측 25초 이상
    ("tests.test_g8_animatic", "AnimaticMapRenderTest"),   # v7.4.0 D-0241 — 막지도 NoAssetRenderTest 를 본 지도 렌더로 교체
    ("tests.test_gates_pipeline", "CliTest"),
    ("tests.test_gates_pipeline", "CommandCenterKeysTest"),
    ("tests.test_gates_pipeline", "GateTest"),
    ("tests.test_gates_pipeline", "AnimaticGateTest"),
    ("tests.test_v3_claims_migration", "V3ClaimsMigrationTest"),
    ("tests.anti_inertia.test_q3_light_e2e", "LightE2ETest"),
    ("tests.anti_inertia.test_provenance_e2e", "ProvenanceE2ETest"),
    ("tests.test_g8_animatic", "AnimaticRunTest"),
    ("tests.test_g9_attribution", "ProjectImpactTest"),
    ("tests.test_v3_lint_waivers", "WaiverTest"),
    ("tests.test_engine_service", "RunStageTest"),
    ("tests.test_script_lint", "ScriptLintTest"),
    ("tests.test_g65_merge", "ReopenTest"),
    ("tests.test_g5_endcard_overflow", "OverflowTest"),
    ("tests.test_g5_labels_endcard", "ProjectPreviewNoLabelTest"),
]


class SlowMarkerTest(unittest.TestCase):
    def test_marker_registered_strict(self) -> None:
        cfg = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]
        self.assertIn("--strict-markers", cfg["addopts"])
        self.assertTrue(any(m.startswith("slow:") for m in cfg["markers"]))

    def test_measured_slow_classes_marked(self) -> None:
        missing = []
        for mod, cls in MEASURED_SLOW:
            c = getattr(importlib.import_module(mod), cls)
            if not any(getattr(m, "name", None) == "slow" for m in getattr(c, "pytestmark", [])):
                missing.append(f"{mod}::{cls}")
        self.assertEqual(missing, [], "느린 테스트에 @pytest.mark.slow 가 없다(C8.3)")


if __name__ == "__main__":
    unittest.main()
