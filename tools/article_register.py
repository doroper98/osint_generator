"""확인된 기사 출처 → 기사 조판(article) 미디어 항목 등록 (v5.6.0, 사용자 지적 2026-10-05).

사용자 지적: "기사 내용을 조판하여 실제 기사 이미지처럼 보여주는 장면이 이번에 없었다 — 원인이 뭐지?"
원인: 기사 조판은 미디어 레지스트리(`assets/media/media_registry.json`)에 등록된 항목만 연출 후보가 되는데, 등록이 손으로 하는
별도 단계라 kaliningrad-suwalki 에서 빠졌다(PIPELINE-AP-019). 이 도구가 sources.json 의 확인된 기사로 항목을 만든다.

    python tools/article_register.py projects/<pid>            # 무엇이 등록될지·무엇이 빠졌는지(쓰지 않음)
    python tools/article_register.py projects/<pid> --write    # 레지스트리에 추가

- 대상: type article · confirmed · 참조 출처(rules source_note.publishers — 위키백과 등) 아님 · 레지스트리에 같은 url 없음.
- 조판 문구(14 §9 — 화면 캡처·로고 없음, 우리 타이포): 매체명·날짜·원문 헤드라인(headline_original)·헤드라인 번역(headline_ko)·
  부제 = 그 출처를 근거로 쓴 원고 claim 문장(검증된 한국어). 번역은 사람·에이전트가 sources.json headline_ko 에 적는다 —
  비어 있으면 등록하지 않고 "번역 필요"로 알린다(조용히 빼지 않는다, 15 P6).
- 권리 = 헤드라인 번역·요지 자체 조판(기존 기사 항목과 같은 문구). 사진은 `tools/media_fetch.py search` 로 권리 통과 풀(A)을 먼저 찾는다.

v5.21.0 back_and_forth D-0177 §5(사용자 결정 D172) — 보도 인용(B) 사진 등록. A 검색 기록이 0건인 문장의 기사에만 쓴다(게이트 ① 표가 검사).

    python tools/article_register.py projects/<pid> --press-photo <기사 페이지 URL> --agency Reuters \
        --verified-by "사용자 라운드" --relevance "리야드 공항 피격 현장" --casualty-free [--write]
    python tools/article_register.py projects/<pid> --press-photo <기사 페이지 URL> --file <사진 파일> --photo-url <사진 원본 URL> ...

- 기사 페이지 URL 은 레지스트리 기사(kind article)의 url 과 같아야 한다(그 기사 카드에서만 쓰는 사진). 파일을 주지 않으면 기사 페이지의
  대표 사진(og:image)을 저장소 UA·재시도 간격(tools/commons_fetch.http_get)으로 받는다.
- 기록: 원본 URL(photo_url)·통신사(agency)·촬영자(--photographer, 없으면 통신사)·받은 시각·파일 md5·rights_status restricted·
  user_exception U20261011·exception 문구·license "통신사 저작물 — 인용(<통신사>)". 사람 확인 칸 verified_by(사상자 없음·관련성)는
  다른 사진 자산과 같은 규칙 — `--casualty-free` 없이는 등록되지 않는다. 가공은 자르기·축소만(G4-10, 렌더가 화면 맞춤).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import hashlib
import re

PRESS_EXCEPTION = "U20261011"
PRESS_EXCEPTION_TEXT = "사용자 결정 D172(2026-10-11) — 보도 인용(저작권법 §28 취지), 개인 프로젝트, 공개 배포 전 재확인"
OG_IMAGE = re.compile(r"""<meta[^>]+(?:property|name)=["'](?:og:image|twitter:image)["'][^>]+content=["']([^"']+)["']""", re.I)
LICENSE = "헤드라인 번역·요지 자체 조판(원문 인용 15단어 미만, 기사 화면 캡처·로고 없음, 14 §9)"
SUB_MAX = 40   # 부제 글자 상한(조판 상자 한 줄)


def _mid(pid: str, sid: str) -> str:
    return f"{pid.replace('-', '_')}_{sid.replace('src_', '')}"


def _strip_site(h: str, pub: str) -> str:
    """원문 헤드라인 끝의 사이트 이름(" | Missile Threat", " - Euromaidan Press")만 뗀다 — 헤드라인 본문은 그대로(verbatim)."""
    for sep in (" | ", " - "):
        if sep in h:
            head, tail = h.rsplit(sep, 1)
            if any(w.lower() in tail.lower() for w in pub.replace("(", " ").split() if len(w) > 2):
                return head
    return h


def plan(proj: Path) -> tuple[dict[str, dict], list[str]]:
    """(등록할 항목 mid → 레지스트리 dict, 빠진 이유 줄)."""
    from engine.media_registry import registry_path  # noqa: PLC0415
    from rules import load_rules  # noqa: PLC0415

    refs = load_rules().source_note.publishers
    reg = json.loads(registry_path().read_text(encoding="utf-8"))["assets"]
    have = {a.get("url") for a in reg.values()}
    srcs = json.loads((proj / "intake" / "sources.json").read_text(encoding="utf-8"))["sources"]
    claims = json.loads((proj / "intake" / "claims.json").read_text(encoding="utf-8"))["claims"]
    by_src: dict[str, list[str]] = {}
    for c in claims:
        for s in c["source_ids"]:
            by_src.setdefault(s, []).append(c["text"])
    out: dict[str, dict] = {}
    skipped: list[str] = []
    today = dt.date.today().isoformat()
    for s in srcs:
        if s.get("type") != "article" or not s.get("confirmed_by"):
            continue
        pub = str(s.get("publisher", ""))
        if any(pub.startswith(p) for p in refs):
            continue
        if s.get("url") in have:
            continue
        if not s.get("headline_ko"):
            skipped.append(f"{s['id']} {pub}: 헤드라인 번역(sources.json headline_ko) 없음 — 번역을 적고 다시 실행")
            continue
        if not by_src.get(s["id"]):
            skipped.append(f"{s['id']} {pub}: 이 출처를 근거로 한 claim 없음 — 영상에 쓰이지 않는 기사")
            continue
        head = _strip_site(str(s.get("headline_original", "")), pub)
        sub = by_src[s["id"]][0]
        sub = sub if len(sub) <= SUB_MAX else sub[: SUB_MAX - 1] + "…"
        date = str(s.get("published_at", ""))
        out[_mid(proj.name, s["id"])] = {
            "kind": "article", "title": f"{pub} {date} — {head}", "license": LICENSE,
            "author": pub, "credit_author": pub, "date": date, "url": s["url"], "caption": pub,
            "file_note": date.replace("-", ". "), "depicts": [sub], "is_file_photo": False,
            "verified_by": {"by": "code(tools/article_register — sources.json 확인 기록·claims 대조)", "on": today,
                            "casualty_free": True, "relevance": f"{proj.name} 원고 claim 근거 기사"},
            "rights_status": "rights_clear", "retrieved_at": str(s.get("retrieved_at", today)),
            "tool": {"name": "article_typeset", "params": {"translation": True}},
            "headline": s["headline_ko"], "sub": sub, "note": "헤드라인 번역 · 원문 영어",
            "headline_original": head or None,
        }
    return out, skipped


def og_image(html: str) -> str:
    """기사 페이지의 대표 사진 URL(og:image, 없으면 twitter:image). 없으면 ValueError(사진을 지어내지 않는다)."""
    m = OG_IMAGE.search(html) or re.search(r"""<meta[^>]+content=["']([^"']+)["'][^>]+(?:property|name)=["']og:image["']""", html, re.I)
    if not m:
        raise ValueError("기사 페이지에 대표 사진(og:image)이 없다 — --file 과 --photo-url 로 지정")
    return m.group(1).replace("&amp;", "&")


def press_photo_entry(reg: dict, page_url: str, agency: str, data: bytes, photo_url: str, ext: str, verified_by: str,
                      relevance: str, casualty_free: bool, photographer: str | None = None,
                      on: str | None = None) -> tuple[str, dict, str]:
    """(사진 mid, 레지스트리 dict, 파일 이름). 기사 = url 이 page_url 인 레지스트리 article."""
    art = next((k for k, a in reg.items() if a.get("kind") == "article" and a.get("url") == page_url), None)
    if art is None:
        raise ValueError(f"레지스트리에 이 url 의 기사(kind article)가 없다: {page_url} — 기사 조판을 먼저 등록(이 도구 기본 모드)")
    a = reg[art]
    now = on or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    name = f"press_{art}{ext}"
    entry = {
        "kind": "photo", "title": f"{agency} photo — {a['title']}", "license": f"통신사 저작물 — 인용({agency})",
        "author": photographer or agency, "credit_author": agency, "date": a["date"], "url": page_url, "caption": f"{agency} 사진",
        "file_note": a["file_note"], "depicts": [relevance], "is_file_photo": False,
        "verified_by": {"by": verified_by, "on": now[:10], "casualty_free": casualty_free, "relevance": relevance},
        "rights_status": "restricted", "retrieved_at": now,
        "tool": {"name": "press_quote", "params": {"edit": "crop_scale_only"}},
        "source_hash": hashlib.md5(data).hexdigest(), "file": name,
        "press_of": art, "agency": agency, "photo_url": photo_url,
        "user_exception": PRESS_EXCEPTION, "exception": PRESS_EXCEPTION_TEXT,
    }
    return f"{art}_press", entry, name


def register_press(a: argparse.Namespace) -> int:
    from engine.media_registry import registry_path  # noqa: PLC0415
    from schemas.media_models import MediaRegistryFile  # noqa: PLC0415
    from tools.commons_fetch import http_get  # noqa: PLC0415 — 저장소 UA·재시도 간격

    p = registry_path()
    doc = json.loads(p.read_text(encoding="utf-8"))
    if a.file is not None:
        if not a.photo_url:
            raise SystemExit("--file 에는 --photo-url(사진 원본 URL)이 필요하다")
        data, photo_url = a.file.read_bytes(), a.photo_url
    else:
        photo_url = a.photo_url or og_image(http_get(a.press_photo).decode("utf-8", "replace"))
        data = http_get(photo_url)
    ext = Path(photo_url.split("?")[0]).suffix.lower() if a.file is None else a.file.suffix.lower()
    mid, entry, name = press_photo_entry(doc["assets"], a.press_photo, a.agency, data, photo_url, ext if ext in (".jpg", ".jpeg", ".png", ".webp") else ".jpg",
                                         a.verified_by, a.relevance, a.casualty_free, a.photographer)
    doc["assets"][mid] = entry
    MediaRegistryFile.model_validate(doc)   # 권리·필드 검증(C9) — 틀리면 쓰지 않는다
    if a.write:
        (a.proj / "media").mkdir(parents=True, exist_ok=True)
        (a.proj / "media" / name).write_bytes(data)
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"press_photo": mid, "file": f"media/{name}", "photo_url": photo_url, "md5": entry["source_hash"],
                      "written": bool(a.write)}, ensure_ascii=False, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    from engine.media_registry import registry_path  # noqa: PLC0415
    from schemas.media_models import MediaRegistryFile  # noqa: PLC0415

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("proj", type=Path)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--press-photo", default=None, help="보도 인용(B) 사진 — 그 사진이 실린 기사 페이지 URL(레지스트리 기사 url)")
    ap.add_argument("--agency", default=None)
    ap.add_argument("--file", type=Path, default=None)
    ap.add_argument("--photo-url", default=None)
    ap.add_argument("--photographer", default=None)
    ap.add_argument("--verified-by", default=None)
    ap.add_argument("--relevance", default=None)
    ap.add_argument("--casualty-free", action="store_true")
    a = ap.parse_args(argv)
    if a.press_photo is not None:
        missing = [f for f in ("agency", "verified_by", "relevance") if not getattr(a, f)]
        if missing:
            raise SystemExit(f"--press-photo 에 필요한 값 없음: {missing}")
        a.proj = a.proj.resolve()
        return register_press(a)
    items, skipped = plan(a.proj.resolve())
    if a.write and items:
        p = registry_path()
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc["assets"].update(items)
        MediaRegistryFile.model_validate(doc)   # 권리·필드 검증(C9) — 틀리면 쓰지 않는다
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"register": sorted(items), "skipped": skipped, "written": bool(a.write and items)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
