"""프레임 렌더 CLI (v2.1.0, render3 `render_frame, __main__`, 16 §4).

    python -m engine.render <proj> --preview auto|t1,t2,…   → prev/p_TTTT.TT.png
    python -m engine.render <proj> --jobs N                → out/video_noaudio.mp4 (N 조각 병렬 → concat)
    python -m engine.render <proj> --chunk START END OUT   → (내부용) 프레임 구간 한 조각

레이어 순서는 v3 와 같다(02 §1): 베이스 → 국경 → 지도 레이어(MAP_LAYER_ORDER) → 라벨 → 하부 암전 → 패널
→ 사진·영상 → 카드·기사 → 날짜 → 전면 카드 → 자막 → 상부 암전 → 전체 페이드. 비네트 없음(라운드 6).
마지막 줄에 StageResult JSON 을 표준 출력으로 낸다. 진행 로그는 표준 오류.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import cairo

from engine.fullcards import draw_fullcards
from engine.hud import draw_date
from engine.layers.borders import draw_borders
from engine.layers.labels import draw_labels
from engine.project import Project, ProjectError, load_project
from engine.projection import View
from engine.registry import MAP_LAYER_ORDER, RegistryError, resolve
from engine.style import CRF, FADE, FPS, H_OUT, PANEL, W_OUT
from engine.subtitles import draw_subtitle
from engine.timebase import smooth, window
from schemas.engine_models import StageResult

REPO = Path(__file__).resolve().parent.parent


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def render_frame(P: Project, i: int) -> tuple[cairo.ImageSurface, bytearray]:  # noqa: N803
    R = P.R  # noqa: N806
    t = i / FPS
    view = View(P.cams[i], R.assets.tiers, R.assets.base)
    R.reserved.clear()
    im = view.base()
    buf = bytearray(im.tobytes("raw", "BGRX"))
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, W_OUT, H_OUT, W_OUT * 4)
    ctx = cairo.Context(surf)
    act = [e for e in P.events if e["t0"] - 0.05 <= t <= e["t1"] + 0.05]
    panel_a = max([window(t, e["t0"], e["t1"], PANEL.fade_sec, PANEL.fade_sec) for e in act if e["type"] == "panel"] + [0])
    draw_borders(ctx, R, view)
    for L in MAP_LAYER_ORDER:  # noqa: N806
        for e in act:
            if e["type"] == L:
                resolve(e).render(ctx, R, view, t, e)
    if panel_a < 0.99:
        draw_labels(ctx, R, view, t, 1 - panel_a)
    for e in act:
        if e["type"] == "dip" and e.get("under"):
            resolve(e).render(ctx, R, t, e)
    for e in act:
        if e["type"] == "panel":
            resolve(e).render(ctx, R, t, e)
    for e in act:
        if e["type"] in ("photo", "clip"):
            resolve(e).render(ctx, R, t, e)
    for e in act:
        if e["type"] in ("card", "article"):
            resolve(e).render(ctx, R, t, e)
    draw_date(ctx, R, t)
    draw_fullcards(ctx, R, t)
    draw_subtitle(ctx, R, t)
    for e in act:
        if e["type"] == "dip" and not e.get("under"):
            resolve(e).render(ctx, R, t, e)
    total = P.plan.total
    fa = 1 - min(smooth(t / FADE.in_sec), smooth((total - t) / FADE.out_sec))
    if fa > 0.001:
        ctx.set_source_rgba(0, 0, 0, fa)
        ctx.paint()
    surf.flush()
    return surf, buf


def auto_preview_times(P: Project) -> list[float]:  # noqa: N803
    """장면마다 30%·70% 지점 + 타이틀·엔딩 카드 가운데."""
    tb = P.R.tb
    ts = []
    for sc in tb.scenes:
        a, b = tb.SC(sc), tb.SC_END(sc)
        ts += [round(a + (b - a) * 0.3, 2), round(a + (b - a) * 0.7, 2)]
    for c in P.plan.cards:
        ts.append(round((c.t0 + c.t1) / 2, 2))
    return sorted(ts)


def preview(P: Project, times: list[float]) -> list[str]:  # noqa: N803
    out = P.root / "prev"
    out.mkdir(exist_ok=True)
    paths = []
    for tt in times:
        s, _ = render_frame(P, min(P.n_frames - 1, int(tt * FPS)))
        p = out / f"p_{tt:07.2f}.png"
        s.write_to_png(str(p))
        paths.append(str(p))
    return paths


def render_chunk(P: Project, st: int, en: int, out: Path) -> None:  # noqa: N803
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{W_OUT}x{H_OUT}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "faster", "-crf", str(CRF),
                           "-pix_fmt", "yuv420p", "-g", "48", str(out)], stdin=subprocess.PIPE)
    assert ff.stdin is not None
    t0 = time.time()
    for i in range(st, en):
        _, b = render_frame(P, i)
        ff.stdin.write(b)
        if (i - st) % 480 == 0:
            log(f"frame {i}/{en} {time.time() - t0:.0f}s")
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError(f"ffmpeg 실패: {out}")


def chunk_ranges(n_frames: int, jobs: int) -> list[tuple[int, int]]:
    jobs = max(1, min(jobs, n_frames))
    step = -(-n_frames // jobs)
    return [(s, min(n_frames, s + step)) for s in range(0, n_frames, step)]


def render_full(P: Project, jobs: int) -> Path:  # noqa: N803
    outdir = P.root / "out"
    outdir.mkdir(exist_ok=True)
    parts, procs = [], []
    t0 = time.time()
    for k, (s, e) in enumerate(chunk_ranges(P.n_frames, jobs)):
        part = outdir / f"part{k:02d}.mp4"
        parts.append(part)
        logf = open(outdir / f"part{k:02d}.log", "w", encoding="utf-8")
        procs.append((subprocess.Popen([sys.executable, "-m", "engine.render", str(P.root), "--chunk", str(s), str(e), str(part)],
                                       cwd=REPO, stdout=logf, stderr=subprocess.STDOUT), logf))
    fails = []
    for k, (p, logf) in enumerate(procs):
        if p.wait() != 0:
            fails.append(k)
        logf.close()
    if fails:
        raise RuntimeError(f"렌더 조각 실패: {fails} (out/partNN.log)")
    lst = outdir / "parts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    final = outdir / "video_noaudio.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(final)],
                   check=True)
    log(f"render: {P.n_frames} frames, {len(parts)} chunks, {time.time() - t0:.0f}s")
    return final


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="engine.render")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--preview", help="auto 또는 쉼표로 구분한 초")
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--chunk", nargs=3, metavar=("START", "END", "OUT"))
    args = ap.parse_args(argv)
    stage = "preview" if args.preview else "render"
    try:
        P = load_project(args.proj)  # noqa: N806
        if args.chunk:
            render_chunk(P, int(args.chunk[0]), int(args.chunk[1]), Path(args.chunk[2]))
            return 0
        if args.preview:
            times = auto_preview_times(P) if args.preview == "auto" else [float(x) for x in args.preview.split(",")]
            arts = {f"prev/{Path(p).name}": p for p in preview(P, times)}
        else:
            from orchestrator.config import load_config  # noqa: PLC0415

            jobs = args.jobs if args.jobs is not None else load_config().engine.jobs
            arts = {"video_noaudio": str(render_full(P, jobs))}
        res = StageResult(ok=True, stage=stage, artifacts=arts, warnings=P.warnings)
    except (ProjectError, RegistryError, RuntimeError, OSError) as ex:
        res = StageResult(ok=False, stage=stage, errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
