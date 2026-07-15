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
    """1 ≤ n ≤ 999 를 한자어로. 단위는 '백십사' 처럼 단위어 우선 (자릿수 1 일 때
    `일백`/`일십` 생략).

    **한 숫자 안에서는 음절을 절대 띄우지 않는다** (TTS-AP-058) — 예전에는 prosody
    힌트라며 "백 육 십 팔" 로 띄웠으나, ElevenLabs 는 공백을 만나면 국어의 연음(자음
    동화)을 끊어 "백육십"[뱅뉵씹] 을 [배·규·씹] 으로 또박또박 읽고, 소수점 앞에서도
    반박자 쉰다. 붙여 써야 모델이 연음/운율을 자연히 적용한다."""
    if n == 0:
        return ""
    hundred, rest = divmod(n, 100)
    ten, one = divmod(rest, 10)
    parts: list[str] = []
    if hundred:
        parts.append("백" if hundred == 1 else f"{_ONES[hundred]}백")
    if ten:
        parts.append("십" if ten == 1 else f"{_ONES[ten]}십")
    if one:
        parts.append(_ONES[one])
    return "".join(parts)


def num_to_sino_kr(n: int) -> str:
    """0 ≤ n ≤ 99,999,999 를 한자어로. 99,999,999 이상은 그대로 반환(드물고
    OSINT 영상에선 만 단위 이상 거의 안 씀, 안전 폴백).

    한 숫자의 음절은 붙여서 반환 (TTS-AP-058) — 연음/운율 보존."""
    if n == 0:
        return "영"
    if n < 1000:
        return _num_to_sino_under_1000(n)
    if n < 10000:
        thousand, rest = divmod(n, 1000)
        head = "천" if thousand == 1 else f"{_ONES[thousand]}천"
        return f"{head}{_num_to_sino_under_1000(rest)}" if rest else head
    if n < 100_000_000:
        man, rest = divmod(n, 10000)
        head = f"{num_to_sino_kr(man)}만"
        return f"{head}{num_to_sino_kr(rest)}" if rest else head
    return str(n)


# 숫자 + 한글 (단위어가 바로 붙는 경우 = "80달러", "19일") 패턴.
_NUM_THEN_HANGUL_RE = re.compile(r"(?<!\d)(\d{1,8})(?=[가-힣])")
_NUM_RE = re.compile(r"(?<!\d)(\d{1,8})(?!\d)")
# 천단위 콤마 (1,395,000) — 콤마 그룹별 개별 변환 파탄 방지용 사전 제거 (TTS-AP-064)
_THOUSANDS_COMMA_RE = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")


def apply_pronunciation(text: str, mapping: dict[str, str] | None = None) -> str:
    """텍스트를 narration 용 음차로 변환. (docs/08_AUDIO_AND_TTS_SPEC.md §2·§4-a)

    1) `mapping` (사용자 사전) 의 key 가 text 에 있으면 value 로 치환 — 가장 우선.
    2) 천단위 콤마를 제거해 하나의 수로 합침 — "1,395,000원"이 콤마 그룹별로 따로
       변환돼 "일,삼백구십오,영 원"이 되는 파탄 방지 (TTS-AP-064).
    3) 남은 숫자(연속 1~8자리) 는 한자어로 자동 변환.
       3-1) 숫자 바로 뒤 한글 단위어는 **붙여서** 반환 — "백육십팔딸러"처럼 한 호흡
            이어야 연음·경음이 산다([뱅뉵씹팔딸러]). 공백을 넣으면 [백육십팔 / 딸러]로
            끊겨 AI 티가 난다 (TTS-AP-065 — 기존 '공백 삽입' 방침 폐기, 사용자 실청취
            피드백 2026-07-12).

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
    out = _THOUSANDS_COMMA_RE.sub("", out)
    out = _NUM_THEN_HANGUL_RE.sub(lambda m: num_to_sino_kr(int(m.group(1))), out)
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
