"""terrain3d 3D 렌더 재현성 fixture 만들기(v7.4.0 back_and_forth D-0614 ②) — 한 번 만들고 커밋한다.

    python tests/fixtures/terrain3d/make_fixture.py <scene_dir>   # scene_dir = sketch.war.terrain3d 가 쓴 out/terrain3d

scene_dir 의 scene.json·height.json·texture.png 를 작게 줄여(427×240, 높이 격자 1/4, 프레임 3 — 내려다보기 90°·중간·규칙 고도각)
이 폴더에 scene/ 로 두고, tools/terrain3d/render.js 로 렌더한 결과를 expected/ 에 둔다. text_in_engine = true(본편 경로, 라벨 좌표 labels.json).
시험 tests/test_terrain3d_render.py 가 같은 scene 을 다시 렌더해 평균 절대 화소 차 ≤ rules qa_checks.terrain3d_render_mad_max 를 잰다.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
TOOL = REPO / "tools" / "terrain3d"
W, H = 427, 240
STEP = 4


def shrink(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    s = json.loads((src / "scene.json").read_text(encoding="utf-8"))
    h = json.loads((src / "height.json").read_text(encoding="utf-8"))
    nx, ny = h["nx"], h["ny"]
    xs, ys = list(range(0, nx, STEP)), list(range(0, ny, STEP))
    if xs[-1] != nx - 1:
        xs.append(nx - 1)
    if ys[-1] != ny - 1:
        ys.append(ny - 1)
    hh = [h["h"][j * nx + i] for j in ys for i in xs]
    (dst / "height.json").write_text(json.dumps({"nx": len(xs), "ny": len(ys), "h": hh}), encoding="utf-8")
    Image.open(src / "texture.png").convert("RGB").resize((W * 2, H * 2), Image.LANCZOS).save(dst / "texture.png")
    el = s["camera"]["elev_deg"]
    s.update(width=W, height=H, text_in_engine=True,
             frames=[{"az": s["frames"][0]["az"], "elev": 90.0}, {"az": s["frames"][0]["az"], "elev": (90.0 + el) / 2},
                     {"az": s["frames"][0]["az"] + 30.0, "elev": el}])
    for u in s["units"]:   # 본편 경로 — 병종 그림은 엔진이 그린다(빌보드 파일 없음, 라벨 기록에 이름만)
        g = u.pop("glyph", None)
        u["glyph_name"] = g[len("glyph_"):-len(".png")] if g else None
    (dst / "scene.json").write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")


def render(scene_dir: Path) -> None:
    shutil.rmtree(scene_dir / "frames", ignore_errors=True)
    npm_root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    import os  # noqa: PLC0415

    subprocess.run(["node", str(TOOL / "render.js"), str(scene_dir)], check=True, cwd=TOOL, env={**os.environ, "NODE_PATH": npm_root})


def main(argv: list[str]) -> int:
    src = Path(argv[0])
    scene = HERE / "scene"
    shrink(src, scene)
    render(scene)
    exp = HERE / "expected"
    shutil.rmtree(exp, ignore_errors=True)
    shutil.copytree(scene / "frames", exp)
    shutil.rmtree(scene / "frames")
    print(sorted(p.name for p in exp.iterdir()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
