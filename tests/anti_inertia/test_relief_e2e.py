"""relief e2e — 골든 원고·연출을 direction 테마 relief 로 고른 렌더가 phaseD0608 기준선과 같은가 (v7.4.0, back_and_forth D-0608 §1-3).

relief(전쟁사 릴리프, 사용자 UF-250·UF-253)를 본편 무대 테마 목록(GeoThemes.names)에 올리면서 단 장치다. light e2e(test_q3_light_e2e)와 같은 꼴:
`projects/hormuz_korea` 를 임시 폴더에 링크로 펼치고 direction 의 stage_config.mercator 만 relief(사유 포함)로 바꾼다.
`geo.prep --theme relief` 로 assets/theme_relief 를 만든 뒤 `engine.render --preview golden` → 25컷 md5(도장 가림) =
`docs/handoff/reports/phaseD0608/hormuz_relief_baseline.json`. provenance map_theme(relief·direction), 장르(지정학 = light)와 달라
[map-theme-override] warning 이 남고, 지도 대비 hard 0. 자산이 없는 컨테이너에서는 오류로 실패한다(조용히 넘어가지 않는다).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from tests.anti_inertia._ast_util import REPO
from tests.anti_inertia.test_provenance_e2e import PREP, _masked_md5

SRC = REPO / "projects" / "hormuz_korea"
SKIP_TOP = {"prev", "prev_animatic", "out", "direction.yaml", "assets"}
BASELINE = REPO / "docs/handoff/reports/phaseD0608/hormuz_relief_baseline.json"
RELIEF = """stage_config:   # relief e2e(D-0608 §1-3) — 원본과 이 블록만 다름
  mercator:
    theme: relief
    theme_reason: relief 기준선(D-0608 §1-3) — 골든 원고·연출의 릴리프 지도 판
    map_layers: []
    map_layers_reason: v3 골든 사용자 합격본 — D-0231
"""


def relief_project(dst: Path) -> Path:
    """원본을 링크로 펼친 relief 사본(assets 는 하위 항목 링크 + 새 theme_relief)."""
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
    (dst / "direction.yaml").write_text(head + RELIEF + rest[rest.index("\nplaces:") + 1:], encoding="utf-8")
    return dst


def render_relief(proj: Path) -> dict:
    """geo.prep --theme relief → engine.render --preview golden. 마지막 줄 JSON(결과)을 돌려준다. 실패 = RuntimeError."""
    run = None
    for cmd in ([sys.executable, "-m", "geo.prep", str(proj), "--theme", "relief"],
                [sys.executable, "-m", "engine.render", str(proj), "--preview", "golden"]):
        run = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, env={**os.environ})
        if run.returncode != 0:
            raise RuntimeError(f"{cmd[2]} 실패 rc={run.returncode}\n{run.stdout[-2000:]}{run.stderr[-2000:]}")
    return json.loads(run.stdout.strip().splitlines()[-1])


def cut_md5s(proj: Path, base: dict) -> dict[str, str]:
    masked = {c["png"] for c in base["cuts"] if c.get("mask")}
    return {p.name: (_masked_md5(p, base["stamp_box"], base["mask_pad_px"]) if p.name in masked else hashlib.md5(p.read_bytes()).hexdigest())
            for p in (proj / "prev").glob("p_*.png")}


@pytest.mark.slow   # C8.3(D187) — 느린 묶음(빠른 묶음 -m "not slow" 밖)
class ReliefE2ETest(unittest.TestCase):
    def test_relief_preview_matches_baseline(self) -> None:
        if not (SRC / "assets" / "geo.pkl").exists() or not (SRC / "plan.json").exists():
            raise RuntimeError(PREP)
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as d:
            proj = relief_project(Path(d) / "hormuz_korea")   # 프로젝트 id 는 원본과 같다 — 시리즈 레지스트리 조회 같음
            res = render_relief(proj)
            self.assertTrue([w for w in res["warnings"] if "map-theme-override" in w])   # 지정학 장르 기본 = light → relief 는 덮어쓰기
            prov = json.loads((proj / "prev" / "provenance.json").read_text(encoding="utf-8"))
            chk = json.loads((proj / "prev" / "checks.json").read_text(encoding="utf-8"))
            self.assertEqual(prov["map_theme"]["effective"], "relief")
            self.assertEqual(next(i for i in chk["items"] if i["id"] == "map_contrast")["count"], 0)
            self.assertEqual(cut_md5s(proj, base), {c["png"]: c.get("md5_masked") or c["md5"] for c in base["cuts"]})
            shutil.rmtree(proj / "assets" / "theme_relief", ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
