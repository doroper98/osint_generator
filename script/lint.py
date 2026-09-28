"""원고 린트 (v2.3.0, plan3 `BANNED, lint()`, 03 §2, back_and_forth D-0021 작업 2).

패턴·수치는 `rules/video_rules.yaml`에서 읽는다(15 P3). 금지 문구의 정본은 규칙 파일
`banned_phrases.patterns` 하나다 — `docs/ANTIPATTERNS/LLM_ANTIPATTERNS.md` LLM-AP-006 은 참조만 한다.

오류(하나라도 있으면 plan 실패):
- slop: AI 상투 문구(banned_phrases.patterns)
- tts-symbol: 발음 텍스트 안의 숫자·기호(tts_rules.forbidden_chars_regex, TTS-AP-021~025·058)
- emphasis-missing: 강조어가 자막에 없음(tts_rules.emphasis_must_be_substring)

경고(plan 은 진행, StageResult.warnings 로 보고):
- source-missing: `sources` 가 빈 문장(03 §3 "모든 수치에 출처")
- subtitle-lines: 자막이 script_schema.subtitle_max_lines 줄을 넘음(렌더러와 같은 글꼴·폭으로 실측 wrap)

CLI (v3.0.0, 16 §4 `direction_validate` 의 6.9 전 대체 — D-0040 작업 4):
    python -m script.lint <proj>   → script.yaml 을 Script 로 로드 + 린트 + 검증 라벨 재계산·대조(D-0043),
                                     마지막 줄 StageResult JSON
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Literal

import cairo
from pydantic import BaseModel, ConfigDict

from rules import load_rules
from script.schema import Script

Severity = Literal["error", "warning"]
NUMERIC = re.compile(r"\d")   # 숫자·날짜가 있는 자막 문장


class LintIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    severity: Severity
    sid: str
    detail: str
    text: str

    def line(self) -> str:
        return f"[{self.kind}] {self.sid}: {self.detail} — {self.text}"


class LintReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issues: list[LintIssue]

    @property
    def errors(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def subtitle_lines(text: str) -> int:
    """렌더러(engine/subtitles.draw_subtitle)와 같은 글꼴·크기·폭으로 wrap 한 줄 수."""
    from engine.style import SUBTITLE, SUBTITLE_WRAP_PX  # noqa: PLC0415 — 글꼴 로딩은 필요할 때만
    from engine.typography import wrap  # noqa: PLC0415

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    return len(wrap(cairo.Context(surf), text, SUBTITLE_WRAP_PX, SUBTITLE.size, "sansm"))


def lint(script: Script) -> LintReport:
    r = load_rules()
    banned = [re.compile(p) for p in r.banned_phrases.patterns]
    forbidden = re.compile(r.tts_rules.forbidden_chars_regex)
    max_lines = r.script_schema.subtitle_max_lines
    out: list[LintIssue] = []
    for sc in script.scenes:
        for k, s in enumerate(sc.sentences):
            sid = f"{sc.id}_{k}"

            def add(kind: str, sev: Severity, detail: str, text: str = s.text, sid: str = sid) -> None:
                out.append(LintIssue(kind=kind, severity=sev, sid=sid, detail=detail, text=text))

            for p in banned:
                if p.search(s.text):
                    add("slop", "error", p.pattern)
            say = s.tts or s.text
            hit = forbidden.search(say)
            if hit:
                add("tts-symbol", "error", repr(hit.group(0)), say)
            if r.tts_rules.emphasis_must_be_substring:
                for e in s.emphasis:
                    if e not in s.text:
                        add("emphasis-missing", "error", e)
            if not s.sources:   # D-0029 §3 경고 유지(6.95 에서 오류 격상). 수치 문장은 표시(D-0043 §5)
                add("source-missing", "warning", "sources 비어 있음" + (" (수치 문장)" if NUMERIC.search(s.text) else ""))
            n = subtitle_lines(s.text)
            if n > max_lines:
                add("subtitle-lines", "warning", f"{n}줄 > {max_lines}")
    return LintReport(issues=out)


def main(argv: list[str] | None = None) -> int:
    import yaml  # noqa: PLC0415
    from pydantic import ValidationError  # noqa: PLC0415

    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="script.lint")
    ap.add_argument("proj", type=Path)
    args = ap.parse_args(argv)
    path = args.proj.resolve() / "script.yaml"
    from script.labels import check_project_labels  # noqa: PLC0415

    try:
        script = Script.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        rep = lint(script)
        labels = check_project_labels(path.parent, script)   # 도시어가 있으면 라벨 재계산·대조(D-0043 §3)
        arts = {"script": str(path)}
        if labels is not None:
            arts["label_counts"] = json.dumps(labels.counts(), ensure_ascii=False)
        res = StageResult(ok=not rep.errors, stage="lint", artifacts=arts,
                          errors=[i.line() for i in rep.errors], warnings=[i.line() for i in rep.warnings])
    except (OSError, ValueError, ValidationError, yaml.YAMLError) as ex:
        res = StageResult(ok=False, stage="lint", errors=[f"{path}: {ex}"])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
