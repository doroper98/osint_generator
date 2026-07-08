"""report_bundle 수신 모델 + research_dossier 어댑터 테스트 (외부 연동, 계약 v1).

순수 레이어(모델 검증 + 변환)만 다룬다 — 디스크/상태전이를 포함하는 import-bundle
end-to-end seam 은 실제 CLI 실행으로 검증한다(프로젝트의 "실물 검증" 방침).
"""

from __future__ import annotations

import copy
import unittest

from orchestrator.bundle_io import bundle_to_research_dossier
from schemas.models import CLAIM_STATUS_LABELS, ReportBundle


def _valid_bundle() -> dict:
    """계약 v1 예시(agents_reviewer 제공)를 축약한 schema-valid bundle."""
    return {
        "schema_version": 1,
        "bundle_kind": "report_bundle",
        "generated_at": "2026-05-25T09:00:00+09:00",
        "producer": {"system": "agents_reviewer", "version": "v5.4.9", "mode": "deep"},
        "report": {
            "report_id": "analysis_20260525_090000",
            "headline": "삼성전자, HBM4 양산 전환 가속",
            "deck": "메모리 사이클 반등과 맞물린 평택 설비 재배치.",
            "closing": "수율 공시가 다음 확인점이다.",
            "html_url": "https://example.github.io/a.html",
            "theme": {
                "id": "editorial_cream",
                "tokens": {"bg": "#F2EBDB", "accent": "#B05A38"},
                "fonts": {"serif": "Noto Serif KR"},
            },
        },
        "sections": [
            {
                "section_id": "s1",
                "heading": "변곡점",
                "kicker": "FACT",
                "prose": "최근 3개월 주가는 71,800원에서 74,100원으로 올랐다.",
                "pull_quote": "수요가 공급을 추월했다.",
                "chart_refs": ["ch-1"],
                "map_ref": None,
                "image_refs": [],
                "claim_refs": ["C-1"],
            }
        ],
        "charts": [
            {
                "chart_id": "ch-1",
                "type": "candle",
                "title": "삼성전자 (최근 3개월)",
                "data": [
                    {"date": "2026-03-02", "open": 71800, "high": 73000, "low": 71500, "close": 72600}
                ],
                "note": "사건일 전후 +-2주",
                "provenance": {
                    "origin": "measured",
                    "verification": "confirmed",
                    "confidence": "high",
                    "sources": [
                        {"source_id": "mkt-1", "provider": "KRX", "code": "005930", "unit": "원"}
                    ],
                },
                "prerendered_svg": None,
            }
        ],
        "map": {
            "id": "map-1",
            "center": [127.05, 37.0],
            "zoom": 6.5,
            "markers": [{"id": "mk-1", "name": "평택", "lng": 127.11, "lat": 37.0, "highlight": True}],
            "arcs": [],
            "legend": [{"label": "신규 라인", "kind": "marker", "highlight": True}],
            "provenance": {"origin": "narrative_inference", "verification": "inferred", "confidence": "medium"},
            "prerendered_svg": None,
        },
        "claims": [
            {
                "claim_id": "C-1",
                "statement": "최근 3개월 주가가 약 3.2% 상승했다.",
                "status": "confirmed",
                "confidence": "high",
                "cross_checked": True,
                "evidence": [
                    {
                        "source_id": "mkt-1",
                        "quote_or_data": "KRX 005930 종가 72,600→74,100",
                        "locator": "ch-1 data",
                        "reliability": "primary",
                        "stance": "supports",
                    }
                ],
                "chart_refs": ["ch-1"],
            },
            {
                "claim_id": "C-2",
                "statement": "HBM4 전환은 2026 하반기 본격화될 것으로 추정된다.",
                "status": "inferred",
                "confidence": "medium",
                "cross_checked": True,
                "evidence": [],
                "chart_refs": [],
            },
        ],
        "signals": [
            {
                "signal": "HBM4 수율 공시",
                "description": "분기 실적 발표 시 수율 언급 여부",
                "indicates": "전환 본격화",
                "deadline": "2026-09-30",
                "verification": "unverified",
            }
        ],
        "contradictions": [
            {"side_a": "수요 견조", "side_b": "재고 누적", "evidence": "채널 데이터 지연", "resolution": "사이클 분기"}
        ],
        "sources": [
            {"source_id": "mkt-1", "url": "", "publisher": "KRX", "title": "시세", "fetched_at": "2026-05-25"}
        ],
        "confidence": {"score": 0.78, "summary": "KRX 일치, 전망 구간은 추정."},
    }


