"""Phase 1 골든 재현 데이터 수집기 (v2.0.1, back_and_forth D-0002 작업 2).

`legacy_v3/*.py`가 기대하는 입력을 `V3_ROOT`(기본 `projects/hormuz_korea_legacy`, gitignore) 아래에 만든다.
출처·수치는 docs/handoff/19a §B·§H, 07 §3.2, 14 §10.4, reference_code/v3_hormuz_korea/media3b_round2.md 를 따른다.

사용법:
    python tools/fetch_data.py fonts | ne | tiles | flags | commons | media | all [--dry-run]

- fonts   : IBM Plex Sans KR 4종·IBM Plex Mono 2종·GmarketSans 2종(woff→otf) → assets/fonts/.cache → 사용자 폰트 폴더 설치 (D3)
- ne      : Natural Earth 10m admin0·admin1·populated places GeoJSON → V3_ROOT/data
- tiles   : terrarium 지형 타일 W z5 / G z7 / K z7 → V3_ROOT/data/{t5,tg,tk}/{x}_{y}.png
- flags   : flag-icons SVG 13개국(1x1·4x3) → V3_ROOT/assets/flags_svg (PNG 변환은 prep3 flags)
- commons : Commons 메타데이터 → V3_ROOT/data/commons_v3.json, media_candidates.json (인물 2·휘장 1·미디어 5)
- media   : legacy_v3/media3.py 실행(1차) → 2차 처리(rok_iraq 사진, niovi·strikes 5초 클립 npy) → media_registry 병합
- bgm     : 배경음악 mp3 를 git 객체(bd37b58)에서 복원 + sha1 대조 (네트워크 불필요, DECISIONS D22)
- all     : fonts ne tiles flags commons bgm (media 는 prep3 people 뒤에 따로 — 런북 순서)

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
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "osint-video-trial/0.4 (research; https://github.com/doroper98/osint_generator)"}
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_GAP_SEC = 15.0          # 14 §10.4 — 요청 간격
COMMONS_429_WAIT = (60.0, 90.0)  # 429 시 대기 범위

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
# media_candidates.json — media3.py pick() 키와 부분 문자열 (reference media_registry.json 기준)
MEDIA_TITLES: dict[str, str] = {
    "hormuz_navy": "File:Strait Of Hormuz Transit 230508-N-NH257-1076.jpg",
    "p8": "File:P-8A Poseidon Executes Training Flight (9341123).jpg",
    "hormuz_video": "File:U S Forces Complete New Round of Retaliatory Strikes Against Iran (1013909).webm",
    "zaytun": "File:Southkoreansoldiersiraq.jpg",
    "niovi": "File:Oil tanker Niovi seized by Iran's Islamic Revolutionary Guard Corps Navy.webm",
}
# media3b_round2.md — 클립 구간 (사람 식별 없음 확인된 구간)
CLIP_SEGMENTS: dict[str, tuple[str, float, float]] = {
    "strikes": ("strikes.webm", 1.5, 5.0),
    "niovi": ("niovi.webm", 28.0, 5.0),
}
# D22 — BGM 은 추적 해제됐고 git 객체에서 복원한다. sha1 은 assets/audio/bgm/RIGHTS.md 에 기록.
BGM_NAME = "The Life and Death of a Certain K. Zabriskie, Patriarch - Chris Zabriskie.mp3"
BGM_COMMIT = "bd37b58"
BGM_SHA1 = "c0ddb7b38ee7866c32d2510a84125cf611a54e93"
CLIP_SIZE = (480, 270)
CLIP_FPS = 24


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
def http_get(url: str, timeout: float = 120.0, tries: int = 4) -> bytes:
    last: Exception | None = None
    for a in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:
                break
            time.sleep(2 ** (a + 1))
        except Exception as e:  # noqa: BLE001 — 재시도 후 FetchError 로 올린다
            last = e
            time.sleep(2 ** (a + 1))
    raise FetchError(f"{url}: {last}")


def download(url: str, dest: Path) -> bool:
    """이미 있으면 건너뛴다(캐시). 받았으면 True."""
    if dest.exists() and dest.stat().st_size > 100:
        return False
    data = http_get(url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True


_last_commons = 0.0


def commons_call(params: dict[str, str]) -> dict:
    """Commons API 1회. 요청 간격 15초, 429 는 60~90초 대기 후 재시도(최대 6회)."""
    global _last_commons
    url = COMMONS_API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    for a in range(6):
        wait = COMMONS_GAP_SEC - (time.time() - _last_commons)
        if wait > 0:
            time.sleep(wait)
        _last_commons = time.time()
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                w = COMMONS_429_WAIT[0] + (COMMONS_429_WAIT[1] - COMMONS_429_WAIT[0]) * (a / 5)
                print(f"commons 429 — {w:.0f}s 대기", flush=True)
                time.sleep(w)
                continue
            raise FetchError(f"commons {e.code}: {params.get('titles')}") from e
    raise FetchError(f"commons 429 지속: {params.get('titles')}")


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


def cmd_commons(root: Path, dry: bool) -> list[str]:
    if dry:
        return [f"commons → commons_v3.json {list(COMMONS_PEOPLE) + list(COMMONS_EMBLEMS)}, media_candidates.json {list(MEDIA_TITLES)}"]
    cv = root / "data" / "commons_v3.json"
    if not cv.exists():
        data: dict[str, list[dict]] = {}
        for key, title in {**COMMONS_PEOPLE, **COMMONS_EMBLEMS}.items():
            data[key] = [commons_info(title)]
            print(f"commons {key}: {data[key][0]['lic']}", flush=True)
        cv.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    mc = root / "data" / "media_candidates.json"
    if not mc.exists():
        media: dict[str, list[dict]] = {}
        for key, title in MEDIA_TITLES.items():
            media[key] = [commons_info(title)]
            print(f"media {key}: {media[key][0]['lic']}", flush=True)
        mc.write_text(json.dumps(media, ensure_ascii=False, indent=1), encoding="utf-8")
    return []


def _clip_to_npy(src: Path, start: float, dur: float, dest: Path) -> None:
    import numpy as np

    w, h = CLIP_SIZE
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{start}", "-t", f"{dur}", "-i", str(src),
         "-vf", f"scale={w}:{h},fps={CLIP_FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True,
    ).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    np.save(dest, arr)


def cmd_media(root: Path, dry: bool) -> list[str]:
    """media3.py(1차) → media3b_round2.md(2차)를 코드로. 레지스트리 값은 reference media_registry.json 을 따른다."""
    if dry:
        return ["media → legacy_v3/media3.py, rok_iraq_720.jpg, niovi.webm, strikes_480.npy, niovi_480.npy, media_registry 병합"]
    env = {**os.environ, "V3_ROOT": str(root)}
    subprocess.run([sys.executable, str(REPO / "legacy_v3" / "media3.py")], check=True, env=env, cwd=REPO)
    from PIL import Image, ImageEnhance

    cand = json.loads((root / "data" / "media_candidates.json").read_text(encoding="utf-8"))
    media = root / "media"
    # 2차 ① rok_iraq 사진: 1600 썸네일 → 720×450 커버 크롭 → 채도 0.82·대비 1.06 → q92
    src = media / "rok_iraq.jpg"
    if not src.exists():
        info = commons_info(cand["zaytun"][0]["title"], width=1600)
        src.write_bytes(http_get(info["thumburl"] or info["url"]))
    im = Image.open(src).convert("RGB")
    w, h = im.size
    tw, th = 720, 450
    s = max(tw / w, th / h)
    im = im.resize((int(w * s) + 1, int(h * s) + 1), Image.LANCZOS)
    x0, y0 = (im.width - tw) // 2, (im.height - th) // 2
    im = im.crop((x0, y0, x0 + tw, y0 + th))
    im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(0.82)).enhance(1.06)
    im.save(media / "rok_iraq_720.jpg", quality=92)
    # 2차 ② niovi 원본 영상
    niovi = media / "niovi.webm"
    if not niovi.exists():
        niovi.write_bytes(http_get(cand["niovi"][0]["url"], timeout=300))
    # 2차 ③ 5초 클립 → 480×270@24 rgb24 npy
    for key, (fname, start, dur) in CLIP_SEGMENTS.items():
        _clip_to_npy(media / fname, start, dur, media / f"{key}_480.npy")
    # 레지스트리 병합 — media3 는 3건만 쓴다. rok_iraq·niovi 는 reference 기록 그대로(저작자 정제 포함)
    ref = json.loads((REPO / "docs/handoff/reference_code/v3_hormuz_korea/media_registry.json").read_text(encoding="utf-8"))
    regp = media / "media_registry.json"
    reg = json.loads(regp.read_text(encoding="utf-8"))
    for key in ("rok_iraq", "niovi"):
        reg[key] = ref[key]
    regp.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return []


def cmd_bgm(root: Path, dry: bool) -> list[str]:
    import hashlib

    dest = REPO / "assets" / "audio" / "bgm" / BGM_NAME
    if dry:
        return [f"bgm → {dest} (git {BGM_COMMIT}, sha1 {BGM_SHA1[:10]})"]
    if not dest.exists():
        data = subprocess.run(["git", "show", f"{BGM_COMMIT}:assets/audio/bgm/{BGM_NAME}"],
                              capture_output=True, check=True, cwd=REPO).stdout
        dest.write_bytes(data)
    got = hashlib.sha1(dest.read_bytes()).hexdigest()
    if got != BGM_SHA1:
        return [f"bgm sha1 불일치: {got} != {BGM_SHA1}"]
    return []


COMMANDS = {"fonts": cmd_fonts, "ne": cmd_ne, "tiles": cmd_tiles, "flags": cmd_flags,
            "commons": cmd_commons, "media": cmd_media, "bgm": cmd_bgm}
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
