"""미디어 레지스트리 스키마·권리 (D-0036 작업 2·8, 14 §2·§6, C9)."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from engine.credits import RightsError
from engine.media_registry import credit_line, load_media_registry, registry_path
from schemas.media_models import MediaAsset


def _raw() -> dict:
    return json.loads(registry_path().read_text(encoding="utf-8"))


class MediaRegistryTest(unittest.TestCase):
    def test_v3_seven_assets(self) -> None:
        reg = load_media_registry()
        kinds = sorted(a.kind for a in reg.values())
        self.assertEqual(kinds, ["article", "article", "cutout", "photo", "photo", "video", "video"])   # 14 §1 v3 7종
        self.assertTrue(all(a.rights_status == "rights_clear" for a in reg.values()))

    def test_strikes_segment_casualty_checked(self) -> None:
        s = load_media_registry()["strikes"]
        self.assertEqual(s.segment, (1.5, 6.5))
        self.assertEqual(s.verified_by.segment_checked, (1.5, 6.5))
        self.assertTrue(s.verified_by.casualty_free)

    def test_credit_line_from_fields(self) -> None:
        reg = load_media_registry()
        self.assertEqual(credit_line(reg["hormuz_transit"]), "자료사진 · 2023. 05 · U.S. Navy · Public domain")
        self.assertEqual(credit_line(reg["p8"]), "자료사진 · U.S. Navy")

    def _bad(self, mutate) -> None:  # noqa: ANN001
        raw = _raw()
        mutate(raw["assets"])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.json"
            p.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(RightsError):
                load_media_registry(p)

    def test_missing_rights_field_is_error(self) -> None:
        self._bad(lambda a: a["hormuz_transit"].pop("license"))

    def test_missing_verification_is_error(self) -> None:
        self._bad(lambda a: a["rok_iraq"].pop("verified_by"))

    def test_file_photo_label_required(self) -> None:
        self._bad(lambda a: a["hormuz_transit"].update(file_note="2023. 05"))   # 자료사진 표기 없음

    def test_casualty_segment_mismatch_is_error(self) -> None:
        self._bad(lambda a: a["strikes"].update(segment=[1.5, 15.0]))           # 확인 안 한 구간(13초 이후 포함)

    def test_casualty_flag_is_error(self) -> None:
        self._bad(lambda a: a["niovi"]["verified_by"].update(casualty_free=False))

    def test_unknown_field_is_error(self) -> None:
        a = copy.deepcopy(_raw()["assets"]["p8"])
        a["screen_caption_override"] = "x"
        with self.assertRaises(ValidationError):
            MediaAsset.model_validate(a)


if __name__ == "__main__":
    unittest.main()