class TestReportBundleModel(unittest.TestCase):
    def test_valid_bundle_parses(self) -> None:
        bundle = ReportBundle.model_validate(_valid_bundle())
        self.assertEqual(bundle.schema_version, 1)
        self.assertEqual(bundle.producer.system, "agents_reviewer")
        self.assertEqual(len(bundle.claims), 2)
        # use_enum_values → status 는 문자열로 저장.
        self.assertEqual(bundle.claims[0].status, "confirmed")
        self.assertEqual(bundle.charts[0].provenance.verification, "confirmed")

    def test_unknown_top_level_field_ignored(self) -> None:
        # 관대한 수신자(tolerant reader): 모르는 top-level 필드는 무시(거부 안 함) →
        # 진화하는 보고서(새 블록 추가)에 안 깨진다. extra="ignore".
        raw = _valid_bundle()
        raw["some_future_block"] = {"foo": 1}
        bundle = ReportBundle.model_validate(raw)  # 안 깨짐
        self.assertEqual(bundle.report.headline, raw["report"]["headline"])
        self.assertFalse(hasattr(bundle, "some_future_block"))

    def test_unknown_section_field_ignored(self) -> None:
        # 섹션 구조 진화도 수용 — 섹션에 모르는 필드가 있어도 무시.
        raw = _valid_bundle()
        raw["sections"][0]["new_section_field"] = "x"
        bundle = ReportBundle.model_validate(raw)
        self.assertEqual(bundle.sections[0].section_id, "s1")

    def test_timeline_accepted(self) -> None:
        # v5.5.2 가 추가한 timeline 블록 수용(보관).
        raw = _valid_bundle()
        raw["timeline"] = {
            "heading": "연표",
            "points": [{"date": "2026-05-24", "label": "합의", "phase": "present", "note": ""}],
        }
        bundle = ReportBundle.model_validate(raw)
        self.assertIsNotNone(bundle.timeline)
        self.assertEqual(len(bundle.timeline.points), 1)

    def test_images_accepted_and_refs_resolved(self) -> None:
        # IMAGE_BUNDLE_CONTRACT: images[] + section.image_refs resolve (v0.42.0).
        raw = _valid_bundle()
        raw["images"] = [{
            "image_id": "img-1", "url": "https://x/y.jpg", "caption": "현장",
            "credit": "제공", "rights_status": "cleared",
        }]
        raw["sections"][0]["image_refs"] = ["img-1"]
        bundle = ReportBundle.model_validate(raw)
        self.assertEqual(bundle.images[0].image_id, "img-1")
        self.assertEqual(bundle.images[0].rights_status, "cleared")

    def test_unresolved_image_ref_rejected(self) -> None:
        raw = _valid_bundle()
        raw["sections"][0]["image_refs"] = ["img-404"]
        with self.assertRaises(Exception):
            ReportBundle.model_validate(raw)

    def test_duplicate_image_id_rejected(self) -> None:
        raw = _valid_bundle()
        img = {"image_id": "img-1", "url": "https://x/y.jpg", "rights_status": "cleared"}
        raw["images"] = [img, dict(img)]
        with self.assertRaises(Exception):
            ReportBundle.model_validate(raw)

    def test_unknown_verification_value_rejected(self) -> None:
        raw = _valid_bundle()
        raw["claims"][0]["status"] = "totally_made_up"
        with self.assertRaises(ValueError):
            ReportBundle.model_validate(raw)

    def test_dangling_chart_ref_rejected(self) -> None:
        raw = _valid_bundle()
        raw["sections"][0]["chart_refs"] = ["ch-does-not-exist"]
        with self.assertRaises(ValueError):
            ReportBundle.model_validate(raw)

    def test_dangling_claim_ref_rejected(self) -> None:
        raw = _valid_bundle()
        raw["sections"][0]["claim_refs"] = ["C-nope"]
        with self.assertRaises(ValueError):
            ReportBundle.model_validate(raw)

    def test_duplicate_chart_id_rejected(self) -> None:
        raw = _valid_bundle()
        dup = copy.deepcopy(raw["charts"][0])
        raw["charts"].append(dup)
        with self.assertRaises(ValueError):
            ReportBundle.model_validate(raw)

    def test_chart_data_shape_not_revalidated(self) -> None:
        # data 모양 SSOT 는 agents_reviewer schemas.py (계약 §9) — 우리는 통과시킨다.
        raw = _valid_bundle()
        raw["charts"][0]["data"] = {"arbitrary": ["shape", 1, 2]}
        bundle = ReportBundle.model_validate(raw)
        self.assertEqual(bundle.charts[0].data, {"arbitrary": ["shape", 1, 2]})

    def test_map_ref_resolves_to_map_id(self) -> None:
        raw = _valid_bundle()
        raw["sections"][0]["map_ref"] = "map-1"  # map.id 와 일치 → resolve
        bundle = ReportBundle.model_validate(raw)
        self.assertEqual(bundle.sections[0].map_ref, "map-1")
        self.assertEqual(bundle.map.id, "map-1")

    def test_dangling_map_ref_rejected(self) -> None:
        raw = _valid_bundle()
        raw["sections"][0]["map_ref"] = "map-nope"
        with self.assertRaises(ValueError):
            ReportBundle.model_validate(raw)

    def test_minimal_bundle_optionals_absent(self) -> None:
        # map/signals/contradictions/confidence 통째 absent 도 통과(지리 없는 보고서).
        raw = {
            "schema_version": 1,
            "producer": {"system": "agents_reviewer", "version": "v5.4.9"},
            "report": {"report_id": "r1", "headline": "제목"},
            "claims": [{"claim_id": "C-1", "statement": "주장", "status": "claim"}],
        }
        bundle = ReportBundle.model_validate(raw)
        self.assertIsNone(bundle.map)
        self.assertEqual(bundle.sections, [])
        self.assertEqual(bundle.claims[0].status, "claim")


