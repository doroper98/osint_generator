"""소스 인테이크 — `intake/sources.json` 을 만들고 고친다 (v3.2.0, docs/handoff/18 §1·§2·§7, 16 §6, back_and_forth D-0051 작업 5·11).

입력 형태(18 §1):
- X 텍스트: 사용자가 붙여넣은 본문 + 계정·시각 → `XPostSource(input="text")`
- X 캡처: 이미지 → `intake/screenshots/<id>.png` 보관 → 캡처 판독 워커(vision) 초안 → `XPostSource(input="capture")`
- 기사: URL(가져오기) 또는 본문 붙여넣기 → `ArticleSource`. 본문은 `intake/bodies/<id>.txt`(비공개)에 두고 레코드엔 요지만
- 공문·자료: 파일/URL → `DocumentSource`
공식 계정 여부(`account_class`)는 코드가 `rules/official_accounts.yaml` 로 정한다. **x.com·twitter.com 은 열지 않는다**
(`BLOCKED_HOSTS`, 18 §1 스크래핑 금지). 사용자 확인(`confirm`) 전 레코드는 검증 단계로 가지 않는다(18 §7).
"""

from __future__ import annotations

import html
import json
import re
import shutil
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional, Union

from rules import classify_handle
from schemas.source_models import ArticleSource, CaptureDraft, DocumentSource, SourcesFile, XPostSource

SOURCES = Path("intake") / "sources.json"
SCREENSHOTS = Path("intake") / "screenshots"
BODIES = Path("intake") / "bodies"
DRAFTS = Path("intake") / "drafts"
# 18 §1 — X 는 로그인 벽·약관 때문에 직접 열지 않는다. 링크만 주면 텍스트/캡처를 요청한다
BLOCKED_HOSTS: frozenset[str] = frozenset({"x.com", "twitter.com", "t.co", "mobile.twitter.com", "mobile.x.com", "nitter.net"})
_PREFIX = {"x_post": "src_x_", "article": "src_art_", "document": "src_doc_"}

Source = Union[XPostSource, ArticleSource, DocumentSource]


class SourceIntakeError(ValueError):
    pass


def sources_path(pdir: Path) -> Path:
    return pdir / SOURCES


def load_sources(pdir: Path) -> SourcesFile:
    p = sources_path(pdir)
    if not p.exists():
        return SourcesFile()
    return SourcesFile.model_validate_json(p.read_text(encoding="utf-8"))


def save_sources(pdir: Path, f: SourcesFile) -> Path:
    p = sources_path(pdir)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(f.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    tmp.replace(p)
    return p


def next_id(f: SourcesFile, kind: str) -> str:
    pre = _PREFIX[kind]
    n = max((int(s.id[len(pre):]) for s in f.sources if s.id.startswith(pre) and s.id[len(pre):].isdigit()), default=0)
    return f"{pre}{n + 1:04d}"


def _append(pdir: Path, rec: Source) -> Source:
    f = load_sources(pdir)
    save_sources(pdir, SourcesFile(sources=[*f.sources, rec]))
    return rec


def host_blocked(url: str) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in BLOCKED_HOSTS)


def add_x_text(pdir: Path, *, account_name: str, handle: str, text: str, posted_at: Optional[datetime], lang: str,
               text_ko: Optional[str] = None, url: Optional[str] = None, attached_media: str = "none", note: str = "",
               retrieved: Optional[date] = None) -> XPostSource:
    """X 게시물 텍스트 붙여넣기(18 §1). url 은 기록만 한다 — 열지 않는다."""
    f = load_sources(pdir)
    rec = XPostSource(id=next_id(f, "x_post"), type="x_post", input="text", account_name=account_name, handle=handle,
                      account_class=classify_handle(handle), posted_at=posted_at, text_original=text, text_ko=text_ko,
                      lang=lang, url=url, attached_media=attached_media, note=note,  # type: ignore[arg-type]
                      retrieved_at=retrieved or date.today())
    return _append(pdir, rec)  # type: ignore[return-value]


def stage_capture(pdir: Path, image: Path) -> str:
    """캡처 이미지를 비공개 보관 위치로 복사하고 새 소스 id 를 예약한다(레코드는 판독 초안이 나온 뒤)."""
    if image.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise SourceIntakeError(f"캡처는 png·jpg 만: {image.name}")
    f = load_sources(pdir)
    taken = {p.stem for p in (pdir / SCREENSHOTS).glob("*.png")}
    sid = next_id(f, "x_post")
    while sid in taken:
        sid = f"src_x_{int(sid[6:]) + 1:04d}"
    dst = pdir / SCREENSHOTS / f"{sid}.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if image.suffix.lower() == ".png":
        shutil.copyfile(image, dst)
    else:
        from PIL import Image  # noqa: PLC0415

        Image.open(image).save(dst)
    return sid


