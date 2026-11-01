"""작품 비율 보존(contain) + 스케치 작품 레코드 공용 레지스트리 이관(v7.4.0 back_and_forth D-0608 §1-3).

- period_art·document 는 tool.params.fit contain + matte 필수(자르지 않음). 사진은 fit 없으면 cover(옛 레코드 그대로). 그 밖 값 = 오류.
- contain 가공은 원본 비율 그대로 틀 안에 넣는다(남는 자리 = matte).
- 칸나이 작품 4점은 공용 레지스트리(assets/media/media_registry.json)에 있고, 스케치 레코드와 권리·출처 칸이 같다(두 벌이 어긋나면 실패).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from engine.media_registry import load_media_registry
from tests.anti_inertia._ast_util import REPO
from tools.media_fetch import MediaFetchError, photo_fit, process_photo

ART = ("cannae_coin", "cannae_bust", "cannae_trumbull", "cannae_closs")
SAME = ("kind", "title", "url", "license", "photo_license", "work_license", "author", "credit_author", "source_hash", "created",
        "work_kind", "holder", "rights_status", "license_tags")
PRM = {"crop": [720, 450], "color": 1.0, "contrast": 1.0, "jpeg_quality": 92}


class PhotoFitTest(unittest.TestCase):
    def test_rules(self) -> None:
        self.assertEqual(photo_fit("photo", {}), "cover")
        self.assertEqual(photo_fit("period_art", {"fit": "contain", "matte": [0, 0, 0]}), "contain")
        for kind, prm in (("period_art", {}), ("period_art", {"fit": "cover"}), ("document", {"fit": "contain"}),
                          ("photo", {"fit": "stretch"}), ("photo", {"fit": "contain"})):
            with self.subTest(kind=kind, prm=prm), self.assertRaises(MediaFetchError):
                photo_fit(kind, prm)

    def test_contain_keeps_aspect(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "a.png", Path(d) / "b.jpg"
            Image.new("RGB", (200, 400), (250, 250, 250)).save(src)
            process_photo(src, out, {**PRM, "matte": [0, 0, 0]}, "contain")
            im = Image.open(out).convert("L")
            self.assertEqual(im.size, (720, 450))
            cols = [x for x in range(720) if im.getpixel((x, 225)) > 128]
            self.assertAlmostEqual(cols[-1] - cols[0] + 1, 225, delta=3)   # 450 × 200/400
            self.assertLess(im.getpixel((5, 225)), 30)                        # 남는 자리 = matte


class ArtRegistryTest(unittest.TestCase):
    def test_cannae_art_in_shared_registry_contain(self) -> None:
        reg = load_media_registry()
        for k in ART:
            with self.subTest(k=k):
                a = reg[k]
                self.assertEqual((a.kind, a.tool.name), ("period_art", "media_fetch.photo"))
                self.assertEqual(photo_fit(a.kind, a.tool.params), "contain")

    def test_sketch_records_match_shared(self) -> None:
        sk = json.loads((REPO / "projects" / "cannae_sketch" / "media.json").read_text(encoding="utf-8"))
        sk = sk.get("assets") or sk
        shared = json.loads((REPO / "assets" / "media" / "media_registry.json").read_text(encoding="utf-8"))["assets"]
        for k in ART:
            for f in SAME:
                with self.subTest(k=k, f=f):
                    self.assertEqual(sk[k].get(f), shared[k].get(f))


if __name__ == "__main__":
    unittest.main()
