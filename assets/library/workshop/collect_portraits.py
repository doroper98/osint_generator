"""코어 인물 원본 사진 수집기 (Phase 2 — v1.1.0 라이브러리 구축).

Wikimedia Commons API 로 인물별 대표 사진의 **라이선스·저작자·출처를 먼저 조회**하고,
허용 라이선스인 것만 내려받는다. 권리 미확인 사진은 절대 저장하지 않는다 (C9 / G4-10).

사용::

    python assets/library/workshop/collect_portraits.py --dry-run   # 조회만
    python assets/library/workshop/collect_portraits.py             # 조회 + 다운로드
    python assets/library/workshop/collect_portraits.py --only trump powell

산출::

    references/photo_{person_id}.jpg          내려받은 원본
    references/photo_manifest.json            출처·라이선스·저작자 기계 기록

`person_id` 는 17 §0.8 규약 (로마자 lowercase snake).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REFS = HERE / "references"
MANIFEST = REFS / "photo_manifest.json"

UA = "osint_generator/1.1 (portrait collection for internal video production; contact: repo owner)"
API = "https://commons.wikimedia.org/w/api.php"

# 썸네일 폭 — Wikimedia 는 임의 폭을 거부할 수 있어 표준 폭을 쓴다 (HANDOFF 학습).
THUMB_WIDTH = 1280

#: 원본 최소 변 길이. 이보다 작으면 고대비 모노톤 가공 시 얼굴이 뭉개진다.
#: 실측 근거(2026-08-15 컨택트 시트 검수): warsh 176x201 은 식별만 겨우 되는 수준이었다.
MIN_DIMENSION = 600

#: 배포 가능한 라이선스만. 여기 없는 값이 나오면 사람이 판단할 때까지 보류한다.
#: KOGL Type 1 (공공누리 제1유형) = 출처표시 조건의 상업적 이용·변형 허용 → CC BY 동등.
#: 한국 정부·공공기관 사진 다수가 이 라이선스라 빼두면 국내 인물 커버리지가 크게 준다.
ALLOWED_LICENSE_PREFIXES = (
    "cc0", "cc-zero", "pd", "public domain",
    "cc-by-1.0", "cc-by-2.0", "cc-by-2.5", "cc-by-3.0", "cc-by-4.0",
    "cc-by-sa-1.0", "cc-by-sa-2.0", "cc-by-sa-2.5", "cc-by-sa-3.0", "cc-by-sa-4.0",
    "kogl type 1",
)

#: Commons 의 restrictions 태그 중 **저작권이 아니라 별도 법익**을 경고하는 값.
#: `personality`(초상권)는 AI 가공 인물을 영상에 싣는 본 용도에 직접 걸리므로
#: 자동 통과시키지 않고 사람 판단으로 넘긴다 (C9).
BLOCKING_RESTRICTIONS = ("personality", "trademarked", "communist", "insignia")

#: 코어 라인업 19인 (사용자 확정 2026-08-15 "19인 전부 O").
#: search = Commons 검색어. 후보 파일을 라이선스 순으로 골라 첫 통과본을 채택한다.
PEOPLE: list[dict[str, str]] = [
    # --- 확정 제안 8인 ---
    {"id": "trump",        "ko": "도널드 트럼프",   "en": "Donald Trump",      "search": "Donald Trump official portrait"},
    {"id": "xi_jinping",   "ko": "시진핑",         "en": "Xi Jinping",        "search": "Xi Jinping portrait"},
    {"id": "putin",        "ko": "블라디미르 푸틴", "en": "Vladimir Putin",    "search": "Vladimir Putin portrait"},
    {"id": "powell",       "ko": "제롬 파월",      "en": "Jerome Powell",     "search": "Jerome Powell official portrait"},
    {"id": "warsh",        "ko": "케빈 워시",      "en": "Kevin Warsh",       "search": "Kevin Warsh Federal Reserve Governor"},
    {"id": "musk",         "ko": "일론 머스크",    "en": "Elon Musk",         "search": "Elon Musk portrait"},
    {"id": "jensen_huang", "ko": "젠슨 황",        "en": "Jensen Huang",      "search": "Jensen Huang"},
    {"id": "chey_tae_won", "ko": "최태원",         "en": "Chey Tae-won",      "search": "Chey Tae-won"},
    # --- 후보 11인 (사용자가 전부 O) ---
    {"id": "zelensky",     "ko": "볼로디미르 젤렌스키", "en": "Volodymyr Zelenskyy", "search": "Volodymyr Zelenskyy portrait"},
    {"id": "kim_jong_un",  "ko": "김정은",         "en": "Kim Jong-un",       "search": "Kim Jong-un", "pin": "File:Kim Jong-un April 2019 (cropped).jpg"},
    {"id": "netanyahu",    "ko": "베냐민 네타냐후", "en": "Benjamin Netanyahu", "search": "Benjamin Netanyahu 2023 official"},
    {"id": "khamenei",     "ko": "알리 하메네이",  "en": "Ali Khamenei",      "search": "Ali Khamenei official"},
    {"id": "macron",       "ko": "에마뉘엘 마크롱", "en": "Emmanuel Macron",   "search": "Emmanuel Macron portrait"},
    {"id": "lagarde",      "ko": "크리스틴 라가르드", "en": "Christine Lagarde", "search": "Christine Lagarde portrait"},
    {"id": "rhee_chang_yong", "ko": "이창용",      "en": "Rhee Chang-yong",   "search": "Rhee Chang-yong", "pin": "File:이창용교수.jpg"},
    {"id": "bezos",        "ko": "제프 베이조스",  "en": "Jeff Bezos",        "search": "Jeff Bezos"},
    {"id": "lee_jae_yong", "ko": "이재용",         "en": "Lee Jae-yong",      "search": "Lee Jae-yong", "pin": "File:Lee Jae-yong in 2016.jpg"},
    {"id": "altman",       "ko": "샘 올트먼",      "en": "Sam Altman",        "search": "Sam Altman"},
    {"id": "zuckerberg",   "ko": "마크 저커버그",  "en": "Mark Zuckerberg",   "search": "Mark Zuckerberg", "pin": "File:Mark Zuckerberg F8 2018 Keynote (cropped).jpg"},
    {"id": "tim_cook",     "ko": "팀 쿡",          "en": "Tim Cook",          "search": "Tim Cook"},
    # --- 온디맨드 (실번들 analysis_20260814_150031 이 지목한 7인, §3.0.1) ---
    # 코어 20인의 적중률이 0% 였던 번들. 학자·이론가 계열이라 사전 구축 대상이 아니었다.
    {"id": "daron_acemoglu",   "ko": "대런 애쓰모글루", "en": "Daron Acemoglu",   "search": "Daron Acemoglu"},
    {"id": "michael_sandel",   "ko": "마이클 샌델",    "en": "Michael Sandel",   "search": "Michael Sandel"},
    {"id": "peter_thiel",      "ko": "피터 틸",       "en": "Peter Thiel",      "search": "Peter Thiel"},
    {"id": "dario_amodei",     "ko": "다리오 아모데이", "en": "Dario Amodei",     "search": "Dario Amodei"},
    {"id": "audrey_tang",      "ko": "오드리 탕",     "en": "Audrey Tang",      "search": "Audrey Tang"},
    {"id": "curtis_yarvin",    "ko": "커티스 야빈",    "en": "Curtis Yarvin",    "search": "Curtis Yarvin"},
    {"id": "helene_landemore", "ko": "Hélène Landemore", "en": "Helene Landemore", "search": "Helene Landemore"},
]


# --- 레이트 리밋 -----------------------------------------------------------
# Wikimedia 는 익명 클라이언트의 연속 호출에 429 를 낸다 (실측 2026-08-15: 0.15s
# 간격으로 18인 연속 조회 시 3인째부터 전부 429). 호출 간 최소 간격을 강제하고
# 429/503 에는 Retry-After 를 존중하는 지수 백오프로 재시도한다.
MIN_INTERVAL_SEC = 1.2
MAX_RETRIES = 4
_last_call: list[float] = [0.0]


def _throttle() -> None:
    elapsed = time.monotonic() - _last_call[0]
    if elapsed < MIN_INTERVAL_SEC:
        time.sleep(MIN_INTERVAL_SEC - elapsed)
    _last_call[0] = time.monotonic()


def _get(params: dict) -> dict:
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
    delay = 2.0
    for attempt in range(MAX_RETRIES + 1):
        _throttle()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == MAX_RETRIES:
                raise
            wait = delay
            if (ra := e.headers.get("Retry-After")):
                try:
                    wait = max(wait, float(ra))
                except ValueError:
                    pass
            print(f"      (HTTP {e.code} — {wait:.0f}s 대기 후 재시도 {attempt + 1}/{MAX_RETRIES})")
            time.sleep(wait)
            delay *= 2
    raise RuntimeError("unreachable")


def search_files(query: str, limit: int = 12) -> list[str]:
    """Commons 에서 이미지 파일명 후보를 검색한다."""
    data = _get({
        "action": "query", "list": "search", "srsearch": f"{query} filetype:bitmap",
        "srnamespace": "6", "srlimit": str(limit),
    })
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def file_info(title: str) -> dict | None:
    """파일 1개의 라이선스·저작자·출처·썸네일 URL 을 조회한다."""
    data = _get({
        "action": "query", "titles": title, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime",
        "iiurlwidth": str(THUMB_WIDTH),
    })
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info = (page.get("imageinfo") or [None])[0]
        if not info:
            continue
        meta = info.get("extmetadata") or {}

        def m(key: str) -> str:
            return str((meta.get(key) or {}).get("value", "")).strip()

        return {
            "title": title,
            "license_short": m("LicenseShortName"),
            "license_code": m("License").lower(),
            "artist_html": m("Artist"),
            "credit_html": m("Credit"),
            "usage_terms": m("UsageTerms"),
            "restrictions": m("Restrictions"),
            "descriptionurl": info.get("descriptionurl", ""),
            "thumb_url": info.get("thumburl") or info.get("url", ""),
            "width": info.get("width"), "height": info.get("height"),
            "mime": info.get("mime", ""),
        }
    return None


def strip_html(text: str) -> str:
    out, depth = [], 0
    for ch in text:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return " ".join("".join(out).split())


def is_allowed(info: dict) -> bool:
    code = (info.get("license_code") or "").lower()
    short = (info.get("license_short") or "").lower()
    if info.get("restrictions"):
        return False
    return any(code.startswith(p) or short.startswith(p) for p in ALLOWED_LICENSE_PREFIXES)


def is_big_enough(info: dict) -> bool:
    w, h = info.get("width") or 0, info.get("height") or 0
    return min(w, h) >= MIN_DIMENSION


def pick_for(person: dict) -> dict | None:
    """한 인물의 후보들을 훑어 허용 라이선스 + 충분한 해상도의 첫 통과본을 고른다.

    `person["pin"]` 이 있으면 검색 대신 그 Commons 파일을 직접 쓴다 — 검색으로는
    엉뚱한 사진이 1등으로 올라오는 인물(분장 배우·동명이인 등)을 사람이 고정하기
    위한 장치.
    """
    if person.get("pin"):
        info = file_info(person["pin"])
        if not info:
            print(f"    !! pin 조회 실패: {person['pin']}")
            return None
        # pin 은 **해상도 하한을 면제**한다 — 사람이 "이 사람이 맞다"를 보고 고른 것이라
        # 자동 필터의 크기 휴리스틱보다 우선한다. 큰 사진일수록 단체·행사 컷일 확률이
        # 높아 오히려 개인 초상이 밀려나는 문제가 실측됐다 (2026-08-15 검수).
        # 다만 **라이선스·restrictions 는 면제하지 않는다** — 권리는 협상 대상이 아니다.
        ok = is_allowed(info)
        note = "" if is_big_enough(info) else "  (해상도 하한 미달 — pin 으로 수용)"
        print(f"    {'OK ' if ok else 'SKIP'} (pin) {info['license_short']} "
              f"{info['width']}x{info['height']} {person['pin'][:46]}{note}")
        return info if ok else None

    for title in search_files(person["search"]):
        try:
            info = file_info(title)
        except Exception as e:  # noqa: BLE001 — 개별 실패는 다음 후보로
            print(f"    ! {title}: {type(e).__name__}")
            continue
        if not info or not info.get("thumb_url"):
            continue
        if not (info.get("mime") or "").startswith("image/"):
            continue
        lic_ok, size_ok = is_allowed(info), is_big_enough(info)
        if lic_ok and size_ok:
            status = "OK "
        elif not lic_ok:
            status = "SKIP"
        else:
            status = "SMALL"
        print(f"    {status:5} {info['license_short'] or info['license_code'] or '?':16} "
              f"{info['width']}x{info['height']:<6} {title[:48]}")
        if lic_ok and size_ok:
            return info
    return None


def download(url: str, dest: pathlib.Path) -> int:
    """썸네일 다운로드. API 와 같은 스로틀·백오프를 탄다.

    v1.1 실측: 이 경로가 `_get` 의 스로틀을 안 타서 upload.wikimedia.org 에서
    429 가 났다 (19인 중 4인 실패). 미디어 호스트도 같은 레이트 정책을 쓴다.
    """
    delay = 2.0
    for attempt in range(MAX_RETRIES + 1):
        _throttle()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            dest.write_bytes(data)
            return len(data)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == MAX_RETRIES:
                raise
            wait = delay
            if (ra := e.headers.get("Retry-After")):
                try:
                    wait = max(wait, float(ra))
                except ValueError:
                    pass
            print(f"      (다운로드 HTTP {e.code} — {wait:.0f}s 대기 후 재시도 "
                  f"{attempt + 1}/{MAX_RETRIES})")
            time.sleep(wait)
            delay *= 2
    raise RuntimeError("unreachable")


def adopt(args) -> int:
    """사용자가 직접 준 사진을 권리 기록과 함께 등록한다.

    Commons 에 쓸 만한 자유 라이선스 사진이 없거나(이재용), restrictions 로 자동
    차단된 인물(김정은)을 사람 판단으로 통과시키는 경로. **출처·라이선스 없이는
    등록하지 않는다** (C9) — 파일만 받고 권리를 비워두면 나중에 추적이 불가능해진다.
    """
    src = pathlib.Path(args.file).expanduser()
    if not src.is_file():
        print(f"error: 파일 없음 — {src}")
        return 1

    known = {p["id"] for p in PEOPLE}
    if args.adopt not in known:
        print(f"error: 알 수 없는 person_id {args.adopt!r}. 가능: {sorted(known)}")
        return 1

    try:
        from PIL import Image

        with Image.open(src) as im:
            w, h = im.size
            fmt = im.format
    except Exception as e:  # noqa: BLE001
        print(f"error: 이미지로 열 수 없음 — {type(e).__name__}: {e}")
        return 1

    if min(w, h) < MIN_DIMENSION:
        print(f"  ! 경고: {w}x{h} — 권장 최소 변 {MIN_DIMENSION}px 미만. "
              f"고대비 모노톤 가공 시 얼굴이 뭉개질 수 있습니다.")

    person = next(p for p in PEOPLE if p["id"] == args.adopt)
    REFS.mkdir(parents=True, exist_ok=True)
    dest = REFS / f"photo_{args.adopt}.jpg"
    dest.write_bytes(src.read_bytes())

    records: dict[str, dict] = {}
    extra: dict = {}
    if MANIFEST.exists():
        loaded = json.loads(MANIFEST.read_text(encoding="utf-8"))
        records = loaded.get("people", {})
        extra = {k: v for k, v in loaded.items() if k != "people"}

    records[args.adopt] = {
        "person_id": args.adopt,
        "name_ko": person["ko"],
        "name_en": person["en"],
        "commons_title": "",
        "license": args.license,
        "usage_terms": args.license,
        "artist": args.artist,
        "credit": args.credit or args.artist,
        "source_page": args.source,
        "image_url": "",
        "original_size": [w, h],
        "local_file": dest.name,
        "adopted_by_user": True,
        "adopt_note": args.note,
    }
    extra.get("pending_manual", {}).pop(args.adopt, None)

    MANIFEST.write_text(
        json.dumps({**extra, "people": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[adopt] {dest.name}  {w}x{h} {fmt}  |  {args.license}")
    print(f"        출처: {args.source}")
    print(f"        저작자: {args.artist}")
    print(f"[manifest] {MANIFEST}  ({len(records)}인)")
    sync_rights_md()   # codex 가 읽는 RIGHTS.md 와 즉시 동기화 (갈라짐 방지)
    print("\n다음: python assets/library/workshop/make_contact_sheet.py 로 육안 재검수")
    return 0


RIGHTS_MD = REFS / "RIGHTS.md"
RIGHTS_BEGIN = "<!-- BEGIN photo_manifest 자동 생성 — 직접 수정 금지 -->"
RIGHTS_END = "<!-- END photo_manifest 자동 생성 -->"


def sync_rights_md() -> int:
    """`photo_manifest.json` 을 `RIGHTS.md` 의 표로 렌더한다.

    권리 기록이 두 곳에 따로 있으면 갈라진다 — 실제로 codex 가
    "photo_helene_landemore.jpg 는 있는데 RIGHTS.md 에 항목이 없다"며 작업을
    거부했다 (2026-08-15). 공방 규칙(AGENTS.md §6)과 codex 는 RIGHTS.md 를 보고,
    우리 도구는 manifest 에 쓴다.

    → **manifest 가 정본**, RIGHTS.md 의 해당 구간은 그 렌더 결과로 둔다.
    """
    if not MANIFEST.exists():
        print(f"error: {MANIFEST} 없음")
        return 1
    people = json.loads(MANIFEST.read_text(encoding="utf-8"))["people"]

    rows = [
        "| 파일 | 인물 | 출처 | 라이선스 | 저작자 | 비고 |",
        "|---|---|---|---|---|---|",
    ]
    for pid, r in sorted(people.items()):
        note = "사용자 제공" if r.get("adopted_by_user") else "자동 수집"
        if r.get("adopt_note"):
            note += f" — {r['adopt_note']}"
        src = r.get("source_page") or r.get("commons_title") or "-"
        rows.append(
            f"| `{r.get('local_file','')}` | {r.get('name_ko','')} | {src} | "
            f"{r.get('license','')} | {r.get('artist') or '-'} | {note} |"
        )

    block = "\n".join([
        RIGHTS_BEGIN,
        "",
        f"**{len(people)}인** — 정본은 `photo_manifest.json` 이며 본 표는 그 렌더 결과다.",
        "갱신: `python collect_portraits.py --sync-rights`",
        "",
        *rows,
        "",
        RIGHTS_END,
    ])

    text = RIGHTS_MD.read_text(encoding="utf-8") if RIGHTS_MD.exists() else ""
    if RIGHTS_BEGIN in text and RIGHTS_END in text:
        head, rest = text.split(RIGHTS_BEGIN, 1)
        _, tail = rest.split(RIGHTS_END, 1)
        text = head + block + tail
    else:
        text = text.rstrip() + "\n\n## 인물 원본 사진 — 자동 생성 표\n\n" + block + "\n"

    RIGHTS_MD.write_text(text, encoding="utf-8")
    print(f"[sync] {RIGHTS_MD}  ({len(people)}인)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sync-rights", action="store_true",
                    help="photo_manifest.json 을 RIGHTS.md 표로 렌더 (codex 가 읽는 파일)")
    ap.add_argument("--dry-run", action="store_true", help="조회만 하고 내려받지 않음")
    ap.add_argument("--only", nargs="*", help="특정 person_id 만")
    ap.add_argument("--adopt", metavar="PERSON_ID",
                    help="사용자 제공 사진을 등록 (Commons 검색 대신)")
    ap.add_argument("--file", help="--adopt 용 이미지 경로")
    ap.add_argument("--source", default="", help="--adopt 용 출처 URL 또는 설명 (필수)")
    ap.add_argument("--license", default="", help="--adopt 용 라이선스 표기 (필수)")
    ap.add_argument("--artist", default="", help="--adopt 용 저작자/촬영자")
    ap.add_argument("--credit", default="", help="--adopt 용 크레딧 표기 (생략 시 artist)")
    ap.add_argument("--note", default="", help="--adopt 용 사용자 판단 메모 (초상권 등)")
    args = ap.parse_args()

    if args.sync_rights:
        return sync_rights_md()

    if args.adopt:
        missing = [n for n in ("file", "source", "license") if not getattr(args, n)]
        if missing:
            print(f"error: --adopt 에는 {', '.join('--' + m for m in missing)} 가 필요합니다.\n"
                  f"       권리 기록 없는 사진은 등록하지 않습니다 (C9).")
            return 1
        return adopt(args)

    targets = PEOPLE
    if args.only:
        want = set(args.only)
        targets = [p for p in PEOPLE if p["id"] in want]
        if not targets:
            print(f"error: 일치하는 person_id 없음. 가능한 값: {[p['id'] for p in PEOPLE]}")
            return 1

    REFS.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict] = {}
    if MANIFEST.exists():
        records = json.loads(MANIFEST.read_text(encoding="utf-8")).get("people", {})

    ok, failed = 0, []
    for person in targets:
        print(f"\n[{person['id']}] {person['ko']} ({person['en']})")
        try:
            info = pick_for(person)
        except Exception as e:  # noqa: BLE001
            print(f"  !! 검색 실패: {type(e).__name__}: {e}")
            failed.append(person["id"])
            continue

        if not info:
            print("  !! 허용 라이선스 후보를 못 찾음 — 수동 수집 필요")
            failed.append(person["id"])
            continue

        rec = {
            "person_id": person["id"],
            "name_ko": person["ko"],
            "name_en": person["en"],
            "commons_title": info["title"],
            "license": info["license_short"] or info["license_code"],
            "usage_terms": strip_html(info["usage_terms"]),
            "artist": strip_html(info["artist_html"]),
            "credit": strip_html(info["credit_html"]),
            "source_page": info["descriptionurl"],
            "image_url": info["thumb_url"],
            "original_size": [info.get("width"), info.get("height")],
            "local_file": f"photo_{person['id']}.jpg",
        }

        if args.dry_run:
            print(f"  -> (dry-run) {rec['license']} | {rec['artist'][:50]}")
        else:
            dest = REFS / rec["local_file"]
            try:
                n = download(info["thumb_url"], dest)
            except Exception as e:  # noqa: BLE001
                print(f"  !! 다운로드 실패: {type(e).__name__}: {e}")
                failed.append(person["id"])
                continue
            print(f"  -> {dest.name} ({n:,} bytes) | {rec['license']}")
        records[person["id"]] = rec
        ok += 1

    if not args.dry_run:
        MANIFEST.write_text(
            json.dumps(
                {"schema_note": "workshop 수집 원본 권리 기록 (C9/G4-10)", "people": records},
                ensure_ascii=False, indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"\n[manifest] {MANIFEST}")
        sync_rights_md()   # 자동 수집 후에도 RIGHTS.md 동기화

    print(f"\n성공 {ok} / 실패 {len(failed)}")
    if failed:
        print(f"수동 수집 필요: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
