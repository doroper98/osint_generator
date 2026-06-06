"""build_narration — HyperFrames demo 의 narration 음성 생성 (v0.34.5).

목적: 사용자 머신의 `.env` 의 ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID 를 써서
demo 의 8 cue narration 을 한 mp3 로 합성. 각 cue 사이에 정확한 무음을 끼워
HyperFrames 의 timeline (t=0.6, 4.5, 9.0, 13.5, 17.0, 21.0, 25.0, 28.5) 와 sync.

cloud 는 외부 TTS API 가 차단되어 음성 생성 불가 — 사용자 머신 전용.

사용법 (사용자 머신):
    cd C:\\01_Antigravity\\osint_generator
    git pull origin claude/stoic-galileo-Xmxyj
    pip install -r requirements.txt    # imageio-ffmpeg + mutagen 포함 (v0.34.6)
    python hyperframes\\scripts\\build_narration.py

산출:
    hyperframes/demo/assets/audio/brent.mp3 (30초)

이후:
    cd hyperframes/demo
    npx hyperframes render

의존성 메모:
    - imageio-ffmpeg: portable ffmpeg 바이너리 (PATH 따로 안 잡아도 작동).
    - mutagen: mp3 길이 측정 (pure python, ffprobe 의존 회피).
    위 두 패키지가 requirements.txt 에 있어 pip install 만으로 됨. 시스템에
    ffmpeg 이미 있어도 imageio-ffmpeg 가 자동 발견하니 중복 OK.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# .env 자동 로딩 (v0.32.1 패턴).
try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]

    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=False)
except ImportError:
    pass


def _resolve_ffmpeg() -> str:
    """ffmpeg 실행 파일 경로 자동 발견.

    1. imageio-ffmpeg (pip 으로 설치되는 portable 바이너리) → PATH 불요.
    2. 시스템 PATH 의 ffmpeg.
    3. 둘 다 없으면 명확한 안내 + exit.
    """
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass

    found = shutil.which("ffmpeg")
    if found:
        return found

    print(
        "error: ffmpeg 가 없습니다. 둘 중 하나로 설치:\n"
        "  (권장) pip install imageio-ffmpeg mutagen\n"
        "  (대안) winget install ffmpeg 또는 https://ffmpeg.org/download.html",
        file=sys.stderr,
    )
    sys.exit(1)


def _probe_duration_mp3(path: Path) -> float:
    """mp3 길이 측정 — mutagen(pure python) 우선, 없으면 ffprobe 폴백.

    Windows 의 ffprobe 가 PATH 에 없는 경우 사고 회피.
    """
    try:
        from mutagen.mp3 import MP3  # type: ignore[import-not-found]

        return float(MP3(str(path)).info.length)
    except ImportError:
        pass

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        print(
            "error: mp3 길이 측정 불가. pip install mutagen 권장.",
            file=sys.stderr,
        )
        sys.exit(1)
    out = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(out.stdout.strip())


FFMPEG_BIN = _resolve_ffmpeg()


# index.html 의 cue 배열과 1:1 매칭.
CUES: list[tuple[float, str]] = [
    (0.6, "2026년 3월 4일, 호르무즈 해협 봉쇄 사태가 발생했습니다."),
    (4.5, "전 세계 원유 공급의 약 20%가 차단되며 충격이 전파됐습니다."),
    (9.0, "봉쇄 직후 브렌트유는 배럴당 80달러에서 120달러로 급등했습니다."),
    (13.5, "한 달 만에 약 50% 가까이 오른 셈입니다."),
    (17.0, "4월 7일 1차 휴전 합의로 유가는 잠시 안정세를 보였지만,"),
    (21.0, "5월 5일 UAE 표적 공격으로 다시 약 114달러까지 반등했습니다."),
    (25.0, "5월 19일 현재 102달러 수준에서 협상이 이어지고 있습니다."),
    (28.5, "유가는 지정학적 리스크에 가장 민감한 지표입니다."),
]

TOTAL_DURATION_SEC = 30.0
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "demo" / "assets" / "audio" / "brent.mp3"
)


def synth_one(text: str, api_key: str, voice_id: str, model_id: str) -> bytes:
    """ElevenLabs API 단일 합성 — mp3 bytes 반환."""
    import httpx

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.7},
    }
    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, json=payload, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:200]}")
        return r.content


def write_silence(path: Path, duration_sec: float) -> None:
    """ffmpeg 으로 정확한 길이의 무음 mp3 생성."""
    subprocess.run(
        [
            FFMPEG_BIN,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-t",
            f"{duration_sec:.3f}",
            "-q:a",
            "9",
            "-acodec",
            "libmp3lame",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def probe_duration(path: Path) -> float:
    """mp3 길이 측정 — mutagen 우선."""
    return _probe_duration_mp3(path)


def concat_mp3s(parts: list[Path], output: Path) -> None:
    """ffmpeg concat demuxer 로 mp3 조각들 이어붙임."""
    listfile = output.parent / "_concat.txt"
    listfile.write_text("\n".join(f"file '{p.resolve()}'" for p in parts) + "\n")
    subprocess.run(
        [
            FFMPEG_BIN,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listfile),
            "-c",
            "copy",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    listfile.unlink()


def main() -> int:
    api_key = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    voice_id = (os.environ.get("ELEVENLABS_VOICE_ID") or "").strip()
    model_id = (os.environ.get("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2").strip()

    if not api_key:
        print("error: ELEVENLABS_API_KEY 환경변수가 없습니다.", file=sys.stderr)
        print("  .env 파일에 ELEVENLABS_API_KEY=sk_... 추가하거나 cmd 에 set 으로 export.", file=sys.stderr)
        return 1
    if not voice_id:
        print("error: ELEVENLABS_VOICE_ID 환경변수가 없습니다.", file=sys.stderr)
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    workdir = OUTPUT_PATH.parent / "_segments"
    workdir.mkdir(exist_ok=True)

    # 1) 각 cue 음성 합성.
    print(f"build_narration: {len(CUES)} cue 합성 시작 (voice={voice_id}, model={model_id})", flush=True)
    seg_paths: list[Path] = []
    for i, (t_start, text) in enumerate(CUES, start=1):
        seg = workdir / f"cue_{i:02d}.mp3"
        print(f"  [{i}/{len(CUES)}] {text[:30]}...", flush=True)
        mp3_bytes = synth_one(text, api_key, voice_id, model_id)
        seg.write_bytes(mp3_bytes)
        dur = probe_duration(seg)
        print(f"    → {seg.name} ({dur:.2f}s)", flush=True)
        seg_paths.append(seg)

    # 2) cue 들 사이 정확한 무음을 끼워서 timeline 매칭.
    print(f"build_narration: cue 사이 무음 삽입 + concat", flush=True)
    parts: list[Path] = []

    # 0 ~ cue1 시작 (t=0.6s) 의 lead-in 무음.
    lead = workdir / "_lead.mp3"
    write_silence(lead, CUES[0][0])
    parts.append(lead)

    for i, seg in enumerate(seg_paths):
        parts.append(seg)
        seg_dur = probe_duration(seg)
        cue_t = CUES[i][0]
        next_t = CUES[i + 1][0] if i + 1 < len(CUES) else TOTAL_DURATION_SEC
        avail = next_t - cue_t
        gap = avail - seg_dur
        if gap > 0.05:
            gap_path = workdir / f"_gap_{i:02d}.mp3"
            write_silence(gap_path, gap)
            parts.append(gap_path)
        elif gap < -0.2:
            print(
                f"  warning: cue {i+1} 음성 길이 {seg_dur:.2f}s 가 가용 시간 {avail:.2f}s 보다 김 (자막과 어긋날 수 있음).",
                flush=True,
            )

    concat_mp3s(parts, OUTPUT_PATH)
    final_dur = probe_duration(OUTPUT_PATH)
    print(f"build_narration 완료: {OUTPUT_PATH} ({final_dur:.2f}s)", flush=True)

    # 작업물 정리.
    for p in seg_paths:
        p.unlink()
    for p in workdir.glob("_*.mp3"):
        p.unlink()
    workdir.rmdir()

    print("", flush=True)
    print("다음 단계:", flush=True)
    print(f"  cd hyperframes\\demo", flush=True)
    print(f"  npx hyperframes render", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
