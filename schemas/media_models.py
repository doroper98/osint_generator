"""미디어 레지스트리 계약 (v2.5.5, D-0036 작업 2, 14 §2·§6·§9, C9).

`assets/media/media_registry.json` 한 파일이 사진·영상·컷아웃·기사 클리핑의 **권리와 화면 문구의 유일한 출처**다.
연출은 `mid` 만 가리키고, 화면 캡션·출처 줄·기사 조판 문구는 여기서 나온다(15 P3).
필드가 빠지면 로드 단계에서 실패하고(`engine.media_registry` 가 RightsError 로 올린다), 권리가 `rights_clear` 가
아니면 렌더 전 오류다(P6, C9 — `<미검증>` 라벨은 사실 검증용이지 권리 미확인 자산의 면죄부가 아니다).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

MediaKind = Literal["photo", "video", "cutout", "article"]   # video = clip 이벤트
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
    # 기사 클리핑(14 §9) — 우리 타이포로 매체명·날짜·헤드라인 번역만 조판(화면 캡처 금지)
    headline: Optional[str] = None
    hl: Optional[str] = None
    sub: Optional[str] = None
    note: Optional[str] = None

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
        if not self.verified_by.casualty_free:
            errs.append("사상자·시신 식별 자료는 쓰지 않는다(14 §2.2)")
        if errs:
            raise ValueError("; ".join(errs))
        return self

    def credit_line(self, fmt: str) -> str:
        """화면 출처 줄 — 형식은 rules media.credit_formats(종류별). 레지스트리 값으로만 만든다(P3)."""
        return fmt.replace("{file_note}", self.file_note).replace("{credit_author}", self.credit_author) \
            .replace("{license}", self.license)


class MediaRegistryFile(_Strict):
    schema_version: int
    assets: dict[str, MediaAsset]


class MediaAssets(RootModel[dict[str, MediaAsset]]):
    pass
