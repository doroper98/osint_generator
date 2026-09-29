"""Phase 5 휘장·뱃지 제안·수집기 테스트 (v2.4.0, back_and_forth D-0029 작업 3·4·6·8).

- 휘장 결정은 코드가 한다: Restrictions 하나라도 → flag_fallback(D5). 손으로 use 로 바꾸면 로드 오류.
- 렌더러: flag_fallback 휘장 뱃지는 국기 이미지만 쓴다(휘장 파일 키 0회).
- 뱃지 제안: 별칭 경계(조사·합성어), 제안만(이벤트 생성 없음).
- commons_fetch 순수 함수: 지수 대기, Restrictions 파싱, 비표준 폭 거부.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from pydantic import ValidationError

from engine.entities import load_emblem_registry, load_entities
from engine.layers.badges import image_keys, resolve_kind
from engine.provenance import emblem_usage
from schemas.emblem_models import EmblemEntry, EmblemRegistry, decide_emblem, license_allowed
from script.badges import badge_usage, find_mentions, suggest_badges
from script.schema import Plan
from tools.commons_fetch import CommonsError, backoff_sec, emblem_entry, info, parse_restrictions


def _entry(**kw: object) -> dict:
    base = dict(file="x.png", title="File:X.svg", license="Public domain", restrictions=[], decision="use",
                reason="no_restrictions", fallback_flag="us")
    return {**base, **kw}


class _FakeAssets:
    def __init__(self, reg: EmblemRegistry) -> None:
        self.emblems = reg

    def emblem_flag(self, eid: str) -> str | None:
        ent = self.emblems.emblems[eid]
        return ent.fallback_flag if ent.decision == "flag_fallback" else None


def _plan(texts: list[str]) -> Plan:
    sents = [dict(sid=f"s_{i}", scene="s", date="2026.09.18", text=t, tts=t, segments=[[t, 0]], mp3="x", npy="x",
                  dur=2.0, t0=i * 3.0, t1=i * 3.0 + 2.0) for i, t in enumerate(texts)]
    return Plan(sentences=sents, cards=[dict(kind="title", t0=0.0, t1=1.0)], scene_start={"s": 0.0},
                total=len(texts) * 3.0, voice="v", title="T", subtitle="S", date="2026.09.18")


class EmblemDecisionTest(unittest.TestCase):
    def test_any_restriction_forces_flag_fallback(self) -> None:
        for r in (["insignia"], ["trademarked"], ["personality"], ["insignia", "trademarked"]):
            dec, why = decide_emblem(r, "Public domain", has_file=True)
            self.assertEqual(dec, "flag_fallback")
            self.assertIn(r[0], why)

    def test_clear_emblem_is_use(self) -> None:
        self.assertEqual(decide_emblem([], "Public domain", True), ("use", "no_restrictions"))
        self.assertEqual(decide_emblem([], "", False)[0], "flag_fallback")
        self.assertEqual(decide_emblem([], "CC BY-SA 4.0", True)[0], "flag_fallback")

    def test_hand_edited_use_with_restrictions_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            EmblemEntry.model_validate(_entry(restrictions=["insignia"], decision="use"))
        with self.assertRaises(ValidationError):   # user_decision 상태 없음(D5)
            EmblemEntry.model_validate(_entry(decision="user_decision"))

    def test_license_filter(self) -> None:
        self.assertTrue(license_allowed("KOGL Type 1"))
        self.assertFalse(license_allowed("CC BY-SA 2.0"))

    def test_repo_registry_restricted_all_fallback(self) -> None:
        reg = load_emblem_registry()
        self.assertIn("navcent", reg.emblems)
        for eid, ent in reg.emblems.items():
            if ent.restrictions and ent.user_exception is None:   # v4.8.0 D-0109 — 사용자 예외(D98 청와대)만 제한을 넘는다
                self.assertEqual(ent.decision, "flag_fallback", eid)
                self.assertIsNone(ent.file, eid)
        ents = load_entities()
        for eid in reg.emblems:
            self.assertEqual(ents.emblem_owner(eid).kind, "org")


class EmblemRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        reg = EmblemRegistry(emblems={
            "ok": EmblemEntry.model_validate(_entry()),
            "bad": EmblemEntry.model_validate(_entry(file=None, restrictions=["insignia"], decision="flag_fallback",
                                                     reason="restrictions: insignia", fallback_flag="ir")),
        })
        self.R = SimpleNamespace(assets=_FakeAssets(reg))

    def test_fallback_uses_flag_only(self) -> None:
        e = dict(type="badge", kind="emblem", img="bad", t0=0.0)
        self.assertEqual(resolve_kind(self.R, e), ("flag", "ir"))
        self.assertEqual(image_keys(e, self.R), ["flag11:ir"])
        self.assertEqual(image_keys(dict(type="badge", kind="emblem", img="ok"), self.R), ["emblem:ok"])

    def test_provenance_emblem_usage(self) -> None:
        evs = [dict(type="badge", kind="emblem", img="bad"), dict(type="badge", kind="emblem", img="ok")]
        self.assertEqual(emblem_usage(evs, self.R.assets.emblem_flag), {"used": ["ok"], "flag_fallback": {"bad": "ir"}})


class BadgeSuggestTest(unittest.TestCase):
    def test_boundaries(self) -> None:
        reg = load_entities()
        self.assertEqual([m[2] for m in find_mentions("인도양과 인도네시아, 인도의 선택", reg)], ["in"])
        self.assertEqual([m[2] for m in find_mentions("대한민국은 청해부대를 보냈다", reg)], ["kr", "cheonghae"])
        self.assertEqual(find_mentions("그것이란 말", reg), [])

    def test_suggest_only_and_usage(self) -> None:
        plan = _plan(["트럼프 대통령이 동맹에 요구했다.", "혁명수비대가 유조선을 나포했다."])
        sug = suggest_badges(plan)
        self.assertEqual([(b.sid, b.entity, b.kind) for b in sug],
                         [("s_0", "trump", "person"), ("s_1", "irgc", "emblem")])
        self.assertTrue(0.0 <= sug[0].at <= 2.0)
        u = badge_usage(plan, [dict(type="badge", kind="person", pid="trump", flag="us", t0=0.0)])
        self.assertEqual(u["used"], ["trump"])
        self.assertEqual(u["suggested_and_used"], ["trump"])


class CommonsFetchPureTest(unittest.TestCase):
    def test_backoff(self) -> None:
        self.assertEqual([backoff_sec(a) for a in range(6)], [60, 120, 240, 480, 600, 600])
        self.assertEqual(backoff_sec(0, "30"), 30)

    def test_restrictions_parse(self) -> None:
        self.assertEqual(parse_restrictions("insignia trademarked"), ["insignia", "trademarked"])
        self.assertEqual(parse_restrictions("<span>personality</span>"), ["personality"])
        self.assertEqual(parse_restrictions(""), [])

    def test_nonstandard_width_rejected_before_network(self) -> None:
        with self.assertRaises(CommonsError):
            info("File:X.jpg", width=700)

    def test_emblem_entry_from_metadata(self) -> None:
        ii = dict(restrictions=["insignia"], lic="Public domain", artist="A", page="https://c/x")
        ent = emblem_entry("irgc", "File:Seal.svg", "ir", ii)
        self.assertEqual((ent.decision, ent.file, ent.fallback_flag), ("flag_fallback", None, "ir"))
        self.assertEqual(emblem_entry("cheonghae", None, "kr", None).reason, "no_emblem_file")


if __name__ == "__main__":
    unittest.main()
