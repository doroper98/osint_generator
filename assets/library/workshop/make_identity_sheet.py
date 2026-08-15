"""원본 사진 ↔ codex 생성물을 나란히 놓는 **인물 동일성 검수 시트** (G4 기준 1).

생성물만 보면 "그럴듯한 흑백 초상"으로 보여 **딴사람이 된 것을 놓친다.** 얼굴 동일성은
원본과 대조해야만 판정된다 — 라이선스·해상도·구도 필터가 못 잡는 마지막 관문이다.

사용::

    python assets/library/workshop/make_identity_sheet.py
"""

from __future__ import annotations

import json
import pathlib

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
REFS = HERE / "references"
GEN = HERE / "output"
MANIFEST = REFS / "photo_manifest.json"
OUT = HERE / "contact_sheet_identity.png"

PAIR_W, PAIR_H = 300, 375     # 한 장 크기
GAP, PAD, LABEL = 8, 18, 52
COLS = 3                       # 쌍 기준 열 수
BG = (24, 22, 20)
FG = (244, 239, 227)
DIM = (150, 143, 128)


def _font(sz: int):
    for n in ("malgun.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(n, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def _fit(path: pathlib.Path, box: tuple[int, int]) -> Image.Image | None:
    try:
        im = Image.open(path).convert("RGB")
    except Exception:  # noqa: BLE001
        return None
    im.thumbnail(box, Image.LANCZOS)
    return im


def main() -> int:
    people = json.loads(MANIFEST.read_text(encoding="utf-8"))["people"]
    items = [
        (pid, rec) for pid, rec in sorted(people.items())
        if (GEN / f"{pid}_mono_v01.png").is_file()
    ]

    cell_w = PAIR_W * 2 + GAP
    rows = (len(items) + COLS - 1) // COLS
    sheet_w = COLS * cell_w + (COLS + 1) * PAD
    sheet_h = rows * (PAIR_H + LABEL) + (rows + 1) * PAD + 64

    sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
    d = ImageDraw.Draw(sheet)
    d.text((PAD, 14), f"인물 동일성 검수 — 원본(왼쪽) vs 생성물(오른쪽) · {len(items)}인",
           font=_font(26), fill=FG)
    d.text((PAD, 44), "판정 기준: 같은 사람으로 보이는가 (G4). 아니면 반려 후 재생성.",
           font=_font(16), fill=DIM)

    f_name, f_meta = _font(20), _font(15)
    for i, (pid, rec) in enumerate(items):
        r, c = divmod(i, COLS)
        x = PAD + c * (cell_w + PAD)
        y = 64 + PAD + r * (PAIR_H + LABEL + PAD)

        src = _fit(REFS / rec["local_file"], (PAIR_W, PAIR_H))
        gen = _fit(GEN / f"{pid}_mono_v01.png", (PAIR_W, PAIR_H))

        for j, im in enumerate((src, gen)):
            bx = x + j * (PAIR_W + GAP)
            if im is None:
                d.rectangle([bx, y, bx + PAIR_W, y + PAIR_H], outline=(200, 90, 80), width=2)
                continue
            sheet.paste(im, (bx + (PAIR_W - im.width) // 2, y + (PAIR_H - im.height) // 2))

        d.text((x, y + PAIR_H + 6), rec["name_ko"], font=f_name, fill=FG)
        d.text((x, y + PAIR_H + 30), pid, font=f_meta, fill=DIM)

    sheet.save(OUT, optimize=True)
    print(f"[identity-sheet] {OUT}  ({sheet.width}x{sheet.height})  {len(items)}쌍")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