def add_capture_draft(pdir: Path, sid: str, draft: CaptureDraft, *, url: Optional[str] = None, note: str = "",
                      retrieved: Optional[date] = None) -> XPostSource:
    """판독 초안 → 미확인 XPostSource. account_class 는 목록 조회(코드), 확인 필드는 비어 있다."""
    rec = XPostSource(id=sid, type="x_post", input="capture", account_name=draft.account_name, handle=draft.handle,
                      account_class=classify_handle(draft.handle), posted_at=draft.posted_at,
                      text_original=draft.text_original, text_ko=draft.text_ko, lang=draft.lang,
                      capture=(SCREENSHOTS / f"{sid}.png").as_posix(), attached_media=draft.attached_media,
                      deleted=draft.deleted_notice, drafted_by="capture_read", url=url,
                      note=note + (f" [판독 못 함: {', '.join(draft.unreadable)}]" if draft.unreadable else "")
                      + (f" [화면 시각: {draft.posted_at_text}]" if draft.posted_at_text else ""),
                      retrieved_at=retrieved or date.today())
    return _append(pdir, rec)  # type: ignore[return-value]


def read_capture(pdir: Path, sid: str, *, note: str = "", backend: str = "claude") -> tuple[Optional[XPostSource], list[str]]:
    """캡처 판독 워커 1회 → 초안 → sources.json. 실패면 (None, 오류) — 레코드를 만들지 않는다(P6)."""
    import argparse  # noqa: PLC0415

    from schemas.models import TaskQueueItem  # noqa: PLC0415
    from workers.capture_read_worker import CaptureReadWorker  # noqa: PLC0415

    w = CaptureReadWorker()
    w.llm_backend = backend
    task = TaskQueueItem(task_id=f"capture_read__{sid}", input_item_id=sid, task_type="capture_read",
                         assigned_worker="capture_read", description=note or "(메모 없음)",
                         input_refs=[(SCREENSHOTS / f"{sid}.png").as_posix()], output_refs=[(DRAFTS / f"{sid}.json").as_posix()])
    args = argparse.Namespace(project_id=pdir.name, task_id=task.task_id, projects_root=str(pdir.parent))
    res = w.run(args, task)
    try:
        w.write_result(args, res)
    except OSError:
        pass
    status = res.status if isinstance(res.status, str) else res.status.value
    draft_p = pdir / DRAFTS / f"{sid}.json"
    if status != "completed" or not draft_p.exists():
        return None, list(res.errors) or [f"capture_read 실패({status})"]
    draft = CaptureDraft.model_validate_json(draft_p.read_text(encoding="utf-8"))
    return add_capture_draft(pdir, sid, draft, note=note), []


_TAG = re.compile(r"<[^>]+>")
_META = r'<meta[^>]+(?:property|name)=["\']{}["\'][^>]+content=["\']([^"\']+)["\']'


