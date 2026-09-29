"""차트 정직성 결정적 검사 (v4.3.0, docs/handoff/20 §5.3, back_and_forth D-0084 작업 5·D-0087).

검사 4개(checks 의 hard 항목): `chart_honesty` · `series_limit_3` · `units_visible` · `as_of_visible`.
대상과 적용 검사는 `rules qa_checks.chart_targets`(요소의 축 종류 → 검사 id) 한 곳(D-0087 보정 3). 축 종류는 렌더러 모듈의 `AXIS`
상수("value"|"date"|"none") — 시간축 series 레이어·패널 11종이 적는다(test_registry_complete). 적용되지 않는 검사는
`n/a(<축> 축)` 메모로 남긴다(조용한 생략 아님, D-0087).

판정은 차트 메타(`ChartMeta`)만 본다. 메타는 요소 데이터(레코드·패널 필드)와 **프리뷰 컷에 실제로 그린 글자**(typography.GLYPH_LOG)
에서 만든다 — 압축 라벨·출처 줄이 "그려졌는가"는 화면 기록으로 확인한다(코드 리뷰로 '적용됨' 판정 금지, 15 P12).

| 20 §5.3 규칙 | 검사 id | 메타 |
| 막대는 0에서 시작 | chart_honesty | kind == bar → baseline == 0 |
| 축 압축 시 물결 + 라벨 | chart_honesty | 화면에 걸친 압축 구간 수 ↔ 그 컷에 그린 압축 라벨 |
| 단위 표시 | units_visible | unit_label ∈ rules data.units (또는 dual_line y_prefix ∈ data.unit_prefixes) |
| %와 %p 구분 | chart_honesty | 한 차트(레인·패널) 안 계열 단위가 하나, 표시 단위의 첫 토큰 = 계열 단위 |
| 계열 수 ≤ 3 | series_limit_3 | series_count ≤ qa_checks.series_max |
| 이중 축 라벨·색 | chart_honesty | axes == 2 → 축 라벨 2개·축 색 2개(계열 색과 같은 순서) |
| 로그 척도 표기 | chart_honesty | log_scale → log_label |
| 기준 시점(as of) | as_of_visible | as_of 있음(시리즈 = 레코드, 패널 = 08 §9 출처 체계) |
| 출처 줄 | as_of_visible | source_shown(시리즈 = 그 컷에 출처 줄을 그림, 패널 = 출처 목록 또는 추정 태그) |
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from rules import load_rules

CHECK_IDS: tuple[str, ...] = ("chart_honesty", "series_limit_3", "units_visible", "as_of_visible")
Axis = Literal["value", "date", "none"]


class ChartMeta(BaseModel):
    """차트 하나(시리즈 레인·수치 패널·시간축 무대)의 정직성 메타."""

    model_config = ConfigDict(extra="forbid")

    ref: str
    axis: Axis
    kind: str
    baseline: Optional[float] = None
    series_count: int = 0
    units: list[str] = Field(default_factory=list)      # 계열마다 데이터 단위(레코드 unit 등)
    unit_label: Optional[str] = None                    # 화면에 쓴 단위(레인 이름 괄호·패널 unit·y_prefix)
    axes: int = 1
    axis_labels: list[str] = Field(default_factory=list)
    axis_colors: list[str] = Field(default_factory=list)
    series_colors: list[str] = Field(default_factory=list)
    log_scale: bool = False
    log_label: bool = False
    compress_on_screen: int = 0                         # 프리뷰 컷에 걸친 압축 구간(컷 × 구간)
    compress_marked: int = 0                            # 그중 압축 라벨이 그 컷에 그려진 수
    as_of: Optional[str] = None
    source_shown: Optional[bool] = None                 # None = 프리뷰 컷에 나오지 않아 확인 불가(메모)


def _first_token(s: str) -> str:
    return s.split()[0] if s.strip() else ""


def chart_honesty(m: ChartMeta) -> list[str]:
    out: list[str] = []
    if m.kind == "bar" and m.baseline not in (0, 0.0):
        out.append(f"[bar-baseline] {m.ref}: 막대 기준선 {m.baseline} ≠ 0")
    if m.compress_marked < m.compress_on_screen:
        out.append(f"[compress-unmarked] {m.ref}: 화면에 걸친 압축 구간 {m.compress_on_screen} 중 물결·라벨 {m.compress_marked}")
    if len(set(m.units)) > 1:
        out.append(f"[unit-mix] {m.ref}: 한 차트에 단위가 섞였다 {sorted(set(m.units))}(%/%p 구분)")
    elif m.units and m.unit_label is not None and m.axis == "value" and _first_token(m.unit_label) != m.units[0] \
            and m.unit_label not in load_rules().data.unit_prefixes:
        out.append(f"[unit-mismatch] {m.ref}: 화면 단위 {m.unit_label!r} ≠ 데이터 단위 {m.units[0]!r}(%/%p 구분)")
    if m.axes == 2 and (len(m.axis_labels) != 2 or len(m.axis_colors) != 2 or m.axis_colors != m.series_colors[:2]):
        out.append(f"[dual-axis] {m.ref}: 이중 축은 양쪽 축 라벨·색이 계열과 대응해야 한다(라벨 {m.axis_labels}, 축 색 {m.axis_colors},"
                   f" 계열 색 {m.series_colors})")
    if m.log_scale and not m.log_label:
        out.append(f"[log-unlabeled] {m.ref}: 로그 척도인데 '로그 척도' 표기가 없다")
    return out


def series_limit_3(m: ChartMeta) -> list[str]:
    mx = load_rules().qa_checks.series_max
    return [f"[series-limit] {m.ref}: 계열 {m.series_count} > {mx}"] if m.series_count > mx else []


def units_visible(m: ChartMeta) -> list[str]:
    d = load_rules().data
    if m.unit_label and (_first_token(m.unit_label) in d.units or m.unit_label in d.unit_prefixes):
        return []
    return [f"[unit-missing] {m.ref}: 화면 단위 {m.unit_label!r} 가 rules data.units·unit_prefixes 에 없다"]


def as_of_visible(m: ChartMeta) -> list[str]:
    out = []
    if not m.as_of:
        out.append(f"[as-of-missing] {m.ref}: 기준 시점(as of) 없음")
    if m.source_shown is False:
        out.append(f"[source-missing] {m.ref}: 출처 줄이 화면에 없다")
    return out


CHECKS = {"chart_honesty": chart_honesty, "series_limit_3": series_limit_3, "units_visible": units_visible,
          "as_of_visible": as_of_visible}


def judge(metas: list[ChartMeta]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """메타 → ({검사 id: hard 상세}, {검사 id: 메모}). 축 종류별 적용 검사는 rules qa_checks.chart_targets."""
    targets = load_rules().qa_checks.chart_targets
    hard: dict[str, list[str]] = {k: [] for k in CHECK_IDS}
    notes: dict[str, list[str]] = {k: [] for k in CHECK_IDS}
    for m in metas:
        on = set(targets[m.axis])
        for k in CHECK_IDS:
            if k in on:
                hard[k] += CHECKS[k](m)
            else:
                notes[k].append(f"n/a({m.axis} 축) {m.ref}")
        if "as_of_visible" in on and m.source_shown is None:
            notes["as_of_visible"].append(f"프리뷰 컷 밖(출처 줄 확인 불가 — 레코드 as_of {m.as_of}) {m.ref}")
    return hard, notes


# ------------------------------------------------------------------ 메타 만들기(프로젝트)
def _cut_texts(drawn: list[tuple[str, float, Optional[str], str]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for lab, _, _, s in drawn:
        out.setdefault(lab, set()).add(s)
    return out


def project_metas(P, times: list[float], labels: list[str], drawn: list[tuple[str, float, Optional[str], str]]) -> list[ChartMeta]:  # noqa: ANN001, N803
    """프로젝트의 차트 메타 — 시간축 무대(압축), series 레인, 패널(모듈 AXIS·chart_meta, 이벤트 chart 로 덮어쓰기)."""
    from engine.projection import View  # noqa: PLC0415
    from engine.style import FPS, TIMELINE  # noqa: PLC0415

    texts = _cut_texts(drawn)
    metas: list[ChartMeta] = []
    st = P.R.stage
    if st.name == "timeline":
        on = marked = 0
        for t, lab in zip(times, labels):
            v = View(st, P.cams[min(P.n_frames - 1, int(t * FPS))])
            n = len(st.compress_on_screen(v))
            on += n
            marked += n if TIMELINE.wave.label in texts.get(lab, set()) else 0
        metas.append(ChartMeta(ref="stage timeline", axis="date", kind="timeline", compress_on_screen=on, compress_marked=marked))
        metas += _series_metas(P, st, times, labels, texts)
    for e in P.events:
        if e["type"] != "panel":
            continue
        axis = PANEL_AXIS[e["kind"]]
        base = {"ref": f"panel {e['kind']} {e['title']!r} t0={e['t0']:.2f}", "axis": axis, "kind": e["kind"]}
        if axis == "value":
            base.update(PANEL_META[e["kind"]](e))
        if e.get("chart"):
            base.update({k: v for k, v in e["chart"].items() if v is not None})
        metas.append(ChartMeta(**base))
    return metas


def _series_metas(P, st, times: list[float], labels: list[str], texts: dict[str, set[str]]) -> list[ChartMeta]:  # noqa: ANN001, N803
    from data.series import load_series  # noqa: PLC0415
    from engine.layers.series import AXIS, record_ids, source_line  # noqa: PLC0415

    out: list[ChartMeta] = []
    by_lane: dict[str, list[dict]] = {}
    for e in P.events:
        if e["type"] == "series":
            by_lane.setdefault(e["lane"], []).append(e)
    for lane, evs in by_lane.items():
        ln = st.lanes[st.lane_index(lane)]
        recs = [load_series(sid) for e in evs for sid in record_ids(e)]   # band = 계열 하나, 레코드 둘(v4.4.0)
        shown: Optional[bool] = None
        for e in evs:
            cuts = [lab for t, lab in zip(times, labels) if e["t0"] <= t <= e["t1"]]
            if cuts:
                ok = all(source_line(e) in texts.get(lab, set()) for lab in cuts)
                shown = ok if shown is None else shown and ok
        out.append(ChartMeta(ref=f"series lane {lane!r} [{', '.join(r.series_id for r in recs)}]", axis=AXIS,
                             kind="line", series_count=len(evs), units=[r.unit for r in recs],
                             unit_label=ln.unit, as_of=min(r.as_of for r in recs), source_shown=shown))
    return out


def _dots_meta(e: dict) -> dict:
    pv = e["provenance"]
    return {"series_count": 1, "units": [e["unit"]] if e["unit"] else [], "unit_label": e["unit"] or None,
            "as_of": "08 §9 출처 체계", "source_shown": bool(pv["sources"]) or _tag(pv)}


def _dual_meta(e: dict) -> dict:
    pv = e["provenance"]
    unit = e.get("unit")
    return {"series_count": len(e["series"]), "units": [unit] * len(e["series"]) if unit else [],
            "unit_label": unit or e["y_prefix"] or None, "series_colors": [s["col"] for s in e["series"]],
            "as_of": "08 §9 출처 체계", "source_shown": bool(pv["sources"]) or _tag(pv)}


def _tag(pv: dict) -> bool:
    from engine.panels.base import prov_tag_text  # noqa: PLC0415

    return prov_tag_text(pv) is not None


def _panel_axes() -> dict[str, Axis]:
    import importlib  # noqa: PLC0415

    return {k: importlib.import_module(f"engine.panels.{k}").AXIS for k in load_rules().registries.panel_kinds}


PANEL_AXIS: dict[str, Axis] = _panel_axes()
PANEL_META = {"dots": _dots_meta, "dual_line": _dual_meta}   # AXIS == "value" 인 패널의 메타(test_registry_complete 가 대조)


__all__ = ["CHECK_IDS", "ChartMeta", "PANEL_AXIS", "PANEL_META", "as_of_visible", "chart_honesty", "judge", "project_metas",
           "series_limit_3", "units_visible"]
