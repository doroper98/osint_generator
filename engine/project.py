"""프로젝트 로드 — plan·라벨·크레딧·자산·연출을 읽고 렌더 전 검사를 끝낸다 (v2.1.0).

프로젝트 폴더 구성(16 §4):
- 입력(추적): `script.yaml`, `direction.yaml`(v3.1.0 — 선언형, 코드 실행 없음), `labels.yaml`, `credits.yaml`
- 생성물(gitignore): `plan.json`, `tts/`, `assets/`, `media/`, `prev/`, `out/`
검사 실패(레지스트리·스키마·권리·자산)는 렌더 시작 전 오류다(15 P6·P10, C9).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cairo
import numpy as np

from engine.assets import Assets, load_labels
from engine.camera import CamKey, build_camera
from engine.context import RenderCtx
from engine.credits import check_credits, load_credits, required_refs
from engine.direction import Direction, DirectionError, load_direction_doc
from engine.direction import build as build_direction
from engine.entities import check_event_refs, load_entities
from engine.panels import network, relation, timeline
from engine.credits import RightsError
from engine.layers.media import caption_width, validate_media
from engine.media_registry import credit_line
from engine.media_plan import density_report, media_box, placement_warnings
from engine.placement import PlacementError, resolve_places
from engine.projection import View
from engine.refs import emblem_ids
from engine.registry import RegistryError, validate_events
from engine.style import FPS
from engine.timebase import Timebase
from script.schema import Plan


class ProjectError(RuntimeError):
    pass


def load_direction(proj: Path, tb: Timebase, doc: Optional[Direction] = None) -> tuple[list[CamKey], list[dict], Optional[dict]]:
    """`direction.yaml`(17 §2) → (카메라 키, 이벤트, sound). 코드를 실행하지 않는다(v3.1.0, D-0047 §0-1 — 옛 direction.py 삭제).
    doc 을 주면 파일 대신 그 연출(아직 저장 전인 LLM 출력)을 같은 경로로 읽는다."""
    p = proj / "direction.yaml"
    if doc is None and not p.exists():
        raise ProjectError(f"연출 파일 없음: {p}")
    try:
        return build_direction(doc if doc is not None else load_direction_doc(p), tb)
    except DirectionError as ex:
        raise ProjectError(str(ex)) from ex


def load_plan(proj: Path) -> Plan:
    p = proj / "plan.json"
    if not p.exists():
        raise ProjectError(f"plan.json 없음 — 먼저 `python -m script.plan {proj}`")
    return Plan.model_validate(json.loads(p.read_text(encoding="utf-8")))


def _walk(o: object):  # noqa: ANN202
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from _walk(v)


def preflight(R: RenderCtx, events: list[dict]) -> list[str]:  # noqa: N803
    """권리·자산 점검. 문제 목록을 돌려준다(빈 목록 = 통과)."""
    A = R.assets  # noqa: N806
    errs: list[str] = []
    keys: set[str] = set()
    for e in events:
        for d in _walk(e):
            if "pid" in d and d["pid"] is not None:
                keys |= {f"portrait:{d['pid']}", f"flag43:{d['flag']}"}
                if d["pid"] not in A.rights.get("people", {}):
                    errs.append(f"권리 레지스트리에 인물 없음: {d['pid']} ({e['type']} t0={e['t0']:.2f})")
            elif "flag" in d and d["flag"] is not None:
                keys.add(f"flag11:{d['flag']}")
        for img in emblem_ids(e):   # 뱃지·패널 노드 모두(engine/refs.py)
            try:
                fb = A.emblem_flag(img)   # D5 — 제한 휘장은 국기로(코드 결정)
            except Exception as ex:  # noqa: BLE001 — 모아서 한 번에 보고
                errs.append(str(ex))
                continue
            if fb is not None:
                keys.add(f"flag11:{fb}")
            else:
                keys.add(f"emblem:{img}")
                if img not in A.rights.get("emblems", {}):
                    errs.append(f"권리 레지스트리에 휘장 없음: {img}")
        if e["type"] in ("photo", "clip", "cutout", "article"):
            try:
                m = validate_media(e, A.media_assets)   # 권리 게이트(D-0036) — 참조·종류·권리 상태
            except RightsError as ex:
                errs.append(str(ex))
                continue
            if e["type"] in ("photo", "cutout"):
                keys.add(f"media:{m.file}")
    for k in sorted(keys):
        try:
            A.load_image(k)
        except Exception as ex:  # noqa: BLE001 — 모아서 한 번에 보고
            errs.append(str(ex))
    for e in events:
        if e["type"] == "clip" and e["mid"] in A.media_assets:
            try:
                A.load_clip(A.media_assets[e["mid"]].file)
            except Exception as ex:  # noqa: BLE001
                errs.append(str(ex))
    return errs


@dataclass
class Project:
    root: Path
    plan: Plan
    R: RenderCtx
    keys: list[CamKey]
    events: list[dict]
    cams: np.ndarray
    n_frames: int
    warnings: list[str] = field(default_factory=list)   # 연출 lint 경고(오류 아님) — StageResult.warnings 로 나간다


def _media_extent(e: dict, w: float, media_assets: dict) -> tuple[float, float]:
    """폭 w 일 때 미디어 상자 (높이, 글자까지 포함한 폭) — 패널 옆 슬롯(engine.placement beside_panel)용."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    m = media_assets[e["mid"]]
    return media_box(dict(e, x=0, y=0, w=w), media_assets)[3], max(w, caption_width(ctx, m.caption, credit_line(m)))


