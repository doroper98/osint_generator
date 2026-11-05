"""사용자 의견 UF-163~173(us_midterms_2026) 재발 방지 장치 (v7.4.0, back_and_forth D-0309 · C12-2).

각 장치가 실제로 실패를 내는지 재현한다 — 린트(원고), 엔진 검사(화면), 규칙 로드 검증(수치 상한).
UF-163 선거 제도 설명 · UF-164 정당 상징 미디어 · UF-167 주 이름 모드 · UF-168 작은 글자 halo 상한 · UF-169 area 외곽선 상한 ·
UF-171 매체명 라틴 표기 · UF-172 '개표 중' 금지 · UF-173 승자 발표 전 = '유력'. UF-165·170 은 기존 테스트(권리 예외·bars)에 원장 연결.
"""

from __future__ import annotations

import types
import unittest

import yaml
from pydantic import ValidationError

from engine import checks
from rules import load_rules
from rules import RULES_PATH
from schemas.rules_models import AreaRules, LabelRules
from script.lint import vocab_issues
from script.schema import Script

ELECTION = "2026년 중간선거 결과입니다."
BASICS = "하원의원 임기는 2년이라 435석을 모두 다시 뽑습니다."


def _sc(*texts: str, tts: "dict[int, str] | None" = None) -> Script:
    tts = tts or {}
    return Script.model_validate(dict(title="t", subtitle="s", date="2026.11.05", scenes=[dict(
        id="a", sentences=[dict(date="2026.11.05", text=t, **({"tts": tts[i]} if i in tts else {})) for i, t in enumerate(texts)])]))


def _kinds(*texts: str, tts: "dict[int, str] | None" = None) -> set[str]:
    return {i.kind for i in vocab_issues(_sc(*texts, tts=tts))}


class ElectionBasicsTest(unittest.TestCase):
    """UF-163 "중간선거 의의 … 왜 하는지, 뭘 뽑는지" — 선거 영상 앞 35 % 안에 임기·선출 설명 문장."""

    def test_missing_basics_fails(self) -> None:
        self.assertIn("election-basics-missing", _kinds(ELECTION, *["결과를 봅니다."] * 6, BASICS))

    def test_basics_early_passes(self) -> None:
        self.assertNotIn("election-basics-missing", _kinds(ELECTION, BASICS, *["결과를 봅니다."] * 6))

    def test_non_election_not_checked(self) -> None:
        self.assertNotIn("election-basics-missing", _kinds("유가가 올랐습니다.", "정유소가 멈췄습니다."))


class CountingWordingTest(unittest.TestCase):
    """UF-172 "개표중이라던지 하는 문구는 빼야 해" · UF-173 "미확정이 아니고 사실상 유력"."""

    def test_counting_in_text_or_tts_fails(self) -> None:
        self.assertIn("counting-wording", _kinds(ELECTION, BASICS, "두 곳은 아직 개표 중입니다."))
        self.assertIn("counting-wording", _kinds(ELECTION, BASICS, "두 곳은 미확정입니다."))
        self.assertIn("counting-wording", _kinds(ELECTION, BASICS, "두 곳은 남았습니다.", tts={2: "두 곳은 개표가 끝나야 정해집니다."}))

    def test_likely_passes(self) -> None:
        self.assertNotIn("counting-wording", _kinds(ELECTION, BASICS, "남은 두 곳도 민주당 후보가 사실상 유력합니다."))

    def test_label_is_likely_everywhere(self) -> None:
        r = load_rules()
        self.assertEqual(r.script_vocab.counting_label, "유력")
        self.assertEqual(r.bars.counting_note, r.script_vocab.counting_label)
        self.assertNotIn(r.bars.counting_note, r.script_vocab.counting_banned)

    def test_screen_wording_counting(self) -> None:
        ev = [dict(type="marker", t0=1.0, t1=5.0, label="미시시피", sub="개표 중 — 표 차 수십 표")]
        self.assertTrue(checks.screen_wording(ev, election=True))
        self.assertEqual(checks.screen_wording(ev, election=False), [])
        ok = [dict(type="marker", t0=1.0, t1=5.0, label="미시시피", sub="콜롬 유력 · 표 차 약 1,100표")]
        self.assertEqual(checks.screen_wording(ok, election=True), [])


class OutletDisplayTest(unittest.TestCase):
    """UF-171 "방송국 같은 명칭의 자막에는 엔비씨 가 아니라 NBC 로" — 자막·화면은 라틴, 발음(tts)은 음차."""

    def test_transliteration_in_text_fails(self) -> None:
        self.assertIn("outlet-display", _kinds("엔비씨 집계로는 민주당이 이겼습니다."))

    def test_latin_text_with_hangul_tts_passes(self) -> None:
        self.assertNotIn("outlet-display", _kinds("NBC 집계로는 민주당이 이겼습니다.", tts={0: "엔비씨 집계로는 민주당이 이겼습니다."}))

    def test_screen_event_strings(self) -> None:
        bad = [dict(type="bars", t0=0.0, t1=5.0, src="씨비에스 집계 · 11월 5일", rows=[dict(name="가", col="dem", pct=50.0)], mid="x_씨비에스")]
        got = checks.screen_wording(bad, election=False)
        self.assertEqual(len(got), 1)   # mid 같은 식별자는 보지 않는다
        self.assertEqual(checks.screen_wording([dict(type="bars", t0=0.0, t1=5.0, src="CBS 집계")], election=False), [])


