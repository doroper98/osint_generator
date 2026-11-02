"""눈 검수 시트(v7.4.0 back_and_forth D-1000 S4-1 — D-0463 "노출 표만 보고 통과" 사고 재발 방지, LLM-AP-023).

    python tools/review_sheet.py projects/<pid> [--src animatic|final|preview] [--every 3]

다시 렌더하지 않는다. 마지막 산출 mp4(콘티 판 out/animatic.mp4 · 전편 out/final.mp4)에서 ffmpeg 로 every 초 간격 프레임을 뽑아
칸마다 시각·문장 id·날짜 HUD 값을 단 시트(out/review/<src>_sheet_NN.jpg, 한 장 40칸)를 만든다. preview 는 prev/ 컷 PNG 를 그대로 쓴다.
둘째 장: 모든 미디어·배지·카드의 (시작, 끝, 완전 노출 초, 보이는 동안 그 요소가 지도 사건 상자를 가린 최대 %) 표
(out/review/<src>_elements.md + .jpg). 가림 % 는 검사 [map-event-covered] 와 같은 함수(engine.checks)로 잰다.
마지막 줄에 결과 JSON 을 표준 출력으로 낸다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.timing import stage_timer  # noqa: E402

PER_SHEET = 40
COLS = 4
ELEMENT_TYPES = ("photo", "clip", "cutout", "article", "quote", "badge", "post", "primitive", "cascade")
SOURCES = {"animatic": "out/animatic.mp4", "final": "out/final.mp4"}


def hud_date(tb, t: float) -> str:  # noqa: ANN001 — engine.timebase.Timebase
    """그 시각 날짜 HUD 값(engine.hud.draw_date 와 같은 규칙 — 문장 시작 0.3초 전부터 그 문장 날짜). 전면 카드·문장 전 = '-'."""
    sid = tb.cur_sentence(t)
    if sid is None or tb.in_fullcard(t):
        return "-"
    return tb.sent[sid].date


def frame_cells(P, src: str, every: float, tmp: Path) -> list[tuple[Path, float]]:  # noqa: ANN001, N803
    if src == "preview":
        prev = P.root / "prev"
        return [(p, float(p.stem[2:])) for p in sorted(prev.glob("p_*.png"))]
    mp4 = P.root / SOURCES[src]
    if not mp4.exists():
        raise FileNotFoundError(f"{mp4} 없음 — 이 도구는 다시 렌더하지 않는다(마지막 산출 mp4 만 본다)")
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf", f"fps=1/{every}:round=down,scale=427:-2",
                    str(tmp / "f_%05d.png")], check=True)
    return [(p, i * every) for i, p in enumerate(sorted(tmp.glob("f_*.png")))]


def element_rows(P) -> list[dict]:  # noqa: ANN001, N803
    """요소 표 — 종류·이름·시작·끝·완전 노출·보이는 동안 지도 사건 상자를 가린 최대 비율(그 요소 하나만 덮개로 쳤을 때)."""
    from engine.checks import _covered, _covered_ratio, _elem_name, _vis_span, element_full_span, map_event_windows  # noqa: PLC0415
    from engine.media_plan import media_box  # noqa: PLC0415
    from engine.reserved import FULL_COVER_TYPES  # noqa: PLC0415
    from engine.style import H_OUT, W_OUT  # noqa: PLC0415
    from rules import load_rules  # noqa: PLC0415

    cfg = load_rules().qa_checks.map_event_covered
    wins = map_event_windows(P)
    assets = P.R.assets.media_assets
    rows = []
    for e in sorted((e for e in P.events if e["type"] in ELEMENT_TYPES), key=lambda e: e["t0"]):
        fa, fb = element_full_span(e)
        va, vb = _vis_span(e)
        if e["type"] in FULL_COVER_TYPES:
            box = (0.0, 0.0, float(W_OUT), float(H_OUT))
        elif e["type"] in ("photo", "clip") and "x" in e and e.get("mid") in assets:
            box = tuple(float(v) for v in media_box(e, assets))
        else:
            box = None
        worst, what = 0.0, ""
        if box is not None and e["type"] in cfg.cover_types:
            for ty, name, a, b, boxf in wins:
                lo, hi = max(a, va), min(b, vb)
                t = lo
                while t <= hi + 1e-9:
                    if not _covered(P, t):
                        bx = boxf(t)
                        if bx is not None:
                            r = _covered_ratio(bx, [box])
                            if r > worst:
                                worst, what = r, f"{ty} {name}"
                    t += cfg.step_sec
        rows.append({"type": e["type"], "name": _elem_name(e), "t0": round(e["t0"], 2), "t1": round(e["t1"], 2),
                     "full_sec": round(max(0.0, fb - fa), 2), "map_cover_max": round(worst, 3), "map_event": what})
    return rows


def write_table(rows: list[dict], dest_md: Path, dest_jpg: Path, title: str) -> None:
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    from rules import load_rules  # noqa: PLC0415

    qa = load_rules().qa_checks

    head = "| # | 종류 | 이름 | 시작 | 끝 | 완전 노출(초) | 지도 사건 가림 최대 | 가린 사건 |"
    lines = [f"# {title}", "", head, "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {i + 1} | {r['type']} | {r['name']} | {r['t0']:.2f} | {r['t1']:.2f} | {r['full_sec']:.2f} | {r['map_cover_max']:.0%} | {r['map_event']} |"
              for i, r in enumerate(rows)]
    dest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    font_p = REPO / "assets" / "fonts" / "IBMPlexSansKR-Regular.ttf"
    font = ImageFont.truetype(str(font_p), 15) if font_p.exists() else ImageFont.load_default()
    lh = 22
    img = Image.new("RGB", (1400, lh * (len(rows) + 3) + 20), (24, 24, 30))
    d = ImageDraw.Draw(img)
    d.text((10, 8), title, fill=(255, 220, 90), font=font)
    cols = [10, 50, 140, 520, 610, 700, 820, 980]
    for k, h in enumerate(["#", "종류", "이름", "시작", "끝", "완전 노출", "지도 가림", "가린 사건"]):
        d.text((cols[k], 8 + lh), h, fill=(200, 200, 200), font=font)
    for i, r in enumerate(rows):
        y = 8 + lh * (i + 2)
        bad = r["map_cover_max"] > qa.map_event_covered.max_ratio or r["full_sec"] < qa.element_hold.min_full_sec   # 빨간 줄 = 검사 실패 값
        col = (255, 120, 110) if bad else (235, 235, 235)
        vals = [str(i + 1), r["type"], r["name"][:34], f"{r['t0']:.1f}", f"{r['t1']:.1f}", f"{r['full_sec']:.1f}",
                f"{r['map_cover_max']:.0%}", r["map_event"][:36]]
        for k, v in enumerate(vals):
            d.text((cols[k], y), v, fill=col, font=font)
    img.save(dest_jpg, quality=88)


def main(argv: list[str] | None = None) -> int:
    from PIL import Image  # noqa: PLC0415

    from engine.project import load_project  # noqa: PLC0415
    from engine.sheet import grid  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="눈 검수 시트(D-1000 S4)")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--src", choices=["animatic", "final", "preview"], default="animatic")
    ap.add_argument("--every", type=float, default=3.0)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    out = proj / "out" / "review"
    out.mkdir(parents=True, exist_ok=True)
    if args.src in SOURCES and not (proj / SOURCES[args.src]).exists():
        raise FileNotFoundError(f"{proj / SOURCES[args.src]} 없음 — 이 도구는 다시 렌더하지 않는다(마지막 산출 mp4 만 본다)")
    with stage_timer(proj, "review.sheet", src=args.src, every=args.every):
        P = load_project(proj, animatic=args.src == "animatic")  # noqa: N806
        tb = P.R.tb
        with tempfile.TemporaryDirectory() as td:
            cells = frame_cells(P, args.src, args.every, Path(td))
            labels = []
            for p, t in cells:
                sid = tb.cur_sentence(t) or "-"
                labels.append((p, f"{t:6.1f}s  {sid}  {hud_date(tb, t)}"))
            sheets = []
            for k in range(0, len(labels), PER_SHEET):
                dest = out / f"{args.src}_sheet_{k // PER_SHEET + 1:02d}.jpg"
                grid([(Image.open(p), lab) for p, lab in labels[k:k + PER_SHEET]], COLS, dest)
                sheets.append(str(dest))
        rows = element_rows(P)
        md, jpg = out / f"{args.src}_elements.md", out / f"{args.src}_elements.jpg"
        write_table(rows, md, jpg, f"{proj.name} — 요소 노출·지도 가림 ({args.src})")
    print(json.dumps({"ok": True, "sheets": sheets, "cells": len(labels), "elements": str(md), "elements_jpg": str(jpg),
                      "rows": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
