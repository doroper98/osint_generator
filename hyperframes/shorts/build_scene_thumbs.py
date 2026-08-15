"""씬별 조판 썸네일 생성 — 프리뷰 시트의 마지막 빈칸을 채운다.

프리뷰 시트(§6.0.1)의 씬 카드가 대사 텍스트만 있으면 "어떻게 보일지" 를 못 본다.
데모 컴포지션을 씬 시작 시점마다 캡처해 **실제 조판 썸네일**을 만든다 — 씬킷이
생긴 뒤에야 가능한 작업이다.

사용::

    python hyperframes/shorts/build_scene_thumbs.py
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

INDEX = HERE / "index.html"
PLAN_JSON = HERE / "scene_plan.json"
OUT_DIR = HERE / "thumbs"
CHROMIUM_FALLBACK = "/opt/pw-browsers/chromium"

PACE_OVERHEAD, PACE_PER_CHAR = 0.225, 0.1298
THUMB_W = 300


def est(text: str) -> float:
    return max(1.5, min(9.0, PACE_OVERHEAD + PACE_PER_CHAR * len(text)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenes", type=int, default=4,
                    help="데모가 만든 씬 수 (build_demo.py 와 같아야 함)")
    args = ap.parse_args()

    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    scenes = plan["scenes"][: args.scenes]

    # build_demo.py 와 **같은 식**으로 씬 시작 시각을 구한다.
    # 어긋나면 엉뚱한 시점을 캡처해 썸네일이 거짓말을 한다.
    starts, acc = [], 0.6
    for s in scenes:
        starts.append(acc)
        acc += sum(est(x) + 0.28 for x in s["lines"])

    # 씬 시작 직후가 아니라 **등장 모션이 끝난 뒤**를 잡는다 (페이드 중간 캡처 방지).
    shots = [(s["id"], t + 1.1) for s, t in zip(scenes, starts)]

    from playwright.sync_api import Error as PWError
    from playwright.sync_api import sync_playwright
    from PIL import Image

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    made = []

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except PWError:
            browser = pw.chromium.launch(executable_path=CHROMIUM_FALLBACK)
        page = browser.new_page(viewport={"width": 1080, "height": 1920},
                                device_scale_factor=1)
        page.goto(INDEX.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(400)

        for sid, t in shots:
            # seek 은 콜백을 억제하지만 자막은 opacity 트윈이라 영향 없다 (v1.2.0 학습).
            page.evaluate(f"""() => {{
                const tl = (window.__timelines || {{}})["shorts-demo"];
                if (tl) tl.seek({t});
            }}""")
            page.wait_for_timeout(160)
            full = OUT_DIR / f"_{sid}_full.png"
            page.screenshot(path=str(full), type="png")

            im = Image.open(full).convert("RGB")
            im.thumbnail((THUMB_W, THUMB_W * 1920 // 1080), Image.LANCZOS)
            dest = OUT_DIR / f"{sid}.png"
            im.save(dest, optimize=True)
            full.unlink(missing_ok=True)
            made.append((sid, t, dest))
            print(f"  + {dest.name:18} t={t:5.1f}s  {im.width}x{im.height}  "
                  f"{dest.stat().st_size:,}B")

        browser.close()

    print(f"\n[썸네일] {len(made)}장 → {OUT_DIR}")
    print("       다음: render_preview_sheet.py 가 씬 카드에 이 이미지를 싣는다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
