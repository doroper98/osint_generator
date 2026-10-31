"""공시·시세 받기 → 데이터 레코드 (v7.4.0, back_and_forth D-0278 §4.2 · D-0251 E3).

    python tools/fetch_filing.py filing data/series/specs/INTC_REV_Q.yaml          # 명세의 값마다 공시 표에서 읽기
    python tools/fetch_filing.py filing data/series/specs/INTC_REV_Q.yaml --offline   # raw/ 에 둔 원문만(사용자 PC 다운로드 경로)
    python tools/fetch_filing.py price INTC_PX_D --ticker INTC --start 2026-07-01 --end 2026-10-30 --unit 달러 \
        --source "Yahoo Finance chart API · 나스닥 INTC 일별 종가"

filing — 명세(YAML)의 값마다 원문을 받아(`raw/<문서 md5 접두>.htm|json`, 받은 그대로) 표에서 값을 읽는다.
  - `kind: table`(EDGAR 8-K Ex.99.1·10-Q·S-1, IR 보도자료 표): `pandas.read_html` 의 `table` 번째 표에서 첫 열이 `row` 와
    같은 행(공백 정규화)의 `col` 번째 칸. 위치(locator)는 "표 N · 행 '…' · 열 M" 으로 레코드에 남는다.
  - `kind: opendart`(DART 정기보고서 재무제표): OpenDART `fnlttSinglAcntAll` 응답에서 `account_nm`·`sj_div` 행의 `thstrm_amount`.
    키는 .env `DART_API_KEY`(C9). 없으면 안내 줄을 내고 멈춘다(받지 않은 값을 만들지 않는다, P6).
  - 원값·원단위는 레코드 `filings` 에 그대로 남고, 화면 값은 `rules data.filing_scales` 환산(로더가 다시 계산해 대조).
price — Yahoo chart API 일별 종가(transform chart_close). 응답 JSON 을 `raw/<series_id>.json` 에 그대로 두고 로더가 다시 대조한다.

도메인은 `rules data.sources_allowed`, 요청 설정은 `config.yaml data_fetch`. 마지막 줄 = 요약 JSON(raw md5 포함).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal, Optional, Union
from urllib.parse import urlencode, urlparse

import requests
import yaml
from pydantic import BaseModel, ConfigDict, Field

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from data.series import SeriesError, chart_close, load_series_file, series_dir, write_csv  # noqa: E402
from orchestrator.config import load_config  # noqa: E402
from rules import load_rules  # noqa: E402

NUM_RE = re.compile(r"^\(?-?[$₩]?\s*[\d,]+(\.\d+)?\s*\)?$")
DART_NOTICE = ("DART_API_KEY 가 없다 — .env 에 OpenDART 인증키(opendart.fss.or.kr 무료 발급)를 넣거나, "
               "DART 원문을 사용자 PC 에서 받아 raw/ 에 두고 --offline 으로 다시 실행한다")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TableValue(_Strict):
    """공시 문서(HTML) 표의 칸 하나."""

    kind: Literal["table"] = "table"
    date: date
    form: str
    number: str                     # EDGAR accession · DART rcept_no
    filed_on: date
    url: str
    table: Optional[int] = Field(default=None, ge=0)   # pandas.read_html 순번. 없으면 모든 표에서 첫 열이 row 인 행이 정확히 하나여야 한다
    row: str                        # 첫 열 문자열(공백 정규화 후 같아야 한다)
    col: int = Field(ge=1)          # 칸 순번(첫 열 = 0)
    part: Optional[Literal["lo", "hi"]] = None   # 범위 칸("$15.0 - $16.0")의 아래·위 끝 — 가이던스
    raw_unit: str


class DartValue(_Strict):
    """OpenDART 단일회사 전체 재무제표(fnlttSinglAcntAll)의 행 하나."""

    kind: Literal["opendart"]
    date: date
    form: str                       # 예: "분기보고서"
    corp_code: str
    bsns_year: int
    reprt_code: Literal["11013", "11012", "11014", "11011"]   # 1분기·반기·3분기·사업
    fs_div: Literal["CFS", "OFS"] = "CFS"
    sj_div: str                     # IS·CIS·BS·CF
    account_nm: str
    raw_unit: str = "원(재무제표)"


class PdfLineValue(_Strict):
    """회사 IR 자료 PDF(실적 발표 자료) 표의 값 — `pdftotext -layout` 줄에서. anchor(이 문자열 뒤부터) 다음,
    첫 낱말이 label 인 줄 중 occurrence 번째(1부터)의 숫자 낱말 중 token 번째(0부터). 괄호 숫자 = 음수, % 붙은 낱말은 숫자가 아니다."""

    kind: Literal["pdf_line"]
    date: date
    form: str                       # 예: "실적 발표 자료(IR)"
    number: str                     # 자료 식별(파일 이름)
    filed_on: date                  # 발표일
    url: str
    anchor: str
    label: str
    occurrence: int = Field(default=1, ge=1)
    token: int = Field(ge=0)
    raw_unit: str


class XbrlValue(_Strict):
    """SEC XBRL companyfacts(data.sec.gov) 의 사실 하나 — 태그·단위·달력 분기 frame(CY2026Q2). 양식·접수번호·제출일은 사실에서."""

    kind: Literal["xbrl"]
    date: date                      # 달력 분기 말(frame 과 같은 분기)
    cik: int
    tag: str                        # us-gaap 태그(예: RevenueFromContractWithCustomerExcludingAssessedTax)
    unit: Literal["USD", "USD/shares"]
    frame: str = Field(pattern=r"^CY\d{4}Q[1-4]$")


class FilingSpec(_Strict):
    """`data/series/specs/<series_id>.yaml` — 레코드 머리 + 값마다 위치."""

    series_id: str
    source: str
    unit: str
    revision_note: Optional[str] = None
    license_note: str = "공개 공시 기록(DART/EDGAR) — 사실 데이터, 저작권 대상 아님"
    issued_on: Optional[date] = None
    values: list[Union[DartValue, XbrlValue, PdfLineValue, TableValue]] = Field(min_length=1)   # kind 없음 = table


def _cfg():  # noqa: ANN202
    c = load_config().data_fetch
    if c is None:
        raise SeriesError("config.yaml data_fetch 가 없다(P6)")
    return c


def _allowed(url: str) -> None:
    host = urlparse(url).hostname
    ok = load_rules().data.sources_allowed
    if urlparse(url).scheme != "https" or host not in ok:
        raise SeriesError(f"{url}: 도메인 {host!r}(https) 는 rules data.sources_allowed 에 없다: {ok}")


def _get(url: str) -> bytes:
    _allowed(url)
    c = _cfg()
    ua = os.environ.get("EDGAR_USER_AGENT") or c.edgar_user_agent
    r = requests.get(url, timeout=c.timeout_sec, headers={"User-Agent": ua})
    r.raise_for_status()
    time.sleep(c.gap_sec)
    return r.content


def raw_name(key: str, ext: str) -> str:
    """원문 파일 이름 — 요청 키(url·API 매개변수)의 md5 앞 12자리. 같은 문서는 한 번만 받는다."""
    return f"filing_{hashlib.md5(key.encode('utf-8')).hexdigest()[:12]}.{ext}"


def _raw(raw_dir: Path, key: str, ext: str, url: str, offline: bool) -> bytes:
    p = raw_dir / raw_name(key, ext)
    if p.exists():
        return p.read_bytes()
    if offline:
        raise SeriesError(f"--offline: 원문 {p} 가 없다 — {url} 을 받아 이 이름으로 둔다")
    b = _get(url)
    p.write_bytes(b)
    return b


def parse_part(cell: str, part: Optional[str]) -> float:
    """범위 칸 "$15.0 - $16.0" → part lo·hi 끝. part 없으면 parse_number 그대로."""
    if part is None:
        return parse_number(cell)
    bits = re.split(r"\s+[-–]\s+", _norm(cell))
    if len(bits) != 2:
        raise SeriesError(f"범위 칸이 아니다(part {part}): {cell!r}")
    return parse_number(bits[0 if part == "lo" else 1])


def parse_number(cell: str) -> float:
    """"13,653" · "(1,234)" · "$ 0.52" · "-0.8" → float. 숫자가 아니면 오류(빈 칸·"—" 를 0 으로 읽지 않는다).
    꼬리 " billion"(보도자료 부문 표 "$8.5 billion")은 떼어 낸다 — 단위는 명세 raw_unit(십억 달러)이 정한다."""
    s = re.sub(r"\s+billion$", "", re.sub(r"\s+", " ", str(cell)).strip())
    if not NUM_RE.match(s):
        raise SeriesError(f"표 칸이 숫자가 아니다: {cell!r}")
    neg = s.startswith("(") or "-" in s
    v = float(re.sub(r"[^\d.]", "", s))
    return -v if neg else v


def _norm(x: object) -> str:
    return re.sub(r"\s+", " ", str(x)).strip()


def read_tables(html: bytes) -> list:  # noqa: ANN201
    import pandas as pd  # noqa: PLC0415

    return [t.astype(str) for t in pd.read_html(io.BytesIO(html), flavor="lxml")]


def table_cell(html: bytes, table: Optional[int], row: str, col: int, part: Optional[str] = None) -> tuple[float, int, str]:
    """(값, 표 순번, 칸 문자열). table 이 없으면 모든 표에서 첫 열 = row 인 행이 정확히 하나여야 한다(추측 금지)."""
    tables = read_tables(html)
    if table is not None and table >= len(tables):
        raise SeriesError(f"표 {table} 없음 — 문서의 표 {len(tables)}개")
    idx = [table] if table is not None else range(len(tables))
    hits = [(t, i) for t in idx for i in range(len(tables[t])) if _norm(tables[t].iat[i, 0]) == _norm(row)]
    if len(hits) != 1:
        raise SeriesError(f"표 {'전체' if table is None else table}: 첫 열 {row!r} 행이 {len(hits)}개(정확히 하나여야 한다 — table 을 적는다)")
    t, i = hits[0]
    if col >= tables[t].shape[1]:
        raise SeriesError(f"표 {t}: 열 {col} 없음 — {tables[t].shape[1]}열")
    cell = _norm(tables[t].iat[i, col])
    return parse_part(cell, part), t, cell


PDF_NUM = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?$")


def pdf_line(pdf: bytes, v: PdfLineValue) -> tuple[float, str]:
    """(원값, 그 줄 문자열). pdftotext(poppler-utils) 가 없거나 줄·낱말이 없으면 오류(추측 금지)."""
    import shutil  # noqa: PLC0415
    import subprocess  # noqa: PLC0415
    import tempfile  # noqa: PLC0415

    if shutil.which("pdftotext") is None:
        raise SeriesError("pdftotext(poppler-utils) 가 없다 — apt-get install poppler-utils")
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in.pdf"
        src.write_bytes(pdf)
        txt = subprocess.run(["pdftotext", "-layout", str(src), "-"], check=True, capture_output=True).stdout.decode("utf-8")
    i = txt.find(v.anchor)
    if i < 0:
        raise SeriesError(f"PDF 에 anchor {v.anchor!r} 없음")
    lines = [ln for ln in txt[i:].splitlines() if ln.split() and ln.split()[0] == v.label]
    if len(lines) < v.occurrence:
        raise SeriesError(f"anchor 뒤 첫 낱말 {v.label!r} 줄이 {len(lines)}개 < occurrence {v.occurrence}")
    ln = lines[v.occurrence - 1]
    nums = [t for t in ln.split()[1:] if PDF_NUM.match(t)]
    if v.token >= len(nums):
        raise SeriesError(f"{v.label!r} 줄의 숫자 낱말 {len(nums)}개 ≤ token {v.token}: {ln.strip()!r}")
    return parse_number(nums[v.token]), ln.strip()


def xbrl_fact(js: bytes, v: XbrlValue) -> dict:
    """companyfacts 에서 태그·단위·frame 이 맞는 사실 하나(정확히 하나 — 없거나 여럿이면 오류)."""
    try:
        rows = json.loads(js)["facts"]["us-gaap"][v.tag]["units"][v.unit]
    except KeyError as ex:
        raise SeriesError(f"XBRL us-gaap:{v.tag} [{v.unit}] 없음 — {ex}") from ex
    hit = [r for r in rows if r.get("frame") == v.frame]
    if len(hit) != 1:
        raise SeriesError(f"XBRL us-gaap:{v.tag} frame {v.frame} 사실이 {len(hit)}개(정확히 하나여야 한다)")
    q = int(v.frame[-1])
    if (v.date.year, (v.date.month - 1) // 3 + 1) != (int(v.frame[2:6]), q):
        raise SeriesError(f"XBRL frame {v.frame} 와 값 날짜 {v.date} 의 분기가 다르다")
    return hit[0]


def dart_row(js: bytes, v: DartValue) -> tuple[float, str]:
    """(원값, rcept_no). 상태 000 이 아니거나 행이 하나가 아니면 오류."""
    d = json.loads(js)
    if d.get("status") != "000":
        raise SeriesError(f"OpenDART 응답 {d.get('status')}: {d.get('message')}")
    rows = [r for r in d.get("list", []) if r.get("sj_div") == v.sj_div and r.get("account_nm") == v.account_nm]
    if len(rows) != 1:
        raise SeriesError(f"OpenDART {v.sj_div} {v.account_nm!r} 행이 {len(rows)}개(정확히 하나여야 한다)")
    return parse_number(rows[0]["thstrm_amount"]), rows[0]["rcept_no"]


def build_filing(spec: FilingSpec, raw_dir: Path, offline: bool, today: date) -> tuple[dict, list[tuple[date, float]], list[str]]:
    """명세 → (레코드 dict, 값, raw md5 목록)."""
    filings: list[dict] = []
    md5s: list[str] = []
    for v in spec.values:
        if isinstance(v, TableValue):
            b = _raw(raw_dir, v.url, "htm", v.url, offline)
            raw_v, t, cell = table_cell(b, v.table, v.row, v.col, v.part)
            if cell.endswith("billion") and v.raw_unit != "십억 달러":
                raise SeriesError(f"{v.row}: 칸 {cell!r} 은 billion — raw_unit 십억 달러")
            f = {"date": v.date, "form": v.form, "number": v.number, "filed_on": v.filed_on, "item": v.row,
                 "locator": f"표 {t} · 행 '{v.row}' · 열 {v.col}" + (f" · 범위 {v.part}" if v.part else ""), "url": v.url}
        elif isinstance(v, PdfLineValue):
            b = _raw(raw_dir, v.url, "pdf", v.url, offline)
            raw_v, line = pdf_line(b, v)
            f = {"date": v.date, "form": v.form, "number": v.number, "filed_on": v.filed_on, "item": v.label,
                 "locator": f"pdftotext -layout · '{v.anchor}' 뒤 '{v.label}' 줄 {v.occurrence}번째 · 숫자 {v.token}번째", "url": v.url}
        elif isinstance(v, XbrlValue):
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{v.cik:010d}.json"
            b = _raw(raw_dir, url, "json", url, offline)
            fact = xbrl_fact(b, v)
            f = {"date": v.date, "form": fact["form"], "number": fact["accn"], "filed_on": date.fromisoformat(fact["filed"]),
                 "item": v.tag, "locator": f"XBRL companyfacts us-gaap:{v.tag} [{v.unit}] frame {v.frame} · 회계 기간 말 {fact['end']}",
                 "url": f"https://www.sec.gov/Archives/edgar/data/{v.cik}/{fact['accn'].replace('-', '')}/"}
            raw_v = float(fact["val"])
        else:
            key = os.environ.get("DART_API_KEY", "")
            q = {"corp_code": v.corp_code, "bsns_year": v.bsns_year, "reprt_code": v.reprt_code, "fs_div": v.fs_div}
            req_key = json.dumps(q, sort_keys=True)
            if not (raw_dir / raw_name(req_key, "json")).exists() and not offline and not key:
                raise SeriesError(DART_NOTICE)
            url = f"{_cfg().opendart_base}/fnlttSinglAcntAll.json?" + urlencode({"crtfc_key": key, **q})
            b = _raw(raw_dir, req_key, "json", url, offline)   # 파일 이름은 키를 뺀 매개변수로(키를 남기지 않는다)
            raw_v, rcept = dart_row(b, v)
            f = {"date": v.date, "form": v.form, "number": rcept, "filed_on": datetime.strptime(rcept[:8], "%Y%m%d").date(),
                 "item": v.account_nm, "locator": f"OpenDART fnlttSinglAcntAll {v.fs_div} {v.sj_div} · thstrm_amount",
                 "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}"}
        md5 = hashlib.md5(b).hexdigest()
        md5s.append(md5)
        f.update(raw_value=raw_v, raw_unit=v.raw_unit, raw_md5=md5)
        filings.append(f)
    filings.sort(key=lambda f: f["date"])
    scales = load_rules().data.filing_scales
    values = [(f["date"], round(f["raw_value"] * scales[f["raw_unit"]].factor, scales[f["raw_unit"]].digits)) for f in filings]
    last = spec.issued_on or values[-1][0]
    rec = {
        "source_kind": "filing",
        "series_id": spec.series_id,
        "source": spec.source,
        "source_url": filings[-1]["url"],
        "retrieved_at": today.isoformat(),
        "transform": {"op": "filing", "formula": load_rules().data.transforms["filing"]},
        "as_of": f"{last.year:04d}-{last.month:02d}",
        "revision_note": spec.revision_note,
        "unit": spec.unit,
        "frequency": "quarterly",
        "license": "public_filing",
        "license_note": spec.license_note,
        "filings": [{**f, "date": f["date"].isoformat(), "filed_on": f["filed_on"].isoformat()} for f in filings],
    }
    if spec.issued_on:
        rec["issued_on"] = spec.issued_on.isoformat()
    return rec, values, md5s


def _write(out: Path, rec: dict, values: list[tuple[date, float]]) -> Path:
    yp = out / f"{rec['series_id']}.yaml"
    yp.write_text(yaml.safe_dump(rec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    write_csv(yp.with_suffix(".csv"), values)
    return yp


def cmd_filing(a: argparse.Namespace) -> int:
    spec = FilingSpec.model_validate(yaml.safe_load(Path(a.spec).read_text(encoding="utf-8")))
    out = a.out or series_dir()
    (out / "raw").mkdir(parents=True, exist_ok=True)
    rec, values, md5s = build_filing(spec, out / "raw", a.offline, a.retrieved_at or date.today())
    r = load_series_file(_write(out, rec, values))   # 다시 읽어 검증(환산 대조 포함)
    print(json.dumps({"series_id": r.series_id, "n": len(r.values), "values": [[d.isoformat(), v] for d, v in r.values],
                      "unit": r.unit, "raw_md5": md5s}, ensure_ascii=False))
    return 0


def cmd_price(a: argparse.Namespace) -> int:
    out = a.out or series_dir()
    (out / "raw").mkdir(parents=True, exist_ok=True)
    jp = out / "raw" / f"{a.series_id}.json"
    p1 = int(datetime.combine(a.start, datetime.min.time(), tzinfo=timezone.utc).timestamp())
    p2 = int(datetime.combine(a.end, datetime.max.time(), tzinfo=timezone.utc).timestamp())
    url = f"{_cfg().yahoo_chart_base}/{a.ticker}?" + urlencode({"period1": p1, "period2": p2, "interval": "1d"})
    if a.offline or (jp.exists() and not a.refresh):   # 캐시(raw json 재사용) — Yahoo 429 를 피한다(감독 지시). 새로 받으려면 --refresh
        if not jp.exists():
            raise SeriesError(f"--offline: {jp} 가 없다 — {url} 응답을 이 이름으로 둔다")
        b = jp.read_bytes()
    else:
        b = _get(url)
        jp.write_bytes(b)
    notes = dict(x.split("=", 1) for x in a.missing_note)
    nulls: list[date] = []
    closes = chart_close(b.decode("utf-8"), nulls)
    for d in nulls:   # v7.4.0 D-0319 ① — null 종가 = missing(사유 rules data.chart_null_note), 기간 안만
        if a.start <= d <= a.end:
            notes.setdefault(d.isoformat(), load_rules().data.chart_null_note)
    skip = {date.fromisoformat(k) for k in notes}
    values = [(d, v) for d, v in closes if a.start <= d <= a.end and d not in skip]
    if len(values) < 2:
        raise SeriesError(f"{a.ticker}: {a.start}~{a.end} 종가 {len(values)}개")
    last = values[-1][0]
    rec = {
        "series_id": a.series_id,
        "source": a.source,
        "source_url": url,
        "retrieved_at": (a.retrieved_at or date.today()).isoformat(),
        "transform": {"op": "chart_close", "formula": load_rules().data.transforms["chart_close"]},
        "as_of": f"{last.year:04d}-{last.month:02d}",
        "revision_note": None,
        "unit": a.unit,
        "frequency": "daily",
        "license": "private_only_market_data",
        "license_note": a.license_note,
        "missing": [{"date": k, "note": n} for k, n in sorted(notes.items())],
    }
    cites = []
    for c in a.cite:   # [price-outlier] 급변일 보도 확인: 날짜=매체|보도일|url|메모
        d, rest = c.split("=", 1)
        outlet, pub, url, note = (rest.split("|") + [None])[:4]
        cites.append({"date": d, "outlet": outlet, "pub_date": pub, "url": url, "note": note})
    if cites:
        rec["cited"] = sorted(cites, key=lambda x: x["date"])
    r = load_series_file(_write(out, rec, values))
    print(json.dumps({"series_id": r.series_id, "n": len(r.values), "start": r.start.isoformat(), "end": r.end.isoformat(),
                      "last": r.values[-1][1], "raw_md5": hashlib.md5(b).hexdigest()}, ensure_ascii=False))
    return 0


def cmd_scan(a: argparse.Namespace) -> int:
    """명세 작성 보조 — 원문(raw 파일 또는 url)의 표마다 머리 행과 첫 열 행 이름을 출력한다(값을 레코드로 쓰지 않는다)."""
    p = Path(a.source)
    b = p.read_bytes() if p.exists() else _get(a.source)
    for t, df in enumerate(read_tables(b)):
        print(json.dumps({"table": t, "shape": list(df.shape), "head": [_norm(x) for x in df.iloc[0].tolist()] if len(df) else [],
                          "rows": [_norm(x) for x in df.iloc[:, 0].tolist()][:40]}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="공시 표·OpenDART·Yahoo 일별 종가 → data/series 레코드")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("filing")
    f.add_argument("spec")
    p = sub.add_parser("price")
    p.add_argument("series_id")
    p.add_argument("--ticker", required=True, help="Yahoo 표기(005930.KS, INTC)")
    p.add_argument("--start", required=True, type=date.fromisoformat)
    p.add_argument("--end", required=True, type=date.fromisoformat)
    p.add_argument("--unit", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--license-note", default="Yahoo Finance 이용약관 — 시세 재배포 제한(비공개 시청용 기록, D264)")
    p.add_argument("--refresh", action="store_true", help="캐시(raw/<id>.json)가 있어도 다시 받는다")
    p.add_argument("--missing-note", action="append", default=[], metavar="YYYY-MM-DD=사유",
                   help="받은 값을 쓰지 않을 거래일(급변일 보도 원문 미확인 등) — 선이 끊긴다")
    p.add_argument("--cite", action="append", default=[], metavar="YYYY-MM-DD=매체|보도일|url|메모",
                   help="하루 변동 ≥ rules data.price_outlier_pct 인 날의 보도 확인([price-outlier])")
    sc = sub.add_parser("scan", help="원문 표 목록(명세 작성 보조)")
    sc.add_argument("source", help="raw 파일 경로 또는 https url")
    for s in (f, p):
        s.add_argument("--offline", action="store_true", help="raw/ 원문만 읽는다(받지 않는다)")
        s.add_argument("--retrieved-at", type=date.fromisoformat, default=None)
        s.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    try:
        return {"filing": cmd_filing, "price": cmd_price, "scan": cmd_scan}[a.cmd](a)
    except (SeriesError, requests.RequestException) as ex:
        print(json.dumps({"error": str(ex)}, ensure_ascii=False))
        return 3 if str(ex) == DART_NOTICE else 2


if __name__ == "__main__":
    sys.exit(main())
