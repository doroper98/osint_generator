"""v0.44.0 쇼츠 콜라주 Phase 0 스키마 테스트.

- 번들 video 블록(BundleSectionVideo 등)이 additive 로 파싱되는지
- AssetLibraryManifest id 유일성 검증
- (DesignSheet 테스트는 v2.0.0 에서 쇼츠 트랙 보관과 함께 삭제)
"""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from schemas.models import (
    AssetLibraryManifest,
    AssetSourceRef,
    LibraryAssetVariant,
    LibraryPerson,
    ReportBundle,
    RightsStatus,
)


def _minimal_bundle(**over: object) -> dict:
    d: dict = {
        "schema_version": 1,
        "bundle_kind": "report_bundle",
        "producer": {"system": "agents_reviewer", "version": "v8.0.0"},
        "report": {"report_id": "r1", "headline": "h"},
    }
    d.update(over)
    return d


class TestBundleVideoBlock(unittest.TestCase):
    def test_video_blocks_parse(self) -> None:
        b = ReportBundle.model_validate(
            _minimal_bundle(
                report={
                    "report_id": "r1",
                    "headline": "h",
                    "video": {"intro_narration": ["첫 문장입니다."]},
                },
                sections=[
                    {
                        "section_id": "s1",
                        "video": {
                            "narration": ["문장 하나.", "문장 둘."],
                            "narration_tts": ["문장 하나.", "문장 둘."],
                            "highlights": ["키 테이크어웨이"],
                            "emphasis": ["키"],
                        },
                    }
                ],
                timeline={"heading": "t", "video": {"narration": ["타임라인 문장."]}},
            )
        )
        assert b.report.video is not None
        self.assertEqual(b.report.video.intro_narration, ["첫 문장입니다."])
        assert b.sections[0].video is not None
        self.assertEqual(len(b.sections[0].video.narration), 2)
        self.assertEqual(b.sections[0].video.emphasis, ["키"])

    def test_video_absent_is_none(self) -> None:
        b = ReportBundle.model_validate(
            _minimal_bundle(sections=[{"section_id": "s1"}])
        )
        self.assertIsNone(b.report.video)
        self.assertIsNone(b.sections[0].video)


class TestAssetLibrary(unittest.TestCase):
    def _person(self, pid: str) -> LibraryPerson:
        return LibraryPerson(
            person_id=pid,
            name_ko="트럼프",
            source=AssetSourceRef(
                license="public_domain", rights_status=RightsStatus.RIGHTS_CLEAR
            ),
            variants=[
                LibraryAssetVariant(
                    style="stipple", path=f"assets/library/people/{pid}/f.svg"
                )
            ],
        )

    def test_manifest_roundtrip(self) -> None:
        m = AssetLibraryManifest(people=[self._person("trump")])
        m2 = AssetLibraryManifest.model_validate_json(m.model_dump_json())
        self.assertEqual(m2.people[0].variants[0].style, "stipple")
        self.assertEqual(m2.schema_version, 1)

    def test_duplicate_person_id_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AssetLibraryManifest(people=[self._person("x"), self._person("x")])

if __name__ == "__main__":
    unittest.main()
