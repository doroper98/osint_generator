"""AI 연출 실증 실행기 (v3.1.0, back_and_forth D-0047 작업 10 — hormuz_ai 보고서용).

    python tools/ai_direction_run.py projects/hormuz_ai [--preview golden] [--backend claude]

파이프라인 advance 와 **같은 함수**(orchestrator.ai_direction.run_worker·qa_loop, engine_service.run_stage)를 쓴다.
다른 점은 두 가지뿐: 매니페스트 상태 전이를 하지 않고, 단계 결과를 `prev/ai_run.jsonl` 한 줄씩 남긴다(보고서 재료).
direction.yaml 이 없을 때만 연출가를 부른다(사람 연출은 건드리지 않는다).
v5.2.0(back_and_forth D-0132 §3): `--rounds N` — 이번 실행의 수정 회차 수(기본 = 규칙 상한). 상한 밖 추가 회차는 감독 결정이 있을 때만.
v5.2.0(back_and_forth D-0131): `--redirect` — 기존 direction.yaml 을 prev/direction_{yymmdd_hhmmss}.yaml 로 **이동**(삭제 아님)한 뒤
연출가를 부른다(무대 구성이 바뀌는 재연출. 옛 연출은 연출가 입력에 넣지 않는다 — P9).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from orchestrator import ai_direction, engine_service  # noqa: E402
from schemas.engine_models import StageResult  # noqa: E402


def redirect(pdir: Path, now: datetime | None = None) -> Path | None:
    """기존 direction.yaml 을 prev/direction_{yymmdd_hhmmss}.yaml 로 옮긴다(없으면 None). 이력 보존 — 삭제하지 않는다."""
    src = pdir / "direction.yaml"
    if not src.exists():
        return None
    dst = pdir / "prev" / f"direction_{(now or datetime.now()).strftime('%y%m%d_%H%M%S')}.yaml"
    dst.parent.mkdir(exist_ok=True)
    if dst.exists():
        raise SystemExit(f"{dst} 가 이미 있다 — 덮어쓰지 않는다")
    src.rename(dst)
    return dst


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AI 연출 → 검사 → 시각 검수 루프 1회 실행")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--preview", default="auto", help="auto · golden · 쉼표 초")
    ap.add_argument("--backend", default="claude")
    ap.add_argument("--redirect", action="store_true", help="기존 direction.yaml 을 prev/ 로 옮기고 연출가부터(D-0131)")
    ap.add_argument("--rounds", type=int, default=None,
                    help="이번 실행의 수정 회차 수(기본 rules qa_checks.visual_qa_loop_max). 상한 밖 추가 회차는 감독 결정(D) 이 있을 때만(D-0132 §3)")
    args = ap.parse_args(argv)
    pdir = args.proj.resolve()
    (pdir / "prev").mkdir(exist_ok=True)
    if args.redirect:
        moved = redirect(pdir)
        print(json.dumps({"redirect": str(moved) if moved else None}, ensure_ascii=False), flush=True)
    log = pdir / "prev" / "ai_run.jsonl"
    t_start = time.time()

    def record(res: StageResult) -> None:
        row = {"t": round(time.time() - t_start, 1), **res.model_dump(include={"stage", "ok", "errors", "warnings"})}
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(json.dumps({k: row[k] for k in ("t", "stage", "ok")} | {"errors": row["errors"][:3]}, ensure_ascii=False), flush=True)

    def run_engine(stage: str) -> StageResult:
        res = engine_service.run_stage(pdir, stage, preview=args.preview)  # type: ignore[arg-type]
        return res.model_copy(update={"stage": stage})

    if not (pdir / "direction.yaml").exists():
        res = ai_direction.run_worker("director", pdir, args.backend)
        record(res)
        if not res.ok:
            return 1
    val = run_engine("validate")
    record(val)
    if not val.ok:
        return 1
    ok, summary = ai_direction.qa_loop(pdir, run_engine, record, args.backend, loop_max=args.rounds)
    print(json.dumps({"ok": ok, **summary}, ensure_ascii=False))
    (pdir / "prev" / "ai_run_summary.json").write_text(json.dumps({"ok": ok, **summary}, ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
