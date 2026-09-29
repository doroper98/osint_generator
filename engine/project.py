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
from engine.direction import Direction, DirectionError, load_direction_doc, shot_stages
from engine.direction import build as build_direction
from engine.entities import check_event_refs, load_entities
from engine.panels import network, relation, timeline
from engine.credits import RightsError
from engine.layers.media import caption_width, validate_media
from engine.media_registry import credit_line
from engine.media_plan import density_report, media_box, placement_warnings
from engine.placement import PlacementError, resolve_places
from engine.projection import View
from engine.shots import ShotStage
from engine.stage import StageSet, attach_world, make_stage
from engine.refs import emblem_ids
from engine.registry import RegistryError, validate_events
from engine.style import FPS, Output, output_profile
from engine.timebase import Timebase
from genres.elements import used_elements
from script.schema import Plan


class ProjectError(RuntimeError):
    pass


def read_direction(proj: Path, doc: Optional[Direction] = None) -> Direction:
    """direction.yaml → Direction(doc 을 주면 그대로). 없거나 틀리면 ProjectError."""
    if doc is not None:
        return doc
    p = proj / "direction.yaml"
    if not p.exists():
        raise ProjectError(f"연출 파일 없음: {p}")
    try:
        return load_direction_doc(p)
    except DirectionError as ex:
        raise ProjectError(str(ex)) from ex


def load_direction(proj: Path, tb: Timebase, stage: object = None, doc: Optional[Direction] = None) -> tuple[list[CamKey], list[dict], Optional[dict]]:
    """`direction.yaml`(17 §2) → (카메라 키, 이벤트, sound). 코드를 실행하지 않는다(v3.1.0, D-0047 §0-1 — 옛 direction.py 삭제).
    doc 을 주면 파일 대신 그 연출(아직 저장 전인 LLM 출력)을 같은 경로로 읽는다.
    stage 없이 부르는 곳(오디오 믹스·도구 — 시각·sound 만 읽는다)은 연출의 주 무대를 자산 없이(좌표 변환만) 만든다."""
    d = read_direction(proj, doc)
    try:
        return build_direction(d, tb, stage if stage is not None
                               else make_stage(d.main_stage(), config=d.stage_settings(d.main_stage())))  # type: ignore[arg-type]
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
    shots: list[ShotStage] = field(default_factory=list)   # v4.1.0 D-0077 — 숏별 무대·전환·월드 카메라(checks stage_continuity)


