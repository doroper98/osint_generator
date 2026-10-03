"""발음 변환(v3.0.0 script.lint 병합, 옛 orchestrator.tts_pronounce) 단위 테스트 (TTS-AP-054 ~ 057, v0.34.10).

목적: ElevenLabs misread (한자어 숫자, 외래어 경음화, 기호 %) 의 회귀 잠금.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from script.lint import apply_pronunciation, num_to_sino_kr
from script.lint import load_pronounce_dict as load_dict   # v3.0.0 — 옛 orchestrator.tts_pronounce 병합(D-0040 작업 8)


class TestNumToSinoKr(unittest.TestCase):
    def test_zero(self) -> None:
        self.assertEqual(num_to_sino_kr(0), "영")

    def test_ones(self) -> None:
        self.assertEqual(num_to_sino_kr(1), "일")
        self.assertEqual(num_to_sino_kr(9), "구")

    def test_teens(self) -> None:
        # TTS-AP-058: 한 숫자 안 음절은 붙여 쓴다 (연음/운율 보존).
        self.assertEqual(num_to_sino_kr(10), "십")
        self.assertEqual(num_to_sino_kr(19), "십구")
        self.assertEqual(num_to_sino_kr(21), "이십일")

    def test_hundreds(self) -> None:
        self.assertEqual(num_to_sino_kr(100), "백")
        self.assertEqual(num_to_sino_kr(102), "백이")
        self.assertEqual(num_to_sino_kr(114), "백십사")
        self.assertEqual(num_to_sino_kr(120), "백이십")
        self.assertEqual(num_to_sino_kr(168), "백육십팔")  # [뱅뉵씹팔] 연음 유도
        self.assertEqual(num_to_sino_kr(999), "구백구십구")

    def test_thousands(self) -> None:
        self.assertEqual(num_to_sino_kr(1000), "천")
        self.assertEqual(num_to_sino_kr(1024), "천이십사")
        self.assertEqual(num_to_sino_kr(9876), "구천팔백칠십육")

    def test_man(self) -> None:
        self.assertEqual(num_to_sino_kr(10000), "일만")
        self.assertEqual(num_to_sino_kr(12345), "일만이천삼백사십오")


class TestApplyPronunciation(unittest.TestCase):
    def test_no_mapping_passthrough_for_pure_text(self) -> None:
        self.assertEqual(apply_pronunciation("안녕하세요"), "안녕하세요")

    def test_number_auto_to_sino(self) -> None:
        # 단순 숫자만 — sino-Korean 변환 (음절 붙임, TTS-AP-058).
        self.assertEqual(apply_pronunciation("19"), "십구")

    def test_number_then_hangul_unit_inserts_space(self) -> None:
        """TTS-AP-055 / 보충: 숫자 뭉치 뒤 한글 단위어 사이에만 공백 1칸.
        숫자 내부는 붙이고(TTS-AP-058) 단위어와의 경계만 띄운다."""
        self.assertEqual(apply_pronunciation("80달러"), "팔십 달러")
        self.assertEqual(apply_pronunciation("19일"), "십구 일")
        self.assertEqual(apply_pronunciation("5월"), "오 월")

    def test_dict_overrides_take_precedence(self) -> None:
        """TTS-AP-054: 외래어 경음화 매핑."""
        d = {"달러": "딸러", "유가": "유까"}
        self.assertEqual(apply_pronunciation("달러는 유가 지표", d), "딸러는 유까 지표")

    def test_dict_then_number_combined(self) -> None:
        """사용자 사전 적용 후 남은 숫자 자동 변환 — 둘 다 작동."""
        d = {"달러": "딸러"}
        self.assertEqual(apply_pronunciation("102달러", d), "백이 딸러")

    def test_percent_mapping(self) -> None:
        """TTS-AP-056: % 직접 사용 회피."""
        d = {"%": " 퍼센트 "}
        # 사용자 사전 적용 → 20 만 남음 → 자동 변환 + 단위 공백.
        self.assertEqual(apply_pronunciation("20%", d), "이십 퍼센트 ")

    def test_long_dict_keys_first(self) -> None:
        """더 긴 key 가 먼저 적용 — '20%' 가 '%' 보다 우선."""
        d = {"%": " 퍼센트 ", "20%": "이십 퍼센트"}
        self.assertEqual(apply_pronunciation("20%", d), "이십 퍼센트")

    def test_no_mapping_none_safe(self) -> None:
        self.assertEqual(apply_pronunciation("102달러", None), "백이 달러")

    def test_underscore_key_in_dict_filtered(self) -> None:
        """load_dict 가 _comment 같은 메타 key 를 필터 (적용 안 함)."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "pronounce.json"
            p.write_text(
                json.dumps({"_comment": "ignore me", "달러": "딸러"}, ensure_ascii=False),
                encoding="utf-8",
            )
            d = load_dict(p)
            self.assertIn("달러", d)
            self.assertNotIn("_comment", d)

    def test_load_dict_missing_is_error(self) -> None:
        # v3.0.0 — 옛 빈 dict 조용한 폴백 제거(15 P6)
        with self.assertRaises(FileNotFoundError):
            load_dict(Path("/no/such/file.json"))

    def test_repo_dict_path_from_rules(self) -> None:
        self.assertTrue(load_dict())   # rules pronounce.dict_path 의 저장소 사전


