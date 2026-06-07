"""hyperframes_compose — ReportBundle → 다중 씬 HyperFrames 컴포지션 자동 생성 (v0.34.14).

옵션 C. render_io(Remotion 시절 render_props.json)의 HyperFrames 후속. agents_reviewer
ReportBundle 을 받아, 각 BundleSection 을 1 개 씬으로 펼친 HyperFrames 컴포지션 HTML 을
생성한다. 차트가 있는 섹션은 `lib/charts/<type>.html` 컴포넌트를 `data-composition-src` 로
임베드하고 bundle 차트 데이터를 `data-variable-values`(JSON)로 주입한다. 차트가 없거나
미지원 타입이면 텍스트 씬으로 폴백한다.

`examples/gallery.html` 의 시퀀싱 패턴을 데이터 구동으로 일반화한 것 — 12 씬 파이프라인의
실 엔트리. narration/자막은 현재 section.prose 를 글자수 비례로 큐 분할(추정 타이밍)하며,
정밀 narration(ScriptWorker)·실 음성 길이 sync 는 후속.

설계:
- 순수 함수(`build_composed_scenes`, `render_composition_html`)는 I/O 없음.
- I/O 경계(`build_and_persist_composition`)만 파일을 읽고 쓴다.
- 산출물은 `hyperframes/generated/<project_id>.html` (lib/charts 와 같은 루트 하위라
  `../lib/charts/...` 로 import 가능 — 번들러의 루트-내부 `../` 허용 실측).
- 문자열 포맷은 `.replace()` 만 사용(C2 — JSON `{}` 와 `.format()` 충돌 회피).
"""

from __future__ import annotations

import html
import json
import math
import os
import re
from datetime import date as _date
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.models import BundleChart, ReportBundle, SubtitleCue

# 우리가 영상용 컴포넌트를 가진 차트 타입 → lib/charts 파일명.
# (v0.34.13 의 4 종. B-ext 로 확장 시 여기에 추가.)
COMPONENT_BY_TYPE: dict[str, str] = {
    "candle": "candle",
    "line": "line",
    "bar": "bar",
    "donut": "donut",
}

# 한 씬 기본 길이 추정용 — 한국어 낭독 대략 초당 글자수.
_NARRATION_CPS = 6.0
_SCENE_MIN_SEC = 4.0
_SCENE_MAX_SEC = 12.0
# 차트/SVG 씬 1 개 고정 길이 (등장 애니 + 숨고르기).
_CHART_SCENE_SEC = 5.0
# 자막 한 줄(큐) 최대 글자수.
_CUE_MAX_CHARS = 42


# ---------------------------------------------------------------------------
# 중간 표현 (테스트·재사용 가능한 도메인 모델)
# ---------------------------------------------------------------------------


class ComposedCue(BaseModel):
    """컴포지션 절대 타임라인 기준 자막 큐(초)."""

    model_config = ConfigDict(extra="forbid")

    text: str
    at_sec: float


class ComposedScene(BaseModel):
    """펼쳐진 씬 1 개. chart=컴포넌트+주입변수, svg=prerendered_svg 폴백, text=heading/본문."""

    model_config = ConfigDict(extra="forbid")

    scene_id: str
    section_id: str = ""                   # 어느 BundleSection 에서 나왔나 (자막 큐 그룹핑용)
    start_sec: float
    duration_sec: float
    kind: str  # "chart" | "svg" | "text"
    component: Optional[str] = None       # kind=="chart" 일 때 lib/charts 파일명
    variables: dict[str, Any] = Field(default_factory=dict)  # data-variable-values 페이로드
    heading: str = ""                     # svg/text 씬 헤드라인 (chart 는 variables.takeaway)
    body: str = ""                        # text 씬 본문(pull_quote/prose)
    svg: str = ""                         # kind=="svg" 일 때 prerendered_svg 원문
    narration: str = ""                   # 음성 나레이션 스크립트(plan 에서 주입)


# ---------------------------------------------------------------------------
# 차트 데이터 매핑 (agents_reviewer 모양 → 컴포넌트 변수)
# ---------------------------------------------------------------------------