class TestBundleToResearchDossier(unittest.TestCase):
    def test_basic_mapping(self) -> None:
        bundle = ReportBundle.model_validate(_valid_bundle())
        dossier = bundle_to_research_dossier(bundle, "samsung-hbm4")

        self.assertEqual(dossier.project_id, "samsung-hbm4")
        self.assertEqual(dossier.topic, "삼성전자, HBM4 양산 전환 가속")
        self.assertIn("평택 설비 재배치", dossier.summary)
        self.assertIn("수율 공시가 다음 확인점", dossier.summary)  # closing 합쳐짐
        self.assertEqual(len(dossier.claims), 2)

    def test_claim_status_and_label_propagation(self) -> None:
        bundle = ReportBundle.model_validate(_valid_bundle())
        dossier = bundle_to_research_dossier(bundle, "p1")

        c1 = dossier.claims[0]
        self.assertEqual(c1.claim_id, "C-1")
        self.assertEqual(c1.status, "confirmed")
        self.assertTrue(c1.cross_checked)
        self.assertEqual(c1.confidence, "high")
        # 라벨 척추: status → display_label.
        self.assertEqual(c1.display_label, CLAIM_STATUS_LABELS["confirmed"])
        self.assertEqual(c1.display_label, "<확인>")
        self.assertEqual(dossier.claims[1].display_label, "<추론>")

    def test_evidence_field_rename(self) -> None:
        bundle = ReportBundle.model_validate(_valid_bundle())
        dossier = bundle_to_research_dossier(bundle, "p1")

        ev = dossier.claims[0].evidence[0]
        self.assertEqual(ev.source_id, "mkt-1")
        self.assertEqual(ev.quote, "KRX 005930 종가 72,600→74,100")  # quote_or_data → quote
        self.assertEqual(ev.locator, "ch-1 data")
        self.assertEqual(ev.stance, "supports")

    def test_empty_evidence_ok(self) -> None:
        bundle = ReportBundle.model_validate(_valid_bundle())
        dossier = bundle_to_research_dossier(bundle, "p1")
        self.assertEqual(dossier.claims[1].evidence, [])

    def test_signals_become_open_questions(self) -> None:
        bundle = ReportBundle.model_validate(_valid_bundle())
        dossier = bundle_to_research_dossier(bundle, "p1")
        self.assertEqual(len(dossier.open_questions), 1)
        self.assertIn("HBM4 수율 공시", dossier.open_questions[0])

    def test_dossier_roundtrip_serializable(self) -> None:
        bundle = ReportBundle.model_validate(_valid_bundle())
        dossier = bundle_to_research_dossier(bundle, "p1")
        # research_io 가 영속화하는 직렬화 경로가 깨지지 않는지.
        from schemas.models import ResearchDossier

        reloaded = ResearchDossier.model_validate_json(dossier.model_dump_json())
        self.assertEqual(reloaded.topic, dossier.topic)
        self.assertEqual(len(reloaded.claims), 2)


