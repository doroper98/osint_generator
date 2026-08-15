"""수집한 인물 원본 사진을 한 장의 컨택트 시트로 묶어 육안 검수용으로 만든다.

라이선스가 통과해도 **구도가 안 맞으면 못 쓴다** (군중 사진, 측면, 저해상도 등).
가공 프롬프트를 만들기 전에 사람이 한 번에 보고 판정하기 위한 도구.

사용::

    python assets/library/workshop/make_contact_sheet.py
"""

from __future__ import annotations

import json
import pathlib

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
REFS = HERE / "references"
MANIFEST = REFS / "photo_manifest.json"
OUT = HERE / "contact_sheet_portraits.png"

COLS = 5
CELL_W, CELL_H = 380, 460
PAD = 14
LABEL_H = 74
BG = (28, 26, 23)
FG = (244, 239, 227)
WARN = (214, 108, 92)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("malgun.ttf", "malgunbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> int:
    people = json.loads(MANIFEST.read_text(encoding="utf-8"))["people"]
    items = sorted(people.items())
    rows = (len(items) + COLS - 1) // COLS

    sheet_w = COLS * CELL_W + (COLS + 1) * PAD
    sheet_h = rows * (CELL_H + LABEL_H) + (rows + 1) * PAD + 56
    sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
    draw = ImageDraw.Draw(sheet)

    f_title = _font(28)
    f_name = _font(22)
    f_meta = _font(16)

    draw.text((PAD, 16), f"코어 인물 원본 검수 시트 — {len(items)}인", font=f_title, fill=FG)

    for i, (pid, rec) in enumerate(items):
        r, c = divmod(i, COLS)
        x = PAD + c * (CELL_W + PAD)
        y = 56 + PAD + r * (CELL_H + LABEL_H + PAD)

        path = REFS / rec["local_file"]
        try:
            img = Image.open(path).convert("RGB")
            w, h = img.size
            img.thumbnail((CELL_W, CELL_H), Image.LANCZOS)
            sheet.paste(img, (x + (CELL_W - img.width) // 2, y + (CELL_H - img.height) // 2))
            size_note = f"{w}x{h}"
            small = min(w, h) < 500
        except Exception as e:  # noqa: BLE001
            draw.rectangle([x, y, x + CELL_W, y + CELL_H], outline=WARN, width=2)
            draw.text((x + 10, y + 10), f"열기 실패\n{type(e).__name__}", font=f_meta, fill=WARN)
            size_note, small = "?", True

        ty = y + CELL_H + 6
        draw.text((x, ty), f"{rec['name_ko']}", font=f_name, fill=FG)
        draw.text((x, ty + 26), f"{pid}", font=f_meta, fill=(150, 143, 128))
        draw.text(
            (x, ty + 46),
            f"{size_note}  ·  {rec['license'][:18]}",
            font=f_meta,
            fill=WARN if small else (150, 143, 128),
        )

    sheet.save(OUT, optimize=True)
    print(f"[contact-sheet] {OUT}  ({sheet.width}x{sheet.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
