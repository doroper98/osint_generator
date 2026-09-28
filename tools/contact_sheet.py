"""프리뷰 컨택트 시트 (v2.0.1, back_and_forth D-0002 작업 5 · D-0006 §2 · docs/handoff/11 §5).

모드:
    python tools/contact_sheet.py sheet [--dir D]         # D/frames/*.png → D/sheet.jpg (4열 427×240, 앵커·시각 라벨)
    python tools/contact_sheet.py pairs [--dir D]         # 골든 | 렌더 쌍 2쌍/행 → D/sheet_vs_golden.jpg
    python tools/contact_sheet.py transitions [--dir D] [--proj P]   # 타이틀·dip 마다 0.3초 간격 8컷
    python tools/contact_sheet.py versus --dir A --dir2 B --out F.jpg  # A | B 같은 앵커 쌍 2쌍/행 (목소리 교체 시트, D31)

라벨은 D/golden_compare.json(golden_compare.py 출력)에서 읽는다. transitions 는 새 엔진 프로젝트(engine.project)를
불러 연출층의 dip 이벤트와 타이틀 카드 시각을 그대로 쓴다(시각을 따로 적지 않는다).
v2.3.0: 옛 v3 렌더러 경로는 삭제했다(D32). `--engine` 은 호환용으로 `new` 만 받는다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
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


def cmd_versus(a: Path, b: Path, dest: Path) -> Path:
    """두 golden_compare 출력 폴더의 같은 앵커 프레임을 나란히(A | B). 라벨에 각자의 절대 시각."""
    from PIL import Image

    ca, cb = _load_compare(a), _load_compare(b)
    cells = []
    for ra, rb in zip(ca["frames"], cb["frames"]):
        if (ra["anchor"], ra["offset"]) != (rb["anchor"], rb["offset"]):
            raise SystemExit(f"앵커 불일치: {ra['anchor']} / {rb['anchor']}")
        cells.append((Image.open(a / ra["frame"]), f"{ra['n']:02d} A {ra['anchor']}{ra['offset']:+g} t={ra['t_now']:.2f}"))
        cells.append((Image.open(b / rb["frame"]), f"{rb['n']:02d} B t={rb['t_now']:.2f}"))
    grid(cells, COLS, dest)
    return dest


def _new_engine_frames(proj: Path) -> tuple[list[tuple[str, float]], "object"]:
    """새 엔진: 타이틀·dip 중심 시각과 프레임 렌더 함수."""
    import numpy as np
    from PIL import Image

    from engine.project import load_project
    from engine.render import render_frame
    from engine.style import FPS, H_OUT, W_OUT

    P = load_project(proj)  # noqa: N806
    title = next(c for c in P.plan.cards if c.kind == "title")
    events: list[tuple[str, float]] = [("title", float(title.t0))]
    for k, e in enumerate(ev for ev in P.events if ev["type"] == "dip"):
        events.append((f"dip{k + 1}{'(under)' if e.get('under') else ''}", (e["t0"] + e["t1"]) / 2))

    def frame(t: float) -> "object":
        _, buf = render_frame(P, min(P.n_frames - 1, int(t * FPS)))
        return Image.fromarray(np.frombuffer(bytes(buf), np.uint8).reshape(H_OUT, W_OUT, 4)[..., [2, 1, 0]])

    return events, frame


def cmd_transitions(d: Path, proj: Path | None = None) -> Path:
    events, frame = _new_engine_frames(proj or REPO / "projects" / "hormuz_korea")
    cells = [(frame(t), f"{name} t={t:.2f}") for name, center in events for t in transition_times(center)]
    grid(cells, TRANSITION_COUNT, d / "transitions.jpg", cell=(214, 120))
    return d / "transitions.jpg"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="프리뷰 컨택트 시트")
    ap.add_argument("mode", choices=["sheet", "pairs", "transitions", "versus"])
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    ap.add_argument("--dir2", type=Path, default=None, help="versus: B 폴더")
    ap.add_argument("--out", type=Path, default=None, help="versus: 출력 JPEG")
    ap.add_argument("--engine", choices=["new"], default="new", help="새 엔진만(v2.3.0, D32)")
    ap.add_argument("--proj", type=Path, default=None, help="transitions 프로젝트(기본 projects/hormuz_korea)")
    args = ap.parse_args(argv)
    if args.mode == "transitions":
        out = cmd_transitions(args.dir, args.proj)
    elif args.mode == "versus":
        if args.dir2 is None or args.out is None:
            raise SystemExit("versus 는 --dir2 와 --out 이 필요하다")
        out = cmd_versus(args.dir, args.dir2, args.out)
    else:
        out = {"sheet": cmd_sheet, "pairs": cmd_pairs}[args.mode](args.dir)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
