"""v7.4.0 D-0606 §2(RIGHTS-AP-001) — 사진 라이선스 대조 [license-mismatch] · 진영 휘장 재작도 레코드(D-0606 A)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from schemas.media_models import MediaAsset, MediaRegistryFile
from schemas.war_history import license_mismatch, norm_license_tag

REPO = Path(__file__).resolve().parents[1]
CNG = ["CC-BY-SA-2.5", "CC-PD-Mark", "GFDL", "License migration not eligible", "PD-old-100-expired", "Self-published work"]   # 실제 앞 주화 사진 분류


class LicenseMismatchTest(unittest.TestCase):
    def test_old_coin_photo_is_caught(self) -> None:
        errs = license_mismatch("Public domain", CNG)
        self.assertTrue(errs and errs[0].startswith("[license-mismatch]"))

    def test_clean_cases_pass(self) -> None:
        self.assertEqual(license_mismatch("CC BY 3.0", ["CC-BY-3.0", "Self-published work"]), [])
        self.assertEqual(license_mismatch("Public domain", ["PD US Marines"]), [])
        self.assertEqual(license_mismatch("Public domain", ["PD-self"]), [])
        self.assertEqual(license_mismatch("CC BY 2.0", ["CC-BY-2.0", "GFDL"]), [])   # 이중 라이선스 — 허용 쪽이 있다

    def test_hand_value_differs(self) -> None:
        self.assertTrue(license_mismatch("CC BY 2.0", ["CC-BY-3.0"]))

    def test_norm(self) -> None:
        self.assertEqual(norm_license_tag("CC-BY-SA-2.5"), "cc by-sa 2.5")
        self.assertEqual(norm_license_tag("CC-BY-4.0"), "cc by 4.0")
        self.assertEqual(norm_license_tag("PD-Art (PD-old-auto-expired)"), "public domain")
        self.assertIsNone(norm_license_tag("Self-published work"))


def _art(**kw: object) -> dict:
    base = dict(is_file_photo=False, rights_status="rights_clear", retrieved_at="2026-11-01", source_hash="0" * 32, kind="period_art",
                title="File:x.jpg", credit_author="a", date="2026-11-01", file_note="n", depicts=["주화"], license="Public domain", photo_license="Public domain", work_license="Public domain(PD-old)",
                license_tags=CNG, author="a", url="https://commons.wikimedia.org/wiki/File:x.jpg", caption="주화",
                file="x.jpg", created="-237~-209", work_kind="coin", holder="h", art_history="문장.", art_history_source="출처",
                tool={"name": "sketch.war.fetch", "params": {"commons_title": "File:x.jpg"}},
                verified_by={"by": "t", "on": "2026-11-01", "casualty_free": True, "relevance": "r"})
    base.update(kw)
    return base


class PhotoLicenseFromTagsTest(unittest.TestCase):
    def test_auto_photo_license(self) -> None:
        from schemas.war_history import photo_license_from_tags as f

        self.assertEqual(f(["CC-BY-3.0"]), "CC BY 3.0")
        self.assertEqual(f(CNG), "CC BY-SA 2.5")                  # 유물 PD 가 아니라 사진 라이선스 → 화면 불가 값
        self.assertEqual(f(["CC-PD-Mark", "PD-old-70-expired"]), "Public domain")
        self.assertEqual(f(["CC-BY-4.0", "GFDL"]), "CC BY 4.0")
        self.assertIsNone(f(["Self-published work"]))


class EngineCheckTest(unittest.TestCase):
    def test_engine_license_mismatch_all_genres(self) -> None:
        from types import SimpleNamespace as NS

        from engine.checks import HARD, check_license_mismatch

        self.assertIn("license_mismatch", HARD)
        bad = NS(license="Public domain", photo_license=None, license_tags=CNG)
        ok = NS(license="CC BY 3.0", photo_license="CC BY 3.0", license_tags=["CC-BY-3.0"])
        none = NS(license="Public domain", photo_license=None, license_tags=None)   # 분류 미기록 레코드(옛 트랙) = 대조 안 함
        P = NS(R=NS(assets=NS(media_assets={"bad": bad, "ok": ok, "none": none})),  # noqa: N806
               events=[{"type": "photo", "mid": "bad"}, {"type": "clip", "mid": "ok"}, {"type": "photo", "mid": "none"}])
        out = check_license_mismatch(P)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("bad: [license-mismatch]"))


class MediaAssetLicenseTest(unittest.TestCase):
    def test_record_with_cng_tags_fails(self) -> None:
        with self.assertRaises(ValidationError) as cm:
            MediaAsset.model_validate(_art())
        self.assertIn("license-mismatch", str(cm.exception))

    def test_period_art_needs_photo_license_and_tags(self) -> None:
        with self.assertRaises(ValidationError):
            MediaAsset.model_validate(_art(license_tags=None))
        with self.assertRaises(ValidationError):
            MediaAsset.model_validate(_art(license_tags=["PD-old-100-expired"], work_license=None))
        with self.assertRaises(ValidationError):   # 입체 유물(coin) + 유물 나이 PD 뿐 = 사진 자체 PD 근거 필수(D710)
            MediaAsset.model_validate(_art(license_tags=["PD-old-100-expired", "CC-PD-Mark"]))
        MediaAsset.model_validate(_art(license_tags=["PD-old-100-expired", "CC-PD-Mark"], photo_pd_basis="1900년 촬영·발행 사진 PD-old"))
        MediaAsset.model_validate(_art(license_tags=["PD-old-100-expired"], work_kind="painting"))   # 2D 복제 = PD-Art 성립

    def test_project_records_pass(self) -> None:
        for pid in ("cannae_sketch", "inchon_sketch"):
            raw = json.loads((REPO / "projects" / pid / "media.json").read_text(encoding="utf-8"))
            MediaRegistryFile.model_validate(raw)
            for mid, a in raw["assets"].items():
                self.assertIsNotNone(a.get("license_tags"), f"{pid}/{mid}: license_tags(Commons 분류) 기록")
                self.assertEqual(a["license"], a["photo_license"], mid)


class EmblemReconstructionTest(unittest.TestCase):
    def test_registry_glyphs_registered(self) -> None:
        from engine.entities import load_emblem_registry
        from engine.glyphs.emblems import EMBLEMS

        rec = load_emblem_registry().reconstructions
        self.assertIn("carthage_tanit", rec)
        self.assertLessEqual({r.glyph for r in rec.values()}, set(EMBLEMS))
        self.assertTrue(all(r.reconstruction and "재현" in r.caption_label for r in rec.values()))

    def test_basis_license_must_be_allowed(self) -> None:
        from schemas.emblem_models import EmblemReconstruction

        good = dict(glyph="tanit", faction="카르타고", basis="b", basis_title="File:x", basis_url="u", basis_license="Public domain",
                    basis_author="a", basis_created="-300~-201", reconstruction=True, caption_label="비석 기호 재현")
        EmblemReconstruction(**good)
        with self.assertRaises(ValidationError):
            EmblemReconstruction(**{**good, "basis_license": "CC BY-SA 4.0"})
        with self.assertRaises(ValidationError):
            EmblemReconstruction(**{**good, "caption_label": "타니트 휘장"})

    def test_emblem_smaller_than_pictogram(self) -> None:
        from rules import load_rules

        wh = load_rules().war_history
        self.assertLess(wh.faction_badge.emblem.block_px, wh.symbol_sets.glyph.size_px)

    def test_asymmetry_needs_reason_and_unknown_key_is_error(self) -> None:
        import yaml

        from sketch.war.scene import SceneError, faction_emblems
        from sketch.war.spec import WarSpec

        raw = yaml.safe_load((REPO / "projects" / "cannae_sketch" / "sketch.yaml").read_text(encoding="utf-8"))
        spec = WarSpec.model_validate(raw)
        self.assertEqual({k: r.glyph for k, r in faction_emblems(spec).items()}, {"carthage": "tanit"})
        bad = json.loads(json.dumps(raw))
        bad["factions"]["rome"].pop("emblem_absent_reason")
        with self.assertRaises(ValidationError):
            WarSpec.model_validate(bad)
        bad2 = json.loads(json.dumps(raw))
        bad2["factions"]["carthage"]["emblem"] = "carthage_invented"
        with self.assertRaises(SceneError):
            faction_emblems(WarSpec.model_validate(bad2))


if __name__ == "__main__":
    unittest.main()


class BandKindTest(unittest.TestCase):
    """D-0610 ① — 띠 종류(kind) 필수, ancient_range 라벨에 '현대' 없음, 한 값은 범위 꼴이 아니다."""

    def test_kind_required_and_labels(self) -> None:
        from schemas.data_models import EstimateBand
        from schemas.war_history import band_label

        with self.assertRaises(ValidationError):
            EstimateBand(low=1, high=2, source="s")
        a = EstimateBand(kind="ancient_range", low=43500, high=70000, low_label="에우트로피우스", high_label="폴리비오스", source="s")
        self.assertEqual(band_label(a), "사료마다 다르다 — 에우트로피우스 43,500~폴리비오스 70,000")
        self.assertNotIn("현대", band_label(a))
        one = EstimateBand(kind="ancient_range", low=86000, high=86000, low_label="폴리비오스", high_label="폴리비오스", source="s")
        self.assertNotIn("~", band_label(one))
        self.assertIn("현대 추정", band_label(EstimateBand(kind="modern_estimate", low=1, high=2, source="s")))

    def test_cannae_forces_all_ancient_range(self) -> None:
        import yaml

        from schemas.data_models import ForceFiguresFile

        f = ForceFiguresFile.model_validate(yaml.safe_load((REPO / "projects/cannae_216bc/forces.yaml").read_text(encoding="utf-8")))
        self.assertIn("rome_strength", f.by_id())
        self.assertTrue(all(x.band.kind == "ancient_range" for x in f.figures))
