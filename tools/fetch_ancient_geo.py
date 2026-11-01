"""고대 지리 자료 수집기 (v7.4.0 전쟁사 W3, back_and_forth D-0600 §5).

    python tools/fetch_ancient_geo.py projects/<pid> --bbox 15.6 40.9 16.9 41.5 --date -216
        → projects/<pid>/ancient_geo/{places.json, roads.json}, sources.json

--date(EraDate 꼴) 가 있으면 시대 부호가 있는 층(AWMC 가도)은 그 날짜에 쓰이던 것만 남긴다(rules geo.basemap_era.periods, Barrington 시대 구분).
부호 없는 피처는 빼고 개수를 sources.json 에 남긴다. 라이선스 파일 sha1 도 남긴다(D-0601 ① a). 추출 파일은 저장소에 올리지 않는다(프로젝트 .gitignore ancient_geo/).

자료 출처는 `rules geo.basemap_era.sources` 한 곳(고정 커밋, 15 P3). 층마다 순서대로:
  ① 1차 사이트(site) 접속 시험 — 막히면 결과를 기록하고
  ② GitHub 공개 저장소의 고정 커밋에서 그 파일만 받는다(git sparse, 프록시 경유)
  ③ 둘 다 안 되면 그 층은 없다고 기록한다 — spec 에 수동 좌표 + '개략' 출처 줄로 대신한다(스케치 SK-H5)
라이선스가 `rules geo.basemap_era.licenses_allowed` 밖이면 받지 않고 skipped 로 남긴다. 우회·누락은 sources.json 에 전부 남는다(P6 — 조용한 폴백 없음).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date as dt
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from rules import load_rules  # noqa: E402

CACHE = REPO / ".cache" / "ancient_geo"
OUT_DIR = "ancient_geo"
SITE_TIMEOUT_SEC = 15
GIT_TIMEOUT_SEC = 600
BBox = tuple[float, float, float, float]


def _site_ok(url: str) -> str:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "osint_generator fetch_ancient_geo"})
        with urllib.request.urlopen(req, timeout=SITE_TIMEOUT_SEC) as r:  # noqa: S310 — 규칙 파일의 고정 주소
            return f"http {r.status}"
    except (urllib.error.URLError, OSError) as ex:
        return f"막힘: {type(ex).__name__}: {str(ex)[:120]}"


def _git_file(repo: str, commit: str, path: str, extra: tuple[str, ...] = ()) -> Path:
    """고정 커밋의 파일(+ extra 파일)만(blob 필터 + sparse) — 캐시 폴더에 받는다."""
    name = repo.rstrip("/").split("/")[-1]
    d = CACHE / f"{name}_{commit[:10]}"
    target = d / path
    if target.exists() and all((d / e).exists() for e in extra):
        return target
    d.parent.mkdir(parents=True, exist_ok=True)
    run = lambda *a: subprocess.run(["git", *a], cwd=d if d.exists() else d.parent, check=True,  # noqa: E731
                                    capture_output=True, text=True, timeout=GIT_TIMEOUT_SEC)
    if not d.exists():
        run("init", "-q", str(d))
    try:
        run("remote", "add", "origin", repo)
    except subprocess.CalledProcessError:
        run("remote", "set-url", "origin", repo)   # 캐시 폴더를 다시 쓸 때(이미 origin 있음)
    run("sparse-checkout", "set", "--no-cone", "/" + path, *("/" + e for e in extra))
    run("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", commit)
    run("checkout", "-q", commit)
    if not target.exists():
        raise FileNotFoundError(f"{repo}@{commit[:10]} 에 {path} 없음")
    return target


def _in(b: BBox, lon: float, lat: float) -> bool:
    return b[0] <= lon <= b[2] and b[1] <= lat <= b[3]


def _places(src: Path, b: BBox) -> list[dict]:
    out = []
    with src.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                lat, lon = float(r["representative_latitude"]), float(r["representative_longitude"])
            except ValueError:
                continue
            if _in(b, lon, lat):
                out.append({"id": r["id"], "title": r["title"], "lon": round(lon, 5), "lat": round(lat, 5),
                            "precision": r["location_precision"], "uri": r["uri"]})
    return sorted(out, key=lambda p: p["title"])


def _era_ok(code: object, year: int | None, periods: dict) -> bool | None:
    """시대 부호(예 'HRL', 'RL?') 가 year 를 덮으면 True, 아니면 False, 부호가 없으면 None(판정 불가)."""
    if year is None:
        return True
    if not code:
        return None
    return any(lo <= year <= hi for ch, (lo, hi) in periods.items() if ch in str(code))


def _roads(src: Path, b: BBox, field: str | None = None, year: int | None = None, periods: dict | None = None,
           tally: dict | None = None) -> list[list[list[float]]]:
    g = json.loads(src.read_text(encoding="utf-8"))
    out = []
    for ft in g.get("features", []):
        if field is not None:
            ok = _era_ok((ft.get("properties") or {}).get(field), year, periods or {})
            if ok is not True:
                if tally is not None:
                    tally["undated" if ok is None else "other_era"] = tally.get("undated" if ok is None else "other_era", 0) + 1
                continue
        geom = ft.get("geometry") or {}
        lines = geom.get("coordinates", []) if geom.get("type") == "MultiLineString" else [geom.get("coordinates", [])]
        for ln in lines:
            if any(_in(b, x, y) for x, y, *_ in ln):
                out.append([[round(x, 5), round(y, 5)] for x, y, *_ in ln])
    return out


def fetch(project: Path, bbox: BBox, date: str | None = None) -> dict:
    be = load_rules().geo.basemap_era
    if be is None:
        raise SystemExit("rules geo.basemap_era 없음")
    out_dir = project / OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    year = None
    if date:
        from schemas.era_date import parse_era_date  # noqa: PLC0415

        d = parse_era_date(date)
        year = -d.historical_year if d.bce else d.historical_year
    rec: dict = {"schema_version": 1, "bbox": list(bbox), "date": date, "retrieved_at": dt.today().isoformat(), "layers": []}
    for s in be.sources:
        row: dict = {"layer": s.layer, "license": s.license, "attribution": s.attribution, "chain": []}
        if s.license not in be.licenses_allowed:
            row["status"] = "skipped"
            row["chain"].append(f"라이선스 {s.license!r} 가 rules geo.basemap_era.licenses_allowed 밖 — 받지 않음")
            rec["layers"].append(row)
            continue
        if s.site:
            row["chain"].append(f"① {s.site}: {_site_ok(s.site)}")
        try:
            f = _git_file(s.repo, s.commit, s.path, (s.license_path,))
            lic = f.parents[len(Path(s.path).parts) - 1] / s.license_path
            row["license_file"] = s.license_path
            row["license_sha1"] = hashlib.sha1(lic.read_bytes()).hexdigest()
            row["chain"].append(f"② {s.repo}@{s.commit[:10]} {s.path}: 받음")
            tally: dict = {}
            data = (_places(f, bbox) if s.layer == "places"
                    else _roads(f, bbox, s.period_field, year, be.periods, tally))
            if s.period_field is not None:
                row["era_filter"] = {"year": year, "dropped": tally}
            (out_dir / f"{s.layer}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            row.update(status="ok", count=len(data), repo=s.repo, commit=s.commit, path=s.path, file=f"{OUT_DIR}/{s.layer}.json")
        except (subprocess.SubprocessError, OSError) as ex:
            row["chain"].append(f"② {s.repo}: 실패 {type(ex).__name__}: {str(ex)[:160]}")
            row["chain"].append("③ 이 층 없음 — spec 수동 좌표 + '개략' 출처 줄로 대신한다")
            row["status"] = "missing"
        rec["layers"].append(row)
    (out_dir / "sources.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="고대 지리 자료 수집(Pleiades·AWMC, rules geo.basemap_era)")
    ap.add_argument("project", type=Path)
    ap.add_argument("--bbox", type=float, nargs=4, required=True, metavar=("LON0", "LAT0", "LON1", "LAT1"))
    ap.add_argument("--date", help="EraDate 꼴(예 -216) — 시대 부호 층을 그 날짜에 쓰이던 것만")
    a = ap.parse_args(argv)
    rec = fetch(a.project, tuple(a.bbox), a.date)
    print(json.dumps(rec, ensure_ascii=False))
    return 0 if all(r["status"] in ("ok", "skipped") for r in rec["layers"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
