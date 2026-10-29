"""미디어 수집·가공기 (v2.5.5, back_and_forth D-0036 작업 4·5, 14 §2·§3·§10.3·§10.4, 07 §3.2).

    python tools/media_fetch.py <project_dir> [--only mid,mid] [--sheets]
    python tools/media_fetch.py search "P-8A Poseidon" [--limit 7]      # 후보 검색(라이선스·제한 표시) — 고르는 것은 사람
    python tools/media_fetch.py search "Pakistan army Saudi" --log projects/<pid> --sid war_0   # 풀 순서(rules media_beats.sources_order) + 기록

레지스트리(`assets/media/media_registry.json`)가 정본이다. 이 도구는 레지스트리 항목마다
  1. 원본 받기 — Commons 표준 폭 썸네일(`tool.params.thumb_w`) 또는 원본(영상). HTTP 층은 tools/commons_fetch 하나
     (요청 간격·429 지수 대기·시도 상한 = config.yaml commons, NB4). 라이선스·Restrictions 필터(07 §3.2).
  2. 검증 — 이미지 `PIL verify`, 영상 ffprobe 길이. 원본 md5 = 레지스트리 `source_hash`(다르면 원본이 바뀐 것 → 오류).
  3. 가공(14 §3) — 사진: 커버 크롭·채도·대비 / 컷아웃: rembg·알파 bbox·폭 / 영상: segment → 480×270@24 npy.
     원본 의미를 바꾸는 보정(합성·삭제)은 없다. 파라미터는 레지스트리 `tool.params` 에서만 읽는다.
  4. 영상 검수 시트 — 전체 길이에서 12장(시각 표시), 사람이 구간을 고른다(14 §10.3-3).
를 한다. 실패는 모아서 마지막에 **남은 항목 + 재실행 명령**과 함께 오류로 낸다(조용히 넘기지 않는다, 15 P6).
기사(kind article)는 받을 파일이 없다(우리 타이포 조판, 14 §9).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

REPO = Path(__file__).resolve().parent.parent
INSET_LIBRARY = REPO / "assets" / "library" / "insets"   # v7.3.0 — 위성 인셋 공용 보관본(정사각 원본 png, 권리 = 미디어 레지스트리)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from engine.media_registry import load_media_registry  # noqa: E402
from schemas.media_models import MediaAsset, SourceVariant  # noqa: E402
from tools import commons_fetch  # noqa: E402

SHEET_N = 12                     # 14 §10.3-3
SHEET_TILE = (320, 180)
SHEET_COLS = 4


class MediaFetchError(RuntimeError):
    pass


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def probe_duration(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out or 0)


# ------------------------------------------------------------------ 1. 받기
FLICKR_PAGE_RE = re.compile(r"^https://www\.flickr\.com/photos/[^/]+/(\d+)/?$")


def flickr_license(page: str, pid: str) -> str:
    """사진 페이지 HTML → 그 사진의 Flickr license 번호(문자열). 못 찾으면 MediaFetchError(가정하지 않는다, C9)."""
    m = re.search(r'"license":(\d+),"sizes":\{"data":\{"sq":\{"data":\{"displayUrl":"[^"]*?/' + pid + "_", page)
    if not m:
        raise MediaFetchError(f"Flickr {pid}: 사진 페이지에서 라이선스를 찾지 못했다 — 받지 않는다")
    return m.group(1)


def fetch_flickr(a: MediaAsset, dest: Path) -> None:
    """v4.4.0 D-0090 작업 4 — 기관 공식 Flickr 사진. 페이지의 license 번호가 rules media.flickr.licenses_allowed 안이고
    그 이름이 레지스트리 license 와 같을 때만 받는다(권리 불확실 = 받지 않음, 20 §8)."""
    import requests  # noqa: PLC0415

    from rules import load_rules  # noqa: PLC0415

    fr = load_rules().media.flickr
    m = FLICKR_PAGE_RE.match(a.url or "")
    if fr is None or m is None:
        raise MediaFetchError(f"Flickr 사진 페이지 URL 이 아니다: {a.url}")
    pid = m.group(1)
    page = requests.get(a.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60).text
    lic = flickr_license(page, pid)
    if lic not in fr.licenses_allowed or fr.licenses_allowed[lic] != a.license:
        raise MediaFetchError(f"Flickr {pid}: 라이선스 {lic}({fr.licenses_allowed.get(lic, '허용 목록 밖')}) ≠ 레지스트리 {a.license!r}")
    u = re.search(r"live\.staticflickr\.com/\d+/" + pid + r"_[0-9a-f]+_" + fr.size_suffix + r"\.jpg", page)
    if not u:
        raise MediaFetchError(f"Flickr {pid}: 크기 {fr.size_suffix} 파일 URL 없음")
    r = requests.get("https://" + u.group(0), timeout=120)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)


def fetch_source(a: MediaAsset, media: Path, restore_from: Path | None = None, tries: int | None = None) -> Path:
    """원본 확보. 순서: 이미 있음 → `restore_from`(artifacts 보존본, v3.0.0 D-0044 B) → Commons.
    보존본도 호출자가 레지스트리 source_hash 로 대조한다(바뀐 원본을 조용히 쓰지 않는다)."""
    prm = a.tool.params
    dest = media / str(prm["source"])
    if dest.exists() and dest.stat().st_size > 100:
        return dest
    if restore_from is not None and (restore_from / str(prm["source"])).exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((restore_from / str(prm["source"])).read_bytes())
        print(f"restore {a.title} ← {restore_from}", flush=True)
        return dest
    if a.kind == "inset":   # v7.3.0 D-0206 — 위성 인셋: 공용 보관본(assets/library/insets) → 없으면 기록된 요청 URL(NASA GIBS WMS)
        lib = INSET_LIBRARY / str(prm["source"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        if lib.exists():
            dest.write_bytes(lib.read_bytes())
            print(f"library {a.title} ← {lib.relative_to(REPO)}", flush=True)
        else:
            dest.write_bytes(commons_fetch.http_get(str(prm["request_url"])))
        return dest
    if a.url and FLICKR_PAGE_RE.match(a.url):   # v4.4.0 — 기관 공식 Flickr(Commons 가 아님)
        fetch_flickr(a, dest)
        return dest
    if a.kind == "video" and prm.get("fetch") == "yt-dlp":   # v7.4.0 — Commons 밖 1차 출처 영상(연준·C-SPAN 등), config media.video_fetch
        return fetch_video(str(prm["url"]), dest)
    kw = {} if tries is None else {"tries": tries}
    ii = commons_fetch.info(a.title, prm.get("thumb_w"))   # 표준 폭만(07 §3.2)
    if not commons_fetch.license_allowed(ii["lic"]) or ii["restrictions"]:
        raise MediaFetchError(f"라이선스·제한 불허 {ii['lic']!r} {ii['restrictions']}: {a.title}")
    if a.kind == "video":
        data = commons_fetch.http_get(ii["url"], timeout=300, **kw)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    else:
        commons_fetch.download(ii, dest)
    return dest


def video_fetch_command(url: str, dest: Path) -> list[str]:
    """yt-dlp 명령(v7.4.0 UF-141 준비). 허용 도메인·고정 버전 검사 뒤 만든다. 형식·해상도는 config media.video_fetch.
    쿠키·클라이언트 위장·추출기 인자 같은 봇 검사 우회 옵션은 넣지 않는다 — 막히면 그대로 실패한다."""
    from urllib.parse import urlparse  # noqa: PLC0415

    from orchestrator.config import load_config  # noqa: PLC0415

    vf = load_config().media.video_fetch
    if vf is None:
        raise MediaFetchError("config media.video_fetch 없음 — 영상 받기 설정(허용 도메인·해상도·yt-dlp 버전)을 먼저")
    host = (urlparse(url).hostname or "").lower()
    if not any(host == d or host.endswith("." + d) for d in vf.allowed_domains):
        raise MediaFetchError(f"허용 도메인 밖 영상 주소: {host} — config media.video_fetch.allowed_domains {vf.allowed_domains}")
    try:
        got = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as ex:
        raise MediaFetchError(f"yt-dlp 실행 불가: {ex}") from ex
    if got != vf.yt_dlp_version:
        raise MediaFetchError(f"yt-dlp 버전 {got} ≠ 고정 {vf.yt_dlp_version} — `pip install yt-dlp=={vf.yt_dlp_version}`")
    fmt = vf.format.replace("{h}", str(vf.max_height))
    return ["yt-dlp", "--no-playlist", "--no-progress", "-f", fmt, "--merge-output-format", "mp4", "-o", str(dest), url]


def fetch_video(url: str, dest: Path) -> Path:
    """1차 출처 영상 원본 받기(yt-dlp). 실패하면 오류(조용한 대체 없음, 15 P6)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(video_fetch_command(url, dest), capture_output=True, text=True)
    if r.returncode != 0 or not dest.exists():
        raise MediaFetchError(f"영상 받기 실패 {url}: {(r.stderr or r.stdout)[-800:]}")
    return dest


