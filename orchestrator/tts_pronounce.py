"""TTS 발음 사전 (한국어 ElevenLabs misread 회피, v0.34.10).

목적: ElevenLabs 가 정확한 한국어 표기조차 misread 하는 경우 — "달러" 를 [딸러]
가 아닌 [달러] 그대로, "유가" 를 [유까] 가 아닌 [유가] 평음으로, "102" 를
[백이] 가 아닌 [백두] 등 잘못 — narration 합성 직전에 텍스트를 음차로 치환해
정확한 발음 유도. **subtitle 은 원본 한국어 유지**(시청자 가독성).

원칙:
- 자동 한자어 숫자 변환(1~9999): "102" → "백 이", "120" → "백 이십".
- JSON 사전(`assets/pronounce.json`) 의 단어 → 음차 매핑이 숫자 변환보다 우선.
- 변환은 narration only — caption / subtitle 은 원본.

사용:
    from orchestrator.tts_pronounce import apply_pronunciation, load_dict
    d = load_dict(Path("hyperframes/demo/assets/pronounce.json"))
    spoken = apply_pronunciation("102달러 까지 반등", d)
    # → "백 이 딸러 까지 반등" (사전: "달러"→"딸러", 자동: "102"→"백 이")
"""

from __future__ import annotations

import json
import re
from pathlib import Path


_ONES = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]


def _num_to_sino_under_1000(n: int) -> str:
    """1 ≤ n ≤ 999 를 한자어로. 단위는 '백 십 사' 처럼 단위어 우선 (자릿수 1 일 때
    `일백`/`일십` 생략). 띄어쓰기는 모델에게 더 정확한 prosody 힌트 — 붙이는 것보다
    안전."""
    if n == 0:
        return ""
    hundred, rest = divmod(n, 100)
    ten, one = divmod(rest, 10)
    parts: list[str] = []
    if hundred:
        parts.append("백" if hundred == 1 else f"{_ONES[hundred]} 백")
    if ten:
        parts.append("십" if ten == 1 else f"{_ONES[ten]} 십")
    if one:
        parts.append(_ONES[one])
    return " ".join(parts)


def num_to_sino_kr(n: int) -> str:
    """0 ≤ n ≤ 99,999,999 를 한자어로. 99,999,999 이상은 그대로 반환(드물고
    OSINT 영상에선 만 단위 이상 거의 안 씀, 안전 폴백)."""
    if n == 0:
        return "영"
    if n < 1000:
        return _num_to_sino_under_1000(n)
    if n < 10000:
        thousand, rest = divmod(n, 1000)
        head = "천" if thousand == 1 else f"{_ONES[thousand]} 천"
        return f"{head} {_num_to_sino_under_1000(rest)}".rstrip() if rest else head
    if n < 100_000_000:
        man, rest = divmod(n, 10000)
        head = f"{num_to_sino_kr(man)} 만"
        return f"{head} {num_to_sino_kr(rest)}".rstrip() if rest else head
    return str(n)


# 숫자 + 한글 (단위어가 바로 붙는 경우 = "80달러", "19일") 패턴. num_to_sino_kr 의 결과
# 뒤에 단위 한글이 붙으면 자연스럽게 공백 1 칸 삽입해 prosody 보정.
_NUM_THEN_HANGUL_RE = re.compile(r"(?<!\d)(\d{1,8})(?=[가-힣])")
_NUM_RE = re.compile(r"(?<!\d)(\d{1,8})(?!\d)")


def apply_pronunciation(text: str, mapping: dict[str, str] | None = None) -> str:
    """텍스트를 narration 용 음차로 변환.

    1) `mapping` (사용자 사전) 의 key 가 text 에 있으면 value 로 치환 — 가장 우선.
    2) 남은 숫자(연속 1~8자리) 는 한자어로 자동 변환.
       2-1) 숫자 바로 뒤에 한글 단위어가 붙어있으면 (예: "80달러", "19일") 사이에
            공백 한 칸 삽입 — TTS 가 단위어 발음을 분리 적용하도록.

    단어 경계: mapping key 가 한국어이므로 `\b` 가 작동 안 함. 단순 substring 치환을
    긴 key 부터 적용해 부분 매칭 충돌 회피.
    """
    out = text
    if mapping:
        for key in sorted(mapping.keys(), key=len, reverse=True):
            if key.startswith("_"):
                continue
            if key in out:
                out = out.replace(key, mapping[key])
    # 숫자 + 단위어 사이 공백 보정 → "팔십 달러", "십 구 일".
    out = _NUM_THEN_HANGUL_RE.sub(
        lambda m: num_to_sino_kr(int(m.group(1))) + " ", out
    )
    out = _NUM_RE.sub(lambda m: num_to_sino_kr(int(m.group(1))), out)
    return out


def load_dict(path: Path) -> dict[str, str]:
    """JSON 사전 로딩. 파일 없거나 깨지면 빈 dict 반환(silent fallback).

    "_" 로 시작하는 key 는 주석/메타 — 사전에 포함 안 함.
    """
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        str(k): str(v)
        for k, v in raw.items()
        if isinstance(k, str) and not k.startswith("_")
    }


__all__ = ["apply_pronunciation", "load_dict", "num_to_sino_kr"]
