"""단어 정렬 JSON 공통 형식 (v2.3.0, back_and_forth D-0026, DECISIONS D34).

`{mp3}.align.json` 한 모양으로 두 백엔드를 통일한다. at_word(engine/timebase)는 형식만 본다.

    {"alignment_source": "edge_word_boundary" | "elevenlabs_timestamps" | "mms_forced_alignment",
     "characters": [...], "character_start_times_seconds": [...], "character_end_times_seconds": [...]}

- ElevenLabs: with-timestamps 응답의 글자별 정렬 그대로 + 출처 필드.
- edge-tts: `WordBoundary` 단어 경계. 단어 첫 글자에 경계 시각, 나머지 글자는 다음 경계까지 선형 보간(참고값 —
  at_word 는 첫 글자만 쓴다). 시각은 합성 원본 mp3 기준(트림 전)이다. 트림 보정은 plan 의 trim_offset.
출처 값은 rules `tts_rules.alignment_sources` 에 등재된 것만 허용한다(15 P10).
"""

from __future__ import annotations

import json
from pathlib import Path

from rules import load_rules

TICKS_PER_SEC = 1e7  # edge-tts offset·duration 단위(100ns)


class AlignmentError(ValueError):
    pass


def align_path(mp3: Path) -> Path:
    return Path(str(mp3) + ".align.json")


def check_source(source: str) -> str:
    allowed = load_rules().tts_rules.alignment_sources
    if source not in allowed:
        raise AlignmentError(f"alignment_source {source!r} 가 rules tts_rules.alignment_sources {allowed} 에 없다")
    return source


def from_word_boundaries(text: str, words: list[tuple[str, float, float]]) -> dict:
    """edge WordBoundary [(단어, 시작초, 길이초)] → 글자 단위 정렬.

    단어를 발음 텍스트에서 앞에서부터 찾는다. 못 찾으면 오류(조용히 넘기지 않는다, 15 P6).
    """
    if not words:
        raise AlignmentError("WordBoundary 가 하나도 없다")
    anchors: list[tuple[int, float]] = []
    pos = 0
    for w, t0, _ in words:
        i = text.find(w, pos)
        if i < 0:
            raise AlignmentError(f"경계 단어 {w!r} 를 발음 텍스트에서 못 찾음: {text!r}")
        anchors.append((i, t0))
        pos = i + len(w)
    last_w, last_t, last_d = words[-1]
    anchors.append((len(text), last_t + last_d))
    if anchors[0][0] > 0:
        anchors.insert(0, (0, anchors[0][1]))
    starts: list[float] = []
    for k in range(len(anchors) - 1):
        (i0, a), (i1, b) = anchors[k], anchors[k + 1]
        n = i1 - i0
        starts += [a + (b - a) * j / n for j in range(n)] if n > 0 else []
    ends = starts[1:] + [anchors[-1][1]]
    return dict(alignment_source="edge_word_boundary", characters=list(text),
                character_start_times_seconds=[round(x, 4) for x in starts],
                character_end_times_seconds=[round(x, 4) for x in ends])


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
