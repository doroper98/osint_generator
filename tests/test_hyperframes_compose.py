"""ReportBundle → HyperFrames 컴포지션 변환기 테스트 (v0.34.14, 옵션 C).

검증 축:
① 차트 데이터 매핑 (candle/line/bar/donut, agents_reviewer 모양 → 컴포넌트 변수)
② 미지원 타입 폴백
③ 씬 펼치기 (section→scene, chart/text 분기, 누적 타이밍)
④ 복합값 JSON-문자열 인코딩 (sub-comp 인스턴스화 사고 회피 — v0.34.14)
⑤ HTML 렌더 계약 (data-composition-src / data-variable-values / 자막 큐)
"""

import json
import unittest

from orchestrator.hyperframes_compose import (
    build_composed_scenes,
    build_composition_html_from_bundle,
    chart_to_component,
    render_composition_html,
    _stringify_complex,
    _text_scene_body,
)
from schemas.models import BundleChart, ReportBundle


def _chart(type_: str, data, title="제목", unit=""):
    return BundleChart.model_validate({
        "chart_id": "c1", "type": type_, "title": title, "data": data,
        "provenance": {"origin": "measured", "verification": "confirmed",
                       "confidence": "high",
                       "sources": ([{"source_id": "s", "provider": "P", "unit": unit}] if unit else [])},
    })


def _bundle(sections, charts):
    return ReportBundle.model_validate({
        "schema_version": 1, "bundle_kind": "report_bundle",
        "producer": {"system": "agents_reviewer", "version": "5.5"},
        "report": {"report_id": "r1", "headline": "헤드라인"},
        "sections": sections, "charts": charts,
    })


class TestChartMapping(unittest.TestCase):
    def test_candle_shape(self) -> None:
        ch = _chart("candle", [
            {"date": "2026-03-02", "open": 71800, "high": 73000, "low": 71500, "close": 72600},
            {"date": "2026-03-09", "open": 72600, "high": 75000, "low": 72000, "close": 74100},
        ], unit="원")
        comp, v = chart_to_component(ch)
        self.assertEqual(comp, "candle")
        self.assertEqual(v["candles"][0], {"d": "03-02", "o": 71800, "h": 73000, "l": 71500, "c": 72600})
        self.assertLess(v["yMin"], 71500)
        self.assertGreater(v["yMax"], 75000)
        self.assertEqual(v["yUnit"], "원")
        self.assertEqual(v["takeaway"], "제목")

    def test_line_shape_with_event_callout(self) -> None:
        ch = _chart("line", [
            {"x": "2026-01", "y": 40},
            {"x": "2026-03", "y": 80.4, "event": "리스크오프"},
        ])
        comp, v = chart_to_component(ch, callout_t=2.5)
        self.assertEqual(comp, "line")
        self.assertEqual(v["series"][0]["points"], [40, 80.4])
        self.assertEqual(v["xLabels"], ["2026-01", "2026-03"])
        self.assertEqual(len(v["callouts"]), 1)
        self.assertEqual(v["callouts"][0]["title"], "리스크오프")
        self.assertEqual(v["callouts"][0]["t"], 2.5)

    def test_bar_tolerant_keys(self) -> None:
        comp, v = chart_to_component(_chart("bar", [{"label": "A", "value": 5}, {"x": "B", "y": 3}]))
        self.assertEqual(comp, "bar")
        self.assertEqual(v["bars"], [{"label": "A", "value": 5}, {"label": "B", "value": 3}])

    def test_donut_center_from_data(self) -> None:
        comp, v = chart_to_component(_chart("donut", [
            {"label": "중국", "value": 48}, {"label": "인도", "value": 19}, {"label": "기타", "value": 33}],
            unit="%"))
        self.assertEqual(comp, "donut")
        self.assertEqual(len(v["slices"]), 3)
        # 중앙 라벨/값은 최대 슬라이스에서 — default("아시아 4개국/91%") 오인 표기 방지.
        self.assertEqual(v["centerLabel"], "중국")
        self.assertEqual(v["centerValue"], "48%")

    def test_unsupported_type_returns_none(self) -> None:
        self.assertIsNone(chart_to_component(_chart("sankey", [{"a": 1}])))
        self.assertIsNone(chart_to_component(_chart("bubble", [{"label": "x", "x": 1, "y": 2, "size": 3}])))

    def test_empty_data_returns_none(self) -> None:
        self.assertIsNone(chart_to_component(_chart("candle", [])))


