"""Q3 light e2e — 골든 원고·연출을 direction 테마 light 로 고른 렌더가 phaseQ3 기준선과 같은가 (v5.18.0, D-0161 §5·D-0172).

`projects/hormuz_korea` 를 임시 폴더에 링크로 펼치고 direction 의 stage_config.mercator 만 light(사유 포함)로 바꾼다.
`geo.prep --theme light` 로 assets/theme_light 를 만든 뒤 `engine.render --preview golden` → 25컷 md5(25_END 도장 가림) =
`docs/handoff/reports/phaseD0306/hormuz_light_baseline.json`(v7.4.0 D-0306 재기준, 옛 phaseQ3). provenance map_theme(light·direction·장르와 같아 override warning 없음),
지도 대비 hard 0. 자산이 없는 컨테이너에서는 test_provenance_e2e 처럼 **오류로 실패**한다(조용히 넘어가지 않는다).
"""

from __future__ import annotations

import pytest
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.anti_inertia._ast_util import REPO
from tests.anti_inertia.test_provenance_e2e import PREP, _masked_md5

SRC = REPO / "projects" / "hormuz_korea"
SKIP_TOP = {"prev", "prev_animatic", "out", "direction.yaml", "assets"}
LIGHT = """stage_config:   # Q3 light e2e(D-0161 §5) — 원본과 이 블록만 다름
  mercator:
    theme: light
    theme_reason: Q3 light 기준선(D-0161 §5) — 골든 원고·연출의 밝은 지도 판
    map_layers: []
    map_layers_reason: v3 골든 사용자 합격본 — D-0231
"""


def light_project(dst: Path) -> Path:
    """원본을 링크로 펼친 light 사본(assets 는 하위 항목 링크 + 새 theme_light)."""
    dst.mkdir()
    for p in SRC.iterdir():
        if p.name not in SKIP_TOP:
            (dst / p.name).symlink_to(p)
    (dst / "assets").mkdir()
    for p in (SRC / "assets").iterdir():
        if not p.name.startswith("theme_"):
            (dst / "assets" / p.name).symlink_to(p)
    text = (SRC / "direction.yaml").read_text(encoding="utf-8")
    head, rest = text.split("stage_config:", 1)
    (dst / "direction.yaml").write_text(head + LIGHT + rest[rest.index("\nplaces:") + 1:], encoding="utf-8")
    return dst


@pytest.mark.slow   # C8.3(D187) — 느린 묶음(빠른 묶음 -m "not slow" 밖)
class LightE2ETest(unittest.TestCase):
    def test_light_preview_matches_baseline(self) -> None:
        if not (SRC / "assets" / "geo.pkl").exists() or not (SRC / "plan.json").exists():
            raise RuntimeError(PREP)
        env = {**os.environ}
        with tempfile.TemporaryDirectory() as d:
            proj = light_project(Path(d) / "hormuz_korea")   # 프로젝트 id(폴더 이름)는 원본과 같다 — 시리즈 레지스트리 조회 같음
            for cmd in ([sys.executable, "-m", "geo.prep", str(proj), "--theme", "light"],
                        [sys.executable, "-m", "engine.render", str(proj), "--preview", "golden"]):
                run = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, env=env)
                self.assertEqual(run.returncode, 0, run.stdout[-2000:] + run.stderr[-2000:])
            res = json.loads(run.stdout.strip().splitlines()[-1])
            self.assertFalse([w for w in res["warnings"] if "map-theme-override" in w])   # light = 장르 기본값
            prov = json.loads((proj / "prev" / "provenance.json").read_text(encoding="utf-8"))
            chk = json.loads((proj / "prev" / "checks.json").read_text(encoding="utf-8"))
            self.assertEqual(prov["map_theme"]["effective"], "light")
            self.assertEqual(next(i for i in chk["items"] if i["id"] == "map_contrast")["count"], 0)
            # v7.4.0 D-0306 — card 7개 삭제로 7컷 바뀐 phaseD0306 기준선(changed_vs_prev). 옛 기준선 = phaseQ3
            base = json.loads((REPO / "docs/handoff/reports/phaseD0306/hormuz_light_baseline.json").read_text(encoding="utf-8"))
            want = {c["png"]: c.get("md5_masked") or c["md5"] for c in base["cuts"]}
            masked = {c["png"] for c in base["cuts"] if c.get("mask")}
            got = {p.name: (_masked_md5(p, base["stamp_box"], base["mask_pad_px"]) if p.name in masked else hashlib.md5(p.read_bytes()).hexdigest())
                   for p in (proj / "prev").glob("p_*.png")}
            self.assertEqual(got, want)
            shutil.rmtree(proj / "assets" / "theme_light", ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