def _v55_bundle() -> dict:
    """v5.5.0 real emit 모양: claims=[], 라벨 척추는 charts/map provenance + contradictions."""
    return {
        "schema_version": 1,
        "producer": {"system": "agents_reviewer", "version": "v5.5.0", "mode": "deep"},
        "report": {"report_id": "r1", "headline": "엔 캐리가 풀린다",
                   "deck": "BOJ 인상 이후 변동성.", "closing": "다음 확인점은 표결 분포."},
        "sections": [
            {"section_id": "s1", "heading": "새 지형", "kicker": "1",
             "prose": "VKOSPI 가 평년의 두 배 수준에 자리 잡았다.", "chart_refs": ["ch-1"]},
        ],
        "charts": [
            {"chart_id": "ch-1", "type": "line", "title": "VKOSPI 주요 지점",
             "data": [{"x": "2026-03-04", "y": 80.37, "event": "risk-off"}],
             "provenance": {"origin": "measured", "verification": "confirmed", "confidence": "high",
                            "sources": [{"source_id": "mkt-1", "provider": "YAHOO", "code": "^VKOSPI"}]}},
            {"chart_id": "ch-2", "type": "bubble", "title": "시나리오 확률 × 영향",
             "data": [{"label": "점진", "x": 0.45, "y": 35, "size": 35}],
             "provenance": {"origin": "narrative_inference", "verification": "inferred", "confidence": "medium", "sources": []}},
        ],
        "map": {
            "id": "map-1", "center": [48.0, 32.0], "zoom": 4.2,
            "markers": [{"id": "isfahan", "name": "이스파한", "lng": 51.7, "lat": 32.7, "highlight": True}],
            "arcs": [{"from_id": "telaviv", "to_id": "isfahan", "highlight": True, "label": "공격축"}],
            "legend": [{"label": "공습 축", "kind": "line", "highlight": True}],
            "provenance": {"origin": "narrative_inference", "verification": "inferred", "confidence": "medium"},
        },
        "claims": [],
        "signals": [{"signal": "BOJ 표결", "description": "인상 위원 수", "verification": "unverified"}],
        "contradictions": [
            {"side_a": "안전판이 sidecar 를 막는다", "side_b": "vega 압력은 못 막는다",
             "evidence": "2024-08 전례", "resolution": "side_b 채택"},
        ],
        "sources": [{"source_id": "mkt-1", "publisher": "YAHOO", "title": ""}],
        "confidence": {"score": 0.72, "summary": "출처 양호."},
    }


