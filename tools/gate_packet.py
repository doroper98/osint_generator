"""gate packet 만들기(v7.4.0 back_and_forth D-0355, UF-267).

    python tools/gate_packet.py projects/{pid} [--by SESSION] [--only script|preview]

사용자 게이트 승인은 감독 세션이 `orchestrator.main approve` 로 기록한다. 감독 작업 트리에는 out/(콘티 판 기록)·미추적 자산이 없으므로,
구현 세션이 게이트 자료를 올릴 때 이 도구로 승인 판정 입력을 `projects/{pid}/gate_packet.json`(git 추적)에 묶어 push 한다.
판정은 approve 와 같은 함수(require_media_plan·콘티 판 기록·공용 자산 승격)로 한다 — 통과하지 못하면 packet 을 만들지 않는다.
원고·연출·plan 을 고치면 packet 지문이 어긋나 승인이 거부된다 → 다시 만든다.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.project_manager import build_gate_packet  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("proj", type=Path)
    ap.add_argument("--by", default=os.environ.get("CLAUDE_SESSION_ID", "") or "구현 세션")
    ap.add_argument("--only", choices=["script", "preview"])
    a = ap.parse_args(argv)
    pkt = build_gate_packet(a.proj.resolve(), a.by, script=a.only in (None, "script"), preview=a.only in (None, "preview"))
    print(f"gate packet {a.proj}/gate_packet.json · digest {pkt.digest[:10]} · sources {sorted(pkt.sources)} · "
          f"script {'있음' if pkt.script else '없음'} · preview {'있음' if pkt.preview else '없음'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
