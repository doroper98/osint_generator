"""수직 슬라이스 V3 — render_props 빌더(순수) + render-debug --props-only CLI.

scene_manifest + full_script → render_props.json 변환을 검증한다. 실제 Remotion 렌더
(node/chromium 필요)는 단위테스트 대상이 아니며 실행 검증으로 확인한다.

실행: python -m unittest tests.test_render_flow
"""

from __future__ import annotations

import unittest

from orchestrator.audio_service import build_audio
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


class TestSubtitleCues(unittest.TestCase):
    def test_splits_sentences_and_distributes_time(self) -> None:
        from orchestrator.render_io import split_subtitle_cues

        nar = "첫 문장입니다. 두 번째 문장이고요. 세 번째 문장으로 마칩니다."
        cues = split_subtitle_cues(nar, 12.0)
        self.assertEqual(len(cues), 3)  # 문장 단위 3개
        # 첫 큐는 scene 시작.
        self.assertEqual(cues[0].startSec, 0.0)
        # 타이밍이 scene 길이를 정확히 채움(반올림 오차 흡수).
        self.assertAlmostEqual(cues[-1].startSec + cues[-1].durationSec, 12.0, places=2)
        # 큐가 순서대로 이어짐.
        for a, b in zip(cues, cues[1:]):
            self.assertAlmostEqual(a.startSec + a.durationSec, b.startSec, places=2)

    def test_long_sentence_wrapped_to_lines(self) -> None:
        from orchestrator.render_io import split_subtitle_cues

        long_one = "가" * 100 + "."  # 한 줄 상한(42) 초과 → 여러 큐로
        cues = split_subtitle_cues(long_one, 10.0)
        self.assertGreater(len(cues), 1)
        self.assertTrue(all(len(c.text) <= 42 for c in cues))

    def test_empty_or_zero_duration(self) -> None:
        from orchestrator.render_io import split_subtitle_cues

        self.assertEqual(split_subtitle_cues("", 5.0), [])
        self.assertEqual(split_subtitle_cues("내용", 0.0), [])


class TestSceneSourceCitation(unittest.TestCase):
    def test_source_citation_via_build_render_props(self) -> None:
        from orchestrator.render_io import build_render_props
        from orchestrator.scene_builder import build_scene_manifest
        from schemas.models import (
            Evidence, FullScript as _FS, ResearchClaim, ResearchDossier,
            ScriptChapter, ScriptSegment, SourceEntry, SourceRegistry,
        )

        script = _FS(
            project_id="p", title="t", topic="t",
            chapters=[ScriptChapter(chapter_id="c", title="c")],
            segments=[
                ScriptSegment(segment_id="seg_01", chapter_id="c",
                              narration="첫 문장.", on_screen_caption="캡션",
                              claim_refs=["C-1"], est_duration_sec=4.0),
            ],
        )
        dossier = ResearchDossier(
            project_id="p", claims=[
                ResearchClaim(claim_id="C-1", statement="주장",
                              evidence=[Evidence(source_id="mkt-1", quote="q")]),
            ],
        )
        registry = SourceRegistry(project_id="p", sources=[
            SourceEntry(source_id="mkt-1", platform="YAHOO", source_type="data_series"),
        ])
        sm = build_scene_manifest(script)
        props = build_render_props(
            sm, script, research_dossier=dossier, source_registry=registry
        )
        self.assertEqual(props.scenes[0].source, "YAHOO")

    def test_no_source_when_unresolvable(self) -> None:
        from orchestrator.render_io import build_render_props
        from orchestrator.scene_builder import build_scene_manifest
        from schemas.models import FullScript as _FS, ScriptChapter, ScriptSegment

        script = _FS(
            project_id="p", title="t", topic="t",
            chapters=[ScriptChapter(chapter_id="c", title="c")],
            segments=[ScriptSegment(segment_id="seg_01", chapter_id="c",
                                    narration="문장.", claim_refs=[], est_duration_sec=4.0)],
        )
        sm = build_scene_manifest(script)
        props = build_render_props(sm, script)  # dossier/registry 없음
        self.assertEqual(props.scenes[0].source, "")


