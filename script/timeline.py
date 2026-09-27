"""원고 → 문장 타임라인 (v2.1.0, plan3 build 전·후반, 02 §2.2).

간격(gap·scene_gap·lead)·타이틀/엔딩 카드 길이는 `rules/video_rules.yaml layout_480p`에서 읽는다(15 P3).
타이틀 카드는 첫 장면(콜드 오픈) 다음에 들어간다(timeline_gaps.title_after_cold_open).
"""

from __future__ import annotations

from rules import load_rules
from script.schema import Card, Script

TITLE_OFFSET = 0.2   # 콜드 오픈 끝 → 타이틀 카드 시작 (v3 값)
TITLE_TAIL = 0.6     # 타이틀 카드 끝 → 다음 장면 (v3 값)
END_LEAD = 1.2       # 마지막 문장 뒤 → 엔딩 카드 (v3 값)
END_TAIL = 0.5       # 엔딩 카드 뒤 여백 (v3 값)


def split_emphasis(text: str, emphasis: list[str]) -> list[list]:
    """자막을 [조각, 강조여부] 목록으로. 강조어마다 첫 등장 한 번만, 이미 강조된 조각은 건드리지 않는다."""
    segs: list[list] = [[text, 0]]
    for e in emphasis:
        ns: list[list] = []
        for s_, f in segs:
            if f or e not in s_:
                ns.append([s_, f])
                continue
            i = s_.index(e)
            ns += [x for x in ([s_[:i], 0], [e, 1], [s_[i + len(e):], 0]) if x[0]]
        segs = ns
    return segs


def sentence_rows(script: Script) -> list[dict]:
    """sid·scene·date·text·tts·segments (음성 전 단계)."""
    rows = []
    for sc in script.scenes:
        for k, s in enumerate(sc.sentences):
            rows.append(dict(sid=f"{sc.id}_{k}", scene=sc.id, date=s.date, text=s.text, tts=s.tts or s.text,
                             segments=split_emphasis(s.text, s.emphasis)))
    return rows


def layout(rows: list[dict]) -> tuple[list[Card], dict[str, float], float]:
    """rows 에 t0·t1 을 채우고 (cards, scene_start, total) 를 돌려준다. rows 에 dur 가 있어야 한다."""
    L = load_rules().layout_480p  # noqa: N806
    g = L.timeline_gaps
    t = g.lead_sec
    prev = None
    first = rows[0]["scene"] if rows else None
    cards: list[Card] = []
    scene_start: dict[str, float] = {}
    for x in rows:
        if x["scene"] != prev:
            if prev == first and g.title_after_cold_open and prev is not None:
                cards.append(Card(kind="title", t0=t + TITLE_OFFSET, t1=t + TITLE_OFFSET + L.title_card.dur_sec))
                t += L.title_card.dur_sec + TITLE_TAIL
            elif prev is not None:
                t += g.scene_gap_sec
            scene_start[x["scene"]] = t
            prev = x["scene"]
        x["t0"] = t
        x["t1"] = t + x["dur"]
        t = x["t1"] + g.gap_sec
    t += END_LEAD
    cards.append(Card(kind="end", t0=t, t1=t + L.end_card.dur_sec))
    return cards, scene_start, t + L.end_card.dur_sec + END_TAIL
