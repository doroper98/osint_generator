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
from typing import Optional

import yaml
from pydantic import ValidationError

from rules import load_rules
from schemas.data_models import SeriesRecord

REPO = Path(__file__).resolve().parent.parent


class SeriesError(ValueError):
    """레코드 없음·형식 오류·원자료 불일치(15 P6)."""


def series_dir() -> Path:
    return REPO / load_rules().data.series_dir


def read_csv(path: Path, allow_empty: bool = False) -> list[tuple[date, Optional[float]]]:
    """`date,value` 또는 FRED fredgraph(`observation_date,<ID>`) CSV → [(날짜, 값)]. 빈 값은 allow_empty 일 때만 None
    (원자료 — 레코드 missing 과 대조한다, D-0086), 아니면 오류."""
    out: list[tuple[date, Optional[float]]] = []
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows or len(rows[0]) != 2:
        raise SeriesError(f"{path}: 두 열 CSV 가 아니다")
    for i, r in enumerate(rows[1:], 2):
        try:
            if allow_empty and len(r) == 2 and r[1].strip() in ("", "."):
                out.append((date.fromisoformat(r[0]), None))
                continue
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


def apply_transform(op: str, raw: list[tuple[date, Optional[float]]], start: date) -> tuple[list[tuple[date, float]], list[date]]:
    """`rules data.transforms` 의 연산(명시된 것만). raw = 원자료(월별, 빈 값 None), start 이상만 → (값, 빈 날짜).
    빈 값은 채우지 않는다(D-0086). yoy_pct 는 t 또는 t−12 가 빈 값이면 t 도 빈 날짜."""
    if op == "raw":
        return [(d, v) for d, v in raw if d >= start and v is not None], [d for d, v in raw if d >= start and v is None]
    if op == "yoy_pct":
        by = dict(raw)
        out: list[tuple[date, float]] = []
        miss: list[date] = []
        for d, v in raw:
            prev = date(d.year - 1, d.month, d.day)
            if d >= start:
                if prev not in by:
                    raise SeriesError(f"yoy_pct: {d} 의 12개월 전 값({prev})이 원자료에 없다")
                pv = by[prev]
                if v is None or pv is None:
                    miss.append(d)
                else:
                    out.append((d, round((v / pv - 1) * 100, 2)))
        return out, miss
    if op == "month_last":   # v4.4.0 D-0090 작업 2 — 일별 원자료 → 그 달 마지막 관측(값 그대로). 관측 없는 달 = 빈 날짜
        last: dict[date, Optional[float]] = {}
        for d, v in raw:
            m = date(d.year, d.month, 1)
            if v is not None or m not in last:
                last[m] = v if v is not None else last.get(m)
        ms = sorted(m for m in last if m >= start)
        return [(m, last[m]) for m in ms if last[m] is not None], [m for m in ms if last[m] is None]  # type: ignore[misc]
    raise SeriesError(f"구현 없는 transform {op!r} — rules data.transforms 와 이 함수가 같아야 한다(P10)")


SEP_FIGURE = "Figure 2."   # SEP 표 HTML 에서 점도표 표를 찾는 머리(연준 fomcprojtabl*.htm)


