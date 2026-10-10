"""V3 컷 대응표·25컷 나란히 시트 (v5.17.0, back_and_forth D-0167 §3-3).

목소리 교체(edge → Supertonic M3)는 모든 컷의 절대 시각을 바꾼다. 골든 25 컷은 문장 앵커 + 오프셋이라
옛·새 plan 만으로 컷을 짝짓는다(`tools.golden_compare.anchor_time` 한 경로). 시트는 컷마다 옛 | 새 | 차이(×4) 한 줄.

    python tools/v3_cut_table.py --old-plan <옛 plan.json> --old-prev <옛 prev/> \
        --new-plan projects/hormuz_korea/plan.json --new-prev projects/hormuz_korea/prev --out docs/handoff/reports/phaseV3

→ `cut_table.json`(행 25 + 요약), `cut_table.md`, `cuts_side_by_side.jpg`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from tools.golden_compare import anchor_time, load_golden, mad  # noqa: E402

CAPTION_FONT = "IBM Plex Sans KR"


def png_name(t: float) -> str:
    """engine.render 프리뷰 파일 이름 규칙(p_TTTT.TT.png)."""
    return f"p_{float(f'{t:.2f}'):07.2f}.png"


def _sentence(plan: dict, sid: str) -> dict | None:
    return next((s for s in plan["sentences"] if s["sid"] == sid), None)


def cut_rows(old_plan: dict, new_plan: dict) -> list[dict]:
    """골든 25 컷: 앵커·오프셋·옛/새 시각·이동량·앵커 문장 길이 전/후·옛/새 파일 이름."""
    rows = []
    for n, f in enumerate(load_golden()["frames"], 1):
        a, off = f["anchor"], float(f["offset"])
        t_old, t_new = anchor_time(a, off, old_plan), anchor_time(a, off, new_plan)
        so, sn = _sentence(old_plan, a), _sentence(new_plan, a)
        rows.append({"n": n, "label": f"{a}{off:+g}", "anchor": a, "offset": off,
                     "old_t": round(t_old, 3), "new_t": round(t_new, 3), "shift": round(t_new - t_old, 3),
                     "old_dur": round(so["dur"], 3) if so else None, "new_dur": round(sn["dur"], 3) if sn else None,
                     "old_png": png_name(t_old), "new_png": png_name(t_new)})
    return rows


def summary(old_plan: dict, new_plan: dict, old_prov: dict | None, new_prov: dict | None) -> dict:
    def at_word(p: dict | None) -> dict | None:
        return (p or {}).get("features_used", {}).get("at_word") if p else None

    def sources(plan: dict) -> dict[str, int]:
        out: dict[str, int] = {}
        for s in plan["sentences"]:
            src = (s.get("alignment") or {}).get("source", "(plan 기록 없음)")
            out[src] = out.get(src, 0) + 1
        return dict(sorted(out.items()))

    return {"old_total": round(old_plan["total"], 3), "new_total": round(new_plan["total"], 3),
            "old_voice": old_plan.get("voice"), "new_voice": new_plan.get("voice"),
            "sentence_dur_sum_old": round(sum(s["dur"] for s in old_plan["sentences"]), 3),
            "sentence_dur_sum_new": round(sum(s["dur"] for s in new_plan["sentences"]), 3),
            "old_at_word": at_word(old_prov), "new_at_word": at_word(new_prov),
            "old_alignment_sources": sources(old_plan), "new_alignment_sources": sources(new_plan)}


def markdown(rows: list[dict], summ: dict) -> str:
    lines = ["| # | 컷(앵커+오프셋) | 옛 시각 | 새 시각 | 이동 | 앵커 문장 길이 옛 → 새 | MAD/255 |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        dur = f"{r['old_dur']:.2f} → {r['new_dur']:.2f}" if r["old_dur"] is not None else "—(카드)"
        m = f"{r['mad']:.2f}" if r.get("mad") is not None else "—"
        lines.append(f"| {r['n']} | {r['label']} | {r['old_t']:.2f} | {r['new_t']:.2f} | {r['shift']:+.2f} | {dur} | {m} |")
    lines += ["", f"전체 길이 {summ['old_total']:.2f} → {summ['new_total']:.2f}초, 문장 길이 합 {summ['sentence_dur_sum_old']:.2f} → "
              f"{summ['sentence_dur_sum_new']:.2f}초.",
              f"at_word 옛 {summ['old_at_word']} → 새 {summ['new_at_word']}.",
              f"정렬 출처 옛 {summ['old_alignment_sources']} → 새 {summ['new_alignment_sources']}."]
    return "\n".join(lines) + "\n"


def sheet(rows: list[dict], old_dir: Path, new_dir: Path, dest: Path) -> None:
    """컷마다 옛 | 새 | |차이|×4 한 줄(427×240 축소). 캡션 = 저장소 글꼴."""
    import numpy as np  # noqa: PLC0415
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

    from engine.typography import fc_match  # noqa: PLC0415

    font = ImageFont.truetype(fc_match(CAPTION_FONT)[1], 15)
    cw, ch, lab = 427, 240, 24
    out = Image.new("RGB", (cw * 3, (ch + lab) * len(rows)), (24, 24, 30))
    d = ImageDraw.Draw(out)
    for i, r in enumerate(rows):
        a = Image.open(old_dir / r["old_png"]).convert("RGB")
        b = Image.open(new_dir / r["new_png"]).convert("RGB")
        r["mad"] = round(mad(a, b), 3)
        x, y = np.asarray(a, np.float32), np.asarray(b, np.float32)
        heat = np.clip(np.abs(x - y).mean(-1) * 4.0, 0, 255).astype(np.uint8)
        hm = Image.fromarray(np.stack([heat, heat // 3, 255 - heat], -1).astype(np.uint8))
        top = i * (ch + lab)
        for k, im in enumerate((a, b, hm)):
            out.paste(im.resize((cw, ch)), (k * cw, top + lab))
        d.text((8, top + 3), f"{r['n']:02d}  {r['label']}   옛 {r['old_t']:.2f}초 | 새 {r['new_t']:.2f}초 ({r['shift']:+.2f})"
               f"   MAD {r['mad']:.2f}/255   [옛 edge | 새 Supertonic | 차이×4]", font=font, fill=(255, 220, 90))
    out.save(dest, quality=85)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="tools.v3_cut_table")
    ap.add_argument("--old-plan", type=Path, required=True)
    ap.add_argument("--old-prev", type=Path, required=True)
    ap.add_argument("--new-plan", type=Path, required=True)
    ap.add_argument("--new-prev", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    old_plan = json.loads(args.old_plan.read_text(encoding="utf-8"))
    new_plan = json.loads(args.new_plan.read_text(encoding="utf-8"))

    def prov(d: Path) -> dict | None:
        p = d / "provenance.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    rows = cut_rows(old_plan, new_plan)
    args.out.mkdir(parents=True, exist_ok=True)
    sheet(rows, args.old_prev, args.new_prev, args.out / "cuts_side_by_side.jpg")
    summ = summary(old_plan, new_plan, prov(args.old_prev), prov(args.new_prev))
    (args.out / "cut_table.json").write_text(json.dumps({"schema_version": 1, "summary": summ, "rows": rows},
                                                        ensure_ascii=False, indent=1), encoding="utf-8")
    (args.out / "cut_table.md").write_text(markdown(rows, summ), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
