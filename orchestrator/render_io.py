"""scene_manifest + full_script → render_props.json (수직 슬라이스 V3, v0.11.0).

Remotion 최소 렌더(텍스트 슬라이드)의 입력 props 를 만든다. scene_manifest 는 타이밍·
라벨 신호를, full_script 는 나레이션·캡션 본문을 갖고 있으므로 둘을 해석(join)해
평면 RenderProps 로 만든다.

`build_render_props` 는 순수 함수(I/O 없음), 본 모듈의 나머지는 I/O 경계 (로딩·영속화).
정식 RemotionJob/render_worker(Phase 9) 는 추후 — 본 모듈은 슬라이스용 최소 구현.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from orchestrator.config import AppConfig, load_config, project_dir
from orchestrator.scene_io import load_scene_manifest
from orchestrator.script_io import load_full_script
from schemas.models import FullScript, RenderProps, RenderSceneProps, SceneManifest


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
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> RenderProps:
    """scene_manifest + full_script 를 합쳐 RenderProps 생성 (순수 함수).

    각 scene 의 narration_segment_ids 로 full_script 세그먼트를 찾아 나레이션을
    이어붙이고, 세그먼트의 label 을 그대로 표기 라벨로 쓴다 (scene 의
    inference_label_required 와 정합).
    """
    seg_by_id = {s.segment_id: s for s in script.segments}

    scenes: list[RenderSceneProps] = []
    for scene in scene_manifest.scenes:
        segs = [seg_by_id[sid] for sid in scene.narration_segment_ids if sid in seg_by_id]
        narration = " ".join(s.narration for s in segs).strip()
        # 라벨: 세그먼트 중 라벨이 달린 첫 값 (없으면 None). 단일 세그먼트가 일반적.
        label = next((s.label for s in segs if s.label), None)
        scenes.append(
            RenderSceneProps(
                sceneId=scene.scene_id,
                startSec=scene.start_sec,
                durationSec=scene.duration_sec,
                caption=scene.caption,
                narration=narration,
                label=label,
                sourceLinkRequired=scene.source_link_required,
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
    props = build_render_props(
        scene_manifest, script, fps=fps, width=width, height=height
    )
    path = persist_render_props(project_id, props, cfg)
    return props, path


__all__ = [
    "render_dir",
    "render_props_path",
    "draft_debug_path",
    "build_render_props",
    "persist_render_props",
    "build_and_persist_render_props",
]
