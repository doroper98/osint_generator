"""AI 연출 실증 실행기 (v3.1.0, back_and_forth D-0047 작업 10 — hormuz_ai 보고서용).

    python tools/ai_direction_run.py projects/hormuz_ai [--preview golden] [--backend claude]

파이프라인 advance 와 **같은 함수**(orchestrator.ai_direction.run_worker·qa_loop, engine_service.run_stage)를 쓴다.
다른 점은 두 가지뿐: 매니페스트 상태 전이를 하지 않고, 단계 결과를 `prev/ai_run.jsonl` 한 줄씩 남긴다(보고서 재료).
direction.yaml 이 없을 때만 연출가를 부른다(사람 연출은 건드리지 않는다).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from orchestrator import ai_direction, engine_service  # noqa: E402
from schemas.engine_models import StageResult  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AI 연출 → 검사 → 시각 검수 루프 1회 실행")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--preview", default="auto", help="auto · golden · 쉼표 초")
    ap.add_argument("--backend", default="claude")
    args = ap.parse_args(argv)
    pdir = args.proj.resolve()
    (pdir / "prev").mkdir(exist_ok=True)
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
    ok, summary = ai_direction.qa_loop(pdir, run_engine, record, args.backend)
    print(json.dumps({"ok": ok, **summary}, ensure_ascii=False))
    (pdir / "prev" / "ai_run_summary.json").write_text(json.dumps({"ok": ok, **summary}, ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
