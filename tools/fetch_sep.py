"""연준 SEP 점도표 받기 → scatter 데이터 레코드 (v4.4.0, docs/handoff/20 §5.1·§5.2, back_and_forth D-0090 작업 2).

    python tools/fetch_sep.py 20260916

- 받는 곳: `https://www.federalreserve.gov/monetarypolicy/fomcprojtabl<YYYYMMDD>.htm`(도메인 = `rules data.sources_allowed`).
  받은 HTML 은 `raw/SEP_<YYYYMMDD>.htm` 에 **그대로** 둔다. 값은 transform `sep_dots`(그림 2 표 → 참가자별 점)로 코드가 만든다.
- 라이선스: 미국 연방정부 기관(연준 이사회)의 공식 발표. 표기 원문(license_note)은 인자로 받는다 — 추측으로 채우지 않는다(C9).
- 레코드를 쓴 뒤 로더로 다시 읽어 검증한다(원자료 재적용 일치 포함). 마지막 줄 = 요약 JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import requests
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from data.series import load_series_file, sep_dots, series_dir, write_scatter_csv  # noqa: E402
from rules import load_rules  # noqa: E402

URL = "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl{d}.htm"
TIMEOUT_SEC = 60


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="연준 SEP 점도표 → data/series scatter 레코드")
    ap.add_argument("release", help="YYYYMMDD — SEP 발표일(FOMC 회의 둘째 날)")
    ap.add_argument("--source", default="연준 FOMC 경제 전망 요약(SEP) 그림 2")
    ap.add_argument("--license", default="us_gov_public_domain")
    ap.add_argument("--license-note", required=True, help="출처의 권리 표기(원문 또는 확인 근거)")
    ap.add_argument("--revision-note", default=None)
    ap.add_argument("--retrieved-at", default=None, help="YYYY-MM-DD(기본 오늘)")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    rel = date(int(a.release[:4]), int(a.release[4:6]), int(a.release[6:]))
    url = URL.format(d=a.release)
    r = requests.get(url, timeout=TIMEOUT_SEC)
    r.raise_for_status()
    out = a.out or series_dir()
    (out / "raw").mkdir(parents=True, exist_ok=True)
    sid = f"SEP_{a.release}"
    raw_path = out / "raw" / f"{sid}.htm"
    raw_path.write_bytes(r.content)
    cols = sep_dots(raw_path.read_text(encoding="utf-8"))
    rules = load_rules().data
    rec = {
        "kind": "scatter",
        "series_id": sid,
        "source": a.source,
        "source_url": url,
        "retrieved_at": a.retrieved_at or date.today().isoformat(),
        "transform": {"op": "sep_dots", "formula": rules.transforms["sep_dots"]},
        "as_of": f"{rel:%Y-%m}",
        "revision_note": a.revision_note,
        "unit": "%",
        "frequency": "release",
        "license": a.license,
        "license_note": a.license_note,
        "released": rel.isoformat(),
    }
    yp = out / f"{sid}.yaml"
    yp.write_text(yaml.safe_dump(rec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    write_scatter_csv(yp.with_suffix(".csv"), cols)
    got = load_series_file(yp)
    print(json.dumps({"series_id": got.series_id, "columns": {c.label: {"n": len(c.values), "median": c.median()} for c in got.columns},
                      "raw_md5": hashlib.md5(r.content).hexdigest(),
                      "csv_md5": hashlib.md5(yp.with_suffix(".csv").read_bytes()).hexdigest()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