def sep_dots(raw_html: str) -> list[dict]:
    """transform sep_dots(v4.4.0 D-0090 작업 2): 연준 SEP HTML 의 그림 2 표(행 = 중간값, 열 = 연도, 칸 = 인원) →
    [{label, values}] 열마다 참가자별 점(값을 인원수만큼, 오름차순). 표를 못 찾거나 칸이 숫자가 아니면 SeriesError."""
    import html as _html  # noqa: PLC0415
    import re  # noqa: PLC0415

    i = raw_html.find(SEP_FIGURE)
    j = raw_html.find("</table>", i)
    if i < 0 or j < 0:
        raise SeriesError(f"SEP 원자료에서 {SEP_FIGURE!r} 표를 찾지 못했다")
    rows = []
    for tr in re.findall(r"<tr.*?</tr>", raw_html[i:j], flags=re.S):
        cells = [re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", c))).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S)]
        rows.append(cells)
    if not rows or len(rows[0]) < 2:
        raise SeriesError("SEP 그림 2 표 머리 행이 없다")
    head, body = rows[0][1:], rows[1:]
    cols: list[list[float]] = [[] for _ in head]
    for r in body:
        if len(r) != len(head) + 1:
            raise SeriesError(f"SEP 표 행 칸 수 {len(r)} ≠ {len(head) + 1}: {r}")
        try:
            v = float(r[0])
            for k, c in enumerate(r[1:]):
                cols[k] += [v] * (int(c) if c else 0)
        except ValueError as ex:
            raise SeriesError(f"SEP 표 칸이 숫자가 아니다: {r} — {ex}") from ex
    return [{"label": h, "values": sorted(c)} for h, c in zip(head, cols)]


def read_scatter_csv(path: Path) -> list[dict]:
    """`column,value` CSV → [{label, values}](열 순서 = 처음 나온 순서)."""
    out: dict[str, list[float]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows or rows[0] != ["column", "value"]:
        raise SeriesError(f"{path}: scatter CSV 머리는 column,value")
    for i, r in enumerate(rows[1:], 2):
        try:
            out.setdefault(r[0], []).append(float(r[1]))
        except (ValueError, IndexError) as ex:
            raise SeriesError(f"{path}:{i}: 값 읽기 실패 {r!r} — {ex}") from ex
    return [{"label": k, "values": v} for k, v in out.items()]


def write_scatter_csv(path: Path, columns: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["column", "value"])
        for c in columns:
            for v in c["values"]:
                w.writerow([c["label"], repr(float(v))])


def _load_scatter(yaml_path: Path, raw: dict) -> SeriesRecord:
    csv_path = yaml_path.with_suffix(".csv")
    try:
        rec = SeriesRecord.model_validate({**raw, "columns": read_scatter_csv(csv_path)})
    except ValidationError as ex:
        raise SeriesError(f"{yaml_path}: {ex}") from ex
    rp = yaml_path.parent / "raw" / f"{yaml_path.stem}.htm"
    if rp.exists():
        if rec.transform.op != "sep_dots":
            raise SeriesError(f"{yaml_path}: scatter 원자료 재적용은 sep_dots 만 — {rec.transform.op}")
        again = sep_dots(rp.read_text(encoding="utf-8"))
        if again != [c.model_dump() for c in rec.columns]:
            raise SeriesError(f"{csv_path}: raw/ 에 sep_dots 를 다시 적용한 값과 다르다")
    return rec


def load_series_file(yaml_path: Path) -> SeriesRecord:
    csv_path = yaml_path.with_suffix(".csv")
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as ex:
        raise SeriesError(f"{yaml_path}: {ex}") from ex
    if not isinstance(raw, dict) or "values" in raw or "columns" in raw:
        raise SeriesError(f"{yaml_path}: 레코드는 dict 이고 값(values)은 {csv_path.name} 에만 둔다")
    if not csv_path.exists():
        raise SeriesError(f"값 파일 없음: {csv_path}")
    if raw.get("kind") == "scatter":
        rec = _load_scatter(yaml_path, raw)
        if rec.series_id != yaml_path.stem:
            raise SeriesError(f"{yaml_path}: series_id {rec.series_id!r} ≠ 파일 이름 {yaml_path.stem!r}")
        return rec
    try:
        rec = SeriesRecord.model_validate({**raw, "values": read_csv(csv_path)})
    except ValidationError as ex:
        raise SeriesError(f"{yaml_path}: {ex}") from ex
    if rec.series_id != yaml_path.stem:
        raise SeriesError(f"{yaml_path}: series_id {rec.series_id!r} ≠ 파일 이름 {yaml_path.stem!r}")
    rp = yaml_path.parent / "raw" / csv_path.name
    if rp.exists():
        again, miss = apply_transform(rec.transform.op, read_csv(rp, allow_empty=True), rec.start)
        if miss != rec.missing_dates():
            raise SeriesError(f"{csv_path}: 원자료의 빈 날짜 {miss} ≠ 레코드 missing {rec.missing_dates()}(D-0086)")
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


__all__ = ["SeriesError", "apply_transform", "load_series", "load_series_file", "read_csv", "read_scatter_csv", "sep_dots", "series_dir",
           "write_csv", "write_scatter_csv"]
