"""Phase 1 골든 재현 데이터 수집기 (v2.0.1, back_and_forth D-0002 작업 2).

골든 재현에 필요한 입력을 `V3_ROOT`(기본 `projects/hormuz_korea_legacy`, gitignore) 아래에 만든다.
v2.5.5(D32 sunset 2/2): 자산 부트스트랩(v3 참조 코드 실행본)은 모두 정식 도구로 옮기고 폴더째 삭제했다 —
인물·국기 = tools/commons_fetch·portrait_fallback(v2.4.0), 미디어 = tools/media_fetch(v2.5.5).
출처·수치는 docs/handoff/19a §B·§H, 07 §3.2, 14 §10.4, reference_code/v3_hormuz_korea/media3b_round2.md 를 따른다.

사용법:
    python tools/fetch_data.py fonts | ne | tiles | flags | commons | people | media | all [--dry-run]

- fonts   : IBM Plex Sans KR 4종·IBM Plex Mono 2종·GmarketSans 2종(woff→otf) → assets/fonts/.cache → 사용자 폰트 폴더 설치 (D3)
- ne      : Natural Earth 10m admin0·admin1·populated places GeoJSON → V3_ROOT/data
- tiles   : terrarium 지형 타일 W z5 / G z7 / K z7 → V3_ROOT/data/{t5,tg,tk}/{x}_{y}.png
- flags   : flag-icons SVG 13개국(1x1·4x3) → V3_ROOT/assets/flags_svg (PNG 변환은 prep3 flags)
- commons : Commons 메타데이터 → V3_ROOT/data/commons_v3.json (인물 2·휘장 1) + 원본 미리 받기
- people  : tools/portrait_fallback.py(초상)·tools/commons_fetch.py(권리 기록) — 인물 4·휘장·국기 PNG·rights_registry(+ assets/rights_bundles.yaml) (v2.4.0 D-0029)
- media   : tools/media_fetch.py — assets/media/media_registry.json 7종(사진·영상·컷아웃, 기사는 파일 없음) 받기·md5 대조·가공·영상 검수 시트
- bgm     : 배경음악 mp3 를 git 객체(bd37b58)에서 복원 + sha1 대조 (네트워크 불필요, DECISIONS D22)
- all     : fonts ne tiles flags commons bgm (people → media 는 따로 — 런북 순서)

실패는 조용히 넘기지 않는다: 받지 못한 파일이 있으면 목록을 출력하고 exit 1 (docs/handoff/15 P6).
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))   # tools.commons_fetch · tools.portrait_fallback

from tools import commons_fetch  # noqa: E402 — HTTP 층 하나(NB4)
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# 19a §H — 티어 경계와 타일 줌 (prep3 TIERS 와 같은 값)
TIERS: dict[str, dict[str, float | int | str]] = {
    "W": dict(lon0=28.0, lon1=140.0, lat0=-12.0, lat1=48.0, z=5, dir="t5"),
    "G": dict(lon0=46.0, lon1=62.0, lat0=20.5, lat1=32.5, z=7, dir="tg"),
    "K": dict(lon0=122.5, lon1=131.8, lat0=32.3, lat1=39.8, z=7, dir="tk"),
}
TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
NE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{name}.geojson"
NE_FILES = ("ne_10m_admin_0_countries", "ne_10m_admin_1_states_provinces", "ne_10m_populated_places")
FLAG_URL = "https://raw.githubusercontent.com/lipis/flag-icons/main/flags/{kind}/{c}.svg"
FLAG_CODES = ("kr", "us", "ir", "cn", "in", "de", "gb", "jp", "au", "fr", "it", "nl", "ca")  # render3 PIL_IMG
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl"
FONT_URLS: dict[str, str] = {
    **{f"IBMPlexSansKR-{w}.ttf": f"{GF}/ibmplexsanskr/IBMPlexSansKR-{w}.ttf" for w in ("Regular", "Medium", "SemiBold", "Bold")},
    **{f"IBMPlexMono-{w}.ttf": f"{GF}/ibmplexmono/IBMPlexMono-{w}.ttf" for w in ("Medium", "SemiBold")},
}
GMARKET_URL = "https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSans{w}.woff"

# commons_v3.json — prep3 portraits_emblems() 가 정확한 title 로 고른다 (reference rights_registry.json 기준)
COMMONS_PEOPLE: dict[str, str] = {
    "lee_jae_myung": "File:Lee Jae Myung portrait.jpg",
    "roh_moo_hyun": "File:Roh Moo-hyun presidential portrait.jpg",
}
COMMONS_EMBLEMS: dict[str, str] = {"centcom": "File:United States Naval Forces Central Command patch 2014.png"}
# 미리 받기: legacy 코드는 파일이 없을 때만 Commons API 를 다시 부른다(prep3 commons_get, media3 thumb_url —
# 후자는 재시도 없음). 메타데이터 조회 1회로 legacy 코드가 요청할 것과 **같은 폭**의 파일을 같은 경로에 둔다.
# key → (폭 또는 None=원본, V3_ROOT 기준 경로). 폭 근거: prep3 commons_get 960/500, media3 thumb 1280/960, round2 1600
PREFETCH: dict[str, tuple[int | None, str]] = {
    "lee_jae_myung": (960, "assets/photo_lee_jae_myung.jpg"),
    "roh_moo_hyun": (960, "assets/photo_roh_moo_hyun.jpg"),
    "centcom": (500, "assets/emblems/navcent.png"),
}
# D22 — BGM 은 추적 해제됐고 git 객체에서 복원한다. 파일명·sha1 은 BGM 레지스트리(v3.4.0 SSOT)에서 읽는다.
BGM_ID = "music.zabriskie_patriarch"
BGM_COMMIT = "bd37b58"


def _bgm_entry() -> tuple[str, str]:
    from audio.registry import track  # noqa: PLC0415

    t = track(BGM_ID)
    assert t.sha1 is not None
    return t.file, t.sha1


class FetchError(RuntimeError):
    pass


# ------------------------------------------------------------------ 경로
def v3_root() -> Path:
    return (REPO / os.environ.get("V3_ROOT", "projects/hormuz_korea_legacy")).resolve()


def ensure_dirs(root: Path) -> None:
    for sub in ("data", "data/t5", "data/tg", "data/tk", "assets/portraits", "assets/emblems", "assets/flags",
                "assets/flags_svg", "media", "prev", "tts"):
        (root / sub).mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ 순수 함수 (테스트 대상)
def lonlat_to_tile(lon: float, lat: float, z: int) -> tuple[int, int]:
    """웹 메르카토르 슬리피 타일 좌표 (x, y)."""
    n = 2 ** z
    x = int(math.floor((lon + 180.0) / 360.0 * n))
    lat_r = math.radians(lat)
    y = int(math.floor((1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n))
    return max(0, min(n - 1, x)), max(0, min(n - 1, y))


def tile_range(lon0: float, lat0: float, lon1: float, lat1: float, z: int) -> tuple[range, range]:
    """bbox 를 덮는 타일 x·y 범위(양 끝 포함). y 는 북쪽(lat1)이 작다."""
    x0, y0 = lonlat_to_tile(lon0, lat1, z)
    x1, y1 = lonlat_to_tile(lon1, lat0, z)
    return range(x0, x1 + 1), range(y0, y1 + 1)


def strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


# ------------------------------------------------------------------ 네트워크
def http_get(url: str, timeout: float = 120.0) -> bytes:
    """GET — HTTP 층은 tools/commons_fetch 하나(429 지수 대기·시도 상한 = config.yaml commons, NB4)."""
    try:
        return commons_fetch.http_get(url, timeout=timeout)
    except commons_fetch.CommonsError as e:
        raise FetchError(str(e)) from e


def download(url: str, dest: Path) -> bool:
    """이미 있으면 건너뛴다(캐시). 받았으면 True."""
    if dest.exists() and dest.stat().st_size > 100:
        return False
    data = http_get(url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True


def commons_call(params: dict[str, str]) -> dict:
    """Commons API 1회 — commons_fetch.api(요청 간격·429 대기·상한 = config.yaml commons)."""
    try:
        return commons_fetch.api(params)
    except commons_fetch.CommonsError as e:
        raise FetchError(f"commons 429/오류 — 시도 상한 소진: {params.get('titles')}: {e}") from e


def commons_info(title: str, width: int | None = None) -> dict:
    params = {"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|extmetadata|mediatype"}
    if width:
        params["iiurlwidth"] = str(width)
    pages = commons_call(params)["query"]["pages"]
    page = next(iter(pages.values()))
    if "imageinfo" not in page:
        raise FetchError(f"Commons 파일 없음: {title}")
    ii = page["imageinfo"][0]
    md = ii.get("extmetadata", {})

    def m(k: str) -> str:
        return strip_html(md.get(k, {}).get("value", ""))

    return dict(
        title=title,
        lic=m("LicenseShortName"),
        artist=m("Artist"),
        date=m("DateTimeOriginal") or m("DateTime"),
        restr=m("Restrictions"),
        page=ii.get("descriptionurl", ""),
        url=ii.get("url", ""),
        thumburl=ii.get("thumburl", ""),
    )


# ------------------------------------------------------------------ 서브커맨드
def cmd_fonts(root: Path, dry: bool) -> list[str]:
    cache = REPO / "assets" / "fonts" / ".cache"
    target = Path(os.environ.get("OSINT_FONT_DIR", Path.home() / ".local" / "share" / "fonts" / "osint"))
    if dry:
        return [f"fonts → {cache} → {target}: {', '.join(list(FONT_URLS) + ['GmarketSansBold.otf', 'GmarketSansMedium.otf'])}"]
    cache.mkdir(parents=True, exist_ok=True)
    for name, url in FONT_URLS.items():
        download(url, cache / name)
    from fontTools.ttLib import TTFont

    for w in ("Bold", "Medium"):
        otf = cache / f"GmarketSans{w}.otf"
        if not otf.exists():
            f = TTFont(io.BytesIO(http_get(GMARKET_URL.replace("{w}", w))))
            f.flavor = None
            f.save(str(otf))
    target.mkdir(parents=True, exist_ok=True)
    for p in cache.iterdir():
        shutil.copy2(p, target / p.name)
    subprocess.run(["fc-cache", "-f"], capture_output=True, check=False)
    return []


def cmd_ne(root: Path, dry: bool) -> list[str]:
    if dry:
        return [f"ne → {root / 'data'}: {', '.join(NE_FILES)}"]
    for name in NE_FILES:
        if download(NE_URL.replace("{name}", name), root / "data" / f"{name}.geojson"):
            print(f"ne {name}", flush=True)
    return []


def cmd_tiles(root: Path, dry: bool) -> list[str]:
    out: list[str] = []
    missing: list[str] = []
    for name, T in TIERS.items():
        xr, yr = tile_range(float(T["lon0"]), float(T["lat0"]), float(T["lon1"]), float(T["lat1"]), int(T["z"]))
        out.append(f"tiles {name} z{T['z']} x{xr.start}–{xr.stop - 1} y{yr.start}–{yr.stop - 1} ({len(xr) * len(yr)}장)")
        if dry:
            continue
        for x in xr:
            for y in yr:
                dest = root / "data" / str(T["dir"]) / f"{x}_{y}.png"
                try:
                    download(TILE_URL.replace("{z}", str(T["z"])).replace("{x}", str(x)).replace("{y}", str(y)), dest)
                except FetchError as e:
                    missing.append(str(e))
    if dry:
        return out
    print("\n".join(out), flush=True)
    return missing


def cmd_flags(root: Path, dry: bool) -> list[str]:
    if dry:
        return [f"flags → {root / 'assets/flags_svg'}: {' '.join(FLAG_CODES)} (1x1, 4x3)"]
    for c in FLAG_CODES:
        download(FLAG_URL.replace("{kind}", "1x1").replace("{c}", c), root / "assets" / "flags_svg" / f"{c}.svg")
        download(FLAG_URL.replace("{kind}", "4x3").replace("{c}", c), root / "assets" / "flags_svg" / f"{c}_4x3.svg")
    return []


def _cached_info(root: Path, key: str, title: str) -> dict:
    """항목별 캐시(data/commons_cache/{key}.json) — 429 로 중단돼도 받은 것은 다시 묻지 않는다."""
    cache = root / "data" / "commons_cache" / f"{key}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    width = PREFETCH[key][0]
    info = commons_info(title, width=width)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"commons {key}: {info['lic']}", flush=True)
    return info


def cmd_commons(root: Path, dry: bool) -> list[str]:
    if dry:
        return [f"commons → commons_v3.json {list(COMMONS_PEOPLE) + list(COMMONS_EMBLEMS)}, 미리 받기 {len(PREFETCH)}건"]
    failures: list[str] = []
    infos: dict[str, dict] = {}
    for key, title in {**COMMONS_PEOPLE, **COMMONS_EMBLEMS}.items():
        try:
            infos[key] = _cached_info(root, key, title)
        except FetchError as e:
            failures.append(f"commons {key}: {e}")
            continue
        width, rel = PREFETCH[key]
        src = (infos[key]["thumburl"] if width else "") or infos[key]["url"]
        try:
            if download(src, root / rel):
                print(f"prefetch {rel}", flush=True)
        except FetchError as e:
            failures.append(f"prefetch {rel}: {e}")
    if set(COMMONS_PEOPLE) | set(COMMONS_EMBLEMS) <= set(infos):
        (root / "data" / "commons_v3.json").write_text(json.dumps(
            {k: [infos[k]] for k in (*COMMONS_PEOPLE, *COMMONS_EMBLEMS)}, ensure_ascii=False, indent=1), encoding="utf-8")
    return failures


LIBRARY_PEOPLE: tuple[str, ...] = ("trump", "khamenei")          # v3 호르무즈 — 라이브러리 가공본
FLAG_EXTRA: tuple[str, ...] = ("eu",)                            # prep3 flags() extra 중 FLAG_CODES 밖


def build_flag_pngs(root: Path) -> int:
    """flag-icons SVG → PNG(1:1 256², 4:3 480×360, 07 §4). prep3 flags() 와 같은 변환."""
    import cairosvg  # noqa: PLC0415

    for c in FLAG_EXTRA:
        download(FLAG_URL.replace("{kind}", "1x1").replace("{c}", c), root / "assets" / "flags_svg" / f"{c}.svg")
        download(FLAG_URL.replace("{kind}", "4x3").replace("{c}", c), root / "assets" / "flags_svg" / f"{c}_4x3.svg")
    n = 0
    for f in sorted((root / "assets" / "flags_svg").glob("*.svg")):
        name = f.stem
        if name.endswith("_4x3"):
            cairosvg.svg2png(url=str(f), write_to=str(root / "assets" / "flags" / f"{name}.png"), output_width=480, output_height=360)
        else:
            cairosvg.svg2png(url=str(f), write_to=str(root / "assets" / "flags" / f"{name}_1x1.png"), output_width=256, output_height=256)
        n += 1
    return n


def cmd_people(root: Path, dry: bool) -> list[str]:
    """인물 초상·휘장·국기 PNG·권리 레지스트리 (v2.4.0 D-0029 작업 4·5 — tools/commons_fetch.py·portrait_fallback.py)."""
    if dry:
        return [f"people → portraits {list(LIBRARY_PEOPLE) + list(COMMONS_PEOPLE)}, emblems {list(COMMONS_EMBLEMS)}, "
                "flags PNG, rights_registry (+ assets/rights_bundles.yaml)"]
    from tools.commons_fetch import now_iso, record_bundles, record_rights  # noqa: PLC0415
    from tools.portrait_fallback import library_portrait, process  # noqa: PLC0415

    regp = root / "assets" / "rights_registry.json"
    pm = json.loads((REPO / "assets/library/workshop/references/photo_manifest.json").read_text(encoding="utf-8"))["people"]
    for pid in LIBRARY_PEOPLE:
        lib = library_portrait(pid, root / "assets" / "portraits" / f"{pid}.png")
        record_rights(regp, "people", pid, dict(src="repo_library", license=lib["source"]["license"],
                                               artist=re.sub("<[^>]+>", "", pm.get(pid, {}).get("artist", "")),
                                               url=lib["source"]["url"], rights_status="rights_clear",
                                               processing={"tool": "tools/portrait_fallback.py library",
                                                           "variant": lib["variant"]["path"]}))
    cand = json.loads((root / "data" / "commons_v3.json").read_text(encoding="utf-8"))
    for pid, title in COMMONS_PEOPLE.items():
        c = next(x for x in cand[pid] if x["title"] == title)
        photo = root / PREFETCH[pid][1]
        if not photo.exists():
            raise FetchError(f"원본 사진 없음: {photo} — 먼저 `fetch_data commons`")
        proc = process(photo, root / "assets" / "portraits" / f"{pid}.png", style="v3")
        record_rights(regp, "people", pid, dict(src="wikimedia_commons", license=c["lic"], artist=c["artist"], url=c["page"],
                                               title=title, rights_status="rights_clear", retrieved_at=now_iso(),
                                               processing=proc))
    for key, title in COMMONS_EMBLEMS.items():   # prep3: cand['centcom'] 의 NAVCENT 패치 → emblems/navcent.png
        c = next(x for x in cand[key] if x["title"] == title)
        if not (root / PREFETCH[key][1]).exists():
            raise FetchError(f"휘장 파일 없음: {PREFETCH[key][1]} — 먼저 `fetch_data commons`")
        record_rights(regp, "emblems", "navcent", dict(license=c["lic"], url=c["page"], title=title, restrictions=c["restr"],
                                                      rights_status="rights_clear", retrieved_at=now_iso()))
    print(f"flags {build_flag_pngs(root)}", flush=True)
    record_bundles(regp)   # 국기·음악·폰트·지도·내레이션 (assets/rights_bundles.yaml)
    return []


def cmd_media(root: Path, dry: bool) -> list[str]:
    """미디어 7종 — tools/media_fetch.py(레지스트리 정본, 원본 md5 대조, 14 §3 가공, 영상 검수 시트). v2.5.5 D32 sunset 2/2."""
    from tools import media_fetch  # noqa: PLC0415

    if dry:
        return ["media → tools/media_fetch.py (assets/media/media_registry.json)"]
    try:
        media_fetch.run(root)
    except media_fetch.MediaFetchError as e:
        return [f"media: {e}"]
    return []


def cmd_bgm(root: Path, dry: bool) -> list[str]:
    import hashlib

    BGM_NAME, BGM_SHA1 = _bgm_entry()  # noqa: N806
    dest = REPO / "assets" / "audio" / "bgm" / BGM_NAME
    if dry:
        return [f"bgm → {dest} (git {BGM_COMMIT}, sha1 {BGM_SHA1[:10]})"]
    if not dest.exists():
        has = subprocess.run(["git", "cat-file", "-e", f"{BGM_COMMIT}^{{commit}}"], capture_output=True, cwd=REPO)
        if has.returncode != 0:  # NB1: 얕은 클론이면 객체가 없다 — 조용히 넘기지 않는다(P6)
            raise FetchError(f"git 객체 {BGM_COMMIT} 없음(얕은 클론?). "
                             "`git fetch --unshallow origin overhaul/v2-map-engine` 후 다시 실행하십시오.")
        data = subprocess.run(["git", "show", f"{BGM_COMMIT}:assets/audio/bgm/{BGM_NAME}"],
                              capture_output=True, check=True, cwd=REPO).stdout
        dest.write_bytes(data)
    got = hashlib.sha1(dest.read_bytes()).hexdigest()
    if got != BGM_SHA1:
        return [f"bgm sha1 불일치: {got} != {BGM_SHA1}"]
    return []


COMMANDS = {"fonts": cmd_fonts, "ne": cmd_ne, "tiles": cmd_tiles, "flags": cmd_flags,
            "commons": cmd_commons, "people": cmd_people, "media": cmd_media, "bgm": cmd_bgm}
ALL = ("fonts", "ne", "tiles", "flags", "commons", "bgm")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", nargs="+", choices=[*COMMANDS, "all"])
    ap.add_argument("--dry-run", action="store_true", help="받을 대상만 출력")
    args = ap.parse_args(argv)
    root = v3_root()
    if not args.dry_run:
        ensure_dirs(root)
    steps = [s for w in args.what for s in (ALL if w == "all" else (w,))]
    failures: list[str] = []
    for step in steps:
        try:
            res = COMMANDS[step](root, args.dry_run)
        except (FetchError, subprocess.CalledProcessError) as e:
            res = [f"{step}: {e}"]
            if not args.dry_run:
                failures.extend(res)
            continue
        if args.dry_run:
            print("\n".join(res))
        else:
            failures.extend(res)
    if failures:
        print("FAILED:\n  " + "\n  ".join(failures), file=sys.stderr)
        return 1
    print(f"ok: {', '.join(steps)} → {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