class TestPronounceBeforeSynth(unittest.TestCase):
    """v5.1.0 back_and_forth D-0121 §D(TTS-AP-067·068 구조 조치) — 합성 직전 사전은 명시 tts 에도 적용, 멱등."""

    def test_veto_fortis(self) -> None:
        from script.lint import pronounce_tts  # noqa: PLC0415

        self.assertEqual(pronounce_tts("의회는 거부권을 행사했습니다"), "의회는 거부꿘을 행사했습니다")   # TTS-AP-067

    def test_fomc_split(self) -> None:
        from script.lint import pronounce_tts  # noqa: PLC0415

        self.assertEqual(pronounce_tts("연방공개시장위원회는 동결했습니다"), "연방 공개시장 위원회는 동결했습니다")   # TTS-AP-068

    def test_noun_plus_subject_ga_not_oil_price(self) -> None:
        """TTS-AP-069 — '브렌트유 + 가(조사)' 를 油價 '유까' 로 바꾸지 않는다(긴 예외 항목이 이긴다). 油價는 그대로 '유까'."""
        from script.lint import pronounce_tts  # noqa: PLC0415

        self.assertEqual(pronounce_tts("브렌트유가 삼 퍼센트 넘게 올랐다"), "브렌트유가 삼 퍼센트 넘게 올랐다")
        self.assertEqual(pronounce_tts("정부 비축유가 줄었다"), "정부 비축유가 줄었다")
        self.assertEqual(pronounce_tts("한국 정부는 유가 상한제를"), "한국 정부는 유까 상한제를")

    def test_single_pass_no_rechain(self) -> None:
        """치환된 글자는 다시 치환하지 않는다(한 번 훑기, 최장 일치) — 값이 다른 key 를 품어도 연쇄 없음."""
        from script.lint import apply_dict  # noqa: PLC0415

        m = {"ab": "ab", "b": "X", "c": "b"}
        self.assertEqual(apply_dict("ab b c", m), "ab X b")

    def test_institution_split(self) -> None:
        """TTS-AP-070 — 긴 기관명은 의미 단위 띄어쓰기로 분절 고정(TTS-AP-068 과 같은 부류)."""
        from script.lint import pronounce_tts  # noqa: PLC0415

        self.assertEqual(pronounce_tts("미국 전략국제문제연구소는 사월 초"), "미국 전략 국제문제 연구소는 사월 초")
        self.assertEqual(pronounce_tts("국제에너지기구 공동 방출"), "국제 에너지 기구 공동 방출")

    def test_explicit_tts_path_in_plan(self) -> None:
        """script.plan.build 가 원고 명시 tts 를 사전에 통과시킨 뒤 캐시 키를 만든다(합성은 가짜)."""
        import yaml  # noqa: PLC0415
        from unittest import mock  # noqa: PLC0415

        from script import plan as plan_mod  # noqa: PLC0415
        from script.tts.cache import cache_key  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            proj = Path(d)
            (proj / "script.yaml").write_text(yaml.safe_dump({
                "title": "t", "subtitle": "s", "date": "2026.09.30", "scenes": [{"id": "a", "sentences": [
                    {"text": "연방공개시장위원회가 거부권을 말했습니다.", "tts": "연방공개시장위원회가 거부권을 말했습니다.", "date": "2026.09.30"}]}]},
                allow_unicode=True), encoding="utf-8")
            seen: list[str] = []
            with mock.patch.object(plan_mod, "lint", return_value=mock.Mock(errors=[], warnings=[])), \
                 mock.patch.object(plan_mod, "load_claims_for", return_value=None), \
                 mock.patch.object(plan_mod.edge, "synth_all", side_effect=lambda jobs, voice=None: seen.extend(t for t, _ in jobs)), \
                 mock.patch.object(plan_mod, "trim_to_npy", return_value=(proj / "x.npy", 1.0, 0.0)):
                pl = plan_mod.build(proj, "edge")
        want = "연방 공개시장 위원회가 거부꿘을 말했습니다."
        self.assertEqual(seen, [want])
        self.assertEqual(pl.sentences[0].tts, want)
        self.assertIn(cache_key(want, None, None), pl.sentences[0].mp3)

    def test_idempotent_whole_dict(self) -> None:
        from script.lint import pronounce_tts  # noqa: PLC0415

        d = load_dict()
        for k in d:
            once = pronounce_tts(k, d)
            self.assertEqual(pronounce_tts(once, d), once, k)
        self.assertEqual(pronounce_tts("사전에  없는   문장", d), "사전에  없는   문장")   # 치환 없으면 그대로(캐시 키 불변)


