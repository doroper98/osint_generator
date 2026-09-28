"""번들 지도·차트 → 연출가 입력 재료 + 연출 초안 (v3.5.0, docs/handoff/12 §2·§7, back_and_forth D-0063 작업 4).

- `intake/bundle_materials.json`(`BundleMaterials`): 장소(마커)·경로(호)·패널 데이터(차트)·미디어 후보(이미지)·엔티티 뱃지 후보·
  인용 후보(highlights). **재료일 뿐 강제가 아니다** — DirectorWorker 입력 `{bundle_materials}` 자리(17 §5.3)에 들어간다.
- `direction.draft.yaml`: places·paths·패널 이벤트만. 숏은 장면마다 그 장면이 부르는 장소를 `engine.framing.frame_points`
  (카메라 제안과 같은 함수)로 담은 컷 하나 — 제안이다. 최종 `direction.yaml` 은 DirectorWorker 가 쓴다(15 P8).
- 이전 영상의 연출은 넣지 않는다(15 P9). 대응표는 `rules bundle`(P3). 표에 없는 차트 종류·패널 모델을 통과하지 못한
  차트는 버리지 않고 `unsupported[]` 에 사유와 함께 남긴다(15 P6).
- 차트 provenance: `bundle.verified_when` + 출처 ≥ 1 → verified(태그 없음), 아니면 estimated → 엔진이 "추정"/"추정 · 출처 미기재"
  태그를 그린다(08 §9, 문구는 엔진 규칙 그대로).
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from bundle.charts import norm_gantt
from bundle.entities import BundleEntity, EntityJoin
from engine.direction import Direction
from engine.events import PanelGantt
from engine.entities import EntityRegistry
from engine.framing import frame_points, marker_point
from engine.registry import RegistryError, resolve
from rules import load_rules
from schemas.models import BundleChart, ReportBundle

MATERIALS_FILE = "bundle_materials.json"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlaceMat(_Strict):
    id: str
    name: str
    lon: float
    lat: float
    highlight: bool = False
    kind: str = ""                                      # 번들 마커 종류(military·chokepoint …, D-0064 선언 필드)
    value: str = ""                                     # 마커 값 표기(예: "8월 25일 회담")
    label_side: str = ""                                # 보고서 라벨 방향 — 참고용(배치는 엔진 placement)
    scenes: list[str] = Field(default_factory=list)    # 이 장소를 부르는 초안 장면


class PathMat(_Strict):
    id: str
    from_id: str
    to_id: str
    label: str = ""
    kind: str = ""                                      # flow(이동 경로 — route 후보) | tension(긴장선), 12 §2
    weight: Optional[float] = None
    label_t: Optional[float] = None
    points: list[tuple[float, float]]


class PanelMat(_Strict):
    chart_id: str
    chart_type: str
    kind: str                                           # 패널 kind(rules bundle.chart_panels)
    scene: Optional[str] = None                         # 차트를 참조한 섹션이 들어간 초안 장면
    data: dict[str, Any]                                # 패널 이벤트 내용(type·kind·시각 제외) — 엔진 모델 통과 확인됨
    prov_tag: Optional[str] = None                      # 엔진이 그릴 추정 태그 문구(08 §9). None = 태그 없음
    notes: list[str] = Field(default_factory=list)      # 변환 중 뺀 노드·선 등(조용히 버리지 않음)


class Unsupported(_Strict):
    chart_id: str
    chart_type: str
    reason: str


class MediaMat(_Strict):
    image_id: str
    url: str
    caption: str = ""
    credit: str = ""
    license: str = ""
    rights_status: str
    usable: bool                                        # rights_status == cleared 만(G4-8·C9)
    scenes: list[str] = Field(default_factory=list)


class BadgeMat(_Strict):
    id: str                                             # 번들 노드·마커 id
    entity_id: str                                      # 조인된 레지스트리 id(뱃지는 레지스트리 엔티티만, 08 §3.1)
    label: str
    scenes: list[str] = Field(default_factory=list)


class VersusMat(_Strict):
    """논쟁 한 건(contradictions) — versus 패널 재료. 양측 같은 무게(G4). 출처(src)는 claims 뒤 연출가가 채운다."""

    label_a: str
    label_b: str
    line_a: str
    line_b: str
    side_a: str
    side_b: str


class QuoteMat(_Strict):
    scene: str
    section: str
    text: str


class BundleMaterials(_Strict):
    schema_version: Literal[1] = 1
    bundle_id: str
    places: list[PlaceMat] = Field(default_factory=list)
    paths: list[PathMat] = Field(default_factory=list)
    panels: list[PanelMat] = Field(default_factory=list)
    unsupported: list[Unsupported] = Field(default_factory=list)
    media: list[MediaMat] = Field(default_factory=list)
    badges: list[BadgeMat] = Field(default_factory=list)
    unmatched: list[str] = Field(default_factory=list)
    quotes: list[QuoteMat] = Field(default_factory=list)
    versus: list[VersusMat] = Field(default_factory=list)


# ------------------------------------------------------------------ 차트 → 패널 데이터
def _prov(c: BundleChart) -> dict[str, Any]:
    B = load_rules().bundle  # noqa: N806
    srcs = [" ".join(x for x in (s.provider, s.code) if x) or s.source_id or s.url for s in c.provenance.sources]
    srcs = [s for s in srcs if s]
    ok = c.provenance.verification == B.verified_when and bool(srcs)
    return {"verification": "verified" if ok else "estimated", "sources": srcs}


def _badge(n: dict, e: Optional[BundleEntity], reg: EntityRegistry) -> tuple[Optional[dict], Optional[str]]:
    """노드 → network 노드 뱃지. 레지스트리 인물(초상)·기관 휘장·국기만(08 §3.1 문자 원 금지). 없으면 (None, 사유)."""
    base = {"id": str(n["id"]), "label": str(n.get("label") or n["id"])}
    if n.get("role"):
        base["role"] = str(n["role"])
    ent = reg.entities.get(e.entity_id) if e and e.entity_id else None
    flag = (ent.flag if ent is not None else None) or (e.flag if e else None)
    if ent is not None and ent.kind == "person" and (ent.portrait or ent.library) and flag:
        return base | {"kind": "person", "pid": ent.id, "flag": flag}, None
    if ent is not None and ent.kind == "org" and ent.emblem:
        return base | {"kind": "emblem", "img": ent.emblem}, None
    if flag:
        return base | {"kind": "flag", "flag": flag}, None
    return None, f"노드 {base['id']}({base['label']}): 레지스트리 뱃지·국기 없음 — 뺌(문자 원 금지, 08 §3.1)"


def _network(c: BundleChart, join: EntityJoin, reg: EntityRegistry) -> tuple[dict, list[str]]:
    B = load_rules().bundle  # noqa: N806
    d = c.data if isinstance(c.data, dict) else {}
    ents = {e.id: e for e in join.entities if e.origin == "node"}
    nodes, notes = [], []
    for n in d.get("nodes", []):
        b, why = _badge(n, ents.get(str(n.get("id"))), reg)
        if b is None:
            notes.append(why or "")
            continue
        col = n.get("col") if n.get("col") in ("left", "center", "right") else "center"
        nodes.append(b | {"col": col, "accent": B.node_accent if n.get("accent") else "muted", "big": bool(n.get("accent"))})
    have = {x["id"]: x["col"] for x in nodes}
    edges = []
    for x in d.get("edges", []):
        s, t, ty = str(x.get("source")), str(x.get("target")), str(x.get("type", ""))
        if s not in have or t not in have:
            notes.append(f"선 {s}→{t}: 끝 노드가 빠져 뺌")
        elif have[s] == have[t]:
            notes.append(f"선 {s}→{t}: 같은 열({have[s]})끼리는 잇지 않는다(08 §3 규칙 3) — 뺌")
        elif ty not in B.edge_types:
            notes.append(f"선 {s}→{t}: 종류 {ty!r} 가 rules bundle.edge_types 에 없음 — 뺌")
        else:
            edges.append({"src": s, "dst": t, "type": B.edge_types[ty], "label": str(x.get("label", ""))})
    return {"nodes": nodes, "edges": edges}, notes


def _dots(c: BundleChart) -> tuple[dict, list[str]]:
    rows_, cols = load_rules().panels.charts.dots.grid
    cells = rows_ * cols
    rows = c.data if isinstance(c.data, list) else []
    vals = [r.get("value") for r in rows if isinstance(r, dict)]
    if not rows or not all(isinstance(v, (int, float)) for v in vals) or not math.isclose(sum(vals), cells):
        raise ValueError(f"dot_matrix 값의 합이 {cells} 이 아니다({cells}칸 패널로 옮길 수 없음)")
    hi = next((r for r in rows if r.get("accent")), rows[0])
    rest = [r for r in rows if r is not hi]
    v = hi["value"]
    return {"highlight": int(round(v)), "big": f"{v:g}", "unit": "%", "caption": str(hi.get("label", "")),
            "detail": " · ".join(f"{r['value']:g}% — {r.get('label', '')}" for r in rest)}, []


def _gantt(c: BundleChart, today: Optional[str]) -> tuple[dict, list[str]]:
    B = load_rules().bundle  # noqa: N806
    g = norm_gantt({"data": c.data}, today)
    if g is None:
        raise ValueError("gantt 날짜가 YYYY-MM(-DD) 가 아니다")
    tasks = g["tasks"]
    cap = next(m.max_length for m in PanelGantt.model_fields["tasks"].metadata if hasattr(m, "max_length"))
    notes = [f"작업 {t['label']!r}: 패널 최대 {cap}개 — 뺌" for t in tasks[cap:]]
    raw = c.data if isinstance(c.data, list) else []
    tasks = [{"label": t["label"], "note": str(raw[i].get("note", "")) if i < len(raw) else "", "start": t["start"],
              "end": t["end"], "col": B.gantt_colors[i % len(B.gantt_colors)]} for i, t in enumerate(tasks[:cap])]
    y0 = min(date.fromisoformat(t["start"]).year for t in tasks)
    y1 = max(date.fromisoformat(t["end"]).year for t in tasks) + 1
    out: dict[str, Any] = {"axis_start": date(y0, 1, 1).isoformat(), "axis_end": date(y1, 1, 1).isoformat(), "tasks": tasks}
    if today:
        d = date.fromisoformat(today)
        out["today"] = {"date": today, "label": f"발행일 {d.month}.{d.day}"}
    return out, notes


def _nice_step(span: float) -> float:
    B = load_rules().bundle  # noqa: N806
    raw = span / B.dual_line_ticks if span > 0 else 1.0
    mag = 10 ** math.floor(math.log10(raw))
    return next(m * mag for m in B.nice_mantissas if m * mag >= raw)


def _dual(c: BundleChart) -> tuple[dict, list[str]]:
    B = load_rules().bundle  # noqa: N806
    d = c.data if isinstance(c.data, dict) else {}
    sides = [d[k] for k in ("left", "right") if isinstance(d.get(k), dict)]
    if not sides:
        raise ValueError("dual_line 에 left/right 계열이 없다")
    xs = [str(p["x"]) for p in sides[0].get("series", [])]
    series, allv = [], []
    for i, s in enumerate(sides):
        pts = s.get("series", [])
        if [str(p["x"]) for p in pts] != xs:
            raise ValueError("dual_line 두 계열의 x 가 다르다")
        vals = [float(p["y"]) for p in pts]
        allv += vals
        series.append({"label": str(s.get("label", "")), "col": B.dual_line_colors[i], "values": vals})
    step = _nice_step(max(allv) - min(allv))
    lo, hi = math.floor(min(allv) / step) * step, math.ceil(max(allv) / step) * step
    unit = str(sides[0].get("unit", ""))
    return {"y_min": lo, "y_max": hi, "y_step": step, "x_labels": xs, "series": series,
            **({"subtitle": unit} if unit else {})}, []


def chart_panel(c: BundleChart, join: EntityJoin, reg: EntityRegistry, today: Optional[str]) -> PanelMat:
    """차트 하나 → 패널 재료. 엔진 이벤트 모델을 통과해야 한다(P4). 못 하면 ValueError(사유)."""
    from engine.panels.base import prov_tag_text  # noqa: PLC0415 — 태그 문구 SSOT 는 엔진

    kind = load_rules().bundle.chart_panels.get(c.type)
    if kind is None:
        raise ValueError(f"차트 종류 {c.type!r} 는 rules bundle.chart_panels 에 없다(패널 렌더러 없음)")
    body, notes = {"network": lambda: _network(c, join, reg), "dots": lambda: _dots(c),
                   "gantt": lambda: _gantt(c, today), "dual_line": lambda: _dual(c)}[kind]()
    prov = _prov(c)
    data = {"kind": kind, "title": c.title or c.chart_id, "provenance": prov} | body
    try:
        resolve({"type": "panel", "kind": kind}).model.model_validate({"type": "panel", "t0": 0.0, "t1": 1.0} | data)
    except (ValidationError, RegistryError) as ex:
        raise ValueError(f"패널 모델 불통과: {ex}") from ex
    return PanelMat(chart_id=c.chart_id, chart_type=c.type, kind=kind, data=data, prov_tag=prov_tag_text(prov), notes=notes)


# ------------------------------------------------------------------ 재료 조립
def build_materials(b: ReportBundle, join: EntityJoin, reg: EntityRegistry, scene_of: dict[str, str],
                    scene_mentions: dict[str, list[str]]) -> BundleMaterials:
    """scene_of: 섹션 id → 초안 장면 id. scene_mentions: 장면 id → 그 장면 문장이 부르는 엔티티·마커 id(폴백 탐지)."""
    today = b.generated_at.strftime("%Y-%m-%d") if b.generated_at else None
    by_ent: dict[str, list[str]] = {}
    for sc, ids in scene_mentions.items():
        for i in ids:
            if sc not in by_ent.setdefault(i, []):
                by_ent[i].append(sc)
    places = [PlaceMat(id=m.id, name=m.name or m.id, lon=m.lng, lat=m.lat, highlight=m.highlight, kind=m.kind, value=m.value,
                       label_side=m.label_side, scenes=by_ent.get(m.id, []))
              for m in (b.map.markers if b.map else [])]
    pos = {p.id: (p.lon, p.lat) for p in places}
    paths = [PathMat(id=f"{a.from_id}__{a.to_id}", from_id=a.from_id, to_id=a.to_id, label=a.label, kind=a.kind,
                     weight=a.weight, label_t=a.label_t, points=[pos[a.from_id], pos[a.to_id]])
             for a in (b.map.arcs if b.map else []) if a.from_id in pos and a.to_id in pos]
    chart_scene: dict[str, str] = {}
    for s in b.sections:
        for cid in s.chart_refs:
            chart_scene.setdefault(cid, scene_of.get(s.section_id, ""))
    panels, unsup = [], []
    for c in b.charts:
        try:
            p = chart_panel(c, join, reg, today)
        except ValueError as ex:
            unsup.append(Unsupported(chart_id=c.chart_id, chart_type=c.type, reason=str(ex)))
            continue
        panels.append(p.model_copy(update={"scene": chart_scene.get(c.chart_id) or None}))
    img_scene: dict[str, list[str]] = {}
    for s in b.sections:
        for iid in s.image_refs:
            img_scene.setdefault(iid, []).append(scene_of.get(s.section_id, ""))
    media = [MediaMat(image_id=i.image_id, url=i.url, caption=i.caption, credit=i.credit, license=i.license,
                      rights_status=i.rights_status, usable=i.rights_status == "cleared", scenes=img_scene.get(i.image_id, []))
             for i in b.images]
    badges = [BadgeMat(id=e.id, entity_id=e.entity_id, label=e.label, scenes=by_ent.get(e.id, []))
              for e in join.entities if e.entity_id and e.origin == "node"]
    quotes = [QuoteMat(scene=scene_of.get(s.section_id, ""), section=s.section_id, text=h)
              for s in b.sections if s.video for h in s.video.highlights]
    versus = [VersusMat(label_a=x.video.label_a, label_b=x.video.label_b, line_a=x.video.line_a, line_b=x.video.line_b,
                        side_a=x.side_a, side_b=x.side_b) if x.video else
              VersusMat(label_a="", label_b="", line_a="", line_b="", side_a=x.side_a, side_b=x.side_b)
              for x in b.contradictions]
    return BundleMaterials(bundle_id=b.report.report_id, places=places, paths=paths, panels=panels, unsupported=unsup,
                           media=media, badges=badges, unmatched=[u.id for u in join.unmatched], quotes=quotes, versus=versus)


def build_direction_draft(mat: BundleMaterials, scenes: list[str]) -> Direction:
    """places·paths·패널만 담은 연출 초안. 숏 = 장면별 장소를 frame_points 로 담은 컷(제안). 장소 없는 장면은 숏 없음."""
    places = {p.id: (p.lon, p.lat) for p in mat.places}
    shots: list[dict[str, Any]] = []
    for sc in scenes:
        pts = [marker_point(p.lon, p.lat, p.id) for p in mat.places if sc in p.scenes]
        if not pts:
            continue
        fr = frame_points(pts)
        shots.append({"at": {"scene_start": sc}, "mode": "cut" if not shots else "move", "scene": sc,
                      "camera": {"lon": fr.lon, "lat": fr.lat, "w": fr.w}})
    if not shots and mat.places:
        fr = frame_points([marker_point(p.lon, p.lat, p.id) for p in mat.places])
        shots.append({"at": {"scene_start": scenes[0]}, "mode": "cut", "scene": scenes[0],
                      "camera": {"lon": fr.lon, "lat": fr.lat, "w": fr.w}})
    if not shots:
        raise ValueError(f"번들 {mat.bundle_id}: 지도 마커가 없어 숏 제안을 만들 수 없다 — 연출은 DirectorWorker 가 처음부터 짠다")
    events = [{"type": "panel", "start": {"scene_start": p.scene}, "end": {"scene_end": p.scene},
               "data": {k: v for k, v in p.data.items()}} for p in mat.panels if p.scene]
    return Direction(places=places, paths={p.id: p.points for p in mat.paths}, shots=shots, events=events)


def dump_direction_draft(d: Direction, mat: BundleMaterials) -> str:
    head = [f"# 연출 초안 — {mat.bundle_id} (bundle.to_direction). 제안·재료일 뿐이다: 최종 direction.yaml 은 DirectorWorker 가 쓴다(15 P8).",
            f"# 장소 {len(mat.places)} · 경로 {len(mat.paths)} · 패널 {len(mat.panels)} · 패널 없는 차트 {len(mat.unsupported)} · 숏 = 장면별 frame_points 제안"]
    body = yaml.safe_dump(d.model_dump(mode="json", exclude_none=True, by_alias=True), allow_unicode=True, sort_keys=False, width=1000)
    return "\n".join(head) + "\n" + body


__all__ = ["BundleMaterials", "MATERIALS_FILE", "PanelMat", "build_direction_draft", "build_materials", "chart_panel",
           "dump_direction_draft"]
