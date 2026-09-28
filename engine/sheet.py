"""프리뷰 컨택트 시트 격자 (v3.0.0, 16 §4 preview → prev/sheet.jpg, docs/handoff/11 §5).

`tools/contact_sheet.py`(v2.0.1) 의 격자 함수를 엔진으로 옮겼다 — preview 단계와 리포트 도구가 같은 함수를 쓴다.
"""

from __future__ import annotations

from pathlib import Path

CELL = (427, 240)
LABEL_H = 22
COLS = 4
BG = (24, 24, 30)
LABEL_RGB = (255, 220, 90)
LABEL_PAD = (6, 5)
JPEG_QUALITY = 88


def grid(cells: list[tuple["object", str]], cols: int, dest: Path, cell: tuple[int, int] = CELL) -> None:
    """(이미지, 라벨) 목록 → cols 열 격자 JPEG."""
    from PIL import Image, ImageDraw  # noqa: PLC0415

    cw, ch = cell
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, (ch + LABEL_H) * rows), BG)
    d = ImageDraw.Draw(sheet)
    for i, (im, label) in enumerate(cells):
        x, y = (i % cols) * cw, (i // cols) * (ch + LABEL_H)
        sheet.paste(im.convert("RGB").resize((cw, ch)), (x, y + LABEL_H))   # type: ignore[attr-defined]
        d.text((x + LABEL_PAD[0], y + LABEL_PAD[1]), label, fill=LABEL_RGB)
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, quality=JPEG_QUALITY)
