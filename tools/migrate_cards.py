"""오른쪽 위 구석 카드(card 이벤트) 이식 도구 (v7.4.0 back_and_forth D-0306, 사용자 의견 UF-148).

UF-148 원문: "이 오른쪽 상단에 뜨는 아일랜드 없애도 될거 같아. 어짜피 자막으로도, 음성으로도 그 이야기를 하는데 … 오른쪽 상단의 카드 자체의
규약을 없애라는 뜻이야."

    python tools/migrate_cards.py projects/*/direction.yaml --report back_and_forth/<표>.md      # 바꾸고 변환 표를 쓴다
    python tools/migrate_cards.py projects/x/direction.yaml --check                               # card 가 남았으면 종료 코드 1

card 이벤트 블록(목록 항목 `- type: card` 부터 다음 같은 깊이 항목 전까지)을 텍스트로 지운다 — 주석·순서·다른 이벤트는 그대로.
카드의 큰 수치(bigs)는 원고가 말하므로 버리고(D-0306 §1.3 ③) 변환 표에 남긴다. 옛 판(direction.vN.yaml)은 이력이라 대상이 아니다.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ITEM_RE = re.compile(r"^(?P<ind>\s*)- type: card\s*$")


def card_blocks(lines: list[str]) -> list[tuple[int, int]]:
    """[시작 줄, 끝 줄) — `- type: card` 항목과 그 아래 더 깊은 줄(같은 깊이 다음 항목·키, 더 얕은 줄 직전까지)."""
    out = []
    i = 0
    while i < len(lines):
        m = ITEM_RE.match(lines[i])
        if not m:
            i += 1
            continue
        ind = len(m.group("ind"))
        j = i + 1
        while j < len(lines):
            s = lines[j]
            if s.strip() and (len(s) - len(s.lstrip(" "))) <= ind and not s.lstrip().startswith("#"):
                break
            if s.strip() and (len(s) - len(s.lstrip(" "))) <= ind and s.lstrip().startswith("#"):   # 같은 깊이 주석 = 다음 항목 머리
                break
            j += 1
        out.append((i, j))
        i = j
    return out


def migrate_text(text: str) -> tuple[str, list[dict]]:
    """(새 텍스트, 지운 카드 목록 — tag·lines·bigs·start)."""
    lines = text.splitlines(keepends=True)
    removed: list[dict] = []
    for a, b in reversed(card_blocks(lines)):
        block = "".join(lines[a:b])
        ind = len(lines[a]) - len(lines[a].lstrip(" "))
        try:
            ev = (yaml.safe_load("\n".join(ln[ind:] if len(ln) > ind else ln.strip() for ln in block.splitlines())) or [{}])[0]
        except yaml.YAMLError:
            ev = {"tag": "?"}
        removed.append({"tag": ev.get("tag"), "lines": ev.get("lines") or [], "bigs": ev.get("bigs") or [], "start": ev.get("start")})
        del lines[a:b]
    return "".join(lines), list(reversed(removed))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="card 이벤트 이식(D-0306)")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--report", type=Path, help="변환 표(markdown) 경로")
    ap.add_argument("--check", action="store_true", help="바꾸지 않고 card 가 남았는지만")
    args = ap.parse_args(argv)
    rows, left = [], 0
    for f in args.files:
        text = f.read_text(encoding="utf-8")
        new, removed = migrate_text(text)
        if args.check:
            left += len(removed)
            continue
        if removed:
            f.write_text(new, encoding="utf-8")
            doc = yaml.safe_load(new)
            evs = doc.get("events") if isinstance(doc, dict) else doc
            assert not any(isinstance(e, dict) and e.get("type") == "card" for e in evs or []), f
        for r in removed:
            rows.append(f"| {f} | {r['tag']} | {' / '.join(map(str, r['lines']))} | {' / '.join(' '.join(map(str, b)) for b in r['bigs'])} | 삭제 |")
        print(f"{f}: card {len(removed)} 삭제", flush=True)
    if args.check:
        print(f"card 남음 {left}")
        return 1 if left else 0
    if args.report:
        args.report.write_text("| 연출 | 태그 | 줄 | 큰 수치(bigs) | 처리 |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
