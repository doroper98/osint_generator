"""CompositionPlan 연출 계층 테스트 (codex 엔진 — ADDENDUM_04).

검증 축:
① plan_validator — 번들 숫자 통과 / 번들 외 숫자 <미검증> 라벨 (사실 가드, C9)
② _apply_plan_to_scenes — 헤드라인 override / 미검증 prefix / 재정렬 / 재타이밍 (사실 불변)
③ _cues_from_plan — 씬별 순차 자막 + 미검증 라벨
④ plan_for_bundle(backend="stub") — BaseLLMWorker stub 경로로 유효 CompositionPlan 산출
⑤ build_composition_html_from_bundle(plan) — plan.title override + 폴백 back-compat
"""

import unittest

from orchestrator.hyperframes_compose import (
    build_composed_scenes,
    build_composition_html_from_bundle,
    _apply_plan_to_scenes,
    _cues_from_plan,
)
from orchestrator.plan_validator import validate_and_label_plan
from orchestrator.composition_planner import plan_for_bundle
from schemas.models import (
    BundleChart,
    CompositionPlan,
    PlannedCaption,
    PlannedScene,
    ReportBundle,
)


def _chart(type_, data, title="제목"):
    return BundleChart.model_validate({
        "chart_id": "c1", "type": type_, "title": title, "data": data,
        "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"},
    })


def _bundle(sections, charts, headline="헤드라인"):
    return ReportBundle.model_validate({
        "schema_version": 1, "bundle_kind": "report_bundle",
        "producer": {"system": "agents_reviewer", "version": "5.5"},
        "report": {"report_id": "r1", "headline": headline},
        "sections": sections, "charts": charts,
    })


def _simple_bundle():
    # 번들에 21.7 이라는 숫자가 prose 에 등장 → allowed set 에 들어감.
    return _bundle(
        sections=[{"section_id": "s1", "heading": "요약", "prose": "월 매출은 21.7억 달러다.",
                   "chart_refs": []}],
        charts=[],
    )


class TestPlanValidator(unittest.TestCase):
    def test_bundle_number_passes_foreign_number_labeled(self):
        b = _simple_bundle()
        plan = CompositionPlan(plan_engine="codex", captions=[
            PlannedCaption(scene_ref="x", order=0, text="월 21.7억 달러"),   # 번들 존재
            PlannedCaption(scene_ref="x", order=1, text="연 999조 원"),      # 번들 부재
        ])
        san, rep = validate_and_label_plan(plan, b)
        self.assertFalse(san.captions[0].unverified)
        self.assertTrue(san.captions[1].unverified)
        self.assertTrue(any(f.token == "999" for f in rep.findings))

    def test_headline_foreign_number_flags_field(self):
        b = _simple_bundle()
        plan = CompositionPlan(plan_engine="codex",
                               scenes=[PlannedScene(scene_id="z", headline="과장된 5000억")])
        san, _ = validate_and_label_plan(plan, b)
        self.assertIn("headline", san.scenes[0].unverified_fields)

    def test_decimal_integer_part_tolerated(self):
        b = _simple_bundle()  # 번들에 "21.7"
        plan = CompositionPlan(plan_engine="codex",
                               captions=[PlannedCaption(scene_ref="x", order=0, text="약 21억")])
        san, _ = validate_and_label_plan(plan, b)
        self.assertFalse(san.captions[0].unverified)  # 21 ⊂ 21.7 → 통과


class TestApplyPlan(unittest.TestCase):
    def _two_text_scenes(self):
        b = _bundle(
            sections=[
                {"section_id": "s1", "heading": "첫째", "prose": "본문1", "chart_refs": []},
                {"section_id": "s2", "heading": "둘째", "prose": "본문2", "chart_refs": []},
            ],
            charts=[],
        )
        return b

    def test_headline_override_and_reorder_and_retiming(self):
        b = self._two_text_scenes()
        base = build_composed_scenes(b)
        self.assertEqual([s.scene_id for s in base], ["s1", "s2"])
        plan = CompositionPlan(plan_engine="codex", scenes=[
            PlannedScene(scene_id="s1", order=1, headline="새 첫째", duration_sec=6.0),
            PlannedScene(scene_id="s2", order=0, headline="새 둘째"),
        ])
        out = _apply_plan_to_scenes([s.model_copy(deep=True) for s in base], plan)
        # s2 가 order=0 으로 앞에 옴
        self.assertEqual([s.scene_id for s in out], ["s2", "s1"])
        # 헤드라인 override (text 씬 → heading)
        by = {s.scene_id: s for s in out}
        self.assertEqual(by["s1"].heading, "새 첫째")
        self.assertEqual(by["s2"].heading, "새 둘째")
        # 페이싱 override + start_sec 재계산(s2 먼저)
        self.assertEqual(by["s2"].start_sec, 0.0)
        self.assertEqual(by["s1"].duration_sec, 6.0)
        self.assertAlmostEqual(by["s1"].start_sec, by["s2"].duration_sec, places=3)

    def test_unverified_headline_gets_label_prefix(self):
        b = self._two_text_scenes()
        base = build_composed_scenes(b)
        plan = CompositionPlan(plan_engine="codex", scenes=[
            PlannedScene(scene_id="s1", headline="9조 헤드라인", unverified_fields=["headline"]),
        ])
        out = _apply_plan_to_scenes([s.model_copy(deep=True) for s in base], plan)
        by = {s.scene_id: s for s in out}
        self.assertTrue(by["s1"].heading.startswith("<미검증> "))


class TestCuesFromPlan(unittest.TestCase):
    def test_sequential_cues_with_label(self):
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "h", "prose": "p", "chart_refs": []}],
            charts=[],
        )
        scenes = build_composed_scenes(b)
        sid = scenes[0].scene_id
        plan = CompositionPlan(plan_engine="codex", captions=[
            PlannedCaption(scene_ref=sid, order=0, text="첫 줄"),
            PlannedCaption(scene_ref=sid, order=1, text="둘째 줄", unverified=True),
        ])
        cues = _cues_from_plan(scenes, plan)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].at_sec, scenes[0].start_sec)
        self.assertTrue(cues[1].text.startswith("<미검증> "))


class TestPlannerStub(unittest.TestCase):
    def test_stub_returns_valid_plan_matching_skeleton(self):
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "요약",
                       "prose": "한 문장. 두 문장. 세 문장.", "chart_refs": []}],
            charts=[],
        )
        plan, why = plan_for_bundle(b, project_id="_pytest_planner", backend="stub")
        self.assertIsNotNone(plan, why)
        self.assertEqual(plan.plan_engine, "stub")
        skeleton_ids = {s.scene_id for s in build_composed_scenes(b)}
        self.assertTrue({s.scene_id for s in plan.scenes}.issubset(skeleton_ids))
        self.assertTrue(plan.captions)  # prose 문장 → 자막

    def test_html_uses_plan_title_and_backcompat(self):
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "h", "prose": "p", "chart_refs": []}],
            charts=[], headline="원래 제목",
        )
        plan = CompositionPlan(plan_engine="codex", title="플랜 제목")
        _, html_with = build_composition_html_from_bundle(b, plan)
        self.assertIn("플랜 제목", html_with)
        _, html_without = build_composition_html_from_bundle(b)  # back-compat
        self.assertIn("원래 제목", html_without)


if __name__ == "__main__":
    unittest.main()
