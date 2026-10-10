"""G7 청와대 휘장 등재 (v4.8.0, back_and_forth D-0109, 사용자 결정 D98 — D5 제한 휘장 규칙의 사용자 예외)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from engine.entities import load_entities
from schemas.emblem_models import USER_EXCEPTIONS, EmblemEntry, EmblemRegistry, decide_emblem
from rules import load_rules

REPO = Path(__file__).resolve().parent.parent


class CheongwadaeEmblemTest(unittest.TestCase):
    def test_registry_entry_and_exception(self) -> None:
        reg = EmblemRegistry.model_validate_json((REPO / "assets/emblems/registry.json").read_text(encoding="utf-8"))
        e = reg.emblems["cheongwadae"]
        self.assertEqual((e.decision, e.user_exception, e.fallback_flag), ("use", "D98", "kr"))
        self.assertIn("insignia", e.restrictions)                      # 제한은 그대로 기록
        self.assertTrue(e.exception_scope and "청와대" in e.exception_scope)
        self.assertTrue(e.source_url.startswith("https://commons.wikimedia.org/"))
        others = [k for k, v in reg.emblems.items() if v.restrictions and k not in ("cheongwadae", "nato")]   # nato = U20261004
        self.assertTrue(others)
        self.assertTrue(all(reg.emblems[k].decision == "flag_fallback" and reg.emblems[k].user_exception is None for k in others))
        self.assertEqual(USER_EXCEPTIONS, {"D98": frozenset({"cheongwadae"}), "U20261004": frozenset({"nato"}),
                                           "U20261010": frozenset({"lee_jae_myung"})})   # v5.15.0 인물 예외(사용자 결정 D153, D-0160)
        n = reg.emblems["nato"]   # v5.5.0 사용자 직접 지시 2026-10-04
        self.assertEqual((n.decision, n.user_exception, n.file), ("use", "U20261004", "nato.png"))
        self.assertIn("insignia", n.restrictions)
        self.assertIn("나토", n.exception_scope or "")
        raw = json.loads((REPO / "assets/emblems/registry.json").read_text(encoding="utf-8"))
        self.assertNotIn("user_exception", raw["emblems"]["navcent"])   # 예외 없는 항목 = v4.7.0 과 같은 필드

    def test_exception_only_for_listed_emblem(self) -> None:
        base = dict(file="x.png", license="Public domain", restrictions=["insignia"], decision="use",
                    reason="r", fallback_flag="kr", user_exception="D98", exception_scope="용도")
        with self.assertRaises(ValidationError):
            EmblemRegistry.model_validate({"emblems": {"irgc": base}})          # 예외 목록 밖 휘장
        with self.assertRaises(ValidationError):
            EmblemEntry.model_validate({**base, "exception_scope": None})       # 용도 한정 없음
        with self.assertRaises(ValidationError):
            EmblemEntry.model_validate({**base, "user_exception": None})        # 예외 없이 use = D5 위반
        self.assertEqual(decide_emblem(["insignia"], "Public domain", True)[0], "flag_fallback")
        self.assertEqual(decide_emblem(["insignia"], "South Korea-Gov", True, "D98")[0], "flag_fallback")   # 라이선스 조건은 그대로

    def test_entity_and_grammar(self) -> None:
        ents = load_entities()
        self.assertEqual(ents.lookup("청와대").id, "cheongwadae")
        self.assertEqual(ents.lookup("대통령실").emblem, "cheongwadae")
        g = [ln for ln in load_rules().direction_grammar if "cheongwadae" in ln]
        self.assertEqual(len(g), 1)
        self.assertIn("초상", g[0])
        # 문법은 데이터(rules)에만 — 엔진·워커 코드에 휘장 id 리터럴 0
        hits = [str(p.relative_to(REPO)) for d in ("engine", "workers", "orchestrator") for p in (REPO / d).rglob("*.py")
                if "cheongwadae" in p.read_text(encoding="utf-8")]
        self.assertEqual(hits, [])

    def test_director_prompt_has_rule(self) -> None:
        from workers.prompt_loader import load_prompt
        for name in ("director", "revise_direction"):
            self.assertIn("img cheongwadae", load_prompt(name, load_rules()), name)


if __name__ == "__main__":
    unittest.main()
