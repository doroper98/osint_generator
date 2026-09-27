"""back_and_forth 감시 도구 — 내가 아직 답하지 않은 상대 파일을 나열한다 (README §5).

표준 라이브러리만 쓴다. 호출 전에 `git pull --rebase` 로 원격 상태를 받아 둔다.

사용법:
    python back_and_forth/check.py --me opus     # 미처리 D 파일 (Opus 용)
    python back_and_forth/check.py --me fable    # 미처리 R 파일 (Fable 용)
    python back_and_forth/check.py --me opus --next-id   # 내가 쓸 다음 파일 번호

종료 코드: 0 = 새 파일 없음, 10 = 새 파일 있음, 2 = 규칙 위반 파일 발견(머리말·이름 오류).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME_RE = re.compile(r"^(?P<kind>[RD])-(?P<num>\d{4})_(?P<ts>\d{8}-\d{4})_(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
MINE = {"opus": "R", "fable": "D"}


def front_matter(path: Path) -> dict[str, str]:
    """머리말 YAML 의 `키: 값` 한 줄 항목만 읽는다(주석 제거). 형식 오류면 빈 dict."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    out: dict[str, str] = {}
    for line in text[4:end].splitlines():
        line = line.split("#", 1)[0].rstrip()
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def id_list(raw: str) -> list[str]:
    return re.findall(r"[RD]-\d{4}", raw or "")


def scan() -> tuple[dict[str, tuple[Path, dict[str, str]]], list[str]]:
    files: dict[str, tuple[Path, dict[str, str]]] = {}
    errors: list[str] = []
    for p in sorted(HERE.glob("[RD]-*.md")):
        m = NAME_RE.match(p.name)
        if not m:
            errors.append(f"이름 규칙 위반: {p.name}")
            continue
        fm = front_matter(p)
        fid = f"{m['kind']}-{m['num']}"
        if fm.get("id") != fid:
            errors.append(f"머리말 id 불일치: {p.name} (id={fm.get('id')!r})")
            continue
        files[fid] = (p, fm)
    return files, errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--me", choices=sorted(MINE), required=True)
    ap.add_argument("--next-id", action="store_true", help="내가 쓸 다음 파일 id 출력")
    args = ap.parse_args()

    files, errors = scan()
    mine_kind = MINE[args.me]
    theirs_kind = "D" if mine_kind == "R" else "R"

    if args.next_id:
        nums = [int(fid[2:]) for fid in files if fid.startswith(mine_kind)]
        print(f"{mine_kind}-{(max(nums) + 1) if nums else 1:04d}")
        return 0

    answered: set[str] = set()
    superseded: set[str] = set()
    for fid, (_, fm) in files.items():
        if fid.startswith(mine_kind):
            answered.update(id_list(fm.get("responds_to", "")))
        superseded.update(id_list(fm.get("supersedes", "")))

    pending = []
    for fid, (path, fm) in sorted(files.items()):
        if not fid.startswith(theirs_kind) or fid in answered or fid in superseded:
            continue
        if theirs_kind == "D" and fm.get("status", "open") != "open":
            continue
        prio = fm.get("priority", "normal")
        if fm.get("kind") == "decision_request":
            prio = "urgent"  # README §6.2 — 결정 요청은 먼저 처리
        pending.append((fid, path.name, fm.get("kind", "?"), prio))

    for e in errors:
        print(f"ERROR {e}")
    if not pending:
        print("new: 0")
        return 2 if errors else 0
    order = {"urgent": 0, "normal": 1, "low": 2}
    pending.sort(key=lambda r: (order.get(r[3], 1), r[0]))
    print(f"new: {len(pending)}")
    for fid, name, kind, prio in pending:
        print(f"{fid}\t{kind}\t{prio}\t{name}")
    return 10


if __name__ == "__main__":
    sys.exit(main())
