"""v5.21.7 — media_fetch 보도 인용(B) 재수집(D-0189 §1) · media_notes 중복 키 오류(D-0190 §3-4)."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import yaml

from schemas.media_models import MediaRegistryFile
from script import media_table as MT
from tests.test_b_press_quote import _article, _press
from tests.test_p1_media_plan import _Proj
from tools import media_fetch as MF

DATA = b"jpegbytes"


def _reg(**over: object) -> dict:
    return MediaRegistryFile.model_validate({"schema_version": 1, "assets": {"art_a": _article(), "art_a_press": _press(**over)}}).assets


class PressFetchTest(unittest.TestCase):
    def test_refetch_matches_hash(self) -> None:
        reg = _reg(source_hash=hashlib.md5(DATA).hexdigest())
        with tempfile.TemporaryDirectory() as d:
            p = MF.fetch_press(reg["art_a_press"], Path(d), getter=lambda u: DATA)
            self.assertEqual(p.read_bytes(), DATA)
            self.assertEqual(MF.fetch_press(reg["art_a_press"], Path(d), getter=lambda u: 1 / 0), p)   # 있으면 받지 않는다

    def test_changed_or_unreachable_is_clear_error(self) -> None:
        reg = _reg(source_hash=hashlib.md5(DATA).hexdigest())
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(MF.MediaFetchError, "보도 인용 — 재수집 불가.*md5"):
                MF.fetch_press(reg["art_a_press"], Path(d), getter=lambda u: b"other")

            def boom(u: str) -> bytes:
                raise OSError("403")

            with self.assertRaisesRegex(MF.MediaFetchError, "보도 인용 — 재수집 불가.*받지 못했다"):
                MF.fetch_press(reg["art_a_press"], Path(d), getter=boom)

    def test_run_no_keyerror_on_press_item(self) -> None:
        reg = _reg(source_hash=hashlib.md5(DATA).hexdigest())
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "media").mkdir()
            rep = MF.run(Path(d), only=["art_a_press"], sheets=False, registry=reg, getter=lambda u: DATA)
            self.assertEqual(rep["assets"]["art_a_press"]["kind"], "press_photo")


class NotesDuplicateKeyTest(_Proj):
    def test_duplicate_sentence_key_is_error(self) -> None:
        (self.proj / MT.NOTES_FILE).write_text("schema_version: 1\nsentences:\n  review_0:\n    photo: 첫 사유입니다\n"
                                               "  review_0:\n    article: 둘째 사유입니다\n", encoding="utf-8")
        with self.assertRaisesRegex(MT.MediaTableError, "같은 키가 두 번"):
            MT.load_notes(self.proj)
        (self.proj / MT.NOTES_FILE).write_text(yaml.safe_dump({"schema_version": 1, "sentences": {"review_0": {"photo": "첫 사유입니다"}}},
                                                              allow_unicode=True), encoding="utf-8")
        self.assertEqual(MT.load_notes(self.proj).sentences["review_0"].photo, "첫 사유입니다")


if __name__ == "__main__":
    unittest.main()
