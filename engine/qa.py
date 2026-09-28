"""시각 검수 판정·연출 수정 계약 (v3.1.0, docs/handoff/17 §4.3·§5.5, back_and_forth D-0047 작업 7).

- `QAVerdict`: 시각 검수 LLM 출력. evidence 없는 지적은 무효(AP-V6-8) — 모델이 거부한다.
  검수자는 연출 파일을 고치지 않는다(AP-V6-11) — fix 는 제안 문장뿐이다.
- `Revision`: 연출 수정 LLM 출력 = 수정된 direction 전체 + changelog(지적 → 바꾼 것). 지적받지 않은 부분은 바꾸지 않는다
  (`unchanged_violations` 로 코드가 검사, 17 §5.5 회귀 방지).
"""

from __future__ import annotations

import json
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from engine.direction import Direction

Category = Literal["occlusion", "empty", "density", "color", "order", "media", "legibility", "camera", "style"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QAFix(_Strict):
    event_ref: str = Field(min_length=1)   # 예: "badge:부산에서 출항", "shot:3", "panel:relation"
    suggest: str = Field(min_length=1)


class QAIssue(_Strict):
    frame: str = Field(min_length=1)       # 예: "p_0184.20" (prev/frames.json file 이름)
    severity: Literal["hard", "soft"]
    category: Category
    evidence: str = Field(min_length=8)    # 근거 없는 지적은 무시(AP-V6-8) — 짧은 한두 단어는 거부
    fix: Optional[QAFix] = None


class QAVerdict(_Strict):
    schema_version: int = 1
    verdict: Literal["pass", "revise"]
    issues: list[QAIssue] = Field(default_factory=list)
    praise: list[str] = Field(default_factory=list)

    def hard_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "hard")


class Change(_Strict):
    issue_ref: str = Field(min_length=1)   # QAVerdict issues 의 frame·event_ref, 또는 checks 항목 id
    change: str = Field(min_length=1)


class Revision(_Strict):
    schema_version: int = 1
    direction: Direction
    changelog: list[Change] = Field(min_length=1)


def _key(e: dict) -> str:
    """이벤트 표지 — 타입|종류|이름(mid·label·tag·패널 제목)|시작 앵커. 같은 이름이 여러 번 나와도 구별된다."""
    name = e.get("mid") or e.get("label") or e.get("tag") or (e.get("data") or {}).get("title", "")
    return f"{e.get('type')}|{e.get('kind', '')}|{name}|{json.dumps(e.get('start'), ensure_ascii=False, sort_keys=True)}"


def unchanged_violations(before: Direction, after: Direction, touched: set[str]) -> list[str]:
    """지적받지 않은 이벤트가 바뀌었으면 목록(17 §5.5). touched = changelog 가 가리키는 이벤트 키(부분 문자열 매칭)."""
    b = {_key(e): e for e in before.events}
    a = {_key(e): e for e in after.events}
    out: list[str] = []
    for k, e in b.items():
        hit = any(t and (t in k) for t in touched)
        if hit:
            continue
        if k not in a:
            out.append(f"지적 없이 삭제: {k}")
        elif a[k] != e:
            out.append(f"지적 없이 변경: {k}")
    return out


__all__ = ["Change", "QAIssue", "QAVerdict", "Revision", "unchanged_violations"]