class TestSceneChartAttach(unittest.TestCase):
    def _bundle_with_charts(self):
        from schemas.models import (
            BundleChart, BundleProvenance, BundleProducer, BundleReport, ReportBundle,
        )
        prov = BundleProvenance(origin="measured", verification="confirmed")
        return ReportBundle(
            producer=BundleProducer(system="agents_reviewer", version="v5.5.2"),
            report=BundleReport(report_id="r", headline="h"),
            charts=[
                BundleChart(chart_id="ch-line", type="line", title="유가",
                            data=[{"x": "a", "y": 1}, {"x": "b", "y": 2}], provenance=prov),
                BundleChart(chart_id="ch-unk", type="future_unknown_type", title="미래형",
                            data=[{"x": 1, "y": 2}], provenance=prov),
                BundleChart(chart_id="ch-table", type="table", title="OCML vs E-BOM",
                            data={
                                "columns": [
                                    {"key": "field", "label": "필드"},
                                    {"key": "ocml", "label": "OCML", "align": "center"},
                                    {"key": "ebom", "label": "E-BOM", "align": "center"},
                                ],
                                "rows": [
                                    {"cells": {"field": "반제품 구조", "ocml": "✗ 없음",
                                               "ebom": "✓ 있음"}, "highlight": True},
                                ],
                            }, provenance=prov),
            ],
        )

    def _script(self, refs0, refs1):
        from schemas.models import FullScript as _FS, ScriptChapter, ScriptSegment
        return _FS(
            project_id="p", title="t", topic="t",
            chapters=[ScriptChapter(chapter_id="c", title="c")],
            segments=[
                ScriptSegment(segment_id="seg_01", chapter_id="c", narration="첫.",
                              claim_refs=refs0, est_duration_sec=4.0),
                ScriptSegment(segment_id="seg_02", chapter_id="c", narration="둘.",
                              claim_refs=refs1, est_duration_sec=4.0),
            ],
        )

    def test_supported_line_chart_attaches(self) -> None:
        from orchestrator.render_io import build_render_props
        from orchestrator.scene_builder import build_scene_manifest

        script = self._script(["ch-line"], [])
        bundle = self._bundle_with_charts()
        props = build_render_props(build_scene_manifest(script), script, report_bundle=bundle)
        self.assertIsNotNone(props.scenes[0].chartData)
        self.assertEqual(props.scenes[0].chartData.type, "line")
        self.assertEqual(props.scenes[0].chartData.chartId, "ch-line")
        self.assertIsNone(props.scenes[1].chartData)

    def test_table_chart_attaches(self) -> None:
        from orchestrator.render_io import build_render_props
        from orchestrator.scene_builder import build_scene_manifest

        script = self._script(["ch-table"], [])  # table = cinematic 표 렌더러 (v0.41.0)
        bundle = self._bundle_with_charts()
        props = build_render_props(build_scene_manifest(script), script, report_bundle=bundle)
        self.assertIsNotNone(props.scenes[0].chartData)
        self.assertEqual(props.scenes[0].chartData.type, "table")
        self.assertEqual(props.scenes[0].chartData.chartId, "ch-table")

    def test_unsupported_type_not_attached(self) -> None:
        from orchestrator.render_io import build_render_props
        from orchestrator.scene_builder import build_scene_manifest

        script = self._script(["ch-unk"], [])  # 미지원 타입 → attach 안 됨(텍스트 폴백)
        bundle = self._bundle_with_charts()
        props = build_render_props(build_scene_manifest(script), script, report_bundle=bundle)
        self.assertIsNone(props.scenes[0].chartData)


