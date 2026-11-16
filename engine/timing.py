"""단계별 시간 기록(v7.4.0 back_and_forth D-1000 S0 — 사용자 UF-300 "영상 제작에 소요되는 시간이 너무 길어").

    with stage_timer(proj, "render.animatic.frames", jobs=4):
        ...

`projects/{pid}/out/timings.jsonl` 에 한 줄 1이벤트로 붙인다:
    {"schema_version": 1, "stage": …, "start_utc": …, "end_utc": …, "sec": …, "ok": true, "args": {…}}
예외로 끝난 단계도 `ok: false` 로 남기고 예외는 그대로 올린다(조용히 삼키지 않는다, 15 P6).
돌지 않은 단계는 기록하지 않는다(P5) — 이 컨텍스트 관리자 안에 들어온 단계만 남는다.
`summarize()` 는 provenance `timings`(단계별 합계·횟수)를 만든다.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict

TIMINGS_NAME = "timings.jsonl"


class StageTiming(BaseModel):
    """timings.jsonl 한 줄(C3 schema_version)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    stage: str
    start_utc: str
    end_utc: str
    sec: float
    ok: bool = True
    args: dict[str, object] = {}


def timings_path(proj: Path) -> Path:
    return Path(proj) / "out" / TIMINGS_NAME


def _utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@contextmanager
def stage_timer(proj: Path | None, stage: str, **args: object) -> Iterator[dict[str, object]]:
    """단계 하나를 잰다. proj 가 None 이면(프로젝트 밖 호출 — 시험·도구) 기록하지 않는다.
    yield 하는 dict 에 값을 넣으면 args 에 더해진다(예: 재사용 조각 수)."""
    extra: dict[str, object] = {}
    t0 = time.time()
    p0 = time.perf_counter()
    ok = True
    try:
        yield extra
    except BaseException:
        ok = False
        raise
    finally:
        if proj is not None:
            rec = StageTiming(stage=stage, start_utc=_utc(t0), end_utc=_utc(time.time()),
                              sec=round(time.perf_counter() - p0, 3), ok=ok, args={**args, **extra})
            path = timings_path(proj)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:   # 한 줄 쓰기 — 조각 프로세스가 동시에 붙여도 줄이 섞이지 않는 크기
                f.write(json.dumps(rec.model_dump(), ensure_ascii=False) + "\n")


def read_timings(proj: Path) -> list[StageTiming]:
    path = timings_path(proj)
    if not path.exists():
        return []
    return [StageTiming.model_validate_json(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def summarize(proj: Path, since_utc: str | None = None) -> dict[str, dict[str, float]] | None:
    """provenance `timings` — 단계별 {sec 합계, n 횟수}. since_utc 이후 시작한 기록만(이번 실행). 기록이 없으면 None(P5)."""
    rows = [r for r in read_timings(proj) if since_utc is None or r.start_utc >= since_utc]
    if not rows:
        return None
    out: dict[str, dict[str, float]] = {}
    for r in rows:
        s = out.setdefault(r.stage, {"sec": 0.0, "n": 0})
        s["sec"] = round(s["sec"] + r.sec, 3)
        s["n"] += 1
    return dict(sorted(out.items()))


def now_utc() -> str:
    return _utc(time.time())


def last_run_start(proj: Path, stage: str) -> str | None:
    """그 단계의 마지막 기록 시작 시각 — summarize(since) 의 기준(없으면 None = 전체)."""
    rows = [r for r in read_timings(proj) if r.stage == stage]
    return rows[-1].start_utc if rows else None
