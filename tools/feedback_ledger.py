"""사용자 의견 원장 표 생성 (v5.22.0, back_and_forth D-0200).

정본 `rules/user_feedback.yaml` → `docs/handoff/USER_FEEDBACK_LEDGER.md` 의 표(`<!-- UF-TABLE:BEGIN -->` ~ `END`).
값을 두 곳에서 손으로 관리하지 않는다 — 테스트(tests/anti_inertia/test_user_feedback_guards.py)가 생성 결과와 문서를 대조한다.

    python tools/feedback_ledger.py            # 다르면 종료 코드 1(차이 요약)
    python tools/feedback_ledger.py --write    # 문서 표를 다시 쓴다
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from rules import load_user_feedback  # noqa: E402
from schemas.feedback_models import FeedbackLedger  # noqa: E402

DOC = REPO / "docs" / "handoff" / "USER_FEEDBACK_LEDGER.md"
BEGIN, END = "<!-- UF-TABLE:BEGIN -->", "<!-- UF-TABLE:END -->"
STATUS = {"guarded": "보호", "open": "**미보호**"}


def _cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def render_table(led: FeedbackLedger) -> str:
    rows = ["| 번호 | 날짜 | 영상·시점 | 사용자 원문 | 분류 | 재발 방지 장치 | 결정 | 상태 |", "|---|---|---|---|---|---|---|---|"]
    for e in led.entries:
        quote = f'"{e.quote}"' if e.quote_kind == "verbatim" else f"(요지) {e.quote}"
        guards = "<br>".join(f"{g.kind}: `{g.ref}`" for g in e.guards) or "—"
        status = STATUS[e.status] + (f" · {e.recurs_of} 재발" if e.recurs_of else "")
        rows.append("| " + " | ".join(_cell(x) for x in (e.id, e.date, f"{e.project} · {e.at}", quote, e.category, guards, e.decision, status)) + " |")
    return "\n".join(rows)


def render_doc(text: str, led: FeedbackLedger) -> str:
    if BEGIN not in text or END not in text:
        raise SystemExit(f"{DOC} 에 표 표식({BEGIN} … {END})이 없다")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{BEGIN}\n{render_table(led)}\n{END}{tail}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    led = load_user_feedback()
    cur = DOC.read_text(encoding="utf-8")
    new = render_doc(cur, led)
    if a.write:
        DOC.write_text(new, encoding="utf-8")
        print(f"{DOC.relative_to(REPO)} — {len(led.entries)}개(미보호 {len(led.open_entries())})")
        return 0
    if new != cur:
        print("원장 문서 표가 rules/user_feedback.yaml 과 다르다 — python tools/feedback_ledger.py --write")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
