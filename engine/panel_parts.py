"""패널·프리미티브 안에서 따로 나타나는 부분의 노출 시간 (v7.4.0 사용자 의견 UF-917, D936).

사용자 원문(2026-11-17): "이 씬에서 아래에 모형추정 이라고 써있는 글씨가 나오자 마자 다음 씬으로 넘어가 사라짐."
목록 패널의 꼬리말은 패널 시작 4.2초 뒤에 떠오르는데 패널이 5.3초 만에 끝났다 — 꼬리말이 완전히 보인 시간이 0.2초였다.
[element-hold](UF-171)는 뱃지·사진·기사·인용 같은 요소 전체만 보고, 패널 안에서 늦게 나타나는 부분은 보지 않았다.

`reveals(e)` = 그 이벤트 안에서 따로 나타나는 부분마다 (이름, 완전히 보이는 시각). 시각은 그리기 코드와 같은 규칙 값으로 계산한다.
`part_holds(e)` = 부분마다 (이름, 완전히 보인 뒤 패널이 사라지기 시작할 때까지의 초). 검사 [panel-part-hold] 가 하한(rules qa_checks.panel_part_hold.min_sec)과 댄다.
"""

from __future__ import annotations

from rules import load_rules

_R = load_rules()


def _checklist(e: dict) -> list[tuple[str, float]]:
    from engine import skin  # noqa: PLC0415

    if skin.active():   # 디자인 시스템 조판(UF-919)은 줄·꼬리말 시각이 다르다 — 그리기와 같은 함수
        from engine.panels.checklist import skin_reveals  # noqa: PLC0415

        return skin_reveals(e)
    K = _R.panels.charts.checklist  # noqa: N806
    n = len(e["items"])
    if e.get("style") == "open":
        at = e.get("at") or [e["t0"] + K.appear_start_sec + i * K.appear_step_sec for i in range(n)]
        out = [(f"항목 {i + 1} {e['items'][i]!r}", at[i] + K.open.fill_fade_sec) for i in range(n)]
    else:
        out = [(f"항목 {i + 1} {e['items'][i]!r}", e["t0"] + K.appear_start_sec + i * K.appear_step_sec + K.appear_sec) for i in range(n)]
    if e.get("footer"):
        out.append((f"꼬리말 {e['footer']!r}", e["t0"] + K.footer_sec + K.footer_fade_sec))
    return out


def _versus(e: dict) -> list[tuple[str, float]]:
    fast = _R.transition.element_motion["panel_item_fast_in_sec"]
    return [(f"항목 {it['text']!r}", it["t"] + fast) for side in e["sides"] for it in side["items"]]


def _fork(e: dict) -> list[tuple[str, float]]:
    F = _R.panels.charts.fork  # noqa: N806
    return [(f"갈래 {br['head']!r}", e["t0"] + F.card_start_sec + i * F.grow_step_sec + F.card_fade_sec) for i, br in enumerate(e["branches"])]


def _relation(e: dict) -> list[tuple[str, float]]:
    from engine.panels.relation import edge_start  # noqa: PLC0415 — 그리기와 같은 선 시작 시각

    REL = _R.panels.relation  # noqa: N806
    s0 = e["t0"] + edge_start(e)
    out = [(f"관계선 {ed['src']}→{ed['dst']}", s0 + k * REL.edge_gap_sec + REL.edge_dur_sec) for k, ed in enumerate(e["edges"])]
    if e.get("edge_label"):
        out.append((f"선 설명 {e['edge_label']!r}", e["t0"] + REL.edge_label.delay_sec + REL.edge_label.fade_sec))
    out += [(f"상태 변화 {c.get('label') or c.get('edge') or ''}", c["at"] + REL.state_fade_sec) for c in e.get("state_changes") or []]
    return out


def _network(e: dict) -> list[tuple[str, float]]:
    from engine.panels.network import edge_start  # noqa: PLC0415

    REL, N = _R.panels.relation, _R.panels.charts.network  # noqa: N806
    s0 = e["t0"] + edge_start(e)
    return [(f"관계선 {ed['src']}→{ed['dst']}", s0 + k * REL.edge_gap_sec + REL.edge_dur_sec + (N.label_sec if ed.get("label") else 0.0))
            for k, ed in enumerate(e["edges"])]


def _statement(e: dict) -> list[tuple[str, float]]:
    j = e["joiner"]
    return [(f"동참국 {j['label']!r}", max(e["t0"] + 2.2, j["t_join"]) + _R.transition.element_motion["panel_item_in_sec"])]


def _timeline(e: dict) -> list[tuple[str, float]]:
    TL = _R.panels.timeline  # noqa: N806
    out = [(f"사건 {ev['label']!r}", ev["t"] + TL.event_fade_sec) for ev in e["events"]]
    if e.get("band"):
        out.append((f"기간 띠 {e['band']['label']!r}", e["band"]["t_show"] + TL.band_fade_sec))
    return out


def _precedent(e: dict) -> list[tuple[str, float]]:
    M = _R.transition.element_motion  # noqa: N806
    out = [(f"연도 카드 {cd['year']!r}", cd["t0"] + M["panel_item_in_sec"]) for cd in e["cards"]]
    if e.get("footnote"):
        out.append(("주석", e["footnote"]["t0"] + M["panel_item_in_sec"]))
    return out


def _doc_excerpt(e: dict) -> list[tuple[str, float]]:
    L = _R.primitives.doc_excerpt  # noqa: N806
    out = [("번역", e["t0"] + L.trans_delay_sec + L.trans_fade_sec)]
    if e.get("highlight"):
        ut = e.get("highlight_t")
        out.append((f"밑줄 {e['highlight']!r}", (e["t0"] + L.underline_delay_sec if ut is None else ut) + L.underline_grow_sec))
    return out


def _era_numeral(e: dict) -> list[tuple[str, float]]:
    L = _R.primitives.era_numeral  # noqa: N806
    return [(f"연도 {s['label']!r}", s["t"] + L.roll_sec) for s in e["steps"]]


PANEL_REVEALS = {"checklist": _checklist, "versus": _versus, "fork": _fork, "relation": _relation, "network": _network,
                 "statement": _statement, "timeline": _timeline, "precedent": _precedent}
PRIMITIVE_REVEALS = {"doc_excerpt": _doc_excerpt, "era_numeral": _era_numeral}


def reveals(e: dict) -> list[tuple[str, float]]:
    """이 이벤트 안에서 따로 나타나는 부분 → (이름, 완전히 보이는 시각). 해당 없는 이벤트 = []."""
    fn = PANEL_REVEALS.get(e.get("kind")) if e["type"] == "panel" else PRIMITIVE_REVEALS.get(e.get("id")) if e["type"] == "primitive" else None
    return fn(e) if fn else []


def exit_start(e: dict) -> float:
    """패널·프리미티브가 사라지기 시작하는 시각(끝 − 퇴장 페이드) — 그리기와 같은 값."""
    if e["type"] == "panel":
        return e["t1"] - _R.layout_480p.panel.fade_sec
    return e["t1"] - getattr(getattr(_R.primitives, e["id"]), "fade_sec", 0.0)


def part_holds(e: dict) -> list[tuple[str, float]]:
    """부분마다 (이름, 완전히 보인 뒤 패널이 사라지기 시작할 때까지의 초). 음수 = 다 나타나기도 전에 사라진다."""
    rv = reveals(e)
    if not rv:
        return []
    end = exit_start(e)
    return [(name, end - tf) for name, tf in rv]


__all__ = ["PANEL_REVEALS", "PRIMITIVE_REVEALS", "exit_start", "part_holds", "reveals"]
