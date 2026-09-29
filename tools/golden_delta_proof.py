"""골든 컷 변경 증명 (v4.8.0, back_and_forth D-0101 작업 4 — D-0079 방식).

옛 엔진 렌더(기준 PNG 폴더)와 지금 렌더(프로젝트 prev/)를 컷마다 비교해, 바뀐 픽셀이 **요소 영역**(뱃지·카드·기사·게시물·
프리미티브·사진·영상·컷아웃·마커 상자, 패널 장면의 패널 영역, 자막 구역) 안에 있는지 센다. 요소 상자는 옛·새 엔진이 각자
계산한 것의 합집합이다(`boxes` 하위 명령을 두 저장소 트리에서 각각 돌려 JSON 으로 남긴다).

    python tools/golden_delta_proof.py boxes projects/hormuz_korea --out boxes_new.json          # 새 트리
    (옛 트리에서) python tools/golden_delta_proof.py boxes projects/hormuz_korea --out boxes_old.json
    python tools/golden_delta_proof.py prove --ref <옛 PNG 폴더> --new projects/hormuz_korea/prev \
        --boxes boxes_old.json boxes_new.json --out docs/handoff/reports/phaseG7/golden_delta

지도 라벨(도시·바다 이름)은 예약 영역(R.reserved)을 피해 자리를 바꾸므로 요소 크기가 바뀌면 요소 밖에서도 움직인다 —
`outside` 로 따로 세고 상자를 적는다(숨기지 않는다, 15 P6).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

SUB_TOP = 400      # 자막 구역(자막 halo 포함) — rules reserved_zones.subtitle.y_from 410 에서 글자 위 끝 여유
DIFF_MIN = 8       # 채널 차이 합(0~765)이 이 값 이하면 같은 픽셀로 본다(안티에일리어싱 반올림)
SHADOW = 10        # 카드·기사 그림자 여유(rules article_card.shadow 6 + shadow_dy 4)
PAD = 4            # 뱃지 상자 여유(글자 halo·팝인 ease_back 초과분)


def element_boxes(proj: Path) -> dict[str, list[list[float]]]:
    """골든 25 시각마다 활성 요소 상자 [x0, y0, x1, y1] 목록(설계 좌표 854×480)."""
    import cairo

    from engine.golden import golden_times
    from engine.layers.badges import badge_box
    from engine.layers.markers import marker_box
    from engine.media_plan import media_box
    from engine.project import load_project
    from engine.projection import View
    from engine.reserved import avoid_badge, card_box, card_zones
    from engine.style import FPS

    P = load_project(proj)  # noqa: N806
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    out: dict[str, list[list[float]]] = {}
    for _, t in golden_times(P.plan.model_dump()):
        v = View(P.R.stage, P.cams[min(P.n_frames - 1, int(t * FPS))])
        bs: list[list[float]] = [[0, SUB_TOP, 854, 480]]
        for e in P.events:
            if not (e["t0"] - 0.6 <= t <= e["t1"] + 0.6):
                continue
            typ = e["type"]
            try:
                if typ == "badge":                          # 그려진 자리(카드 회피·가장자리 보정 뒤) — 엔진마다 자기 함수로
                    x, y = (e["screen"] if e.get("over_panel") else v.to_screen(*e["world"]))
                    zones = card_zones(ctx, P.events, t)
                    try:
                        from engine.layers.badges import place_badge
                        dx, dy, _ = place_badge(ctx, e, x, y, t, zones)
                        b = badge_box(ctx, e, x + dx, y + dy, t)
                    except ImportError:                     # 옛 엔진(v4.7.0 — 가장자리 보정·시각 인자 없음)
                        b0 = badge_box(ctx, e, x, y)
                        dx, dy, _, _ = avoid_badge(b0, zones)
                        b = (b0[0] + dx, b0[1] + dy, b0[2] + dx, b0[3] + dy)
                    b = (b[0] - PAD, b[1] - PAD, b[2] + PAD, b[3] + PAD)
                elif typ in ("card", "article", "post", "primitive"):
                    b = card_box(ctx, e)
                    b = (b[0] - SHADOW, b[1] - SHADOW, b[2] + SHADOW, b[3] + SHADOW)   # 카드 그림자(번짐 6 + 이동 2·4)
                    if e.get("align") == "center":          # 가운데 기사 = 아래 무대 어둡게(화면 전체)
                        b = (0, 0, 854, 480)
                elif typ in ("photo", "clip"):
                    b = media_box(e, P.R.assets.media_assets)
                elif typ in ("marker", "cutout"):
                    x, y = v.to_screen(*e["world"])
                    b = marker_box(ctx, e, x, y, with_sub=True) if typ == "marker" else (x - e["w"], y - e["w"], x + e["w"], y + e["w"])
                elif typ == "panel":
                    b = (0, 50, 854, 480)
                else:
                    continue
            except Exception:  # noqa: BLE001 — 상자를 못 구한 요소는 증명에 쓰지 않는다(요소 밖으로 센다)
                continue
            bs.append([round(float(z), 1) for z in b])
        out[f"p_{t:07.2f}.png"] = bs
    return out


def prove(ref: Path, new: Path, box_files: list[Path], out: Path) -> dict:
    import numpy as np
    from PIL import Image

    out.mkdir(parents=True, exist_ok=True)
    boxes: dict[str, list] = {}
    for f in box_files:
        for k, v in json.loads(f.read_text(encoding="utf-8")).items():
            boxes.setdefault(k, []).extend(v)
    rows = []
    for p in sorted(new.glob("p_*.png")):
        r = ref / p.name
        a = np.asarray(Image.open(r).convert("RGB"), np.int16)
        b = np.asarray(Image.open(p).convert("RGB"), np.int16)
        d = np.abs(a - b).sum(-1)
        mask = d > DIFF_MIN
        n = int(mask.sum())
        if n == 0:
            continue
        H, W = mask.shape  # noqa: N806
        k = W / 854
        inside = np.zeros_like(mask)
        for x0, y0, x1, y1 in boxes.get(p.name, []):
            inside[max(0, int(y0 * k)):max(0, int(np.ceil(y1 * k))), max(0, int(x0 * k)):max(0, int(np.ceil(x1 * k)))] = True
        outm = mask & ~inside
        ys, xs = np.where(mask)
        oys, oxs = np.where(outm)
        row = {"png": p.name, "changed_px": n, "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
               "inside_px": n - int(outm.sum()), "outside_px": int(outm.sum()),
               "outside_bbox": [int(oxs.min()), int(oys.min()), int(oxs.max()), int(oys.max())] if len(oxs) else None,
               "mad": round(float(np.abs(a - b).mean()), 4), "md5": hashlib.md5(p.read_bytes()).hexdigest()}
        rows.append(row)
        heat = np.clip(d * 2, 0, 255).astype(np.uint8)
        hm = np.stack([heat, heat // 3, 255 - heat], -1).astype(np.uint8)
        hm[outm] = (255, 255, 0)                       # 요소 밖 변경 = 노랑
        strip = np.concatenate([a.astype(np.uint8), b.astype(np.uint8), hm], 1)
        Image.fromarray(strip).save(out / p.name.replace(".png", "_old_new_diff.png"))
    rep = {"schema_version": 1, "reference": str(ref), "new": str(new), "diff_min": DIFF_MIN, "cuts": rows,
           "changed_cuts": len(rows), "inside_ratio": round(sum(r["inside_px"] for r in rows) / max(1, sum(r["changed_px"] for r in rows)), 4)}
    (out / "golden_delta.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("boxes")
    b.add_argument("proj", type=Path)
    b.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("prove")
    p.add_argument("--ref", type=Path, required=True)
    p.add_argument("--new", type=Path, required=True)
    p.add_argument("--boxes", type=Path, nargs="+", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.cmd == "boxes":
        a.out.write_text(json.dumps(element_boxes(a.proj), ensure_ascii=False) + "\n", encoding="utf-8")
        print(a.out)
    else:
        rep = prove(a.ref, a.new, a.boxes, a.out)
        print(json.dumps({k: rep[k] for k in ("changed_cuts", "inside_ratio")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
