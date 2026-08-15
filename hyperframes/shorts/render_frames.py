"""데모 컴포지션의 특정 시점 프레임을 PNG 로 뽑는다 (mp4 전 조판 검수).

GSAP 타임라인을 `seek()` 으로 원하는 시점에 세우고 스크린샷한다. mp4 렌더는
분 단위인데 조판 오류는 프레임 하나로 잡히므로, 왕복 비용을 줄인다.

사용::

    python hyperframes/shorts/render_frames.py
    python hyperframes/shorts/render_frames.py -t 2 8 16 24 --guides
"""

from __future__ import annotations

import argparse
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
INDEX = HERE / "index.html"
OUT_DIR = HERE / "frames"
CHROMIUM_FALLBACK = "/opt/pw-browsers/chromium"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-t", "--times", type=float, nargs="*",
                    default=[1.6, 6.0, 13.0, 22.0, 30.0])
    ap.add_argument("--guides", action="store_true")
    ap.add_argument("--sheet", action="store_true", help="프레임을 한 장으로 묶기")
    args = ap.parse_args()

    from playwright.sync_api import Error as PWError
    from playwright.sync_api import sync_playwright

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    url = INDEX.as_uri() + ("?guides=1" if args.guides else "")
    made = []

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except PWError:
            browser = pw.chromium.launch(executable_path=CHROMIUM_FALLBACK)
        page = browser.new_page(viewport={"width": 1080, "height": 1920},
                                device_scale_factor=1)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        page.goto(url, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(400)

        info = page.evaluate("""() => {
            const t = (window.__timelines || {})["shorts-demo"];
            return { found: !!t, dur: t ? t.duration() : 0,
                     imgs: [...document.images].filter(i => !i.complete || !i.naturalWidth)
                             .map(i => i.getAttribute("src")) };
        }""")
        print(f"[timeline] found={info['found']} duration={info['dur']:.2f}s")
        if info["imgs"]:
            print(f"[warn] 로드 실패 이미지: {info['imgs']}")

        for t in args.times:
            page.evaluate(f"""() => {{
                const tl = (window.__timelines || {{}})["shorts-demo"];
                if (tl) tl.seek({t});
            }}""")
            page.wait_for_timeout(180)
            p = OUT_DIR / f"t{t:05.1f}.png"
            page.screenshot(path=str(p), type="png")
            made.append((t, p))
            print(f"  + {p.name}")

        browser.close()

    if errors:
        print(f"[warn] page errors: {errors[:5]}")

    if args.sheet and made:
        from PIL import Image, ImageDraw, ImageFont

        cw, ch, pad = 330, 587, 12
        sheet = Image.new("RGB", (len(made) * (cw + pad) + pad, ch + 60), (24, 22, 20))
        d = ImageDraw.Draw(sheet)
        try:
            f = ImageFont.truetype("malgun.ttf", 20)
        except OSError:
            f = ImageFont.load_default()
        d.text((pad, 14), "쇼츠 데모 프레임 — 시점별 조판", font=f, fill=(244, 239, 227))
        for i, (t, p) in enumerate(made):
            im = Image.open(p).convert("RGB")
            im.thumbnail((cw, ch), Image.LANCZOS)
            x = pad + i * (cw + pad)
            sheet.paste(im, (x, 46))
            d.text((x, 46 + ch + 4), f"t={t:.1f}s", font=f, fill=(244, 239, 227))
        out = HERE / "frames_sheet.png"
        sheet.save(out, optimize=True)
        print(f"[sheet] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
