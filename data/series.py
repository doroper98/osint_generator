"""시리즈 레코드 로더 (v4.3.0, docs/handoff/20 §5.1, back_and_forth D-0084 작업 1).

`data/series/<series_id>.yaml`(레코드) + `<series_id>.csv`(값, 헤더 `date,value`) → `schemas.data_models.SeriesRecord`.
`raw/<series_id>.csv`(출처에서 받은 그대로)가 있으면 레코드의 transform 을 다시 적용해 값과 **정확히** 같은지 본다
— 다르면 오류(값을 손으로 고치지 않았음을 증명, 15 P6). 폴더는 `rules data.series_dir`.
"""

from __future__ import annotations

import csv
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import ValidationError

from rules import load_rules
from schemas.data_models import SeriesRecord

REPO = Path(__file__).resolve().parent.parent


class SeriesError(ValueError):
    """레코드 없음·형식 오류·원자료 불일치(15 P6)."""


def series_dir() -> Path:
    return REPO / load_rules().data.series_dir


def read_csv(path: Path) -> list[tuple[date, float]]:
    """`date,value` 또는 FRED fredgraph(`observation_date,<ID>`) CSV → [(날짜, 값)]. 빈 값('.' 등) = 오류."""
    out: list[tuple[date, float]] = []
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows or len(rows[0]) != 2:
        raise SeriesError(f"{path}: 두 열 CSV 가 아니다")
    for i, r in enumerate(rows[1:], 2):
        try:
            out.append((date.fromisoformat(r[0]), float(r[1])))
        except (ValueError, IndexError) as ex:
            raise SeriesError(f"{path}:{i}: 값 읽기 실패 {r!r} — {ex}") from ex
    return out


def write_csv(path: Path, values: list[tuple[date, float]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "value"])
        for d, v in values:
            w.writerow([d.isoformat(), repr(float(v))])


def apply_transform(op: str, raw: list[tuple[date, float]], start: date) -> list[tuple[date, float]]:
    """`rules data.transforms` 의 연산(명시된 것만). raw = 원자료(월별 연속), start 이상만 돌려준다."""
    if op == "raw":
        return [(d, v) for d, v in raw if d >= start]
    if op == "yoy_pct":
        by = dict(raw)
        out = []
        for d, v in raw:
            prev = date(d.year - 1, d.month, d.day)
            if d >= start:
                if prev not in by:
                    raise SeriesError(f"yoy_pct: {d} 의 12개월 전 값({prev})이 원자료에 없다")
                out.append((d, round((v / by[prev] - 1) * 100, 2)))
        return out
    raise SeriesError(f"구현 없는 transform {op!r} — rules data.transforms 와 이 함수가 같아야 한다(P10)")


def load_series_file(yaml_path: Path) -> SeriesRecord:
    csv_path = yaml_path.with_suffix(".csv")
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as ex:
        raise SeriesError(f"{yaml_path}: {ex}") from ex
    if not isinstance(raw, dict) or "values" in raw:
        raise SeriesError(f"{yaml_path}: 레코드는 dict 이고 값(values)은 {csv_path.name} 에만 둔다")
    if not csv_path.exists():
        raise SeriesError(f"값 파일 없음: {csv_path}")
    try:
        rec = SeriesRecord.model_validate({**raw, "values": read_csv(csv_path)})
    except ValidationError as ex:
        raise SeriesError(f"{yaml_path}: {ex}") from ex
    if rec.series_id != yaml_path.stem:
        raise SeriesError(f"{yaml_path}: series_id {rec.series_id!r} ≠ 파일 이름 {yaml_path.stem!r}")
    rp = yaml_path.parent / "raw" / csv_path.name
    if rp.exists():
        again = apply_transform(rec.transform.op, read_csv(rp), rec.start)
        if again != rec.values:
            diff = next(((a, b) for a, b in zip(again, rec.values) if a != b), (len(again), len(rec.values)))
            raise SeriesError(f"{csv_path}: raw/ 에 transform {rec.transform.op} 을 다시 적용한 값과 다르다 — 첫 차이 {diff}")
    return rec


@lru_cache(maxsize=None)
def load_series(series_id: str) -> SeriesRecord:
    """series_id → 레코드(data/series/<id>.yaml). 없으면 SeriesError."""
    p = series_dir() / f"{series_id}.yaml"
    if not p.exists():
        have = sorted(x.stem for x in series_dir().glob("*.yaml"))
        raise SeriesError(f"시리즈 레코드 없음 {series_id!r} — {series_dir().relative_to(REPO)}: {have}")
    return load_series_file(p)


__all__ = ["SeriesError", "apply_transform", "load_series", "load_series_file", "read_csv", "series_dir", "write_csv"]