# ------------------------------------------------------------------ 2·3. 검증·가공
def process_photo(src: Path, out: Path, prm: dict) -> None:
    tw, th = prm["crop"]
    im = Image.open(src).convert("RGB")
    w, h = im.size
    s = max(tw / w, th / h)
    im = im.resize((int(w * s) + 1, int(h * s) + 1), Image.LANCZOS)
    x0, y0 = (im.width - tw) // 2, (im.height - th) // 2
    im = im.crop((x0, y0, x0 + tw, y0 + th))
    im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(prm["color"])).enhance(prm["contrast"])
    im.save(out, quality=prm["jpeg_quality"])


def process_cutout(src: Path, out: Path, prm: dict) -> None:
    from rembg import new_session, remove  # noqa: PLC0415 — 무거운 의존성

    cut = remove(Image.open(src).convert("RGB"), session=new_session(prm["rembg"])).convert("RGBA")
    al = np.asarray(cut.getchannel("A"))
    ys, xs = np.where(al > prm["alpha_threshold"])
    cut = cut.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    cut = cut.resize((prm["width"], int(cut.height * prm["width"] / cut.width)), Image.LANCZOS)
    cut.save(out)


def process_clip(src: Path, out: Path, a: MediaAsset, offset_sec: float = 0.0, scale: tuple[int, int] | None = None) -> None:
    """정본 segment 를 쓴다. 대체 원본(source_variants)은 offset_sec 만큼 옮긴 시각에서 자른다(D-0045).
    scale = 기본이 아닌 출력 프로파일의 클립 크기(config engine.output.profiles.<이름>.clip, v4.0.0 D-0074) — None 이면 레지스트리 scale."""
    prm = a.tool.params
    w, h = scale or prm["scale"]
    t0, t1 = (x + offset_sec for x in a.segment)
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", str(src),
         "-vf", f"scale={w}:{h},fps={prm['fps']}", "-f", "rawvideo", "-pix_fmt", prm["pix_fmt"], "-"],
        capture_output=True, check=True).stdout
    np.save(out, np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3))


