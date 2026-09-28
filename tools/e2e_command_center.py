"""Command Center e2e 드라이버 (v3.0.0, back_and_forth D-0040 작업 10 · D-0042).

Command Center(TUI)를 textual pilot 으로 **헤드리스로 조작**해 한 프로젝트를 CREATED → DONE 까지 진행한다.
사람이 누르는 키와 같은 경로다: `g`(엔진 단계 advance) · `a`(게이트 승인) · `x` + 입력(게이트 반려).
LLM·사람 단계(CREATED~SCRIPT_DRAFT)는 이 프로젝트에 해당 없음(v3 수동 원고·연출) → CLI `transition` 으로 기록만.

    python tools/e2e_command_center.py <project_id> [--reject-demo] [--timeout-sec 5400]

stdout: TUI 오케스트레이터 로그 한 줄 1이벤트(C4.5) + 단계별 StageResult 요약 + 게이트 화면 텍스트.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.config import load_config, project_dir  # noqa: E402
from orchestrator.gate_view import gate_view  # noqa: E402
from orchestrator.main import main as cli  # noqa: E402
from orchestrator.project_manager import load_manifest  # noqa: E402
from orchestrator.tui_app import CommandCenterApp  # noqa: E402

PRE_GATE = ["intake", "source_verify", "research", "script_draft", "script_approval"]
LLM_NOTE = "v3 수동 원고·연출 사용 — LLM 단계(intake·source·research·script) 해당 없음(e2e, D-0040 작업 10)"


def say(line: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {line}", flush=True)


class LoggedApp(CommandCenterApp):
    """오케스트레이터 로그 패널에 쓰는 줄을 stdout 에도 낸다(e2e 기록)."""

    def _orch_emit(self, kind: str, line: str) -> None:  # noqa: D401
        say(f"[tui:{kind}] {line}")
        super()._orch_emit(kind, line)


def state(pid: str) -> str:
    return str(load_manifest(pid).current_state)


async def wait_state(app: LoggedApp, pilot, pid: str, before: str, timeout: float) -> str:  # noqa: ANN001
    t0 = time.time()
    while time.time() - t0 < timeout:
        await pilot.pause(2.0)
        now = state(pid)
        if now != before:
            return now
        if not app._busy and time.time() - t0 > 3:   # advance 끝났는데 상태가 그대로 = 실패(머묾)
            return now
    raise TimeoutError(f"{before} 에서 {timeout}s 안에 진행 없음")


async def drive(pid: str, reject_demo: bool, timeout: float) -> int:
    cfg = load_config()
    pdir = project_dir(pid, cfg)
    app = LoggedApp(project_id=pid, project_dir=pdir, cfg=cfg, current_state=state(pid))
    rejected: set[str] = set()
    async with app.run_test(size=(200, 60)) as pilot:
        await pilot.pause(1.0)
        while True:
            st = state(pid)
            app.current_state = st
            if st == "done":
                say("e2e: done")
                return 0
            if st in ("script_approval", "preview_approval"):
                text, _ = gate_view(pdir, st)
                say(f"=== 게이트 화면 {st} ===")
                print(text, flush=True)
                say("=== 끝 ===")
                if reject_demo and st not in rejected:
                    rejected.add(st)
                    to = "script_draft" if st == "script_approval" else "direction"
                    await pilot.press("x")                       # 반려 입력줄 열기
                    await pilot.pause(0.5)
                    assert app.reject_input is not None
                    app.reject_input.value = f"{to} e2e 반려 시연 — {st} 에서 {to} 로 되돌림"   # 사람이 타이핑하는 자리
                    await pilot.press("enter")
                    await pilot.pause(1.0)
                    say(f"reject: {st} → {state(pid)}")
                    if state(pid) == "script_draft":   # 원고 단계는 사람 수정 후 다시 게이트로(여기선 수정 없음)
                        cli(["transition", pid, "--to", "script_approval", "--reason", "반려 사유 확인 — 원고 유지(e2e)"])
                    continue
                await pilot.press("a")
                await pilot.pause(1.0)
                say(f"approve: {st} → {state(pid)}")
                continue
            before = st
            await pilot.press("g")
            now = await wait_state(app, pilot, pid, before, timeout)
            say(f"advance: {before} → {now}")
            if now == before:
                say("e2e: 단계 실패 — 상태에 머묾(15 P6). 중단")
                return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project_id")
    ap.add_argument("--reject-demo", action="store_true")
    ap.add_argument("--timeout-sec", type=float, default=5400.0)
    args = ap.parse_args(argv)
    pid = args.project_id
    try:
        load_manifest(pid)
    except FileNotFoundError:
        say(f"new-project {pid}")
        rc = cli(["new-project", pid, "--title", "호르무즈와 한국", "--category", "geopolitics"])
        if rc != 0:
            return rc
    for s in PRE_GATE:
        if state(pid) in ("created", *PRE_GATE[:PRE_GATE.index(s)]):
            cli(["transition", pid, "--to", s, "--reason", LLM_NOTE])
    return asyncio.run(drive(pid, args.reject_demo, args.timeout_sec))


if __name__ == "__main__":
    raise SystemExit(main())
