"""프레임 렌더 CLI (v2.1.0, render3 `render_frame, __main__`, 16 §4).

    python -m engine.render <proj> --preview auto|golden|t1,t2,…   → prev/p_TTTT.TT.png, sheet.jpg, provenance.json
    python -m engine.render <proj> --jobs N                → out/video_noaudio.mp4 (N 조각 병렬 → concat)
    python -m engine.render <proj> --chunk START END OUT   → (내부용) 프레임 구간 한 조각
    --res 480p|1080p|trial|final  → 출력 프로파일(v3.6.0, config engine.output). 기본 프로파일이 아니면 프리뷰는 prev_<이름>/

레이어 순서는 v3 와 같다(02 §1): 무대 배경(베이스 → 국경, engine.stage) → 지도 레이어(MAP_LAYER_ORDER) → 라벨 → 하부 암전 → 패널
→ 사진·영상 → 카드·기사 → 날짜 → 전면 카드 → 자막 → 상부 암전 → 전체 페이드. 비네트 없음(라운드 6).
마지막 줄에 StageResult JSON 을 표준 출력으로 낸다. 진행 로그는 표준 오류.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import cairo

from engine.fullcards import draw_fullcards
from engine.hud import draw_date
from engine.project import Project, ProjectError, load_project
from engine.projection import View
from engine.reserved import card_zones
from engine.registry import MAP_LAYER_ORDER, RegistryError
from engine.style import BACKDROP, FADE, FPS, PANEL, output_profile
from engine.subtitles import draw_subtitle
from rules import load_rules
from engine.timebase import smooth, window
from schemas.engine_models import StageResult

REPO = Path(__file__).resolve().parent.parent


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def render_frame(P: Project, i: int) -> tuple[cairo.ImageSurface, bytearray]:  # noqa: N803
    """한 프레임. 모든 레이어는 설계 좌표(854×480)로 그리고, 장치 해상도는 여기서 한 번 건 변환(translate pad_x · scale k)이
    맡는다 — `px()` 의 전역 적용(v3.6.0 D-0067 A). k=1 이면 변환을 걸지 않는다(480p 항등)."""
    R = P.R  # noqa: N806
    OP = R.out  # noqa: N806
    t = i / FPS
    view = View(R.stage, P.cams[i])
    L = P.layers   # noqa: N806 — 전편 FULL_LAYERS · 콘티 판 ANIMATIC_LAYERS(v4.9.0 D-0108, 진입 = load_project)
    R.reserved.clear()
    buf = bytearray(OP.width * OP.height * 4)   # 배경은 무대가 채운다(render_base — 지형 래스터를 이 버퍼에 그대로 복사)
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_RGB24, OP.width, OP.height, OP.width * 4)
    ctx = cairo.Context(surf)
    if OP.k != 1:
        ctx.translate(OP.pad_x, 0)
        ctx.scale(OP.k, OP.k)
    act = [e for e in P.events if e["t0"] - 0.05 <= t <= e["t1"] + 0.05]
    panel_a = max([window(t, e["t0"], e["t1"], PANEL.fade_sec, PANEL.fade_sec) for e in act if e["type"] == "panel"] + [0])
    R.zones = card_zones(ctx, P.events, t)   # 카드 RESERVED — 지도 레이어가 먼저 그려지므로 미리(D-0033). 앞뒤 lead 포함(글자 측정만, 그리지 않음)
    R.stage.render_base(ctx, view)           # 무대 배경: 지형 래스터 + 국경(v4.1.0 D-0076 — MercatorStage = v3 순서 그대로)
    if getattr(R.stage, "border_glow", False):   # v5.3.1 국경선 글로우(시안 — direction stage_config.mercator.border_glow, valdai-2026 한정)
        from engine.layers.borders import draw_border_glow  # noqa: PLC0415

        draw_border_glow(ctx, R.stage, view, t)
    for e in P.events:   # v5.1.0 D-0123 — backdrop 배경 사진: crossfade 로 끝 뒤 crossfade_sec 까지 남는다(act 창 밖)
        if e["type"] == "backdrop" and e["t0"] <= t <= e["t1"] + BACKDROP.crossfade_sec:
            L.resolve(e).render(ctx, R, view, t, e)
    for typ in MAP_LAYER_ORDER:
        for e in act:
            if e["type"] == typ and not e.get("in_island"):   # v5.1.0 D-0126 — 차트 아일랜드 안 이벤트는 island 렌더러가 상자 안에 그린다
                L.resolve(e).render(ctx, R, view, t, e)
    for e in act:   # v5.2.0 겹침 카드(사용자 재구성 2026-10-01) — 지명 라벨 회피(마커·뱃지와 같은 예약 상자). 회피 장치가 없는 해역 이름은 checks cascade 가 잡는다
        if e["type"] == "cascade":
            from engine.cascade import cascade_boxes  # noqa: PLC0415

            R.reserved += cascade_boxes(t, e)
    if panel_a < 0.99:
        R.stage.draw_labels(ctx, view, R.reserved, 1 - panel_a)
    for e in act:
        if e["type"] == "dip" and e.get("under"):
            L.resolve(e).render(ctx, R, t, e)
    for e in act:   # v5.2.0 겹침 카드(시안) — 지도 위·패널 덮개 아래(패널이 뜨면 덮인다)
        if e["type"] == "cascade":
            L.resolve(e).render(ctx, R, t, e)
    for e in act:
        if e["type"] == "panel":
            L.resolve(e).render(ctx, R, t, e)
    for e in act:
        if e["type"] == "badge" and e.get("over_panel"):   # v4.8.0 D-0104 D2(c) — 패널 위 인물 뱃지(화면 고정)
            L.over_panel(ctx, R, t, e)
    for e in act:
        if e["type"] in ("photo", "clip"):
            L.resolve(e).render(ctx, R, t, e)
    for e in act:
        if e["type"] in ("card", "post"):
            L.resolve(e).render(ctx, R, t, e)
        elif e["type"] == "primitive":            # v4.2.0 D-0081 — 무대 무관 오버레이(카드 층), 20 §4.2 draw(ctx, view, t, e, style)
            L.resolve(e).render(ctx, R, view, t, e)
    for e in act:   # v5.3.1 인물 발언 중앙 인용(시안) — 지도·카드 위 덮개 + 가운데 초상·인용문, 기사·날짜·자막 아래
        if e["type"] == "quote":
            L.resolve(e).render(ctx, R, t, e)
    for e in act:   # v5.1.0 D-0121 §C — 기사 프레스 v2: 화면 전체(프레스 사진·블러 무대 + 덮개) — 카드 층 위, 날짜·자막 아래
        if e["type"] == "article":
            L.resolve(e).render(ctx, R, t, e)
    draw_date(ctx, R, t)
    draw_fullcards(ctx, R, t)
    draw_subtitle(ctx, R, t)
    for e in act:
        if e["type"] == "dip" and not e.get("under"):
            L.resolve(e).render(ctx, R, t, e)
    total = P.plan.total
    fa = 1 - min(smooth(t / FADE.in_sec), smooth((total - t) / FADE.out_sec))
    if fa > 0.001:
        ctx.set_source_rgba(0, 0, 0, fa)
        ctx.paint()
    if L.overlay is not None:   # 콘티 판 표식 띠 — 페이드 뒤 맨 위(D-0108)
        L.overlay(ctx, R, t)
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
    # v3.3.0 F6 — 본편(문장을 읽는 중, 전면 카드 밖) 컷이 rules preview.min_body_cuts 보다 적으면 문장 가운데 시각을 고르게 보탠다
    need = load_rules().preview.min_body_cuts

    def body(t: float) -> bool:
        return not tb.in_fullcard(t) and any(s.t0 <= t <= s.t1 for s in tb.sent.values())

    have = sum(body(t) for t in ts)
    if have < need:
        mids = sorted({round(s.t0 + (s.t1 - s.t0) * f, 2) for s in tb.sent.values() for f in (0.25, 0.5, 0.75)})
        mids = [m for m in mids if m not in ts and body(m)]
        k = min(need - have, len(mids))
        ts += [mids[round(i * (len(mids) - 1) / max(1, k - 1))] for i in range(k)] if k > 1 else mids[:k]
    return sorted(set(ts))


PREVIEW_STAGES = {"plan": True, "geo": True, "preview": True, "render": False, "mix": False, "mux": False,
                  "ai_direction": False, "visual_qa": False}   # 돌지 않은 단계는 false 로 명시(D-0041 §1, 15 P5)


def preview_times(P: Project, spec: str) -> list[tuple[str, float]]:  # noqa: N803
    """`auto` · `golden`(골든 25 앵커, D-0041) · 쉼표로 구분한 초 → [(라벨, 시각)]."""
    if spec == "auto":
        return [(f"t={t:.2f}", t) for t in auto_preview_times(P)]
    if spec == "golden":
        from engine.golden import golden_times  # noqa: PLC0415

        return golden_times(P.plan.model_dump())
    return [(f"t={float(x):.2f}", float(x)) for x in spec.split(",")]


def preview(P: Project, times: list[float], labels: list[str] | None = None) -> list[str]:  # noqa: N803
    """prev/p_TTTT.TT.png + prev/sheet.jpg + prev/provenance.json (16 §4, D-0041)."""
    import json  # noqa: PLC0415

    from PIL import Image  # noqa: PLC0415

    from engine.checks import frames_info, run_checks  # noqa: PLC0415
    from engine.mux import project_provenance  # noqa: PLC0415
    from engine.sheet import COLS, grid  # noqa: PLC0415

    out = prev_dir(P)
    out.mkdir(exist_ok=True)
    for old in out.glob("p_*.png"):   # 이전 프리뷰 컷이 섞이지 않게
        old.unlink()
    from engine import typography  # noqa: PLC0415

    paths = []
    drawn: list[tuple[str, float, str | None, str]] = []   # glyph_size(D-0069) — 컷마다 그린 글자
    miss: list[tuple[str, str, str, str]] = []   # v4.4.0 — 그린 글꼴에 없는 글자(checks glyphs)
    from engine.fullcards import EndCardOverflowError  # noqa: PLC0415

    kept: list[tuple[float, str]] = []
    for tt, lab in zip(times, labels or [f"t={t:.2f}" for t in times]):
        typography.GLYPH_LOG, typography.GLYPH_MISS = [], []
        try:
            s, _ = render_frame(P, min(P.n_frames - 1, int(tt * FPS)))
        except EndCardOverflowError as e:
            # 엔딩 카드 크레딧 넘침(D-0098) — 이 컷은 그리지 않고 checks offscreen [endcard-overflow] hard 로 연출 루프에 돌려준다.
            # 전편 렌더(render_chunk)는 같은 오류로 멈춘다(조용한 넘침 금지, 15 P6)
            log(f"preview {lab}: {e}")
            continue
        finally:
            glog, typography.GLYPH_LOG = typography.GLYPH_LOG, None
            gmiss, typography.GLYPH_MISS = typography.GLYPH_MISS, None
        drawn += [(lab, size, role, txt) for size, role, txt in glog]
        miss += [(lab, name, ch, txt) for name, ch, txt in gmiss]
        p = out / f"p_{tt:07.2f}.png"
        s.write_to_png(str(p))
        paths.append(str(p))
        kept.append((tt, lab))
    times, names = [t for t, _ in kept], [n for _, n in kept]
    grid([(Image.open(p), f"{i + 1:02d} {n}" + ("" if n.startswith("t=") else f"  t={t:.2f}"))
          for i, (p, n, t) in enumerate(zip(paths, names, times))],
         COLS, out / "sheet.jpg")
    prov = project_provenance(P, PREVIEW_STAGES)
    prov["preview"] = {"frames": len(paths), "times": [round(t, 3) for t in times], "dir": out.name}
    P.R.cache["glyph_miss"] = miss
    checks = run_checks(P, times, prov, drawn, names)   # 17 §3 결정적 사전 검사(D-0047 작업 6)
    prov["checks"] = {"hard": checks["hard"], "warnings": checks["warnings"], "passed": checks["passed"]}
    (out / "provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "frames.json").write_text(json.dumps(frames_info(P, times, names), ensure_ascii=False, indent=1), encoding="utf-8")
    return paths


def prev_dir(P: Project) -> Path:  # noqa: N803
    """프리뷰 폴더 — 기본 프로파일은 prev/(검수 루프·게이트가 읽는 자리), 그 밖은 prev_<프로파일>/(480p 결과를 덮지 않는다).
    콘티 판은 prev_animatic/(v4.9.0 D-0108 — 게이트가 읽는 prev/ 를 덮지 않는다)."""
    if getattr(P, "animatic", False):
        return P.root / "prev_animatic"
    return P.root / ("prev" if P.R.out == output_profile() else f"prev_{P.R.out.name}")


def render_chunk(P: Project, st: int, en: int, out: Path) -> None:  # noqa: N803
    OP = P.R.out  # noqa: N806
    preset = load_rules().animatic.preset if P.animatic else OP.preset   # 콘티 판 인코딩만(D-0108)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{OP.width}x{OP.height}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(OP.crf),
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


def mem_available_mb() -> int | None:
    try:
        for ln in Path("/proc/meminfo").read_text().splitlines():
            if ln.startswith("MemAvailable:"):
                return int(ln.split()[1]) // 1024
    except OSError:
        return None
    return None


def plan_jobs(requested: int | None, out: "object", cpu: int | None = None, mem_mb: int | None = None) -> tuple[int, str]:
    """청크 병렬 수(v3.6.0 D-0066 작업 6) — 요청(CLI --jobs) → config engine.render.jobs → os.cpu_count() 순,
    그 뒤 사용 가능 메모리 ÷ 프로파일 mem_per_job_mb 로 줄인다(최소 1). (수, 사유)."""
    from orchestrator.config import load_config  # noqa: PLC0415

    cfg = load_config().engine.render.jobs
    j, why = (requested, "--jobs") if requested is not None else (cfg, "config") if cfg is not None else (cpu or os.cpu_count() or 1, "cpu")
    mem = mem_available_mb() if mem_mb is None else mem_mb
    per = out.mem_per_job_mb  # type: ignore[attr-defined]
    if mem is not None and j * per > mem:
        j, why = max(1, mem // per), f"{why}→mem({mem}MB/{per}MB)"
    return j, why


def render_full(P: Project, jobs: int) -> Path:  # noqa: N803
    """전편 → out/video_noaudio.mp4 + render.json. 콘티 판(P.animatic) → out/animatic_noaudio.mp4 + animatic_render.json
    (조각·목록 이름도 animatic_ 접두 — 전편 산출물을 덮지 않는다, D-0108). 콘티 판 mp4 에는 표식 메타데이터(rules animatic.mp4_comment)."""
    outdir = P.root / "out"
    outdir.mkdir(exist_ok=True)
    pre = "animatic_" if P.animatic else ""
    flag = ["--animatic"] if P.animatic else ["--res", P.R.out.name]
    parts, procs = [], []
    t0 = time.time()
    for k, (s, e) in enumerate(chunk_ranges(P.n_frames, jobs)):
        part = outdir / f"{pre}part{k:02d}.mp4"
        parts.append(part)
        logf = open(outdir / f"{pre}part{k:02d}.log", "w", encoding="utf-8")
        procs.append((subprocess.Popen([sys.executable, "-m", "engine.render", str(P.root), *flag,
                                        "--chunk", str(s), str(e), str(part)],
                                       cwd=REPO, stdout=logf, stderr=subprocess.STDOUT), logf))
    fails = []
    for k, (p, logf) in enumerate(procs):
        if p.wait() != 0:
            fails.append(k)
        logf.close()
    if fails:
        raise RuntimeError(f"렌더 조각 실패: {fails} (out/{pre}partNN.log)")
    lst = outdir / f"{pre}parts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    final = outdir / ("animatic_noaudio.mp4" if P.animatic else "video_noaudio.mp4")
    meta = ["-metadata", f"comment={load_rules().animatic.mp4_comment}"] if P.animatic else []
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", *meta, str(final)],
                   check=True)
    log(f"render: {P.n_frames} frames, {len(parts)} chunks, {time.time() - t0:.0f}s")
    # mux 가 provenance render.resolution 에 옮겨 적는다(영상을 만든 프로파일 = 이 파일, 15 P5)
    import resource  # noqa: PLC0415

    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024   # 가장 큰 청크 프로세스(또는 그 ffmpeg) 피크, MB
    (outdir / f"{pre}render.json").write_text(json.dumps({"schema_version": 1, "resolution": P.R.out.record(), "jobs": len(parts),
                                                    "frames": P.n_frames, "sec": round(time.time() - t0, 1),
                                                    "peak_child_rss_mb": peak},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    return final


ANIMATIC_STAGES = {"plan": True, "geo": False, "preview": False, "render": False, "mix": True, "mux": False,
                   "ai_direction": False, "visual_qa": False}   # 콘티 판 — 전편 render·deliver 는 돌지 않았다(render.json 을 읽지 않게, P5)


def render_animatic(P: Project, jobs: int) -> tuple[Path, dict]:  # noqa: N803
    """콘티 판(v4.9.0 back_and_forth D-0108) → out/animatic.mp4 + animatic_checks.json + animatic_provenance.json.
    ① 음성·음악 = 기존 out/mix.f32 그대로(없으면 오류 — audio.mix 먼저) ② checks 콘티 프로파일(hard 면 렌더 전 실패, 프리뷰와 같은 게이트)
    ③ 조각 렌더(자리표시·막지도, 480p·fps 24) ④ 2패스 loudnorm + AAC → animatic.mp4(표식 메타데이터) ⑤ provenance animatic: true."""
    from audio.qa import loudnorm_two_pass, mix_inputs  # noqa: PLC0415
    from engine.checks import run_checks  # noqa: PLC0415
    from engine.mux import AAC_BITRATE, SR, project_provenance  # noqa: PLC0415

    AN = load_rules().animatic  # noqa: N806
    outd = P.root / "out"
    mix = outd / "mix.f32"
    if not mix.exists():
        raise ProjectError(f"out/mix.f32 없음 — 콘티 판도 음성·음악은 그대로 입힌다: `python -m audio.mix {P.root}` 먼저")
    outd.mkdir(exist_ok=True)
    t0 = time.time()
    prov = project_provenance(P, ANIMATIC_STAGES)
    times = auto_preview_times(P)
    checks = run_checks(P, times, prov, [], [f"t={t:.2f}" for t in times])
    (outd / "animatic_checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=1), encoding="utf-8")
    if not checks["passed"]:
        errs = [f"checks hard {i['id']}: {d}" for i in checks["items"] if i["severity"] == "hard" for d in i["details"]]
        raise ProjectError("콘티 판 checks hard 실패(렌더 전):\n" + "\n".join(errs[:50]))
    video = render_full(P, jobs)
    t1 = time.time()
    final = outd / AN.output
    af, loud = loudnorm_two_pass(mix, P.plan.total)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), *mix_inputs(mix, P.plan.total),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", af, "-ar", str(SR), "-c:a", "aac", "-b:a", AAC_BITRATE,
                    "-t", f"{P.plan.total:.3f}", "-movflags", "+faststart", "-metadata", f"comment={AN.mp4_comment}", str(final)],
                   check=True)
    rj = json.loads((outd / "animatic_render.json").read_text(encoding="utf-8"))
    kinds: dict[str, int] = {}
    from engine.layers.animatic import PLACEHOLDERS, flat_map_source  # noqa: PLC0415

    for e in P.events:
        if e["type"] in PLACEHOLDERS:
            kinds[e["type"]] = kinds.get(e["type"], 0) + 1
    prov["animatic"] = True
    prov["animatic_run"] = {"output": f"out/{AN.output}", "profile": P.R.out.name, "fps": FPS, "preset": AN.preset,
                            "band": AN.band.text, "placeholders": dict(sorted(kinds.items())),
                            "flat_map": flat_map_source() if "mercator" in P.R.cache["stage"]["instances"] else None,
                            "voice": P.plan.voice, "checks_skipped": checks["skipped"],
                            # v5.2.0 — 어느 연출 판으로 만든 콘티 판인지(게이트 ② 기록, orchestrator.project_manager.require_animatic)
                            "direction_sha1": hashlib.sha1((P.root / "direction.yaml").read_bytes()).hexdigest()
                            if (P.root / "direction.yaml").exists() else None,
                            "sec": {"render": rj["sec"], "total": round(time.time() - t0, 1), "mux": round(time.time() - t1, 1)},
                            "jobs": rj["jobs"], "frames": rj["frames"], "loudnorm": {"passes": 2, **loud},
                            "bytes": final.stat().st_size}
    prov["checks"] = {"hard": checks["hard"], "warnings": checks["warnings"], "passed": checks["passed"], "profile": checks["profile"]}
    (outd / "animatic_provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    return final, prov


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="engine.render")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--preview", help="auto · golden(골든 25 앵커) · 쉼표로 구분한 초")
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--chunk", nargs=3, metavar=("START", "END", "OUT"))
    ap.add_argument("--res", default=None, help="출력 프로파일(config engine.output.profiles 이름 또는 trial·final)")
    ap.add_argument("--animatic", action="store_true",
                    help="콘티 판(v4.9.0 D-0108) → out/animatic.mp4 — 막지도·자리표시·표식 띠, 480p 고정. --preview 와 함께면 prev_animatic/")
    args = ap.parse_args(argv)
    stage = "preview" if args.preview else "render"
    try:
        if args.animatic and args.res is not None:
            raise ProjectError("--animatic 은 rules animatic.profile 고정 — --res 와 함께 쓰지 않는다")
        P = load_project(args.proj, out=None if args.animatic else output_profile(args.res), animatic=args.animatic)  # noqa: N806
        if args.chunk:
            render_chunk(P, int(args.chunk[0]), int(args.chunk[1]), Path(args.chunk[2]))
            return 0
        if args.preview:
            lt = preview_times(P, args.preview)
            arts = {f"{prev_dir(P).name}/{Path(p).name}": p for p in preview(P, [t for _, t in lt], [n for n, _ in lt])}
            pd = prev_dir(P)
            arts["sheet"] = str(pd / "sheet.jpg")
            arts["provenance"] = str(pd / "provenance.json")
            arts["checks"] = str(pd / "checks.json")
            arts["frames"] = str(pd / "frames.json")
            chk = json.loads((pd / "checks.json").read_text(encoding="utf-8"))
            if not chk["passed"]:   # hard 실패 = 이 단계 실패 — 시각 검수로 가지 않고 연출에 오류를 돌려준다(17 §3, D-0048)
                errs = [f"checks hard {i['id']}: {d}" for i in chk["items"] if i["severity"] == "hard" for d in i["details"]]
                res = StageResult(ok=False, stage=stage, artifacts=arts, warnings=P.warnings, errors=errs[:50])
                print(json.dumps(res.model_dump(), ensure_ascii=False))
                return 1
        elif args.animatic:
            jobs, why = plan_jobs(args.jobs, P.R.out)
            log(f"jobs {jobs} ({why}) animatic")
            final, _ = render_animatic(P, jobs)
            outd = P.root / "out"
            arts = {"animatic": str(final), "provenance": str(outd / "animatic_provenance.json"), "checks": str(outd / "animatic_checks.json")}
        else:
            jobs, why = plan_jobs(args.jobs, P.R.out)
            log(f"jobs {jobs} ({why})")
            arts = {"video_noaudio": str(render_full(P, jobs))}
        res = StageResult(ok=True, stage=stage, artifacts=arts, warnings=P.warnings)
    except (ProjectError, RegistryError, RuntimeError, OSError, ValueError) as ex:
        res = StageResult(ok=False, stage=stage, errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
