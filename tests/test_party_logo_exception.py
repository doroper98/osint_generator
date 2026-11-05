"""정당 공식 로고 권리 예외 (v7.4.0, back_and_forth D-0296 · 사용자 결정 D519 · UF-165).

- 예외 기록 없는 restricted(trademarked) 휘장은 여전히 flag_fallback(D5) — 손으로 use 로 바꾸면 로드 오류.
- D519 기록이 있는 dem_party·rep_party 만 use. 예외 목록 밖 id 에 D519 를 붙이면 로드 오류.
- provenance emblems.rights_exceptions 에 실제 쓴 예외 휘장과 용도 한정 문구가 남는다(P5).
"""

from __future__ import annotations

import unittest
from unittest import mock

from engine.provenance import emblem_usage
from schemas.emblem_models import USER_EXCEPTIONS, EmblemEntry, EmblemRegistry, decide_emblem


def entry(**kw: object) -> EmblemEntry:
    base = dict(file="dem_party.png", title="File:US Democratic Party 2025 logo (profile).svg", license="Public domain", author="DNC",
                restrictions=["trademarked"], decision="use", reason="user_exception D519: restrictions trademarked — 용도 한정",
                fallback_flag="us", user_exception="D519", exception_scope="정당 범례 뱃지 전용, 비공개 시청 한정")
    base.update(kw)
    return EmblemEntry.model_validate(base)


class PartyLogoExceptionTest(unittest.TestCase):
    def test_restricted_without_record_falls_back(self) -> None:
        self.assertEqual(decide_emblem(["trademarked"], "Public domain", True)[0], "flag_fallback")
        with self.assertRaises(ValueError):   # 예외 기록 없이 use = 규칙 위반
            entry(user_exception=None, exception_scope=None)

    def test_d519_only_party_logos(self) -> None:
        self.assertEqual(USER_EXCEPTIONS["D519"], frozenset({"dem_party", "rep_party"}))
        self.assertEqual(decide_emblem(["trademarked"], "Public domain", True, "D519")[0], "use")
        EmblemRegistry(emblems={"dem_party": entry(), "rep_party": entry(file="rep_party.png")})
        with self.assertRaises(ValueError):
            EmblemRegistry(emblems={"centcom": entry(file="centcom.png")})

    def test_provenance_records_exception(self) -> None:
        reg = EmblemRegistry(emblems={"dem_party": entry()})
        evs = [{"type": "badge", "kind": "emblem", "img": "dem_party"}]
        with mock.patch("engine.entities.load_emblem_registry", return_value=reg):
            got = emblem_usage(evs, lambda eid: None)
        self.assertEqual(got["used"], ["dem_party"])
        self.assertEqual(got["rights_exceptions"]["dem_party"]["user_exception"], "D519")


class CreditsEmblemExceptionTest(unittest.TestCase):
    def test_restricted_emblem_needs_registered_exception(self) -> None:
        """engine.credits.rights_exception — restricted 휘장은 D519 기록이 있고 그 id 일 때만 예외로 통과(나머지는 None → 권리 점검 실패)."""
        from engine.credits import rights_exception  # noqa: PLC0415

        ok = {"rights_status": "restricted", "user_exception": "D519", "exception": "정당 범례"}
        self.assertEqual(rights_exception("emblems.dem_party", ok), "D519")
        self.assertIsNone(rights_exception("emblems.centcom", ok))
        self.assertIsNone(rights_exception("emblems.dem_party", {"rights_status": "restricted"}))


if __name__ == "__main__":
    unittest.main()
