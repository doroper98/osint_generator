"""휘장 레지스트리 데이터 계약 (v2.4.0, back_and_forth D-0029 작업 3, 07 §5, 13).

`assets/emblems/registry.json`: 기관별 `{file, license, restrictions[], decision, reason, source_url, fetched_at}`.
결정은 코드가 내린다(D5 Fable 전결, README §7.2): 위키미디어 `Restrictions`(insignia·trademarked·personality 등)가
하나라도 있으면 `flag_fallback` — 렌더러는 휘장 대신 `fallback_flag` 국기 뱃지를 그린다. `user_decision` 상태는 없다.
파일에 적힌 decision 이 규칙 결과와 다르면 로드 오류다(손으로 `use` 로 바꿔 우회할 수 없다).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


EmblemDecision = Literal["use", "flag_fallback"]
ALLOWED_LICENSE_PREFIXES: tuple[str, ...] = ("public domain", "pd", "cc0", "cc by ", "cc-by-", "kogl type 1")


def license_allowed(lic: str) -> bool:
    """07 §3.2 허용 라이선스: PD·CC0·CC BY(1.0~4.0)·KOGL 제1유형. CC BY-SA 는 불허(파생물 검토 필요)."""
    s = lic.strip().lower()
    if "sa" in s.replace("-", " ").split():
        return False
    return s.startswith(ALLOWED_LICENSE_PREFIXES) or s == "cc by"


def decide_emblem(restrictions: list[str], license: str, has_file: bool) -> tuple[EmblemDecision, str]:
    """휘장 사용 결정(D5 Fable 전결). 제한 하나라도 → 국기. 라이선스 불허·파일 없음 → 국기."""
    if restrictions:
        return "flag_fallback", "restrictions: " + ", ".join(restrictions)
    if not has_file:
        return "flag_fallback", "no_emblem_file"
    if not license_allowed(license):
        return "flag_fallback", f"license_not_allowed: {license}"
    return "use", "no_restrictions"


class EmblemEntry(_Strict):
    file: Optional[str] = None          # 프로젝트 assets/emblems/ 아래 파일명. flag_fallback 이면 받지 않는다
    title: Optional[str] = None         # Commons File: 제목
    license: str = ""
    author: str = ""
    restrictions: list[str] = Field(default_factory=list)
    decision: EmblemDecision
    reason: str = Field(min_length=1)
    fallback_flag: str = Field(pattern=r"^[a-z]{2}$")
    source_url: str = ""
    fetched_at: str = ""

    @model_validator(mode="after")
    def _decision_matches_rule(self) -> "EmblemEntry":
        want, _ = decide_emblem(self.restrictions, self.license, self.file is not None)
        if want != self.decision:
            raise ValueError(f"decision={self.decision} 이 규칙 결과 {want} 와 다르다(restrictions={self.restrictions}, "
                             f"license={self.license!r}, file={self.file}) — 휘장 결정은 코드가 한다(D5)")
        return self


class EmblemRegistry(_Strict):
    schema_version: int = 1
    emblems: dict[str, EmblemEntry]
