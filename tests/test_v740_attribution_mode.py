"""v7.4.0 back_and_forth D-0233(UF-117, D243) — 보도 귀속 방식 credits: 보도 출처는 엔딩 크레딧 장면별 '보도 출처', 자막·내레이션은 평서.
(a) credits 모드 보도 귀속 → [press-attribution] 경고 (b) 당사자 발언(statement)은 경고 없음 (c) 논쟁(disputed) 수치는 자료 이름 유지
(d) 크레딧 press 슬롯 장면별 줄·롤 상한 안 (e) narration 모드(옛 원고·골든 hormuz)는 종전과 같다."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from engine import fullcards
from engine.credits import press_items
from engine.project import press_by_scene
from script.lint import attribution_mode, lint
from script.schema import Script

REPO = Path(__file__).resolve().parent.parent


def _sc(text: str, src: str = "c1", date: str = "2026.10.18") -> Script:
    return Script.model_validate(dict(title="t", subtitle="s", date=date, scenes=[
        dict(id="a", kind="cold", sentences=[dict(date="2026.10.15", text=text, sources=[src])])]))


def _kinds(rep) -> list[str]:  # noqa: ANN001
    return [i.kind for i in rep.issues if i.kind in ("press-attribution", "attribution")]


class CreditsModeTest(unittest.TestCase):
    def test_a_press_attribution_warns(self) -> None:
        rep = lint(_sc("로이터에 따르면 처리량은 하루 380만 배럴이었습니다."), {"c1": "unverified"}, mode="credits", kinds={"c1": "fact"})
        self.assertEqual(_kinds(rep), ["press-attribution"])
        self.assertEqual(_kinds(lint(_sc("처리량은 하루 380만 배럴이었습니다."), {"c1": "unverified"}, mode="credits", kinds={"c1": "fact"})), [])

    def test_b_party_statement_kept(self) -> None:
        rep = lint(_sc("러시아 국방부는 파편이 불을 냈다고 밝혔습니다."), {"c1": "unverified"}, mode="credits", kinds={"c1": "statement"})
        self.assertEqual(_kinds(rep), [])
        rep = lint(_sc("파편이 불을 냈습니다."), {"c1": "unverified"}, mode="credits", kinds={"c1": "statement"})
        self.assertEqual(_kinds(rep), ["attribution"])   # 당사자 발언인데 말한 쪽이 없다

    def test_c_disputed_keeps_source_name(self) -> None:
        rep = lint(_sc("케이플러 자료에 따르면 한국산은 11만 2천 t이었습니다."), {"c1": "disputed"}, mode="credits", kinds={"c1": "fact"})
        self.assertEqual(_kinds(rep), [])
        for text in ("케이플러 자료로는 한국산이 11만 2천 t이었습니다.", "크레아 집계로는 한국산이 1만 8천 t이었습니다."):   # D-0234 표기
            rep = lint(_sc(text), {"c1": "disputed"}, mode="credits", kinds={"c1": "fact"})
            self.assertEqual(_kinds(rep), [], text)
            self.assertFalse([i for i in rep.issues if i.kind == "disputed-claim"], text)

    def test_f_press_prefix_on_kept_sentence(self) -> None:   # D-0234 — ① 부류라도 매체 접두는 경고, 발언자만 남긴다
        st = {"c1": "statement"}
        for text in ("AP통신에 따르면 트럼프 대통령은 경유를 공급할 것이라고 말했습니다.",
                     "AP통신은 젤렌스키 대통령이 배신감을 느낀다고 말했다고 전했습니다."):
            self.assertEqual(_kinds(lint(_sc(text), {"c1": "unverified"}, mode="credits", kinds=st)), ["press-attribution"], text)
        rep = lint(_sc("가디언이 인용한 케이플러 자료에 따르면 한국산은 11만 2천 t이었습니다."), {"c1": "disputed"}, mode="credits", kinds={"c1": "fact"})
        self.assertEqual(_kinds(rep), ["press-attribution"])
        for text in ("트럼프 대통령은 경유를 공급할 것이라고 말했습니다.",
                     "AP통신은 이 수치를 독립적으로 검증할 수 없다고 전했습니다."):   # 매체가 발언 주체면 그대로
            self.assertEqual(_kinds(lint(_sc(text), {"c1": "unverified"}, mode="credits", kinds=st)), [], text)


class PressCreditTest(unittest.TestCase):
    def test_d_scene_lines_and_roll(self) -> None:
        press = press_by_scene(REPO / "projects" / "diesel_road_2026")
        self.assertEqual(press[0][0], "콜드 오픈")
        items = press_items(press)
        self.assertTrue(all(" · " in m for m, _ in items))
        self.assertEqual(len(items), sum(1 for _, n in press if n))   # 한 장면 한 줄(긴 줄은 열 폭에서 줄바꿈)
        secs = [("보도 출처", items), ("기사 카드", [("헤드라인 번역·요지 자체 조판", "기사 화면 캡처·로고 없음")])]
        self.assertEqual(fullcards.endcard_overflow(secs, [0, 0]), [])   # 롤 속도 상한 안


class NarrationModeTest(unittest.TestCase):
    def test_e_old_projects_unchanged(self) -> None:
        proj = REPO / "projects" / "hormuz_korea"
        sc = Script.model_validate(yaml.safe_load((proj / "script.yaml").read_text(encoding="utf-8")))
        self.assertEqual(attribution_mode(proj, sc), "narration")
        a = lint(sc, check_sources=False)
        b = lint(sc, check_sources=False, mode="narration", kinds={})
        self.assertEqual([i.line() for i in a.issues], [i.line() for i in b.issues])

    def test_new_project_default_credits(self) -> None:
        proj = REPO / "projects" / "diesel_road_2026"
        sc = Script.model_validate(yaml.safe_load((proj / "script.yaml").read_text(encoding="utf-8")))
        self.assertEqual(attribution_mode(proj, sc), "credits")


if __name__ == "__main__":
    unittest.main()
