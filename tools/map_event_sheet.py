"""[map-event-covered] 눈 검증 시트(v7.4.0 back_and_forth D-1001 §3 — 표만 보고 통과 금지, LLM-AP-023).

    python tools/map_event_sheet.py projects/<pid> OUT_DIR [--animatic] [--limit N] [--seed S]

검사 [map-event-covered] 가 잡은 건마다 가림이 가장 큰 표본 시각의 프레임을 **그 프레임만** 그려(전체 렌더 없음)
사건 상자(빨강 외곽선)·덮개 상자(파랑 외곽선)·가림 %·사건 종류·문장 id 를 얹은 낱장(OUT_DIR/<pid>_NN.png)과 한 장 시트(OUT_DIR/<pid>_sheet.jpg)를 만든다.
--limit 이면 무작위(seed) N 건만. 마지막 줄 = 결과 JSON.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main(argv: list[str] | None = None) -> int:
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    from engine.checks import _cover_boxes, map_event_covered, map_event_windows  # noqa: PLC0415
    from engine.project import load_project  # noqa: PLC0415
    from engine.render import render_frame  # noqa: PLC0415
    from engine.sheet import grid  # noqa: PLC0415
    from engine.style import FPS  # noqa: PLC0415
    from rules import load_rules  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="map_event_covered 눈 검증 시트(D-1001 §3)")
    ap.add_argument("proj", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--animatic", action="store_true", help="콘티 판 레이어(사진·영상 = 자리표시 상자)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--seed", type=int, default=1000)
    args = ap.parse_args(argv)
    cfg = load_rules().qa_checks.map_event_covered
    P = load_project(args.proj.resolve(), animatic=args.animatic)  # noqa: N806
    wins = map_event_windows(P)
    cov = map_event_covered(P)   # map_event_windows 와 같은 순서(같은 함수를 돈다)
    assert len(wins) == len(cov)
    hits = [(*h, w[4]) for w, h in zip(wins, cov) if h[4] > cfg.max_ratio + 1e-9]
    if args.limit is not None and len(hits) > args.limit:
        hits = sorted(random.Random(args.seed).sample(hits, args.limit), key=lambda h: h[5])
    args.out.mkdir(parents=True, exist_ok=True)
    from engine.typography import fc_match  # noqa: PLC0415

    font = ImageFont.truetype(fc_match("IBM Plex Sans KR")[1], 14)   # 시스템 글꼴(fetch_data fonts) — 한글 없는 기본 글꼴로 조용히 폴백하지 않는다(P6)
    cells, rows = [], []
    for k, (ty, name, a, b, r, t, boxf) in enumerate(hits):
        surf, _ = render_frame(P, min(P.n_frames - 1, int(t * FPS)))
        im = Image.frombuffer("RGBA", (surf.get_width(), surf.get_height()), bytes(surf.get_data()), "raw", "BGRA", 0, 1).convert("RGB")
        k_ = P.R.out.k
        d = ImageDraw.Draw(im)

        def dev(bx: tuple) -> tuple:
            return tuple(round(v * k_ + (P.R.out.pad_x if i % 2 == 0 else 0)) for i, v in enumerate(bx))

        for cb in _cover_boxes(P, t, cfg.camera_cover_types if ty == "camera" else cfg.cover_types):   # 검사와 같은 덮개(D-1002)
            d.rectangle(dev(cb), outline=(40, 120, 255), width=3)
        ev = boxf(t)
        if ev is not None:
            d.rectangle(dev(ev), outline=(255, 40, 40), width=3)
        sid = P.R.tb.cur_sentence(t) or "-"
        label = f"{ty} {name} · 가림 {r:.0%} · t={t:.1f}s · {sid}"
        d.rectangle((0, 0, im.width, 22), fill=(0, 0, 0))
        d.text((6, 3), label, fill=(255, 230, 120), font=font)
        dest = args.out / f"{args.proj.name}_{k + 1:02d}.png"
        im.save(dest)
        cells.append((im, f"{k + 1:02d} {ty} {r:.0%} t={t:.1f} {sid}"))
        rows.append({"n": k + 1, "type": ty, "name": name, "window": [round(a, 2), round(b, 2)], "ratio": round(r, 3), "t": round(t, 2),
                     "sid": sid, "png": str(dest)})
    sheet = args.out / f"{args.proj.name}_sheet.jpg"
    if cells:
        grid(cells, 2, sheet)
    (args.out / f"{args.proj.name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"ok": True, "project": args.proj.name, "hits": len(rows), "sheet": str(sheet) if cells else None}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
