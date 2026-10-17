"""미디어 레지스트리 계약 (v2.5.5, D-0036 작업 2, 14 §2·§6·§9, C9).

`assets/media/media_registry.json` 한 파일이 사진·영상·컷아웃·기사 클리핑의 **권리와 화면 문구의 유일한 출처**다.
연출은 `mid` 만 가리키고, 화면 캡션·출처 줄·기사 조판 문구는 여기서 나온다(15 P3).
필드가 빠지면 로드 단계에서 실패하고(`engine.media_registry` 가 RightsError 로 올린다), 권리가 `rights_clear` 가
아니면 렌더 전 오류다(P6, C9 — `<미검증>` 라벨은 사실 검증용이지 권리 미확인 자산의 면죄부가 아니다).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

MediaKind = Literal["photo", "video", "cutout", "article", "inset"]   # video = clip 이벤트, inset = flight.inset 위성 타일(v7.3.0 D-0206)
RightsStatus = Literal["rights_clear", "restricted", "unverified"]
FILE_PHOTO_PREFIXES: tuple[str, ...] = ("자료사진", "자료 영상")   # 14 §2.3 저널리즘 표기


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MediaVerification(_Strict):
    """사람 검수 체크리스트(14 §2.2·§10.3-3). 사상자·시신 식별 여부는 구간 단위로 확인한다."""

    by: str = Field(min_length=1)                  # 누가(사용자 라운드·검수 세션)
    on: str = Field(min_length=1)                  # 언제(YYYY-MM-DD)
    casualty_free: bool                            # 사상자·시신이 식별되지 않음
    segment_checked: Optional[tuple[float, float]] = None   # 영상: 확인한 구간(= segment)
    relevance: str = Field(min_length=1)           # 문장이 말하는 대상과 맞는가(관련성 없는 자료는 넣지 않는다, 14 §10.3-3)


class MediaTool(_Strict):
    """가공 기록(14 §3, C9·G4-10) — 원본 의미를 바꾸는 보정(합성·삭제)은 없다."""

    name: str
    params: dict[str, object] = Field(default_factory=dict)


class SourceVariant(_Strict):
    """정본(Commons) 대신 쓴 1차 출처 원본(v3.0.0, back_and_forth D-0045, D43). 정본 url·source_hash 는 고치지 않는다.
    가공은 이 원본에서 하되 정본 segment 를 쓰고, 두 원본의 시각 차이는 offset_sec 로만 적는다."""

    source: Literal["dvids"]
    url: str = Field(min_length=1)                  # 1차 출처 페이지
    id: str = Field(min_length=1)
    file_url: str = Field(min_length=1)             # 받은 원본 파일 URL
    file: str = Field(min_length=1)                 # project media/ 안 원본 파일 이름
    md5: str = Field(min_length=32, max_length=32)
    license: str = Field(min_length=1)
    duration: float = Field(gt=0)
    offset_sec: float = 0.0                         # 정본 시각 t ↔ 이 원본 시각 t + offset_sec
    retrieved_at: str = Field(min_length=1)
    match: str = Field(min_length=1)                # 같은 영상 확인 근거(프레임 대응표 경로)
    note: str = Field(min_length=1)


class MediaAsset(_Strict):
    kind: MediaKind
    title: str = Field(min_length=1)               # 원본 파일 제목(Commons File:…) 또는 기사 원제
    license: str = Field(min_length=1)
    author: str = Field(min_length=1)              # 원 저작자 표기(extmetadata Artist 정제)
    credit_author: str = Field(min_length=1)       # 화면 출처 줄의 짧은 이름(예: U.S. Navy)
    date: str = Field(min_length=1)
    url: Optional[str] = None                      # 원본 페이지 URL
    source_ref: Optional[str] = None               # url 이 아직 없을 때 출처가 적힌 곳(예: credits.yaml 행) — D-0037
    pending_source: Optional[str] = None           # url 이 비어 있는 이유·채울 Phase(예: "6.95") — 채워지면 지운다
    caption: str = Field(min_length=1)             # 화면 캡션(사진·영상) / 라벨(컷아웃) / 매체명(기사)
    file_note: str = Field(min_length=1)           # 화면 날짜 표기(예: 자료사진 · 2023. 05) / 기사 날짜
    depicts: list[str] = Field(min_length=1)       # 사건·장소·인물·장비
    is_file_photo: bool                            # 해당 사건 당일 자료가 아님 → file_note 가 "자료사진/자료 영상"으로 시작
    verified_by: MediaVerification
    rights_status: RightsStatus
    retrieved_at: str = Field(min_length=1)
    tool: MediaTool
    source_hash: Optional[str] = None              # 원본 파일 md5(기사는 없음)
    file: Optional[str] = None                     # 렌더가 읽는 가공 파일(project media/ 기준) — 영상은 클립 키
    duration: Optional[float] = None
    segment: Optional[tuple[float, float]] = None  # 영상 사용 구간(초)
    source_variants: list[SourceVariant] = Field(default_factory=list)   # v3.0.0 optional(C3) — D-0045
    # 기사 클리핑(14 §9) — 우리 타이포로 매체명·날짜·헤드라인 번역만 조판(화면 캡처 금지)
    headline: Optional[str] = None
    hl: Optional[str] = None
    sub: Optional[str] = None
    note: Optional[str] = None
    headline_original: Optional[str] = None   # v5.1.0 D-0121 §C·D-0126 Q6 A — 원문 헤드라인 verbatim(원문 언어). 없으면 번역 헤드라인 + "헤드라인 번역"
    # v5.21.0 back_and_forth D-0177(사용자 결정 D172) — 통신사 사진 "보도 인용"(B). 인용한 기사(press_of = 기사 mid)에 실린 사진 1장,
    # 그 기사 카드의 프레스 칸에서만. restricted + 범주 예외(schemas.emblem_models USER_EXCEPTIONS press_quote) + 크레딧 3곳 + 배포 전 재확인
    press_of: Optional[str] = None        # 이 사진이 실린 기사(레지스트리 kind article mid)
    agency: Optional[str] = None          # 통신사(예: Reuters) — 카드 안 "사진: <통신사> via <매체>"
    photo_url: Optional[str] = None       # 받은 사진 원본 URL(url = 기사 페이지)
    user_exception: Optional[str] = Field(default=None, pattern=r"^(D\d+|U\d{8})$")
    exception: Optional[str] = None       # 예외 문구(결정 번호·근거·"공개 배포 전 재확인")

    @model_validator(mode="after")
    def _by_kind(self) -> "MediaAsset":
        errs: list[str] = []
        if not self.url and not self.source_ref:
            errs.append("url 과 source_ref 중 하나는 있어야 한다(D-0037)")
        if not self.url and not self.pending_source:
            errs.append("url 이 비었으면 pending_source(비어 있는 이유·채울 Phase)를 적는다(D-0037)")
        if self.url and self.pending_source:
            errs.append("url 이 채워졌으면 pending_source 를 지운다(D-0037)")
        if self.is_file_photo and not self.file_note.startswith(FILE_PHOTO_PREFIXES):
            errs.append(f"file_photo_label_required: 자료사진·자료 영상 표기 없음 (file_note={self.file_note!r}, 14 §2.3)")
        if self.kind == "article":
            for f in ("headline", "sub", "note"):
                if not getattr(self, f):
                    errs.append(f"기사 필드 없음: {f}")
            if self.hl and self.headline and self.hl not in self.headline:
                errs.append(f"기사 hl 이 헤드라인에 없다: {self.hl!r}")
        elif self.headline_original is not None:
            errs.append("headline_original 은 기사(kind article)만")
        else:
            if not self.file:
                errs.append("가공 파일(file) 없음")
            if not self.source_hash:
                errs.append("원본 해시(source_hash) 없음")
        if self.kind == "video":
            if self.segment is None or self.duration is None:
                errs.append("영상은 segment·duration 필수")
            elif not 0 <= self.segment[0] < self.segment[1] <= self.duration:
                errs.append(f"segment {self.segment} 가 영상 길이 {self.duration} 밖")
            if self.verified_by.segment_checked != self.segment:
                errs.append(f"사상자 식별 체크 구간 {self.verified_by.segment_checked} ≠ 사용 구간 {self.segment} (14 §2.2)")
        errs += self._press_quote_errors()
        if not self.verified_by.casualty_free:
            errs.append("사상자·시신 식별 자료는 쓰지 않는다(14 §2.2)")
        if errs:
            raise ValueError("; ".join(errs))
        return self

    def _press_quote_errors(self) -> list[str]:
        """보도 인용(B) 사진의 기록 칸(D-0177 §1·§2). 사용자 예외는 보도 인용 범주만 — 다른 restricted 사진은 지금처럼 렌더 거부."""
        from schemas.emblem_models import press_exception_ok  # noqa: PLC0415

        errs: list[str] = []
        if self.press_of is None:
            if self.user_exception is not None or self.agency is not None:
                errs.append("user_exception·agency 는 보도 인용 사진(press_of)만 — 미디어의 사용자 예외는 보도 인용 범주뿐(D-0177)")
            return errs
        if self.kind != "photo":
            errs.append(f"보도 인용(press_of)은 사진만: kind={self.kind}")
        if self.rights_status != "restricted":
            errs.append(f"보도 인용 사진은 rights_status restricted 로 적는다(권리 확인 자산이 아니다): {self.rights_status}")
        if not press_exception_ok(self.user_exception):
            errs.append(f"보도 인용 사진의 사용자 예외가 press_quote 범주가 아니다: {self.user_exception!r}(USER_EXCEPTIONS)")
        for f in ("agency", "photo_url", "exception", "url"):
            if not getattr(self, f):
                errs.append(f"보도 인용 사진 기록 없음: {f}")
        if self.exception and "재확인" not in self.exception:
            errs.append("보도 인용 exception 문구에 '공개 배포 전 재확인' 이 없다(D-0177 §2)")
        return errs

    def credit_line(self, fmt: str) -> str:
        """화면 출처 줄 — 형식은 rules media.credit_formats(종류별). 레지스트리 값으로만 만든다(P3)."""
        return fmt.replace("{file_note}", self.file_note).replace("{credit_author}", self.credit_author) \
            .replace("{license}", self.license)


class MediaRegistryFile(_Strict):
    schema_version: int
    assets: dict[str, MediaAsset]

    @model_validator(mode="after")
    def _press_of_article(self) -> "MediaRegistryFile":
        bad = [f"{k}→{a.press_of}" for k, a in self.assets.items()
               if a.press_of is not None and (a.press_of not in self.assets or self.assets[a.press_of].kind != "article")]
        if bad:
            raise ValueError(f"보도 인용 사진의 press_of 가 레지스트리 기사(kind article)가 아니다: {bad}")
        return self


class MediaAssets(RootModel[dict[str, MediaAsset]]):
    pass


class MediaNote(_Strict):
    """v5.19.0 D-0163 §2 — 문장 하나의 미디어 사유(사람·에이전트가 적는다, LLM 연출이 아니다).
    photo = 사진을 고르지 못한 이유(검색어·결과·라이선스 탈락), article = 기사 카드 후보를 연출에서 쓰지 않은 이유,
    press_quote = 그 문장의 기사 카드에 보도 인용(B) 통신사 사진을 쓴다(v5.21.0 — 권리 통과 풀 검색 기록 0건일 때만)."""

    photo: Optional[str] = Field(default=None, min_length=4)
    article: Optional[str] = Field(default=None, min_length=4)
    press_quote: Optional[str] = Field(default=None, min_length=4)   # v5.21.0 D-0177 §4 — 보도 인용(B) 사진을 쓰는 이유·사진(검색 기록 통과 0 필수)


class MediaNotes(_Strict):
    """`projects/<pid>/media_notes.yaml`(git 추적) — 미디어 계획 표(게이트 ①)·[article-unused] 검사가 읽는다.
    문장 id 는 `{장면}_{순번}`(원고 기준). 원고에 없는 문장 id = 오류(낡은 사유, P6)."""

    schema_version: Literal[1] = 1
    project_photo: Optional[str] = Field(default=None, min_length=4)   # 사진 후보 문장이 하나도 없을 때의 사유(영상 전체)
    sentences: dict[str, MediaNote] = Field(default_factory=dict)


class MediaSearch(_Strict):
    """`tools/media_fetch.py search --log` 한 번(풀 하나)의 결과 요약 — 찾은 수·권리 통과 수·상위 제목."""

    sid: str = Field(min_length=1)
    query: str = Field(min_length=1)
    pool: str = Field(min_length=1)
    on: str = Field(min_length=10)          # YYYY-MM-DD
    found: int = Field(ge=0)
    passed: int = Field(ge=0)
    top: list[str] = Field(default_factory=list)   # 통과 후보 제목(최대 5)
    rejected: list[str] = Field(default_factory=list)   # 탈락 사유 요약(라이선스·제한)

    @model_validator(mode="after")
    def _counts(self) -> "MediaSearch":
        if self.passed > self.found:
            raise ValueError(f"{self.sid}: 통과 {self.passed} > 찾은 수 {self.found}")
        return self


class MediaSearchLog(_Strict):
    """`projects/<pid>/media_search.json`(git 추적) — 문장별 사진 검색 기록(게이트 ① 미디어 계획 표의 '찾은 수/통과 수')."""

    schema_version: Literal[1] = 1
    searches: list[MediaSearch] = Field(default_factory=list)