def _num(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _short_date(s: Any) -> str:
    """"2026-03-02" → "03-02". 이미 짧거나 비-ISO 면 원문."""
    t = str(s or "")
    m = re.match(r"^\d{4}-(\d{2})-(\d{2})", t)
    return f"{m.group(1)}-{m.group(2)}" if m else t


def _nice_step(rough: float) -> float:
    if rough <= 0:
        return 1.0
    mag = 10 ** math.floor(math.log10(rough))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= rough:
            return m * mag
    return 10 * mag


def _nice_bounds(lo: float, hi: float) -> tuple[float, float, float]:
    """데이터 [lo,hi] 를 여유 + nice step 으로 축 경계 산출 → (yMin, yMax, yStep)."""
    if hi <= lo:
        hi = lo + 1
    span = hi - lo
    raw_min, raw_max = lo - span * 0.15, hi + span * 0.15
    step = _nice_step((raw_max - raw_min) / 4)
    y_min = math.floor(raw_min / step) * step
    y_max = math.ceil(raw_max / step) * step
    return _clean(y_min), _clean(y_max), _clean(step)


def _clean(n: float) -> float:
    """정수면 int 로(JSON 노이즈 회피)."""
    r = round(n, 4)
    return int(r) if r == int(r) else r


def _rows(chart: BundleChart) -> list[dict]:
    data = chart.data
    return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []


def _candle_vars(chart: BundleChart) -> Optional[dict]:
    rows = _rows(chart)
    candles, lows, highs = [], [], []
    for r in rows:
        o, h, l, c = _num(r.get("open")), _num(r.get("high")), _num(r.get("low")), _num(r.get("close"))
        candles.append({"d": _short_date(r.get("date")), "o": _clean(o), "h": _clean(h), "l": _clean(l), "c": _clean(c)})
        lows.append(l)
        highs.append(h)
    if not candles:
        return None
    y_min, y_max, y_step = _nice_bounds(min(lows), max(highs))
    return {"candles": candles, "yMin": y_min, "yMax": y_max, "yStep": y_step,
            "yUnit": _unit(chart), "callouts": [], "endpoint": None}


def _line_vars(chart: BundleChart, callout_t: float) -> Optional[dict]:
    rows = _rows(chart)
    x_labels, ys, events = [], [], []
    for i, r in enumerate(rows):
        x_labels.append(_short_date(r.get("x", r.get("label", i))))
        ys.append(_clean(_num(r.get("y"))))
        ev = r.get("event")
        events.append(str(ev) if ev else None)
    if not ys:
        return None
    n = len(ys)
    # 콜아웃 방향: 오른쪽 가장자리(뒤 40%)의 점은 왼쪽("ul")으로 띄워 viewBox 밖 넘침과
    # 끝점 라벨 충돌을 피한다. 그 외엔 오른쪽("ur"). 같은 t 로 동시 등장하지 않게 살짝 stagger.
    callouts = []
    for i, ev in enumerate(events):
        if not ev:
            continue
        direction = "ul" if (n > 1 and i >= n * 0.6) else "ur"
        callouts.append({"xi": i, "si": 0, "t": callout_t + 0.4 * len(callouts),
                         "title": ev, "sub": "", "dir": direction})
    y_min, y_max, y_step = _nice_bounds(min(ys), max(ys))
    # 단일 시리즈는 끝점 라벨 이름을 비운다 — chart.title 은 이미 takeaway 헤드라인으로
    # 표시되므로 series.name 에 또 박으면 긴 문장이 차트 밖으로 넘쳐 값과 겹친다(v0.36.4).
    series = [{"name": "", "color": "#e84a2d", "points": ys}]
    return {"xLabels": x_labels, "series": series, "yMin": y_min, "yMax": y_max,
            "yStep": y_step, "yUnit": _unit(chart), "callouts": callouts}


def _bar_vars(chart: BundleChart) -> Optional[dict]:
    rows = _rows(chart)
    bars = []
    for r in rows:
        label = str(r.get("label", r.get("x", "")))
        value = _clean(_num(r.get("value", r.get("y", r.get("size")))))
        bars.append({"label": label, "value": value})
    if not bars:
        return None
    return {"bars": bars, "unit": _unit(chart) or "", "highlight": 0}


def _donut_vars(chart: BundleChart) -> Optional[dict]:
    rows = _rows(chart)
    slices = []
    for r in rows:
        label = str(r.get("label", r.get("x", "")))
        value = _clean(_num(r.get("value", r.get("y", r.get("size")))))
        slc = {"label": label, "value": value}
        if r.get("color"):
            slc["color"] = str(r["color"])
        slices.append(slc)
    if not slices:
        return None
    unit = _unit(chart) or "%"
    # 중앙 라벨/값을 실 데이터에서 산출(컴포넌트 default 가 무관 데이터에 오인 표기되는 것 방지).
    total = sum(s["value"] for s in slices) or 1
    top = max(slices, key=lambda s: s["value"])
    top_pct = round(top["value"] / total * 100)
    return {"slices": slices, "unit": unit,
            "centerLabel": str(top["label"]), "centerValue": f"{top_pct}%"}


def _unit(chart: BundleChart) -> str:
    srcs = chart.provenance.sources if chart.provenance else []
    return srcs[0].unit if srcs and srcs[0].unit else ""


def _source_label(chart: BundleChart) -> str:
    """출처 표기 — provenance.sources[0].provider (+ code). 없으면 ""."""
    srcs = chart.provenance.sources if chart.provenance else []
    if not srcs:
        return ""
    s = srcs[0]
    prov = (s.provider or "").strip()
    code = (s.code or "").strip()
    if prov and code:
        return f"{prov} ({code})"
    return prov or code


def _chart_dates(chart: BundleChart) -> list[str]:
    out: list[str] = []
    for r in _rows(chart):
        d = r.get("date") if "date" in r else r.get("x")
        if d not in (None, ""):
            out.append(str(d))
    return out


def _period_interval(dates: list[str]) -> tuple[str, str, str]:
    """날짜 목록 → (시작, 끝, 인터벌라벨). 인터벌은 중앙 간격(일)으로 추론."""
    if not dates:
        return "", "", ""
    start, end = _short_date(dates[0]), _short_date(dates[-1])
    parsed: list[Any] = []
    for d in dates:
        m = re.match(r"^(\d{4})-(\d{2})(?:-(\d{2}))?", str(d))
        if m:
            y, mo, da = int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)
            try:
                parsed.append(_date(y, mo, da))
            except ValueError:
                pass
    interval = ""
    if len(parsed) >= 2:
        gaps = sorted((parsed[i + 1] - parsed[i]).days for i in range(len(parsed) - 1))
        med = gaps[len(gaps) // 2]
        interval = "일봉" if med <= 3 else "주봉" if med <= 10 else "월봉" if med <= 45 else ""
    return start, end, interval


def _attach_meta(v: dict, chart: BundleChart) -> None:
    """차트 변수에 출처·기간·인터벌 footer 메타 주입 (모든 컴포넌트 공통)."""
    v["source"] = _source_label(chart)
    start, end, interval = _period_interval(_chart_dates(chart))
    v["periodStart"], v["periodEnd"], v["interval"] = start, end, interval


def chart_to_component(
    chart: BundleChart, *, callout_t: float = 3.0, accent: Optional[str] = None
) -> Optional[tuple[str, dict]]:
    """BundleChart → (lib/charts 컴포넌트 파일명, data-variable-values 변수 dict).

    지원 타입이 아니거나 데이터가 비어 매핑 불가면 None (호출자가 svg/텍스트 폴백).
    accent 가 주어지면(번들 theme.tokens.accent) 강조색으로 주입(candle/line/bar). donut 은
    슬라이스 자체 팔레트라 제외.
    """
    comp = COMPONENT_BY_TYPE.get(chart.type)
    if comp is None:
        return None
    if comp == "candle":
        v = _candle_vars(chart)
    elif comp == "line":
        v = _line_vars(chart, callout_t)
    elif comp == "bar":
        v = _bar_vars(chart)
    elif comp == "donut":
        v = _donut_vars(chart)
    else:  # pragma: no cover - COMPONENT_BY_TYPE 와 동기
        return None
    if v is None:
        return None
    v["takeaway"] = chart.title or ""
    if accent and comp in ("candle", "line", "bar"):
        v["accent"] = accent
    _attach_meta(v, chart)  # 출처·기간·시작~끝 footer (필수)
    return comp, v


def _theme_token(bundle: ReportBundle, key: str) -> Optional[str]:
    """번들 report.theme.tokens[key] (있으면). accent/up/down 등 테마색."""
    theme = bundle.report.theme if bundle.report else None
    if theme and isinstance(theme.tokens, dict):
        v = theme.tokens.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _theme_accent(bundle: ReportBundle) -> Optional[str]:
    """번들 report.theme.tokens.accent (있으면). 보고서 테마색을 영상 강조색으로 잇는다."""
    return _theme_token(bundle, "accent")


# 보조차트(strip) 후보 type — 시장 시계열 sparkline. candle 은 상세 OHLC 라 제외(기본 메인,
# v0.34.17). display 가 항상 우선(docs/CHART_DISPLAY_RULES.md).
_STRIP_CANDIDATE_TYPES = {"line", "area"}


def _classify_section(charts: list[BundleChart]) -> list[str]:
    """섹션 내 각 차트의 "full"/"strip" 판정 (docs/CHART_DISPLAY_RULES.md).

    1순위 display 필드 → 없으면 type 휴리스틱(line/candle/area 가 같은 섹션에 2개 이상
    연속이면 strip). role(composed_report.json) 기반 2순위는 그 JSON 이 함께 올 때 후속.
    """
    n = len(charts)
    run_strip = [False] * n
    i = 0
    while i < n:
        if charts[i].type in _STRIP_CANDIDATE_TYPES:
            j = i
            while j < n and charts[j].type in _STRIP_CANDIDATE_TYPES:
                j += 1
            if j - i >= 2:
                for k in range(i, j):
                    run_strip[k] = True
            i = j
        else:
            i += 1
    out: list[str] = []
    for idx, c in enumerate(charts):
        d = (c.display or "").strip().lower()
        out.append(d if d in ("full", "strip") else ("strip" if run_strip[idx] else "full"))
    return out


def _strip_series(chart: BundleChart) -> Optional[dict]:
    """strip 차트 → 티커 보드 item {name, unit, points}. candle 은 종가선, line/area 는 y."""
    rows = _rows(chart)
    pts: list[float] = []
    for r in rows:
        if "close" in r:
            pts.append(_clean(_num(r.get("close"))))
        elif "y" in r:
            pts.append(_clean(_num(r.get("y"))))
    if not pts:
        return None
    return {"name": chart.title or "", "unit": _unit(chart), "points": pts}


# ---------------------------------------------------------------------------
# 씬 펼치기 (순수)
# ---------------------------------------------------------------------------


def _estimate_duration(prose: str) -> float:
    n = len(prose.strip())
    return max(_SCENE_MIN_SEC, min(_SCENE_MAX_SEC, n / _NARRATION_CPS)) if n else _SCENE_MIN_SEC


def _text_scene_body(pull_quote: str, prose: str, cap: int = 140) -> str:
    """텍스트 씬의 화면 body — **통문단 도배 금지(C0)**.

    pull_quote 가 있으면 그 핵심 인용문을, 없으면 prose 의 첫 문장만 cap 자로 발췌한
    key-takeaway 한 줄을 반환한다. prose 전문은 body 가 아니라 자막 큐로만 흐른다
    (RENDER-AP: 차트 없는 섹션이 prose 전체를 body 로 박아 "정적 보고서를 화면에 박은"
    글자 벽이 되던 사고).
    """
    pq = (pull_quote or "").strip()
    if pq:
        return pq
    t = (prose or "").strip()
    if not t:
        return ""
    m = re.search(r"[.!?。…](?:\s|$)", t)
    first = t[: m.end()].strip() if m else t
    if len(first) > cap:
        first = first[:cap].rstrip() + "…"
    return first


def _split_cues(text: str, total_sec: float) -> list[SubtitleCue]:
    """prose 를 문장/줄 단위 큐로 쪼개고 글자수 비례로 타이밍 배분(씬 시작 기준 상대)."""
    t = text.strip()
    if not t or total_sec <= 0:
        return []
    sentences = [s for s in re.split(r"(?<=[.?!。])\s+", t) if s.strip()]
    chunks: list[str] = []
    for sent in sentences:
        s = sent.strip()
        while len(s) > _CUE_MAX_CHARS:
            cut = s.rfind(" ", 0, _CUE_MAX_CHARS)
            cut = cut if cut > 0 else _CUE_MAX_CHARS
            chunks.append(s[:cut].strip())
            s = s[cut:].strip()
        if s:
            chunks.append(s)
    if not chunks:
        return []
    total_chars = sum(len(c) for c in chunks)
    cues, cursor = [], 0.0
    for i, c in enumerate(chunks):
        dur = max(0.0, total_sec - cursor) if i == len(chunks) - 1 else total_sec * (len(c) / total_chars)
        cues.append(SubtitleCue(text=c, startSec=round(cursor, 3), durationSec=round(dur, 3)))
        cursor += dur
    return cues


def build_composed_scenes(
    bundle: ReportBundle, plan: Any = None
) -> list[ComposedScene]:
    """ReportBundle 의 각 section → 1개 이상의 ComposedScene.

    plan(검증된 CompositionPlan) 이 주어지면 마지막에 연출 판단(헤드라인/페이싱/순서)을
    얹는다. 사실·차트 데이터는 plan 과 무관하게 결정론으로 산출된다(_apply_plan_to_scenes).

    한 section 의 chart_refs 에서 **모든** 시각 자산을 펼친다(차트당 1씬):
    - 지원 타입(candle/line/bar/donut) → chart 씬 (번들 데이터 주입)
    - 미지원 + prerendered_svg 있음 → svg 씬 (정적 폴백, C0 v0.25.0)
    - 미지원 + svg 없음 → 건너뜀(섹션에 시각 자산이 하나도 없으면 text 씬)
    section.prose 는 그 섹션의 전 씬 구간에 자막 큐로 깔린다(별도 build 단계).
    """
    charts_by_id = {c.chart_id: c for c in bundle.charts}
    accent = _theme_accent(bundle)
    up_color, down_color = _theme_token(bundle, "up"), _theme_token(bundle, "down")
    scenes: list[ComposedScene] = []
    cursor = 0.0
    for i, sec in enumerate(bundle.sections):
        prose = sec.prose or ""
        sid = sec.section_id or f"s{i + 1}"
        callout_t = round(min(3.0, _CHART_SCENE_SEC * 0.5), 2)

        # 섹션 차트를 순서대로 해소하고 full/strip 분류 (docs/CHART_DISPLAY_RULES.md).
        sec_charts = [charts_by_id[cid] for cid in sec.chart_refs if cid in charts_by_id]
        disp = _classify_section(sec_charts)

        visuals: list[ComposedScene] = []
        strip_buf: list[BundleChart] = []
        main_names: set[str] = set()   # 이 섹션에서 메인으로 그린 종목명(dedupe 기준)

        def _norm(s: str) -> str:
            return re.sub(r"\s+", "", (s or "")).lower()

        def _flush_strips() -> None:
            if not strip_buf:
                return
            charts = list(strip_buf)
            strip_buf.clear()
            items, seen = [], set()
            board_src = ""
            for c in charts:
                s = _strip_series(c)
                if not s:
                    continue
                nm = _norm(s["name"])
                if nm in main_names or nm in seen:  # 메인 중복 / 보드 내 중복 제외
                    continue
                seen.add(nm)
                items.append(s)
                if not board_src:
                    board_src = _source_label(c)
            if not items:
                return
            start, end, interval = _period_interval(_chart_dates(charts[0]))
            tb_vars: dict[str, Any] = {
                "takeaway": sec.heading or "주요 지표", "items": items,
                "source": board_src, "periodStart": start, "periodEnd": end, "interval": interval,
            }
            if up_color:
                tb_vars["upColor"] = up_color
            if down_color:
                tb_vars["downColor"] = down_color
            visuals.append(ComposedScene(
                scene_id=f"{sid}-strip{len(visuals)}", section_id=sid, start_sec=0.0,
                duration_sec=_CHART_SCENE_SEC, kind="chart", component="tickerboard",
                variables=tb_vars,
            ))

        for ch, dsp in zip(sec_charts, disp):
            if dsp == "strip":
                strip_buf.append(ch)
                continue
            _flush_strips()  # full 이 strip run 을 끊으면 먼저 보드로 묶어 낸다
            mapped = chart_to_component(ch, callout_t=callout_t, accent=accent)
            if mapped is not None:
                comp, variables = mapped
                if not variables.get("takeaway"):
                    variables["takeaway"] = sec.heading or ""
                main_names.add(_norm(ch.title))  # dedupe: 보드에서 이 종목 제외
                visuals.append(ComposedScene(
                    scene_id=f"{sid}-{ch.chart_id}", section_id=sid, start_sec=0.0,
                    duration_sec=_CHART_SCENE_SEC, kind="chart",
                    component=comp, variables=variables,
                ))
            elif ch.prerendered_svg:
                visuals.append(ComposedScene(
                    scene_id=f"{sid}-{ch.chart_id}", section_id=sid, start_sec=0.0,
                    duration_sec=_CHART_SCENE_SEC, kind="svg",
                    heading=ch.title or sec.heading or "", svg=ch.prerendered_svg,
                ))
        _flush_strips()

        if visuals:
            for v in visuals:
                v.start_sec = round(cursor, 3)
                cursor += v.duration_sec
            scenes.extend(visuals)
        else:
            dur = _estimate_duration(prose)
            scenes.append(ComposedScene(
                scene_id=sid, section_id=sid, start_sec=round(cursor, 3),
                duration_sec=dur, kind="text",
                heading=sec.heading or "", body=_text_scene_body(sec.pull_quote, prose),
            ))
            cursor += dur

    if plan is not None:
        scenes = _apply_plan_to_scenes(scenes, plan)
    return scenes


def _apply_plan_to_scenes(scenes: list[ComposedScene], plan: Any) -> list[ComposedScene]:
    """검증된 CompositionPlan 의 연출 판단을 결정론 씬에 얹는다(사실 불변, 연출만).

    적용: 헤드라인 override(미검증 필드는 <미검증> 라벨) · 페이싱 override(clamp) · 씬 재정렬.
    데이터(variables 의 차트 값)는 건드리지 않는다. plan 에 없는 씬은 원래 상대순서로 뒤에 붙는다.
    """
    by_id = {p.scene_id: p for p in plan.scenes}
    # 1) 필드 override (사실 불변 — 헤드라인/페이싱만)
    for sc in scenes:
        p = by_id.get(sc.scene_id)
        if p is None:
            continue
        if p.headline:
            head = p.headline
            if "headline" in p.unverified_fields:
                head = f"<미검증> {head}"
            if sc.kind == "chart":
                sc.variables["takeaway"] = head
            else:
                sc.heading = head
        if p.narration:
            sc.narration = ("<미검증> " + p.narration) if "narration" in p.unverified_fields else p.narration
        if p.duration_sec is not None:
            sc.duration_sec = round(min(30.0, max(3.0, float(p.duration_sec))), 3)
    # 2) 재정렬 — plan order 우선, 그 외는 원래 순서 보존(stable)
    order_of = {p.scene_id: p.order for p in plan.scenes}
    big = max([p.order for p in plan.scenes], default=0) + 1
    indexed = list(enumerate(scenes))
    indexed.sort(key=lambda t: (order_of.get(t[1].scene_id, big + t[0]), t[0]))
    ordered = [sc for _, sc in indexed]
    # 3) start_sec 전구간 재계산
    cur = 0.0
    for sc in ordered:
        sc.start_sec = round(cur, 3)
        cur += sc.duration_sec
    return ordered


# ---------------------------------------------------------------------------
# HTML 렌더 (순수)
# ---------------------------------------------------------------------------


def _stringify_complex(variables: dict[str, Any]) -> dict[str, Any]:
    """복합값(list/dict/None)을 JSON 문자열로 인코딩.

    컴포넌트의 data-composition-variables 는 candles/series/slices/callouts/endpoint 등을
    type="string"(JSON 문자열)으로 선언한다. host 에서 raw 배열/null 을 그대로 주면
    HyperFrames 의 변수 타입 처리가 첫 sub-comp 인스턴스화를 깨뜨리는 사고가 있었다(v0.34.14
    실측: candle 의 candles 배열 → root null). 컴포넌트는 문자열도 parseJSON 하므로 복합값을
    JSON 문자열로 인코딩해 선언 타입과 정합화한다. 스칼라(str/int/float/bool)는 그대로 둔다.
    """
    out: dict[str, Any] = {}
    for k, v in variables.items():
        out[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) or v is None else v
    return out


def _attr_json(obj: Any) -> str:
    """data-variable-values 용 — 단일따옴표 속성 안에 안전하게 박히도록 escape."""
    s = json.dumps(obj, ensure_ascii=False)
    return s.replace("&", "&amp;").replace("'", "&#39;")


def render_composition_html(
    *,
    title: str,
    scenes: list[ComposedScene],
    cues: Optional[list[ComposedCue]] = None,
    assets_prefix: str = "../assets",
    charts_prefix: str = "../lib/charts",
    width: int = 1920,
    height: int = 1080,
    audio_src: Optional[str] = None,
    total_override: Optional[float] = None,
) -> str:
    """ComposedScene[] (+ 절대 타임라인 자막 cues) → HyperFrames 컴포지션 HTML 문자열.

    각 씬은 class="clip" + data-start/duration 으로 프레임워크가 표시 구간을 관리한다.
    차트 씬은 sub-composition 임베드, 텍스트 씬은 인라인 카드(루트 타임라인이 fade).
    하단 자막바는 항상 떠 있고 텍스트만 큐 시점에 swap.

    total_override: 나레이션 경로처럼 씬이 0 이 아닌 lead 오프셋에서 시작하거나 말미 tail
    무음이 붙는 경우, 루트·audio 의 data-duration 을 실제 컴포지션 길이로 강제한다. 없으면
    씬 길이 합(씬이 0 부터 연속이라는 가정)을 쓴다.
    """
    if total_override is not None:
        total = round(float(total_override), 3)
    else:
        total = round(sum(s.duration_sec for s in scenes), 3) if scenes else 1.0
    abs_cues: list[ComposedCue] = list(cues or [])

    scene_divs: list[str] = []
    text_anim: list[str] = []
    n_sc = len(scenes)
    _XF = 0.6  # 크로스페이드 길이(초)
    for idx, sc in enumerate(scenes):
        host_id = f"scene-{idx + 1}"
        s, d = f"{sc.start_sec:.3f}", f"{sc.duration_sec:.3f}"
        next_start = scenes[idx + 1].start_sec if idx + 1 < n_sc else None

        # 씬 전환(모션 내재화): 모든 씬은 opacity:0 으로 시작, 자기 시작에 fade-in,
        # 다음 씬 시작에 fade-out → 크로스페이드(clip 하드컷 대신). 챕터는 sub-comp 가 내부
        # 등장 애니를, 텍스트/svg 는 헤딩 reveal 을 추가로 얹는다.
        text_anim.append(
            f'      tl.fromTo("#{host_id}", {{ opacity: 0 }}, '
            f'{{ opacity: 1, duration: {_XF}, ease: "power2.inOut" }}, {s});'
        )
        if next_start is not None:
            text_anim.append(
                f'      tl.to("#{host_id}", {{ opacity: 0, duration: {_XF}, '
                f'ease: "power2.inOut" }}, {next_start:.3f});'
            )

        if sc.kind == "chart" and sc.component:
            src = f"{charts_prefix}/{sc.component}.html"
            scene_divs.append(
                f'      <div class="scene-host" id="{html.escape(host_id)}" style="opacity:0"\n'
                f'           data-composition-id="{html.escape(host_id)}"\n'
                f'           data-composition-src="{html.escape(src)}"\n'
                f"           data-variable-values='{_attr_json(_stringify_complex(sc.variables))}'\n"
                f'           data-start="{s}" data-duration="{d}" data-track-index="1"></div>'
            )
        elif sc.kind == "svg":
            # 미지원 타입의 정적 폴백 — agents_reviewer prerendered_svg 를 그대로 인라인.
            heading = html.escape(sc.heading or "")
            scene_divs.append(
                f'      <div class="scene-host svg-scene" id="{host_id}" style="opacity:0">\n'
                f'        <div class="hf-card svg-card">\n'
                f'          <div class="svg-heading">{heading}</div>\n'
                f'          <div class="svg-wrap">{sc.svg}</div>\n'
                f'        </div>\n'
                f'      </div>'
            )
            text_anim.append(
                f'      if (window.__hf) window.__hf.revealWords(tl, '
                f'document.querySelector("#{host_id} .svg-heading"), {s} + 0.2, {{ stagger: 0.05 }});'
            )
        else:
            heading = html.escape(sc.heading or "")
            body = html.escape(sc.body or "")
            scene_divs.append(
                f'      <div class="scene-host text-scene" id="{host_id}" style="opacity:0">\n'
                f'        <div class="text-card">\n'
                f'          <div class="text-heading">{heading}</div>\n'
                f'          <div class="text-body">{body}</div>\n'
                f'        </div>\n'
                f'      </div>'
            )
            # 텍스트 씬: 헤딩 SplitText reveal + 본문 fade(호스트 크로스페이드 위에 얹음).
            text_anim.append(
                f'      if (window.__hf) window.__hf.revealWords(tl, '
                f'document.querySelector("#{host_id} .text-heading"), {s} + 0.25, {{ stagger: 0.05 }});\n'
                f'      tl.fromTo("#{host_id} .text-body", {{ opacity: 0, y: 18 }}, '
                f'{{ opacity: 1, y: 0, duration: 0.6, ease: "power2.out" }}, {s} + 0.5);'
            )

    # 자막 큐 JS 배열 (절대 타임라인).
    cue_lines = ",\n        ".join(
        f'{{ t: {c.at_sec:.3f}, text: "{_escape_js(c.text)}" }}' for c in abs_cues
    )
    cues_block = f"[\n        {cue_lines},\n      ]" if abs_cues else "[]"
    first_cue = html.escape(abs_cues[0].text) if abs_cues else ""  # HTML 컨텍스트(span 안)

    # 음성 나레이션 <audio> 블록 — audio_src 가 있을 때만 (HyperFrames 가 재생할 정확한 마크업).
    if audio_src:
        audio_block = (
            '      <audio\n'
            '        id="narration-comp"\n'
            '        class="clip"\n'
            '        data-start="0"\n'
            f'        data-duration="{total:.3f}"\n'
            '        data-track-index="100"\n'
            f'        src="{html.escape(audio_src)}"\n'
            '        preload="auto"\n'
            '      ></audio>'
        )
    else:
        audio_block = ""

    tmpl = _COMPOSITION_TEMPLATE
    return (
        tmpl
        .replace("@@WIDTH@@", str(width))
        .replace("@@HEIGHT@@", str(height))
        .replace("@@ASSETS@@", assets_prefix)
        .replace("@@TOTAL@@", f"{total:.3f}")
        .replace("@@HEADLINE@@", html.escape(title))
        .replace("@@SCENES@@", "\n".join(scene_divs))
        .replace("@@FIRSTCUE@@", first_cue)
        .replace("@@CUES@@", cues_block)
        .replace("@@TEXTANIM@@", "\n".join(text_anim))
        .replace("@@AUDIO@@", audio_block)
    )


def _escape_js(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


_COMPOSITION_TEMPLATE = """<!doctype html>
<!-- 자동 생성 (orchestrator/hyperframes_compose.py). 직접 편집 금지 — 재생성됨. -->
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=@@WIDTH@@, height=@@HEIGHT@@" />
    <script src="@@ASSETS@@/gsap.min.js"></script>
    <script src="@@ASSETS@@/../lib/motion/hf-motion.js"></script>
    <style>
      @font-face {
        font-family: "Pretendard Variable";
        src: url("@@ASSETS@@/fonts/PretendardVariable.woff2") format("woff2-variations");
        font-weight: 100 900; font-style: normal; font-display: block;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body {
        margin: 0; width: @@WIDTH@@px; height: @@HEIGHT@@px; overflow: hidden; background: #f6f3ec;
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #16130f; word-break: keep-all; overflow-wrap: anywhere;
      }
      /* 에디토리얼 톤 (v0.34.21) — 따뜻한 종이 + 절제된 테라코타 + 헤어라인 */
      .brand { position: absolute; top: 64px; left: 120px; display: flex; align-items: center; gap: 12px; z-index: 10; }
      .brand-mark { width: 14px; height: 14px; border-radius: 3px; background: #b5482e; }
      .brand-name { font-size: 22px; font-weight: 800; letter-spacing: 5px; text-transform: uppercase; color: #16130f; }
      .kicker { position: absolute; top: 66px; right: 120px; left: 560px; text-align: right; font-size: 20px;
        font-weight: 700; letter-spacing: 1px; color: #9b9082; z-index: 10; }
      .topline { position: absolute; top: 116px; left: 120px; right: 120px; height: 2px; background: #16130f; z-index: 10; }
      .scene-host { position: absolute; inset: 0; }
      .text-scene { display: flex; align-items: center; justify-content: flex-start; }
      .text-card { width: 1280px; margin-left: 160px; padding-left: 50px; text-align: left; border-left: 6px solid #b5482e; }
      .text-heading { font-size: 96px; font-weight: 900; line-height: 1.05; letter-spacing: -2px; color: #16130f; }
      .text-body { margin-top: 30px; font-size: 40px; font-weight: 600; line-height: 1.5; color: #6a6157; max-width: 1040px; }
      /* svg/text 씬도 차트 sub-comp 과 동일한 top:160px 띠에서 시작 — topline(116px) 비켜감.
         (이전 align-items:center 는 콘텐츠가 크면 카드 윗변이 116px 위로 올라가 헤어라인을 뚫었음) */
      .svg-scene { display: flex; align-items: flex-start; justify-content: center; padding-top: 160px; }
      .svg-card { width: 1520px; background: #fbf9f4; border: 1px solid #e2dccf; border-radius: 18px;
        box-shadow: 0 1px 2px rgba(22,19,15,0.05); padding: 48px 56px; max-height: 780px; overflow: hidden; }
      .svg-heading { font-size: 56px; font-weight: 900; line-height: 1.15; letter-spacing: -0.3px; color: #16130f; margin-bottom: 24px; }
      .svg-wrap { width: 1408px; }
      .svg-wrap svg { display: block; width: 100%; height: auto; max-height: 560px; }
      .subtitle-bar { position: absolute; bottom: 40px; left: 0; right: 0; display: flex; justify-content: center;
        padding: 0 160px; z-index: 20; }
      .subtitle { background: #2a2320; padding: 15px 34px; border-radius: 10px; max-width: 1320px;
        box-shadow: 0 4px 18px rgba(22,19,15,0.22); min-height: 66px; min-width: 480px;
        display: flex; align-items: center; justify-content: center; }
      .subtitle .text { font-size: 33px; line-height: 1.3; font-weight: 700; color: #f6f3ec;
        letter-spacing: -0.3px; text-align: center; word-break: keep-all; overflow-wrap: anywhere; }
    </style>
  </head>
  <body>
    <div id="root" class="clip" data-composition-id="root" data-start="0" data-duration="@@TOTAL@@"
         data-track-index="0" data-width="@@WIDTH@@" data-height="@@HEIGHT@@">
      <div class="brand"><span class="brand-mark"></span><span class="brand-name">OSINT 브리핑</span></div>
      <div class="kicker">@@HEADLINE@@</div>
      <div class="topline"></div>

@@SCENES@@

      <div class="subtitle-bar"><div class="subtitle"><span class="text" id="subtitleText">@@FIRSTCUE@@</span></div></div>
@@AUDIO@@
    </div>

    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true, defaults: { ease: "power2.out" } });
      tl.from(".brand", { opacity: 0, y: -8, duration: 0.4 }, 0);
      tl.from(".kicker", { opacity: 0, duration: 0.5 }, 0.1);

@@TEXTANIM@@

      const cues = @@CUES@@;
      const $sub = document.getElementById("subtitleText");
      const $box = document.querySelector(".subtitle");
      if (cues.length) {
        $sub.textContent = cues[0].text;
        tl.fromTo($box, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, overwrite: "auto" }, cues[0].t);
        // 자막 swap: 순수 콜백 큐(tl 의 call)는 seek 기반 캡처 렌더러가 미지원("... is not a
        // function" → zero duration). hf-motion 의 countUp 과 동일하게 tl.to(proxy, {onUpdate})
        // 로 현재 시점의 활성 큐 텍스트를 고른다(seek-safe, RENDER-AP).
        var __cue = { t: 0 };
        tl.to(__cue, {
          t: @@TOTAL@@, duration: @@TOTAL@@, ease: "none",
          onUpdate: function () {
            var now = __cue.t, txt = cues[0].text;
            for (var k = 0; k < cues.length; k++) {
              if (cues[k].t <= now + 1e-4) { txt = cues[k].text; } else { break; }
            }
            if ($sub.textContent !== txt) { $sub.textContent = txt; }
          }
        }, 0);
      }

      window.__timelines["root"] = tl;
    </script>
  </body>
</html>
"""


# ---------------------------------------------------------------------------
# I/O 경계
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def generated_dir() -> Path:
    return _repo_root() / "hyperframes" / "generated"


def composition_path(project_id: str) -> Path:
    return generated_dir() / f"{_safe_slug(project_id)}.html"


def _safe_slug(project_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", project_id.strip())
    return slug or "composition"


def build_composition_html_from_bundle(
    bundle: ReportBundle, plan: Any = None
) -> tuple[list[ComposedScene], str]:
    """ReportBundle → (씬 목록, 컴포지션 HTML).

    자막 큐(plan 없음): 각 section.prose 를 그 섹션의 **전 씬 구간**에 걸쳐 글자수 비례로 깐다.
    자막 큐(plan 있음): codex 가 재작성한 plan.captions 를 각 씬 구간 안에 순차 배치(미검증 라벨).
    """
    scenes = build_composed_scenes(bundle, plan)

    if plan is not None and plan.captions:
        abs_cues = _cues_from_plan(scenes, plan)
    else:
        prose_by_sid = {(s.section_id or f"s{i + 1}"): (s.prose or "")
                        for i, s in enumerate(bundle.sections)}
        spans: dict[str, list[float]] = {}
        for sc in scenes:
            sid = sc.section_id
            if sid not in spans:
                spans[sid] = [sc.start_sec, 0.0]
            spans[sid][0] = min(spans[sid][0], sc.start_sec)
            spans[sid][1] += sc.duration_sec
        abs_cues = []
        for sid, (start, span) in spans.items():
            for cue in _split_cues(prose_by_sid.get(sid, ""), span):
                abs_cues.append(ComposedCue(text=cue.text, at_sec=round(start + cue.startSec, 3)))
    abs_cues.sort(key=lambda c: c.at_sec)

    title = (plan.title if (plan is not None and plan.title) else
             (bundle.report.headline if bundle.report else ""))
    html_str = render_composition_html(title=title, scenes=scenes, cues=abs_cues)
    return scenes, html_str


def _cues_from_plan(scenes: list[ComposedScene], plan: Any) -> list["ComposedCue"]:
    """plan.captions(씬별 순차 자막)를 절대 타임라인 큐로 변환. 미검증은 <미검증> 라벨."""
    span_of = {sc.scene_id: (sc.start_sec, sc.duration_sec) for sc in scenes}
    by_scene: dict[str, list[Any]] = {}
    for cap in plan.captions:
        by_scene.setdefault(cap.scene_ref, []).append(cap)
    cues: list[ComposedCue] = []
    for scene_id, caps in by_scene.items():
        if scene_id not in span_of:
            continue
        start, dur = span_of[scene_id]
        caps = sorted(caps, key=lambda c: c.order)
        total_chars = sum(max(1, len(c.text)) for c in caps) or 1
        cursor = 0.0
        for i, c in enumerate(caps):
            text = f"<미검증> {c.text}" if c.unverified else c.text
            cues.append(ComposedCue(text=text, at_sec=round(start + cursor, 3)))
            slice_sec = dur if i == len(caps) - 1 else dur * (max(1, len(c.text)) / total_chars)
            cursor += slice_sec
    return cues


def _atomic_write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise


def build_and_persist_composition(
    project_id: str, bundle: ReportBundle, plan: Any = None
) -> Path:
    """ReportBundle → `hyperframes/generated/<project_id>.html` 영속화 후 경로 반환."""
    _, html_str = build_composition_html_from_bundle(bundle, plan)
    path = composition_path(project_id)
    _atomic_write_text(path, html_str)
    return path


__all__ = [
    "ComposedCue",
    "ComposedScene",
    "chart_to_component",
    "build_composed_scenes",
    "render_composition_html",
    "build_composition_html_from_bundle",
    "composition_path",
    "generated_dir",
    "build_and_persist_composition",
]
