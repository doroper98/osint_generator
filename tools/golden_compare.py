"""골든 25컷 대조 (v2.0.1, back_and_forth D-0002 작업 4 · D-0006 §2).

`docs/handoff/golden/golden_frames.json`의 앵커(문장 id + 오프셋)를 **현재 plan.json 으로 시각 재계산**하고,
`legacy_v3/render3.py --preview`로 같은 앵커 프레임을 렌더해 골든 PNG와 평균 절대 차이(MAD, /255)를 잰다.
음성(edge-tts)이 재합성되면 절대 시각이 달라지므로 비교는 반드시 앵커 기준이다(골든 README).

앵커 규칙: 문장 id → `sentence.t0 + offset`, `TITLE` → `cards[title].t0 + offset`, `END` → `total + offset`.

사용법:
    python tools/golden_compare.py --dry-run                 # plan 없이 골든 절대 시각 25개 출력
    python tools/golden_compare.py [--plan P] [--out DIR]     # 렌더 → MAD 표 → json·히트맵·프레임 저장

출력(DIR, 기본 docs/handoff/reports/phase1): golden_compare.json, golden_compare_diff.jpg, frames/{NN}_{anchor}.png
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO / "docs" / "handoff" / "golden"
DEFAULT_OUT = REPO / "docs" / "handoff" / "reports" / "phase1"
MAD_THRESHOLD = 2.0  # /255 — Phase 2 판정 임계. Phase 1 은 참고값(D-0005 결정 1)


def v3_root() -> Path:
    return (REPO / os.environ.get("V3_ROOT", "projects/hormuz_korea_legacy")).resolve()


def load_golden() -> dict:
    return json.loads((GOLDEN_DIR / "golden_frames.json").read_text(encoding="utf-8"))


def anchor_time(anchor: str, offset: float, plan: dict) -> float:
    """앵커 → 절대 시각(초)."""
    if anchor == "TITLE":
        return next(c["t0"] for c in plan["cards"] if c["kind"] == "title") + offset
    if anchor == "END":
        return float(plan["total"]) + offset
    for s in plan["sentences"]:
        if s["sid"] == anchor:
            return float(s["t0"]) + offset
    raise KeyError(f"plan.json 에 앵커 없음: {anchor}")


def mad(a: "object", b: "object") -> float:
    """두 RGB 배열의 평균 절대 차이(/255)."""
    import numpy as np

    x = np.asarray(a, np.float32)[..., :3]
    y = np.asarray(b, np.float32)[..., :3]
    if x.shape != y.shape:
        raise ValueError(f"크기 불일치 {x.shape} != {y.shape}")
    return float(np.abs(x - y).mean())


def render_previews(times: list[float], root: Path) -> list[Path]:
    arg = ",".join(f"{t:.2f}" for t in times)
    env = {**os.environ, "V3_ROOT": str(root)}
    subprocess.run([sys.executable, str(REPO / "legacy_v3" / "render3.py"), "--preview", arg], check=True, env=env, cwd=REPO)
    return [root / "prev" / f"p_{float(f'{t:.2f}'):07.2f}.png" for t in times]


def diff_sheet(pairs: list[tuple[str, "object", "object", float]], dest: Path) -> None:
    """골든 | 렌더 | 차이 히트맵 3열, 컷마다 한 줄 (427×240 축소)."""
    import numpy as np
    from PIL import Image, ImageDraw

    cw, ch, lab = 427, 240, 22
    sheet = Image.new("RGB", (cw * 3, (ch + lab) * len(pairs)), (24, 24, 30))
    d = ImageDraw.Draw(sheet)
    for i, (label, g, r, m) in enumerate(pairs):
        ga = np.asarray(g, np.float32)[..., :3]
        ra = np.asarray(r, np.float32)[..., :3]
        heat = np.clip(np.abs(ga - ra).mean(-1) * 4.0, 0, 255).astype(np.uint8)  # 4배 증폭
        hm = Image.fromarray(np.stack([heat, heat // 3, 255 - heat], -1).astype(np.uint8))
        y = i * (ch + lab)
        for k, im in enumerate((g, r, hm)):
            sheet.paste(im.convert("RGB").resize((cw, ch)), (k * cw, y + lab))
        d.text((6, y + 4), f"{label}   MAD {m:.2f}/255   [golden | render | |diff|x4]", fill=(255, 220, 90))
    sheet.save(dest, quality=88)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="골든 25컷 앵커 대조")
    ap.add_argument("--plan", type=Path, default=None, help="plan.json (기본 V3_ROOT/plan.json)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--dry-run", action="store_true", help="plan 없이 골든 절대 시각만 출력")
    args = ap.parse_args(argv)
    golden = load_golden()
    frames = golden["frames"]

    if args.dry_run:
        print(f"golden total {golden['total']:.2f}s, {len(frames)} anchors")
        for i, f in enumerate(frames, 1):
            print(f"{i:02d} {f['anchor']:<12} {f['offset']:+5.1f}  t={f['t']:7.2f}  {f['file']}")
        return 0

    from PIL import Image

    root = v3_root()
    plan = json.loads((args.plan or root / "plan.json").read_text(encoding="utf-8"))
    times = [anchor_time(f["anchor"], float(f["offset"]), plan) for f in frames]
    pngs = render_previews(times, root)
    out = args.out
    (out / "frames").mkdir(parents=True, exist_ok=True)
    rows, pairs = [], []
    for i, (f, t, png) in enumerate(zip(frames, times, pngs), 1):
        g = Image.open(GOLDEN_DIR / f["file"]).convert("RGB")
        r = Image.open(png).convert("RGB")
        m = mad(g, r)
        name = f"{i:02d}_{f['anchor']}.png"
        shutil.copy2(png, out / "frames" / name)
        rows.append(dict(n=i, anchor=f["anchor"], offset=f["offset"], t_golden=f["t"], t_now=round(t, 3),
                         dt=round(t - f["t"], 3), mad=round(m, 3), over=m > MAD_THRESHOLD, frame=f"frames/{name}"))
        pairs.append((f"{i:02d} {f['anchor']}{f['offset']:+.1f}  t={t:.2f} (golden {f['t']:.2f})", g, r, m))
        print(f"{i:02d} {f['anchor']:<12} t={t:7.2f} (golden {f['t']:7.2f})  MAD {m:6.2f}", flush=True)
    over = [r["anchor"] for r in rows if r["over"]]
    result = dict(schema_version=1, threshold=MAD_THRESHOLD, total_now=plan["total"], total_golden=golden["total"],
                  mean_mad=round(sum(r["mad"] for r in rows) / len(rows), 3), over_threshold=over, frames=rows,
                  note="Phase 1 MAD 는 참고값(TTS 재합성 편차). 판정 임계 2/255 는 Phase 2 (DECISIONS D21)")
    (out / "golden_compare.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    diff_sheet(pairs, out / "golden_compare_diff.jpg")
    print(f"mean MAD {result['mean_mad']:.2f}/255, over {MAD_THRESHOLD}: {over or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