def cited_sources(proj: Path, events: list[dict]) -> list:
    """이번 영상이 인용한 소스 레코드(원고 문장 claim 의 소스 + post 카드), sources.json 순서. 소스 파일이 없으면 [](v3 전 프로젝트)."""
    import yaml  # noqa: PLC0415

    from schemas.source_models import ClaimsFile, SourcesFile  # noqa: PLC0415

    sp, cp, scp = proj / "intake" / "sources.json", proj / "intake" / "claims.json", proj / "script.yaml"
    if not sp.exists():
        return []
    sources = SourcesFile.model_validate_json(sp.read_text(encoding="utf-8"))
    ids: set[str] = {e["src"] for e in events if e["type"] == "post"}
    if cp.exists() and scp.exists():
        claims = ClaimsFile.model_validate_json(cp.read_text(encoding="utf-8")).by_id()
        script = yaml.safe_load(scp.read_text(encoding="utf-8"))
        for sc in script.get("scenes", []):
            for sent in sc.get("sentences", []):
                for cid in sent.get("sources") or []:
                    if cid in claims:
                        ids |= set(claims[cid].source_ids)
    return [s for s in sources.sources if s.id in ids]


def _attach_posts(proj: Path, R: RenderCtx, events: list[dict]) -> None:  # noqa: N803
    posts = [e for e in events if e["type"] == "post"]
    if not posts:
        return
    from engine.layers.post import PostSourceError, post_geom  # noqa: PLC0415
    from schemas.source_models import SourcesFile  # noqa: PLC0415

    sp = proj / "intake" / "sources.json"
    if not sp.exists():
        raise ProjectError("post 이벤트가 있는데 intake/sources.json 이 없다(18 §5)")
    R.cache["sources"] = SourcesFile.model_validate_json(sp.read_text(encoding="utf-8")).by_id()
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    errs: list[str] = []
    for e in posts:
        try:
            e["post_box"] = post_geom(ctx, e, R.cache["sources"])[:4]
        except PostSourceError as ex:
            errs.append(str(ex))
    if errs:
        raise ProjectError("post 카드 점검 실패:\n" + "\n".join(errs))


def load_project(proj: Path, direction: Optional[Direction] = None) -> Project:
    """렌더 입력 한 벌. direction 을 주면 direction.yaml 대신 그것으로(연출 워커의 저장 전 점검 — 렌더와 같은 경로, 15 P8)."""
    proj = proj.resolve()
    plan = load_plan(proj)
    tb = Timebase(plan)
    assets = Assets(proj, load_labels(proj / "labels.yaml"))
    R = RenderCtx(assets=assets, tb=tb, credits=load_credits(proj / "credits.yaml"))  # noqa: N806
    keys, raw_events, sound = load_direction(proj, tb, direction)
    n = int(plan.total * FPS)
    cams = build_camera(keys, n, FPS) if keys else None
    A0 = assets  # noqa: N806

    def view_at(t: float) -> View:
        assert cams is not None
        return View(cams[min(n - 1, max(0, int(t * FPS)))], A0.tiers, A0.base)

    try:   # 17 §2 배치 슬롯 + 14 §10.3-5 기본 배치(D-0047 작업 5) — 좌표는 코드가 계산
        placement = resolve_places(raw_events, view_at, lambda e, w: _media_extent(e, w, A0.media_assets))
    except PlacementError as ex:
        raise ProjectError(str(ex)) from ex
    events = validate_events(raw_events)
    _attach_posts(proj, R, events)   # v3.2.0 18 §5 — post 카드 문구·상자는 intake/sources.json 에서(없으면 오류)
    ent_errs = check_event_refs(events, load_entities())  # 07 §6 — 미등재 인물·국기·휘장은 렌더 전 오류(P10)
    if ent_errs:
        raise RegistryError("엔티티 레지스트리 점검 실패:\n" + "\n".join(ent_errs))
    errs = preflight(R, events)
    if errs:
        raise ProjectError("렌더 전 점검 실패:\n" + "\n".join(errs))
    A = R.assets  # noqa: N806
    req = required_refs(events, A.rights, A.emblem_flag, set(A.img), uses_music=sound is not None)
    R.cache["cited_sources"] = cited_sources(proj, events)   # v3.2.0 18 §6 — 엔딩 카드 '보도 · 자료'·설명란 원문 링크
    check_credits(R.credits, A.rights, A.media, req,          # D-0029 작업 7 — 누락·미확인·미표기 자산은 RightsError
                  cited_ids={s.id for s in R.cache["cited_sources"]})
    R.cache["credit_refs"] = req
    R.cache["media_placement"] = placement
    if not keys or cams is None:
        raise ProjectError("카메라 키가 없다")
    warns = lint_events(events) + placement_warnings(events, A.media_assets) \
        + density_report(events, tb, plan.total)["warnings"]
    return Project(proj, plan, R, keys, events, cams, n, warns)


def lint_events(events: list[dict]) -> list[str]:
    """연출 경고 — 관계선 과다(08 §3 규칙 6) 등. 분할 제안은 `engine.panels.relation.split_suggestion`(실행 안 함, P8).
    미디어 배치(예약 영역)·밀도(14 §10.1) 경고는 load_project 가 engine.media_plan 으로 덧붙인다."""
    out: list[str] = []
    for e in events:
        if e["type"] == "panel" and e["kind"] == "relation":
            out += relation.lint(e)
        if e["type"] == "panel" and e["kind"] == "timeline":
            out += timeline.lint(e)
        if e["type"] == "panel" and e["kind"] == "network":
            out += network.lint(e)
    return out
