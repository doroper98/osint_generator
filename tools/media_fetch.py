"""미디어 수집·가공기 (v2.5.5, back_and_forth D-0036 작업 4·5, 14 §2·§3·§10.3·§10.4, 07 §3.2).

    python tools/media_fetch.py <project_dir> [--only mid,mid] [--sheets]
    python tools/media_fetch.py search "P-8A Poseidon" [--limit 7]      # 후보 검색(라이선스·제한 표시) — 고르는 것은 사람

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
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from engine.media_registry import load_media_registry  # noqa: E402
from schemas.media_models import MediaAsset  # noqa: E402
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


def process_clip(src: Path, out: Path, a: MediaAsset) -> None:
    prm = a.tool.params
    w, h = prm["scale"]
    t0, t1 = a.segment
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


def run(proj: Path, only: list[str] | None = None, sheets: bool = True, registry: dict | None = None,
        restore_from: Path | None = None, tries: int | None = None) -> dict:
    reg = registry if registry is not None else load_media_registry()
    media = proj / "media"
    media.mkdir(parents=True, exist_ok=True)
    report: dict = {"schema_version": 1, "assets": {}}
    failed: list[tuple[str, str]] = []
    for mid, a in reg.items():
        if only and mid not in only:
            continue
        if a.kind == "article":
            report["assets"][mid] = {"kind": "article", "files": []}
            continue
        try:
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
            else:
                dur = probe_duration(src)
                if a.duration is not None and abs(dur - a.duration) > 0.05:
                    raise MediaFetchError(f"영상 길이 {dur} ≠ 레지스트리 {a.duration}")
                process_clip(src, media / f"{a.file}_480.npy", a)
                files = [f"{a.file}_480.npy"]
                if sheets:
                    thumbsheet(src, media / f"thumbsheet_{mid}.jpg", mid, a.segment)
                    files.append(f"thumbsheet_{mid}.jpg")
            report["assets"][mid] = {"kind": a.kind, "source": prm["source"], "source_md5": h,
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


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "search":
        ap = argparse.ArgumentParser(description="Commons 후보 검색")
        ap.add_argument("cmd")
        ap.add_argument("query")
        ap.add_argument("--limit", type=int, default=7)
        args = ap.parse_args(argv)
        for c in commons_fetch.search(args.query, args.limit):
            print(json.dumps({k: c[k] for k in ("title", "lic", "restrictions", "allowed", "page")}, ensure_ascii=False))
        return 0
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("proj", type=Path)
    ap.add_argument("--only", default="")
    ap.add_argument("--no-sheets", action="store_true")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--restore-from", type=Path, default=None,
                    help="원본 보존본 폴더(artifacts hormuz/media_src) — 있으면 Commons 에 요청하지 않는다(D-0044 B)")
    ap.add_argument("--tries", type=int, default=None, help="원본 요청 시도 횟수(기본 config commons.tries). 차단 중 30분 간격 1회 시도용")
    args = ap.parse_args(argv)
    try:
        rep = run(args.proj, [x for x in args.only.split(",") if x] or None, not args.no_sheets,
                  restore_from=args.restore_from, tries=args.tries)
    except MediaFetchError as ex:
        print(str(ex), file=sys.stderr)
        return 1
    if args.report:
        args.report.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
