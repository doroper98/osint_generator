"""워커 프롬프트 템플릿 로더 (v2.0.0, docs/handoff/15 §3 P3).

프롬프트는 코드 상수가 아니라 `prompts/*.md`(텍스트)·`prompts/*.yaml`(구조 데이터) 파일에서
읽는다. 규칙 자리표시 `{{RULES.<키>}}` 는 `rules/video_rules.yaml` 값으로 `.replace()` 치환한다
(CLAUDE.md C2 — `.format()` 금지). 치환되지 않은 `{{` 가 남으면 `PromptTemplateError` —
조용히 빈 값으로 보내지 않는다(15 P6).

파일 머리의 `<!-- ... -->` 거버넌스 헤더(DOCS_GOVERNANCE §2)는 프롬프트 본문이 아니므로 떼어 낸다.
워커별 단일 중괄호 자리표시(`{project_id}` 등)는 각 워커의 `build_user_prompt` 가 치환한다.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

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
    }


def _slot_form(s) -> str:  # noqa: ANN001 — schemas.rules_models.PlacementSlot
    if s.box is not None:
        return "화면 상자"
    if s.point is not None:
        return "화면 점 → 경위도"
    if s.beside_panel is not None:
        return "패널 위 미디어 — 엔진이 그 순간 패널 글자·자막·날짜를 피하는 빈 귀퉁이를 고른다(자리가 없으면 오류)"
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


def prompt_path(name: str, suffix: str = ".md") -> Path:
    return PROMPTS_DIR / f"{name}{suffix}"


def load_prompt(name: str, rules: VideoRules) -> str:
    """`prompts/{name}.md` 를 읽어 규칙 자리표시를 치환한 문자열을 반환한다."""
    path = prompt_path(name)
    if not path.exists():
        raise PromptTemplateError(f"프롬프트 파일이 없습니다: {path}")
    text = _examples(_strip_header(path.read_text(encoding="utf-8")))
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
