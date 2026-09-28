"""지오 티어 해상도 (v3.6.0, back_and_forth D-0066 작업 3, 19 §6 "티어 ppd 2.25배").

`python -m geo.prep <proj> --res 1080p` → assets/res_1080p/(ppd × k, 줌 + round(log2 k)). 480p 자산은 그대로.
엔진은 기본이 아닌 프로파일이면 그 폴더에서만 티어를 읽는다(없으면 오류 — 480p 를 늘려 쓰지 않는다).
"""

from __future__ import annotations

import pickle
import tempfile
import unittest
from pathlib import Path

from engine.assets import AssetError, Assets
from geo.prep import TierConf, assets_dir, res_spec


class ResSpecTest(unittest.TestCase):
    def test_identity_k1(self) -> None:
        tc = TierConf(name="W", ppd=24, z=5, bbox=(28.0, -12.0, 140.0, 48.0))
        self.assertEqual(res_spec(tc, 1.0), tc.spec())

    def test_1080(self) -> None:
        w = res_spec(TierConf(name="W", ppd=24, z=5, bbox=(28.0, -12.0, 140.0, 48.0)), 2.25)
        g = res_spec(TierConf(name="G", ppd=96, z=7, bbox=(46.0, 20.5, 62.0, 32.5)), 2.25)
        self.assertEqual((w.ppd, w.z, g.ppd, g.z), (54, 6, 216, 8))
        self.assertEqual((w.lon0, w.lat1), (28.0, 48.0))   # 경계(도)는 그대로

    def test_dirs(self) -> None:
        p = Path("/x")
        self.assertEqual(assets_dir(p, None), p / "assets")
        self.assertEqual(assets_dir(p, "1080p"), p / "assets" / "res_1080p")


class AssetsResTest(unittest.TestCase):
    def test_missing_res_tiers_loud(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "assets").mkdir()
            with self.assertRaises(AssetError) as cm:
                Assets(Path(d), None, "1080p")  # type: ignore[arg-type]
            self.assertIn("--res 1080p", str(cm.exception))

    def test_bounds_mismatch_loud(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "assets"
            (a / "res_1080p").mkdir(parents=True)
            t = {"W": {"lon0": 0.0, "lon1": 10.0, "lat0": 0.0, "lat1": 10.0, "levels": []}}
            pickle.dump(t, open(a / "tiers.pkl", "wb"))
            pickle.dump({"W": {**t["W"], "lon1": 11.0}}, open(a / "res_1080p" / "tiers.pkl", "wb"))
            with self.assertRaises(AssetError):
                Assets(Path(d), None, "1080p")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
