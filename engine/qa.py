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

# honesty·wording = v4.4.0 장르 루브릭(20 §9 — 차트 정직성·숫자 일치 / 용어 정의·투자 권유 표현, D-0090 작업 1)
Category = Literal["occlusion", "empty", "density", "color", "order", "media", "legibility", "camera", "style", "honesty", "wording"]


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


class QARubricItem(_Strict):
    """장르 루브릭 한 항목 판정(v4.4.0 D-0090 작업 1, 20 §9). item = rules genre_prompt.rubric_extra 번호(1부터)."""

    item: int = Field(ge=1)
    ok: bool
    evidence: str = Field(min_length=8)   # 근거 필수(AP-V6-8)


class QAVerdict(_Strict):
    schema_version: int = 1
    verdict: Literal["pass", "revise"]
    issues: list[QAIssue] = Field(default_factory=list)
    praise: list[str] = Field(default_factory=list)
    rubric: list[QARubricItem] = Field(default_factory=list)   # v4.4.0 — 기본 장르(지정학)는 비움. 그 밖은 항목 전부(워커 check_parsed)

    def rubric_missing(self, n: int) -> list[int]:
        """1..n 중 판정이 없거나 두 번 이상인 항목 번호."""
        seen = [r.item for r in self.rubric]
        return [i for i in range(1, n + 1) if seen.count(i) != 1] + sorted({i for i in seen if i > n})

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
    - checks 항목 id("offscreen" 등) → 그 항목 상세 문장(hard 검사 수정 루프). "id:상세" 꼴도 상세 문장으로"""
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
        elif ":" in r and r.split(":", 1)[0].strip() in by_check:   # "offscreen:마커 호르무즈 해협 t=185.1" — 검사 id + 상세
            out.add(("~", r.split(":", 1)[1]))
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


class QALoopRound(_Strict):
    """검수 루프 한 회차 = 연출 한 판(D-0049 쟁점 3). 파일 이름은 prev/ 기준(direction 은 프로젝트 루트)."""
    version: int                          # direction.v{version}.yaml
    checks_hard: int
    checks_file: str                      # prev/checks.v{n}.json
    sheet: str                            # prev/sheet.v{n}.jpg
    qa: Optional[str] = None              # prev/qa_verdict.v{k}.json (hard 검사가 남으면 검수 없음)
    qa_hard: Optional[int] = None
    qa_soft: Optional[int] = None
    revision: Optional[str] = None        # 이 판을 고친 prev/revision.v{m}.json


class QALoopPick(_Strict):
    version: int
    by: Literal["code", "human"]
    reason: str


class QALoopRecord(_Strict):
    """prev/qa_loop.json — 루프 이력(수정 워커 입력·게이트 ② 판 목록·provenance 의 공용 기록)."""
    schema_version: int = 1
    rounds: list[QALoopRound] = Field(default_factory=list)
    selected: Optional[QALoopPick] = None


def pick_best(rounds: list[QALoopRound], order: list[str]) -> QALoopRound:
    """rules qa_checks.loop_pick_order 사전식 최소. 검수 없는 판(hard 검사 잔존)은 검수 값 무한대. 동점이면 이른 회차(D-0049 구속 1)."""
    big = 10 ** 6

    def score(r: QALoopRound) -> tuple:
        vals = {"checks_hard": r.checks_hard, "qa_hard": big if r.qa_hard is None else r.qa_hard,
                "qa_soft": big if r.qa_soft is None else r.qa_soft}
        return tuple(vals[k] for k in order) + (r.version,)

    return min(rounds, key=score)


__all__ = ["Change", "QAIssue", "QALoopPick", "QALoopRecord", "QALoopRound", "QAVerdict", "Revision", "event_name",
           "pick_best", "resolve_refs", "unchanged_violations"]
