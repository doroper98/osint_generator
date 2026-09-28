"""카드 RESERVED 증명 (D-0033 구속 조건 4·5) — 부산 뱃지 겹침을 회피 OFF/ON 으로 렌더해 세고 한 장으로 묶는다.

    python tools/reserved_proof.py --proj projects/hormuz_korea --badge "부산에서 출항" \
        --times 164.594,170.519 --after 181.0 --phase5 docs/handoff/reports/phase5/hormuz_25/frames \
        --out docs/handoff/reports/phase6/reserved

겹침 = 뱃지 상자(원·이름표, engine.layers.badges.badge_box)와 카드 영역(engine.reserved.card_zones)의 교집합 면적(px²).
OFF 는 영역 계산을 비워서(회피 없음) 같은 프레임을 다시 그린 것이다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cairo
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import engine.render as er  # noqa: E402
from engine.layers.badges import badge_box  # noqa: E402
from engine.project import load_project  # noqa: E402
from engine.projection import View  # noqa: E402
from engine.reserved import avoid_badge, card_zones  # noqa: E402
from engine.style import FPS, H_OUT, W_OUT  # noqa: E402


def overlap(b: tuple, z: tuple) -> float:
    w = min(b[2], z[2]) - max(b[0], z[0])
    h = min(b[3], z[3]) - max(b[1], z[1])
    return max(0.0, w) * max(0.0, h)


def measure(P, e: dict, i: int, on: bool) -> dict:  # noqa: ANN001
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    t = i / FPS
    zones = card_zones(ctx, P.events, t)
    x, y = View(P.cams[i], P.R.assets.tiers, P.R.assets.base).xy(e["lon"], e["lat"])
    box = badge_box(ctx, e, x, y)
    dx, dy, ka, info = avoid_badge(box, zones) if on else (0.0, 0.0, 1.0, None)
    moved = (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
    card_boxes = [z.box for z in zones]
    return {"t": round(t, 3), "badge_xy": [round(x, 1), round(y, 1)], "shift": [round(float(dx), 1), round(float(dy), 1)],
            "alpha_scale": round(ka, 3), "overlap_px2": round(sum(overlap(moved, c) for c in card_boxes), 1),
            "card_boxes": [[round(v, 1) for v in c] for c in card_boxes], "avoidance": info}


def frame(P, i: int, on: bool) -> Image.Image:  # noqa: ANN001
    orig = er.card_zones
    if not on:
        er.card_zones = lambda ctx, events, t: []   # noqa: E731 — 회피 OFF
    try:
        s, _ = er.render_frame(P, i)
    finally:
        er.card_zones = orig
    return Image.frombuffer("RGBA", (W_OUT, H_OUT), bytes(s.get_data()), "raw", "BGRA", 0, 1).convert("RGB")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--proj", type=Path, required=True)
    ap.add_argument("--badge", required=True, help="뱃지 label")
    ap.add_argument("--times", required=True, help="쉼표로 구분한 초(골든 앵커 시각)")
    ap.add_argument("--after", type=float, required=True, help="카드 퇴장 뒤 시각(원위치 확인)")
    ap.add_argument("--phase5", type=Path, required=True, help="임시 조치 시절 프레임 폴더(15_*.png, 16_*.png)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    P = load_project(args.proj)  # noqa: N806
    e = next(x for x in P.events if x["type"] == "badge" and x["label"] == args.badge)
    args.out.mkdir(parents=True, exist_ok=True)
    times = [float(x) for x in args.times.split(",")]
    old = sorted(args.phase5.glob("1[56]_*.png"))
    rows: list[tuple[str, list[Image.Image]]] = [("(a) 실제 부산 · 회피 OFF", []), ("(b) 실제 부산 · 회피 ON", []),
                                                 ("(c) Phase 5 · 임시 좌표 125.6E 22.3N", [])]
    report: dict = {"schema_version": 1, "badge": args.badge, "lonlat": [e["lon"], e["lat"]], "frames": []}
    for n, t in enumerate(times):
        i = int(round(t * FPS))
        off, on = frame(P, i, False), frame(P, i, True)
        rows[0][1].append(off)
        rows[1][1].append(on)
        rows[2][1].append(Image.open(old[n]).convert("RGB"))
        off.save(args.out / f"off_{t:.2f}.png")
        on.save(args.out / f"on_{t:.2f}.png")
        report["frames"].append({"t": t, "off": measure(P, e, i, False), "on": measure(P, e, i, True)})
    ia = int(round(args.after * FPS))
    after = frame(P, ia, True)
    after.save(args.out / f"after_{args.after:.2f}.png")
    report["after"] = measure(P, e, ia, True)
    sc = 0.5
    w, h = int(W_OUT * sc), int(H_OUT * sc)
    lab = 22
    sheet = Image.new("RGB", (w * 2, (h + lab) * 4), (12, 14, 20))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 14)
    except OSError:
        font = ImageFont.load_default()
    for r, (title, ims) in enumerate(rows + [("(d) 카드 퇴장 뒤 · 제자리", [after])]):
        y0 = r * (h + lab)
        d.text((6, y0 + 3), title, fill=(230, 230, 230), font=font)
        for c, im in enumerate(ims):
            sheet.paste(im.resize((w, h)), (c * w, y0 + lab))
    sheet.save(args.out.parent / "reserved_before_after.png")
    (args.out / "reserved_proof.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in report["frames"]:
        print(f"t={f['t']}: OFF 겹침 {f['off']['overlap_px2']} px² → ON {f['on']['overlap_px2']} px² (이동 {f['on']['shift']})")
    print(f"after t={args.after}: 이동 {report['after']['shift']}, 겹침 {report['after']['overlap_px2']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
