"""render_demo — HyperFrames demo 통합 빌드 (v0.34.8).

사용자 머신 한 줄로:
    python hyperframes/scripts/render_demo.py --with-narration

순서:
    1. (--with-narration 시) build_narration: ElevenLabs 로 cue 별 음성 합성 +
       lead/pause/tail 끼워 mp3 + cuesync.json 출력.
    2. cuesync.json 으로 index.html 의 cue.t + composition duration 자동 patch
       한 index.synced.html 생성 → 음성·자막 sync drift 사고 회피 (v0.34.7
       사용자 보고: "자막은 멀리 가고, 음성은 이전 자막 내용 읽고 있음").
    3. portable ffmpeg(imageio-ffmpeg) 를 임시 dir 에 `ffmpeg(.exe)` 로 심볼릭/복사
       → 그 dir 을 PATH 에 prepend → hyperframes 가 자동 탐지.
    4. `npx hyperframes render -c index.synced.html` 실행.

옵션 (build_narration 으로 forward):
    --pause-sec   문장 사이 무음 (기본 0.5).
    --lead-sec    영상 시작 후 첫 음성까지 무음 (기본 0.5).
    --tail-sec    마지막 음성 후 tail 무음 (기본 0.5).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HF_DEMO_DIR = REPO_ROOT / "hyperframes" / "demo"
CUESYNC_PATH = HF_DEMO_DIR / "cuesync.json"
INDEX_HTML = HF_DEMO_DIR / "index.html"
SYNCED_HTML = HF_DEMO_DIR / "index.synced.html"


def _resolve_portable_ffmpeg() -> str:
    """imageio-ffmpeg 의 portable ffmpeg path. 없으면 명확한 에러."""
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        print(
            "error: imageio-ffmpeg 미설치.\n"
            "  pip install -r requirements.txt\n"
            "  (또는: pip install imageio-ffmpeg mutagen)",
            file=sys.stderr,
        )
        sys.exit(1)


def _stage_ffmpeg_on_path(ffmpeg_src: str) -> tuple[str, Path]:
    """portable ffmpeg 를 `ffmpeg(.exe)` 이름으로 임시 dir 에 배치하고 그 dir 을 반환.

    Windows: copy (symlink 가 권한 필요할 수 있음).
    POSIX: symlink (빠름).
    """
    stage_dir = Path(tempfile.mkdtemp(prefix="hf-ffmpeg-"))
    target_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    target = stage_dir / target_name

    if platform.system() == "Windows":
        shutil.copy2(ffmpeg_src, target)
    else:
        try:
            target.symlink_to(ffmpeg_src)
        except OSError:
            shutil.copy2(ffmpeg_src, target)
        target.chmod(0o755)

    return str(stage_dir), target


def _resolve_npx() -> str:
    """npx 위치. Windows 는 `npx.cmd`, POSIX 는 `npx`."""
    for name in ("npx.cmd", "npx"):
        found = shutil.which(name)
        if found:
            return found
    print(
        "error: npx 를 찾을 수 없습니다. Node.js(LTS) 설치 후 새 cmd 에서 다시 시도.",
        file=sys.stderr,
    )
    sys.exit(1)


def _run_build_narration(
    pause_sec: float, lead_sec: float, tail_sec: float, auto_pronounce: bool
) -> int:
    """build_narration.py 를 같은 인터프리터로 실행 (옵션 forward)."""
    script = Path(__file__).resolve().parent / "build_narration.py"
    print(f"[render_demo] narration 음성 합성 시작...", flush=True)
    cmd = [
        sys.executable,
        str(script),
        "--pause-sec", str(pause_sec),
        "--lead-sec", str(lead_sec),
        "--tail-sec", str(tail_sec),
    ]
    if auto_pronounce:
        cmd.append("--auto-pronounce")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(
            f"[render_demo] build_narration 실패 (exit {result.returncode}). 진행 중단.",
            file=sys.stderr,
        )
    return result.returncode


def _patch_index_html() -> Path:
    """cuesync.json 으로 index.html 의 cue.t + composition duration 을 patch 한
    index.synced.html 생성. 원본 index.html 은 안 건드림 (git 충돌 회피).

    Patch 대상:
        1. `const cues = [ {t: ..., text: ...}, ... ];` 블록의 t 값.
        2. `data-duration="30"` (root composition + audio 두 곳).
        3. `tl.fromTo("#stage", ..., { scale: 1.04, duration: 30, ... }, 0)` 의 duration.

    cuesync.json 없으면 그냥 원본 그대로 복사 (silent demo 용).
    """
    if not INDEX_HTML.exists():
        print(f"error: {INDEX_HTML} 없음.", file=sys.stderr)
        sys.exit(1)
    html = INDEX_HTML.read_text(encoding="utf-8")

    if CUESYNC_PATH.exists():
        sync = json.loads(CUESYNC_PATH.read_text(encoding="utf-8"))
        total = float(sync["totalDurationSec"])
        cues = sync["cues"]

        # 1. cues 배열 t 값 patch — text 는 보존, t 만 cuesync.json 값으로.
        new_cue_lines = ",\n        ".join(
            f'{{ t: {c["t"]:.3f}, text: "{_escape_js(c["text"])}" }}'
            for c in cues
        )
        new_cues_block = f"const cues = [\n        {new_cue_lines},\n      ];"
        html = re.sub(
            r"const cues = \[.*?\];",
            lambda _m: new_cues_block,
            html,
            count=1,
            flags=re.DOTALL,
        )

        # 2. data-duration="30" 모두 새 total 로 (root + audio).
        html = re.sub(
            r'data-duration="30"',
            f'data-duration="{total:.3f}"',
            html,
        )

        # 3. Ken Burns 의 duration 값 — `{ scale: 1.04, duration: 30, ease: "none" }`.
        html = re.sub(
            r'(\{\s*scale:\s*1\.04,\s*duration:\s*)30(,\s*ease:\s*"none"\s*\})',
            rf'\g<1>{total:.3f}\g<2>',
            html,
            count=1,
        )

        print(
            f"[render_demo] index.synced.html patched: total={total:.2f}s, "
            f"{len(cues)} cues",
            flush=True,
        )
    else:
        print(
            "[render_demo] cuesync.json 없음 — silent 데모로 진행 (원본 index.html 그대로).",
            flush=True,
        )

    SYNCED_HTML.write_text(html, encoding="utf-8")
    return SYNCED_HTML


def _escape_js(s: str) -> str:
    """JS 문자열 내 backslash / double-quote escape."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-narration",
        action="store_true",
        help="ElevenLabs 로 narration mp3 먼저 합성한 뒤 렌더 (사용자 머신, .env 의 키).",
    )
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="narration 합성만 하고 렌더는 안 함.",
    )
    parser.add_argument(
        "--pause-sec",
        type=float,
        default=0.5,
        help="문장 사이 무음 (build_narration 으로 forward, 기본 0.5).",
    )
    parser.add_argument(
        "--lead-sec",
        type=float,
        default=0.5,
        help="영상 시작 후 첫 음성까지 무음 (기본 0.5).",
    )
    parser.add_argument(
        "--tail-sec",
        type=float,
        default=0.5,
        help="마지막 음성 후 tail 무음 (기본 0.5).",
    )
    parser.add_argument(
        "--auto-pronounce",
        action="store_true",
        help="narration None 인 cue 에 자동 사전+숫자 한자어 변환 적용 (기본 OFF, "
        "v0.34.12 — 명시 narration 만 쓰는 패턴 권장).",
    )
    args = parser.parse_args()

    if not HF_DEMO_DIR.is_dir():
        print(f"error: HyperFrames demo 디렉토리 없음: {HF_DEMO_DIR}", file=sys.stderr)
        return 1

    if args.with_narration:
        rc = _run_build_narration(
            args.pause_sec, args.lead_sec, args.tail_sec, args.auto_pronounce
        )
        if rc != 0:
            return rc

    if args.no_render:
        return 0

    # cuesync.json (있으면) 으로 index.synced.html 자동 patch.
    synced = _patch_index_html()

    # portable ffmpeg 를 PATH 에 prepend.
    ffmpeg_src = _resolve_portable_ffmpeg()
    stage_dir, target = _stage_ffmpeg_on_path(ffmpeg_src)
    print(f"[render_demo] portable ffmpeg = {target}", flush=True)

    env = os.environ.copy()
    sep = ";" if platform.system() == "Windows" else ":"
    env["PATH"] = f"{stage_dir}{sep}{env.get('PATH', '')}"

    npx = _resolve_npx()
    cmd = [npx, "hyperframes", "render", "-c", synced.name]
    print(f"[render_demo] {' '.join(cmd)} (cwd={HF_DEMO_DIR})", flush=True)
    try:
        result = subprocess.run(cmd, cwd=str(HF_DEMO_DIR), env=env)
        return result.returncode
    finally:
        # 임시 stage dir 정리 (실패해도 무시).
        shutil.rmtree(stage_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
