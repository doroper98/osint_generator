"""소스 인테이크 계약 (v3.2.0, docs/handoff/18 §2·§3, 16 §6, back_and_forth D-0051 작업 3).

- `intake/sources.json` = `SourcesFile` — 사용자가 준 기사·X 게시물·공문의 **소스 레코드**(18 §2).
  X 캡처는 캡처 판독 워커가 초안을 쓰고, 사용자가 계정·시각을 확인해야(`confirmed_by`) 검증 단계로 간다(18 §7).
- `intake/claims.json` = `ClaimsFile` — 검증 워커가 만든 **주장(claim)** 목록(18 §3-6). research·script 는 이 id 만 인용한다.
검증 상태 4종은 18 §2 `verification.status` 그대로. 영상 라벨(`<미검증>` 등)은 코드가 이 status 로 계산한다(D42).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceType = Literal["x_post", "article", "document"]
AccountClass = Literal["official_gov", "official_org", "journalist", "public_figure", "private", "unknown"]
VerificationStatus = Literal["verified", "corroborated", "unverified", "disputed"]
AttachedMedia = Literal["video", "photo", "none"]
SOURCE_ID = r"^src_[a-z0-9_]+$"
CLAIM_ID = r"^clm_[a-z0-9_]+$"
HANDLE = r"^@[A-Za-z0-9_]{1,15}$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceVerification(_Strict):
    """검증 결과(18 §2). checks = 통과한 확인 항목 이름(예: official_account, matches_src_art_0002)."""

    status: VerificationStatus
    checks: list[str] = Field(default_factory=list)
    notes: str = ""


class _SourceBase(_Strict):
    id: str = Field(pattern=SOURCE_ID)
    url: Optional[str] = None
    retrieved_at: date                                # 사용자가 준 날(캡처·붙여넣기 시점)
    lang: str = "ko"
    verification: Optional[SourceVerification] = None  # 검증 워커 전 = None
    confirmed_by: Optional[str] = None                # 사용자 확인(18 §7) — 비면 검증 단계로 못 간다
    confirmed_at: Optional[datetime] = None
    note: str = ""                                    # 사용자 메모

    @property
    def confirmed(self) -> bool:
        return bool(self.confirmed_by)


class XPostSource(_SourceBase):
    """X 게시물(18 §2). 입력은 텍스트 붙여넣기 또는 화면 캡처 — x.com 을 직접 열지 않는다(18 §1, 스크래핑 금지)."""

    type: Literal["x_post"]
    input: Literal["text", "capture"]
    account_name: str = Field(min_length=1)
    handle: str = Field(pattern=HANDLE)
    account_class: AccountClass = "unknown"           # 공식 계정 목록(rules/official_accounts.yaml)으로 코드가 정한다
    posted_at: Optional[datetime] = None              # 게시 시각(사건 시각과 구분, 18 §3-2). 캡처에 절대 시각이 없으면 사용자가 확인 때 채운다
    text_original: str = Field(min_length=1)
    text_ko: Optional[str] = None
    capture: Optional[str] = None                     # intake/screenshots/<id>.png (비공개 보관)
    attached_media: AttachedMedia = "none"
    deleted: bool = False                             # 삭제된 게시물(캡처 시점 보관, 18 §3-4)
    drafted_by: Optional[str] = None                  # 캡처 판독 워커가 쓴 초안이면 그 워커 이름

    @model_validator(mode="after")
    def _capture(self) -> "XPostSource":
        if self.input == "capture" and not self.capture:
            raise ValueError(f"{self.id}: 캡처 입력인데 capture 경로가 없다")
        if self.confirmed_by and self.posted_at is None:
            raise ValueError(f"{self.id}: 사용자 확인에는 게시 시각(posted_at)이 필요하다(18 §7)")
        return self


class CaptureDraft(_Strict):
    """캡처 판독 워커(vision) 출력 — X 게시물 화면 캡처 1장에서 읽은 것만(18 §1·§7).

    id·캡처 경로·account_class(공식 계정 목록)·사용자 확인 필드는 코드가 채운다. 화면에 없는 것은 null 로 두고
    `unreadable` 에 필드 이름을 적는다(추측 금지). 이 초안은 사용자 확인 전에는 검증 단계로 가지 않는다."""

    schema_version: Literal[1] = 1
    account_name: str = Field(min_length=1)
    handle: str = Field(pattern=HANDLE)
    posted_at: Optional[datetime] = None             # 화면의 절대 시각(예: "2:05 PM · Sep 20, 2026") → ISO. 상대 시각("3시간")이면 null
    posted_at_text: str = ""                         # 화면에 보이는 시각 문구 그대로
    text_original: str = Field(min_length=1)
    lang: str = Field(min_length=2)
    text_ko: Optional[str] = None                    # 원문이 한국어가 아니면 번역(과장·요약 왜곡 금지, 18 §5)
    attached_media: AttachedMedia = "none"
    deleted_notice: bool = False                     # 화면에 삭제·제한 안내가 보이면 true(18 §3-4)
    unreadable: list[str] = Field(default_factory=list)


class ArticleSource(_SourceBase):
    """기사(18 §2). 원문 장문 복제 금지 — 요지(key_facts)만."""

    type: Literal["article"]
    publisher: str = Field(min_length=1)
    headline_original: str = Field(min_length=1)
    headline_ko: Optional[str] = None
    published_at: date
    key_facts: list[str] = Field(min_length=1)
    source_ref: Optional[str] = None                 # 원문 대신 가리키는 기록 위치(예: "credits.yaml 보도 · 자료 — Reuters (9.4)")
    pending_source: Optional[str] = None             # 원문 위치를 아직 못 채운 사유(예: v3 이관 "원문 URL 미확보 — 매체·날짜만", D-0052 D51)


class DocumentSource(_SourceBase):
    """공문·보도자료·데이터(18 §1). 원문 파일은 intake/files/ 에 보관, 여기엔 요지만."""

    type: Literal["document"]
    issuer: str = Field(min_length=1)
    title: str = Field(min_length=1)
    published_at: Optional[date] = None
    file: Optional[str] = None
    key_facts: list[str] = Field(min_length=1)


SourceRecord = Annotated[Union[XPostSource, ArticleSource, DocumentSource], Field(discriminator="type")]


class SourcesFile(_Strict):
    schema_version: Literal[1] = 1
    sources: list[SourceRecord] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique(self) -> "SourcesFile":
        ids = [s.id for s in self.sources]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            raise ValueError(f"소스 id 중복: {dup}")
        return self

    def by_id(self) -> dict[str, Union[XPostSource, ArticleSource, DocumentSource]]:
        return {s.id: s for s in self.sources}


class ClaimSide(_Strict):
    """분쟁 사안의 한쪽 입장(18 §3-5) — 누가 무엇을 주장하나, 어느 소스로."""

    party: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)


class Claim(_Strict):
    """주장 하나(18 §3-6). status 는 검증 워커의 코드 대조 결과 — LLM 이 정하지 않는다(D-0051 작업 6)."""

    claim_id: str = Field(pattern=CLAIM_ID)
    text: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    status: VerificationStatus
    contested: bool = False
    sides: Optional[list[ClaimSide]] = None
    event_date: Optional[date] = None                 # 사건일(날짜 배지) — 게시일과 다를 수 있다(18 §3-2)
    checks: list[str] = Field(default_factory=list)   # 코드 판정 근거(quote_match:<src>·official:<src>·independent_origins:N …)
    attributed_only: bool = False                     # 근거가 전부 "~라고 주장/said" 인용 — 사실이 아니라 주장의 존재만 확인(D-0054 B)
    notes: str = ""

    @model_validator(mode="after")
    def _contested(self) -> "Claim":
        if self.contested and len(self.sides or []) < 2 and self.status != "unverified":
            raise ValueError(f"{self.claim_id}: 분쟁 사안인데 양측 입장(sides ≥ 2)이 없으면 unverified 여야 한다(18 §3-5)")
        return self


class ClaimsFile(_Strict):
    schema_version: Literal[1] = 1
    claims: list[Claim] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique(self) -> "ClaimsFile":
        ids = [c.claim_id for c in self.claims]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            raise ValueError(f"claim id 중복: {dup}")
        return self

    def ids(self) -> set[str]:
        return {c.claim_id for c in self.claims}

    def by_id(self) -> dict[str, Claim]:
        return {c.claim_id: c for c in self.claims}


class OfficialAccount(_Strict):
    """공식 계정 한 줄(`rules/official_accounts.yaml`, 18 §3-1). 출처 URL·확인 방법·확인일이 없으면 등재할 수 없다."""

    handle: str = Field(pattern=HANDLE)
    name: str = Field(min_length=1)
    name_ko: str = Field(min_length=1)
    account_class: Literal["official_gov", "official_org"]
    country: Optional[str] = None
    source_url: str = Field(pattern=r"^https://")
    check_method: Literal["official_site", "wikidata_P2002"]
    checked_on: date


class OfficialAccountsFile(_Strict):
    schema_version: Literal[1] = 1
    accounts: list[OfficialAccount] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique(self) -> "OfficialAccountsFile":
        keys = [a.handle.lower() for a in self.accounts]
        dup = sorted({k for k in keys if keys.count(k) > 1})
        if dup:
            raise ValueError(f"공식 계정 핸들 중복: {dup}")
        return self

    def lookup(self, handle: str) -> Optional[OfficialAccount]:
        """핸들(대소문자 무시, X 핸들 규칙)로 찾기. 없으면 None — 호출자는 unknown 으로 둔다."""
        h = handle.strip().lower()
        h = h if h.startswith("@") else "@" + h
        return next((a for a in self.accounts if a.handle.lower() == h), None)


class EvidenceQuote(_Strict):
    """검증 LLM 이 댄 근거 하나 — 그 소스 본문의 짧은 연속 인용과 입장(D-0052 D50). 인용 일치는 코드가 확인한다."""

    source_id: str = Field(pattern=SOURCE_ID)
    quote: str = Field(min_length=1)
    stance: Literal["supports", "contradicts"]


class ClaimCandidate(_Strict):
    """검증 LLM 의 주장 후보. id·status 는 코드가 매긴다(LLM 이 정하지 않는다)."""

    text: str = Field(min_length=1)
    evidence: list[EvidenceQuote] = Field(min_length=1)
    event_date: Optional[date] = None
    contested: bool = False
    sides: Optional[list[ClaimSide]] = None


class VerifyDraft(_Strict):
    """검증 워커(verify_sources) 출력 — `intake/verify_draft.json`. 코드 판정 → `claims.json`."""

    schema_version: Literal[1] = 1
    claims: list[ClaimCandidate] = Field(min_length=1)
    summary: str = ""                                # 대조 결과 요약(사람이 읽는 메모 — 판정에 쓰지 않는다)


def check_claim_sources(claims: ClaimsFile, sources: SourcesFile) -> list[str]:
    """claims 가 가리키는 소스 id 가 sources.json 에 있는가(sides 포함). 없으면 오류 문구."""
    have = set(sources.by_id())
    out: list[str] = []
    for c in claims.claims:
        refs = list(c.source_ids) + [s for side in c.sides or [] for s in side.source_ids]
        miss = sorted(set(refs) - have)
        if miss:
            out.append(f"{c.claim_id}: sources.json 에 없는 소스 {miss}")
    return out


__all__ = ["AccountClass", "CaptureDraft", "ClaimCandidate", "EvidenceQuote", "VerifyDraft", "OfficialAccount", "OfficialAccountsFile", "ArticleSource", "Claim", "ClaimSide", "ClaimsFile", "DocumentSource", "SourceRecord",
           "SourceVerification", "SourcesFile", "VerificationStatus", "XPostSource", "check_claim_sources"]
