"""시각 검수 판정·연출 수정 계약 (v3.1.0, docs/handoff/17 §4.3·§5.5, back_and_forth D-0047 작업 7).

- `QAVerdict`: 시각 검수 LLM 출력. evidence 없는 지적은 무효(AP-V6-8) — 모델이 거부한다.
  검수자는 연출 파일을 고치지 않는다(AP-V6-11) — fix 는 제안 문장뿐이다.
- `Revision`: 연출 수정 LLM 출력 = 수정된 direction 전체 + changelog(지적 → 바꾼 것). 지적받지 않은 부분은 바꾸지 않는다
  (`unchanged_violations` 로 코드가 검사, 17 §5.5 회귀 방지).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
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


def event_name(e: dict) -> str:
    """이벤트 이름 — mid·label·tag·패널 제목(data.title)·title 순. 검수 event_ref("타입:이름")·frames.json 과 같은 규칙."""
    return str(e.get("mid") or e.get("label") or e.get("tag") or (e.get("data") or {}).get("title") or e.get("title") or "")


def _key(e: dict) -> str:
    """이벤트 표지 — 타입|종류|이름|시작 앵커. 같은 이름이 여러 번 나와도 구별된다."""
    return f"{e.get('type')}|{e.get('kind', '')}|{event_name(e)}|{json.dumps(e.get('start'), ensure_ascii=False, sort_keys=True)}"


FRAME_RE = re.compile(r"^p_\d+\.\d+")


def resolve_refs(refs: set[str], frames: Optional[dict] = None, checks: Optional[dict] = None) -> set[tuple[str, str]]:
    """지적 표지 → (타입, 이름) 집합. 타입 "*" = 이름 일치 또는 표지 부분 문자열, "~" = 검사 상세 문장에 이름이 나옴.
    - "badge:부산에서 출항"·"badge|flag|부산에서 출항|…" → (badge, 부산에서 출항)
    - "p_0136.97" → frames.json 그 컷에 활성인 이벤트 전부(검수는 컷을 보고 지적한다 — 17 §4.1)
    - checks 항목 id("offscreen" 등) → 그 항목 상세 문장(hard 검사 수정 루프)"""
    out: set[tuple[str, str]] = set()
    by_file = {Path(f["file"]).stem: f for f in (frames or {}).get("frames", [])}
    by_check = {i["id"]: i.get("details", []) for i in (checks or {}).get("items", [])}
    for r in refs:
        r = r.strip()
        if not r:
            continue
        m = FRAME_RE.match(r)
        if m and m.group(0) in by_file:
            out |= {(ev["type"], event_name(ev)) for ev in by_file[m.group(0)]["events"]}
        elif r in by_check:
            out |= {("~", d) for d in by_check[r]}
        elif "|" in r:
            parts = r.split("|")
            out.add((parts[0], parts[2] if len(parts) > 2 else parts[-1]))
        elif ":" in r and r.split(":", 1)[0].isidentifier():
            t, n = r.split(":", 1)
            out.add((t.strip(), n.strip()))
        out.add(("*", r))
    return out


def _touched(e: dict, key: str, touched: set[tuple[str, str]]) -> bool:
    name = event_name(e)
    for t, n in touched:
        if t == "*":
            if n == name or n in key:
                return True
        elif t == "~":
            if name and name in n:
                return True
        elif t == e.get("type") and n == name:
            return True
    return False


def unchanged_violations(before: Direction, after: Direction, touched: set[str],
                         frames: Optional[dict] = None, checks: Optional[dict] = None) -> list[str]:
    """지적받지 않은 이벤트가 바뀌었거나 사라졌으면 목록(17 §5.5). touched = changelog issue_ref + 검수 frame·event_ref.
    frames(prev/frames.json)·checks(prev/checks.json)로 컷·검사 지적을 이벤트로 푼다(resolve_refs)."""
    tset = resolve_refs(touched, frames, checks)
    b = {_key(e): e for e in before.events}
    a = {_key(e): e for e in after.events}
    out: list[str] = []
    for k, e in b.items():
        if _touched(e, k, tset):
            continue
        if k not in a:
            out.append(f"지적 없이 삭제: {k}")
        elif a[k] != e:
            out.append(f"지적 없이 변경: {k}")
    return out


__all__ = ["Change", "QAIssue", "QAVerdict", "Revision", "event_name", "resolve_refs", "unchanged_violations"]