def _media_extent(e: dict, w: float, media_assets: dict) -> tuple[float, float]:
    """폭 w 일 때 미디어 상자 (높이, 글자까지 포함한 폭) — 패널 옆 슬롯(engine.placement beside_panel)용."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    m = media_assets[e["mid"]]
    return media_box(dict(e, x=0, y=0, w=w), media_assets)[3], max(w, caption_width(ctx, m.caption, credit_line(m)))


def sentence_labels(proj: Path) -> dict[str, str]:
    """문장 id → 화면 검증 라벨 문구(claims.json status → 규칙 표). 라벨 없는 문장은 빠진다. claims 가 없으면 {}."""
    import yaml  # noqa: PLC0415

    from script.labels import LabelError, check_project_labels  # noqa: PLC0415
    from script.schema import Script  # noqa: PLC0415

    sp = proj / "script.yaml"
    if not sp.exists():
        return {}
    try:
        labels = check_project_labels(proj, Script.model_validate(yaml.safe_load(sp.read_text(encoding="utf-8"))))
    except LabelError as ex:
        raise ProjectError(f"검증 라벨 계산 실패: {ex}") from ex
    return {} if labels is None else {sid: sl.label for sid, sl in labels.labels.items() if sl.label}


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


def _check_quotes(proj: Path, events: list[dict]) -> None:
    """statement_diff 문구 원문 대조(v4.4.0 D-0090 작업 4). 주문(order.yaml)이 있는 프로젝트는 before·after 가 각각 intake 본문
    (intake/bodies/<소스 id>.txt) 어딘가의 연속 부분 문자열이어야 한다(공백 정규화) — 연출이 성명 문구를 지어내지 못하게(C0 정확성).
    주문 없는 프로젝트(갤러리·스케치 예시 문구)는 대상 아님."""
    diffs = [e for e in events if e["type"] == "primitive" and e.get("id") == "statement_diff"]
    if not diffs or not (proj / "order.yaml").exists():
        return
    norm = lambda t: " ".join(t.replace("\u2011", "-").split())  # noqa: E731 — 비분리 하이픈(연준 성명)도 보통 하이픈으로
    bodies = [norm(p.read_text(encoding="utf-8")) for p in sorted((proj / "intake" / "bodies").glob("*.txt"))]
    errs = [f"statement_diff {k} 문구가 intake 본문에 없다: {norm(e[k])[:60]!r}" for e in diffs for k in ("before", "after")
            if not any(norm(e[k]) in b for b in bodies)]
    if errs:
        raise ProjectError("원문 대조 실패(20 §5, C0):\n" + "\n".join(errs))


def music_ids(sound: Optional[dict]) -> set[str]:
    """연출 sound.bgm 이 쓰는 BGM 레지스트리 id(v3.4.0 D-0060 작업 2·5 — 문자열 또는 곡 교체 목록). sound 가 없으면 빈 집합."""
    b = (sound or {}).get("bgm")
    if not b:
        return set()
    return {b} if isinstance(b, str) else {g["id"] for g in b}


def load_project(proj: Path, direction: Optional[Direction] = None, out: Optional[Output] = None) -> Project:
    """렌더 입력 한 벌. direction 을 주면 direction.yaml 대신 그것으로(연출 워커의 저장 전 점검 — 렌더와 같은 경로, 15 P8).
    out = 출력 프로파일(v3.6.0, None = config engine.output.default). 설계 좌표·연출·검사는 프로파일과 무관하다."""
    proj = proj.resolve()
    plan = load_plan(proj)
    tb = Timebase(plan)
    out = out or output_profile()
    doc = read_direction(proj, direction)
    uses_map = "mercator" in {doc.main_stage(), *(doc.shot_stage(s) for s in doc.shots)}   # v4.3.0 — 지도 자산은 지도 무대에만
    assets = Assets(proj, load_labels(proj / "labels.yaml"), None if out == output_profile() else out.name, geo=uses_map)
    R = RenderCtx(assets=assets, tb=tb, credits=load_credits(proj / "credits.yaml"), out=out)  # noqa: N806
    try:
        stages = StageSet(assets, out, doc.stage_configs())   # v4.1.0 D-0076·D-0077 — 무대는 이름마다 한 번만. 설정 v4.3.0
        R.stage = stages.get(doc.main_stage())
    except ValueError as ex:
        raise ProjectError(f"무대 설정 오류: {ex}") from ex
    keys, raw_events, sound = load_direction(proj, tb, R.stage, doc)
    try:
        shots = shot_stages(doc, tb, stages.get)
    except (DirectionError, ValueError) as ex:
        raise ProjectError(str(ex)) from ex
    R.cache["stage"] = {"name": R.stage.name, "declared": doc.stage is not None,          # provenance stage(15 P5)
                        "shots_declared": sum(1 for s in doc.shots if s.stage is not None), "instances": dict(stages.created),
                        "configs": {k: json.loads(json.dumps(v, default=str)) for k, v in doc.stage_configs().items()}}   # v4.3.0
    R.cache["genre"] = {"name": doc.genre_name(), "declared": doc.genre is not None,    # v4.2.0 D-0081 작업 3 — provenance genre(15 P5)
                        "status": doc.genre_profile().status,                          # v4.3.0 D-0084 작업 6 — proposed 프로필 사용 기록(P6)
                        "elements_used": used_elements(doc.events)}                   # checks genre_elements 입력(연출이 쓴 요소)
    n = int(plan.total * FPS)
    cams = build_camera(keys, n, FPS) if keys else None
    A0 = assets  # noqa: N806

    def view_at(t: float) -> View:
        assert cams is not None
        return View(R.stage, cams[min(n - 1, max(0, int(t * FPS)))])

    try:   # 17 §2 배치 슬롯 + 14 §10.3-5 기본 배치(D-0047 작업 5) — 좌표는 코드가 계산
        placement = resolve_places(raw_events, view_at, lambda e, w: _media_extent(e, w, A0.media_assets))
    except PlacementError as ex:
        raise ProjectError(str(ex)) from ex
    bad = [k for e in raw_events if e.get("type") == "series" for k in ("key", "axis", "slot") if k in e]
    if bad:
        raise ProjectError(f"series 이벤트의 {sorted(set(bad))} 는 코드가 채운다 — 연출에 쓰지 않는다(P8)")
    events = validate_events(raw_events)
    try:
        attach_world(events, R.stage)
    except ValueError as ex:   # 앵커 키가 무대와 다름(지도 핀을 시간축에, 등) = 오류(P10, D-0085)
        raise ProjectError(f"앵커 오류: {ex}") from ex   # 앵커(lon·lat) → 월드 좌표. 레이어·검사기는 이 값과 View 만 쓴다(D-0076 작업 3)
    _check_quotes(proj, events)      # v4.4.0 — statement_diff 문구 = intake 원문(D-0090 작업 4)
    _attach_posts(proj, R, events)   # v3.2.0 18 §5 — post 카드 문구·상자는 intake/sources.json 에서(없으면 오류)
    ent_errs = check_event_refs(events, load_entities())  # 07 §6 — 미등재 인물·국기·휘장은 렌더 전 오류(P10)
    if ent_errs:
        raise RegistryError("엔티티 레지스트리 점검 실패:\n" + "\n".join(ent_errs))
    errs = preflight(R, events)
    if errs:
        raise ProjectError("렌더 전 점검 실패:\n" + "\n".join(errs))
    A = R.assets  # noqa: N806
    req = required_refs(events, A.rights, A.emblem_flag, set(A.img), music_ids=music_ids(sound), uses_map=uses_map)
    from data.series import load_series  # noqa: PLC0415

    from engine.layers.series import record_ids  # noqa: PLC0415

    series_ids = list(dict.fromkeys(sid for e in events if e["type"] == "series" for sid in record_ids(e)))   # band = 두 레코드(v4.4.0)
    R.cache["series_records"] = [load_series(s) for s in series_ids]   # v4.3.0 — 엔딩 카드 auto: series(레코드 출처·라이선스·기준 시점)
    R.cache["sentence_labels"] = sentence_labels(proj)       # v3.3.0 NB12 — 자막 검증 라벨(C9)
    R.cache["cited_sources"] = cited_sources(proj, events)   # v3.2.0 18 §6 — 엔딩 카드 '보도 · 자료'·설명란 원문 링크
    check_credits(R.credits, A.rights, A.media, req,          # D-0029 작업 7 — 누락·미확인·미표기 자산은 RightsError
                  cited_ids={s.id for s in R.cache["cited_sources"]}, series_ids=set(series_ids))
    R.cache["credit_refs"] = req
    b = (sound or {}).get("bgm")
    R.cache["bgm_segments"] = 0 if not b else (1 if isinstance(b, str) else len(b))   # provenance audio.crossfades
    R.cache["media_placement"] = placement
    if not keys or cams is None:
        raise ProjectError("카메라 키가 없다")
    prepare_series(R, events, cams, n)   # v4.3.0 D-0084 작업 4 — 레코드 로드·레인 범위·grow 앞끝(카메라 경로)
    warns = lint_events(events) + placement_warnings(events, A.media_assets) \
        + density_report(events, tb, plan.total)["warnings"]
    return Project(proj, plan, R, keys, events, cams, n, warns, shots)


def prepare_series(R: RenderCtx, events: list[dict], cams: np.ndarray, n: int) -> None:  # noqa: N803
    """series 이벤트 준비(v4.3.0 D-0084 작업 4). 시간축 무대만 · 레코드 로드 실패 = 오류(P6) · 레인 kind step|line 만.
    key(이벤트 순번)·axis(레인의 첫 series 만 축 라벨)·slot(레인 안 순번 — 출처 줄 위치), 레인 값 범위, grow 앞끝(프레임별 누적 최대)."""
    from data.series import SeriesError, load_series  # noqa: PLC0415
    from engine.layers.series import band_pairs, lane_range, record_ids  # noqa: PLC0415
    from engine.style import TIMELINE  # noqa: PLC0415
    from engine.timebase import ease_out  # noqa: PLC0415

    ser = [e for e in events if e["type"] == "series"]
    R.cache["series_range"], R.cache["series_front"] = {}, {}
    if not ser:
        return
    st = R.stage
    if st.name != "timeline":
        raise ProjectError(f"series 이벤트는 시간축 무대 전용 — 주 무대 {st.name!r}")
    slots: dict[str, int] = {}
    for i, e in enumerate(ser):
        try:
            for sid in record_ids(e):
                load_series(sid)
            if e["style"] == "band":
                band_pairs(e)   # 두 레코드 날짜 일치·위 ≥ 아래(v4.4.0) — 어긋나면 렌더 전 오류(P6)
            kind = st.lanes[st.lane_index(e["lane"])].kind  # type: ignore[attr-defined]
        except (SeriesError, ValueError) as ex:
            raise ProjectError(f"series {e['series_id']} @ {e['lane']}: {ex}") from ex
        if kind == "pins":
            raise ProjectError(f"series {e['series_id']}: 레인 {e['lane']!r} 은 pins(핀 = marker) — step|line 레인에만")
        e["key"], e["slot"] = i, slots.get(e["lane"], 0)
        e["axis"] = e["slot"] == 0
        slots[e["lane"]] = e["slot"] + 1
    for lane in slots:
        R.cache["series_range"][lane] = lane_range(events, lane)
    S = TIMELINE.series  # noqa: N806
    for e in ser:
        if not e["grow"]:
            continue
        i0, i1 = int(e["t0"] * FPS), min(n, int(e["t1"] * FPS) + 1)
        front = np.full(n, -np.inf)
        best = -np.inf
        for i in range(i0, i1):
            v = View(st, cams[i])
            sweep = ease_out((i / FPS - e["t0"]) / S.grow_in_sec)
            rest = st.bounds[2] - (v.x0 + v.w)   # 화면 오른쪽 끝 너머 남은 무대 — 끝에 닿으면 앞끝도 화면 끝(= 전부 드러남)
            ph = S.playhead + (1 - S.playhead) * min(1.0, max(0.0, 1 - rest / (v.w * (1 - S.playhead))))
            best = max(best, v.x0 + v.w * ph * sweep)
            front[i] = best
        front[i1:] = best
        R.cache["series_front"][e["key"]] = front


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
