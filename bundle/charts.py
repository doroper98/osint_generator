"""bundle.charts — agents_reviewer 번들 차트 정규화 순수 함수 (v2.0.0 이관).

`hyperframes/scripts/bundle_to_video.py`(archive/hyperframes-briefing 브랜치)에서 HTML·파일 I/O
없는 차트 함수만 **본문 무변경**으로 옮겼다 (docs/handoff/19 §3.2·§5.3). 출력 dict 는 아직 옛
HyperFrames 씬 데이터 모양이다 — 새 엔진 패널 모델로의 변환은 Phase 6·9 에서 한다.

이관 제외(DECISIONS D11): `norm_map`·`_load_map_metas`·`_project_merc` — 삭제된 미리 투영 권역 SVG
메타(`hyperframes/briefing/assets/maps/*.meta.json`)에 묶여 있어 옮기면 "권역 미지원 → 생략"
조용한 드롭 통로가 된다(15 P6). 참고 사본: docs/handoff/reference_code/repo_legacy/norm_map.py.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from bundle.text import clip, iso_to_kr, to_polite

REPO = Path(__file__).resolve().parent.parent

UNIT_RE = re.compile(r"[(（]단위[:：]\s*([^)）]+)[)）]")


def split_unit(title: str) -> tuple[str, str]:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    m = UNIT_RE.search(title)
    unit = m.group(1).strip() if m else ""
    return UNIT_RE.sub("", title).strip(), unit


def build_candle(charts: list) -> dict | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    c = next((c for c in charts if c.get("type") == "candle" and isinstance(c.get("data"), list)), None)
    if not c or len(c["data"]) < 10:
        return None
    ohlc = [{k: d[k] for k in ("date", "open", "high", "low", "close")} for d in c["data"]]
    return {"title": c.get("title", ""), "ohlc": ohlc, "chart_id": c.get("chart_id")}


def build_bar_panels(charts: list) -> list:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """bar 차트 → 패널 그룹. 단일 차트 1패널 씬 + 잔여 2개 묶음 듀얼 패널 씬."""
    bars = [c for c in charts if c.get("type") == "bar" and isinstance(c.get("data"), list) and c["data"]]
    scenes = []
    used = []
    for c in bars:
        title, unit = split_unit(c.get("title", ""))
        items = [{"label": d.get("label", ""), "value": d.get("value", 0), "note": clip(d.get("note", "") or "", 46)}
                 for d in c["data"][:7]]
        used.append({"title": clip(title, 30), "unit": unit, "items": items, "chart_id": c.get("chart_id")})
    if not used:
        return []
    # 같은 단위의 마지막 두 개는 듀얼 패널로 묶는다 (예: 두 회사의 목표주가)
    if len(used) >= 3 and used[-1]["unit"] == used[-2]["unit"]:
        scenes.append({"panels": [used[0]]})
        scenes.append({"panels": used[-2:]})
    elif len(used) >= 2 and used[-1]["unit"] == used[-2]["unit"]:
        scenes.append({"panels": used[-2:]})
    else:
        scenes.append({"panels": [used[0]]})
    return scenes


def norm_stacked(c: dict) -> dict | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """stacked/stacked_bar — 행별 세그먼트. parts/segments/series(dict|list) 허용."""
    raw = c.get("data")
    if not isinstance(raw, list) or not raw:
        return None
    rows = []
    for it in raw[:5]:
        segs = it.get("segments") or it.get("parts") or it.get("series")
        if isinstance(segs, dict):
            segs = [{"name": k, "value": v} for k, v in segs.items()]
        if not isinstance(segs, list) or not segs:
            return None
        rows.append({
            "label": clip(str(it.get("label", "")), 14),
            "segments": [{"name": clip(str(s.get("name") or s.get("label") or ""), 12),
                          "value": float(s.get("value", 0))} for s in segs[:5]],
        })
    return {"rows": rows, "unit": split_unit(c.get("title", ""))[1]}


def norm_waterfall(c: dict) -> dict | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """waterfall — 증감 브리지. kind/type 명시 없으면 첫 항목 start, 나머지 delta."""
    raw = c.get("data")
    if not isinstance(raw, list) or len(raw) < 2:
        return None
    items = []
    for i, it in enumerate(raw[:9]):
        v = it.get("value", it.get("delta", 0))
        kind = it.get("kind") or it.get("type")
        if kind not in ("start", "delta", "total"):
            kind = "start" if i == 0 else "delta"
        items.append({"label": clip(str(it.get("label", "")), 12), "value": float(v), "kind": kind})
    return {"items": items, "unit": split_unit(c.get("title", ""))[1]}


def norm_scatter(c: dict) -> dict | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    raw = c.get("data")
    if not isinstance(raw, list) or len(raw) < 3:
        return None
    pts = []
    for it in raw[:14]:
        if not isinstance(it.get("x"), (int, float)) or not isinstance(it.get("y"), (int, float)):
            return None
        raw_label = str(it.get("label", "")).split("(")[0].strip()
        pts.append({"x": it["x"], "y": it["y"],
                    "label": clip(raw_label, 36) or None,
                    "hi": bool(it.get("hi") or it.get("accent"))})
    xs = [p["x"] for p in pts]
    ys = [p["y"] for p in pts]
    # 같은 스케일 축이면 대각 기준선 (변화 없음 선)
    xr = (max(xs) - min(xs)) or 1
    yr = (max(ys) - min(ys)) or 1
    diagonal = 0.4 < (xr / yr) < 2.5 and min(max(xs), max(ys)) > max(min(xs), min(ys))
    return {"points": pts, "xLabel": clip(str(c.get("x_label") or ""), 20) or None,
            "yLabel": clip(str(c.get("y_label") or ""), 20) or None, "diagonal": diagonal}


def norm_heatmap(c: dict) -> dict | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    raw = c.get("data")
    if isinstance(raw, dict) and raw.get("rows") and raw.get("cols") and raw.get("values"):
        return {"rows": [clip(str(r), 10) for r in raw["rows"][:7]],
                "cols": [clip(str(x), 8) for x in raw["cols"][:14]],
                "values": [row[:14] for row in raw["values"][:7]]}
    if isinstance(raw, list) and raw and {"row", "col", "value"} <= set(raw[0].keys()):
        rows = []
        cols = []
        for it in raw:
            if it["row"] not in rows:
                rows.append(it["row"])
            if it["col"] not in cols:
                cols.append(it["col"])
        V = [[0.0] * len(cols) for _ in rows]
        for it in raw:
            V[rows.index(it["row"])][cols.index(it["col"])] = float(it["value"])
        return {"rows": [clip(str(r), 10) for r in rows[:7]],
                "cols": [clip(str(x), 8) for x in cols[:14]],
                "values": [row[:14] for row in V[:7]]}
    return None


DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


def _full_date(s: str, end: bool = False) -> str | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """YYYY-MM-DD 또는 YYYY-MM(월 단위 → 1일/28일 보정)."""
    if not DATE_RE.match(s):
        return None
    return s if len(s) == 10 else s + ("-28" if end else "-01")


def norm_gantt(c: dict, today: str | None) -> dict | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    raw = c.get("data")
    if not isinstance(raw, list) or not raw:
        return None
    tasks = []
    for it in raw[:7]:
        s = _full_date(str(it.get("start", "")))
        e = _full_date(str(it.get("end", "")), end=True)
        if not (s and e):
            return None
        tasks.append({"label": clip(str(it.get("label", "")), 16), "start": s, "end": e,
                      "phase": it.get("phase")})
    return {"tasks": tasks, "today": today}


def norm_sankey(c: dict) -> dict | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """sankey — 자금/물량 흐름 배분. nodes[{id,label,accent?}] + links[{source,target,value>0}].

    깊이(컬럼) 배치는 빌더(JS)가 링크 방향에서 전파 계산. 여기서는 참조 무결성·
    양수 값 검증과 라벨 클립만 담당. 내레이션용 최대 종착지(_max_sink)는 씬 조립
    쪽에서 pop 해 소비한다 (BRIEFING_DATA 에 남기지 않음)."""
    d = c.get("data")
    if not isinstance(d, dict):
        return None
    nodes = [n for n in (d.get("nodes") or [])
             if isinstance(n, dict) and n.get("id") and n.get("label")]
    ids = {n["id"] for n in nodes}
    links = [L for L in (d.get("links") or [])
             if isinstance(L, dict) and L.get("source") in ids and L.get("target") in ids
             and L.get("source") != L.get("target")
             and isinstance(L.get("value"), (int, float)) and L["value"] > 0]
    if len(nodes) < 2 or not links:
        return None
    linked = {L["source"] for L in links} | {L["target"] for L in links}
    out_nodes = [{"id": n["id"], "label": clip(str(n["label"]), 18),
                  "accent": bool(n.get("accent"))} for n in nodes if n["id"] in linked]
    out_links = [{"source": L["source"], "target": L["target"], "value": float(L["value"])}
                 for L in links]
    # 최대 유입 종착 노드 (유출 없는 노드 중) — 두 번째 cue 용
    sources = {L["source"] for L in out_links}
    inflow: dict = {}
    for L in out_links:
        if L["target"] not in sources:
            inflow[L["target"]] = inflow.get(L["target"], 0.0) + L["value"]
    label_of = {n["id"]: n["label"] for n in out_nodes}
    max_sink = label_of.get(max(inflow, key=inflow.get)) if inflow else None
    inferred = ((c.get("provenance") or {}).get("verification") or "") != "official"
    return {"nodes": out_nodes, "links": out_links, "unit": str(d.get("unit") or ""),
            "inferred": inferred, "_max_sink": max_sink}


def _strip_lead_date(s: str) -> str:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """신호명 앞의 날짜 토큰(7/13 · 2026-07-13) 제거 — deadline(when)과 중복 낭독 방지."""
    return re.sub(r"^\s*(?:\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\s+", "", s.strip())


def build_signals(signals: list) -> dict | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    if not signals:
        return None
    items = []
    for s in signals[:5]:
        nm = _strip_lead_date(s.get("signal", ""))
        # 낭독용: 첫 절만 ('+·' 앞) — 절단 꼬리("+ 레버리지 ETF 상장…") 낭독 방지
        spoken = re.split(r"\s*[+·]\s*", nm)[0].strip()
        items.append({
            "when": clip(iso_to_kr(s.get("deadline", "")), 14),
            "name": clip(nm, 26),
            "name_spoken": clip(spoken, 30),
            "desc": clip(s.get("description", ""), 56),
            "unverified": s.get("verification") == "unverified",
        })
    return {"items": items}


def build_slopes(charts: list) -> list:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    out = []
    for c in charts:
        if c.get("type") != "slope" or not isinstance(c.get("data"), dict):
            continue
        d = c["data"]
        items = [{"label": clip(it.get("label", ""), 12), "a": it.get("a", 0), "b": it.get("b", 0)}
                 for it in (d.get("items") or [])[:6]]
        if not items:
            continue
        out.append({
            "left_label": clip(d.get("left_label", ""), 14),
            "right_label": clip(d.get("right_label", ""), 14),
            "items": items,
            "title": split_unit(c.get("title", ""))[0],
            "chart_id": c.get("chart_id"),
        })
    return out


def build_tables(charts: list) -> list:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """type=="table" 차트 → 표 씬 데이터 (비교표·매핑표). columns/rows 평면 통과 + clip.

    data 계약: { columns: [{key, label, align?, weight?, accent?}],
                 rows: [{cells: {key: str}, highlight?: bool}] }.
    """
    out = []
    for c in charts:
        if c.get("type") != "table" or not isinstance(c.get("data"), dict):
            continue
        d = c["data"]
        cols = [
            {
                "key": str(col.get("key", "")),
                "label": clip(str(col.get("label", "")), 20),
                "align": col.get("align", "left"),
                "weight": col.get("weight", 1),
                "accent": col.get("accent"),
            }
            for col in (d.get("columns") or [])
            if col.get("key")
        ]
        rows = []
        for r in (d.get("rows") or [])[:12]:
            cells = r.get("cells") or {}
            rows.append({
                "cells": {str(k): clip(str(v), 44) for k, v in cells.items()},
                "highlight": bool(r.get("highlight")),
            })
        if not cols or not rows:
            continue
        out.append({
            "columns": cols,
            "rows": rows,
            "title": split_unit(c.get("title", ""))[0],
            "chart_id": c.get("chart_id"),
        })
    return out


FLAG_IDS = {"nk": "kp", "kp": "kp", "kr": "kr", "jp": "jp", "cn": "cn", "ru": "ru",
            "us": "us", "ir": "ir", "il": "il", "lb": "lb"}


_FLAG_DIR = REPO / "assets" / "flags" / "legacy_svg"  # v2.0.0: hyperframes/briefing/assets/flags 에서 이동


def norm_network(c: dict) -> dict | None:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    """network 차트 → 관계망 씬. 최다 연결 노드 중심 + 나머지 원형 배치."""
    d = c.get("data")
    if not isinstance(d, dict) or not d.get("nodes") or not d.get("links"):
        return None
    nodes_raw = d["nodes"][:8]
    links = [{"s": l.get("source"), "t": l.get("target"), "type": l.get("type", "영향")}
             for l in d["links"][:14]]
    deg: dict = {}
    for l in links:
        deg[l["s"]] = deg.get(l["s"], 0) + 1
        deg[l["t"]] = deg.get(l["t"], 0) + 1
    order = sorted(nodes_raw, key=lambda nd: -deg.get(nd["id"], 0))
    cx, cy, r = 880, 566, 234
    nodes = []
    for i, nd in enumerate(order):
        if i == 0:
            x, y = cx, cy
        else:
            ang = -math.pi / 2 + (i - 1) * (2 * math.pi / max(1, len(order) - 1))
            x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        flag = FLAG_IDS.get(str(nd["id"]).lower())
        entry = {"id": nd["id"], "label": clip(nd.get("label", ""), 10),
                 "x": round(x, 1), "y": round(y, 1), "kind": "center" if i == 0 else "ring"}
        if flag and (_FLAG_DIR / f"{flag}.svg").exists():
            entry["img"] = f"assets/flags/{flag}.svg"
        else:
            entry["initials"] = entry["label"][:2]
        nodes.append(entry)
    return {"nodes": nodes, "links": links}


def section_for_chart(sections: list, chart_id: str):
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    for s in sections:
        if chart_id in (s.get("chart_refs") or []):
            return s
    return None


def build_versus(contradiction: dict, theme: dict) -> dict:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    res = contradiction.get("resolution", "")
    if "강세" in res and "보수" in res:
        names = ("강세론", "보수론")
    else:
        names = ("시각 A", "시각 B")
    stance_a = (0.82, "다수설") if "다수" in res else (0.7, "우세")
    stance_b = (0.24, "소수설") if "소수" in res else (0.3, "신중")

    def org_and_line(side: str) -> tuple[str, str]:
        m = re.match(r"(.{4,60}?)[은는]\s+(.+)", side)
        if m:
            return clip(m.group(1), 30), clip(m.group(2), 92)
        return "", clip(side, 92)

    org_a, line_a = org_and_line(contradiction.get("side_a", ""))
    org_b, line_b = org_and_line(contradiction.get("side_b", ""))
    up = theme.get("tokens", {}).get("up", "#88B888")
    return {
        "axis": {"left": "신중", "right": "강세", "tag": "분석 추정"},
        "cards": [
            {"initials": names[0][:2], "name": names[0], "org": org_a or "다수 진영",
             "line": to_polite(line_a), "stance": stance_a[0], "stanceLabel": stance_a[1], "color": up},
            {"initials": names[1][:2], "name": names[1], "org": org_b or "소수 진영",
             "line": to_polite(line_b), "stance": stance_b[0], "stanceLabel": stance_b[1], "color": "#8d99ae"},
        ],
    }


def build_markets(charts: list) -> dict:
    # moved from hyperframes/scripts/bundle_to_video.py (v2.0.0)
    markets = []
    for c in charts:
        if c.get("type") != "line" or not isinstance(c.get("data"), list):
            continue
        ys = [pt["y"] for pt in c["data"] if isinstance(pt, dict) and isinstance(pt.get("y"), (int, float))]
        if len(ys) < 8 or ys[0] == 0:
            continue
        arr = [round((y / ys[0] - 1) * 100, 2) for y in ys]
        pct = arr[-1]
        spread = max(arr) - min(arr)
        if pct >= 3:
            kind = "vol" if spread >= max(12, abs(pct) * 2.2) else "up"
        elif pct <= -3:
            kind = "down"
        elif spread >= 10:
            kind = "vol"
        else:
            kind = "flat"
        markets.append({
            "name": clip(c.get("title", ""), 10),
            "last": ys[-1],
            "pct": round(pct, 2),
            "kind": kind,
            "arr": arr,
        })
        if len(markets) == 4:
            break
    return {"markets": markets}

