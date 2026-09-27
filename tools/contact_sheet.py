"""프리뷰 컨택트 시트 (v2.0.1, back_and_forth D-0002 작업 5 · D-0006 §2 · docs/handoff/11 §5).

모드:
    python tools/contact_sheet.py sheet [--dir D]         # D/frames/*.png → D/sheet.jpg (4열 427×240, 앵커·시각 라벨)
    python tools/contact_sheet.py pairs [--dir D]         # 골든 | 렌더 쌍 2쌍/행 → D/sheet_vs_golden.jpg
    python tools/contact_sheet.py transitions [--dir D]   # 타이틀·dip 마다 0.3초 간격 8컷 → D/transitions.jpg

라벨은 D/golden_compare.json(golden_compare.py 출력)에서 읽는다. transitions 는 legacy_v3/render3.py 를
모듈로 불러 연출층의 dip 이벤트와 타이틀 카드 시각을 그대로 쓴다(시각을 따로 적지 않는다).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO / "docs" / "handoff" / "golden"
DEFAULT_DIR = REPO / "docs" / "handoff" / "reports" / "phase1"
CELL = (427, 240)
LABEL_H = 22
COLS = 4
TRANSITION_STEP = 0.3
TRANSITION_COUNT = 8


def grid(cells: list[tuple["object", str]], cols: int, dest: Path, cell: tuple[int, int] = CELL) -> None:
    """(이미지, 라벨) 목록 → cols 열 격자 JPEG."""
    from PIL import Image, ImageDraw

    cw, ch = cell
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, (ch + LABEL_H) * rows), (24, 24, 30))
    d = ImageDraw.Draw(sheet)
    for i, (im, label) in enumerate(cells):
        x, y = (i % cols) * cw, (i // cols) * (ch + LABEL_H)
        sheet.paste(im.convert("RGB").resize((cw, ch)), (x, y + LABEL_H))
        d.text((x + 6, y + 5), label, fill=(255, 220, 90))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, quality=88)


def transition_times(center: float) -> list[float]:
    """center 를 가운데 두고 0.3초 간격 8컷."""
    half = (TRANSITION_COUNT - 1) / 2
    return [round(center + (k - half) * TRANSITION_STEP, 3) for k in range(TRANSITION_COUNT)]


def _load_compare(d: Path) -> dict:
    p = d / "golden_compare.json"
    if not p.exists():
        raise SystemExit(f"{p} 없음 — 먼저 tools/golden_compare.py 실행")
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_sheet(d: Path) -> Path:
    from PIL import Image

    cmp_ = _load_compare(d)
    cells = [(Image.open(d / r["frame"]), f"{r['n']:02d} {r['anchor']}{r['offset']:+g}  t={r['t_now']:.2f}")
             for r in cmp_["frames"]]
    grid(cells, COLS, d / "sheet.jpg")
    return d / "sheet.jpg"


def cmd_pairs(d: Path) -> Path:
    from PIL import Image

    cmp_ = _load_compare(d)
    golden = {f"{f['anchor']}|{f['offset']}": f["file"] for f in json.loads((GOLDEN_DIR / "golden_frames.json").read_text(encoding="utf-8"))["frames"]}
    cells = []
    for r in cmp_["frames"]:
        cells.append((Image.open(GOLDEN_DIR / golden[f"{r['anchor']}|{r['offset']}"]), f"{r['n']:02d} GOLDEN {r['anchor']}"))
        cells.append((Image.open(d / r["frame"]), f"{r['n']:02d} RENDER  MAD {r['mad']:.2f}"))
    grid(cells, COLS, d / "sheet_vs_golden.jpg")
    return d / "sheet_vs_golden.jpg"


def _import_render3() -> "object":
    sys.argv = [sys.argv[0]]
    spec = importlib.util.spec_from_file_location("render3", REPO / "legacy_v3" / "render3.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def cmd_transitions(d: Path) -> Path:
    import numpy as np
    from PIL import Image

    r3 = _import_render3()
    events: list[tuple[str, float]] = []
    title = next(c for c in r3.P["cards"] if c["kind"] == "title")
    events.append(("title", float(title["t0"])))
    for k, e in enumerate(ev for ev in r3.EV if ev["type"] == "dip"):
        events.append((f"dip{k + 1}{'(under)' if e.get('under') else ''}", (e["t0"] + e["t1"]) / 2))
    cells = []
    for name, center in events:
        for t in transition_times(center):
            surf, buf = r3.render_frame(min(r3.N - 1, int(t * r3.FPS)))
            arr = np.frombuffer(bytes(buf), np.uint8).reshape(r3.H_OUT, r3.W_OUT, 4)[..., [2, 1, 0]]
            cells.append((Image.fromarray(arr), f"{name} t={t:.2f}"))
    grid(cells, TRANSITION_COUNT, d / "transitions.jpg", cell=(214, 120))
    return d / "transitions.jpg"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="프리뷰 컨택트 시트")
    ap.add_argument("mode", choices=["sheet", "pairs", "transitions"])
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    args = ap.parse_args(argv)
    os.environ.setdefault("V3_ROOT", "projects/hormuz_korea_legacy")
    out = {"sheet": cmd_sheet, "pairs": cmd_pairs, "transitions": cmd_transitions}[args.mode](args.dir)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
