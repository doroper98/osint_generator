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


def _masked_md5(p: Path, box: list[float], pad: int) -> str:
    """도장 상자(+pad)를 0 으로 가린 RGB 픽셀 md5 — 버전 도장 문자열(VERSION)과 무관한 대조(v5.1.0 D-0124)."""
    import math  # noqa: PLC0415

    import numpy as np  # noqa: PLC0415
    from PIL import Image  # noqa: PLC0415

    a = np.array(Image.open(p).convert("RGB"))
    x0, y0 = math.floor(box[0]) - pad, math.floor(box[1]) - pad
    x1, y1 = math.ceil(box[2]) + pad, math.ceil(box[3]) + pad
    a[y0:y1 + 1, x0:x1 + 1] = 0
    return hashlib.md5(a.tobytes()).hexdigest()


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
        self.assertEqual(len(chk["items"]), 36)   # v5.6.0 label_collision(hard) — 골든 0, v5.3.1 subtitle_overlap(hard), v5.3.0 D-0139 cascade(hard)·cascade_label_hidden(warning) — 지도 무대 골든 0, v5.2.0 D-0133 island_label_clip(hard)·island_label_overlap(warning), D-0129 backdrop_main_missing(hard)·card_island(warning) — 지도 무대 0, v5.1.0 D-0123·D-0126 backdrop_rights·backdrop_repeat·island_overlap(hard)·stage_choice(warning), D-0121 §A timeline_rescale(hard), v4.11.0 D-0118 static_window(warning), v4.10.0 D-0116 geo_mismatch(hard), v4.7.0 D-0107 boundary_as_route(hard)·geo_unsourced(warning), D-0106 endcard_roll(warning), v3.6.0 media_upscaled(warning)·glyph_size(hard), v4.1.0 stage_continuity(hard), v4.2.0 genre_elements(hard), v4.3.0 정직성 4(hard)
        self.assertEqual(next(i for i in chk["items"] if i["id"] == "stage_continuity")["count"], 0)
        for cid in ("backdrop_main_missing", "card_island", "island_label_clip", "island_label_overlap",
                    "cascade", "cascade_label_hidden", "subtitle_overlap"):   # v5.3.0 D-0139 — 골든에는 겹침 카드 없음   # v5.2.0 D-0129·D-0133 — 지도 무대(hormuz)는 새 검사 영향 0
            self.assertEqual(next(i for i in chk["items"] if i["id"] == cid)["count"], 0, cid)
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
        self.assertNotIn("series", prov)
        self.assertNotIn("cascade", prov)   # v5.3.0 D-0139 §3 — 겹침 카드를 쓰지 않은 영상(P5)   # v4.3.0 — 데이터 레코드를 그리지 않은 영상
        self.assertEqual(prov["render"]["resolution"]["profile"], "480p")   # v3.6.0 D-0066 작업 1
        self.assertEqual(prov["checks"]["hard"], chk["hard"])
        frames = json.loads((proj / "prev" / "frames.json").read_text(encoding="utf-8"))
        self.assertEqual(len(frames["frames"]), 25)
        # v4.1.0 D-0076 작업 6·8 — 무대 추상화 뒤에도 25컷 픽셀 동일(기준선 = KZ 수정 뒤 hormuz_baseline.json, D-0078)
        # v4.8.0 G7 — 기사 카드 조판·켄 번스 연속 변환(D-0101 §2·D-0104 D6)으로 바뀐 컷을 반영한 phaseG7 기준선(바뀐 컷 = changed_vs_g1)
        # v4.11.0 G10 — 글자 크기 2차 표(D-0118 §3, 자막 22·카드 line 16)로 바뀐 컷을 반영한 phaseG10 기준선(바뀐 컷 = changed_vs_g7)
        # v5.1.0 G12 — 엔딩 카드 버전 도장(D-0124)으로 바뀐 25_END 를 반영한 phaseG12 기준선. 도장은 VERSION 을 따르므로 그 컷은 도장 상자를 가린 md5
        # v5.4.0 G15 — 국경선 글로우 정규 승격(사용자 결정 2026-10-02)으로 25컷 전부 바뀐 phaseG15 기준선. 글로우 끄면 = phaseG12(기록)
        # v5.5.0 G16 — 인물 뱃지 정수리 원 안·이동 경로 고정점(사용자 지적 2026-10-02)으로 9컷 바뀐 phaseG16 기준선
        # v5.6.0 G17 — 뱃지 고정(badge_hold)·가운데 라벨 클램프로 2컷 바뀐 phaseG17 기준선(expected_deltas g17_badge_hold_label_clamp)
        base = json.loads((REPO / "docs" / "handoff" / "reports" / "phaseG17" / "hormuz_baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(prov.get("border_glow"), {"status": "adopted", "on": True})
        want = {c["png"]: c.get("md5_masked") or c["md5"] for c in base["cuts"]}
        masked = {c["png"] for c in base["cuts"] if c.get("mask")}
        got = {p.name: (_masked_md5(p, base["stamp_box"], base["mask_pad_px"]) if p.name in masked else hashlib.md5(p.read_bytes()).hexdigest())
               for p in (proj / "prev").glob("p_*.png")}
        self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()
