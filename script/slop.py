"""AI 상투 문구 검사 범위 — 원고 밖 화면 문자열·검토 문서(v7.4.0 back_and_forth D-0281, 사용자 의견 UF-145).

UF-145 원문: "니가 작성하는 문구에 이런내용이 없도록 강하게 쪼여. 정말 ai slop 느껴지는 문구들이거든."
패턴은 `rules/video_rules.yaml banned_phrases.patterns` 하나다(원고 린트 `script.lint` 와 같은 목록). 여기서는 원고(`s.text`) 밖을 본다:
설명문(description.yaml)·연출 화면 문자열(direction.yaml — 카드·패널·핀·뱃지·아일랜드·캐스케이드·카탈로그 라벨)·엔딩 크레딧 줄(credits.yaml)·
게이트 ① 검토 문서(gate1_view*.txt·gate1_elements.md). 인물 발언 원문(quote 이벤트의 text)은 남의 말이라 제외한다.
위반은 원고 린트와 같은 `slop` error(면제 불가). 감독·구현 보고문은 `tools/slop_check.py` 로 같은 패턴을 검사한다.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

from rules import load_rules

# 연출 이벤트에서 화면에 글자로 나오는 키(값이 문자열 또는 문자열 목록). 식별자·앵커·자산 id 키는 넣지 않는다
SCREEN_KEYS = frozenset({"tag", "lines", "label", "sub", "role", "title", "text", "items", "caption", "headline", "note", "name",
                         "left", "right", "body", "quote_ko", "summary"})
QUOTE_TYPES = frozenset({"quote"})   # 발언 원문 — text 는 남의 말(제외), 그 밖 키(인물 라벨 등)는 본다
QUOTE_SKIP_KEYS = frozenset({"text", "quote"})
DESC_KEYS = ("headline", "summary")
DOC_GLOBS = ("gate1_view*.txt", "gate1_elements.md")


def patterns() -> list[re.Pattern[str]]:
    return [re.compile(p) for p in load_rules().banned_phrases.patterns]


def slop_hits(text: str, pats: list[re.Pattern[str]] | None = None) -> list[str]:
    """text 에 걸린 금지 패턴 목록(패턴 문자열)."""
    return [p.pattern for p in (pats or patterns()) if p.search(text)]


def _strings(v: object) -> Iterator[str]:
    if isinstance(v, str):
        yield v
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)
    elif isinstance(v, dict):
        for k, x in v.items():
            if k in SCREEN_KEYS:
                yield from _strings(x)
            elif isinstance(x, (dict, list)):
                yield from _walk_nested(x)


def _walk_nested(v: object) -> Iterator[str]:
    """중첩 구조(패널 items·cascade 단계 등) 안의 화면 키만."""
    if isinstance(v, dict):
        yield from _strings(v)
    elif isinstance(v, list):
        for x in v:
            if isinstance(x, (dict, list)):
                yield from _walk_nested(x)


def direction_strings(doc: dict) -> Iterator[tuple[str, str]]:
    """(위치, 문자열) — direction.yaml 이벤트의 화면 문자열."""
    for i, e in enumerate(doc.get("events") or []):
        if not isinstance(e, dict):
            continue
        typ = str(e.get("type", "?"))
        for k, v in e.items():
            if k not in SCREEN_KEYS and not isinstance(v, (dict, list)):
                continue
            if typ in QUOTE_TYPES and k in QUOTE_SKIP_KEYS:
                continue
            src = _strings(v) if k in SCREEN_KEYS else _walk_nested(v)
            for s in src:
                yield f"direction.events[{i}].{typ}.{k}", s


def project_strings(proj: Path) -> Iterator[tuple[str, str]]:
    """(위치, 문자열) — 원고 밖 화면 문자열·검토 문서. 없는 파일은 건너뛴다(그 단계 전)."""
    import yaml  # noqa: PLC0415

    d = proj / "description.yaml"
    if d.exists():
        desc = yaml.safe_load(d.read_text(encoding="utf-8")) or {}
        for k in DESC_KEYS:
            if isinstance(desc.get(k), str):
                yield f"description.{k}", desc[k]
        for j, c in enumerate(desc.get("chapters") or []):
            if isinstance(c, dict) and isinstance(c.get("label"), str):
                yield f"description.chapters[{j}].label", c["label"]
        for j, f in enumerate(desc.get("footer") or []):
            if isinstance(f, str):
                yield f"description.footer[{j}]", f
    p = proj / "direction.yaml"
    if p.exists():
        yield from direction_strings(yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    c = proj / "credits.yaml"
    if c.exists():
        cr = yaml.safe_load(c.read_text(encoding="utf-8")) or {}
        for si, sec in enumerate(cr.get("sections") or []):
            for ii, it in enumerate(sec.get("items") or [] if isinstance(sec, dict) else []):
                if isinstance(it, dict) and isinstance(it.get("main"), str):
                    yield f"credits.sections[{si}].items[{ii}].main", it["main"]
    for g in DOC_GLOBS:
        for f in sorted(proj.glob(g)):
            for n, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                yield f"{f.name}:{n}", ln


def project_slop(proj: Path) -> list[tuple[str, str, str]]:
    """(위치, 문자열, 패턴) — 원고 밖 상투 문구 위반."""
    pats = patterns()
    return [(where, s, p) for where, s in project_strings(proj) for p in slop_hits(s, pats)]


__all__ = ["direction_strings", "patterns", "project_slop", "project_strings", "slop_hits"]