class SymbolMediaTest(unittest.TestCase):
    """UF-164 "당나귀와 코끼리 이미지도 보이게 되는거지?" — 상징을 말하는 문장에 그 그림."""

    S = [types.SimpleNamespace(sid="basics_7", t0=10.0, t1=20.0, text="민주당 당나귀와 공화당 코끼리는 만평에서 시작됐습니다.")]

    def test_no_media_fails(self) -> None:
        self.assertTrue(checks.symbol_media(self.S, [dict(type="marker", t0=10.0, t1=20.0)]))

    def test_photo_or_emblem_passes(self) -> None:
        self.assertEqual(checks.symbol_media(self.S, [dict(type="photo", t0=12.0, t1=15.0)]), [])
        self.assertEqual(checks.symbol_media(self.S, [dict(type="badge", kind="emblem", t0=12.0, t1=15.0)]), [])


class LabelHaloTest(unittest.TestCase):
    """UF-168 "흰색 테두리가 너무 작은 글씨에는 맞지 않는" — 10px 이하 지명 halo 상한(규칙 로드 오류)."""

    def test_thick_small_halo_rejected(self) -> None:
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))["labels"]
        LabelRules.model_validate(raw)
        raw["admin1_modes"]["prominent"]["cities"]["halo"] = 2.6
        with self.assertRaises(ValidationError):
            LabelRules.model_validate(raw)


class AreaOutlineTest(unittest.TestCase):
    """UF-169 "테두리 라인의 두께를 좀 얇게 해. 너무 투박해" — area 외곽선 가장 굵은 단 상한."""

    def test_old_thick_outline_rejected(self) -> None:
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))["area"]
        AreaRules.model_validate(raw)
        raw["outline"] = [[5.0, 0.08], [2.2, 0.22], [0.9, 0.85]]   # UF-169 이전 값
        with self.assertRaises(ValidationError):
            AreaRules.model_validate(raw)


class Admin1LabelTest(unittest.TestCase):
    """UF-167 "도시 이름들 보다 주 이름이 표기 되면 좋겠어" — prominent 모드에서 주 이름이 화면에 없으면 경고."""

    def test_check_registered(self) -> None:
        self.assertIn("admin1_label_missing", checks.WARN)
        self.assertIn("screen_wording", checks.HARD)
        self.assertIn("symbol_media", checks.HARD)

    def test_subtle_mode_not_checked(self) -> None:
        P = types.SimpleNamespace(R=types.SimpleNamespace(stage=types.SimpleNamespace(admin1_mode_name="subtle")), cams=None)  # noqa: N806
        self.assertEqual(checks.admin1_label_missing(P), [])


class LeadingConnectiveTest(unittest.TestCase):
    """UF-174 "무지성으로 한편같은거 넣지 말라고 하지 않았어?" — 문장 첫머리 '한편' 금지(slop), 첫머리 접속사 남발 = [flow-overuse]."""

    V14 = ["그리고 다음 날 새벽까지 민주당은 하원과 상원을 모두 되찾았습니다.", "그래서 이번에는 상원 35석을 뽑았습니다.",
           "또한 주지사 선거에서는 민주당이 다섯 곳을 가져왔습니다.", "이어서 캔자스에서는 해밀턴 후보가 이겼습니다.",
           "또한 노스캐롤라이나에서는 쿠퍼 후보가 이겼습니다.", "메인은 잭슨 후보가 이겼습니다.", "오하이오는 브라운 후보가 이겼습니다.",
           "조지아는 오소프 의원이 재선됐습니다.", "그리고 네바다에서는 포드 후보가 이겼습니다.", "텍사스는 탈라리코 후보가 이겼습니다."]

    def _lint(self, texts: list[str]) -> "list[tuple[str, str]]":
        from script.lint import lint  # noqa: PLC0415

        return [(i.kind, i.severity) for i in lint(_sc(*texts), check_sources=False).issues]

    def test_hanpyeon_head_is_slop(self) -> None:
        self.assertIn(("slop", "error"), self._lint(["한편 주민투표에서는 버지니아가 투표권을 넓혔습니다."]))
        self.assertNotIn(("slop", "error"), self._lint(["주민투표에서는 버지니아가 투표권을 넓혔습니다."]))

    def test_v14_connective_overuse_warns(self) -> None:
        self.assertIn(("flow-overuse", "warning"), self._lint(self.V14))

    def test_rules_no_longer_recommend_hanpyeon(self) -> None:
        r = load_rules()
        self.assertNotIn("한편", r.script_grammar.connectives)
        self.assertLessEqual(r.script_grammar.connective_max_ratio, 0.35)
        self.assertNotIn('"한편"으로 잇는다', r.script_vocab.contrast_hint)


if __name__ == "__main__":
    unittest.main()
