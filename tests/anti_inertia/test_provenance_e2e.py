"""test_provenance_e2e — "이번 영상에 쓰였다"를 산출물로 증명 (docs/handoff/15 P5, 19 부록 B).

`projects/hormuz_korea` 를 `--preview` 모드(25 앵커 프레임)로 돌려 `out/provenance.json` 의
`features_used` 가 v3 기대값과 일치하고 `drops == []` 인지 본다.

Phase 0: 엔진·프로젝트 없음 → strict xfail. Phase 6.8 에서 해제.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest

import pytest

from tests.anti_inertia._ast_util import REPO

EXPECTED_FEATURES: dict[str, object] = {
    "camera_moves": 5,
    "dips": 4,
    "badges": 9,
    "panels": ["relation", "statement", "timeline", "precedent", "versus"],
    "media": {"clip": 2, "photo": 2, "cutout": 1, "article": 2},
    "label_lod": True,
}


class ProvenanceE2ETest(unittest.TestCase):
    @pytest.mark.xfail(strict=True, reason="Phase 6.8 — 엔진·engine_service·projects/hormuz_korea 미구현")
    def test_hormuz_preview_provenance(self) -> None:
        proj = REPO / "projects" / "hormuz_korea"
        self.assertTrue(proj.exists(), "projects/hormuz_korea 없음")
        subprocess.run(
            [sys.executable, "-m", "engine.render", str(proj), "--preview", "golden"],
            check=True, cwd=REPO,
        )
        prov = json.loads((proj / "out" / "provenance.json").read_text(encoding="utf-8"))
        features = prov["features_used"]
        for key, value in EXPECTED_FEATURES.items():
            self.assertEqual(features.get(key), value, key)
        self.assertEqual(prov["drops"], [])


if __name__ == "__main__":
    unittest.main()
