"""legacy_v3 단계 실행기 (v2.0.1, back_and_forth D-0002·D-0006) — Phase 1 골든 재현을 명령 한 줄씩으로.

`legacy_v3/*.py`는 경로만 바꾼 원본이라 인자 체계가 제각각이다. 이 실행기는 원본을 고치지 않고
환경변수·인자만 맞춰 부른다(19 §3.9). 단계:

    plan      --tts edge|elevenlabs   plan3 (골든은 반드시 edge — ElevenLabs 키가 환경에 있어도 지운다)
    prep      [fonts geo base people flags]   prep3
    media     tools/fetch_data.py media (media3 1차 + 2차)
    render    --jobs N                render3 를 N 조각 병렬 → concat → video_noaudio.mp4
    mix       mix3 → mix.f32
    mux       ffmpeg loudnorm(I=-14 TP=-1.5 LRA=11) + AAC 192k → out/final.mp4 (docs/handoff/10 §5)
    subs      out/final.srt, out/description.txt (골든 설명문의 챕터 시각만 현재 plan 으로 갱신)
    audio     오디오 리포트 → REPORT_DIR/audio_report.json

환경: V3_ROOT(기본 projects/hormuz_korea_legacy), OG_ROOT(기본 저장소 루트).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEG = REPO / "legacy_v3"
GOLDEN_DIR = REPO / "docs" / "handoff" / "golden"
DEFAULT_REPORT = REPO / "docs" / "handoff" / "reports" / "phase1"
FPS = 24          # render3 FPS (원본 상수 — 읽기만)
SR = 44100        # mix3 SR
LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=11"
ELEVEN_ENV = ("ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID")


def v3_root() -> Path:
    return (REPO / os.environ.get("V3_ROOT", "projects/hormuz_korea_legacy")).resolve()


def env_for(root: Path, tts: str = "edge") -> dict[str, str]:
    env = {**os.environ, "V3_ROOT": str(root), "OG_ROOT": os.environ.get("OG_ROOT", str(REPO))}
    if tts == "edge":
        for k in ELEVEN_ENV:
            env.pop(k, None)
    return env


def run(cmd: list[str], env: dict[str, str]) -> None:
    print("$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, env=env, cwd=REPO)


def load_plan(root: Path) -> dict:
    return json.loads((root / "plan.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ 순수 함수 (테스트 대상)
def chunk_ranges(n_frames: int, jobs: int) -> list[tuple[int, int]]:
    """[0, n) 을 jobs 조각으로. 빈 조각 없음."""
    jobs = max(1, min(jobs, n_frames))
    step = -(-n_frames // jobs)
    return [(s, min(n_frames, s + step)) for s in range(0, n_frames, step)]


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


SRT_TAIL_SEC = 0.15  # 골든 SRT 실측: 끝 = t1 + 0.15 (45문장 전부)


def build_srt(plan: dict) -> str:
    """골든 hormuz_korea_ko.srt 와 같은 규칙: 시작 t0, 끝 t1 + 0.15, 자막 텍스트(발음 텍스트 아님)."""
    out = []
    for i, x in enumerate(plan["sentences"], 1):
        out.append(f"{i}\n{srt_time(x['t0'])} --> {srt_time(x['t1'] + SRT_TAIL_SEC)}\n{x['text']}\n")
    return "\n".join(out)


def chapter_times(plan: dict) -> list[float]:
    """골든 설명문 챕터 순서: open, 타이틀, 이후 장면 순서(scene_start 삽입 순서)."""
    sc = plan["scene_start"]
    title = next(c["t0"] for c in plan["cards"] if c["kind"] == "title")
    names = list(sc)
    return [0.0, float(title)] + [float(sc[n]) for n in names[1:]]


def mmss(t: float) -> str:
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def build_description(plan: dict, golden_text: str) -> str:
    """골든 설명문에서 챕터 줄의 시각만 현재 plan 으로 바꾼다(문안 무변경)."""
    lines = golden_text.splitlines()
    idx = [i for i, ln in enumerate(lines) if re.match(r"^\d+:\d{2} ", ln)]
    times = chapter_times(plan)
    if len(idx) != len(times):
        raise ValueError(f"챕터 수 불일치: 설명문 {len(idx)} / plan {len(times)}")
    for i, t in zip(idx, times):
        lines[i] = mmss(t) + lines[i][lines[i].index(" "):]
    return "\n".join(lines) + ("\n" if golden_text.endswith("\n") else "")


# ------------------------------------------------------------------ 단계
def step_plan(root: Path, args: argparse.Namespace) -> None:
    run([sys.executable, str(LEG / "plan3.py")], env_for(root, args.tts))
    p = load_plan(root)
    print(f"plan: {len(p['sentences'])} sentences, total {p['total']:.2f}s, voice {p['voice']}")
    if args.tts == "edge" and not p["voice"].startswith("edge"):
        raise SystemExit(f"골든 재현은 edge 여야 한다: voice={p['voice']}")


def step_prep(root: Path, args: argparse.Namespace) -> None:
    run([sys.executable, str(LEG / "prep3.py"), *args.what], env_for(root))


def step_media(root: Path, args: argparse.Namespace) -> None:
    run([sys.executable, str(REPO / "tools" / "fetch_data.py"), "media"], env_for(root))


def step_render(root: Path, args: argparse.Namespace) -> None:
    n = int(load_plan(root)["total"] * FPS)
    parts = []
    procs = []
    t0 = time.time()
    for k, (s, e) in enumerate(chunk_ranges(n, args.jobs)):
        out = root / f"part{k:02d}.mp4"
        parts.append(out)
        log = open(root / f"part{k:02d}.log", "w", encoding="utf-8")
        procs.append((subprocess.Popen([sys.executable, str(LEG / "render3.py"), str(s), str(e), str(out)],
                                       env=env_for(root), cwd=REPO, stdout=log, stderr=subprocess.STDOUT), log))
    fails = []
    for k, (p, log) in enumerate(procs):
        if p.wait() != 0:
            fails.append(k)
        log.close()
    if fails:
        raise SystemExit(f"render 조각 실패: {fails} (V3_ROOT/partNN.log)")
    lst = root / "parts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
         str(root / "video_noaudio.mp4")], env_for(root))
    print(f"render: {n} frames, {len(parts)} chunks, {time.time() - t0:.0f}s")


def step_mix(root: Path, args: argparse.Namespace) -> None:
    run([sys.executable, str(LEG / "mix3.py")], env_for(root))


def step_mux(root: Path, args: argparse.Namespace) -> None:
    total = load_plan(root)["total"]
    (root / "out").mkdir(exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", str(root / "video_noaudio.mp4"),
         "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(root / "mix.f32"),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", LOUDNORM, "-ar", str(SR),
         "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart",
         str(root / "out" / "final.mp4")], env_for(root))


def step_subs(root: Path, args: argparse.Namespace) -> None:
    plan = load_plan(root)
    out = root / "out"
    out.mkdir(exist_ok=True)
    (out / "final.srt").write_text(build_srt(plan), encoding="utf-8")
    golden = (GOLDEN_DIR / "youtube_description.txt").read_text(encoding="utf-8")
    (out / "description.txt").write_text(build_description(plan, golden), encoding="utf-8")
    print(f"subs: {out / 'final.srt'}, {out / 'description.txt'}")


def step_audio(root: Path, args: argparse.Namespace) -> None:
    from audio_report import audio_report  # noqa: PLC0415 — tools/audio_report.py

    rep = audio_report(root, load_plan(root))
    args.report.mkdir(parents=True, exist_ok=True)
    (args.report / "audio_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False))


STEPS = {"plan": step_plan, "prep": step_prep, "media": step_media, "render": step_render,
         "mix": step_mix, "mux": step_mux, "subs": step_subs, "audio": step_audio}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="legacy_v3 단계 실행기")
    ap.add_argument("step", choices=list(STEPS))
    ap.add_argument("what", nargs="*", default=[], help="prep 단계 인자 (fonts geo base people flags)")
    ap.add_argument("--tts", choices=["edge", "elevenlabs"], default="edge")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = ap.parse_args(argv)
    root = v3_root()
    for sub in ("prev", "tts", "out"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    STEPS[args.step](root, args)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
