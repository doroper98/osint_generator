"""수직 슬라이스 V2 — build-scene CLI + scene_builder(순수).

script_writing 까지 진행 후 build-scene 이 full_script 를 결정론적으로
scene_manifest.json 으로 변환하고 state 를 script_writing → script_review →
scene_planning 으로 전이하는지 검증. LLM 미사용(순수 변환).

실행: python -m unittest tests.test_scene_flow
"""

from __future__ import annotations

from orchestrator.main import main as cli_main
from orchestrator.scene_builder import build_scene_manifest
from schemas.models import FullScript, ProjectState, SceneManifest
from tests.test_script_flow import VALID_SCRIPT_JSON, _ScriptHarness


class _SceneHarness(_ScriptHarness):
    def _advance_to_script_writing(self) -> None:
        self._advance_to_research_in_progress()
        self._stub(VALID_SCRIPT_JSON)
        self.assertEqual(cli_main(["build-script", "demo3"]), 0)
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.SCRIPT_WRITING.value,
        )


class TestSceneBuilderPure(_SceneHarness):
    """scene_builder 결정론·매핑 규칙 (순수 함수, 디스크 불필요)."""

    def test_one_scene_per_segment_with_cumulative_timing(self) -> None:
        script = FullScript.model_validate_json(VALID_SCRIPT_JSON)
        manifest = build_scene_manifest(script)
        self.assertEqual(len(manifest.scenes), len(script.segments))
        # 누적 타이밍: seg est 6/8/9 → start 0/6/14.
        self.assertEqual([s.start_sec for s in manifest.scenes], [0.0, 6.0, 14.0])
        self.assertEqual(manifest.scenes[0].duration_sec, 6.0)
        # 라벨 있는 세그먼트(seg_03 <주장>)는 inference_label_required.
        self.assertFalse(manifest.scenes[0].inference_label_required)  # label null
        self.assertTrue(manifest.scenes[2].inference_label_required)   # <주장>
        # narration_segment_ids 가 원 segment 를 가리킴.
        self.assertEqual(manifest.scenes[2].narration_segment_ids, ["seg_03"])
        # claim_refs 있는 세그먼트는 source_link_required.
        self.assertTrue(manifest.scenes[1].source_link_required)   # claim_01
        self.assertFalse(manifest.scenes[0].source_link_required)  # claim_refs 없음

    def test_deterministic(self) -> None:
        script = FullScript.model_validate_json(VALID_SCRIPT_JSON)
        a = build_scene_manifest(script).model_dump_json()
        b = build_scene_manifest(script).model_dump_json()
        self.assertEqual(a, b)


class TestBuildSceneCLI(_SceneHarness):
    def test_creates_manifest_and_advances_state(self) -> None:
        self._advance_to_script_writing()
        rc = cli_main(["build-scene", "demo3"])
        self.assertEqual(rc, 0)

        path = self.projects_root / "demo3" / "06_scene" / "scene_manifest.json"
        self.assertTrue(path.exists())
        manifest = SceneManifest.model_validate_json(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.project_id, "demo3")
        self.assertEqual(len(manifest.scenes), 3)

        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.SCENE_PLANNING.value,
        )

    def test_rejected_outside_script_writing(self) -> None:
        self._create_demo3()  # created
        self.assertEqual(cli_main(["build-scene", "demo3"]), 2)

    def test_invalid_project_id_rejected(self) -> None:
        self.assertEqual(cli_main(["build-scene", "../etc"]), 1)


if __name__ == "__main__":
    import unittest

    unittest.main()
