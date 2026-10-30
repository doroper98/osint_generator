"""AI 상투 문구 점검기(v7.4.0 back_and_forth D-0281, 사용자 의견 UF-145) — 보고문·검토 문서를 보내기 전에 돌린다.

    python tools/slop_check.py back_and_forth/<R 문서>.md      # 파일(여럿 가능)
    python tools/slop_check.py -  < 문안.txt                      # 표준입력
    python tools/slop_check.py projects/<pid>                     # 프로젝트 원고 밖 화면 문자열·검토 문서(script.slop)

패턴은 rules/video_rules.yaml banned_phrases.patterns(원고 린트와 같은 목록). 걸리면 "위치 | 줄 | 패턴" 을 찍고 종료 코드 1.
문서의 YAML 머리말(--- … ---)과 코드 블록(``` … ```)은 보지 않는다(경로·식별자 오탐 방지).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from script.slop import patterns, project_slop, slop_hits  # noqa: E402


def text_lines(text: str) -> list[tuple[int, str]]:
    """검사할 (줄 번호, 줄) — 머리말·코드 블록 제외."""
    out, fence, front = [], False, False
    for n, ln in enumerate(text.splitlines(), 1):
        if n == 1 and ln.strip() == "---":
            front = True
            continue
        if front:
            front = ln.strip() != "---"
            continue
        if ln.strip().startswith("```"):
            fence = not fence
            continue
        if not fence:
            out.append((n, ln))
    return out


def check_text(name: str, text: str) -> list[str]:
    pats = patterns()
    return [f"{name}:{n} | {ln.strip()} | {p}" for n, ln in text_lines(text) for p in slop_hits(ln, pats)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AI 상투 문구 점검(banned_phrases.patterns)")
    ap.add_argument("paths", nargs="+", help="파일·프로젝트 폴더 또는 - (표준입력)")
    args = ap.parse_args(argv)
    hits: list[str] = []
    for a in args.paths:
        if a == "-":
            hits += check_text("<stdin>", sys.stdin.read())
        elif Path(a).is_dir():
            hits += [f"{a}/{w} | {s.strip()} | {p}" for w, s, p in project_slop(Path(a))]
        else:
            hits += check_text(a, Path(a).read_text(encoding="utf-8"))
    print("\n".join(hits) if hits else "ok — 상투 문구 0")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
