"""수직 슬라이스 V3 — render_props 빌더(순수) + render-debug --props-only CLI.

scene_manifest + full_script → render_props.json 변환을 검증한다. 실제 Remotion 렌더
(node/chromium 필요)는 단위테스트 대상이 아니며 실행 검증으로 확인한다.

실행: python -m unittest tests.test_render_flow
"""

from __future__ import annotations

from orchestrator.main import main as cli_main
from orchestrator.render_io import build_render_props
from orchestrator.scene_builder import build_scene_manifest
from schemas.models import FullScript, ProjectState, RenderProps
from tests.test_scene_flow import _SceneHarness
from tests.test_script_flow import VALID_SCRIPT_JSON


class _RenderHarness(_SceneHarness):
    def _advance_to_scene_planning(self) -> None:
        self._advance_to_script_writing()
        self.assertEqual(cli_main(["build-scene", "demo3"]), 0)
        self.assertEqual(
            self._load_manifest("demo3").current_state,
            ProjectState.SCENE_PLANNING.value,
        )


class TestBuildRenderPropsPure(_RenderHarness):
    def test_resolves_narration_label_and_source(self) -> None:
        script = FullScript.model_validate_json(VALID_SCRIPT_JSON)
        scene_manifest = build_scene_manifest(script)
        props = build_render_props(scene_manifest, script)

        self.assertEqual(props.project_id, "demo3")
        self.assertEqual(len(props.scenes), len(script.segments))
        # scene_01 (seg_01): narration 본문 결합, label 없음, source 없음.
        self.assertEqual(props.scenes[0].sceneId, "scene_01")
        self.assertEqual(props.scenes[0].narration, script.segments[0].narration)
        self.assertIsNone(props.scenes[0].label)
        self.assertFalse(props.scenes[0].sourceLinkRequired)
        # scene_03 (seg_03 <주장>, claim_02): 라벨 + 출처 표기.
        self.assertEqual(props.scenes[2].label, "<주장>")
        self.assertTrue(props.scenes[2].sourceLinkRequired)
        # 타이밍 보존.
        self.assertEqual(props.scenes[1].startSec, 6.0)


class TestRenderDebugCLI(_RenderHarness):
    def test_props_only_creates_render_props(self) -> None:
        self._advance_to_scene_planning()
        rc = cli_main(["render-debug", "demo3", "--props-only"])
        self.assertEqual(rc, 0)
        path = self.projects_root / "demo3" / "09_render" / "render_props.json"
        self.assertTrue(path.exists())
        props = RenderProps.model_validate_json(path.read_text(encoding="utf-8"))
        self.assertEqual(len(props.scenes), 3)

    def test_invalid_project_id_rejected(self) -> None:
        self.assertEqual(cli_main(["render-debug", "../etc", "--props-only"]), 1)

    def test_missing_scene_manifest_errors(self) -> None:
        # scene_manifest 없이 호출 → exit 1 (build-scene 안내).
        self._create_demo3()
        self.assertEqual(cli_main(["render-debug", "demo3", "--props-only"]), 1)


if __name__ == "__main__":
    import unittest

    unittest.main()
