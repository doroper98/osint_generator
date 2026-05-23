"""full_script → scene_manifest 결정론적 빌더 (수직 슬라이스 V2, v0.10.0).

수직 슬라이스의 최소 Scene 단계. 텍스트 슬라이드 영상이 목표라 LLM 이 필요 없고,
ScriptSegment 1개를 SceneEntry 1개로 결정론적으로 매핑한다 (Phase 5
source_registry_builder 와 같은 **순수 함수** 패턴 — 디스크 I/O 없음).

매핑 규칙
---------
- scene_id = `scene_{i:02d}` (1-기반), segment 순서 유지.
- start_sec 는 앞 scene 들의 duration 누적, duration_sec = segment.est_duration_sec
  (0 이하면 DEFAULT_SEGMENT_SEC 로 보정).
- caption = segment.on_screen_caption (없으면 narration 앞부분).
- narration_segment_ids = [segment.segment_id] → 렌더러가 full_script 에서 본문/라벨 조회.
- inference_label_required = segment.label 이 있으면 True (<미검증>/<추론>/<주장>/<반박됨>
  배지 표기 신호. docs/06 §6).
- source_link_required = claim_refs 가 있으면 True (근거 있는 사실엔 출처 표기).

깊은 시각 연출(에셋·지도·전환 등)은 슬라이스 관통 후 정식 ScenePlanner(LLM)에서 보강.
"""

from __future__ import annotations

from schemas.models import (
    FullScript,
    SceneEntry,
    SceneManifest,
    SceneProvenance,
)


DEFAULT_SEGMENT_SEC: float = 8.0
SLICE_SCENE_TYPE: str = "text_slide"


def _segment_duration(est: float) -> float:
    """est_duration_sec 보정 — 0 이하/비정상은 DEFAULT_SEGMENT_SEC."""
    if est is None or est <= 0:
        return DEFAULT_SEGMENT_SEC
    return float(est)


def build_scene_manifest(script: FullScript) -> SceneManifest:
    """FullScript 를 받아 결정론적으로 SceneManifest 생성 (순수 함수, I/O 없음).

    segment 순서 그대로 1:1 scene 을 만들고 start_sec 를 누적한다. 같은 입력이면
    항상 같은 manifest (테스트·재현 가능).
    """
    scenes: list[SceneEntry] = []
    cursor = 0.0
    for i, seg in enumerate(script.segments, start=1):
        duration = _segment_duration(seg.est_duration_sec)
        caption = seg.on_screen_caption or seg.narration[:40]
        scenes.append(
            SceneEntry(
                scene_id=f"scene_{i:02d}",
                chapter_id=seg.chapter_id,
                start_sec=round(cursor, 3),
                duration_sec=round(duration, 3),
                scene_type=SLICE_SCENE_TYPE,
                narration_segment_ids=[seg.segment_id],
                caption=caption,
                visual_type=SLICE_SCENE_TYPE,
                inference_label_required=seg.label is not None,
                source_link_required=bool(seg.claim_refs),
                worker_provenance=SceneProvenance(
                    primary_worker="scene_builder",
                    input_manifests=["05_script/full_script.json"],
                ),
            )
        )
        cursor += duration

    return SceneManifest(project_id=script.project_id, scenes=scenes)


__all__ = ["build_scene_manifest", "DEFAULT_SEGMENT_SEC", "SLICE_SCENE_TYPE"]
