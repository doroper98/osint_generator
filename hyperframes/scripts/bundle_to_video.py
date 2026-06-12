"""bundle_to_video — agents_reviewer report_bundle → HyperFrames 브리핑 컴포지션 (v0.36.0).

옵션 C(번들 → 영상 자동 변환)의 1차 결정론 변환기. LLM 없이 번들 필드만으로
씬 플랜·cue·테마를 추출해 `hyperframes/briefing/auto.html` 을 생성한다.

핵심 원칙:
    - **데이터에 있는 씬만 만든다** — 이 번들에 지도가 없으면 지도 씬도 없다.
    - CSS 는 briefing/index.html 의 <style> 블록을 그대로 재사용 (테마 SSOT).
    - 씬 조립 로직은 assets/auto_builder.js (정적) — 본 변환기는 DATA 만 생성.

사용:
    python hyperframes/scripts/bundle_to_video.py <bundle.json>
    (이후) cd hyperframes/briefing && npx hyperframes render -c auto.html
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
BRIEFING = REPO / "hyperframes" / "briefing"

# ── 텍스트 유틸 ──────────────────────────────────────────────


def char_units(ch: str) -> float:
    """SceneKit.estTextWidth 와 같은 결정론 폭 추정 (em 단위)."""
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7A3 or 0x4E00 <= o <= 0x9FFF or 0x3000 <= o <= 0x303F:
        return 1.0
    if ch == "·":
        return 0.42
    if ch.isdigit():
        return 0.62
    if ch == " ":
        return 0.3
    if ch.isupper():
        return 0.74
    if ch.islower():
        return 0.56
    return 0.5


def est_units(text: str) -> float:
    return sum(char_units(c) for c in text)


def clip(text: str, n: int) -> str:
    text = text.strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?다])\s+", text.strip()) if s.strip()]


def wrap_units(text: str, max_units: float) -> list[str]:
    """공백 단위 greedy wrap (keep-all)."""
    words = text.split(" ")
    lines: list[str] = []
    cur = ""
    for w in words:
        cand = (cur + " " + w) if cur else w
        if cur and est_units(cand) > max_units:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def date_kr(iso: str) -> str:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso)
    if not m:
        return iso
    return f"{int(m.group(2))}월 {int(m.group(3))}일"


# ── 추출기 ──────────────────────────────────────────────────


def build_title(report: dict, sections: list, date_str: str) -> dict:
    headline = report["headline"]
    # 94px 헤드라인 — 한 줄 최대 약 17 유닛
    raw_lines = wrap_units(headline, 17.0)[:3]
    lines = []
    for i, ln in enumerate(raw_lines):
        em = 1 if i == len(raw_lines) - 1 else 0  # 마지막 줄 강조
        lines.append([[ln, em]])
    words = headline.split(" ")
    watermark = "\n".join(words[-2:]) if len(words) >= 2 else headline
    kicker = (sections[0].get("kicker") or "리서치 브리핑") if sections else "리서치 브리핑"
    return {
        "kicker": f"{kicker} · {date_str}",
        "lines": lines,
        "deck": clip(report.get("deck", ""), 160),
        "watermark": watermark,
    }


def pick_timeline_steps(points: list, limit: int = 7) -> list:
    pts = sorted(points, key=lambda p: p.get("date", ""))
    if len(pts) <= limit:
        return pts
    non_past = [p for p in pts if p.get("phase") != "past"]
    past = [p for p in pts if p.get("phase") == "past"]
    if len(non_past) > limit - 2:
        non_past = non_past[: limit - 2]
    slots = limit - len(non_past)
    chosen_past = []
    if past and slots > 0:
        if slots >= len(past):
            chosen_past = past
        else:
            # 처음 포함, 균등 샘플
            idxs = sorted({round(i * (len(past) - 1) / (slots - 1)) for i in range(slots)}) if slots > 1 else [0]
            chosen_past = [past[i] for i in idxs]
    merged = sorted(chosen_past + non_past, key=lambda p: p.get("date", ""))
    return merged[:limit]


def build_ladder(timeline: dict, limit: int = 7) -> dict:
    steps = []
    for p in pick_timeline_steps(timeline.get("points", []), limit):
        steps.append({
            "date": p.get("date", "").replace("-", "."),
            "label": clip(p.get("label", ""), 44),
            "phase": p.get("phase", "past"),
        })
    return {"steps": steps}


VIDEO_THEMES = {"ink_brass", "graphite_slate", "midnight_navy", "forest_archive", "paper_oxblood"}

# 번들 테마 id → 영상 테마 프리셋 별칭 (색 계열 매칭)
THEME_ALIASES = {"forest_sage": "forest_archive", "midnight_indigo": "midnight_navy"}

NUM_TOKEN = re.compile(r"\d[\d,\.]*")

# ── TTS 발음 표기 (템플릿 cue 용 — 계약 narration_tts 와 동일 철학) ──
sys.path.insert(0, str(REPO))
from orchestrator.tts_pronounce import apply_pronunciation, load_dict, num_to_sino_kr  # noqa: E402

_PRONOUNCE = load_dict(REPO / "hyperframes" / "demo" / "assets" / "pronounce.json")
_NATIVE = ["", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열",
           "열한", "열두", "열세", "열네", "열다섯", "열여섯", "열일곱", "열여덟", "열아홉", "스무"]


def native_count(n: int) -> str:
    """수사+단위(개/곳/가지)용 고유어 — '7개'를 '칠 개'가 아니라 '일곱 개'로."""
    return _NATIVE[n] if 0 < n <= 20 else None  # 초과는 한자어로 폴백


def josa(word: str, with_jong: str, without_jong: str) -> str:
    """받침 유무로 조사 선택 (이/가, 은/는, 을/를)."""
    if not word:
        return without_jong
    o = ord(word[-1])
    if 0xAC00 <= o <= 0xD7A3 and (o - 0xAC00) % 28:
        return with_jong
    return without_jong


# 월 발음 — 6월(유월)·10월(시월) 불규칙 포함. "육 월 오 일" 끊어 읽기 방지 (TTS-AP-054 계열)
_MONTH_KR = {1: "일월", 2: "이월", 3: "삼월", 4: "사월", 5: "오월", 6: "유월",
             7: "칠월", 8: "팔월", 9: "구월", 10: "시월", 11: "십일월", 12: "십이월"}


def _date_kr_tts(m: re.Match) -> str:
    mon = _MONTH_KR.get(int(m.group(1)), m.group(1) + "월")
    day = num_to_sino_kr(int(m.group(2)))
    return f"{mon} {day}일"


def tts_of(text: str) -> str:
    """템플릿 문장 → 발음 표기: 날짜/부호/소수점 정리 후 사전+숫자 한글화."""
    s = text.replace("+", " 플러스 ").replace("−", " 마이너스 ")
    s = re.sub(r"(\d{1,2})월\s*(\d{1,2})일", _date_kr_tts, s)
    s = re.sub(r"(?<![\d가-힣])(\d{1,2})월", lambda m: _MONTH_KR.get(int(m.group(1)), m.group(0)), s)
    s = re.sub(r"(?<=\d)\.(?=\d)", " 점 ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return apply_pronunciation(s, _PRONOUNCE)



def build_corpus(b: dict) -> str:
    """검증용 말뭉치 — 번들 전체를 콤마/공백 제거 직렬화."""
    return re.sub(r"[,\s]", "", json.dumps(b, ensure_ascii=False))


def sentence_grounded(sent: str, corpus: str) -> bool:
    """계약 G4: 문장 속 모든 수치 토큰이 번들에 실재해야 한다."""
    for tok in NUM_TOKEN.findall(sent):
        norm = tok.replace(",", "").rstrip(".")
        if norm and norm not in corpus:
            return False
    return True


def em_segments_line(text: str, emphasis: list[str]) -> list:
    """emphasis 부분 문자열을 em=1 세그먼트로 분할한 한 줄."""
    spans = []
    for term in emphasis or []:
        start = 0
        while term:
            i = text.find(term, start)
            if i < 0:
                break
            spans.append((i, i + len(term)))
            start = i + len(term)
    spans.sort()
    # 겹침 제거
    merged = []
    for a, bnd in spans:
        if merged and a < merged[-1][1]:
            continue
        merged.append((a, bnd))
    segs = []
    pos = 0
    for a, bnd in merged:
        if a > pos:
            segs.append([text[pos:a], 0])
        segs.append([text[a:bnd], 1])
        pos = bnd
    if pos < len(text):
        segs.append([text[pos:], 0])
    return segs or [[text, 0]]


def section_videos(sections: list, corpus: str) -> dict:
    """계약 video 필드 수집 + 사실 근거 검증. 위반 문장은 폐기."""
    out = {}
    dropped = 0
    for s in sections:
        v = s.get("video")
        if not isinstance(v, dict):
            continue
        narr = []
        tts_src = v.get("narration_tts") or []
        for i, sent in enumerate(v.get("narration") or []):
            sent = clip(str(sent), 75)
            if not sentence_grounded(sent, corpus):
                dropped += 1
                continue
            narr.append({"text": sent,
                         "tts": clip(str(tts_src[i]), 120) if i < len(tts_src) else None})
        his = []
        for h in (v.get("highlights") or [])[:3]:
            h = clip(str(h), 40)
            if sentence_grounded(h, corpus):
                his.append(h)
            else:
                dropped += 1
        if narr or his:
            out[s.get("section_id")] = {
                "narration": narr, "highlights": his,
                "emphasis": [str(e) for e in (v.get("emphasis") or [])],
            }
    if dropped:
        print(f"[bundle_to_video] 검증기: 근거 불일치 문장 {dropped}건 폐기 → 템플릿 폴백")
    return out

TIMELINE_LIMITS = {"ladder": 7, "axis": 7, "serpentine": 10, "vertical": 6, "metro": 7}


def timeline_kind(points: list, override: str | None = None) -> str:
    """타임라인 시각화 5유형 자동 선택.

    - ladder     : crack+present 공존 — 에스컬레이션 서사 (계단)
    - serpentine : 분기점 11개 이상 — 2단 S자 흐름
    - vertical   : 라벨이 긴 설명형 (평균 26자 초과) — 기사 레일
    - metro      : 미래 비중 40% 이상 — 국면 구간 색 노선도
    - axis       : 그 외 중립 시계열 — 수평 축
    """
    if override:
        return override
    phases = {p.get("phase") for p in points}
    n = len(points)
    if {"crack", "present"} <= phases:
        return "ladder"
    if n >= 11:
        return "serpentine"
    avg_label = sum(len(p.get("label", "")) for p in points) / max(1, n)
    if avg_label > 26:
        return "vertical"
    fut = sum(1 for p in points if p.get("phase") == "future")
    if fut / max(1, n) >= 0.4:
        return "metro"
    return "axis"


UNIT_RE = re.compile(r"[(（]단위[:：]\s*([^)）]+)[)）]")


def split_unit(title: str) -> tuple[str, str]:
    m = UNIT_RE.search(title)
    unit = m.group(1).strip() if m else ""
    return UNIT_RE.sub("", title).strip(), unit


def build_candle(charts: list) -> dict | None:
    c = next((c for c in charts if c.get("type") == "candle" and isinstance(c.get("data"), list)), None)
    if not c or len(c["data"]) < 10:
        return None
    ohlc = [{k: d[k] for k in ("date", "open", "high", "low", "close")} for d in c["data"]]
    return {"title": c.get("title", ""), "ohlc": ohlc, "chart_id": c.get("chart_id")}


def build_bar_panels(charts: list) -> list:
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
    """YYYY-MM-DD 또는 YYYY-MM(월 단위 → 1일/28일 보정)."""
    if not DATE_RE.match(s):
        return None
    return s if len(s) == 10 else s + ("-28" if end else "-01")


def norm_gantt(c: dict, today: str | None) -> dict | None:
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


EXTRA_CHART_SCENES = {
    "stacked": ("stacked", "구성", "구성으로 보면 이렇게 나뉩니다"),
    "stacked_bar": ("stacked", "구성", "구성으로 보면 이렇게 나뉩니다"),
    "waterfall": ("waterfall", "증감", "증감을 다리로 이으면 흐름이 보입니다"),
    "scatter": ("scatter", "분포", "분포로 놓으면 각자의 위치가 드러납니다"),
    "heatmap": ("heatmap", "강도", "강도의 지도로 보면 쏠림이 보입니다"),
    "gantt": ("gantt", "일정", "남은 일정을 레인으로 펼칩니다"),
}


def build_signals(signals: list) -> dict | None:
    if not signals:
        return None
    items = [{
        "when": clip(s.get("deadline", ""), 14),
        "name": clip(s.get("signal", ""), 26),
        "desc": clip(s.get("description", ""), 56),
        "unverified": s.get("verification") == "unverified",
    } for s in signals[:5]]
    return {"items": items}


def build_slopes(charts: list) -> list:
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


def section_for_chart(sections: list, chart_id: str):
    for s in sections:
        if chart_id in (s.get("chart_refs") or []):
            return s
    return None


def build_versus(contradiction: dict, theme: dict) -> dict:
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
             "line": line_a, "stance": stance_a[0], "stanceLabel": stance_a[1], "color": up},
            {"initials": names[1][:2], "name": names[1], "org": org_b or "소수 진영",
             "line": line_b, "stance": stance_b[0], "stanceLabel": stance_b[1], "color": "#8d99ae"},
        ],
    }


def build_markets(charts: list) -> dict:
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


EM_NUM = re.compile(r"\d[\d,\.]*\s?(?:조원|만원|억원|원|%|배|달러)")


def quote_segments(text: str) -> list:
    """숫자+단위를 강조(em) 세그먼트로 분할."""
    segs = []
    pos = 0
    for m in EM_NUM.finditer(text):
        if m.start() > pos:
            segs.append([text[pos:m.start()], 0])
        segs.append([m.group(0), 1])
        pos = m.end()
    if pos < len(text):
        segs.append([text[pos:], 0])
    return [segs or [[text, 0]]]


def build_closing(report: dict, sections: list, confidence: dict, skip_pq: bool = False) -> dict:
    pq = None if skip_pq else next((s.get("pull_quote") for s in sections if s.get("pull_quote")), None)
    quote_text = clip(pq or sentences(report.get("closing", ""))[0], 90)
    closing_sents = sentences(report.get("closing", ""))
    return {
        "quote": quote_segments(quote_text),
        "closing": clip(" ".join(closing_sents[:2]), 170),
        "confidence": {
            "score": confidence.get("score", 0.0),
            "desc": clip(confidence.get("summary", ""), 110),
        },
    }


def find_section(sections: list, keywords: list[str], default: tuple[str, str]) -> tuple[str, str, str | None]:
    for s in sections:
        hay = (s.get("kicker") or "") + (s.get("heading") or "")
        if any(k in hay for k in keywords):
            return (s.get("kicker") or default[0], s.get("heading") or default[1],
                    s.get("section_id"))
    return default[0], default[1], None


# ── 메인 ────────────────────────────────────────────────────


def convert(bundle_path: Path, out_path: Path, tl_override: str | None = None,
            theme_override: str | None = None, cuesync: dict | None = None) -> dict:
    b = json.loads(bundle_path.read_text(encoding="utf-8"))
    report = b["report"]
    sections = b.get("sections", [])
    theme = report.get("theme", {})
    tokens = theme.get("tokens", {})
    gen = b.get("generated_at", "")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", gen)
    date_dot = f"{m.group(1)}.{m.group(2)}.{m.group(3)}" if m else ""
    date_kor = f"{int(m.group(1))}년 {int(m.group(2))}월 {int(m.group(3))}일" if m else ""

    # 비디오 테마: 번들 theme.id 가 프리셋과 일치하면 그대로, 아니면 ink_brass +
    # 번들 토큰(accent/up/down)만 오버라이드. --video-theme 가 최우선.
    bundle_tid = (theme.get("id") or "").strip()
    bundle_tid = THEME_ALIASES.get(bundle_tid, bundle_tid)
    if theme_override and theme_override in VIDEO_THEMES:
        theme_id = theme_override
        theme_vars = {}
    elif bundle_tid in VIDEO_THEMES:
        theme_id = bundle_tid
        theme_vars = {}
    else:
        theme_id = "ink_brass"
        theme_vars = {}
        if tokens.get("accent"):
            theme_vars["--accent"] = tokens["accent"]
        if tokens.get("up"):
            theme_vars["--sage"] = tokens["up"]
        if tokens.get("down"):
            theme_vars["--oxide"] = tokens["down"]

    # ── 계약 video 필드 (v0.38.0) — 검증 후 수집 ──
    corpus = build_corpus(b)
    svideos = section_videos(sections, corpus)
    report_video = report.get("video") or {}

    def grounded_narr(vdict, key="narration"):
        out = []
        tts_src = vdict.get(key + "_tts") or []
        for i, sent in enumerate(vdict.get(key) or []):
            sent = clip(str(sent), 75)
            if sentence_grounded(sent, corpus):
                out.append({"text": sent,
                            "tts": clip(str(tts_src[i]), 120) if i < len(tts_src) else None})
        return out

    intro_narr = grounded_narr(report_video, "intro_narration")
    outro_narr = grounded_narr(report_video, "outro_narration")
    # 계약 확장: timeline.video.narration (검수 반영 — 분기점 라벨 낭독 대체)
    timeline_narr = grounded_narr((b.get("timeline") or {}).get("video") or {})

    # ── 씬 플랜 (데이터에 있는 것만) ──
    scenes = []
    cues = []
    t = 0.0

    def add_scene(stype, dur, chip_label, head, data, sid=None):
        nonlocal t
        scenes.append({
            "type": stype, "t0": round(t, 2), "t1": round(t + dur, 2),
            "no": f"{len(scenes) + 1:02d}", "chip": f"{len(scenes) + 1:02d} · {chip_label}",
            "head": head, "data": data, "_sid": sid,
        })
        t += dur

    def tcue(at, text, tts=None):
        return {"t": at, "text": text, "tts": tts or tts_of(text)}

    # 1. 타이틀 (항상)
    title = build_title(report, sections, date_kor)
    add_scene("title", 9, "타이틀", None, title, sid="__intro")
    deck_sents = sentences(report.get("deck", ""))
    cues.append(tcue(0.8, clip(deck_sents[0], 58)))
    if len(deck_sents) > 1:
        cues.append(tcue(4.6, clip(deck_sents[1], 58)))

    charts = b.get("charts") or []

    # 2. 타임라인 — 유형 자동 선택 (에스컬레이션 서사 = 계단 / 중립 시계열 = 수평 축)
    tl_data = b.get("timeline") or {}
    if tl_data.get("points"):
        t0 = t
        kind = timeline_kind(tl_data["points"], tl_override)
        ladder = build_ladder(tl_data, TIMELINE_LIMITS.get(kind, 7))
        head = ("Timeline", tl_data.get("heading", "사건의 궤적"))
        add_scene(kind, 11, "타임라인", {"kicker": head[0], "title": head[1]}, ladder,
                  sid="__timeline")
        n = len(ladder["steps"])
        nat = native_count(n)
        cues.append(tcue(t0 + 0.6,
                         f"이 흐름이 어떻게 쌓여 왔는지, {n}개의 분기점으로 따라가 보겠습니다.",
                         tts=tts_of(f"이 흐름이 어떻게 쌓여 왔는지, {nat or n} 개의 분기점으로 따라가 보겠습니다.")))
        key = next((s for s in ladder["steps"] if s["phase"] in ("present", "crack")), None)
        if key:
            kd = date_kr(key["date"].replace(".", "-"))
            cues.append(tcue(t0 + 4.4, clip(
                f"{kd}에는 {key['label']}{josa(key['label'], '이', '가')} 있었습니다.", 75)))
        fut = next((s for s in ladder["steps"] if s["phase"] == "future"), None)
        if fut:
            fd = date_kr(fut["date"].replace(".", "-"))
            cues.append(tcue(t0 + 8.0, clip(f"다음은 {fd}에 예정된 {fut['label']}입니다.", 75)))

    # 2-b. 인용 인터스티셜 (pull_quote 있으면 — 클로징은 폴백 인용 사용)
    pq = next((s.get("pull_quote") for s in sections if s.get("pull_quote")), None)
    if pq:
        t0 = t
        pq_sec = next((s for s in sections if s.get("pull_quote") == pq), None)
        add_scene("quote", 7, "인용", None, {
            "segments": quote_segments(clip(pq, 80)),
            "source": (pq_sec.get("kicker") if pq_sec else "") or "보고서 본문",
        }, sid=pq_sec.get("section_id") if pq_sec else None)
        cues.append(tcue(t0 + 0.8, clip(pq, 58)))

    # 3. 일봉 캔들 (candle 차트 있으면)
    candle = build_candle(charts)
    if candle:
        t0 = t
        sec = section_for_chart(sections, candle["chart_id"])
        k = (sec.get("kicker") if sec else None) or "Daily"
        h = (sec.get("heading") if sec else None) or candle["title"]
        add_scene("candle", 9, "일봉", {"kicker": k, "title": h},
                  {"ohlc": candle["ohlc"], "title": candle["title"]},
                  sid=sec.get("section_id") if sec else None)
        cues.append(tcue(t0 + 0.6, clip(f"{candle['title']} — 최근 {len(candle['ohlc'])}거래일의 흐름입니다.", 58)))
        closes = [d["close"] for d in candle["ohlc"]]
        chg = (closes[-1] / closes[0] - 1) * 100
        cues.append(tcue(t0 + 4.6, f"구간 등락은 {chg:+.1f}%, 종가 {round(closes[-1]):,}입니다."))

    # 4. 바 패널 (bar 차트 있으면 — 단일 + 듀얼)
    for bp in build_bar_panels(charts):
        t0 = t
        first_id = bp["panels"][0].get("chart_id")
        sec = section_for_chart(sections, first_id)
        k = (sec.get("kicker") if sec else None) or "전망"
        h = (sec.get("heading") if sec else None) or bp["panels"][0]["title"]
        dur = 9 if len(bp["panels"]) == 1 else 10
        add_scene("bars", dur, "전망" if len(bp["panels"]) == 1 else "목표가", {"kicker": k, "title": h}, bp, sid=sec.get("section_id") if sec else None)
        if len(bp["panels"]) == 1:
            pn = bp["panels"][0]
            top = max(pn["items"], key=lambda it: it["value"])
            cues.append(tcue(t0 + 0.6, clip(f"{pn['title']} — 상단은 {top['label']}, {top['value']:,}{pn['unit']}입니다.", 58)))
        else:
            # 패널(차트)별 상단/하단 비율 — 패널 간 혼합은 스케일이 달라 무의미
            ratios = []
            for pn in bp["panels"]:
                vals = [it["value"] for it in pn["items"]]
                if min(vals):
                    ratios.append((pn["title"], max(vals) / min(vals)))
            cues.append(tcue(t0 + 0.6, "같은 회사를 두고, 12개월 시선은 이렇게 벌어져 있습니다."))
            if ratios:
                wt, wr = max(ratios, key=lambda r: r[1])
                cues.append(tcue(t0 + 4.8, clip(f"{wt} — 상단과 하단이 {wr:.1f}배 차이입니다.", 58)))

    # 4-b. 슬로프 (slope 차트 있으면)
    for sl in build_slopes(charts):
        t0 = t
        sec = section_for_chart(sections, sl["chart_id"])
        k = (sec.get("kicker") if sec else None) or "변화 폭"
        h = (sec.get("heading") if sec else None) or sl["title"]
        add_scene("slope", 10, "상향 폭", {"kicker": k, "title": h},
                  {"left_label": sl["left_label"], "right_label": sl["right_label"], "items": sl["items"]},
                  sid=sec.get("section_id") if sec else None)
        hi = max(sl["items"], key=lambda it: abs(it["b"] - it["a"]))
        cues.append(tcue(t0 + 0.6, clip(f"{sl['title']} — {sl['left_label']}에서 {sl['right_label']}까지.", 58)))
        cues.append(tcue(t0 + 4.6, clip(f"가장 크게 움직인 건 {hi['label']}, {hi['a']:,}에서 {hi['b']:,}입니다.", 58)))

    # 4-c. 잔여 차트 유형 (stacked/waterfall/scatter/heatmap/gantt — 있으면)
    today_iso = m.group(0) if m else None
    for c in charts:
        ctype = c.get("type")
        if ctype not in EXTRA_CHART_SCENES:
            continue
        stype, chip_label, cue_tail = EXTRA_CHART_SCENES[ctype]
        norm = {"stacked": norm_stacked, "waterfall": norm_waterfall, "scatter": norm_scatter,
                "heatmap": norm_heatmap}.get(stype)
        d = norm_gantt(c, today_iso) if stype == "gantt" else (norm(c) if norm else None)
        if not d:
            continue
        t0 = t
        sec = section_for_chart(sections, c.get("chart_id"))
        title_clean = split_unit(c.get("title", ""))[0]
        k = (sec.get("kicker") if sec else None) or chip_label
        h = (sec.get("heading") if sec else None) or title_clean
        add_scene(stype, 9, chip_label, {"kicker": k, "title": h}, d,
                  sid=sec.get("section_id") if sec else None)
        cues.append(tcue(t0 + 0.6, clip(f"{title_clean} — {cue_tail}.", 58)))

    # 4-d. 스테이트먼트 (계약 video.highlights — 차트 없는 서술 섹션 구제)
    versus_k, versus_h, versus_sid = find_section(
        sections, ["강세", "보수", "쟁점", "대립", "해석"], ("쟁점", "갈리는 시각"))
    signals_k, signals_h, signals_sid = find_section(
        sections, ["신호", "감시", "Signal"], ("Signals", "무엇이 갈림길을 정하는가"))
    consumed = {sc.get("_sid") for sc in scenes}
    for s in sections:
        sid = s.get("section_id")
        sv = svideos.get(sid)
        if not sv or not sv["highlights"]:
            continue
        if sid in consumed or sid in (versus_sid, signals_sid):
            continue
        dur = min(14, max(9, 3 + 3.0 * len(sv["narration"])))
        add_scene("statement", dur, "키 포인트",
                  {"kicker": s.get("kicker") or "Key Point", "title": s.get("heading") or ""},
                  {"lines": [em_segments_line(h2, sv["emphasis"]) for h2 in sv["highlights"]]},
                  sid=sid)

    # 5. 쟁점 (contradictions 있으면)
    contras = b.get("contradictions") or []
    if contras:
        t0 = t
        versus = build_versus(contras[0], theme)
        k, h = versus_k, versus_h
        # 섹션 제목 "A인가, B인가" 패턴이면 양 진영 이름으로 사용
        mm = re.match(r"(.+?)인가[,，]?\s*(.+?)인가", h or "")
        if mm and versus["cards"][0]["name"].startswith("시각"):
            versus["cards"][0]["name"] = clip(mm.group(1).strip(), 12)
            versus["cards"][1]["name"] = clip(mm.group(2).strip(), 12)
            versus["cards"][0]["initials"] = versus["cards"][0]["name"][:2]
            versus["cards"][1]["initials"] = versus["cards"][1]["name"][:2]
        add_scene("versus", 12, "쟁점", {"kicker": k, "title": h}, versus, sid=versus_sid)
        a, bb = versus["cards"][0], versus["cards"][1]
        cues.append(tcue(t0 + 0.6, f"시각은 둘로 갈립니다 — {a['name']}과 {bb['name']}."))
        cues.append(tcue(t0 + 4.4, clip(f"{a['org']} — {a['line']}", 58)))
        cues.append(tcue(t0 + 8.2, clip(sentences(contras[0].get("resolution", ""))[0], 58)))

    # 6. 가격 비교 (line 차트 있으면)
    markets = build_markets(charts)
    if markets["markets"]:
        t0 = t
        line_sec = next((section_for_chart(sections, c.get("chart_id"))
                         for c in charts if c.get("type") == "line"), None)
        add_scene("markets", 10, "가격", {"kicker": "Relative", "title": "같은 기간, 가격의 궤적"},
                  markets, sid=line_sec.get("section_id") if line_sec else None)
        cues.append(tcue(t0 + 0.6, "같은 기간, 가격은 이렇게 움직였습니다."))
        top = max(markets["markets"], key=lambda mk: abs(mk["pct"]))
        cues.append(tcue(t0 + 4.6, f"가장 크게 움직인 건 {top['name']}, {top['pct']:+.1f}%입니다."))

    # 7. 관측 신호 (signals 있으면)
    sig = build_signals(b.get("signals") or [])
    if sig:
        t0 = t
        add_scene("signals", 10, "신호", {"kicker": signals_k, "title": signals_h}, sig,
                  sid=signals_sid)
        cues.append(tcue(t0 + 0.6, f"앞으로 확인할 신호 {len(sig['items'])}가지 — 전부 <미검증> 관측 대상입니다."))
        first = sig["items"][0]
        cues.append(tcue(t0 + 4.6, clip(f"가장 가까운 분기점은 {first['when']}, {first['name']}입니다.", 58)))

    # 5. 클로징 (항상)
    t0 = t
    closing = build_closing(report, sections, b.get("confidence") or {}, skip_pq=bool(pq))
    k, h = (sections[-1].get("kicker"), sections[-1].get("heading")) if sections else ("Outlook", "다음 좌표")
    add_scene("closing", 9, "향방", {"kicker": k or "Outlook", "title": h or "다음 좌표"}, closing, sid="__outro")
    cues.append(tcue(t0 + 0.4, clip(sentences(report.get("closing", ""))[0], 58)))
    cues.append(tcue(t0 + 4.2, f"신뢰도 {closing['confidence']['score']:.2f} — 근거와 한계는 화면과 같습니다."))

    # ── 계약 narration → cue 교체 (검증 통과 문장만, 섹션 시간창에 균등 배치) ──
    narration_map = {sid: sv for sid, sv in svideos.items() if sv.get("narration")}
    if intro_narr:
        narration_map["__intro"] = {"narration": intro_narr}
    if outro_narr:
        narration_map["__outro"] = {"narration": outro_narr}
    if timeline_narr:
        narration_map["__timeline"] = {"narration": timeline_narr}
    windows_by_sid: dict = {}
    for sc in scenes:
        sid = sc.get("_sid")
        if sid in narration_map:
            windows_by_sid.setdefault(sid, []).append((sc["t0"], sc["t1"]))
    replaced = [w for ws in windows_by_sid.values() for w in ws]
    kept = [c for c in cues if not any(w0 <= c["t"] < w1 for w0, w1 in replaced)]
    narr_cues = []
    for sid, ws in windows_by_sid.items():
        sents = narration_map[sid]["narration"]
        ws = sorted(ws)
        lens = [w1 - w0 - 1.4 for w0, w1 in ws]
        total_len = sum(lens) or 1.0
        rem = len(sents)
        idx = 0
        for wi, (w0, w1) in enumerate(ws):
            k_n = rem if wi == len(ws) - 1 else min(rem, round(len(sents) * lens[wi] / total_len))
            if k_n <= 0:
                continue
            step = lens[wi] / k_n
            for j in range(k_n):
                s2 = sents[idx]
                idx += 1
                cue = {"t": round(w0 + 0.5 + j * step, 2), "text": s2["text"]}
                if s2.get("tts"):
                    cue["tts"] = s2["tts"]
                narr_cues.append(cue)
            rem -= k_n
    if narr_cues:
        print(f"[bundle_to_video] 계약 narration 채택: {len(narr_cues)}문장 "
              f"(섹션 {len(windows_by_sid)}곳, 템플릿 cue {len(cues) - len(kept)}건 대체)")
    cues = sorted(kept + narr_cues, key=lambda c: c["t"])

    total = round(t, 2)

    # ── cuesync 적용 (내레이션 실측 시계 — build_auto_narration 산출) ──
    audio_src = None
    if cuesync:
        sd = cuesync.get("scene_durs") or []
        ct = cuesync.get("cue_times") or []
        if len(sd) != len(scenes) or len(ct) != len(cues):
            print(f"error: cuesync 불일치 (scenes {len(sd)}/{len(scenes)}, "
                  f"cues {len(ct)}/{len(cues)}). 동일 번들로 재생성 필요.", file=sys.stderr)
            sys.exit(1)
        acc = 0.0
        for sc, dur in zip(scenes, sd):
            sc["t0"] = round(acc, 2)
            sc["t1"] = round(acc + dur, 2)
            acc = round(acc + dur, 2)
        for c, ti in zip(cues, ct):
            c["t"] = round(ti, 2)
        cues.sort(key=lambda c: c["t"])
        total = round(cuesync.get("total", acc), 2)
        audio_src = cuesync.get("audio")
        print(f"[bundle_to_video] cuesync 적용: 씬 {len(sd)}개 재시계, total={total}s, "
              f"audio={audio_src}")

    # ── 출처 라인 ──
    pubs = []
    for s in b.get("sources", []):
        p = s.get("publisher")
        if p and p not in pubs:
            pubs.append(p)
    src1 = "출처 · " + " · ".join(pubs[:3]) + (f" 외 {len(b.get('sources', [])) - 3}개" if len(b.get("sources", [])) > 3 else "")
    src2 = "데이터 · agents_reviewer report_bundle · 미검증 영역은 <b>&lt;미검증&gt;</b> 표기 원칙"

    data = {
        "meta": {
            "brand": "OSINT BRIEFING",
            "sub": "리서치 브리핑",
            "date": date_dot,
            "sourceLine1": src1,
            "sourceLine2": src2,
        },
        "themeId": theme_id,
        "themeVars": theme_vars,
        "total": total,
        "scenes": scenes,
        "cues": cues,
        "audio": audio_src,
    }

    emit_html(data, out_path, bundle_path.name, report.get("report_id", ""))
    return data


def emit_html(data: dict, out_path: Path, src_name: str, report_id: str) -> None:
    """DATA → 컴포지션 HTML. CSS 는 briefing/index.html <style> 재사용 (테마 SSOT)."""
    total = data["total"]
    audio_tag = ""
    if data.get("audio"):
        audio_tag = (f'      <audio id="narration-auto" class="clip" data-start="0" '
                     f'data-duration="{data["total"]}" data-track-index="100" '
                     f'src="{data["audio"]}" preload="auto"></audio>')
    index_html = (BRIEFING / "index.html").read_text(encoding="utf-8")
    css = re.search(r"<style>.*?</style>", index_html, re.DOTALL).group(0)
    # 렌더러가 body 끝 외부 <script src> 를 실행하지 않는 사고(v0.36.0 빈 렌더)
    # → 빌더를 인라인으로 박는다. SSOT 는 assets/auto_builder.js.
    builder_js = (BRIEFING / "assets" / "auto_builder.js").read_text(encoding="utf-8")

    html = f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <!-- 자동 생성: bundle_to_video.py — {src_name}
         report_id: {report_id}
         수정 금지. 변환기를 고치고 재실행할 것. -->
    <link rel="stylesheet" href="assets/noto_serif_kr.css" />
    <script src="assets/gsap.min.js"></script>
    <script src="assets/scene_kit.js"></script>
    <script src="assets/themes.js"></script>
{css}
  </head>
  <body>
    <div id="root" class="clip" data-composition-id="autobrief" data-start="0"
         data-duration="{total}" data-track-index="0" data-width="1920" data-height="1080">
      <div id="bg">
        <svg id="grain" viewBox="0 0 1920 1080" preserveAspectRatio="none">
          <filter id="noiseFilter"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7" stitchTiles="stitch"/></filter>
          <rect width="100%" height="100%" filter="url(#noiseFilter)"/>
        </svg>
        <div id="vignette"></div>
      </div>
      <div id="prog"></div>
      <div class="topbar">
        <div class="brand">
          <span class="brand-mark"></span>
          <span class="brand-name" id="brand-name"></span>
          <span class="brand-sub" id="brand-sub"></span>
        </div>
        <div class="topright">
          <span class="chip" id="scene-chip"><span class="dot"></span><span id="scene-label"></span></span>
          <span id="top-date"></span>
        </div>
      </div>
      <div class="toprule"></div>
      <div id="stage"></div>
      <div id="scrim"></div>
      <div class="subwrap"><div class="subbar"></div><div id="cap"></div></div>
      <div class="source"><span id="source-line1"></span><br/><span id="source-line2"></span></div>
{audio_tag}
    </div>
    <script>window.BRIEFING_DATA = {json.dumps(data, ensure_ascii=False)};</script>
    <script>
{builder_js}
    </script>
  </body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


def preview_charts(out_path: Path, theme_id: str = "ink_brass") -> dict:
    """신규 차트 5유형 비주얼 검증용 갤러리 컴포지션 (합성 데이터, 결정론)."""
    scenes = []
    cues = []
    t = 0.0

    def add(stype, dur, chip_label, head, data, cue):
        nonlocal t
        scenes.append({"type": stype, "t0": round(t, 2), "t1": round(t + dur, 2),
                       "no": f"{len(scenes) + 1:02d}",
                       "chip": f"{len(scenes) + 1:02d} · {chip_label}",
                       "head": head, "data": data})
        cues.append(tcue(round(t + 0.6, 2), cue))
        t += dur

    add("stacked", 9, "구성", {"kicker": "Stacked", "title": "HBM 출하 구성 — 세대 교체의 속도"},
        {"unit": "만", "rows": [
            {"label": "2024", "segments": [{"name": "HBM3", "value": 62}, {"name": "HBM3E", "value": 18}, {"name": "기타", "value": 20}]},
            {"label": "2025", "segments": [{"name": "HBM3", "value": 30}, {"name": "HBM3E", "value": 58}, {"name": "기타", "value": 12}]},
            {"label": "2026E", "segments": [{"name": "HBM3", "value": 12}, {"name": "HBM3E", "value": 56}, {"name": "HBM4", "value": 30}]},
        ]},
        "세대별 구성으로 보면 교체의 속도가 드러납니다.")

    add("waterfall", 9, "증감", {"kicker": "Waterfall", "title": "영업이익 브리지 — 1분기에서 2분기로"},
        {"unit": "조", "items": [
            {"label": "1Q 실적", "value": 67, "kind": "start"},
            {"label": "DRAM", "value": 18, "kind": "delta"},
            {"label": "HBM", "value": 21, "kind": "delta"},
            {"label": "NAND", "value": 9, "kind": "delta"},
            {"label": "환영향", "value": -6, "kind": "delta"},
            {"label": "2Q 전망", "value": 109, "kind": "total"},
        ]},
        "증감을 다리로 이으면 어디서 늘었는지 보입니다.")

    add("scatter", 9, "분포", {"kicker": "Scatter", "title": "증권사 목표가 — 직전 대비 어디로 옮겼나"},
        {"xLabel": "직전 목표가(만원)", "yLabel": "최근 목표가(만원)", "diagonal": True,
         "points": [
             {"x": 234, "y": 400, "label": "노무라", "hi": True},
             {"x": 300, "y": 380, "label": "KB증권"},
             {"x": 205, "y": 380, "label": "한국투자"},
             {"x": 170, "y": 310, "label": "씨티"},
             {"x": 260, "y": 340, "label": "골드만"},
             {"x": 210, "y": 210, "label": "모건스탠리", "hi": True},
         ]},
        "대각선 위쪽은 전부 상향 — 한 점만 제자리입니다.")

    add("heatmap", 9, "강도", {"kicker": "Heatmap", "title": "지표별 모멘텀 — 어디가 뜨거운가"},
        {"rows": ["가격", "수급", "실적", "심리"],
         "cols": ["1월", "2월", "3월", "4월", "5월", "6월"],
         "values": [[1, 2, -1, 3, 4, -2], [0, 1, 2, 3, 2, -1],
                    [1, 1, 2, 4, 5, 4], [2, -1, 1, 3, 4, -3]]},
        "강도의 지도로 보면 쏠림과 균열이 같이 보입니다.")

    add("gantt", 9, "일정", {"kicker": "Gantt", "title": "남은 분기점 — 검증의 달력"},
        {"today": "2026-06-11", "tasks": [
            {"label": "D램 판가 집계", "start": "2026-07-01", "end": "2026-07-15", "phase": "future"},
            {"label": "2Q 잠정실적", "start": "2026-07-25", "end": "2026-07-31", "phase": "future"},
            {"label": "엔비디아 실적", "start": "2026-08-20", "end": "2026-08-26", "phase": "future"},
            {"label": "HBM4 수율 검증", "start": "2026-06-11", "end": "2026-09-30", "phase": "present"},
        ]},
        "남은 일정을 레인으로 펼치면 검증의 달력이 됩니다.")

    data = {
        "meta": {"brand": "OSINT BRIEFING", "sub": "차트 갤러리", "date": "2026.06.12",
                 "sourceLine1": "데이터 · 합성 샘플 (비주얼 검증용)",
                 "sourceLine2": "신규 차트 5유형 — stacked / waterfall / scatter / heatmap / gantt"},
        "themeId": theme_id,
        "themeVars": {},
        "total": round(t, 2),
        "scenes": scenes,
        "cues": cues,
    }
    emit_html(data, out_path, "preview_charts (synthetic)", "preview")
    return data


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else "")
             for a in sys.argv[1:] if a.startswith("--")}
    if "--preview-charts" in flags:
        out = Path(args[0]) if args else BRIEFING / "preview_charts.html"
        data = preview_charts(out, flags.get("--video-theme") or "ink_brass")
        print(f"[bundle_to_video] preview-charts scenes={[s['type'] for s in data['scenes']]} "
              f"total={data['total']}s -> {out}")
        return 0
    if not args:
        print("usage: python bundle_to_video.py <bundle.json> [out.html] "
              "[--timeline=ladder|axis|serpentine|vertical|metro] "
              "[--video-theme=...] [--narration=estimate|synth] [--cuesync=path] "
              "| --preview-charts [out.html]",
              file=sys.stderr)
        return 1
    bundle = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else BRIEFING / "auto.html"

    def run_convert(cs: dict | None = None) -> dict:
        return convert(bundle, out, tl_override=flags.get("--timeline") or None,
                       theme_override=flags.get("--video-theme") or None, cuesync=cs)

    narration = flags.get("--narration")  # estimate | synth
    cuesync_flag = flags.get("--cuesync")
    if narration:
        import subprocess
        run_convert()  # 1차: cue 확정
        cmd = [sys.executable, str(Path(__file__).parent / "build_auto_narration.py"), str(out)]
        if narration == "estimate":
            cmd.append("--estimate")
        rc = subprocess.run(cmd).returncode
        if rc != 0:
            return rc
        cuesync_flag = str(BRIEFING / "cuesync_auto.json")
    cs = json.loads(Path(cuesync_flag).read_text(encoding="utf-8")) if cuesync_flag else None
    data = run_convert(cs)
    print(f"[bundle_to_video] theme={data['themeId']} "
          f"scenes={[s['type'] for s in data['scenes']]} "
          f"total={data['total']}s cues={len(data['cues'])} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
