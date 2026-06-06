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
    """펼쳐진 씬 1 개. chart 면 컴포넌트+주입변수, text 면 heading/prose 만."""

    model_config = ConfigDict(extra="forbid")

    scene_id: str
    start_sec: float
    duration_sec: float
    kind: str  # "chart" | "text"
    component: Optional[str] = None       # kind=="chart" 일 때 lib/charts 파일명
    variables: dict[str, Any] = Field(default_factory=dict)  # data-variable-values 페이로드
    heading: str = ""                     # text 씬 헤드라인 (chart 는 variables.takeaway)
    body: str = ""                        # text 씬 본문(pull_quote/prose)


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
    x_labels, ys, callouts = [], [], []
    for i, r in enumerate(rows):
        x_labels.append(_short_date(r.get("x", r.get("label", i))))
        y = _num(r.get("y"))
        ys.append(_clean(y))
        ev = r.get("event")
        if ev:
            callouts.append({"xi": i, "si": 0, "t": callout_t, "title": str(ev), "sub": "", "dir": "ur"})
    if not ys:
        return None
    y_min, y_max, y_step = _nice_bounds(min(ys), max(ys))
    series = [{"name": chart.title or "값", "color": "#e84a2d", "points": ys}]
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


def chart_to_component(chart: BundleChart, *, callout_t: float = 3.0) -> Optional[tuple[str, dict]]:
    """BundleChart → (lib/charts 컴포넌트 파일명, data-variable-values 변수 dict).

    지원 타입이 아니거나 데이터가 비어 매핑 불가면 None (호출자가 텍스트 씬 폴백).
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
    return comp, v


# ---------------------------------------------------------------------------
# 씬 펼치기 (순수)
# ---------------------------------------------------------------------------


def _estimate_duration(prose: str) -> float:
    n = len(prose.strip())
    return max(_SCENE_MIN_SEC, min(_SCENE_MAX_SEC, n / _NARRATION_CPS)) if n else _SCENE_MIN_SEC


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


def build_composed_scenes(bundle: ReportBundle) -> list[ComposedScene]:
    """ReportBundle 의 각 section → ComposedScene. chart_refs 의 첫 지원 차트를 attach."""
    charts_by_id = {c.chart_id: c for c in bundle.charts}
    scenes: list[ComposedScene] = []
    cursor = 0.0
    for i, sec in enumerate(bundle.sections):
        prose = sec.prose or ""
        duration = _estimate_duration(prose)
        callout_t = round(min(3.0, max(1.5, duration * 0.5)), 2)

        mapped: Optional[tuple[str, dict]] = None
        for cid in sec.chart_refs:
            ch = charts_by_id.get(cid)
            if ch is None:
                continue
            mapped = chart_to_component(ch, callout_t=callout_t)
            if mapped is not None:
                break

        sid = sec.section_id or f"s{i + 1}"
        if mapped is not None:
            comp, variables = mapped
            if not variables.get("takeaway"):
                variables["takeaway"] = sec.heading or ""
            scenes.append(ComposedScene(
                scene_id=sid, start_sec=round(cursor, 3), duration_sec=duration,
                kind="chart", component=comp, variables=variables,
            ))
        else:
            scenes.append(ComposedScene(
                scene_id=sid, start_sec=round(cursor, 3), duration_sec=duration,
                kind="text", heading=sec.heading or "", body=sec.pull_quote or prose,
            ))
        cursor += duration
    return scenes


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
) -> str:
    """ComposedScene[] (+ 절대 타임라인 자막 cues) → HyperFrames 컴포지션 HTML 문자열.

    각 씬은 class="clip" + data-start/duration 으로 프레임워크가 표시 구간을 관리한다.
    차트 씬은 sub-composition 임베드, 텍스트 씬은 인라인 카드(루트 타임라인이 fade).
    하단 자막바는 항상 떠 있고 텍스트만 큐 시점에 swap.
    """
    total = round(sum(s.duration_sec for s in scenes), 3) if scenes else 1.0
    abs_cues: list[ComposedCue] = list(cues or [])

    scene_divs: list[str] = []
    text_anim: list[str] = []
    for idx, sc in enumerate(scenes):
        host_id = f"scene-{idx + 1}"
        s, d = f"{sc.start_sec:.3f}", f"{sc.duration_sec:.3f}"
        if sc.kind == "chart" and sc.component:
            src = f"{charts_prefix}/{sc.component}.html"
            scene_divs.append(
                f'      <div class="scene-host clip" data-composition-id="{html.escape(host_id)}"\n'
                f'           data-composition-src="{html.escape(src)}"\n'
                f"           data-variable-values='{_attr_json(_stringify_complex(sc.variables))}'\n"
                f'           data-start="{s}" data-duration="{d}" data-track-index="1"></div>'
            )
        else:
            heading = html.escape(sc.heading or "")
            body = html.escape(sc.body or "")
            scene_divs.append(
                f'      <div class="scene-host text-scene clip" id="{host_id}"\n'
                f'           data-start="{s}" data-duration="{d}" data-track-index="1">\n'
                f'        <div class="text-card">\n'
                f'          <div class="text-heading">{heading}</div>\n'
                f'          <div class="text-body">{body}</div>\n'
                f'        </div>\n'
                f'      </div>'
            )
            # 텍스트 씬 등장 애니(루트 타임라인). 단일 transform.
            text_anim.append(
                f'      tl.fromTo("#{host_id} .text-card", {{ opacity: 0, y: 24 }}, '
                f'{{ opacity: 1, y: 0, duration: 0.6, ease: "power2.out" }}, {s});'
            )

    # 자막 큐 JS 배열 (절대 타임라인).
    cue_lines = ",\n        ".join(
        f'{{ t: {c.at_sec:.3f}, text: "{_escape_js(c.text)}" }}' for c in abs_cues
    )
    cues_block = f"[\n        {cue_lines},\n      ]" if abs_cues else "[]"
    first_cue = html.escape(abs_cues[0].text) if abs_cues else ""  # HTML 컨텍스트(span 안)

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
    <style>
      @font-face {
        font-family: "Pretendard Variable";
        src: url("@@ASSETS@@/fonts/PretendardVariable.woff2") format("woff2-variations");
        font-weight: 100 900; font-style: normal; font-display: block;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body {
        margin: 0; width: @@WIDTH@@px; height: @@HEIGHT@@px; overflow: hidden; background: #f5f1ea;
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #1a1a1a; word-break: keep-all; overflow-wrap: anywhere;
      }
      .brand { position: absolute; top: 56px; left: 80px; display: flex; align-items: center; gap: 12px; z-index: 10; }
      .brand-mark { width: 14px; height: 14px; border-radius: 3px; background: #e84a2d; }
      .brand-name { font-size: 20px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; }
      .kicker { position: absolute; top: 60px; right: 80px; left: 460px; text-align: right; font-size: 18px;
        font-weight: 700; letter-spacing: 1px; color: rgba(26,26,26,0.4); z-index: 10; }
      .scene-host { position: absolute; inset: 0; }
      .text-scene { display: flex; align-items: center; justify-content: center; }
      .text-card { width: 1400px; padding: 0 80px; text-align: center; }
      .text-heading { font-size: 84px; font-weight: 900; line-height: 1.12; letter-spacing: -0.5px; color: #1a1a1a; }
      .text-body { margin-top: 28px; font-size: 38px; font-weight: 600; line-height: 1.5; color: rgba(26,26,26,0.66); }
      .subtitle-bar { position: absolute; bottom: 72px; left: 0; right: 0; display: flex; justify-content: center;
        padding: 0 140px; z-index: 20; }
      .subtitle { background: #4a1e10; padding: 24px 48px; border-radius: 12px; max-width: 1520px;
        box-shadow: 0 6px 32px rgba(74,30,16,0.4); min-height: 96px; min-width: 720px;
        display: flex; align-items: center; justify-content: center; }
      .subtitle .text { font-size: 40px; line-height: 1.3; font-weight: 800; color: #ffffff;
        letter-spacing: -0.4px; text-align: center; word-break: keep-all; overflow-wrap: anywhere; }
    </style>
  </head>
  <body>
    <div id="root" class="clip" data-composition-id="root" data-start="0" data-duration="@@TOTAL@@"
         data-track-index="0" data-width="@@WIDTH@@" data-height="@@HEIGHT@@">
      <div class="brand"><span class="brand-mark"></span><span class="brand-name">OSINT 브리핑</span></div>
      <div class="kicker">@@HEADLINE@@</div>

@@SCENES@@

      <div class="subtitle-bar"><div class="subtitle"><span class="text" id="subtitleText">@@FIRSTCUE@@</span></div></div>
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
      if (cues.length) { $sub.textContent = cues[0].text; }
      cues.forEach((c, i) => {
        if (i === 0) {
          tl.fromTo($box, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, overwrite: "auto" }, c.t);
        } else {
          tl.to($box, { opacity: 0, duration: 0.2, overwrite: "auto" }, Math.max(0, c.t - 0.25));
          tl.call(() => { $sub.textContent = c.text; }, [], Math.max(0, c.t - 0.05));
          tl.to($box, { opacity: 1, duration: 0.25, overwrite: "auto" }, c.t);
        }
      });

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


def build_composition_html_from_bundle(bundle: ReportBundle) -> tuple[list[ComposedScene], str]:
    """ReportBundle → (씬 목록, 컴포지션 HTML). 자막 큐는 section.prose 에서 절대 타임라인으로."""
    scenes = build_composed_scenes(bundle)
    # 절대 타임라인 자막 큐: 각 section.prose 를 씬 구간 안에서 큐 분할.
    abs_cues: list[ComposedCue] = []
    for sec, sc in zip(bundle.sections, scenes):
        for cue in _split_cues(sec.prose or "", sc.duration_sec):
            abs_cues.append(ComposedCue(text=cue.text, at_sec=round(sc.start_sec + cue.startSec, 3)))
    title = bundle.report.headline if bundle.report else ""
    html_str = render_composition_html(title=title, scenes=scenes, cues=abs_cues)
    return scenes, html_str


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


def build_and_persist_composition(project_id: str, bundle: ReportBundle) -> Path:
    """ReportBundle → `hyperframes/generated/<project_id>.html` 영속화 후 경로 반환."""
    _, html_str = build_composition_html_from_bundle(bundle)
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
