"""test_provenance_e2e — "이번 영상에 쓰였다"를 산출물로 증명 (docs/handoff/15 P5, 19 부록 B).

`projects/hormuz_korea` 를 `engine.render --preview golden`(골든 25 앵커, 전편 렌더 없음)으로 돌려
`prev/provenance.json` 의 `features_used` 가 v3 기대값과 일치하고, 돌지 않은 단계가 false 로 적혔고
(`stages.render/mix/mux == False`), `drops == []` 인지 본다.

v3.0.0(back_and_forth D-0041, DECISIONS D40): preview 경로·기대값 실물 정정 — 뱃지 8(골든 연출 badge 이벤트 8개,
Phase 1~6.5 provenance 전부 8), 패널 relation(옛 refusal). 19 부록 B·15 §P5 의 "9"·"refusal" 은 문서 오기.
자산이 없는 컨테이너에서는 **오류로 실패**한다(A1 — 관성 방지 테스트는 준비 안 된 곳에서 조용히 넘어가지 않는다).
"""

from __future__ import annotations

import hashlib
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
        self.assertEqual(len(chk["items"]), 23)   # v4.11.0 D-0118 static_window(warning), v4.10.0 D-0116 geo_mismatch(hard), v4.7.0 D-0107 boundary_as_route(hard)·geo_unsourced(warning), D-0106 endcard_roll(warning), v3.6.0 media_upscaled(warning)·glyph_size(hard), v4.1.0 stage_continuity(hard), v4.2.0 genre_elements(hard), v4.3.0 정직성 4(hard)
        self.assertEqual(next(i for i in chk["items"] if i["id"] == "stage_continuity")["count"], 0)
        self.assertEqual(next(i for i in chk["items"] if i["id"] == "genre_elements")["count"], 0)
        self.assertEqual(next(i for i in chk["items"] if i["id"] == "boundary_as_route")["count"], 0)   # v4.7.0 D-0107 D2(b)
        self.assertEqual(len(prov["geo"]["unsourced"]), 3)   # v4.10.0 D-0116 — places 8 은 지명 사전과 맞음, paths 2·인라인 route 1 만 남음
        self.assertEqual(next(i for i in chk["items"] if i["id"] == "geo_unsourced")["count"], 3)
        self.assertEqual(sorted(it["gazetteer"] for it in prov["geo"]["matched"]),   # 골든 좌표 무변경 — 전부 허용 오차 안
                         ["busan_kor", "gulf_of_aden", "irbil_irq", "kharg_island", "seoul_kor", "strait_of_hormuz", "ulsan_kor",
                          "us_embassy_seoul"])
        self.assertEqual(prov["geo"]["mismatch"], [])
        self.assertEqual(next(i for i in chk["items"] if i["id"] == "geo_mismatch")["count"], 0)
        self.assertEqual(prov["genre"], {"name": "geopolitics", "declared": False, "status": "approved"})   # v4.2.0 D-0081 작업 3, v4.3.0 status
        self.assertEqual(prov["stage"], {"name": "mercator", "declared": False, "shots_declared": 0, "instances": {"mercator": 1},
                                         "configs": {}})   # D-0076 작업 7, v4.3.0 configs(무대 설정 — 지도는 없음)
        self.assertNotIn("series", prov)   # v4.3.0 — 데이터 레코드를 그리지 않은 영상
        self.assertEqual(prov["render"]["resolution"]["profile"], "480p")   # v3.6.0 D-0066 작업 1
        self.assertEqual(prov["checks"]["hard"], chk["hard"])
        frames = json.loads((proj / "prev" / "frames.json").read_text(encoding="utf-8"))
        self.assertEqual(len(frames["frames"]), 25)
        # v4.1.0 D-0076 작업 6·8 — 무대 추상화 뒤에도 25컷 픽셀 동일(기준선 = KZ 수정 뒤 hormuz_baseline.json, D-0078)
        # v4.8.0 G7 — 기사 카드 조판·켄 번스 연속 변환(D-0101 §2·D-0104 D6)으로 바뀐 컷을 반영한 phaseG7 기준선(바뀐 컷 = changed_vs_g1)
        # v4.11.0 G10 — 글자 크기 2차 표(D-0118 §3, 자막 22·카드 line 16)로 바뀐 컷을 반영한 phaseG10 기준선(바뀐 컷 = changed_vs_g7)
        base = json.loads((REPO / "docs" / "handoff" / "reports" / "phaseG10" / "hormuz_baseline.json").read_text(encoding="utf-8"))
        got = {p.name: hashlib.md5(p.read_bytes()).hexdigest() for p in (proj / "prev").glob("p_*.png")}
        self.assertEqual(got, {c["png"]: c["md5"] for c in base["cuts"]})


if __name__ == "__main__":
    unittest.main()
