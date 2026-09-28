"""report_bundle 로드·검증 (v3.5.0, docs/handoff/12 §7 `bundle/load.py`, back_and_forth D-0063 §0).

agents_reviewer 가 emit 한 report_bundle.json 을 `ReportBundle` 로 검증 로드한다.
v3.5.0 에서 `orchestrator/bundle_io.py` 를 이리로 옮겼다(경로 하나, 15 P2 — 오케스트레이터는 얇은 호출만).

- `load_report_bundle(path)`: 로드 + 검증. 선언 필드의 타입·enum·필수·참조 해석 위반은 오류로 전파한다.
- `unknown_fields(raw)`: 모델이 선언하지 않은 필드를 **모든 깊이**에서 경로로 나열한다(`$.map.markers[].kind` 형식).
  로더는 이 목록을 로그로 알린다 — 조용히 버리지 않는다(15 P6).
- CLI: `python -m bundle.load json samples --out docs/handoff/reports/phase9/corpus_load.json`
  → 건별 pass/fail·오류·미지 필드 표(D-0063 §0).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import typing
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel

from schemas.models import ReportBundle

logger = logging.getLogger(__name__)


def _submodel(ann: Any) -> Optional[type[BaseModel]]:
    """필드 주석에서 BaseModel 하위 타입 하나를 찾는다(Optional[X]·list[X] 포함). 없으면 None."""
    if typing.get_origin(ann) is None:
        return ann if isinstance(ann, type) and issubclass(ann, BaseModel) else None
    for a in typing.get_args(ann):
        m = _submodel(a)
        if m is not None:
            return m
    return None


def _walk(model: type[BaseModel], data: Any, path: str, out: Counter) -> None:
    if isinstance(data, list):
        for d in data:
            _walk(model, d, path + "[]", out)
        return
    if not isinstance(data, dict):
        return
    for k, v in data.items():
        f = model.model_fields.get(k)
        if f is None:
            out[f"{path}.{k}"] += 1
            continue
        sub = _submodel(f.annotation)
        if sub is not None:
            _walk(sub, v, f"{path}.{k}", out)


def unknown_fields(raw: object) -> dict[str, int]:
    """모델 미선언 필드 경로 → 등장 횟수. 경로의 `[]` 는 목록 원소."""
    out: Counter = Counter()
    _walk(ReportBundle, raw, "$", out)
    return dict(sorted(out.items()))


def load_report_bundle(path: Path) -> ReportBundle:
    """report_bundle.json 을 로드 → `ReportBundle`.

    raise: FileNotFoundError(파일 없음) / json.JSONDecodeError / pydantic.ValidationError(=ValueError) — 건너뛰지 않고 전파.
    """
    if not path.exists():
        raise FileNotFoundError(f"report_bundle 파일이 없습니다: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    unk = unknown_fields(raw)
    if unk:
        logger.warning("report_bundle 모델 미선언 필드(%s): %s — 영상에 쓰려면 schemas/models.py 번들 모델에 선언하라",
                       path.name, sorted(unk))
    return ReportBundle.model_validate(raw)


def corpus_files(roots: list[Path]) -> list[Path]:
    """코퍼스 파일 목록 — 폴더면 하위 `*.bundle.json` 전부(정렬), 파일이면 그대로."""
    out: list[Path] = []
    for r in roots:
        out += sorted(r.rglob("*.bundle.json")) if r.is_dir() else [r]
    return out


def corpus_report(roots: list[Path]) -> dict[str, Any]:
    """코퍼스 전부 로드 → 건별 pass/fail·오류·미지 필드와 합계(D-0063 §0)."""
    rows: list[dict[str, Any]] = []
    agg: Counter = Counter()
    for p in corpus_files(roots):
        row: dict[str, Any] = {"file": p.as_posix()}
        raw: object = None
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            unk = unknown_fields(raw)
            b = ReportBundle.model_validate(raw)
            row |= {"ok": True, "producer": f"{b.producer.system} {b.producer.version}", "sections": len(b.sections),
                    "charts": len(b.charts), "markers": len(b.map.markers) if b.map else 0,
                    "arcs": len(b.map.arcs) if b.map else 0, "claims": len(b.claims),
                    "contradictions": len(b.contradictions), "sources": len(b.sources), "images": len(b.images)}
        except (json.JSONDecodeError, ValueError) as e:
            unk = unknown_fields(raw)
            row |= {"ok": False, "error": str(e)[:500]}
        row["unknown_fields"] = unk
        agg.update({k: 1 for k in unk})   # 필드가 나온 번들 수
        rows.append(row)
    return {"schema_version": 1, "files": len(rows), "passed": sum(r["ok"] for r in rows),
            "failed": sum(not r["ok"] for r in rows),
            "unknown_fields_by_bundles": dict(sorted(agg.items())), "rows": rows}


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m bundle.load", description="번들 코퍼스 로드 표(D-0063 §0)")
    ap.add_argument("roots", nargs="+", type=Path, help="번들 파일 또는 폴더(하위 *.bundle.json)")
    ap.add_argument("--out", type=Path, help="JSON 표 저장 경로")
    a = ap.parse_args(argv)
    rep = corpus_report(a.roots)
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("files", "passed", "failed", "unknown_fields_by_bundles")}, ensure_ascii=False))
    return 0 if rep["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["corpus_files", "corpus_report", "load_report_bundle", "unknown_fields"]
