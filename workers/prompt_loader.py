"""워커 프롬프트 템플릿 로더 (v2.0.0, docs/handoff/15 §3 P3).

프롬프트는 코드 상수가 아니라 `prompts/*.md`(텍스트)·`prompts/*.yaml`(구조 데이터) 파일에서
읽는다. 규칙 자리표시 `{{RULES.<키>}}` 는 `rules/video_rules.yaml` 값으로 `.replace()` 치환한다
(CLAUDE.md C2 — `.format()` 금지). 치환되지 않은 `{{` 가 남으면 `PromptTemplateError` —
조용히 빈 값으로 보내지 않는다(15 P6).

파일 머리의 `<!-- ... -->` 거버넌스 헤더(DOCS_GOVERNANCE §2)는 프롬프트 본문이 아니므로 떼어 낸다.
워커별 단일 중괄호 자리표시(`{project_id}` 등)는 각 워커의 `build_user_prompt` 가 치환한다.

v4.4.0 장르 프롬프트 층(back_and_forth D-0090 작업 1, docs/handoff/20 §6·§7·§9): 템플릿 끝의 `{{GENRE_BLOCK}}` 은
`prompts/genre_<이름>.md` 를 장르 프로필(`genres/<genre>.yaml`)·`rules genre_prompt` 로 채운 문단으로 바뀐다.
기본 프롬프트가 이미 전제한 장르(`rules genre_prompt.base_genre`, 지정학)와 장르 미지정은 빈 문자열 — 출력 바이트 동일.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from schemas.genre_models import GenreProfile
from schemas.rules_models import VideoRules

PROMPTS_DIR: Path = Path(__file__).resolve().parent.parent / "prompts"

_HEADER_OPEN = "<!--"
_HEADER_CLOSE = "-->\n"


class PromptTemplateError(ValueError):
    """프롬프트 파일 누락, 또는 치환되지 않은 `{{...}}` 자리표시가 남음."""


def _strip_header(text: str) -> str:
    if text.startswith(_HEADER_OPEN):
        end = text.find(_HEADER_CLOSE)
        if end < 0:
            raise PromptTemplateError("거버넌스 헤더 `<!--` 가 닫히지 않았습니다")
        return text[end + len(_HEADER_CLOSE):]
    return text


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {s}" for s in items)


def _rules_placeholders(rules: VideoRules) -> dict[str, str]:
    """`{{RULES.<키>}}` → 치환 문자열. 새 자리표시는 여기에만 추가한다."""
    return {
        "{{RULES.banned_phrases}}": _bullets(rules.banned_phrases.patterns),
        "{{RULES.defect_classes}}": _bullets(rules.banned_phrases.defect_classes),
        "{{RULES.balance_principles}}": _bullets(rules.balance_principles),
        "{{RULES.direction_grammar}}": _bullets(rules.direction_grammar),   # v4.7.0 D-0104 D2(a)
        "{{RULES.tts_rules}}": yaml.safe_dump(
            rules.tts_rules.model_dump(mode="json"), allow_unicode=True, sort_keys=False
        ).rstrip("\n"),
        # v3.1.0 — 연출·검수 프롬프트(D-0047 작업 7)
        "{{RULES.shot_grammar}}": yaml.safe_dump(
            rules.shot_grammar.model_dump(mode="json"), allow_unicode=True, sort_keys=False
        ).rstrip("\n"),
        "{{RULES.qa_checks}}": yaml.safe_dump(
            rules.qa_checks.model_dump(mode="json"), allow_unicode=True, sort_keys=False
        ).rstrip("\n"),
        "{{RULES.event_types}}": _bullets(list(rules.registries.event_types)),
        "{{RULES.panel_kinds}}": _bullets(list(rules.registries.panel_kinds)),
        "{{RULES.placement_slots}}": _bullets([
            f"{name} — {', '.join(s.kinds)} ({_slot_form(s)})" for name, s in rules.placement.slots.items()]),
        "{{RULES.corner_elements}}": ", ".join(rules.hud.allowed_corner_elements),
        "{{RULES.verification.quote_max_chars}}": str(rules.verification.quote_max_chars),
        "{{RULES.script_labels}}": ", ".join(v for v in rules.script_schema.labels.values() if v),   # v4.4.0 D-0093
        "{{RULES.attribution_markers}}": ", ".join(f'"{m}"' for m in rules.script_schema.attribution_markers),   # v4.10.0 D-0116 — 린트·검증 판정과 같은 목록
    }


def _slot_form(s) -> str:  # noqa: ANN001 — schemas.rules_models.PlacementSlot
    if s.box is not None:
        return "화면 상자"
    if s.point is not None:
        return "화면 점 → 경위도"
    if s.beside_panel is not None:
        return "패널 위 미디어 — 엔진이 그 순간 패널 글자·자막·날짜를 피하는 빈 귀퉁이를 고른다(자리가 없으면 오류)"
    if s.screen:
        return "패널 위 화면 고정 자리 — 패널이 떠 있는 동안 시작하는 지도 슬롯(map_*) 뱃지는 엔진이 이 자리로 옮긴다"
    if s.align is not None:
        return "무대 가운데(아래 무대를 어둡게) — 기사 카드를 크게 보여 줄 때"
    return "카드 위치"


_EXAMPLE = re.compile(r"\{\{EXAMPLE:([A-Za-z0-9_.\-]+)\}\}")


def _examples(text: str) -> str:
    """`{{EXAMPLE:파일}}` → prompts/examples/파일 내용(펜스 블록). 예시 정본은 한 파일(중복 금지)."""
    def rep(m: re.Match[str]) -> str:
        p = PROMPTS_DIR / "examples" / m.group(1)
        if not p.exists():
            raise PromptTemplateError(f"예시 파일 없음: {p}")
        lang = "yaml" if p.suffix in (".yaml", ".yml") else "json"
        return f"```{lang}\n{p.read_text(encoding='utf-8').rstrip()}\n```"
    return _EXAMPLE.sub(rep, text)


GENRE_BLOCK = "{{GENRE_BLOCK}}"


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{i}. {s}" for i, s in enumerate(items, 1))


def _genre_placeholders(rules: VideoRules, g: GenreProfile) -> dict[str, str]:
    """`{{GENRE.<키>}}` → 치환 문자열. 문장은 규칙 파일(rules genre_prompt), 켜고 끄는 것은 장르 프로필(15 P3 — 코드 문장 0)."""
    gp = rules.genre_prompt
    primary = g.stage.primary
    if primary not in gp.stage_grammar:
        raise PromptTemplateError(f"장르 {g.genre}: 주 무대 {primary!r} 의 문법이 rules genre_prompt.stage_grammar 에 없다")
    tl = g.stage.timeline
    lanes = (_bullets([f"{ln.id} — {ln.label} ({ln.kind}{', 단위 ' + ln.unit if ln.unit else ''})" for ln in tl.lanes])
             if tl is not None else "(없음)")
    nar = g.narration
    rows: list[str] = []
    if nar is not None:
        for key, text in gp.narration.items():
            v = getattr(nar, key, None)
            if v:
                rows.append(text.replace("{n}", str(v)))
        extra = sorted(set(type(nar).model_fields) - set(gp.narration) - {"avoid"})
        if extra:
            raise PromptTemplateError(f"장르 프로필 narration 키 {extra} 의 문장이 rules genre_prompt.narration 에 없다")
    return {
        "{{GENRE.name}}": g.genre,
        "{{GENRE.status}}": g.status,
        "{{GENRE.stages}}": primary + (f" (보조: {', '.join(sec)})" if (sec := [x for x in g.stage.secondary if x in rules.registries.stages]) else ""),   # 구현 전 무대(planned)는 보이지 않는다
        "{{GENRE.stage_grammar}}": _bullets(gp.stage_grammar[primary]),
        "{{GENRE.lanes}}": lanes,
        "{{GENRE.colors}}": _bullets([f"{k}: {v}" for k, v in g.color_semantics.items()]),
        "{{GENRE.elements}}": ", ".join(sorted(g.elements() & set(_registered(rules)))),
        "{{GENRE.narration}}": _bullets(rows) if rows else "(없음)",
        "{{GENRE.avoid}}": ", ".join(nar.avoid) if nar is not None and nar.avoid else "(없음)",
        "{{GENRE.data_sources}}": _bullets(gp.data_sources),
        "{{GENRE.rubric}}": _numbered(gp.rubric_extra),
        "{{GENRE.rubric_n}}": str(len(gp.rubric_extra)),
        "{{GENRE.accents}}": ", ".join(rules.registries.accents),
    }


def _registered(rules: VideoRules) -> list[str]:
    reg = rules.registries
    return [*reg.event_types, *reg.panel_kinds, *reg.badge_kinds, *reg.primitives]


def genre_block(name: str, rules: VideoRules, genre: GenreProfile | None) -> str:
    """`{{GENRE_BLOCK}}` 의 내용. 기본 장르·미지정 = ""(바이트 동일). 그 밖은 `prompts/genre_<name>.md`(없으면 오류)."""
    if genre is None or genre.genre == rules.genre_prompt.base_genre:
        return ""
    path = prompt_path(f"genre_{name}")
    if not path.exists():
        raise PromptTemplateError(f"{name}: 장르 {genre.genre} 문단 템플릿이 없다 — {path}")
    text = _examples(_strip_header(path.read_text(encoding="utf-8")))
    for key, value in _genre_placeholders(rules, genre).items():
        text = text.replace(key, value)
    return "\n" + text


def prompt_path(name: str, suffix: str = ".md") -> Path:
    return PROMPTS_DIR / f"{name}{suffix}"


def load_prompt(name: str, rules: VideoRules, genre: GenreProfile | None = None) -> str:
    """`prompts/{name}.md` 를 읽어 규칙 자리표시를 치환한 문자열을 반환한다. genre = 장르 프롬프트 층(v4.4.0)."""
    path = prompt_path(name)
    if not path.exists():
        raise PromptTemplateError(f"프롬프트 파일이 없습니다: {path}")
    text = _examples(_strip_header(path.read_text(encoding="utf-8")))
    if GENRE_BLOCK in text:
        text = text.replace(GENRE_BLOCK, genre_block(name, rules, genre))
    for key, value in _rules_placeholders(rules).items():
        text = text.replace(key, value)
    if "{{" in text:
        start = text.index("{{")
        raise PromptTemplateError(
            f"{path.name}: 치환되지 않은 자리표시 {text[start:start + 40]!r}"
        )
    return text


def load_prompt_data(name: str) -> Any:
    """`prompts/{name}.yaml` 구조 데이터(예: 카테고리 가이드)를 읽는다."""
    path = prompt_path(name, ".yaml")
    if not path.exists():
        raise PromptTemplateError(f"프롬프트 데이터 파일이 없습니다: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def prompt_sha1(text: str) -> str:
    """렌더된 프롬프트의 sha1 (provenance, 15 P5)."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()
