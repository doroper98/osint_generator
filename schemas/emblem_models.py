"""휘장 레지스트리 데이터 계약 (v2.4.0, back_and_forth D-0029 작업 3, 07 §5, 13).

`assets/emblems/registry.json`: 기관별 `{file, license, restrictions[], decision, reason, source_url, fetched_at}`.
결정은 코드가 내린다(D5 Fable 전결, README §7.2): 위키미디어 `Restrictions`(insignia·trademarked·personality 등)가
하나라도 있으면 `flag_fallback` — 렌더러는 휘장 대신 `fallback_flag` 국기 뱃지를 그린다. `user_decision` 상태는 없다.
파일에 적힌 decision 이 규칙 결과와 다르면 로드 오류다(손으로 `use` 로 바꿔 우회할 수 없다).

v4.8.0 back_and_forth D-0109(사용자 결정 D98): 사용자 예외 `user_exception: "D98"` 가 있는 항목만 제한(restrictions)을
넘어 `use` 가 된다. 라이선스·파일 조건은 그대로다. 예외는 `exception_scope`(용도 한정 문구)와 함께 적어야 하고,
허용 예외 목록 `USER_EXCEPTIONS` 밖의 번호는 로드 오류다(다른 제한 휘장은 그대로 D5).
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


# 사용자 예외(DECISIONS 번호 → 휘장 id). v4.8.0 D98 = 청와대(대통령 표장) — 청와대·대통령실 언급 문장의 식별 표시, 무가공, 크레딧
USER_EXCEPTIONS: dict[str, frozenset[str]] = {"D98": frozenset({"cheongwadae"})}


def decide_emblem(restrictions: list[str], license: str, has_file: bool,
                  user_exception: Optional[str] = None) -> tuple[EmblemDecision, str]:
    """휘장 사용 결정(D5 Fable 전결). 제한 하나라도 → 국기(사용자 예외면 제한만 넘는다, D98). 라이선스 불허·파일 없음 → 국기."""
    if restrictions and user_exception is None:
        return "flag_fallback", "restrictions: " + ", ".join(restrictions)
    if not has_file:
        return "flag_fallback", "no_emblem_file"
    if not license_allowed(license):
        return "flag_fallback", f"license_not_allowed: {license}"
    if restrictions:
        return "use", f"user_exception {user_exception}: restrictions {', '.join(restrictions)} — 용도 한정"
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
    user_exception: Optional[str] = Field(default=None, pattern=r"^D\d+$")   # v4.8.0 D-0109 — 사용자 결정 번호(D98)
    exception_scope: Optional[str] = None                                     # 예외의 용도 한정 문구(필수 — 예외가 있으면)

    @model_validator(mode="after")
    def _decision_matches_rule(self) -> "EmblemEntry":
        if self.user_exception is not None and not self.exception_scope:
            raise ValueError(f"user_exception={self.user_exception} 에 exception_scope(용도 한정) 없음")
        want, _ = decide_emblem(self.restrictions, self.license, self.file is not None, self.user_exception)
        if want != self.decision:
            raise ValueError(f"decision={self.decision} 이 규칙 결과 {want} 와 다르다(restrictions={self.restrictions}, "
                             f"license={self.license!r}, file={self.file}) — 휘장 결정은 코드가 한다(D5)")
        return self


class EmblemRegistry(_Strict):
    schema_version: int = 1
    emblems: dict[str, EmblemEntry]

    @model_validator(mode="after")
    def _exceptions_known(self) -> "EmblemRegistry":
        bad = [f"{k}:{e.user_exception}" for k, e in self.emblems.items()
               if e.user_exception is not None and k not in USER_EXCEPTIONS.get(e.user_exception, frozenset())]
        if bad:
            raise ValueError(f"사용자 예외 목록(USER_EXCEPTIONS)에 없는 휘장 예외: {bad} — 다른 제한 휘장은 D5(국기 대체)")
        return self
