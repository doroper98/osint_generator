"""tools/golden_delta_proof — 바뀐 픽셀의 요소 영역 안/밖 판정 (v4.8.0, back_and_forth D-0101 작업 4)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from golden_delta_proof import prove  # noqa: E402


class ProveTest(unittest.TestCase):
    def test_inside_outside(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "ref").mkdir()
            (d / "new").mkdir()
            a = np.zeros((480, 854, 3), np.uint8)
            b = a.copy()
            b[100:120, 100:120] = 255      # 요소 상자 안
            b[300:302, 700:705] = 255      # 밖(10 px)
            Image.fromarray(a).save(d / "ref" / "p_0001.00.png")
            Image.fromarray(b).save(d / "new" / "p_0001.00.png")
            Image.fromarray(a).save(d / "ref" / "p_0002.00.png")
            Image.fromarray(a).save(d / "new" / "p_0002.00.png")
            (d / "boxes.json").write_text(json.dumps({"p_0001.00.png": [[90, 90, 130, 130]]}), encoding="utf-8")
            rep = prove(d / "ref", d / "new", [d / "boxes.json"], d / "out")
            self.assertEqual(rep["changed_cuts"], 1)
            c = rep["cuts"][0]
            self.assertEqual((c["changed_px"], c["inside_px"], c["outside_px"]), (410, 400, 10))
            self.assertEqual(c["outside_bbox"], [700, 300, 704, 301])
            self.assertTrue((d / "out" / "p_0001.00_old_new_diff.png").exists())


if __name__ == "__main__":
    unittest.main()
