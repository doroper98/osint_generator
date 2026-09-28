"""소스 인테이크 e2e 드라이버 (v3.2.0, back_and_forth D-0051 작업 13).

X 캡처 3 + 기사 2(tests/fixtures/e2e_intake — 전부 가상, x.com 접근 없음)로
CREATED → INTAKE → SOURCE_VERIFY → RESEARCH → SCRIPT_DRAFT → (출처 검사) SCRIPT_APPROVAL 까지 진행한다.
LLM 단계(계획·캡처 판독·검증·리서치·원고)는 실제 `claude -p` 를 부른다. 소스 확인 하나는 Command Center 를
textual pilot 으로 헤드리스 조작해 'c' 키로 한다(사람과 같은 경로), 나머지는 CLI confirm-source.

    python tools/e2e_source_intake.py <project_id> --out docs/handoff/reports/phase6_95/e2e

stdout = 한 줄 1이벤트. `<out>/run_log.jsonl` = 단계별 {t, step, ok, rc, detail}.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.config import load_config, project_dir  # noqa: E402
from orchestrator.main import main as cli  # noqa: E402
from orchestrator.project_manager import load_manifest  # noqa: E402

FIX = REPO / "tests" / "fixtures" / "e2e_intake"
KST = timezone(timedelta(hours=9))
USER = "e2e 사용자(Opus 대행 — 픽스처 캡처와 대조)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project_id")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--resume-from", choices=["build-research"], default=None,
                    help="앞 단계가 끝난 프로젝트에서 이어서(예: LLM 사용량 한도 429 뒤). 로그는 이어 쓴다")
    args = ap.parse_args(argv)
    pid = args.project_id
    args.out.mkdir(parents=True, exist_ok=True)
    log = (args.out / "run_log.jsonl").open("a" if args.resume_from else "w", encoding="utf-8")
    t0 = time.time()

    def step(name: str, argv_: list[str], expect: int = 0) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli(argv_)
        out = buf.getvalue()
        row = {"t": round(time.time() - t0, 1), "at": datetime.now(KST).strftime("%H:%M:%S"), "step": name,
               "ok": rc == expect, "rc": rc, "state": load_manifest(pid).current_state, "detail": out.strip()[-600:]}
        log.write(json.dumps(row, ensure_ascii=False) + "\n")
        log.flush()
        print(json.dumps({k: row[k] for k in ("t", "step", "ok", "rc", "state")}, ensure_ascii=False), flush=True)
        if rc != expect:
            raise SystemExit(f"단계 실패: {name} rc={rc}\n{out[-2000:]}")
        return out

    if args.resume_from:
        log.write(json.dumps({"t": 0, "step": f"resume-from {args.resume_from}", "ok": True,
                              "state": load_manifest(pid).current_state}, ensure_ascii=False) + "\n")
        return _tail(step, pid, log, t0)
    step("new-project", ["new-project", pid, "--title", "가온항 호위 출항(가상 e2e)", "--category", "geopolitics",
                         "--topic-summary", "가상 시나리오 — 가온항 화물선 호위 출항과 노라의 영해 주장(e2e 픽스처, 실존 아님)",
                         "--duration-min", "3"])
    step("plan-intake", ["plan-intake", pid])
    ids = {}
    for key, img, note in (("cap1", "cap1_port.png", "항만청을 자처하는 계정 — 목록 미등재"),
                           ("cap2", "cap2_watcher.png", "관찰 계정의 단독 주장"),
                           ("cap3", "cap3_resident.png", "주민 목격담(개인 계정)")):
        out = step(f"add-source x-capture {key}", ["add-source", pid, "--kind", "x-capture", "--image", str(FIX / img), "--note", note])
        ids[key] = json.loads(out.strip().splitlines()[-1])["id"]
    for key, f, pub, head, lang in (("art1", "art1_gaon_ilbo.txt", "가온일보", "가온항서 화물선 2척 호위 출항", "ko"),
                                    ("art2", "art2_test_maritime_wire.txt", "Test Maritime Wire", "Cargo ships leave Gaon under escort", "en")):
        out = step(f"add-source article {key}", ["add-source", pid, "--kind", "article", "--publisher", pub, "--headline", head,
                                                   "--pub-date", "2026-09-24", "--text-file", str(FIX / f), "--lang", lang,
                                                   "--note", "가상 매체(e2e 픽스처)"])
        ids[key] = json.loads(out.strip().splitlines()[-1])["id"]
    step("list-sources(확인 전)", ["list-sources", pid])
    step("submit-intake(미확인 → 거부)", ["submit-intake", pid], expect=2)
    # Command Center 헤드리스 — 'c' 키로 기사 1건 확인(사람과 같은 경로)
    asyncio.run(_cc_confirm(pid, ids["art1"]))
    log.write(json.dumps({"t": round(time.time() - t0, 1), "step": f"command-center c {ids['art1']}", "ok": True,
                          "state": load_manifest(pid).current_state}, ensure_ascii=False) + "\n")
    step(f"confirm-source {ids['cap1']}", ["confirm-source", pid, "--id", ids["cap1"], "--by", USER])
    step(f"confirm-source {ids['cap2']}", ["confirm-source", pid, "--id", ids["cap2"], "--by", USER])
    step(f"confirm-source {ids['cap3']} private", ["confirm-source", pid, "--id", ids["cap3"], "--by", USER, "--account-class", "private"])
    step(f"confirm-source {ids['art2']}", ["confirm-source", pid, "--id", ids["art2"], "--by", USER])
    step("submit-intake", ["submit-intake", pid])
    step("verify-sources", ["verify-sources", pid])
    return _tail(step, pid, log, t0)


def _tail(step, pid: str, log, t0: float) -> int:  # noqa: ANN001
    step("build-research", ["build-research", pid])
    step("build-script", ["build-script", pid])
    step("lint-script", ["lint-script", pid])
    step("transition script_approval(출처 검사)", ["transition", pid, "--to", "script_approval", "--reason", "e2e 원고 확정"])
    step("gate-view", ["gate-view", "--project", pid])
    log.close()
    print(f"완료 — {round(time.time() - t0)}초, 상태 {load_manifest(pid).current_state}")
    return 0


async def _cc_confirm(pid: str, sid: str) -> None:
    from orchestrator.tui_app import CommandCenterApp  # noqa: PLC0415

    app = CommandCenterApp(project_id=pid, project_dir=project_dir(pid), cfg=load_config(), current_state="intake")
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()
        for ch in sid:
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
    print(json.dumps({"step": f"command-center c {sid}", "ok": True}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    sys.exit(main())
