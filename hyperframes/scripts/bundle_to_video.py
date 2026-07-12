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
    # 구두점(. ! ?) 뒤에서만 분할 — 바 "다 "(보다/한다 중간) 오분할 방지
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


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


VIDEO_THEMES = {"ink_brass", "graphite_slate", "midnight_navy", "forest_archive", "paper_oxblood",
                # 르포(reportage) 8종 — agents_reviewer 르포 테마 팔레트 (v0.44.0)
                "reportage_cyprus", "reportage_noturno", "reportage_bridal", "reportage_cosmos",
                "reportage_laurel", "reportage_princess", "reportage_steel", "reportage_navy"}

# 번들 테마 id → 영상 테마 프리셋 별칭 (색 계열 매칭)
THEME_ALIASES = {"forest_sage": "forest_archive", "midnight_indigo": "midnight_navy",
                 # agents_reviewer 비-르포 테마 id → 가장 가까운 영상 팔레트 (v0.44.0)
                 "pine_forest": "forest_archive", "burgundy_mono": "reportage_bridal",
                 "editorial_cream": "paper_oxblood"}

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


# 표기 정규화 — 번들 transliteration 을 영상 표기로 (검수 반영)
_DISPLAY_NORMALIZE = {"장보고-엔": "장보고 N", "장보고 엔": "장보고 N",
                      "오커스(AUKUS)": "AUKUS", "오커스 (AUKUS)": "AUKUS", "오커스": "AUKUS"}


def normalize_display(text: str) -> str:
    for a, b in _DISPLAY_NORMALIZE.items():
        text = text.replace(a, b)
    return text