def thumbsheet(src: Path, out: Path, mid: str, segment: tuple[float, float] | None = None) -> list[float]:
    """영상 전체에서 12장(시각 표시) — 사람이 사용 구간을 고르는 검수 시트(14 §10.3-3). 사용 구간은 초록 테두리."""
    dur = probe_duration(src)
    tw_, th_ = SHEET_TILE
    rows = (SHEET_N + SHEET_COLS - 1) // SHEET_COLS
    sheet = Image.new("RGB", (tw_ * SHEET_COLS, (th_ + 24) * rows + 30), (24, 26, 32))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 14)
    except OSError:
        font = ImageFont.load_default()
    times = [dur * (k + 0.5) / SHEET_N for k in range(SHEET_N)]
    for k, tt in enumerate(times):
        png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{tt:.2f}", "-i", str(src), "-frames:v", "1",
                              "-vf", f"scale={tw_}:{th_}", "-f", "image2pipe", "-vcodec", "png", "-"],
                             capture_output=True, check=True).stdout
        im = Image.open(io.BytesIO(png)).convert("RGB")
        x, y = (k % SHEET_COLS) * tw_, (k // SHEET_COLS) * (th_ + 24)
        sheet.paste(im, (x, y))
        inside = segment is not None and segment[0] <= tt <= segment[1]
        if inside:
            d.rectangle((x + 1, y + 1, x + tw_ - 2, y + th_ - 2), outline=(90, 220, 120), width=3)
        d.text((x + 6, y + th_ + 3), f"{tt:5.1f}s" + ("  ← 사용 구간" if inside else ""), fill=(240, 220, 90), font=font)
    seg = f"사용 구간 {segment[0]}–{segment[1]}초" if segment else "구간 미정"
    d.text((6, (th_ + 24) * rows + 6), f"{mid} · 전체 {dur:.1f}초 · {seg} · 사상자·시신 식별 여부를 구간 단위로 확인(14 §2.2)",
           fill=(230, 230, 230), font=font)
    sheet.save(out, quality=88)
    return times


def fetch_variant(v: SourceVariant, media: Path, restore_from: Path | None = None) -> Path:
    """1차 출처 원본(source_variants) — Commons 가 아니다(D-0045). 이미 있음 → 보존본 → 직접 받기, md5 대조."""
    dest = media / v.file
    if not (dest.exists() and dest.stat().st_size > 100):
        dest.parent.mkdir(parents=True, exist_ok=True)
        if restore_from is not None and (restore_from / v.file).exists():
            dest.write_bytes((restore_from / v.file).read_bytes())
            print(f"restore {v.source}:{v.id} ← {restore_from}", flush=True)
        else:
            import urllib.request  # noqa: PLC0415
            req = urllib.request.Request(v.file_url, headers=commons_fetch.UA)
            with urllib.request.urlopen(req, timeout=300) as r:   # noqa: S310 — 레지스트리에 적힌 1차 출처 URL
                dest.write_bytes(r.read())
    h = md5(dest)
    if h != v.md5:
        raise MediaFetchError(f"{v.source}:{v.id} 원본 md5 {h} ≠ 레지스트리 source_variants md5 {v.md5}")
    return dest


def run(proj: Path, only: list[str] | None = None, sheets: bool = True, registry: dict | None = None,
        restore_from: Path | None = None, tries: int | None = None, variant: str | None = None, res: str | None = None,
        getter=None) -> dict:  # noqa: ANN001 — getter = 보도 인용 사진 받기 대역(테스트)
    """res = 기본이 아닌 출력 프로파일(v4.0.0 D-0074, NB28): 영상만 같은 segment·fps·pix_fmt 로 그 프로파일의 clip 크기로
    media/res_<이름>/{file}.npy 에 뽑는다(사진·컷아웃은 원본에서 장치 해상도로 렌더 때 리샘플하므로 대상 아님). 480p npy 는 건드리지 않는다."""
    reg = registry if registry is not None else load_media_registry()
    media = proj / "media"
    media.mkdir(parents=True, exist_ok=True)
    clip_scale: tuple[int, int] | None = None
    if res is not None:
        from engine.style import H_OUT  # noqa: PLC0415
        from orchestrator.config import load_config  # noqa: PLC0415
        cfg = load_config().engine
        name, prof = cfg.profile(res)
        if prof.height == H_OUT:   # v5.5.1 — 기본 클립 = 설계 해상도(480p). 기본 출력 프로파일(720p)과 분리
            raise MediaFetchError(f"--res {res} 는 설계 해상도 프로파일이다 — 기본 클립은 --res 없이(레지스트리 scale)")
        if prof.clip is None:
            raise MediaFetchError(f"config engine.output.profiles.{name}.clip 이 없다 — 클립 크기를 정하지 않은 프로파일")
        res, clip_scale = name, prof.clip
        (media / f"res_{res}").mkdir(exist_ok=True)
    report: dict = {"schema_version": 1, "assets": {}, "res": res, "clip_scale": list(clip_scale) if clip_scale else None}
    failed: list[tuple[str, str]] = []
    for mid, a in reg.items():
        if only and mid not in only:
            continue
        if a.kind == "article" or (res is not None and a.kind != "video"):
            if a.kind == "article":
                report["assets"][mid] = {"kind": "article", "files": []}
            continue
        if a.press_of is not None:   # v5.21.7 D-0189 §1 — 보도 인용(B): 가공 없음, photo_url 원본 그대로가 화면 파일
            try:
                fetch_press(a, media, getter)
                report["assets"][mid] = {"kind": "press_photo", "source": a.photo_url, "source_md5": a.source_hash,
                                         "files": {str(a.file): md5(media / str(a.file))}}
                print(f"ok {mid}: {a.file}", flush=True)
            except MediaFetchError as ex:
                failed.append((mid, str(ex)))
                print(f"FAIL {mid}: {ex}", file=sys.stderr, flush=True)
            continue
        try:
            var = next((v for v in a.source_variants if v.source == variant), None) if variant else None
            if var is not None:   # 정본 대신 1차 출처 원본(D-0045) — 정본 source_hash 는 건드리지 않는다
                src = fetch_variant(var, media, restore_from)
                h = var.md5
            else:
                src = fetch_source(a, media, restore_from, tries)
                h = md5(src)
                if h != a.source_hash:
                    raise MediaFetchError(f"원본 md5 {h} ≠ 레지스트리 source_hash {a.source_hash} — 원본이 바뀌었다(사람 확인)")
            prm = a.tool.params
            if a.kind == "photo":
                if a.file is None:
                    raise MediaFetchError("file 없음")
                Image.open(src).verify()
                process_photo(src, media / a.file, prm)
                files = [a.file]
            elif a.kind == "cutout":
                Image.open(src).verify()
                process_cutout(src, media / str(a.file), prm)
                files = [str(a.file)]
            elif a.kind == "inset":   # v7.3.0 — 가공 없음(원형 클립은 렌더러, UF-103). 원본이 화면 파일
                Image.open(src).verify()
                if src.name != str(a.file):
                    (media / str(a.file)).write_bytes(src.read_bytes())
                files = [str(a.file)]
            else:
                dur = probe_duration(src)
                want = var.duration if var is not None else a.duration
                if want is not None and abs(dur - want) > 0.05:
                    raise MediaFetchError(f"영상 길이 {dur} ≠ 레지스트리 {want}")
                name_ = f"{a.file}_480.npy" if res is None else f"res_{res}/{a.file}.npy"
                process_clip(src, media / name_, a, var.offset_sec if var is not None else 0.0, clip_scale)
                files = [name_]
                if sheets and res is None:
                    thumbsheet(src, media / f"thumbsheet_{mid}.jpg", mid, a.segment)
                    files.append(f"thumbsheet_{mid}.jpg")
            report["assets"][mid] = {"kind": a.kind, "source": var.file if var is not None else prm["source"], "source_md5": h,
                                     "variant": var.source if var is not None else None,
                                     "files": {f: md5(media / f) for f in files}}
            print(f"ok {mid}: {', '.join(files)}", flush=True)
        except Exception as ex:  # noqa: BLE001 — 모아서 마지막에 한 번에(남은 항목 + 재실행 명령)
            failed.append((mid, str(ex)))
            print(f"FAIL {mid}: {ex}", file=sys.stderr, flush=True)
    if failed:
        left = ",".join(m for m, _ in failed)
        raise MediaFetchError("미디어 수집 실패 — 남은 항목:\n" + "\n".join(f"  {m}: {e}" for m, e in failed)
                              + f"\n재실행: python tools/media_fetch.py {proj} --only {left}")
    return report


def fetch_press(a: MediaAsset, media: Path, getter=None) -> Path:  # noqa: ANN001 — getter(url) -> bytes = commons_fetch.http_get 대역(테스트)
    """보도 인용(B) 사진 재수집(v5.21.7 D-0189 §1) — 프로젝트 media/ 에 있고 md5 가 맞으면 그대로, 없으면 photo_url 을 저장소 UA·재시도로
    받아 source_hash 와 대조한다. 받지 못하거나 다르면 MediaFetchError(재수집 불가 — 조용히 넘기지 않는다, P6)."""
    dest = media / str(a.file)
    if dest.exists() and md5(dest) == a.source_hash:
        return dest
    get = getter or commons_fetch.http_get
    try:
        data = get(str(a.photo_url))
    except Exception as ex:  # noqa: BLE001 — 아래 한 문구로
        raise MediaFetchError(f"보도 인용 — 재수집 불가: {a.photo_url} 를 받지 못했다({ex}). 원본은 등록한 컨테이너의 프로젝트 media/{a.file}") from ex
    h = hashlib.md5(data).hexdigest()
    if h != a.source_hash:
        raise MediaFetchError(f"보도 인용 — 재수집 불가: {a.photo_url} 원본 md5 {h} ≠ 레지스트리 {a.source_hash}"
                              f"(매체가 사진을 바꿨다). 원본은 등록한 컨테이너의 프로젝트 media/{a.file} — 사람 확인")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest


def _excluded(lic: str, pieces: list[str]) -> bool:
    """라이선스 이름에 제외 조각(NC·ND — NATO BY-NC-ND 등)이 낱말로 있는가."""
    words = re.split(r"[\s\-_/]+", lic.upper())
    return any(p.upper() in words for p in pieces)


def search_pools(query: str, limit: int = 7, only: str | None = None, log: Path | None = None, sid: str | None = None,
                 searcher=None) -> list[dict]:  # noqa: ANN001 — searcher(query, limit) = commons_fetch.search 대역(테스트)
    """v5.19.0 D-0163 §2 — rules media_beats.sources_order 순서로 후보를 찾는다(권리 통과가 쉬운 풀 먼저).
    via commons = Commons 검색 + query_suffix(라이선스 허용·제한 없음·제외 조각 없음 = 통과), via manual = 안내 줄(조용히 건너뛰지 않는다, P6).
    log·sid 를 주면 풀마다 결과 요약을 `media_search.json` 에 덧붙인다(찾은 수·통과 수·상위 제목·탈락 사유)."""
    import datetime as dt  # noqa: PLC0415

    from rules import load_rules  # noqa: PLC0415
    from schemas.media_models import MediaSearch, MediaSearchLog  # noqa: PLC0415

    mb = load_rules().media_beats
    pools = [p for p in mb.sources_order if only is None or p.id == only]
    if not pools:
        raise MediaFetchError(f"풀 {only!r} 없음 — rules media_beats.sources_order: {[p.id for p in mb.sources_order]}")
    find = searcher or commons_fetch.search
    rows: list[dict] = []
    logged: list[MediaSearch] = []
    for rank, p in enumerate(pools, 1):
        if p.via == "manual":
            rows.append({"pool": p.id, "rank": rank, "label": p.label, "manual": p.hint})
            continue
        q = f"{query} {p.query_suffix}".strip()
        found = find(q, limit)
        ok, rej = [], []
        for c in found:
            bad = _excluded(c["lic"], mb.sources_excluded_licenses)
            doc = c.get("mime", "") in mb.sources_excluded_mimes   # v5.21.0 — 문서·도식은 사진 후보 밖(통과 수에 넣지 않는다)
            good = c["allowed"] and not bad and not doc
            rows.append({"pool": p.id, "rank": rank, **{k: c[k] for k in ("title", "lic", "restrictions", "page")}, "allowed": good})
            (ok if good else rej).append(c["title"] if good else f"문서·도식({c['mime']})" if doc else f"{c['lic'] or '라이선스 없음'}"
                                         + (" 제한" if c["restrictions"] else "") + (" NC·ND" if bad else ""))
        logged.append(MediaSearch(sid=sid or "-", query=q, pool=p.id, on=dt.date.today().isoformat(), found=len(found), passed=len(ok),
                                  top=ok[:5], rejected=sorted(set(rej))[:5]))
    if log is not None:
        from script.media_table import SEARCH_FILE  # noqa: PLC0415

        path = log / SEARCH_FILE
        doc = MediaSearchLog.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else MediaSearchLog()
        again = {(x.sid, x.query, x.pool) for x in logged}   # v5.21.0 — 같은 문장·검색어·풀을 다시 찾으면 최신 기록이 대체한다
        doc.searches = [x for x in doc.searches if (x.sid, x.query, x.pool) not in again] + logged
        path.write_text(doc.model_dump_json(indent=1) + "\n", encoding="utf-8")
    return rows


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "search":
        ap = argparse.ArgumentParser(description="사진 후보 검색 — rules media_beats.sources_order 풀 순서(D-0163 §2)")
        ap.add_argument("cmd")
        ap.add_argument("query")
        ap.add_argument("--limit", type=int, default=7)
        ap.add_argument("--pool", default=None, help="풀 하나만(id). 기본 = 규칙 순서 전부")
        ap.add_argument("--log", type=Path, default=None, help="프로젝트 폴더 — 결과 요약을 media_search.json 에(게이트 ① 미디어 계획 표)")
        ap.add_argument("--sid", default=None, help="--log 와 함께: 문장 id({장면}_{순번})")
        args = ap.parse_args(argv)
        if (args.log is None) != (args.sid is None):
            ap.error("--log 와 --sid 는 함께 쓴다")
        for row in search_pools(args.query, args.limit, args.pool, args.log, args.sid):
            print(json.dumps(row, ensure_ascii=False))
        return 0
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("proj", type=Path)
    ap.add_argument("--only", default="")
    ap.add_argument("--no-sheets", action="store_true")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--restore-from", type=Path, default=None,
                    help="원본 보존본 폴더(artifacts hormuz/media_src) — 있으면 Commons 에 요청하지 않는다(D-0044 B)")
    ap.add_argument("--variant", choices=["dvids"], default=None,
                    help="정본(Commons) 대신 레지스트리 source_variants 의 1차 출처 원본으로 가공(D-0045, 영상만)")
    ap.add_argument("--res", default=None, help="기본이 아닌 출력 프로파일(1080p·final) — 영상 클립만 media/res_<프로파일>/ 로(D-0074)")
    ap.add_argument("--tries", type=int, default=None, help="원본 요청 시도 횟수(기본 config commons.tries). 차단 중 30분 간격 1회 시도용")
    args = ap.parse_args(argv)
    try:
        rep = run(args.proj, [x for x in args.only.split(",") if x] or None, not args.no_sheets,
                  restore_from=args.restore_from, tries=args.tries, variant=args.variant, res=args.res)
    except MediaFetchError as ex:
        print(str(ex), file=sys.stderr)
        return 1
    if args.report:
        args.report.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
