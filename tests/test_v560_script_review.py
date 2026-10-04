"""v5.6.0 사용자 시청 지적 12건(2026-10-04, kaliningrad-suwalki 콘티 판) 규약 승격 — 회귀 테스트.

TTS-AP-074~081, RENDER-AP-008·009, LLM-AP-015.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from rules import load_rules
from script.lint import ends_present, lint, letter_spacing, load_pronounce_dict, pronounce_tts, spoken_risks
from script.schema import Script

REPO = Path(__file__).resolve().parent.parent


def _script(rows: list[tuple[str, str, str | None]], date: str = "2026.10.04") -> Script:
    return Script.model_validate({"schema_version": 1, "title": "t", "subtitle": "s", "date": date, "scenes": [
        {"id": "a", "sentences": [dict({"date": d, "text": t, "emphasis": [], "sources": ["clm_0001"]}, **({"tts": s} if s else {}))
                                  for d, t, s in rows]}]})


def _kinds(sc: Script, noted: set[str] | None = None) -> list[str]:
    return [i.kind for i in lint(sc, {"clm_0001": "unverified"}, noted=noted).issues]


class PronounceTest(unittest.TestCase):
    def test_letter_names_are_spaced_only_for_registered(self) -> None:
        """TTS-AP-075 — 붙은 글자 이름 연속(등재 약어·사전 값)만 띄운다. 일반 낱말('비디오')은 그대로."""
        self.assertEqual(pronounce_tts("에이에프피 통신은"), "에이 에프 피 통신은")
        self.assertEqual(pronounce_tts("씨에스아이에스 자료"), "씨 에스 아이 에스 자료")
        self.assertEqual(pronounce_tts("비디오와 오디오를 봤다"), "비디오와 오디오를 봤다")
        self.assertIn("에이에프피", letter_spacing(load_pronounce_dict()))

    def test_same_month_dictionary(self) -> None:
        """TTS-AP-080 — '같은 달'은 발음에서 붙인다(자막은 맞춤법대로)."""
        self.assertEqual(pronounce_tts("같은 달 수바우키에서는"), "같은달 수바우키에서는")

    def test_spoken_patterns(self) -> None:
        """TTS-AP-074·076·077·078·079·081 — 사전 적용 뒤 합성 문자열 경고."""
        cases = {"particle_merge_seo": "러시아가 나토에 서면 메시지를", "modifier_name_group": "나머지 나토 회원국과",
                 "dest_noun_chain": "칼리닌그라드행 러시아 통과 열차의", "short_name_after_modifier": "리투아니아 인근 고자, 폴란드",
                 "name_org_title": "앨리슨 하트 나토 대변인도", "op_name_noun_run": "발트 센트리 해저 기반시설을"}
        for kind, s in cases.items():
            with self.subTest(kind=kind):
                self.assertIn(kind, [k for k, _, _ in spoken_risks(s)])
        fixed = ["서면 메시지를 나토에", "나토의 다른 회원국과", "칼리닌그라드로 가는 러시아 열차에서", "리투아니아와 가까운 고자 훈련장,",
                 "나토의 앨리슨 하트 대변인도", "발트 센트리 활동으로 발트해의 해저 기반시설을"]
        for s in fixed:
            self.assertEqual(spoken_risks(s), [], s)


class ScriptRulesTest(unittest.TestCase):
    def test_acronym_reading(self) -> None:
        """사용자 결정 2026-10-04 — CSIS 는 글자 이름 + 국문 명칭, AFP 는 글자 이름."""
        bad = _script([("2026", "CSIS 자료에 따르면 사거리는 길다.", "씨에스아이에스 자료에 따르면 사거리는 길다.")])
        self.assertIn("tts-acronym", _kinds(bad))
        ok = _script([("2026", "CSIS 자료에 따르면 사거리는 길다.", "씨 에스 아이 에스, 전략국제문제연구소 자료에 따르면 사거리는 길다.")])
        self.assertNotIn("tts-acronym", _kinds(ok))
        self.assertIn("tts-acronym", _kinds(_script([("2026", "AFP통신이 보도했습니다.", None)])))

    def test_reference_not_in_narration(self) -> None:
        sc = _script([("2026", "위키백과에 따르면 이 도시는 오래됐습니다.", None)])
        self.assertIn("reference-in-narration", _kinds(sc))

    def test_tense_present_for_past_dates(self) -> None:
        self.assertTrue(ends_present("이 땅의 옛 이름은 쾨니히스베르크입니다."))
        self.assertFalse(ends_present("소련군이 장악했습니다."))
        self.assertFalse(ends_present("1946년까지 쾨니히스베르크로 불렸던 칼리닌그라드."))
        self.assertIn("tense-present", _kinds(_script([("1255", "튜턴 기사단이 세운 도시입니다.", "튜턴 기사단이 세운 도시입니다.")])))
        self.assertNotIn("tense-present", _kinds(_script([("1255", "튜턴 기사단이 세운 도시였습니다.", None)])))

    def test_screen_note_satisfies_attribution(self) -> None:
        sc = _script([("2026", "이 땅은 러시아의 역외 영토입니다.", None)])
        self.assertIn("attribution", _kinds(sc))
        self.assertNotIn("attribution", _kinds(sc, noted={"clm_0001"}))

    def test_rules_reach_prompt(self) -> None:
        from workers.prompt_loader import load_prompt  # noqa: PLC0415

        p = load_prompt("script", load_rules())
        self.assertIn("앵커 브리핑", p)
        self.assertIn("과거형", p)
        self.assertIn("위키백과에 따르면", p)          # 금지 문구로 안내
        self.assertIn("전략국제문제연구소", p)          # 약어 등재(tts_rules 덤프)


class SourceNoteTest(unittest.TestCase):
    def test_notes_from_reference_sources(self) -> None:
        from engine.source_note import source_notes  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "intake").mkdir()
            (p / "script.yaml").write_text(yaml.safe_dump({"scenes": [{"id": "a", "sentences": [
                {"text": "x", "sources": ["clm_1"]}, {"text": "y", "sources": ["clm_2"]}]}]}, allow_unicode=True), encoding="utf-8")
            (p / "intake" / "claims.json").write_text(json.dumps({"claims": [
                {"claim_id": "clm_1", "source_ids": ["s1"]}, {"claim_id": "clm_2", "source_ids": ["s2"]}]}), encoding="utf-8")
            (p / "intake" / "sources.json").write_text(json.dumps({"sources": [
                {"id": "s1", "publisher": "Wikipedia (Kaliningrad)", "url": "https://en.wikipedia.org/wiki/Suwa%C5%82ki_Agreement"},
                {"id": "s2", "publisher": "Reuters", "url": "https://reuters.com/x"}]}), encoding="utf-8")
            n = source_notes(p)
        self.assertEqual(n, {"a_0": "출처 · en.wikipedia.org/wiki/Suwałki_Agreement"})   # 참조 출처만, URL 디코드


class LabelCollisionTest(unittest.TestCase):
    def test_centered_marker_box_matches_drawing(self) -> None:
        """RENDER-AP-009 — side top 라벨 검사 상자는 점 가운데 정렬(그린 자리와 같다)."""
        import cairo  # noqa: PLC0415

        from engine.layers.markers import marker_box  # noqa: PLC0415

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = {"label": "발트해", "sub": "2025년 1월~ 발트 센트리 · 해저 기반시설 보호", "side": "top"}
        x0, _, x1, _ = marker_box(ctx, e, 300.0, 200.0, with_sub=True)
        self.assertAlmostEqual((x0 + x1) / 2, 300.0, delta=1.0)
        self.assertLess(x0, 300.0 - 50)

    def test_registered_hard(self) -> None:
        from engine import checks  # noqa: PLC0415

        self.assertIn("label_collision", checks.HARD)

    def test_line_label_vs_marker_text_only(self) -> None:
        """RENDER-AP-012 — 경로·봉쇄선 이름표는 마커 글자 영역과 대조(점·맥동 고리 제외 — 호르무즈 '봉쇄' 골든 합격 배치)."""
        from engine.checks import _overlap_px, _text_part  # noqa: PLC0415

        mk = {"type": "marker", "side": "right"}
        box = (100.0, 84.0, 260.0, 126.0)                    # 점 (114, 100) 오른쪽 라벨
        near_dot = (60.0, 90.0, 118.0, 104.0)                # 선 옆 이름표가 점 고리에만 닿음
        on_text = (150.0, 90.0, 230.0, 104.0)                # 이름표가 마커 글자 위
        self.assertLessEqual(_overlap_px(_text_part(mk, box), near_dot), 0)
        self.assertGreater(_overlap_px(_text_part(mk, box), on_text), 0)

    def test_timeline_span_hard(self) -> None:
        """RENDER-AP-011 — 월 축 타임라인 패널은 max_span_months 이하."""
        from engine import checks  # noqa: PLC0415

        self.assertIn("timeline_span", checks.HARD)
        self.assertEqual(load_rules().panels.timeline.max_span_months, 36)


class BadgeHoldTest(unittest.TestCase):
    def test_hold_rule_on(self) -> None:
        """RENDER-AP-008 — 뱃지는 카드 회피 이동을 수명 내내 고정(아일랜드 아래)."""
        from engine.reserved import RES  # noqa: PLC0415

        self.assertTrue(RES.badge_hold)
        self.assertEqual(RES.hold_directions[0], "down")

    def test_place_badge_uses_hold(self) -> None:
        import cairo  # noqa: PLC0415

        from engine.layers.badges import place_badge  # noqa: PLC0415

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = {"type": "badge", "kind": "flag", "flag": "ru", "R": 20, "t0": 0.0, "t1": 5.0, "label": "", "push_hold": (0.0, 37.0)}
        dx, dy, ka = place_badge(ctx, e, 400.0, 200.0, 2.0, [])
        self.assertEqual((dy, ka), (37.0, 1.0))


if __name__ == "__main__":
    unittest.main()
