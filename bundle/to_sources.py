"""번들 출처·주장 → 6.95 소스 인테이크 재료 (v3.5.0, docs/handoff/12 §2, 18 §2·§3, back_and_forth D-0063 작업 2, D-0064 쟁점 2·3).

**번들은 2차 자료다.** 번들이 가리킨 기사를 6.95 기사 레코드(`ArticleSource`)로만 옮긴다(D-0064 쟁점 2 A):
1. 번들 `sources[].url` 이 인용 문자열("매체, '제목', YYYY-MM-DD (url)")이면 매체·제목·게시일·url 을 읽는다.
2. 본문·빠진 칸은 `fetch`(기사 URL 가져오기 — `add-source --fetch` 와 같은 함수, 호출자가 주입)로 채운다.
3. 본문·제목·매체·게시일 네 칸이 다 차야 레코드가 된다(`add-source` 기사 조건과 같음). 못 채우면 **만들지 않고**
   `unresolved[]` 에 사유를 남긴다(15 P6) — 코드가 본문을 요약해 지어내지 않는다. `key_facts` 는 add-source 와 같이 헤드라인.
- 검증 status 는 여기서 정하지 않는다. 번들 confidence·status 는 status 로 옮기지 않는다(D-0063 작업 2) — 판정은 6.95
  `orchestrator.source_verify.judge`(인용 대조, D50·D53). 레코드는 사용자 확인 전(`confirmed_by` 비움, 18 §7).
- claims 후보(`BundleClaimsFile`, `intake/bundle_claims.json`): 번들 `claims[]`(status·confidence 는 참고 필드 `bundle_*`)와
  `contradictions[]`(양측 → contested 후보, sides 라벨 = `video.label_a/b`). 검증 워커 `{bundle_hints}` 블록 재료일 뿐이다(D-0064 쟁점 3).

이 모듈은 오케스트레이터를 import 하지 않는다(15 P1) — 가져오기·호스트 차단 판정은 호출자가 넘긴다.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.models import BundleSource, ReportBundle

BUNDLE_CLAIMS_FILE = "bundle_claims.json"
NOTE_PREFIX = "번들 이관"
_URL = re.compile(r"https?://[^\s)]+")
_QUOTED = re.compile(r"'([^']+)'|\"([^\"]+)\"|‘([^’]+)’")
_DATE = re.compile(r"(?<!\d)(\d{4})-(\d{2})(?:-(\d{2}))?(?!\d)")

Fetcher = Callable[[str], dict[str, str]]   # url → {title, publisher, published_at, body}
Blocked = Callable[[str], bool]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Citation(_Strict):
    """번들 출처 한 줄에서 읽은 것. 없는 칸은 빈 값(추측 금지)."""

    url: str = ""
    publisher: str = ""
    title: str = ""
    published_at: Optional[date] = None
    date_text: str = ""                 # 날짜 원문(월까지만이면 published_at 은 None)


class ResolvedArticle(_Strict):
    bundle_source_id: str
    url: str
    publisher: str
    headline: str
    published_at: date
    body: str
    filled_by: list[Literal["citation", "fetch"]]
    note: str


class Unresolved(_Strict):
    bundle_source_id: str
    raw: str
    reason: str                          # blocked_host · no_url · fetch_failed:<오류> · missing:<칸들>


def parse_citation(s: BundleSource) -> Citation:
    """번들 출처 → 인용 칸. url 칸이 인용 문자열이면 풀어 읽고, 순수 URL 이면 url 만. 번들 publisher·title 이 있으면 우선."""
    raw = s.url.strip()
    m = _URL.search(raw)
    url = m.group(0).rstrip(".,") if m else ""
    head = raw[: m.start()] if m else raw
    q = _QUOTED.search(head)
    title = next((g for g in q.groups() if g), "") if q else ""
    pub = head[: q.start()].strip(" ,(") if q else ""
    d = _DATE.search(head[q.end():] if q else head)
    day, dtext = None, ""
    if d:
        dtext = d.group(0)
        if d.group(3):
            try:
                day = date(int(d.group(1)), int(d.group(2)), int(d.group(3)))
            except ValueError:
                day = None
    return Citation(url=url, publisher=s.publisher or pub, title=s.title or title, published_at=day, date_text=dtext)


def resolve_sources(b: ReportBundle, *, fetch: Optional[Fetcher], blocked: Blocked) -> tuple[list[ResolvedArticle], list[Unresolved]]:
    """번들 출처 전부 → (기사 레코드 재료, 못 만든 것). fetch=None 이면 가져오지 않는다(--no-fetch)."""
    ok: list[ResolvedArticle] = []
    bad: list[Unresolved] = []
    for s in b.sources:
        c = parse_citation(s)
        if not c.url:
            bad.append(Unresolved(bundle_source_id=s.source_id, raw=s.url, reason="no_url"))
            continue
        if blocked(c.url):
            bad.append(Unresolved(bundle_source_id=s.source_id, raw=s.url, reason="blocked_host"))
            continue
        pub, head, day, body = c.publisher, c.title, c.published_at, ""
        filled: list[Literal["citation", "fetch"]] = ["citation"] if (pub or head or day) else []
        if fetch is not None:
            try:
                got = fetch(c.url)
            except Exception as ex:  # noqa: BLE001 — 네트워크·HTTP·파싱 오류 전부 사유로 남긴다(조용히 버리지 않음)
                bad.append(Unresolved(bundle_source_id=s.source_id, raw=s.url, reason=f"fetch_failed:{type(ex).__name__}: {str(ex)[:120]}"))
                continue
            body = got.get("body", "")
            head, pub = head or got.get("title", ""), pub or got.get("publisher", "")
            if day is None and got.get("published_at"):
                try:
                    day = date.fromisoformat(got["published_at"][:10])
                except ValueError:
                    day = None
            filled.append("fetch")
        missing = [k for k, v in (("body", body), ("headline", head), ("publisher", pub), ("published_at", day)) if not v]
        if missing:
            bad.append(Unresolved(bundle_source_id=s.source_id, raw=s.url,
                                  reason="missing:" + ",".join(missing) + ("" if fetch is not None else " (--no-fetch)")))
            continue
        assert day is not None
        ok.append(ResolvedArticle(bundle_source_id=s.source_id, url=c.url, publisher=pub, headline=head, published_at=day,
                                  body=body, filled_by=filled, note=f"{NOTE_PREFIX} {b.report.report_id} {s.source_id}"))
    return ok, bad


# ------------------------------------------------------------------ claims 후보
class HintSide(_Strict):
    party: str
    text: str


class BundleClaimHint(_Strict):
    """검증 워커에 주는 후보 하나 — 판정 재료가 아니다. 인용 근거가 소스 본문에 없으면 버려진다(judge)."""

    id: str
    kind: Literal["claim", "contested"]
    text: str
    sides: list[HintSide] = Field(default_factory=list)
    bundle_status: Optional[str] = None          # 번들 claims[].status — 참고만, 판정에 쓰지 않는다(D-0064 쟁점 3)
    bundle_confidence: Optional[str] = None


class BundleClaimsFile(_Strict):
    schema_version: Literal[1] = 1
    bundle_id: str
    hints: list[BundleClaimHint] = Field(default_factory=list)


def claim_hints(b: ReportBundle) -> BundleClaimsFile:
    hints: list[BundleClaimHint] = []
    for c in b.claims:
        hints.append(BundleClaimHint(id=f"bh_{len(hints) + 1:03d}", kind="claim", text=c.statement,
                                     bundle_status=c.status, bundle_confidence=c.confidence))
    for x in b.contradictions:
        v = x.video
        la, lb = (v.label_a, v.label_b) if v else ("", "")
        sides = [HintSide(party=la or "A측", text=x.side_a), HintSide(party=lb or "B측", text=x.side_b)]
        text = (f"{v.line_a} / {v.line_b}" if v and v.line_a and v.line_b else x.evidence) or x.side_a
        hints.append(BundleClaimHint(id=f"bh_{len(hints) + 1:03d}", kind="contested", text=text,
                                     sides=[s for s in sides if s.text]))
    return BundleClaimsFile(bundle_id=b.report.report_id, hints=hints)


def format_hints(f: BundleClaimsFile) -> str:
    """검증 워커 `{bundle_hints}` 블록 본문(파일이 있을 때만). 번들 status·confidence 는 넣지 않는다 — 판정을 기울이지 않게."""
    rows = []
    for h in f.hints:
        row = f"- [{h.id}] ({'논쟁' if h.kind == 'contested' else '주장'}) {h.text}"
        for s in h.sides:
            row += f"\n    · {s.party}: {s.text}"
        rows.append(row)
    return "\n".join(rows)


__all__ = ["BUNDLE_CLAIMS_FILE", "BundleClaimHint", "BundleClaimsFile", "Citation", "NOTE_PREFIX", "ResolvedArticle",
           "Unresolved", "claim_hints", "format_hints", "parse_citation", "resolve_sources"]
