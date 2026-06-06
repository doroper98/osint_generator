"""build-audio-demo — demo props 에 음성 입히기 (v0.32.2).

`build-audio` 는 project state machine 위에서 full_script.json 을 받아 동작한다.
데모(`remotion/demo_props.json`) 는 그 흐름을 거치지 않으므로, 본 모듈은 props 한
파일만 받아:

  1. 각 scene 의 narration 을 TTS 백엔드로 합성 → wav/mp3
  2. 각 scene 의 durationSec 을 실 음성 길이로 갱신 (시각 진입 모션이 음성에 맞춤)
  3. startSec 누적 재계산
  4. audioPath 를 staticFile 가 잡을 상대경로로 박음
  5. <props>_with_audio.json 으로 저장

state 머신·full_script·project_dir 컨텍스트 없이 동작. 사용자가 데모만 빠르게
보고 싶을 때 쓰는 1회용 헬퍼.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from workers.tts_backends import TTSError, get_backend


def build_audio_demo(
    props_path: Path,
    *,
    backend: str = "local",
    voice: Optional[str] = None,
    audio_subdir: str = "demo_audio",
) -> Path:
    """demo props 에 음성 입히고 새 props 반환.

    Parameters
    ----------
    props_path : Path
        원본 props JSON. `scenes[].narration` 필수.
    backend : str
        TTS 백엔드 (`local` / `elevenlabs` / `stub`).
    voice : Optional[str]
        백엔드별 voice id 오버라이드. None 이면 환경변수 사용.
    audio_subdir : str
        props 와 같은 디렉토리 아래 만들 wav 폴더 이름. 본 디렉토리가
        Remotion `--public-dir` 가 되므로 staticFile 가 잡는다.

    Returns
    -------
    Path
        새 props 파일 경로 (`<원본stem>_with_audio.json`).

    Raises
    ------
    FileNotFoundError : props 가 없거나 narration 비어있는 경우.
    TTSError          : 백엔드 실패.
    ValueError        : props 스키마 위반.
    """
    if not props_path.exists():
        raise FileNotFoundError(f"props 파일이 없습니다: {props_path}")

    raw = json.loads(props_path.read_text(encoding="utf-8"))
    scenes = raw.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError(f"props.scenes 가 비어있거나 잘못된 형식: {props_path}")

    engine = get_backend(backend)
    audio_dir = props_path.parent / audio_subdir
    audio_dir.mkdir(parents=True, exist_ok=True)

    n = len(scenes)
    print(f"build-audio-demo: {n}개 scene 합성 (backend={backend})", flush=True)
    cur_start = 0.0
    for i, sc in enumerate(scenes, start=1):
        sid = sc.get("sceneId") or f"scene_{i:02d}"
        narration = (sc.get("narration") or "").strip()
        if not narration:
            print(f"  [{i}/{n}] {sid} narration 비어있음 — skip (무음 유지)", flush=True)
            sc["startSec"] = cur_start
            cur_start += float(sc.get("durationSec", 0.0))
            continue
        out_path = audio_dir / f"{sid}{engine.file_ext}"
        print(f"  [{i}/{n}] {sid} 합성 중...", flush=True)
        duration = engine.synthesize(narration, out_path, voice)
        print(f"  [{i}/{n}] {sid} 완료 ({duration:.1f}s)", flush=True)
        # public-dir 가 props 디렉토리이므로 audioPath 는 상대경로 (slash).
        rel = f"{audio_subdir}/{out_path.name}"
        sc["audioPath"] = rel
        sc["startSec"] = round(cur_start, 3)
        sc["durationSec"] = round(max(duration, 0.5), 3)
        cur_start += sc["durationSec"]

    out_props = props_path.with_name(f"{props_path.stem}_with_audio.json")
    out_props.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"build-audio-demo 완료: {out_props}", flush=True)
    print(f"  audio dir: {audio_dir}", flush=True)
    print(f"  total    : {cur_start:.1f}s", flush=True)
    return out_props


__all__ = ["build_audio_demo"]