class TestSceneMapAttach(unittest.TestCase):
    def test_map_attaches_to_scene_referencing_map_id(self) -> None:
        from orchestrator.render_io import build_render_props
        from orchestrator.scene_builder import build_scene_manifest
        from schemas.models import (
            BundleMap, BundleMapArc, BundleMapMarker, BundleProducer, BundleReport,
            FullScript as _FS, ReportBundle, ScriptChapter, ScriptSegment,
        )

        script = _FS(
            project_id="p", title="t", topic="t",
            chapters=[ScriptChapter(chapter_id="c", title="c")],
            segments=[
                ScriptSegment(segment_id="seg_01", chapter_id="c", narration="첫.",
                              claim_refs=["map-1"], est_duration_sec=4.0),
                ScriptSegment(segment_id="seg_02", chapter_id="c", narration="둘.",
                              claim_refs=[], est_duration_sec=4.0),
            ],
        )
        bundle = ReportBundle(
            producer=BundleProducer(system="agents_reviewer", version="v5.5.0"),
            report=BundleReport(report_id="r", headline="h"),
            map=BundleMap(
                id="map-1", center=[48.0, 32.0], zoom=4.0,
                markers=[
                    BundleMapMarker(id="a", name="A", lng=51.0, lat=35.0, highlight=True),
                    BundleMapMarker(id="b", name="B", lng=35.0, lat=32.0),
                ],
                arcs=[BundleMapArc(from_id="a", to_id="b", highlight=True)],
            ),
        )
        sm = build_scene_manifest(script)
        props = build_render_props(sm, script, report_bundle=bundle)

        s0 = props.scenes[0]
        self.assertIsNotNone(s0.mapData)
        self.assertEqual(len(s0.mapData.markers), 2)
        self.assertEqual(s0.mapData.arcs[0].fromId, "a")  # from_id → fromId 변환
        self.assertTrue(s0.mapData.arcs[0].highlight)
        # map id 를 참조하지 않는 scene 엔 안 붙음.
        self.assertIsNone(props.scenes[1].mapData)

    def test_no_map_without_bundle(self) -> None:
        from orchestrator.render_io import build_render_props
        from orchestrator.scene_builder import build_scene_manifest
        from schemas.models import FullScript as _FS, ScriptChapter, ScriptSegment

        script = _FS(
            project_id="p", title="t", topic="t",
            chapters=[ScriptChapter(chapter_id="c", title="c")],
            segments=[ScriptSegment(segment_id="seg_01", chapter_id="c",
                                    narration="문장.", est_duration_sec=4.0)],
        )
        sm = build_scene_manifest(script)
        props = build_render_props(sm, script)
        self.assertIsNone(props.scenes[0].mapData)


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
        # 인용부호 없는 caption → isQuote False (영상 문법 ③).
        self.assertFalse(props.scenes[0].isQuote)

    def test_quote_caption_marks_is_quote(self) -> None:
        # on_screen_caption 에 인용부호가 있으면 isQuote=True (강조색 렌더 신호).
        from schemas.models import ScriptChapter, ScriptSegment

        script = FullScript(
            project_id="demo3",
            title="t",
            topic="t",
            chapters=[ScriptChapter(chapter_id="ch1", title="c")],
            segments=[
                ScriptSegment(
                    segment_id="seg_01", chapter_id="ch1",
                    narration="한 관계자는 그렇게 말했다.",
                    on_screen_caption="「수요가 공급을 추월했다」",
                    est_duration_sec=4.0,
                ),
                ScriptSegment(
                    segment_id="seg_02", chapter_id="ch1",
                    narration="일반 서술 문장.",
                    on_screen_caption="평범한 캡션",
                    est_duration_sec=4.0,
                ),
            ],
        )
        scene_manifest = build_scene_manifest(script)
        props = build_render_props(scene_manifest, script)
        self.assertTrue(props.scenes[0].isQuote)
        self.assertFalse(props.scenes[1].isQuote)


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


class TestRenderWithAudio(_RenderHarness):
    """V4b — audio_manifest 가 있으면 실측 길이/오디오 경로가 render_props 에 반영."""

    def test_props_use_audio_durations_and_paths(self) -> None:
        self._advance_to_scene_planning()
        audio = build_audio("demo3", backend="stub")

        rc = cli_main(["render-debug", "demo3", "--props-only"])
        self.assertEqual(rc, 0)
        path = self.projects_root / "demo3" / "09_render" / "render_props.json"
        props = RenderProps.model_validate_json(path.read_text(encoding="utf-8"))

        # 각 scene 에 audioPath 가 붙고, 그 길이가 audio_manifest 와 일치.
        dur_by_seg = {a.segment_id: a.duration_sec for a in audio.segments}
        cursor = 0.0
        for sc in props.scenes:
            self.assertIsNotNone(sc.audioPath, f"{sc.sceneId} audioPath 누락")
            self.assertTrue(sc.audioPath.endswith(".wav"))
            # scene 1:1 segment → seg_id = sceneId 의 대응 (seg_01↔scene_01 순서).
            # 길이는 audio 와 일치, start 는 누적.
            self.assertAlmostEqual(sc.startSec, round(cursor, 3), places=2)
            cursor += sc.durationSec
        # 총 길이가 audio_manifest 총합과 근사.
        self.assertAlmostEqual(
            sum(s.durationSec for s in props.scenes),
            audio.total_duration_sec,
            places=1,
        )

    def test_pure_builder_without_audio_is_silent(self) -> None:
        # audio_manifest 미전달 → audioPath None, scene 타이밍 유지 (하위호환).
        script = FullScript.model_validate_json(VALID_SCRIPT_JSON)
        scene_manifest = build_scene_manifest(script)
        props = build_render_props(scene_manifest, script)
        self.assertTrue(all(s.audioPath is None for s in props.scenes))
        self.assertEqual(props.scenes[1].startSec, 6.0)


if __name__ == "__main__":
    import unittest

    unittest.main()
