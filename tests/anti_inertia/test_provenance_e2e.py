"""test_provenance_e2e — "이번 영상에 쓰였다"를 산출물로 증명 (docs/handoff/15 P5, 19 부록 B).

`projects/hormuz_korea` 를 `engine.render --preview golden`(골든 25 앵커, 전편 렌더 없음)으로 돌려
`prev/provenance.json` 의 `features_used` 가 v3 기대값과 일치하고, 돌지 않은 단계가 false 로 적혔고
(`stages.render/mix/mux == False`), `drops == []` 인지 본다.

v3.0.0(back_and_forth D-0041, DECISIONS D40): preview 경로·기대값 실물 정정 — 뱃지 8(골든 연출 badge 이벤트 8개,
Phase 1~6.5 provenance 전부 8), 패널 relation(옛 refusal). 19 부록 B·15 §P5 의 "9"·"refusal" 은 문서 오기.
자산이 없는 컨테이너에서는 **오류로 실패**한다(A1 — 관성 방지 테스트는 준비 안 된 곳에서 조용히 넘어가지 않는다).
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest

from tests.anti_inertia._ast_util import REPO

EXPECTED_FEATURES: dict[str, object] = {
    "camera_moves": 5,
    "dips": 4,
    "badges": 8,
    "panels": ["relation", "statement", "timeline", "precedent", "versus"],
    "media": {"clip": 2, "photo": 2, "cutout": 1, "article": 2},
    "label_lod": True,
}
PREP = (
    "hormuz 자산이 없다 — docs/handoff/reports/phase6_5/run_log.md §0·§4 준비 절차:\n"
    "  python tools/fetch_data.py all && python tools/fetch_data.py people media\n"
    "  (assets·media 를 projects/hormuz_korea 로 복사) && python -m geo.prep projects/hormuz_korea\n"
    "  python -m script.plan projects/hormuz_korea --tts edge"
)


class ProvenanceE2ETest(unittest.TestCase):
    def test_hormuz_preview_provenance(self) -> None:
        proj = REPO / "projects" / "hormuz_korea"
        missing = [p for p in ("plan.json", "tts", "assets", "media") if not (proj / p).exists()]
        if missing:
            raise RuntimeError(f"{PREP}\n  없는 것: {', '.join(missing)}")
        run = subprocess.run([sys.executable, "-m", "engine.render", str(proj), "--preview", "golden"],
                             cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stdout[-2000:] + run.stderr[-2000:])
        prov = json.loads((proj / "prev" / "provenance.json").read_text(encoding="utf-8"))
        features = prov["features_used"]
        for key, value in EXPECTED_FEATURES.items():
            self.assertEqual(features.get(key), value, key)
        self.assertEqual(prov["drops"], [])
        self.assertEqual(prov["preview"]["frames"], 25)
        self.assertTrue(prov["stages"]["preview"])
        for not_run in ("render", "mix", "mux"):
            self.assertIs(prov["stages"][not_run], False, not_run)
        self.assertTrue((proj / "prev" / "sheet.jpg").exists())
        chk = json.loads((proj / "prev" / "checks.json").read_text(encoding="utf-8"))   # v3.1.0 17 §3(D-0047 작업 6)
        self.assertEqual(len(chk["items"]), 13)   # v3.6.0 media_upscaled(warning)·glyph_size(hard), v4.1.0 stage_continuity(hard)
        self.assertEqual(next(i for i in chk["items"] if i["id"] == "stage_continuity")["count"], 0)
        self.assertEqual(prov["stage"], {"name": "mercator", "declared": False, "shots_declared": 0, "instances": {"mercator": 1}})   # D-0076 작업 7
        self.assertEqual(prov["render"]["resolution"]["profile"], "480p")   # v3.6.0 D-0066 작업 1
        self.assertEqual(prov["checks"]["hard"], chk["hard"])
        frames = json.loads((proj / "prev" / "frames.json").read_text(encoding="utf-8"))
        self.assertEqual(len(frames["frames"]), 25)


if __name__ == "__main__":
    unittest.main()
