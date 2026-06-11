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


def build_ladder(timeline: dict) -> dict:
    steps = []
    for p in pick_timeline_steps(timeline.get("points", [])):
        steps.append({
            "date": p.get("date", "").replace("-", "."),
            "label": clip(p.get("label", ""), 44),
            "phase": p.get("phase", "past"),
        })
    return {"steps": steps}


def timeline_kind(points: list) -> str:
    """에스컬레이션 서사(crack+present 공존)면 계단, 아니면 수평 축."""
    phases = {p.get("phase") for p in points}
    return "ladder" if {"crack", "present"} <= phases else "axis"


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


def build_closing(report: dict, sections: list, confidence: dict) -> dict:
    pq = next((s.get("pull_quote") for s in sections if s.get("pull_quote")), None)
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


def find_section(sections: list, keywords: list[str], default: tuple[str, str]) -> tuple[str, str]:
    for s in sections:
        hay = (s.get("kicker") or "") + (s.get("heading") or "")
        if any(k in hay for k in keywords):
            return s.get("kicker") or default[0], s.get("heading") or default[1]
    return default


# ── 메인 ────────────────────────────────────────────────────


def convert(bundle_path: Path, out_path: Path) -> dict:
    b = json.loads(bundle_path.read_text(encoding="utf-8"))
    report = b["report"]
    sections = b.get("sections", [])
    theme = report.get("theme", {})
    tokens = theme.get("tokens", {})
    gen = b.get("generated_at", "")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", gen)
    date_dot = f"{m.group(1)}.{m.group(2)}.{m.group(3)}" if m else ""
    date_kor = f"{int(m.group(1))}년 {int(m.group(2))}월 {int(m.group(3))}일" if m else ""

    accent = tokens.get("accent", "#c4a265")
    up = tokens.get("up", "#7d9b76")
    down = tokens.get("down", "#b25450")

    # ── 씬 플랜 (데이터에 있는 것만) ──
    scenes = []
    cues = []
    t = 0.0

    def add_scene(stype, dur, chip_label, head, data):
        nonlocal t
        scenes.append({
            "type": stype, "t0": round(t, 2), "t1": round(t + dur, 2),
            "no": f"{len(scenes) + 1:02d}", "chip": f"{len(scenes) + 1:02d} · {chip_label}",
            "head": head, "data": data,
        })
        t += dur

    # 1. 타이틀 (항상)
    title = build_title(report, sections, date_kor)
    add_scene("title", 9, "타이틀", None, title)
    deck_sents = sentences(report.get("deck", ""))
    cues.append({"t": 0.8, "text": clip(deck_sents[0], 58)})
    if len(deck_sents) > 1:
        cues.append({"t": 4.6, "text": clip(deck_sents[1], 58)})

    charts = b.get("charts") or []

    # 2. 타임라인 — 유형 자동 선택 (에스컬레이션 서사 = 계단 / 중립 시계열 = 수평 축)
    tl_data = b.get("timeline") or {}
    if tl_data.get("points"):
        t0 = t
        ladder = build_ladder(tl_data)
        kind = timeline_kind(tl_data["points"])
        head = ("Timeline", tl_data.get("heading", "사건의 궤적"))
        add_scene(kind, 11, "타임라인", {"kicker": head[0], "title": head[1]}, ladder)
        n = len(ladder["steps"])
        cues.append({"t": t0 + 0.6, "text": f"{head[1]} — {n}개의 분기점으로 흐름을 따라갑니다."})
        key = next((s for s in ladder["steps"] if s["phase"] in ("present", "crack")), None)
        if key:
            cues.append({"t": t0 + 4.4, "text": clip(f"{date_kr(key['date'].replace('.', '-'))}, {key['label']}", 58)})
        fut = next((s for s in ladder["steps"] if s["phase"] == "future"), None)
        if fut:
            cues.append({"t": t0 + 8.0, "text": clip(f"다음 분기점은 {date_kr(fut['date'].replace('.', '-'))} — {fut['label']}", 58)})

    # 3. 일봉 캔들 (candle 차트 있으면)
    candle = build_candle(charts)
    if candle:
        t0 = t
        sec = section_for_chart(sections, candle["chart_id"])
        k = (sec.get("kicker") if sec else None) or "Daily"
        h = (sec.get("heading") if sec else None) or candle["title"]
        add_scene("candle", 9, "일봉", {"kicker": k, "title": h},
                  {"ohlc": candle["ohlc"], "title": candle["title"]})
        cues.append({"t": t0 + 0.6, "text": clip(f"{candle['title']} — 최근 {len(candle['ohlc'])}거래일의 흐름입니다.", 58)})
        closes = [d["close"] for d in candle["ohlc"]]
        chg = (closes[-1] / closes[0] - 1) * 100
        cues.append({"t": t0 + 4.6, "text": f"구간 등락은 {chg:+.1f}%, 종가 {round(closes[-1]):,}입니다."})

    # 4. 바 패널 (bar 차트 있으면 — 단일 + 듀얼)
    for bp in build_bar_panels(charts):
        t0 = t
        first_id = bp["panels"][0].get("chart_id")
        sec = section_for_chart(sections, first_id)
        k = (sec.get("kicker") if sec else None) or "전망"
        h = (sec.get("heading") if sec else None) or bp["panels"][0]["title"]
        dur = 9 if len(bp["panels"]) == 1 else 10
        add_scene("bars", dur, "전망" if len(bp["panels"]) == 1 else "목표가", {"kicker": k, "title": h}, bp)
        if len(bp["panels"]) == 1:
            pn = bp["panels"][0]
            top = max(pn["items"], key=lambda it: it["value"])
            cues.append({"t": t0 + 0.6, "text": clip(f"{pn['title']} — 상단은 {top['label']}, {top['value']:,}{pn['unit']}입니다.", 58)})
        else:
            # 패널(차트)별 상단/하단 비율 — 패널 간 혼합은 스케일이 달라 무의미
            ratios = []
            for pn in bp["panels"]:
                vals = [it["value"] for it in pn["items"]]
                if min(vals):
                    ratios.append((pn["title"], max(vals) / min(vals)))
            cues.append({"t": t0 + 0.6, "text": "같은 회사를 두고, 12개월 시선은 이렇게 벌어져 있습니다."})
            if ratios:
                wt, wr = max(ratios, key=lambda r: r[1])
                cues.append({"t": t0 + 4.8, "text": clip(f"{wt} — 상단과 하단이 {wr:.1f}배 차이입니다.", 58)})

    # 5. 쟁점 (contradictions 있으면)
    contras = b.get("contradictions") or []
    if contras:
        t0 = t
        versus = build_versus(contras[0], theme)
        k, h = find_section(sections, ["강세", "보수", "쟁점", "대립"], ("쟁점", "갈리는 시각"))
        add_scene("versus", 12, "쟁점", {"kicker": k, "title": h}, versus)
        a, bb = versus["cards"][0], versus["cards"][1]
        cues.append({"t": t0 + 0.6, "text": f"시각은 둘로 갈립니다 — {a['name']}과 {bb['name']}."})
        cues.append({"t": t0 + 4.4, "text": clip(f"{a['org']} — {a['line']}", 58)})
        cues.append({"t": t0 + 8.2, "text": clip(sentences(contras[0].get("resolution", ""))[0], 58)})

    # 6. 가격 비교 (line 차트 있으면)
    markets = build_markets(charts)
    if markets["markets"]:
        t0 = t
        add_scene("markets", 10, "가격", {"kicker": "Relative", "title": "같은 기간, 가격의 궤적"}, markets)
        cues.append({"t": t0 + 0.6, "text": "같은 기간, 가격은 이렇게 움직였습니다."})
        top = max(markets["markets"], key=lambda mk: abs(mk["pct"]))
        cues.append({"t": t0 + 4.6, "text": f"가장 크게 움직인 건 {top['name']}, {top['pct']:+.1f}%입니다."})

    # 7. 관측 신호 (signals 있으면)
    sig = build_signals(b.get("signals") or [])
    if sig:
        t0 = t
        add_scene("signals", 10, "신호", {"kicker": "Signals", "title": "무엇이 갈림길을 정하는가"}, sig)
        cues.append({"t": t0 + 0.6, "text": f"앞으로 확인할 신호 {len(sig['items'])}가지 — 전부 <미검증> 관측 대상입니다."})
        first = sig["items"][0]
        cues.append({"t": t0 + 4.6, "text": clip(f"가장 가까운 분기점은 {first['when']}, {first['name']}입니다.", 58)})

    # 5. 클로징 (항상)
    t0 = t
    closing = build_closing(report, sections, b.get("confidence") or {})
    k, h = (sections[-1].get("kicker"), sections[-1].get("heading")) if sections else ("Outlook", "다음 좌표")
    add_scene("closing", 9, "향방", {"kicker": k or "Outlook", "title": h or "다음 좌표"}, closing)
    cues.append({"t": t0 + 0.4, "text": clip(sentences(report.get("closing", ""))[0], 58)})
    cues.append({"t": t0 + 4.2, "text": f"신뢰도 {closing['confidence']['score']:.2f} — 근거와 한계는 화면과 같습니다."})

    total = round(t, 2)

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
        "themeVars": {"--accent": accent, "--sage": up, "--oxide": down},
        "colors": {
            "phase": {"past": "#6e6a60", "crack": accent, "present": down, "future": "#8d99ae"},
            "gradStops": [["0", "#55524a"], ["0.62", down], ["1", "#8d99ae"]],
            "market": {"up": up, "down": down, "vol": accent, "flat": "#9aa3b2"},
            "marketTag": {"up": "상승", "down": "하락", "vol": "변동", "flat": "보합"},
        },
        "total": total,
        "scenes": scenes,
        "cues": cues,
    }

    # ── auto.html 생성 (CSS 는 briefing/index.html 의 <style> 재사용) ──
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
    <!-- 자동 생성: bundle_to_video.py — {bundle_path.name}
         report_id: {report.get("report_id", "")}
         수정 금지. 변환기를 고치고 재실행할 것. -->
    <link rel="stylesheet" href="assets/noto_serif_kr.css" />
    <script src="assets/gsap.min.js"></script>
    <script src="assets/scene_kit.js"></script>
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
    </div>
    <script>window.BRIEFING_DATA = {json.dumps(data, ensure_ascii=False)};</script>
    <script>
{builder_js}
    </script>
  </body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    return data


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python bundle_to_video.py <bundle.json> [out.html]", file=sys.stderr)
        return 1
    bundle = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else BRIEFING / "auto.html"
    data = convert(bundle, out)
    print(f"[bundle_to_video] scenes={[s['type'] for s in data['scenes']]} "
          f"total={data['total']}s cues={len(data['cues'])} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
