"""Phase 5 엔딩 크레딧·권리 대조 테스트 (v2.4.0, back_and_forth D-0029 작업 7·8).

렌더가 쓰는 자산은 ① 권리 레지스트리에 있고 ② rights_clear 이고 ③ 크레딧 행이 가리켜야 한다 — 어기면 RightsError.
"""

from __future__ import annotations

import unittest

import yaml

from engine.credits import Credits, RightsError, check_credits, credit_sections, required_refs
from schemas.engine_models import RightsRegistry

BUNDLES = {k: v for k, v in yaml.safe_load(open("assets/rights_bundles.yaml", encoding="utf-8")).items() if k != "schema_version"}
PEOPLE = {"trump": dict(src="repo_library", license="Public domain", artist="S", url="u")}
MEDIA = {"p8": dict(kind="photo", title="File:P8.jpg", license="Public domain", author="Navy", date="", url="u", caption="c",
                    file_note="")}
EVENTS = [dict(type="badge", t0=0.0, kind="person", pid="trump", flag="us"), dict(type="photo", t0=1.0, mid="p8", img="p8.jpg")]
KEYS = {"portrait:trump", "flag43:us", "media:p8.jpg"}


def _rights() -> dict:
    return {"people": PEOPLE, **BUNDLES}


def _credits(extra_items: list[dict] | None = None, auto_fonts: bool = True) -> Credits:
    secs = [dict(title="인물", column=0, items=[dict(main="트럼프", rights=["people.trump"], license="PD")]),
            dict(title="사진", column=1, items=[dict(main="P-8A", rights=["media.p8"], license="PD")]),
            dict(title="기타", column=0, items=[
                dict(main="국기", rights=["flags.flag_icons"]),
                dict(main="지도", rights=["map_data.natural_earth", "map_data.aws_terrain_tiles"]),
                dict(main="음악", rights=["music.zabriskie_patriarch"]),
                dict(main="내레이션", rights=["narration.tts"]), *(extra_items or [])])]
    if auto_fonts:
        secs.append(dict(title="폰트", column=1, auto="fonts"))
    return Credits.model_validate(dict(sections=secs))


def _flag(_: str) -> None:
    return None


class CreditsCheckTest(unittest.TestCase):
    def test_bundles_parse(self) -> None:
        RightsRegistry.model_validate(_rights())

    def test_complete_credits_pass(self) -> None:
        req = required_refs(EVENTS, _rights(), _flag, KEYS)
        self.assertIn("fonts.ibm_plex_sans_kr", req)
        self.assertIn("flags.flag_icons", req)
        check_credits(_credits(), _rights(), MEDIA, req)

    def test_missing_credit_line_is_error(self) -> None:
        req = required_refs(EVENTS, _rights(), _flag, KEYS)
        with self.assertRaisesRegex(RightsError, "엔딩 크레딧 누락: fonts"):
            check_credits(_credits(auto_fonts=False), _rights(), MEDIA, req)

    def test_missing_registry_entry_is_error(self) -> None:
        req = required_refs([*EVENTS, dict(type="clip", t0=2.0, mid="niovi", clip="niovi")], _rights(), _flag, KEYS)
        with self.assertRaisesRegex(RightsError, "권리 레지스트리에 없음: media.niovi"):
            check_credits(_credits(), _rights(), MEDIA, req)
        r = _rights()
        r.pop("music")
        with self.assertRaisesRegex(RightsError, "music 절이 비었다"):
            check_credits(_credits(), r, MEDIA, required_refs(EVENTS, r, _flag, KEYS))

    def test_dangling_credit_ref_is_error(self) -> None:
        req = required_refs(EVENTS, _rights(), _flag, KEYS)
        with self.assertRaisesRegex(RightsError, "가리키는 권리 항목 없음"):
            check_credits(_credits([dict(main="X", rights=["emblems.cia"])]), _rights(), MEDIA, req)

    def test_unverified_asset_is_error(self) -> None:
        r = _rights()
        r["people"] = {"trump": {**PEOPLE["trump"], "rights_status": "unverified"}}
        with self.assertRaisesRegex(RightsError, "권리 미확인"):
            check_credits(_credits(), r, MEDIA, required_refs(EVENTS, r, _flag, KEYS))

    def test_fallback_emblem_needs_no_emblem_rights(self) -> None:
        evs = [dict(type="badge", t0=0.0, kind="emblem", img="irgc")]
        self.assertNotIn("emblems.irgc", required_refs(evs, _rights(), lambda _: "ir", {"flag11:ir"}))
        self.assertIn("emblems.irgc", required_refs(evs, _rights(), _flag, {"emblem:irgc"}))

    def test_auto_section_lists_used_entries(self) -> None:
        req = required_refs(EVENTS, _rights(), _flag, KEYS)
        secs = dict(credit_sections(_credits(), _rights(), MEDIA, req))
        self.assertEqual([m for m, _ in secs["폰트"]], ["IBM Plex Sans KR", "IBM Plex Mono", "GmarketSans", "Noto Serif CJK KR"])
        self.assertTrue(secs["폰트"][0][1].endswith("SIL OFL 1.1"))

    def test_items_xor_auto(self) -> None:
        with self.assertRaises(ValueError):
            Credits.model_validate(dict(sections=[dict(title="x", column=0)]))


if __name__ == "__main__":
    unittest.main()