def iso_to_kr(s: str) -> str:
    """ISO 날짜(YYYY-MM-DD) → 'M월 D일' 표시. 그 외는 원본."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})$", s.strip())
    return f"{int(m.group(2))}월 {int(m.group(3))}일" if m else s


def _date_kr_tts(m: re.Match) -> str:
    mon = _MONTH_KR.get(int(m.group(1)), m.group(1) + "월")
    day = num_to_sino_kr(int(m.group(2)))
    return f"{mon} {day}일"


# 고유어 수사를 쓰는 단위 (가지/개/곳/척/명/번 …) — "5가지" → "다섯 가지"
_NATIVE_UNITS = "가지|개|곳|척|명|번|살|발|건|차례|대"


def _native_unit(m: re.Match) -> str:
    n = int(m.group(1))
    nat = native_count(n)
    return f"{nat} {m.group(2)}" if nat else f"{num_to_sino_kr(n)} {m.group(2)}"


def _iso_date_tts(m: re.Match) -> str:
    mon = _MONTH_KR.get(int(m.group(2)), m.group(2) + "월")
    return f"{mon} {num_to_sino_kr(int(m.group(3)))}일"


def _slash_date_tts(m: re.Match) -> str:
    """'7/13' → '칠월 십삼일'. 월 1~12·일 1~31 아니면 원본 유지 (비율/분수 오변환 방지)."""
    mo, dy = int(m.group(1)), int(m.group(2))
    if not (1 <= mo <= 12 and 1 <= dy <= 31):
        return m.group(0)
    return f"{_MONTH_KR[mo]} {num_to_sino_kr(dy)}일"


def _decimal_tts(m: re.Match) -> str:
    """'168.49' → '백육십팔쩜사구' (TTS-AP-059). 소수점은 '쩜', 소수부는 자릿수별 낭독.
    붙여 써서 반박자 쉼·연음 끊김 방지."""
    intp = num_to_sino_kr(int(m.group(1)))
    frac = "".join(num_to_sino_kr(int(d)) for d in m.group(2))
    return f"{intp}쩜{frac}"


def tts_of(text: str) -> str:
    """템플릿/계약 문장 → 발음 표기: 부호/날짜/소수/수사 정리 후 사전+숫자 한글화.

    계약 narration_tts(producer 제공)에도 동일 적용 — 소수·슬래시날짜·말끝 '…' 을
    producer 가 안 풀어 보내도 소비측에서 마지막으로 교정 (멱등)."""
    s = normalize_display(text)
    # 구두점 — em대시/가운뎃점/화살괄호는 음성에서 어색 (검수 반영)
    s = s.replace("—", ", ").replace(" – ", ", ").replace(" - ", ", ")
    s = s.replace("·", ", ").replace("<", "").replace(">", "")
    s = s.replace("+", " 플러스 ").replace("−", " 마이너스 ")
    # 소수 (168.49 → 백육십팔쩜사구) — 날짜/단위 변환보다 먼저 (점 소실 방지)
    s = re.sub(r"(?<!\d)(\d+)\.(\d+)(?!\d)", _decimal_tts, s)
    # producer 가 이미 "십삼 점 일" 처럼 풀어 보낸 소수 — 한글 숫자 사이 " 점 "→"쩜"
    # (TTS-AP-059). 숫자가 남아있지 않아 위 규칙이 못 잡는 계약 tts 커버.
    _SINO = "영일이삼사오육칠팔구십백천만"
    s = re.sub(rf"([{_SINO}])\s*점\s*([{_SINO}])", r"\1쩜\2", s)
    # ISO 날짜 YYYY-MM-DD → "M월 D일" (연도 생략 — 근접 시점)
    s = re.sub(r"(\d{4})-(\d{2})-(\d{2})", _iso_date_tts, s)
    # 슬래시 날짜 M/D → "M월 D일" ('분기' 앞은 제외 = 1/4분기 오변환 방지)
    s = re.sub(r"(?<!\d)(\d{1,2})/(\d{1,2})(?!\d)(?!\s*분기)", _slash_date_tts, s)
    s = re.sub(r"(\d{1,2})월\s*(\d{1,2})일", _date_kr_tts, s)
    s = re.sub(r"(?<![\d가-힣])(\d{1,2})월", lambda m: _MONTH_KR.get(int(m.group(1)), m.group(0)), s)
    # 고유어 수사 (사전/한자어 변환 전에)
    s = re.sub(rf"(\d{{1,2}})\s*({_NATIVE_UNITS})", _native_unit, s)
    # 말끝 정리 — 절단 표식 '…'/'...' 은 음성에서 말이 끊긴 것처럼 들리므로 제거 (TTS-AP-060)
    s = s.replace("…", " ").replace("...", " ")
    s = re.sub(r"[\s,]*(?:플러스|및|와|과)\s*$", "", s)  # 절단으로 남은 접속 꼬리 제거
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"\s+", " ", apply_pronunciation(s, _PRONOUNCE)).strip()



# 논설체 → 다큐 경어체 (versus 등 원문 노출 cue/카드 용 — 반말 사고 해소)
# 구체 규칙이 먼저, 일반 규칙(마지막 폴백)이 나중 — 순서 뒤집히면 "본다"→"본습니다"
# 처럼 일반 규칙이 구체 규칙을 가려버린다 (TTS-AP-061).
_POLITE_TAIL = [
    (re.compile(r"이다\.?$"), "입니다."),
    (re.compile(r"한다\.?$"), "합니다."), (re.compile(r"된다\.?$"), "됩니다."),
    (re.compile(r"본다\.?$"), "봅니다."), (re.compile(r"있다\.?$"), "있습니다."),
    (re.compile(r"없다\.?$"), "없습니다."), (re.compile(r"크다\.?$"), "큽니다."),
    (re.compile(r"높다\.?$"), "높습니다."), (re.compile(r"낮다\.?$"), "낮습니다."),
    (re.compile(r"같다\.?$"), "같습니다."), (re.compile(r"든다\.?$"), "듭니다."),
    (re.compile(r"하다\.?$"), "합니다."),  # 우세하다→우세합니다 등 '하다' 류
    (re.compile(r"([가-힣])다\.?$"), r"\1습니다."),  # 일반 폴백 — 반드시 마지막
]


def to_polite(text: str) -> str:
    """문장 종결을 다큐 경어체로. 끝맺지 않은(절단된) 문장은 그대로."""
    s = text.strip()
    for rx, rep in _POLITE_TAIL:
        if rx.search(s):
            return rx.sub(rep, s)
    return s


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


# 번들 narration 어구 안전망 — A 미반영분 교정 (검수: "물러설 한계선" 등 비문)
_PHRASING_FIXES = [
    (re.compile(r"물러설 (한계선|선|지점|영역|레드라인)"), r"물러설 수 없는 \1"),
    (re.compile(r"양보할 (한계선|선|지점)"), r"양보할 수 없는 \1"),
]


def fix_phrasing(text: str) -> str:
    for rx, rep in _PHRASING_FIXES:
        text = rx.sub(rep, text)
    return text


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
            sent = fix_phrasing(clip(str(sent), 75))
            if not sentence_grounded(sent, corpus):
                dropped += 1
                continue
            narr.append({"text": sent,
                         "tts": fix_phrasing(clip(str(tts_src[i]), 120)) if i < len(tts_src) else None})
        his = []
        for h in (v.get("highlights") or [])[:3]:
            h = fix_phrasing(clip(str(h), 40))
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


def norm_sankey(c: dict) -> dict | None:
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


EXTRA_CHART_SCENES = {
    "stacked": ("stacked", "구성", "구성으로 보면 이렇게 나뉩니다"),
    "stacked_bar": ("stacked", "구성", "구성으로 보면 이렇게 나뉩니다"),
    "waterfall": ("waterfall", "증감", "증감을 다리로 이으면 흐름이 보입니다"),
    "scatter": ("scatter", "분포", "분포로 놓으면 각자의 위치가 드러납니다"),
    "heatmap": ("heatmap", "강도", "강도의 지도로 보면 쏠림이 보입니다"),
    "gantt": ("gantt", "일정", "남은 일정을 레인으로 펼칩니다"),
}


def _strip_lead_date(s: str) -> str:
    """신호명 앞의 날짜 토큰(7/13 · 2026-07-13) 제거 — deadline(when)과 중복 낭독 방지."""
    return re.sub(r"^\s*(?:\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\s+", "", s.strip())


def build_signals(signals: list) -> dict | None:
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


def fetch_photos(b: dict, report_id: str, bundle_dir: Path | None = None) -> dict:
    """images[] 를 로컬 자산화 → {image_id: photo 씬 dict}. (IMAGE_BUNDLE_CONTRACT)

    권리 게이트(G4-8/C9): rights_status == "cleared" + credit 있는 사진만 사용.
    나머지·실패 건은 photos_manifest.json 에 사유와 함께 기록만 한다(추적성).
    섹션이 참조하지 않는 이미지는 받지 않는다.

    자산 확보 순서 — 원인① (사용자 결정 2026-07-12: "우리가 직접 찾는다").
    계약 §목적의 '영상 쪽 자동 스크래핑 금지' 대비 소비측 폴백 예외이며, LLM
    무호출·결정론(고정 URL → 고정 og:image)은 유지한다:
      1. url 이 http(s) 직링크면 그대로 다운로드.
      2. url 이 로컬 경로면 bundle_dir 기준으로 resolve 해 읽는다 (CWD 아님).
      3. 1·2 가 실패하고 source_id 로 원문 페이지 URL 을 알 수 있으면, 그 페이지의
         대표 이미지(og:image → twitter:image)를 직접 회수한다. 회수 사실은
         manifest 에 recovered="source_page" 로 남긴다.
    권리는 producer 가 이미 cleared(출처표기 갈음)로 판정하고 credit 이 화면에
    노출되므로, 같은 출처 도메인의 대표 이미지 회수는 §3.1-a 전제와 일치한다.
    """
    import urllib.request
    from urllib.parse import urljoin

    images = b.get("images") or []
    if not images:
        return {}
    referenced = {r for s in b.get("sections", []) for r in (s.get("image_refs") or [])}
    src_url_by_id = {s.get("source_id"): s.get("url")
                     for s in (b.get("sources") or []) if s.get("url")}
    photo_dir = BRIEFING / "assets" / "photos" / report_id
    out: dict = {}
    manifest = []
    ext_by_mime = {"image/jpeg": ".jpg", "image/png": ".png",
                   "image/webp": ".webp", "image/gif": ".gif"}

    def _http_image(u: str) -> tuple[bytes | None, str, str]:
        """직링크 다운로드 → (data, ext, reason). data 가 None 이면 reason 에 사유."""
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "osint-generator/0.44"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                mime = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
                data = resp.read(12 * 1024 * 1024 + 1)
        except Exception as e:  # 네트워크 실패는 폴백/스킵 — 파이프라인은 계속
            return None, "", f"다운로드 실패: {type(e).__name__}"
        if len(data) > 12 * 1024 * 1024:
            return None, "", "12MB 초과"
        if mime and not mime.startswith("image/"):
            return None, "", f"이미지 아님: {mime}"
        ext = ext_by_mime.get(mime) or (Path(u.split("?")[0]).suffix or ".jpg")
        return data, ext, ""

    def _og_image(page_url: str) -> str | None:
        """원문 페이지에서 대표 이미지 URL 추출 (og:image → twitter:image). 결정론."""
        try:
            req = urllib.request.Request(page_url,
                                         headers={"User-Agent": "osint-generator/0.44"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                ctype = resp.headers.get("Content-Type") or ""
                if ctype and "html" not in ctype:
                    return None
                html = resp.read(2 * 1024 * 1024).decode("utf-8", "ignore")
        except Exception:
            return None
        for pat in (
            r'<meta[^>]+property=["\']og:image(?::url)?["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::url)?["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        ):
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                return urljoin(page_url, m.group(1).strip())
        return None

    for im in images:
        iid = im.get("image_id") or ""
        url = im.get("url") or ""
        rights = im.get("rights_status") or "needs_review"
        entry = {"image_id": iid, "url": url, "caption": im.get("caption", ""),
                 "credit": im.get("credit", ""), "rights_status": rights,
                 "license": im.get("license", ""), "source_id": im.get("source_id", ""),
                 "used": False, "recovered": "", "reason": ""}
        manifest.append(entry)
        if not iid or not url:
            entry["reason"] = "image_id/url 누락"
            continue
        if rights != "cleared":
            entry["reason"] = f"권리 게이트: rights_status={rights} (cleared 만 사용)"
            continue
        if not (im.get("credit") or "").strip():
            # §3.1-a: cleared 의 근거가 출처표기 갈음이므로 credit 없는 cleared 는
            # 전제 불성립 — 소비측 fail-closed 이중화 (producer 보증과 별개).
            entry["reason"] = "credit 누락 — §3.1-a 출처표기 갈음 전제 불성립"
            continue
        if iid not in referenced:
            entry["reason"] = "어느 섹션도 참조하지 않음"
            continue

        data: bytes | None = None
        ext = ".jpg"
        fail_reason = ""
        # 1) http(s) 직링크
        if url.startswith(("http://", "https://")):
            data, ext, fail_reason = _http_image(url)
        else:
            # 2) 로컬 경로 — bundle_dir 기준 우선, 그다음 CWD (백필 오프라인 대비)
            cands = []
            p = Path(url)
            if bundle_dir is not None and not p.is_absolute():
                cands.append(bundle_dir / url)
            cands.append(p)
            src = next((c for c in cands if c.exists()), None)
            if src is not None:
                try:
                    data = src.read_bytes()
                    ext = src.suffix or ".jpg"
                except Exception as e:
                    fail_reason = f"로컬 읽기 실패: {type(e).__name__}"
            else:
                fail_reason = "로컬 파일 없음"

        # 3) 원문 페이지에서 대표 이미지 회수 (1·2 실패 시 — 원인① 폴백)
        if data is None:
            page = src_url_by_id.get(im.get("source_id"))
            if page and page.startswith(("http://", "https://")):
                og = _og_image(page)
                if og:
                    data, ext, r2 = _http_image(og)
                    if data is not None:
                        entry["recovered"] = "source_page"
                        entry["recovered_url"] = og
                    else:
                        fail_reason = f"원문 회수 실패: {r2}"
                else:
                    fail_reason = fail_reason or "원문 대표이미지 없음"

        if data is None:
            entry["reason"] = fail_reason or "자산 확보 실패"
            continue

        try:
            photo_dir.mkdir(parents=True, exist_ok=True)
            fname = f"{iid}{ext}"
            (photo_dir / fname).write_bytes(data)
        except Exception as e:
            entry["reason"] = f"저장 실패: {type(e).__name__}"
            continue

        entry["used"] = True
        out[iid] = {"src": f"assets/photos/{report_id}/{fname}",
                    "caption": clip(im.get("caption", ""), 60),
                    "credit": clip(im.get("credit", ""), 30),
                    "focus": im.get("focus", "center")}

    if manifest:
        photo_dir.mkdir(parents=True, exist_ok=True)
        (photo_dir / "photos_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        skipped = [m for m in manifest if not m["used"]]
        recovered = [m for m in manifest if m["used"] and m.get("recovered")]
        print(f"[bundle_to_video] photos: {len(out)}장 사용"
              + (f"(원문회수 {len(recovered)})" if recovered else "")
              + f" / {len(skipped)}건 스킵"
              + (f" ({'; '.join(m['image_id'] + ':' + m['reason'] for m in skipped[:3])})"
                 if skipped else ""))
    return out


import math

MAPS_DIR = BRIEFING / "assets" / "maps"


def _load_map_metas() -> list[dict]:
    metas = []
    for f in sorted(MAPS_DIR.glob("*_map.meta.json")):
        metas.append(json.loads(f.read_text(encoding="utf-8")))
    return metas


def _project_merc(meta: dict, lng: float, lat: float) -> tuple[float, float]:
    """d3 geoMercator 와 동일: x = t0 + k·λ, y = t1 − k·ln(tan(π/4 + φ/2))."""
    k = meta["k"]
    tx, ty = meta["t"]
    x = tx + k * math.radians(lng)
    y = ty - k * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return round(x, 1), round(y, 1)


MAP_KIND_COLOR = {"flow": "ACCENT", "subject": "OXIDE", "ally": "SAGE", "rival": "SLATE"}


def norm_map(map_data: dict) -> dict | None:
    """번들 map → geo 씬 데이터. 마커 bbox 를 포함하는 권역 베이스맵 선택."""
    markers = map_data.get("markers") or []
    if len(markers) < 2:
        return None
    lngs = [m["lng"] for m in markers]
    lats = [m["lat"] for m in markers]
    meta = None
    for cand in _load_map_metas():
        (lo_lng, lo_lat), (hi_lng, hi_lat) = cand["bbox"]
        if all(lo_lng <= g <= hi_lng for g in lngs) and all(lo_lat <= a <= hi_lat for a in lats):
            meta = cand
            break
    if not meta:
        print(f"[bundle_to_video] map 권역 미지원 (lng {min(lngs)}~{max(lngs)}) — geo 씬 생략")
        return None
    out_markers = []
    for m in markers:
        x, y = _project_merc(meta, m["lng"], m["lat"])
        out_markers.append({"id": m["id"], "name": clip(m.get("name", ""), 12),
                            "note": clip(re.sub(r"\s*\([^)]*\)", "", m.get("value", "") or "").strip(), 26) or None,
                            "x": x, "y": y, "hi": bool(m.get("highlight"))})
    arcs = []
    for a in (map_data.get("arcs") or [])[:4]:
        arcs.append({"id": f'{a["from_id"]}-{a["to_id"]}', "from": a["from_id"], "to": a["to_id"],
                     "kind": a.get("kind", "flow"), "width": min(5, 2 + (a.get("weight") or 2)),
                     "label": clip(a.get("label", "") or "", 30) or None,
                     "labelT": a.get("label_t", 0.5)})
    legend = [{"label": clip(item.get("label", ""), 16), "kind": item.get("kind", "")}
              for item in (map_data.get("legend") or [])[:5]]
    inferred = ((map_data.get("provenance") or {}).get("verification") or "") != "official"
    return {"region": meta["region"], "markers": out_markers, "arcs": arcs,
            "legend": legend, "inferred": inferred}


FLAG_IDS = {"nk": "kp", "kp": "kp", "kr": "kr", "jp": "jp", "cn": "cn", "ru": "ru",
            "us": "us", "ir": "ir", "il": "il", "lb": "lb"}
_FLAG_DIR = BRIEFING / "assets" / "flags"


def norm_network(c: dict) -> dict | None:
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
             "line": to_polite(line_a), "stance": stance_a[0], "stanceLabel": stance_a[1], "color": up},
            {"initials": names[1][:2], "name": names[1], "org": org_b or "소수 진영",
             "line": to_polite(line_b), "stance": stance_b[0], "stanceLabel": stance_b[1], "color": "#8d99ae"},
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
    closing_sents = sentences(report.get("closing", ""))
    # closing 이 빈 실번들(v8.3.3 관측) 대비: pull_quote → closing → deck → headline 순 폴백.
    quote_text = clip(
        pq or (closing_sents[0] if closing_sents else "")
        or (sentences(report.get("deck", "")) or [""])[0]
        or report.get("headline", ""), 90)
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
            theme_override: str | None = None, cuesync: dict | None = None,
            music_credit: str | None = None) -> dict:
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
        # 기본 폴백을 르포(reportage_cyprus)로 — 르포 서체·색감이 하우스 스타일 (v0.44.0).
        # 번들 토큰(accent/up/down)이 있으면 그 위에 오버라이드해 밝게 유지.
        theme_id = "reportage_cyprus"
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

    # 보도 사진 (IMAGE_BUNDLE_CONTRACT) — cleared 만 로컬 자산화, 섹션당 첫 1장.
    photos = fetch_photos(b, report.get("report_id") or "report", bundle_dir=bundle_path.parent)
    photo_by_sid: dict = {}
    for s in sections:
        for r in (s.get("image_refs") or []):
            if r in photos:
                photo_by_sid[s.get("section_id")] = photos[r]
                break
    report_video = report.get("video") or {}

    def grounded_narr(vdict, key="narration"):
        out = []
        tts_src = vdict.get(key + "_tts") or []
        for i, sent in enumerate(vdict.get(key) or []):
            sent = fix_phrasing(clip(str(sent), 75))
            if sentence_grounded(sent, corpus):
                out.append({"text": sent,
                            "tts": fix_phrasing(clip(str(tts_src[i]), 120)) if i < len(tts_src) else None})
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
                         f"이 흐름이 어떻게 쌓여 왔는지, {n}개의 갈림길로 따라가 보겠습니다.",
                         tts=tts_of(f"이 흐름이 어떻게 쌓여 왔는지, {nat or n} 개의 갈림길로 따라가 보겠습니다.")))
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

    # 2-c. 사건의 좌표 (map 있으면 — 권역 베이스맵 자동 선택)
    geo = norm_map(b.get("map") or {}) if b.get("map") else None
    if geo:
        t0 = t
        k, h, geo_sid = find_section(sections, ["좌표", "지도", "지정학"], ("Geospatial", "사건의 좌표"))
        add_scene("geo", 11, "좌표", {"kicker": k, "title": h}, geo, sid=geo_sid)
        cues.append(tcue(t0 + 0.6, "사건의 좌표를 지도 위에 놓으면 흐름이 보입니다."))
        hi_m = next((m for m in geo["markers"] if m["hi"] and m["note"]), None)
        if hi_m:
            cues.append(tcue(t0 + 4.4, clip(f"{hi_m['name']}에서는 {hi_m['note']}{josa(hi_m['note'], '이', '가')} 있었습니다.", 75)))
        arc_l = next((a for a in geo["arcs"] if a["label"]), None)
        if arc_l:
            cues.append(tcue(t0 + 7.8, clip(f"{arc_l['label']}{josa(arc_l['label'], '이', '가')} 핵심 동선입니다.", 75)))

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

    # 4-b2. 관계망 (network 차트 있으면)
    for c in charts:
        if c.get("type") != "network":
            continue
        nw = norm_network(c)
        if not nw:
            continue
        t0 = t
        sec = section_for_chart(sections, c.get("chart_id"))
        k = (sec.get("kicker") if sec else None) or "Network"
        h = (sec.get("heading") if sec else None) or c.get("title", "관계 구도")
        add_scene("geonet", 11, "관계망", {"kicker": k, "title": h}, nw,
                  sid=sec.get("section_id") if sec else None)
        n = len(nw["nodes"])
        nat = native_count(n)
        cues.append(tcue(t0 + 0.6, clip(f"{split_unit(c.get('title', ''))[0]}, {n}개 행위자를 한 판에 놓았습니다.", 75),
                         tts=tts_of(f"{split_unit(c.get('title', ''))[0]}, {nat or n} 행위자를 한 판에 놓았습니다.")))
        center = nw["nodes"][0]["label"]
        cues.append(tcue(t0 + 5.0, clip(f"관계가 가장 많이 얽힌 쪽은 {center}입니다.", 75)))

    # 4-b2. 산키 (sankey 차트 있으면 — 자금/물량 흐름 배분)
    for c in charts:
        if c.get("type") != "sankey":
            continue
        sk = norm_sankey(c)
        if not sk:
            continue
        max_sink = sk.pop("_max_sink")
        t0 = t
        sec = section_for_chart(sections, c.get("chart_id"))
        title_clean = split_unit(c.get("title", ""))[0]
        k = (sec.get("kicker") if sec else None) or "흐름"
        h = (sec.get("heading") if sec else None) or title_clean
        add_scene("sankey", 12, "흐름", {"kicker": k, "title": h}, sk,
                  sid=sec.get("section_id") if sec else None)
        cues.append(tcue(t0 + 0.6, clip(f"{title_clean} — 흐름을 따라가면 행선지가 보입니다.", 75)))
        if max_sink:
            cues.append(tcue(t0 + 6.2, clip(f"가장 굵은 줄기는 {max_sink} 쪽으로 흐릅니다.", 75)))

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
        cues.append(tcue(t0 + 0.6, clip(f"{title_clean}, {cue_tail}.", 75)))

    # 4-c2. 표 (table 차트 있으면 — 비교표/매핑표)
    for tb in build_tables(charts):
        t0 = t
        sec = section_for_chart(sections, tb["chart_id"])
        k = (sec.get("kicker") if sec else None) or "비교"
        h = (sec.get("heading") if sec else None) or tb["title"]
        add_scene("table", 9, "표", {"kicker": k, "title": h},
                  {"columns": tb["columns"], "rows": tb["rows"]},
                  sid=sec.get("section_id") if sec else None)
        first_col = tb["columns"][0]["key"]
        hl = next((r for r in tb["rows"] if r["highlight"]), None)
        if hl:
            cues.append(tcue(t0 + 0.6, clip(
                f"{tb['title']} — 갈리는 지점은 '{hl['cells'].get(first_col, '')}'입니다.", 75)))
        else:
            cues.append(tcue(t0 + 0.6, clip(f"{tb['title']} — 항목별로 나란히 보면 이렇습니다.", 75)))

    # 4-d. 스테이트먼트 (계약 video.highlights — 차트 없는 서술 섹션 구제)
    versus_k, versus_h, versus_sid = find_section(
        sections, ["강세", "보수", "쟁점", "대립", "해석"], ("쟁점", "갈리는 시각"))
    signals_k, signals_h, signals_sid = find_section(
        sections, ["신호", "감시", "Signal"], ("Signals", "무엇이 갈림길을 정하는가"))
    consumed = {sc.get("_sid") for sc in scenes}
    photo_shown: set = set()

    def add_photo(sid, s):
        # 풀블리드 보도 사진 (IMAGE_BUNDLE_CONTRACT). 오버레이 텍스트 없음 —
        # 화면엔 사진·캡션·크레딧만, 내레이션은 자막이 전달한다. (AI 슬롭 제거, v0.45.1)
        img = photo_by_sid[sid]
        sv = svideos.get(sid)
        n = len(sv["narration"]) if sv and sv["narration"] else 3
        add_scene("photo", min(12, max(9, 3 + 3.0 * n)), "현장",
                  {"kicker": s.get("kicker") or "현장", "title": s.get("heading") or ""},
                  {**img, "lines": []}, sid=sid)
        photo_shown.add(sid)

    for s in sections:
        sid = s.get("section_id")
        if sid in (versus_sid, signals_sid):
            continue
        sv = svideos.get(sid)
        has_narr = bool(sv and sv["narration"])
        emphasis = sv["emphasis"] if sv else []
        img = photo_by_sid.get(sid)
        heading = s.get("heading") or ""

        if sid in consumed:
            # 차트 등으로 이미 소진된 섹션이라도 cleared 사진이 있으면 인접 photo 씬으로
            # 함께 노출한다 (C0 영상미 우선). 사진 없으면 별도 씬 없음(차트가 담당).
            if img and sid not in photo_shown:
                add_photo(sid, s)
            continue

        if img:
            # 차트 없는 사진 섹션 — 풀블리드 photo 씬.
            if sid not in photo_shown:
                add_photo(sid, s)
            continue

        # 차트·사진 없는 서술 섹션 — 섹션 제목을 큰 편집형 스테이트먼트로.
        # (기존 video.highlights 번호 카드는 텔레그래프식 AI 슬롭이라 폐기 — 사용자
        #  결정 2026-07-12. 살아있는 문장인 내레이션은 자막으로 그대로 나간다.)
        if has_narr and heading:
            dur = min(14, max(9, 3 + 3.0 * len(sv["narration"])))
            add_scene("statement", dur, "키 포인트",
                      {"kicker": s.get("kicker") or "Key Point", "title": ""},
                      {"lines": [em_segments_line(heading, emphasis)]}, sid=sid)

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
        if a["name"].startswith("시각"):
            cues.append(tcue(t0 + 0.6, "이 사안을 보는 시각은 크게 둘로 갈립니다."))
        else:
            cues.append(tcue(t0 + 0.6,
                             f"시각은 {a['name']}{josa(a['name'], '과', '와')} {bb['name']}, 둘로 갈립니다."))
        # 자막은 75자 클립, 음성은 첫 완결 문장 — 중간에 말이 끊기지 않게 (TTS-AP-060)
        a_line_first = (sentences(a["line"]) or [a["line"]])[0]
        cues.append(tcue(t0 + 4.4, clip(f"{a['org']}, {a['line']}", 75),
                         tts=tts_of(f"{a['org']}, {to_polite(a_line_first)}")))
        res0 = sentences(contras[0].get("resolution", ""))
        if res0:
            cues.append(tcue(t0 + 8.2, clip(to_polite(res0[0]), 75)))

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
        cues.append(tcue(t0 + 0.6, f"앞으로 확인할 신호는 {len(sig['items'])}가지. 전부 <미검증> 관측 대상입니다."))
        first = sig["items"][0]
        # 자막은 name(풀), 음성은 name_spoken(첫 절·날짜 중복 제거) — 절단 "…" 낭독 방지
        cues.append(tcue(
            t0 + 4.6,
            clip(f"가장 가까운 갈림길은 {first['when']}, {first['name']}입니다.", 75),
            tts=tts_of(f"가장 가까운 갈림길은 {first['when']}, {first['name_spoken']}입니다.")))

    # 5. 클로징 (항상)
    t0 = t
    closing = build_closing(report, sections, b.get("confidence") or {}, skip_pq=bool(pq))
    k, h = (sections[-1].get("kicker"), sections[-1].get("heading")) if sections else ("Outlook", "다음 좌표")
    add_scene("closing", 9, "향방", {"kicker": k or "Outlook", "title": h or "다음 좌표"}, closing, sid="__outro")
    # closing 빈 실번들(v8.3.3 관측) 폴백 — deck 첫 문장. (__outro 계약 narration 이 있으면 어차피 대체됨)
    closing_first = (sentences(report.get("closing", "")) or sentences(report.get("deck", "")) or [""])[0]
    if closing_first:
        cues.append(tcue(t0 + 0.4, clip(closing_first, 58)))
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

    # 표기 정규화(display) + 발음 정규화(tts) — 계약 narration_tts 까지 소수·슬래시날짜·
    # 말끝·사전·숫자 전부 커버 (tts_of 멱등). apply_pronunciation 단독 → tts_of 로 승격.
    for c in cues:
        c["text"] = normalize_display(c["text"])
        if c.get("tts"):
            c["tts"] = tts_of(c["tts"])
    for sc in scenes:
        if sc.get("head"):
            sc["head"]["title"] = normalize_display(sc["head"]["title"])
        d = sc.get("data") or {}
        if isinstance(d.get("lines"), list):  # statement
            for ln in d["lines"]:
                for seg in ln:
                    seg[0] = normalize_display(seg[0])

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
    if music_credit:
        src2 += f" · Music: {music_credit}"

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
        "mapRegion": (geo or {}).get("region") if "geo" in dir() and geo else None,
    }

    emit_html(data, out_path, bundle_path.name, report.get("report_id", ""))
    return data


def emit_html(data: dict, out_path: Path, src_name: str, report_id: str) -> None:
    """DATA → 컴포지션 HTML. CSS 는 briefing/index.html <style> 재사용 (테마 SSOT)."""
    total = data["total"]
    map_script = ""
    if data.get("mapRegion"):
        map_script = f'    <script src="assets/maps/{data["mapRegion"]}_map.js"></script>'
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
    <link rel="stylesheet" href="assets/reportage_fonts.css" />
    <script src="assets/gsap.min.js"></script>
    <script src="assets/scene_kit.js"></script>
    <script src="assets/themes.js"></script>
{map_script}
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

    def tcue(at, text, tts=None):
        return {"t": at, "text": text, "tts": tts or tts_of(text)}

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

    add("sankey", 12, "흐름", {"kicker": "Sankey", "title": "조달금액의 흐름 — 어디로 갈라지나"},
        {"unit": "억달러", "inferred": True,
         "nodes": [
             {"id": "raise", "label": "조달총액"},
             {"id": "fab", "label": "팹 투자"},
             {"id": "rnd", "label": "R&D"},
             {"id": "debt", "label": "재무"},
             {"id": "pkg", "label": "패키징"},
             {"id": "node2", "label": "차세대 공정"},
             {"id": "repay", "label": "차입금 상환", "accent": True},
         ],
         "links": [
             {"source": "raise", "target": "fab", "value": 14},
             {"source": "raise", "target": "rnd", "value": 10},
             {"source": "raise", "target": "debt", "value": 8},
             {"source": "fab", "target": "pkg", "value": 9},
             {"source": "fab", "target": "node2", "value": 5},
             {"source": "rnd", "target": "node2", "value": 10},
             {"source": "debt", "target": "repay", "value": 8},
         ]},
        "흐름을 따라가면 행선지가 보입니다.")

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

    add("table", 10, "비교", {"kicker": "Table", "title": "OCML vs E-BOM — 빠진 것을 보라"},
        {"columns": [
            {"key": "field", "label": "필드", "weight": 1.5},
            {"key": "ocml", "label": "OCML", "align": "center", "weight": 1.1, "accent": "#d69a5e"},
            {"key": "ebom", "label": "E-BOM", "align": "center", "weight": 1.1, "accent": "#88b888"},
            {"key": "note", "label": "비고", "weight": 1.6},
         ],
         "rows": [
            {"cells": {"field": "자재 리스트", "ocml": "✓ 있음", "ebom": "✓ 있음", "note": ""}},
            {"cells": {"field": "소요량", "ocml": "✓ 1-Cell", "ebom": "✓ 계층별", "note": "스케일링 차이"}},
            {"cells": {"field": "반제품 구조", "ocml": "✗ 없음", "ebom": "✓ 있음", "note": "★ 가장 결정적 차이"}, "highlight": True},
            {"cells": {"field": "부품 계층", "ocml": "✗ 평면", "ebom": "✓ 8레벨", "note": "★ 구조적 차이"}, "highlight": True},
            {"cells": {"field": "CAD 참조", "ocml": "✗ 없음", "ebom": "✓ 있음", "note": ""}},
            {"cells": {"field": "공정 정보", "ocml": "✗ 없음", "ebom": "부분적", "note": "M-BOM에서 추가"}},
         ]},
        "표로 나란히 놓으면, 빠진 한 줄이 드러납니다.")

    # photo 씬 검증용 플레이스홀더 (네트워크 불필요 — 로컬 SVG 생성, 결정론)
    ph_dir = BRIEFING / "assets" / "photos" / "preview"
    ph_dir.mkdir(parents=True, exist_ok=True)
    (ph_dir / "placeholder.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#2a3b52"/><stop offset="1" stop-color="#0e1620"/>'
        '</linearGradient></defs><rect width="1920" height="1080" fill="url(#g)"/>'
        '<circle cx="1450" cy="330" r="180" fill="#c4a265" opacity="0.25"/>'
        '<rect x="180" y="620" width="900" height="300" fill="#111a26" opacity="0.6"/>'
        '<text x="200" y="700" font-size="44" fill="#8fa3bd" font-family="sans-serif">'
        'PLACEHOLDER PHOTO 1920x1080</text></svg>', encoding="utf-8")
    add("photo", 10, "현장", {"kicker": "Photo", "title": "현장 사진 — Ken Burns 검증"},
        {"src": "assets/photos/preview/placeholder.svg",
         "caption": "울산 AI 데이터센터 예정 부지 (합성 샘플)", "credit": "합성 샘플",
         "focus": "center",
         "lines": [em_segments_line("사진 위에 key takeaway 가 얹힙니다", ["key takeaway"]),
                   em_segments_line("크레딧과 캡션은 우하단에", ["크레딧"])]},
        "사진이 천천히 확대되며, 핵심 문장이 위에 얹힙니다.")

    data = {
        "meta": {"brand": "OSINT BRIEFING", "sub": "차트 갤러리", "date": "2026.06.12",
                 "sourceLine1": "데이터 · 합성 샘플 (비주얼 검증용)",
                 "sourceLine2": "신규 차트 6유형 — stacked / waterfall / scatter / heatmap / gantt / table"},
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
              "[--bgm] | --preview-charts [out.html]",
              file=sys.stderr)
        return 1
    bundle = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else BRIEFING / "auto.html"

    def run_convert(cs: dict | None = None) -> dict:
        return convert(bundle, out, tl_override=flags.get("--timeline") or None,
                       theme_override=flags.get("--video-theme") or None, cuesync=cs,
                       music_credit=flags.get("--music-credit") or None)

    narration = flags.get("--narration")  # estimate | synth
    cuesync_flag = flags.get("--cuesync")
    if narration:
        import subprocess
        run_convert()  # 1차: cue 확정
        cmd = [sys.executable, str(Path(__file__).parent / "build_auto_narration.py"), str(out)]
        if narration == "estimate":
            cmd.append("--estimate")
        bgm_val = flags.get("--bgm")
        if bgm_val is not None:
            cmd.append(f"--bgm={bgm_val}" if bgm_val else "--bgm")
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
