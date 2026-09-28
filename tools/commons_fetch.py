"""위키미디어 공용 수집기 (v2.4.0, back_and_forth D-0029 작업 4, 07 §3.2·§5, 13, 19 부록 D prep3 `commons_get`).

검색 → 라이선스·Restrictions 필터 → 표준 폭(960) 또는 원본 다운로드 → PIL 검증 → 권리 기록.

    python tools/commons_fetch.py search "Lee Jae Myung portrait" [--limit 7]
    python tools/commons_fetch.py get "File:X.jpg" DEST [--width 960] [--allow-restricted]
    python tools/commons_fetch.py emblems <project> [--only irgc,cia] [--refresh]
    python tools/commons_fetch.py bundles <project>               # assets/rights_bundles.yaml → 프로젝트 rights_registry

- 요청 간격·429 지수 대기·시도 상한은 `config.yaml commons`(기본 15초, 60·120·240·480·600·600초, `Retry-After` 우선) — Phase 4 run_log 25분·Phase 5 30분 사례(NB4).
- 폭은 표준 썸네일 폭(960·500·1280·1600) 또는 원본. 비표준 폭은 썸네일 생성 요청이 되어 429 가 반복된다(07 §3.2).
- 받은 바이트는 `PIL.Image.open().verify()` 로 검증한다(429 HTML 이 jpg 로 저장되는 사고 방지).
- 허용 라이선스·제한 판정은 `schemas/emblem_models.py`(`license_allowed`, `decide_emblem`). 제한 있는 파일은
  기본적으로 받지 않는다. 휘장은 제한이 하나라도 있으면 `flag_fallback`(D5, README §7.2) — 파일을 받지 않는다.
- 권리 기록: 프로젝트 `assets/rights_registry.json`(people·emblems 절)과 저장소 `assets/emblems/registry.json`.
  필드 대응(07 §7.1 v3 이름 유지): author = `artist`, source_url = `url`, 그리고 `rights_status`·`retrieved_at`.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.config import load_config  # noqa: E402
from schemas.emblem_models import EmblemEntry, EmblemRegistry, decide_emblem, license_allowed  # noqa: E402

UA = {"User-Agent": "osint-video-trial/0.4 (research; https://github.com/doroper98/osint_generator)"}
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
_CFG = load_config().commons              # config.yaml commons — 간격·지수 대기·시도 상한(NB4, 15 P3)
COMMONS_GAP_SEC = _CFG.gap_sec
BACKOFF_BASE_SEC = _CFG.backoff_base_sec
BACKOFF_MAX_SEC = _CFG.backoff_max_sec
TRIES = _CFG.tries
STANDARD_WIDTHS: tuple[int, ...] = tuple(_CFG.standard_widths)
EMBLEM_REGISTRY = REPO / "assets" / "emblems" / "registry.json"
EMBLEM_WIDTH = 500                         # prep3 portraits_emblems: commons_get(title, dest, 500)

# 기관 휘장 후보 (07 §5.2 판단 사례). 제목은 2026-09-28 search 로 확인한 기관 공식본(제한 태그를 피하려 변형본을 고르지 않는다).
# 파일이 없는 기관은 None → flag_fallback(no_emblem_file).
EMBLEM_TITLES: dict[str, tuple[str | None, str]] = {
    "navcent": ("File:United States Naval Forces Central Command patch 2014.png", "us"),
    "centcom": ("File:Seal of United States Central Command.svg", "us"),
    "irgc": ("File:Seal of the Army of the Guardians of the Islamic Revolution.svg", "ir"),
    "rok_navy": ("File:Emblem of the Republic of Korea Navy.svg", "kr"),
    "mnd_korea": ("File:Emblem of the Ministry of National Defense (South Korea).svg", "kr"),
    "cheonghae": (None, "kr"),
    "cia": ("File:Seal of the U.S. Central Intelligence Agency.svg", "us"),
    "potus": ("File:Seal of the President of the United States.svg", "us"),
}


class CommonsError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def backoff_sec(attempt: int, retry_after: str | None = None) -> float:
    """429 대기 시간. `Retry-After`(초)가 있으면 그 값, 없으면 60·2^n 초(최대 600)."""
    if retry_after and retry_after.strip().isdigit():
        return min(float(retry_after), BACKOFF_MAX_SEC)
    return min(BACKOFF_BASE_SEC * 2 ** attempt, BACKOFF_MAX_SEC)


def parse_restrictions(s: str) -> list[str]:
    return [x for x in re.split(r"[\s,;|]+", strip_html(s).lower()) if x]


_last_call = 0.0


def _open(url: str, timeout: float) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def http_get(url: str, timeout: float = 120.0, tries: int = TRIES, api: bool = False) -> bytes:
    """GET. api=True 면 Commons API 간격(15초)을 지킨다. 429 는 지수 대기, 404 는 즉시 실패."""
    global _last_call
    last: Exception | None = None
    for a in range(tries):
        if api:
            wait = COMMONS_GAP_SEC - (time.time() - _last_call)
            if wait > 0:
                time.sleep(wait)
            _last_call = time.time()
        try:
            return _open(url, timeout)
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:
                break
            if e.code == 429:
                w = backoff_sec(a, e.headers.get("Retry-After") if e.headers else None)
                print(f"429 {url[:70]} — {w:.0f}s 대기 ({a + 1}/{tries})", flush=True)
                time.sleep(w)
                continue
            time.sleep(2 ** (a + 1))
        except Exception as e:  # noqa: BLE001 — 재시도 후 CommonsError 로 올린다
            last = e
            time.sleep(2 ** (a + 1))
    raise CommonsError(f"{url}: {last}")


def api(params: dict[str, str]) -> dict:
    url = COMMONS_API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    return json.loads(http_get(url, timeout=40, api=True))


def _ii(page: dict) -> dict:
    ii = page["imageinfo"][0]
    md = ii.get("extmetadata", {})

    def m(k: str) -> str:
        return strip_html(md.get(k, {}).get("value", ""))

    return dict(title=page["title"], lic=m("LicenseShortName"), artist=m("Artist"), credit=m("Credit"),
                date=m("DateTimeOriginal") or m("DateTime"), restr=m("Restrictions"),
                restrictions=parse_restrictions(md.get("Restrictions", {}).get("value", "")),
                page=ii.get("descriptionurl", ""), url=ii.get("url", ""), thumburl=ii.get("thumburl", ""),
                mime=ii.get("mime", ""))


def info(title: str, width: int | None = None) -> dict:
    """파일 1건 메타데이터. width 는 표준 폭만(07 §3.2)."""
    if width is not None and width not in STANDARD_WIDTHS:
        raise CommonsError(f"비표준 폭 {width} — 429 반복 원인(07 §3.2). 허용: {STANDARD_WIDTHS}")
    params = {"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|extmetadata|mime"}
    if width:
        params["iiurlwidth"] = str(width)
    page = next(iter(api(params)["query"]["pages"].values()))
    if "imageinfo" not in page:
        raise CommonsError(f"Commons 파일 없음: {title}")
    return _ii(page)


def search(query: str, limit: int = 7, width: int = 960) -> list[dict]:
    """후보 검색(07 §3.2). 라이선스 허용·제한 여부를 붙여 돌려준다 — 고르는 것은 사람/연출."""
    params = {"action": "query", "generator": "search", "gsrsearch": query, "gsrnamespace": "6", "gsrlimit": str(limit),
              "prop": "imageinfo", "iiprop": "url|extmetadata|mime", "iiurlwidth": str(width)}
    pages = api(params).get("query", {}).get("pages", {})
    out = [_ii(p) for p in pages.values() if "imageinfo" in p]
    for c in out:
        c["allowed"] = license_allowed(c["lic"]) and not c["restrictions"]
    return out


def verify_image(data: bytes) -> None:
    from PIL import Image  # noqa: PLC0415

    Image.open(io.BytesIO(data)).verify()


def download(ii: dict, dest: Path) -> Path:
    """썸네일(표준 폭) → 실패 시 원본. 이미 있으면 받지 않는다(캐시 — legacy 와 같은 바이트 유지)."""
    if dest.exists() and dest.stat().st_size > 100:
        return dest
    last: Exception | None = None
    for src in (ii.get("thumburl"), ii.get("url")):
        if not src:
            continue
        try:
            data = http_get(src, timeout=60)
            verify_image(data)
        except Exception as e:  # noqa: BLE001 — 다음 소스로
            last = e
            print(f"src fail {ii['title'][:40]}: {e}", flush=True)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest
    raise CommonsError(f"다운로드 실패 {ii['title']}: {last}")


def fetch(title: str, dest: Path, width: int | None = 960, allow_restricted: bool = False) -> dict:
    """1건 수집 + 필터. 제한·불허 라이선스면 받지 않고 CommonsError(사람 판단 — 07 §3.2)."""
    ii = info(title, width)
    if not license_allowed(ii["lic"]):
        raise CommonsError(f"허용 안 되는 라이선스 {ii['lic']!r}: {title}")
    if ii["restrictions"] and not allow_restricted:
        raise CommonsError(f"Restrictions {ii['restrictions']}: {title} — 자동 차단(07 §3.2)")
    download(ii, dest)
    return ii


# ------------------------------------------------------------------ 권리 기록
def rights_entry(ii: dict, src: str = "wikimedia_commons") -> dict:
    return dict(src=src, license=ii["lic"], artist=ii["artist"], url=ii["page"], title=ii["title"],
                rights_status="rights_clear" if license_allowed(ii["lic"]) and not ii["restrictions"] else "restricted",
                retrieved_at=now_iso())


def record_rights(registry: Path, section: str, key: str, entry: dict) -> None:
    """프로젝트 rights_registry.json 의 한 절에 기록(없으면 만든다). 스키마 검증 후 저장."""
    from schemas.engine_models import RightsRegistry  # noqa: PLC0415

    reg = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {}
    reg.setdefault(section, {})[key] = entry
    RightsRegistry.model_validate(reg)
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")


BUNDLES = REPO / "assets" / "rights_bundles.yaml"


def record_bundles(registry: Path, bundles: Path = BUNDLES) -> int:
    """묶음 자산 권리(국기·음악·폰트·지도·내레이션)를 프로젝트 권리 레지스트리에 병합. 병합한 항목 수."""
    import yaml  # noqa: PLC0415

    data = yaml.safe_load(bundles.read_text(encoding="utf-8"))
    n = 0
    for sec, entries in data.items():
        if sec == "schema_version":
            continue
        for k, v in entries.items():
            record_rights(registry, sec, k, v)
            n += 1
    return n


# ------------------------------------------------------------------ 휘장
def emblem_entry(eid: str, title: str | None, flag: str, ii: dict | None) -> EmblemEntry:
    if title is None or ii is None:
        dec, why = decide_emblem([], "", has_file=False)
        return EmblemEntry(file=None, decision=dec, reason=why, fallback_flag=flag, fetched_at=now_iso())
    dec, why = decide_emblem(ii["restrictions"], ii["lic"], has_file=True)
    return EmblemEntry(file=f"{eid}.png" if dec == "use" else None, title=title, license=ii["lic"], author=ii["artist"],
                       restrictions=ii["restrictions"], decision=dec, reason=why, fallback_flag=flag,
                       source_url=ii["page"], fetched_at=now_iso())


def load_emblem_registry(path: Path = EMBLEM_REGISTRY) -> EmblemRegistry:
    if not path.exists():
        return EmblemRegistry(emblems={})
    return EmblemRegistry.model_validate_json(path.read_text(encoding="utf-8"))


def fetch_emblems(proj: Path | None, only: list[str] | None = None, refresh: bool = False,
                  registry: Path = EMBLEM_REGISTRY) -> EmblemRegistry:
    """휘장 메타데이터 → 결정(코드) → `use` 만 파일을 받는다. 프로젝트 권리 레지스트리 emblems 절에도 기록."""
    reg = load_emblem_registry(registry)
    for eid, (title, flag) in EMBLEM_TITLES.items():
        if only and eid not in only:
            continue
        ent = reg.emblems.get(eid)
        if ent is None or refresh:
            ii = info(title, EMBLEM_WIDTH) if title else None
            ent = emblem_entry(eid, title, flag, ii)
            reg.emblems[eid] = ent
            registry.parent.mkdir(parents=True, exist_ok=True)
            registry.write_text(reg.model_dump_json(indent=1) + "\n", encoding="utf-8")
            print(f"emblem {eid}: {ent.decision} ({ent.reason})", flush=True)
        if proj is not None and ent.decision == "use":
            ii = info(ent.title or "", EMBLEM_WIDTH)
            download(ii, proj / "assets" / "emblems" / (ent.file or f"{eid}.png"))
            record_rights(proj / "assets" / "rights_registry.json", "emblems", eid,
                          dict(license=ii["lic"], url=ii["page"], title=ii["title"], restrictions=ii["restr"],
                               rights_status="rights_clear", retrieved_at=now_iso()))
    return reg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=7)
    g = sub.add_parser("get")
    g.add_argument("title")
    g.add_argument("dest", type=Path)
    g.add_argument("--width", type=int, default=960)
    g.add_argument("--allow-restricted", action="store_true")
    e = sub.add_parser("emblems")
    e.add_argument("proj", type=Path, nargs="?")
    e.add_argument("--only", default="")
    e.add_argument("--refresh", action="store_true")
    b = sub.add_parser("bundles")
    b.add_argument("proj", type=Path)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "search":
            for c in search(a.query, a.limit):
                print(json.dumps({k: c[k] for k in ("title", "lic", "restrictions", "allowed", "artist")}, ensure_ascii=False))
        elif a.cmd == "get":
            print(json.dumps(rights_entry(fetch(a.title, a.dest, a.width or None, a.allow_restricted)), ensure_ascii=False))
        elif a.cmd == "bundles":
            print(f"bundles {record_bundles(a.proj / 'assets' / 'rights_registry.json')}")
        else:
            fetch_emblems(a.proj, [x for x in a.only.split(",") if x] or None, a.refresh)
    except CommonsError as ex:
        print(f"commons_fetch: {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
