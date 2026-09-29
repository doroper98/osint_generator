"""공개 시리즈 받기 → 데이터 레코드 (v4.3.0, docs/handoff/20 §5.1, back_and_forth D-0084 작업 1·2).

    python tools/fetch_series.py FEDFUNDS --start 2019-01 --transform raw --unit % \
        --source "FRED(세인트루이스 연은) · 원출처 연준 이사회 H.15" --license us_gov_public_domain

- 받는 곳은 FRED `fredgraph.csv?id=`(도메인 = `rules data.sources_allowed`). 받은 CSV 는 `raw/<id>.csv` 에 **그대로** 둔다.
- 값은 `rules data.transforms` 의 연산(명시된 것만)으로 코드가 만든다. yoy_pct 는 12개월 앞부터 받는다.
- 라이선스 표기 원문(license_note)은 시리즈 페이지에서 읽는다. 못 읽으면 오류(추측 금지, C9).
- 레코드(yaml)·값(csv)을 쓴 뒤 로더로 다시 읽어 검증한다(원자료 재적용 일치 포함). 마지막 줄 = 요약 JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from data.series import SeriesError, apply_transform, load_series_file, read_csv, series_dir, write_csv  # noqa: E402
from rules import load_rules  # noqa: E402

CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={cosd}"
PAGE_URL = "https://fred.stlouisfed.org/series/{sid}"
NOTE_RE = re.compile(r"(Public Domain: Citation Requested|Copyrighted: Citation Required|Copyrighted: Permission Required)")
TIMEOUT_SEC = 60


def month(s: str) -> date:
    y, m = (int(x) for x in s.split("-"))
    return date(y, m, 1)


def fetch(url: str) -> bytes:
    r = requests.get(url, timeout=TIMEOUT_SEC)
    r.raise_for_status()
    return r.content


def license_note(sid: str) -> str:
    """시리즈 페이지의 저작권 표기(FRED copyright 칸). 없으면 오류 — 라이선스를 가정하지 않는다(20 §8)."""
    m = NOTE_RE.search(fetch(PAGE_URL.format(sid=sid)).decode("utf-8", "replace"))
    if not m:
        raise SeriesError(f"{sid}: 시리즈 페이지에서 라이선스 표기를 찾지 못했다 — 수동 확인 전 레코드를 만들지 않는다")
    return m.group(1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="FRED 시리즈 → data/series 레코드")
    ap.add_argument("series_id")
    ap.add_argument("--start", required=True, help="YYYY-MM — 첫 값의 달")
    ap.add_argument("--transform", required=True, help="rules data.transforms 키")
    ap.add_argument("--unit", required=True)
    ap.add_argument("--source", required=True, help="출처 줄(화면 표기)")
    ap.add_argument("--license", required=True)
    ap.add_argument("--revision-note", default=None)
    ap.add_argument("--missing-note", action="append", default=[], metavar="YYYY-MM-DD=사유",
                    help="원자료 빈 날짜마다 사유(D-0086). 사유 없는 빈 날짜 = 오류")
    ap.add_argument("--retrieved-at", default=None, help="YYYY-MM-DD(기본 오늘)")
    ap.add_argument("--out", type=Path, default=None, help="레코드 폴더(기본 rules data.series_dir)")
    a = ap.parse_args(argv)
    rules = load_rules().data
    if a.transform not in rules.transforms:
        ap.error(f"--transform {a.transform!r} 는 rules data.transforms 에 없다: {sorted(rules.transforms)}")
    start = month(a.start)
    cosd = date(start.year - 1, start.month, 1) if a.transform == "yoy_pct" else start
    url = CSV_URL.format(sid=a.series_id, cosd=cosd.isoformat())
    out = a.out or series_dir()
    (out / "raw").mkdir(parents=True, exist_ok=True)
    raw_bytes = fetch(url)
    raw_path = out / "raw" / f"{a.series_id}.csv"
    raw_path.write_bytes(raw_bytes)
    raw = read_csv(raw_path, allow_empty=True)
    values, miss = apply_transform(a.transform, raw, start)
    notes = dict(x.split("=", 1) for x in a.missing_note)
    raw_empty = {d for d, v in raw if v is None}
    lacking = [d.isoformat() for d in miss if next((n for k, n in notes.items() if date.fromisoformat(k) in (d, date(d.year - 1, d.month, 1)) and date.fromisoformat(k) in raw_empty), None) is None]
    if lacking:
        raise SeriesError(f"{a.series_id}: 빈 날짜 {lacking} 의 사유(--missing-note) 없음 — 채우지 않고 사유를 기록한다(D-0086)")
    last = values[-1][0]
    rec = {
        "series_id": a.series_id,
        "source": a.source,
        "source_url": url,
        "retrieved_at": a.retrieved_at or date.today().isoformat(),
        "transform": {"op": a.transform, "formula": rules.transforms[a.transform]},
        "as_of": f"{last.year:04d}-{last.month:02d}",
        "revision_note": a.revision_note,
        "unit": a.unit,
        "frequency": "monthly",
        "license": a.license,
        "license_note": license_note(a.series_id),
        "missing": [{"date": d.isoformat(), "note": next(n for k, n in notes.items()
                                                        if date.fromisoformat(k) in (d, date(d.year - 1, d.month, 1)))} for d in miss],
    }
    yp = out / f"{a.series_id}.yaml"
    yp.write_text(yaml.safe_dump(rec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    write_csv(yp.with_suffix(".csv"), values)
    r = load_series_file(yp)   # 다시 읽어 검증(스키마·원자료 재적용 일치)
    print(json.dumps({"series_id": r.series_id, "n": len(r.values), "start": r.start.isoformat(), "end": r.end.isoformat(),
                      "as_of": r.as_of, "license": r.license, "license_note": r.license_note,
                      "raw_md5": hashlib.md5(raw_bytes).hexdigest(),
                      "csv_md5": hashlib.md5(yp.with_suffix(".csv").read_bytes()).hexdigest()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
