"""쇼츠 타이포그라피 스페시먼(`specimen_typo.html`)을 1080×1920 PNG 로 굽는다.

최종 렌더러(HyperFrames = HTML+GSAP)와 **같은 기술로 조판·래스터라이즈**하는 것이
목적이라, 헤드리스 크로미엄(Playwright)으로 실제 페이지를 띄워 스크린샷을 뜬다.
폰트가 폴백 고딕으로 떨어지면 검수가 무의미하므로 `document.fonts.ready` 를 기다린
뒤 실제 사용 폰트 패밀리를 함께 보고한다.

배경 갱지는 `workers.engraving_stylizer.make_crumpled_paper` 로 **결정론 생성**해
`assets/paper_crumpled_1080x1920.png` 에 캐시한다(같은 seed → 같은 바이트).

사용::

    python hyperframes/shorts/render_specimen.py [-o 출력.png] [--guides]
"""

from __future__ import annotations

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CANVAS_W = 1080
CANVAS_H = 1920
PAPER_SEED = 20260814
PAPER_PATH = HERE / "assets" / "paper_crumpled_1080x1920.png"
SPECIMEN_PATH = HERE / "specimen_typo.html"
CHROMIUM_FALLBACK = "/opt/pw-browsers/chromium"


def ensure_paper(force: bool = False) -> pathlib.Path:
    """갱지 배경 텍스처를 결정론 생성한다(이미 있으면 재사용)."""
    if PAPER_PATH.exists() and not force:
        return PAPER_PATH

    from workers.engraving_stylizer import make_crumpled_paper

    PAPER_PATH.parent.mkdir(parents=True, exist_ok=True)
    image = make_crumpled_paper(
        CANVAS_W, CANVAS_H, seed=PAPER_SEED, amplitude=0.048, creases=96
    )
    image.save(PAPER_PATH, format="PNG", optimize=True)
    print(f"[paper] generated {PAPER_PATH} (seed={PAPER_SEED})")
    return PAPER_PATH


def render(out_path: pathlib.Path, guides: bool = False) -> pathlib.Path:
    """스페시먼을 1080×1920 PNG 로 렌더한다."""
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    url = SPECIMEN_PATH.as_uri() + ("?guides=1" if guides else "")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except PlaywrightError:
            browser = pw.chromium.launch(executable_path=CHROMIUM_FALLBACK)

        page = browser.new_page(
            viewport={"width": CANVAS_W, "height": CANVAS_H},
            device_scale_factor=1,
        )
        errors: list[str] = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto(url, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(400)

        # 폰트 검수 — 폴백 고딕으로 떨어졌는지 여기서 잡는다.
        report = page.evaluate(
            """() => {
                const seen = new Set();
                for (const f of document.fonts) {
                    if (f.status === 'loaded') seen.add(f.family);
                }
                const pick = (sel) => {
                    const el = document.querySelector(sel);
                    return el ? getComputedStyle(el).fontFamily : null;
                };
                return {
                    loaded: [...seen],
                    headline: pick('.headline'),
                    body: pick('.body'),
                    paperTitle: pick('.paper-title'),
                    cards: [...document.querySelectorAll('.card')].map((c) => {
                        const r = c.getBoundingClientRect();
                        return {
                            id: c.id,
                            top: Math.round(r.top),
                            bottom: Math.round(r.bottom),
                            overflow: c.scrollHeight - c.clientHeight,
                        };
                    }),
                };
            }"""
        )
        page.screenshot(path=str(out_path), type="png")
        browser.close()

    print(f"[fonts] loaded={report['loaded']}")
    print(f"[fonts] headline={report['headline']}")
    print(f"[fonts] body={report['body']}")
    print(f"[fonts] paper-title={report['paperTitle']}")
    for card in report["cards"]:
        print(f"[card] {card}")
    if errors:
        print(f"[warn] page errors: {errors}")
    print(f"[render] {out_path}")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="쇼츠 타이포그라피 스페시먼 렌더")
    parser.add_argument("-o", "--out", default=str(HERE / "specimen_typo.png"))
    parser.add_argument("--guides", action="store_true", help="safe area 가이드 표시")
    parser.add_argument("--regen-paper", action="store_true", help="갱지 텍스처 재생성")
    args = parser.parse_args()

    ensure_paper(force=args.regen_paper)
    render(pathlib.Path(args.out), guides=args.guides)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
