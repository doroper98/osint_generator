"""단어 정렬 JSON 공통 형식 (v2.3.0, back_and_forth D-0026, DECISIONS D34).

`{mp3}.align.json` 한 모양으로 백엔드를 통일한다. at_word(engine/timebase)는 형식만 본다.

    {"alignment_source": "elevenlabs_timestamps" | "mms_forced_alignment",
     "characters": [...], "character_start_times_seconds": [...], "character_end_times_seconds": [...]}

- ElevenLabs: with-timestamps 응답의 글자별 정렬 그대로 + 출처 필드.
- MMS 강제 정렬(표준 음성 Supertonic, C0.2): 글자마다 구간. 시각은 합성 원본 mp3 기준(트림 전), 트림 보정은 plan 의 trim_offset.
- edge-tts `WordBoundary` 경로는 v5.23.0 V4(D-0212)에서 삭제.
출처 값은 rules `tts_rules.alignment_sources` 에 등재된 것만 허용한다(15 P10).
"""

from __future__ import annotations

import json
from pathlib import Path

from rules import load_rules

class AlignmentError(ValueError):
    pass


def align_path(mp3: Path) -> Path:
    return Path(str(mp3) + ".align.json")


def check_source(source: str) -> str:
    allowed = load_rules().tts_rules.alignment_sources
    if source not in allowed:
        raise AlignmentError(f"alignment_source {source!r} 가 rules tts_rules.alignment_sources {allowed} 에 없다")
    return source


def from_elevenlabs(alignment: dict) -> dict:
    return dict(alignment_source="elevenlabs_timestamps", characters=alignment["characters"],
                character_start_times_seconds=alignment["character_start_times_seconds"],
                character_end_times_seconds=alignment["character_end_times_seconds"])


def from_forced_alignment(text: str, spans: list) -> dict:
    """강제 정렬 글자 구간(script/tts/forced_align.CharSpan, 발음 텍스트 글자마다 하나) → 공통 형식(v5.16.0 D-0164 §5-3).
    글자 수가 다르면 오류(조용히 맞추지 않는다, P6)."""
    if len(spans) != len(text) or any(sp.char != c for sp, c in zip(spans, text)):
        raise AlignmentError(f"강제 정렬 글자 {len(spans)}개 ↔ 발음 텍스트 {len(text)}글자 불일치: {text!r}")
    return dict(alignment_source="mms_forced_alignment", characters=list(text),
                character_start_times_seconds=[round(sp.start, 4) for sp in spans],
                character_end_times_seconds=[round(sp.end, 4) for sp in spans])


def write(mp3: Path, al: dict) -> None:
    check_source(al["alignment_source"])
    align_path(mp3).write_text(json.dumps(al, ensure_ascii=False), encoding="utf-8")


def read(mp3: Path) -> dict | None:
    p = align_path(mp3)
    if not p.exists():
        return None
    al = json.loads(p.read_text(encoding="utf-8"))
    check_source(al.get("alignment_source", "<없음>"))
    if len(al["characters"]) != len(al["character_start_times_seconds"]):
        raise AlignmentError(f"{p.name}: characters 와 시각 길이가 다르다")
    return al
