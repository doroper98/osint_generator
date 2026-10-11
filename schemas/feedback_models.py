"""사용자 의견 원장 모델 (v5.22.0, back_and_forth D-0200 — 사용자 지시 "내가 코멘트 한 사항들은 모두 기록되고 재발이 되면 안돼").

정본은 `rules/user_feedback.yaml`. `docs/handoff/USER_FEEDBACK_LEDGER.md` 표는 `tools/feedback_ledger.py` 가 만든다.
"""

from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

UF_ID = re.compile(r"^UF-\d{2,3}$")


class FeedbackGuard(BaseModel):
    """재발 방지 장치 — 재발하면 실제로 실패를 내는 것만. check = engine.checks HARD·WARN id(스케치 SK-*), test = 경로::클래스::함수,
    rule = rules/video_rules.yaml 점 경로, code = 파이썬 점 경로 함수(예외를 던지는 게이트·검증기)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["check", "test", "rule", "code"]
    ref: str = Field(min_length=1)


class FeedbackEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    project: str = Field(min_length=1)
    at: str = Field(min_length=1)
    quote: str = Field(min_length=1)                       # 사용자 원문 그대로(소급 항목에 원문이 없으면 quote_kind summary)
    quote_kind: Literal["verbatim", "summary"] = "verbatim"
    category: str = Field(min_length=1)
    guards: list[FeedbackGuard] = Field(default_factory=list)
    status: Literal["open", "guarded"]
    recurs_of: Optional[str] = None                        # 재발이면 원래 번호
    decision: str = Field(min_length=1)                    # D 번호·AP 번호
    source: Optional[str] = None                           # 소급 항목의 출처(DECISIONS 행·AP)

    @model_validator(mode="after")
    def _shape(self) -> "FeedbackEntry":
        if not UF_ID.match(self.id):
            raise ValueError(f"{self.id}: 번호는 UF-NN")
        if self.recurs_of is not None and not UF_ID.match(self.recurs_of):
            raise ValueError(f"{self.id}: recurs_of 는 UF-NN")
        if (self.status == "guarded") != bool(self.guards):
            raise ValueError(f"{self.id}: status guarded ⇔ 장치 1개 이상(장치 없음 = open)")
        return self


class FeedbackLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    entries: list[FeedbackEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def _ids(self) -> "FeedbackLedger":
        ids = [e.id for e in self.entries]
        if len(set(ids)) != len(ids):
            raise ValueError("UF 번호 중복")
        nums = [int(i[3:]) for i in ids]
        if nums != sorted(nums):
            raise ValueError("UF 번호는 오름차순(append-only)")
        known = set(ids)
        for e in self.entries:
            if e.recurs_of is not None and (e.recurs_of not in known or int(e.recurs_of[3:]) >= int(e.id[3:])):
                raise ValueError(f"{e.id}: recurs_of {e.recurs_of} 는 앞선 원장 번호여야 한다")
        return self

    def open_entries(self) -> list[FeedbackEntry]:
        return [e for e in self.entries if e.status == "open"]
