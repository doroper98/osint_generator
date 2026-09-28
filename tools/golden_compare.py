"""골든 25컷 대조 (v2.0.1, v2.3.0 새 엔진 전용, back_and_forth D-0002 작업 4 · D-0006 §2 · D-0024).

`docs/handoff/golden/golden_frames.json`의 앵커(문장 id + 오프셋)를 **현재 plan.json 으로 시각 재계산**하고,
새 엔진(`python -m engine.render --preview`)으로 같은 앵커 프레임을 렌더해 기준 PNG와 평균 절대 차이(MAD, /255)를 잰다.
음성이 재합성되면 절대 시각이 달라지므로 비교는 반드시 앵커 기준이다(골든 README).
v2.3.0: 옛 v3 렌더러 경로(`--engine legacy`)는 삭제했다(D32). 골든 대조 기준은 `--reference golden`(R-0016 §6, 1.825).

의도된 차이(D34, back_and_forth D-0026): `docs/handoff/golden/expected_deltas.json`
`{"NN_anchor": {reason, decision, old_t, new_t | old_lonlat, new_lonlat}}`에 등재된 컷만 MAD 기준에서 빼고 결과에 `intended_delta: true`로 적는다.
등재 없이 기준을 넘으면 종전대로 불합격이다. 골든 PNG 는 바꾸지 않는다.

앵커 규칙: 문장 id → `sentence.t0 + offset`, `TITLE` → `cards[title].t0 + offset`, `END` → `total + offset`.

사용법:
    python tools/golden_compare.py --dry-run                                   # 골든 절대 시각 25개 출력
    python tools/golden_compare.py --reference golden --out DIR                # 골든 PNG 와 대조(참고값)
    python tools/golden_compare.py --ref docs/handoff/reports/phase2/frames    # 무손실 기준 프레임과 대조(판정)

출력(DIR): golden_compare.json, golden_compare_diff.jpg, frames/{NN}_{anchor}.png
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO / "docs" / "handoff" / "golden"
DEFAULT_OUT = REPO / "docs" / "handoff" / "reports" / "phase1"
PHASE1_FRAMES = REPO / "docs" / "handoff" / "reports" / "phase1" / "frames"
PHASE2_OUT = REPO / "docs" / "handoff" / "reports" / "phase2"
NEW_MEAN_MAX, NEW_FRAME_MAX = 1.0, 2.0  # D-0010 §2: 무손실끼리 평균 < 1.0, 최대 < 2.0
MAD_THRESHOLD = 2.0  # /255 — Phase 2 판정 임계. Phase 1 은 참고값(D-0005 결정 1)


def load_expected_deltas() -> dict[str, dict]:
    p = GOLDEN_DIR / "expected_deltas.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    for k, v in d.get("deltas", {}).items():
        missing = {"reason", "decision"} - set(v)
        # 무엇이 바뀌었나 — 시각(D34 단어 정렬) 또는 좌표(D36 부산 뱃지) 한 쌍이 있어야 한다
        if not ({"old_t", "new_t"} <= set(v) or {"old_lonlat", "new_lonlat"} <= set(v)):
            missing |= {"old_t|old_lonlat", "new_t|new_lonlat"}
        if missing:
            raise ValueError(f"expected_deltas.json {k}: 필드 누락 {sorted(missing)}")
    return d.get("deltas", {})


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
    subprocess.run([sys.executable, "-m", "engine.render", str(root), "--preview", arg], check=True, cwd=REPO)
    return [root / "prev" / f"p_{float(f'{t:.2f}'):07.2f}.png" for t in times]


def diff_sheet(pairs: list[tuple[str, "object", "object", float]], dest: Path) -> None:
    """기준 | 렌더 | 차이 히트맵 3열, 컷마다 한 줄 (427×240 축소)."""
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


def compare_new(args: argparse.Namespace) -> int:
    """새 엔진 프리뷰 ↔ Phase 1 legacy 무손실 프레임(같은 앵커). 판정: 평균 < 1.0, 최대 < 2.0."""
    from PIL import Image

    golden = load_golden()
    frames = golden["frames"]
    proj = args.proj.resolve()
    plan = json.loads((proj / "plan.json").read_text(encoding="utf-8"))
    times = [anchor_time(f["anchor"], float(f["offset"]), plan) for f in frames]
    pngs = render_previews(times, proj)
    out = PHASE2_OUT if args.out == DEFAULT_OUT else args.out
    (out / "frames").mkdir(parents=True, exist_ok=True)
    rows, pairs = [], []
    golden_ref = args.reference == "golden"
    deltas = load_expected_deltas()
    for i, (f, t, png) in enumerate(zip(frames, times, pngs), 1):
        name = f"{i:02d}_{f['anchor']}.png"
        ref = Image.open((GOLDEN_DIR / f["file"]) if golden_ref else (args.ref / name)).convert("RGB")
        r = Image.open(png).convert("RGB")
        m = mad(ref, r)
        shutil.copy2(png, out / "frames" / name)
        key = name[:-4]
        rows.append(dict(n=i, anchor=f["anchor"], offset=f["offset"], t_now=round(t, 3), mad=round(m, 4),
                         over=m >= NEW_FRAME_MAX, frame=f"frames/{name}", intended_delta=key in deltas))
        pairs.append((f"{i:02d} {f['anchor']}{f['offset']:+.1f}  t={t:.2f}", ref, r, m))
        print(f"{i:02d} {f['anchor']:<12} t={t:7.2f}  MAD {m:7.4f}", flush=True)
    judged = [r for r in rows if not r["intended_delta"]]   # 의도된 차이(D34)는 판정에서 뺀다
    mean = sum(r["mad"] for r in judged) / len(judged)
    mx = max(r["mad"] for r in judged)
    ok = mean < NEW_MEAN_MAX and mx < NEW_FRAME_MAX
    if golden_ref:  # 골든은 H.264 추출본 — 코덱 차가 섞인 참고값(D-0009 §1). 판정 임계는 Phase 1 과 같은 2/255 참고선
        ok = mean < MAD_THRESHOLD
        for r in rows:
            r["over"] = r["mad"] > MAD_THRESHOLD
    ref_desc = ("골든 PNG(docs/handoff/golden, H.264 추출본) — 참고값" if golden_ref
                else f"무손실 프리뷰({args.ref.relative_to(REPO) if args.ref.is_relative_to(REPO) else args.ref})")
    result = dict(schema_version=1, engine="new", reference=ref_desc,
                  mean_max=NEW_MEAN_MAX, frame_max=NEW_FRAME_MAX, mean_mad=round(mean, 4), max_mad=round(mx, 4),
                  passed=ok, over_threshold=[r["anchor"] for r in judged if r["over"]],
                  intended_deltas=[r["anchor"] for r in rows if r["intended_delta"]], frames=rows)
    (out / "golden_compare.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    diff_sheet(pairs, out / "golden_compare_diff.jpg")
    print(f"mean MAD {mean:.4f}/255, max {mx:.4f} (의도된 차이 {len(rows) - len(judged)}컷 제외) -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="골든 25컷 앵커 대조(새 엔진)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--dry-run", action="store_true", help="plan 없이 골든 절대 시각만 출력")
    ap.add_argument("--engine", choices=["new"], default="new", help="새 엔진만(옛 v3 렌더러 경로는 v2.3.0 삭제, D32)")
    ap.add_argument("--proj", type=Path, default=REPO / "projects" / "hormuz_korea", help="프로젝트")
    ap.add_argument("--ref", type=Path, default=PHASE1_FRAMES, help="--reference frames 기준 프레임 폴더")
    ap.add_argument("--reference", choices=["frames", "golden"], default="frames",
                    help="frames = --ref 무손실 프레임(판정), golden = 골든 PNG(H.264 추출본, 참고값)")
    args = ap.parse_args(argv)
    if args.dry_run:
        golden = load_golden()
        frames = golden["frames"]
        print(f"golden total {golden['total']:.2f}s, {len(frames)} anchors")
        for i, f in enumerate(frames, 1):
            print(f"{i:02d} {f['anchor']:<12} {f['offset']:+5.1f}  t={f['t']:7.2f}  {f['file']}")
        return 0
    return compare_new(args)


if __name__ == "__main__":
    sys.exit(main())