class TestComposedScenes(unittest.TestCase):
    def test_section_to_scene_chart_and_text(self) -> None:
        b = _bundle(
            sections=[
                {"section_id": "s1", "heading": "차트 씬", "prose": "프로즈 한 문장.", "chart_refs": ["c1"]},
                {"section_id": "s2", "heading": "텍스트 씬", "prose": "본문.", "pull_quote": "인용구", "chart_refs": []},
            ],
            charts=[{"chart_id": "c1", "type": "bar", "title": "T",
                     "data": [{"label": "A", "value": 1}],
                     "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}}],
        )
        scenes = build_composed_scenes(b)
        self.assertEqual(len(scenes), 2)
        self.assertEqual(scenes[0].kind, "chart")
        self.assertEqual(scenes[0].component, "bar")
        self.assertEqual(scenes[1].kind, "text")
        self.assertEqual(scenes[1].body, "인용구")
        # 누적 타이밍: 두번째 시작 == 첫번째 시작+길이.
        self.assertAlmostEqual(scenes[1].start_sec, scenes[0].start_sec + scenes[0].duration_sec, places=3)
        self.assertEqual(scenes[0].start_sec, 0.0)

    def test_text_scene_without_pull_quote_uses_lead_not_full_prose(self) -> None:
        # RENDER-AP: pull_quote 없는 차트-없는 섹션이 prose 전문을 body 로 박으면
        # "정적 보고서를 화면에 박은" 글자 벽이 된다(C0 위반). 첫 문장만 떠야 함.
        long_prose = "첫 문장이다. " + ("뒤따르는 본문 문장이 길게 이어진다. " * 30)
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "텍스트", "prose": long_prose, "chart_refs": []}],
            charts=[],
        )
        scenes = build_composed_scenes(b)
        self.assertEqual(len(scenes), 1)
        sc = scenes[0]
        self.assertEqual(sc.kind, "text")
        self.assertEqual(sc.body, "첫 문장이다.")
        self.assertNotIn("뒤따르는", sc.body)  # 통문단 도배가 아님
        self.assertLess(len(sc.body), len(long_prose))

    def test_text_scene_body_helper_caps_long_single_sentence(self) -> None:
        # 마침표 없는 초장문 한 문장도 cap 으로 잘려 벽이 되지 않아야 함.
        body = _text_scene_body("", "마침표가없는아주긴문장" * 40, cap=140)
        self.assertTrue(body.endswith("…"))
        self.assertLessEqual(len(body), 141)
        # pull_quote 가 있으면 그대로 우선.
        self.assertEqual(_text_scene_body("핵심 인용", "긴 본문 " * 50), "핵심 인용")

    def test_unsupported_chart_falls_back_to_text(self) -> None:
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "H", "prose": "p", "chart_refs": ["c1"]}],
            charts=[{"chart_id": "c1", "type": "sankey", "data": [{"a": 1}],
                     "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}}],
        )
        scenes = build_composed_scenes(b)
        self.assertEqual(scenes[0].kind, "text")

    def test_full_charts_split_into_individual_scenes(self) -> None:
        # full 메인 차트(bar/donut)는 차트당 1씬으로 분리.
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "패널", "prose": "p", "chart_refs": ["c1", "c2"]}],
            charts=[
                {"chart_id": "c1", "type": "bar", "title": "A", "data": [{"label": "x", "value": 3}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}},
                {"chart_id": "c2", "type": "donut", "title": "B", "data": [{"label": "y", "value": 4}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}},
            ],
        )
        scenes = build_composed_scenes(b)
        self.assertEqual([s.component for s in scenes], ["bar", "donut"])
        self.assertEqual(scenes[0].start_sec, 0.0)
        self.assertAlmostEqual(scenes[1].start_sec, scenes[0].duration_sec, places=3)

    def test_candle_is_main_lines_grouped_into_tickerboard(self) -> None:
        # candle 은 메인(상세 OHLC), line 2개 연속은 strip → 티커 보드(docs/CHART_DISPLAY_RULES.md).
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "지표", "prose": "p",
                       "chart_refs": ["c1", "c2", "c3"]}],
            charts=[
                {"chart_id": "c1", "type": "candle", "title": "엔비디아",
                 "data": [{"date": "2026-03-02", "open": 80, "high": 90, "low": 78, "close": 88},
                          {"date": "2026-03-03", "open": 88, "high": 95, "low": 85, "close": 92}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high",
                                "sources": [{"source_id": "s", "provider": "YAHOO", "code": "NVDA", "unit": "$"}]}},
                {"chart_id": "c2", "type": "line", "title": "알파벳", "data": [{"x": "1", "y": 1}, {"x": "2", "y": 2}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}},
                {"chart_id": "c3", "type": "line", "title": "MS", "data": [{"x": "1", "y": 3}, {"x": "2", "y": 5}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}},
            ],
        )
        scenes = build_composed_scenes(b)
        self.assertEqual([s.component for s in scenes], ["candle", "tickerboard"])
        # candle 메인에 출처·기간 메타.
        self.assertEqual(scenes[0].variables["source"], "YAHOO (NVDA)")
        self.assertEqual(scenes[0].variables["periodStart"], "03-02")
        # 티커 보드엔 line 2종만(candle 은 메인이라 제외).
        items = scenes[1].variables["items"]
        self.assertEqual([it["name"] for it in items], ["알파벳", "MS"])

    def test_tickerboard_dedupes_name_already_shown_as_main(self) -> None:
        # 같은 종목이 candle(메인)+line(strip) 둘 다면 보드에서 그 종목 제외(dedupe).
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "h", "prose": "p", "chart_refs": ["c1", "c2", "c3"]}],
            charts=[
                {"chart_id": "c1", "type": "candle", "title": "엔비디아",
                 "data": [{"date": "2026-03-02", "open": 80, "high": 90, "low": 78, "close": 88}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}},
                {"chart_id": "c2", "type": "line", "title": "엔비디아", "data": [{"x": "1", "y": 1}, {"x": "2", "y": 2}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}},
                {"chart_id": "c3", "type": "line", "title": "알파벳", "data": [{"x": "1", "y": 3}, {"x": "2", "y": 5}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}},
            ],
        )
        scenes = build_composed_scenes(b)
        self.assertEqual([s.component for s in scenes], ["candle", "tickerboard"])
        items = scenes[1].variables["items"]
        self.assertEqual([it["name"] for it in items], ["알파벳"])  # 엔비디아 line 은 dedupe

    def test_display_full_overrides_strip_heuristic(self) -> None:
        # display=="full" 이면 line 2연속이어도 개별 메인 씬(휴리스틱 무시).
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "h", "prose": "p", "chart_refs": ["c1", "c2"]}],
            charts=[
                {"chart_id": "c1", "type": "line", "title": "A", "display": "full",
                 "data": [{"x": "1", "y": 1}, {"x": "2", "y": 2}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}},
                {"chart_id": "c2", "type": "line", "title": "B", "display": "full",
                 "data": [{"x": "1", "y": 3}, {"x": "2", "y": 4}],
                 "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}},
            ],
        )
        scenes = build_composed_scenes(b)
        self.assertEqual([s.component for s in scenes], ["line", "line"])

    def test_unsupported_with_prerendered_svg_becomes_svg_scene(self) -> None:
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "흐름", "prose": "p", "chart_refs": ["c1"]}],
            charts=[{"chart_id": "c1", "type": "sankey", "title": "Sankey", "data": {"nodes": [], "links": []},
                     "prerendered_svg": "<svg><rect/></svg>",
                     "provenance": {"origin": "narrative_inference", "verification": "inferred", "confidence": "medium"}}],
        )
        scenes = build_composed_scenes(b)
        self.assertEqual(scenes[0].kind, "svg")
        self.assertIn("<svg>", scenes[0].svg)
        self.assertEqual(scenes[0].heading, "Sankey")

    def test_theme_accent_injected_into_chart_vars(self) -> None:
        b = ReportBundle.model_validate({
            "schema_version": 1, "bundle_kind": "report_bundle",
            "producer": {"system": "agents_reviewer", "version": "6"},
            "report": {"report_id": "r", "headline": "H",
                       "theme": {"id": "forest_sage", "tokens": {"accent": "#4A7C5B"}}},
            "sections": [{"section_id": "s1", "heading": "h", "prose": "p", "chart_refs": ["c1"]}],
            "charts": [{"chart_id": "c1", "type": "candle", "title": "T",
                        "data": [{"date": "2026-03-02", "open": 80, "high": 90, "low": 78, "close": 88}],
                        "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}}],
        })
        scenes = build_composed_scenes(b)
        self.assertEqual(scenes[0].variables.get("accent"), "#4A7C5B")

    def test_chart_takeaway_falls_back_to_heading(self) -> None:
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "섹션 제목", "prose": "p", "chart_refs": ["c1"]}],
            charts=[{"chart_id": "c1", "type": "bar", "title": "", "data": [{"label": "A", "value": 1}],
                     "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}}],
        )
        scenes = build_composed_scenes(b)
        self.assertEqual(scenes[0].variables["takeaway"], "섹션 제목")


class TestStringifyComplex(unittest.TestCase):
    def test_arrays_and_null_become_strings_scalars_unchanged(self) -> None:
        out = _stringify_complex({
            "candles": [{"d": "1", "o": 1}], "endpoint": None, "callouts": [],
            "yMin": 60, "yUnit": "$", "takeaway": "t",
        })
        self.assertEqual(out["candles"], '[{"d": "1", "o": 1}]')
        self.assertEqual(out["endpoint"], "null")
        self.assertEqual(out["callouts"], "[]")
        self.assertEqual(out["yMin"], 60)
        self.assertEqual(out["yUnit"], "$")
        self.assertEqual(out["takeaway"], "t")
        # 인코딩된 문자열은 다시 JSON 파싱 가능(컴포넌트 parseJSON 계약).
        self.assertEqual(json.loads(out["candles"]), [{"d": "1", "o": 1}])


class TestRenderHtml(unittest.TestCase):
    def test_html_contract(self) -> None:
        b = _bundle(
            sections=[
                {"section_id": "s1", "heading": "캔들", "prose": "급등했다.", "chart_refs": ["c1"]},
                {"section_id": "s2", "heading": "마무리", "prose": "끝.", "chart_refs": []},
            ],
            charts=[{"chart_id": "c1", "type": "candle", "title": "유가",
                     "data": [{"date": "2026-03-02", "open": 80, "high": 90, "low": 78, "close": 88}],
                     "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high"}}],
        )
        scenes, html = build_composition_html_from_bundle(b)
        # 차트 씬: data-composition-src + data-variable-values 임베드.
        self.assertIn('data-composition-src="../lib/charts/candle.html"', html)
        self.assertIn("data-variable-values='", html)
        # 복합값은 문자열로 인코딩 — raw 배열이 속성에 직접 노출되지 않아야(인스턴스화 사고 회피).
        self.assertNotIn('data-variable-values=\'{"candles": [', html)
        self.assertIn("candles", html)
        # 인코딩된 candles 는 JSON 문자열 값이라 내부 따옴표가 escape 되어 나타난다.
        self.assertIn('\\"o\\"', html)
        # 텍스트 씬 + 자막 큐 + 타임라인 등록.
        self.assertIn("text-scene", html)
        self.assertIn("급등했다", html)
        self.assertIn('window.__timelines["root"]', html)
        self.assertIn("data-composition-id=\"root\"", html)

    def test_render_empty_scenes_no_crash(self) -> None:
        html = render_composition_html(title="빈", scenes=[], cues=[])
        self.assertIn("data-duration=", html)
        self.assertIn("const cues = []", html)

    def test_subtitle_swap_is_seek_safe_no_tl_call(self) -> None:
        # RENDER-AP: tl.call(순수 콜백)은 seek 기반 캡처 렌더러가 미지원("tl.call is not a
        # function" → zero duration). 자막 swap 은 tl.to(proxy,{onUpdate}) (seek-safe)여야 함.
        b = _bundle(
            sections=[{"section_id": "s1", "heading": "H", "prose": "한 문장. 두 문장.",
                       "chart_refs": []}],
            charts=[],
        )
        _scenes, html = build_composition_html_from_bundle(b)
        # 코드상 실제 tl.call( 호출이 없어야 한다(주석 언급은 허용하므로 호출 형태로 검사).
        import re as _re
        code_calls = [m for m in _re.findall(r"tl\.call\(", html)]
        self.assertEqual(code_calls, [], "tl.call( 호출이 남아 있으면 캡처 렌더러에서 크래시")
        self.assertIn("onUpdate", html)
        self.assertIn("window.__timelines[\"root\"]", html)


if __name__ == "__main__":
    unittest.main()