def fetch_article(url: str, timeout: float = 20.0) -> dict[str, str]:
    """기사 URL 가져오기(18 §1) — 제목·매체·게시일·본문 텍스트. X 계열 호스트는 거부(스크래핑 금지)."""
    if host_blocked(url):
        raise SourceIntakeError(f"X 링크는 열지 않는다(18 §1) — 게시물 텍스트나 캡처를 달라: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (osint_generator source intake)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:   # noqa: S310 — http(s) 만(아래 검사)
        raw = r.read().decode(r.headers.get_content_charset() or "utf-8", errors="replace")
    if urllib.parse.urlparse(url).scheme not in ("http", "https"):
        raise SourceIntakeError(f"http(s) 만: {url}")

    def meta(key: str) -> str:
        m = re.search(_META.format(re.escape(key)), raw, re.I)
        return html.unescape(m.group(1)).strip() if m else ""

    title = meta("og:title") or html.unescape((re.search(r"<title>(.*?)</title>", raw, re.S | re.I) or [None, ""])[1]).strip()
    body = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
    paras = [html.unescape(_TAG.sub(" ", p)).strip() for p in re.findall(r"(?is)<p[^>]*>(.*?)</p>", body)]
    text = "\n".join(re.sub(r"\s+", " ", p) for p in paras if len(p) > 30)
    return {"title": title, "publisher": meta("og:site_name"), "published": meta("article:published_time")[:10], "body": text}


def add_article(pdir: Path, *, publisher: str, headline: str, published_at: date, body: str, url: Optional[str] = None,
                headline_ko: Optional[str] = None, key_facts: Optional[list[str]] = None, lang: str = "ko", note: str = "",
                retrieved: Optional[date] = None) -> ArticleSource:
    """기사(18 §2). 본문은 `intake/bodies/<id>.txt` 비공개 보관 — 레코드에는 요지(key_facts)만. 요지가 없으면 헤드라인."""
    if url and host_blocked(url):
        raise SourceIntakeError(f"X 링크는 기사로 받지 않는다: {url}")
    f = load_sources(pdir)
    sid = next_id(f, "article")
    bp = pdir / BODIES / f"{sid}.txt"
    bp.parent.mkdir(parents=True, exist_ok=True)
    bp.write_text(body, encoding="utf-8")
    rec = ArticleSource(id=sid, type="article", publisher=publisher, headline_original=headline, headline_ko=headline_ko,
                        published_at=published_at, key_facts=key_facts or [headline], url=url, lang=lang, note=note,
                        retrieved_at=retrieved or date.today())
    return _append(pdir, rec)  # type: ignore[return-value]


def add_document(pdir: Path, *, issuer: str, title: str, body: str, key_facts: Optional[list[str]] = None,
                 published_at: Optional[date] = None, url: Optional[str] = None, file: Optional[Path] = None,
                 lang: str = "ko", note: str = "", retrieved: Optional[date] = None) -> DocumentSource:
    f = load_sources(pdir)
    sid = next_id(f, "document")
    bp = pdir / BODIES / f"{sid}.txt"
    bp.parent.mkdir(parents=True, exist_ok=True)
    bp.write_text(body, encoding="utf-8")
    kept = None
    if file is not None:
        dst = pdir / "intake" / "files" / file.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, dst)
        kept = dst.relative_to(pdir).as_posix()
    rec = DocumentSource(id=sid, type="document", issuer=issuer, title=title, published_at=published_at, url=url, file=kept,
                         key_facts=key_facts or [title], lang=lang, note=note, retrieved_at=retrieved or date.today())
    return _append(pdir, rec)  # type: ignore[return-value]


def body_text(pdir: Path, rec: Source) -> str:
    """검증 대조용 본문 — X 는 원문(+번역), 기사·공문은 보관 본문 + 헤드라인·요지."""
    if isinstance(rec, XPostSource):
        return "\n".join(x for x in (rec.text_original, rec.text_ko) if x)
    bp = pdir / BODIES / f"{rec.id}.txt"
    head = rec.headline_original if isinstance(rec, ArticleSource) else rec.title
    extra = [rec.headline_ko] if isinstance(rec, ArticleSource) and rec.headline_ko else []
    return "\n".join([head, *extra, *rec.key_facts, bp.read_text(encoding="utf-8") if bp.exists() else ""])


def confirm(pdir: Path, sid: str, by: str, **fix: object) -> Source:
    """사용자 확인(18 §7) — 계정·시각이 맞는지 본 사람. fix 로 초안 값을 고칠 수 있다(account_class 는 코드가 다시 정한다)."""
    f = load_sources(pdir)
    recs = f.by_id()
    if sid not in recs:
        raise SourceIntakeError(f"소스 없음: {sid}")
    data = recs[sid].model_dump() | {k: v for k, v in fix.items() if v is not None}
    if data["type"] == "x_post":
        data["account_class"] = classify_handle(str(data["handle"]))
    data |= {"confirmed_by": by, "confirmed_at": datetime.now(timezone.utc)}
    new = type(recs[sid]).model_validate(data)
    save_sources(pdir, SourcesFile(sources=[new if s.id == sid else s for s in f.sources]))
    return new


def unconfirmed(pdir: Path) -> list[str]:
    return [s.id for s in load_sources(pdir).sources if not s.confirmed]


def summary(pdir: Path) -> dict[str, object]:
    f = load_sources(pdir)
    return {"total": len(f.sources), "by_type": {t: sum(s.type == t for s in f.sources) for t in _PREFIX},
            "unconfirmed": unconfirmed(pdir),
            "official": [s.id for s in f.sources if isinstance(s, XPostSource) and s.account_class.startswith("official")]}


def dump(pdir: Path) -> str:
    return json.dumps(summary(pdir), ensure_ascii=False)


__all__ = ["BLOCKED_HOSTS", "SourceIntakeError", "add_article", "add_capture_draft", "add_document", "add_x_text",
           "body_text", "confirm", "fetch_article", "host_blocked", "load_sources", "read_capture", "save_sources",
           "stage_capture", "summary", "unconfirmed"]
