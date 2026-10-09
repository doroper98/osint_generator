"""스케치 CLI 공통 인자(D-0140 §3) — 프로젝트 폴더 하나, spec = `<project>/sketch.yaml`."""

from __future__ import annotations

import argparse
from pathlib import Path


def base_parser(prog: str, description: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog=prog, description=description)
    ap.add_argument("project", type=Path, help="프로젝트 폴더(spec = <project>/sketch.yaml, 산출 = <project>/out/)")
    ap.add_argument("--frames", default=None, help="쉼표로 구분한 초 — 정지 화면만(검사·테스트용)")
    ap.add_argument("--check", action="store_true", help="렌더 없이 검사만(종료 코드 ≠ 0 = hard 위반)")
    ap.add_argument("--res", default="trial",
                    help="출력 프로파일(config engine.output 이름·별칭). 기본 trial(테스트) — 사용자 전달본은 final")
    return ap


def parse_frames(arg: str | None) -> list[float]:
    """'5,27.5' → [5.0, 27.5]. 빈 값·숫자 아님은 오류."""
    if not arg:
        return []
    try:
        return [float(s) for s in arg.split(",") if s.strip()]
    except ValueError as e:
        raise SystemExit(f"--frames 형식 오류 {arg!r}: {e}") from e
