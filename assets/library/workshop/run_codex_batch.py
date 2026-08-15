"""생성된 프롬프트 세트를 codex `$imagegen` 으로 배치 실행한다 (Phase 2 — 3단계).

**codex 가 프롬프트 파일을 디스크에서 직접 읽게** 한다 — 셸 파이프로 본문을 넘기면
인코딩이 깨진다 (실측 2026-08-15: 한글 프롬프트가 mojibake 로 도착해 codex 가 스스로
영어로 재작성했다). 파이프에는 짧은 ASCII 지시만 싣는다.

사용::

    python assets/library/workshop/run_codex_batch.py --only trump      # 1명
    python assets/library/workshop/run_codex_batch.py                   # 미생성분 전부
    python assets/library/workshop/run_codex_batch.py --force           # 기존 산출물도 재생성
    python assets/library/workshop/run_codex_batch.py --dry-run         # 명령만 출력
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "output"
REFS = HERE / "references"
ANCHOR = "style_anchor_portrait_v1.png"

INSTRUCTION = (
    "Read the file {prompt_file} and follow it exactly. "
    "It is an image generation prompt. Use the native imagegen tool "
    "(never HTML/CSS/SVG/Canvas/Pillow). "
    "Save the generated raster image to {out_png}. "
    "Do not modify the prompt file. Do not create any other file."
)


def resolve_codex() -> str:
    for name in ("codex.cmd", "codex"):
        found = shutil.which(name)
        if found:
            return found
    print("error: codex CLI 를 찾을 수 없습니다.", file=sys.stderr)
    sys.exit(1)


def targets(only: list[str] | None, force: bool) -> list[tuple[str, pathlib.Path, pathlib.Path]]:
    out: list[tuple[str, pathlib.Path, pathlib.Path]] = []
    for pf in sorted(OUT.glob("*_mono_v01.prompt.txt")):
        pid = pf.name.removesuffix("_mono_v01.prompt.txt")
        if only and pid not in only:
            continue
        png = OUT / f"{pid}_mono_v01.png"
        if png.exists() and not force:
            continue
        out.append((pid, pf, png))
    return out


def photo_for(pid: str) -> pathlib.Path | None:
    p = REFS / f"photo_{pid}.jpg"
    return p if p.is_file() else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--force", action="store_true", help="기존 PNG 도 재생성")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=900, help="인물당 상한(초)")
    args = ap.parse_args()

    codex = resolve_codex()
    jobs = targets(args.only, args.force)
    if not jobs:
        print("대상 없음 (이미 생성됐거나 프롬프트가 없습니다). --force 로 재생성 가능.")
        return 0

    print(f"대상 {len(jobs)}인\n")
    ok, failed = [], []

    for i, (pid, pf, png) in enumerate(jobs, 1):
        photo = photo_for(pid)
        if not photo:
            print(f"[{i}/{len(jobs)}] {pid}: 입력 사진 없음 — 건너뜀")
            failed.append((pid, "사진 없음"))
            continue

        instruction = INSTRUCTION.format(
            prompt_file=f"output/{pf.name}", out_png=f"output/{png.name}"
        )
        # `--` 필수: `-i/--image` 가 가변 인자(<FILE>...)라 구분자가 없으면 프롬프트
        # 문자열까지 이미지 목록으로 삼켜 "No prompt provided via stdin" 으로 죽는다
        # (실측 2026-08-15: 이것 때문에 16인 배치가 전부 exit 1).
        cmd = [
            codex, "exec", "-C", str(HERE),
            "-s", "workspace-write", "--skip-git-repo-check",
            "-i", f"references/{ANCHOR}",
            "-i", f"references/{photo.name}",
            "--", instruction,
        ]

        print(f"[{i}/{len(jobs)}] {pid} ...", flush=True)
        if args.dry_run:
            print("    " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
            continue

        started = time.monotonic()
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=args.timeout,
            )
        except subprocess.TimeoutExpired:
            print(f"    !! 타임아웃 ({args.timeout}s)")
            failed.append((pid, "timeout"))
            continue

        elapsed = time.monotonic() - started
        if png.exists():
            size = png.stat().st_size
            print(f"    -> {png.name} ({size:,}B, {elapsed:.0f}s)")
            ok.append(pid)
        else:
            tail = (r.stdout or r.stderr or "").strip().splitlines()[-3:]
            print(f"    !! PNG 미생성 (exit {r.returncode}, {elapsed:.0f}s)")
            for line in tail:
                print(f"       {line[:100]}")
            failed.append((pid, f"exit {r.returncode}"))

    print(f"\n성공 {len(ok)} / 실패 {len(failed)}")
    if failed:
        for pid, why in failed:
            print(f"  실패 {pid}: {why}")
    print("\n다음: python assets/library/workshop/make_contact_sheet.py --generated 로 육안 검수")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
