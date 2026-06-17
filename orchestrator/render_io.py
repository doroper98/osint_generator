"""scene_manifest + full_script → render_props.json (수직 슬라이스 V3, v0.11.0).

Remotion 최소 렌더(텍스트 슬라이드)의 입력 props 를 만든다. scene_manifest 는 타이밍·
라벨 신호를, full_script 는 나레이션·캡션 본문을 갖고 있으므로 둘을 해석(join)해
평면 RenderProps 로 만든다.

`build_render_props` 는 순수 함수(I/O 없음), 본 모듈의 나머지는 I/O 경계 (로딩·영속화).
정식 RemotionJob/render_worker(Phase 9) 는 추후 — 본 모듈은 슬라이스용 최소 구현.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.scene_io import load_scene_manifest
from orchestrator.script_io import load_full_script
from schemas.models import (
    AudioManifest,
    FullScript,
    RenderChart,
    RenderMap,
    RenderMapArc,
    RenderMapMarker,
    RenderProps,
    RenderSceneProps,
    ReportBundle,
    ResearchDossier,
    SceneManifest,
    SourceEntry,
    SourceRegistry,
    SubtitleCue,
)

# 영상용 family 렌더러가 있는(=cinematic 재렌더 가능한) 차트 타입 (Remotion ChartView 와 동기).
# 영상미 최우선(C0): 전 타입을 우리가 데이터로 재렌더. 미지원 타입만 텍스트 폴백.
SUPPORTED_CHART_TYPES = {
    "line", "area", "stacked_area", "small_multiples", "dual_line", "forecast",
    "bar", "lollipop", "range_bar", "stacked", "stacked_bar", "waterfall",
    "scatter", "bubble", "candle", "donut", "gantt", "slope", "heatmap",
    "network", "sankey", "choropleth", "table",
}


def _bundle_map_to_render_map(bm) -> RenderMap:
    """bundle.map (BundleMap) → RenderMap (TS 친화 필드명 변환)."""
    return RenderMap(
        center=list(bm.center),
        zoom=bm.zoom,
        markers=[
            RenderMapMarker(
                id=m.id, name=m.name, lng=m.lng, lat=m.lat, highlight=m.highlight
            )
            for m in bm.markers
        ],
        arcs=[
            RenderMapArc(
                fromId=a.from_id, toId=a.to_id, label=a.label, highlight=a.highlight
            )
            for a in bm.arcs
        ],
    )

# 화면 상단 출처 표기에 노출할 최대 출처 수.
_SCENE_SOURCE_MAX = 3


def _source_display_name(entry: SourceEntry) -> str:
    """SourceEntry → 화면 표기명 (publisher/provider 우선, 없으면 도메인/title)."""
    if entry.platform and entry.platform not in ("data", "source"):
        return entry.platform
    if entry.original_url:
        dom = re.sub(r"^https?://(www\.)?", "", entry.original_url).split("/")[0]
        if dom:
            return dom
    if entry.title:
        return entry.title
    return entry.platform or entry.source_id


def _scene_source_citation(
    segs: list,
    claims_by_id: dict,
    registry_by_id: dict,
) -> str:
    """scene 의 segment claim_refs → dossier claim → evidence.source_id → registry 표기명.

    해소 가능한 출처가 없으면 "" (자막바 위 출처 줄을 숨김). v5.5.0 은 claim-출처 연결이
    sparse 하므로(차트 데이터 출처 위주) 해소되는 scene 에서만 표기한다(과잉 귀속 방지).
    """
    names: list[str] = []
    seen: set[str] = set()
    for seg in segs:
        for cid in seg.claim_refs:
            claim = claims_by_id.get(cid)
            if claim is None:
                continue
            for ev in claim.evidence:
                sid = ev.source_id
                if not sid or sid in seen:
                    continue
                entry = registry_by_id.get(sid)
                if entry is None:
                    continue
                seen.add(sid)
                names.append(_source_display_name(entry))
    return ", ".join(names[:_SCENE_SOURCE_MAX])


# 자막 한 줄(큐) 최대 글자 수. 한 화면 자막은 통문단이 아니라 1~2줄이어야 한다.
_SUBTITLE_CUE_MAX_CHARS = 42


def split_subtitle_cues(narration: str, total_sec: float) -> list[SubtitleCue]:
    """narration 을 줄 단위 큐로 쪼개고 scene 길이를 글자수 비례로 배분한다.

    TTS 가 문장별 타임스탬프를 주지 않으므로 글자수 비례로 추정 타이밍을 만든다
    (자동 자막의 표준 근사). 문장(종결부호) 단위로 먼저 나누고, 너무 긴 문장은
    공백 경계에서 한 줄 길이로 다시 쪼갠다.
    """
    text = narration.strip()
    if not text or total_sec <= 0:
        return []

    # 1) 문장 분할 — 종결부호(. ? ! 。) 뒤 공백에서.
    sentences = [s for s in re.split(r"(?<=[.?!。])\s+", text) if s.strip()]

    # 2) 긴 문장은 한 줄 길이로 재분할 (공백 경계 우선).
    chunks: list[str] = []
    for sent in sentences:
        s = sent.strip()
        while len(s) > _SUBTITLE_CUE_MAX_CHARS:
            cut = s.rfind(" ", 0, _SUBTITLE_CUE_MAX_CHARS)
            if cut <= 0:
                cut = _SUBTITLE_CUE_MAX_CHARS
            chunks.append(s[:cut].strip())
            s = s[cut:].strip()
        if s:
            chunks.append(s)

    if not chunks:
        return []

    # 3) 글자수 비례 타이밍 배분 (scene 시작 기준 상대).
    total_chars = sum(len(c) for c in chunks)
    cues: list[SubtitleCue] = []
    cursor = 0.0
    for i, c in enumerate(chunks):
        if i == len(chunks) - 1:
            dur = max(0.0, total_sec - cursor)  # 마지막 큐는 끝까지 (반올림 오차 흡수).
        else:
            dur = total_sec * (len(c) / total_chars)
        cues.append(
            SubtitleCue(text=c, startSec=round(cursor, 3), durationSec=round(dur, 3))
        )
        cursor += dur
    return cues


RENDER_DIRNAME = "09_render"
RENDER_PROPS_FILENAME = "render_props.json"
DRAFT_DEBUG_FILENAME = "draft_debug.mp4"


def render_dir(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    """`projects/{pid}/09_render/` 디렉토리."""
    return project_dir(project_id, cfg) / RENDER_DIRNAME


def render_props_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    return render_dir(project_id, cfg) / RENDER_PROPS_FILENAME


def draft_debug_path(project_id: str, cfg: Optional[AppConfig] = None) -> Path:
    return render_dir(project_id, cfg) / DRAFT_DEBUG_FILENAME


def build_render_props(
    scene_manifest: SceneManifest,
    script: FullScript,
    *,
    audio_manifest: Optional[AudioManifest] = None,
    research_dossier: Optional[ResearchDossier] = None,
    source_registry: Optional[SourceRegistry] = None,
    report_bundle: Optional[ReportBundle] = None,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> RenderProps:
    """scene_manifest + full_script (+ audio_manifest) 를 합쳐 RenderProps 생성 (순수 함수).

    각 scene 의 narration_segment_ids 로 full_script 세그먼트를 찾아 나레이션을
    이어붙이고, 세그먼트의 label 을 표기 라벨로 쓴다.

    audio_manifest 가 주어지면 (V4b): scene 길이를 **실제 음성 길이**로 교체하고
    start_sec 를 음성 길이로 재누적하며, scene 의 wav 경로를 audioPath 로 단다 (오디오
    트랙 + 슬라이드 길이 동기화). 없으면 scene_manifest 의 (추정) 타이밍을 그대로 쓰고
    audioPath 는 None (무음 — 하위호환).
    """
    seg_by_id = {s.segment_id: s for s in script.segments}
    audio_by_seg = (
        {a.segment_id: a for a in audio_manifest.segments} if audio_manifest else {}
    )
    claims_by_id = (
        {c.claim_id: c for c in research_dossier.claims} if research_dossier else {}
    )
    registry_by_id = (
        {e.source_id: e for e in source_registry.sources} if source_registry else {}
    )
    # 지도 비주얼: bundle map 을 claim_refs 로 해당 scene 에 붙인다(비주얼↔scene 연결은
    # claim_refs 로 보존됨 — 차트/지도를 claim 으로 합성한 결과).
    bundle_map = (
        report_bundle.map
        if (report_bundle is not None and report_bundle.map is not None)
        else None
    )
    map_id = bundle_map.id if bundle_map is not None else None
    render_map = _bundle_map_to_render_map(bundle_map) if bundle_map is not None else None
    # 차트 비주얼: claim_refs 에 chart id 가 있고 지원 타입이면 그 scene 에 차트 attach.
    chart_by_id = (
        {c.chart_id: c for c in report_bundle.charts} if report_bundle is not None else {}
    )

    # 인용부호가 들어간 caption 은 인용(quote)으로 표기 (영상 문법 ③). 정식 인용 마킹
    # (ScriptSegment 필드 / bundle pull_quote)이 생기기 전의 휴리스틱.
    quote_marks = ("「", "」", "『", "』", "“", "”", '"')

    scenes: list[RenderSceneProps] = []
    cursor = 0.0
    for scene in scene_manifest.scenes:
        seg_ids = scene.narration_segment_ids
        segs = [seg_by_id[sid] for sid in seg_ids if sid in seg_by_id]
        narration = " ".join(s.narration for s in segs).strip()
        label = next((s.label for s in segs if s.label), None)
        is_quote = any(m in scene.caption for m in quote_marks)
        # 이 scene 의 segment claim_refs 에 map id 가 있으면 지도 attach.
        scene_claim_refs = [r for s in segs for r in s.claim_refs]
        scene_map = (
            render_map
            if (map_id is not None and map_id in set(scene_claim_refs))
            else None
        )
        # 첫 번째로 매칭되는 지원 타입 차트를 attach (claim_refs 순서 보존).
        scene_chart = None
        for cid in scene_claim_refs:
            ch = chart_by_id.get(cid)
            if ch is not None and ch.type in SUPPORTED_CHART_TYPES:
                unit = ch.provenance.sources[0].unit if ch.provenance.sources else ""
                scene_chart = RenderChart(
                    chartId=ch.chart_id, type=ch.type, title=ch.title,
                    data=ch.data, unit=unit,
                )
                break

        # 이 scene 에 대응하는 오디오 (세그먼트 전부가 audio_manifest 에 있을 때만 사용).
        audio_segs = [audio_by_seg[sid] for sid in seg_ids if sid in audio_by_seg]
        use_audio = bool(audio_segs) and len(audio_segs) == len(seg_ids)

        if use_audio:
            duration = round(sum(a.duration_sec for a in audio_segs), 3)
            start = round(cursor, 3)
            # 단일 세그먼트 scene(기본 빌더)이면 그 wav 경로. 다중이면 첫 트랙만(드묾).
            audio_path = audio_segs[0].audio_path
            cursor += duration
        else:
            duration = scene.duration_sec
            start = scene.start_sec
            audio_path = None

        scenes.append(
            RenderSceneProps(
                sceneId=scene.scene_id,
                startSec=start,
                durationSec=duration,
                caption=scene.caption,
                narration=narration,
                subtitleCues=split_subtitle_cues(narration, duration),
                label=label,
                sourceLinkRequired=scene.source_link_required,
                source=_scene_source_citation(segs, claims_by_id, registry_by_id),
                isQuote=is_quote,
                mapData=scene_map,
                chartData=scene_chart,
                audioPath=audio_path,
            )
        )

    return RenderProps(
        project_id=script.project_id,
        title=script.title or script.topic,
        fps=fps,
        width=width,
        height=height,
        scenes=scenes,
    )


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
    try:
        dir_fd = os.open(path.parent, getattr(os, "O_DIRECTORY", os.O_RDONLY))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass


def persist_render_props(
    project_id: str, props: RenderProps, cfg: Optional[AppConfig] = None
) -> Path:
    """RenderProps 를 `09_render/render_props.json` 으로 atomic 영속화."""
    cfg = cfg or load_config()
    path = render_props_path(project_id, cfg)
    _atomic_write_text(path, props.model_dump_json(indent=2))
    return path


def build_and_persist_render_props(
    project_id: str,
    *,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    cfg: Optional[AppConfig] = None,
) -> tuple[RenderProps, Path]:
    """scene_manifest + full_script 로딩 → build_render_props → 영속화.

    raises: FileNotFoundError (scene_manifest/full_script 없음) /
    json.JSONDecodeError / pydantic.ValidationError (손상).
    """
    cfg = cfg or load_config()
    scene_manifest = load_scene_manifest(project_id, cfg)
    script = load_full_script(project_id, cfg)
    # audio_manifest 가 있으면 실측 길이/오디오 트랙을 반영 (V4b). 없으면 무음.
    audio_manifest = None
    try:
        from orchestrator.audio_io import load_audio_manifest

        audio_manifest = load_audio_manifest(project_id, cfg)
    except FileNotFoundError:
        audio_manifest = None
    # 화면 상단 출처 표기용 (선택적 — 없으면 source 빈 문자열로 graceful).
    research_dossier = None
    try:
        from orchestrator.research_io import load_research_dossier

        research_dossier = load_research_dossier(project_id, cfg)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        research_dossier = None
    source_registry = None
    try:
        from orchestrator.source_registry_io import load_source_registry

        source_registry = load_source_registry(project_id, cfg)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        source_registry = None
    # 지도 지오데이터용 받은 bundle 사본 (외부 연동 경로에서만 존재).
    report_bundle = None
    try:
        from orchestrator.bundle_io import load_persisted_bundle

        report_bundle = load_persisted_bundle(project_id, cfg)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        report_bundle = None
    props = build_render_props(
        scene_manifest, script, audio_manifest=audio_manifest,
        research_dossier=research_dossier, source_registry=source_registry,
        report_bundle=report_bundle,
        fps=fps, width=width, height=height,
    )
    # forced-alignment(opt-in, OSINT_ALIGN_BACKEND): 음성이 있으면 자막 큐 타이밍을 실측으로
    # 정밀화. 백엔드 미설정/무음/실패면 비례 큐 유지(graceful). 본 클라우드는 기본 no-op.
    _maybe_align_subtitles(props, project_id, cfg)
    path = persist_render_props(project_id, props, cfg)
    return props, path


def _maybe_align_subtitles(props: RenderProps, project_id: str, cfg: AppConfig) -> None:
    from orchestrator.subtitle_align import align_cues, alignment_enabled

    if not alignment_enabled():
        return
    pdir = project_dir(project_id, cfg)
    for sc in props.scenes:
        if not sc.audioPath or not sc.subtitleCues:
            continue
        aligned = align_cues(sc.subtitleCues, pdir / sc.audioPath)
        if aligned:
            sc.subtitleCues = aligned


__all__ = [
    "render_dir",
    "render_props_path",
    "draft_debug_path",
    "split_subtitle_cues",
    "build_render_props",
    "persist_render_props",
    "build_and_persist_render_props",
]
