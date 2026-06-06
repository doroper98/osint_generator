"""render_demo — HyperFrames demo 통합 빌드 (v0.34.7).

사용자 머신 한 줄로:
    python hyperframes/scripts/render_demo.py [--with-narration]

순서:
    1. (선택) build_narration: ElevenLabs 로 narration mp3 생성.
    2. portable ffmpeg(imageio-ffmpeg) 를 임시 dir 에 `ffmpeg(.exe)` 로 심볼릭/복사
       → 그 dir 을 PATH 에 prepend → hyperframes 가 자동 탐지.
    3. `npx hyperframes render` 실행.

HyperFrames CLI 는 시스템 PATH 의 `ffmpeg` 를 spawn 하는데, 사용자 머신에
ffmpeg 가 안 깔려있어도 imageio-ffmpeg 의 portable 바이너리 한 번이면
설치 우회 가능 (winget/chocolatey/manual 설치 불필요).
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HF_DEMO_DIR = REPO_ROOT / "hyperframes" / "demo"


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


def _run_build_narration() -> int:
    """build_narration.py 를 같은 인터프리터로 실행."""
    script = Path(__file__).resolve().parent / "build_narration.py"
    print(f"[render_demo] narration 음성 합성 시작...", flush=True)
    result = subprocess.run([sys.executable, str(script)])
    if result.returncode != 0:
        print(
            f"[render_demo] build_narration 실패 (exit {result.returncode}). 진행 중단.",
            file=sys.stderr,
        )
    return result.returncode


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
    args = parser.parse_args()

    if not HF_DEMO_DIR.is_dir():
        print(f"error: HyperFrames demo 디렉토리 없음: {HF_DEMO_DIR}", file=sys.stderr)
        return 1

    if args.with_narration:
        rc = _run_build_narration()
        if rc != 0:
            return rc

    if args.no_render:
        return 0

    # portable ffmpeg 를 PATH 에 prepend.
    ffmpeg_src = _resolve_portable_ffmpeg()
    stage_dir, target = _stage_ffmpeg_on_path(ffmpeg_src)
    print(f"[render_demo] portable ffmpeg = {target}", flush=True)

    env = os.environ.copy()
    sep = ";" if platform.system() == "Windows" else ":"
    env["PATH"] = f"{stage_dir}{sep}{env.get('PATH', '')}"

    npx = _resolve_npx()
    cmd = [npx, "hyperframes", "render"]
    print(f"[render_demo] {' '.join(cmd)} (cwd={HF_DEMO_DIR})", flush=True)
    try:
        result = subprocess.run(cmd, cwd=str(HF_DEMO_DIR), env=env)
        return result.returncode
    finally:
        # 임시 stage dir 정리 (실패해도 무시).
        shutil.rmtree(stage_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
