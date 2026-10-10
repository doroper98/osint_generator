"""원고 린트 면제 목록 (v5.17.0, back_and_forth D-0168, DECISIONS D162).

`projects/<pid>/lint_waivers.yaml`(git 추적 — 결정 기록). 원고가 승인된 **뒤에** 생긴 문체·흐름 규칙에만,
(kind, sid, text_sha1) **정확 일치**로만 오류를 통과시킨다. 나머지 오류는 지금처럼 막는다(P6).
- kind 는 `rules script_grammar.lint_waivable` 안에만. 그 밖(AI 상투 문구·출처·수치·발음 등) = 로드 오류.
- rule_since 는 CHANGELOG 태그, script_approved 는 그 태그 날짜보다 앞이어야 한다(아니면 로드 오류).
- 낡은 면제(일치하는 오류가 더는 없음, 원고 text 가 바뀌어 sha1 불일치) = 오류 — 목록을 정리한다.
plan(`script.plan`)과 린트 CLI(`script.lint`, 게이트 ① 화면)가 같은 함수를 쓴다.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from rules import load_rules
from script.schema import Script

REPO = Path(__file__).resolve().parent.parent
FILE = "lint_waivers.yaml"
TAG_RE = re.compile(r"^## \[v(\d+\.\d+\.\d+)\] — (\d{4}-\d{2}-\d{2})", re.M)


class LintWaiverError(ValueError):
    """면제 목록 로드·적용 오류(면제 불가 kind, 날짜 조건, 낡은 면제)."""


class LintWaiver(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    sid: str                     # 문장 id, 전체 규칙은 "-"
    text_sha1: str = Field(pattern=r"^[0-9a-f]{40}$")
    rule_since: str = Field(pattern=r"^v\d+\.\d+\.\d+$")
    script_approved: dt.date
    reason: str = Field(min_length=1)
    decided_by: str = Field(pattern=r"^D-\d{4}$")


class LintWaivers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    waivers: list[LintWaiver]


def changelog_dates(text: str | None = None) -> dict[str, dt.date]:
    """CHANGELOG 헤더 `## [vX.Y.Z] — YYYY-MM-DD` → {"vX.Y.Z": 날짜}."""
    text = text if text is not None else (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    return {f"v{v}": dt.date.fromisoformat(d) for v, d in TAG_RE.findall(text)}


def sentence_texts(script: Script) -> dict[str, str]:
    return {f"{sc.id}_{k}": s.text for sc in script.scenes for k, s in enumerate(sc.sentences)}


def text_sha1(script: Script, sid: str) -> str:
    """sid 규칙 = 그 문장 text, 전체 규칙("-") = 전 문장 text 를 원고 순서로 이어붙인 것의 sha1."""
    texts = sentence_texts(script)
    if sid != "-" and sid not in texts:
        raise LintWaiverError(f"면제 sid {sid!r} 가 원고에 없다")
    body = "".join(texts.values()) if sid == "-" else texts[sid]
    return hashlib.sha1(body.encode("utf-8")).hexdigest()


def load(proj: Path, changelog: str | None = None) -> list[LintWaiver]:
    """면제 목록(없으면 []). 면제 불가 kind·rule_since 태그 없음·승인일 ≥ 규칙 날짜 = LintWaiverError."""
    p = proj / FILE
    if not p.exists():
        return []
    try:
        doc = LintWaivers.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
    except (ValueError, yaml.YAMLError) as ex:
        raise LintWaiverError(f"{p}: {ex}") from ex
    allowed = load_rules().script_grammar.lint_waivable
    dates = changelog_dates(changelog)
    for w in doc.waivers:
        if w.kind not in allowed:
            raise LintWaiverError(f"{p}: kind {w.kind!r} 는 면제할 수 없다(rules script_grammar.lint_waivable {allowed})")
        if w.rule_since not in dates:
            raise LintWaiverError(f"{p}: rule_since {w.rule_since} 가 CHANGELOG 태그가 아니다")
        if w.script_approved >= dates[w.rule_since]:
            raise LintWaiverError(f"{p}: 원고 승인 {w.script_approved} 가 규칙 {w.rule_since}({dates[w.rule_since]}) 보다 늦다 — "
                                  "승인 뒤에 생긴 규칙만 면제한다")
    return doc.waivers


def apply(report, waivers: list[LintWaiver], script: Script):  # noqa: ANN001, ANN201 — (LintReport, list[dict])
    """오류 중 면제와 정확 일치하는 것만 뺀 보고서와 면제 기록. 낡은 면제 = LintWaiverError."""
    if not waivers:   # 면제 목록이 없으면 보고서를 그대로(면제 기록 없음)
        return report, []
    used: set[int] = set()
    kept = []
    waived: list[dict] = []
    for issue in report.issues:
        hit = next((k for k, w in enumerate(waivers)
                    if w.kind == issue.kind and w.sid == issue.sid and w.text_sha1 == text_sha1(script, w.sid)), None)
        if hit is None:
            kept.append(issue)
            continue
        used.add(hit)
        waived.append({"kind": issue.kind, "sid": issue.sid, "decided_by": waivers[hit].decided_by})
    stale = [w for k, w in enumerate(waivers) if k not in used]
    if stale:
        raise LintWaiverError("낡은 린트 면제(일치하는 오류가 없거나 원고가 바뀜) — 면제 목록 정리: "
                              + ", ".join(f"{w.kind} {w.sid} ({w.decided_by})" for w in stale))
    uniq = sorted({tuple(x.items()): x for x in waived}.values(), key=lambda x: (x["kind"], x["sid"]))
    return type(report)(issues=kept), uniq   # 같은 보고서 타입(`python -m script.lint` 의 __main__ 포함)


def waived_lines(waived: list[dict]) -> list[str]:
    return [f"[waived {x['kind']} {x['sid']} — {x['decided_by']}]" for x in waived]