if __name__ == "__main__":
    unittest.main()


class TestSpokenRisks(unittest.TestCase):
    """v5.3.0 TTS-AP-071~073 — 사전 적용 뒤 합성 문자열 경고(rules tts_risk.spoken_patterns)·사전 항목."""

    def test_dictionary_fixes(self) -> None:
        from script.lint import pronounce_tts  # noqa: PLC0415

        self.assertEqual(pronounce_tts("에이피통신에 따르면"), "에이피 통신에 따르면")   # TTS-AP-071
        self.assertEqual(pronounce_tts("AP통신은"), "에이피 통신은")
        self.assertEqual(pronounce_tts("모스크바타임스는"), "모스크바 타임스는")   # TTS-AP-072
        self.assertEqual(pronounce_tts("키이우포스트는"), "키이우 포스트는")

    def test_spoken_patterns(self) -> None:
        from script.lint import pronounce_tts, spoken_risks  # noqa: PLC0415

        kinds = lambda t: [k for k, _, _ in spoken_risks(t)]  # noqa: E731
        self.assertEqual(kinds("비비씨뉴스는"), ["glued_acronym"])
        self.assertEqual(kinds("가디언포스트는"), ["glued_media_name"])
        self.assertEqual(kinds("폴란드 리투아니아 국경 구간"), ["bare_parallel_names"])   # TTS-AP-073
        self.assertEqual(kinds("폴란드와 리투아니아 사이"), [])
        self.assertEqual(kinds(pronounce_tts("에이피통신과 모스크바타임스")), [])   # 사전이 고친 것은 경고하지 않는다

    def test_lint_reports_spoken(self) -> None:
        from script.lint import lint  # noqa: PLC0415
        from script.schema import Script  # noqa: PLC0415

        s = Script.model_validate({"schema_version": 1, "title": "t", "subtitle": "s", "date": "2026.10.02", "scenes": [{"id": "a", "sentences": [
            {"date": "2026.10.02", "text": "폴란드-리투아니아 국경입니다.", "tts": "폴란드 리투아니아 국경입니다.", "emphasis": [], "sources": []}]}]})
        self.assertIn("tts-spoken:bare_parallel_names", [i.kind for i in lint(s, check_sources=False).issues])