class TestV55EmptyClaimsSynthesis(unittest.TestCase):
    def test_map_arc_highlight_accepted(self) -> None:
        # 실물 emit 의 map arc highlight 필드(§11 갭 수정) 수용.
        bundle = ReportBundle.model_validate(_v55_bundle())
        self.assertTrue(bundle.map.arcs[0].highlight)

    def test_claims_synthesized_from_charts(self) -> None:
        bundle = ReportBundle.model_validate(_v55_bundle())
        dossier = bundle_to_research_dossier(bundle, "p1")
        by_id = {c.claim_id: c for c in dossier.claims}
        # 차트 provenance.verification → claim status → 라벨 척추.
        self.assertEqual(by_id["ch-1"].status, "confirmed")
        self.assertEqual(by_id["ch-1"].display_label, "<확인>")
        self.assertEqual(by_id["ch-2"].status, "inferred")
        self.assertEqual(by_id["ch-2"].display_label, "<추론>")
        # 시장데이터 차트는 provenance.sources → evidence.
        self.assertTrue(len(by_id["ch-1"].evidence) >= 1)

    def test_map_and_contradictions_become_claims(self) -> None:
        bundle = ReportBundle.model_validate(_v55_bundle())
        dossier = bundle_to_research_dossier(bundle, "p1")
        by_id = {c.claim_id: c for c in dossier.claims}
        self.assertIn("map-1", by_id)
        self.assertEqual(by_id["map-1"].display_label, "<추론>")
        # 모순은 봉합하지 않고 disputed(<반박됨>) 로.
        self.assertEqual(by_id["contradiction_1"].status, "disputed")
        self.assertEqual(by_id["contradiction_1"].display_label, "<반박됨>")

    def test_narrative_summary_carries_prose(self) -> None:
        bundle = ReportBundle.model_validate(_v55_bundle())
        dossier = bundle_to_research_dossier(bundle, "p1")
        # deck + 섹션 prose + closing 이 summary 에 실린다(ScriptWorker 원천).
        self.assertIn("VKOSPI 가 평년의 두 배", dossier.summary)
        self.assertIn("다음 확인점", dossier.summary)


class TestBundleToSourceRegistry(unittest.TestCase):
    def test_collects_provenance_and_toplevel_sources(self) -> None:
        from orchestrator.bundle_io import bundle_to_source_registry

        raw = _v55_bundle()
        # 차트 전용 데이터 출처(top-level 에 없음)를 하나 추가.
        raw["charts"][1]["provenance"]["sources"] = [
            {"source_id": "mkt-9", "provider": "KRX", "code": "005930"}
        ]
        raw["sources"] = [
            {"source_id": "src-1", "publisher": "reuters.com", "title": ""},
        ]
        bundle = ReportBundle.model_validate(raw)
        reg = bundle_to_source_registry(bundle, "p1")
        by_id = {s.source_id: s for s in reg.sources}
        # 차트 provenance 출처 (데이터 시리즈).
        self.assertEqual(by_id["mkt-1"].platform, "YAHOO")
        self.assertEqual(by_id["mkt-1"].source_type, "data_series")
        self.assertEqual(by_id["mkt-9"].platform, "KRX")
        # top-level 보고서 인용 출처.
        self.assertEqual(by_id["src-1"].platform, "reuters.com")
        self.assertEqual(by_id["src-1"].source_type, "report_cited")


if __name__ == "__main__":
    unittest.main()
