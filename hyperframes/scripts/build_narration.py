"""build_narration — HyperFrames demo narration 음성 생성 + sync 데이터 출력 (v0.34.8).

v0.34.5 → 0.34.8 변경: cue 시점을 고정 timeline 으로 박지 않고, 실 음성 길이를
측정해 누적 시점을 계산 → cuesync.json 출력. render_demo 가 그걸로 index.html
의 cue.t + 영상 duration 을 자동 patch → 음성·자막 sync drift 사고 회피.

사용자: "음성과 자막의 싱크가 안맞아. 자막은 이미 저 멀리 가고, 음성은 이미
지나간 화면의 자막을 읽고 있어" → 음성이 cue 간격보다 길어 누적 drift 했던 사고.

산출:
    hyperframes/demo/assets/audio/brent.mp3  (실 음성 길이에 맞춘 mp3)
    hyperframes/demo/cuesync.json            (각 cue 의 실 시작 시점 + 총 길이)

사용법 (사용자 머신, render_demo wrapper 가 자동 호출):
    python hyperframes/scripts/render_demo.py --with-narration
"""

from __future__ import annotations

import argparse
import json
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


# v0.34.8 — index.html 의 cue 배열과 1:1 매칭. t 값은 더 이상 hardcoded 가 아니라
# 실 음성 길이 + lead/pause/tail 로 누적 계산해 cuesync.json 으로 출력.
CUE_TEXTS: list[str] = [
    "2026년 3월 4일, 호르무즈 해협 봉쇄 사태가 발생했습니다.",
    "전 세계 원유 공급의 약 20%가 차단되며 충격이 전파됐습니다.",
    "봉쇄 직후 브렌트유는 배럴당 80달러에서 120달러로 급등했습니다.",
    "한 달 만에 약 50% 가까이 오른 셈입니다.",
    "4월 7일 1차 휴전 합의로 유가는 잠시 안정세를 보였지만,",
    "5월 5일 UAE 표적 공격으로 다시 약 114달러까지 반등했습니다.",
    "5월 19일 현재 102달러 수준에서 협상이 이어지고 있습니다.",
    "유가는 지정학적 리스크에 가장 민감한 지표입니다.",
]

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo"
OUTPUT_PATH = DEMO_DIR / "assets" / "audio" / "brent.mp3"
CUESYNC_PATH = DEMO_DIR / "cuesync.json"


def synth_one(text: str, api_key: str, voice_id: str, model_id: str) -> bytes:
    """ElevenLabs API 단일 합성 — mp3 bytes 반환.

    v0.34.9 — voice_settings 를 더 이상 hardcode 안 함.
    사용자가 ElevenLabs 웹의 voice library 에서 stability/similarity/style 등
    조정한 값을 그대로 반영하려면 payload 의 voice_settings 필드를 omit 해
    ElevenLabs 가 voice 의 default 를 적용하게 두는 게 정답. 사용자가 매 호출마다
    override 하고 싶으면 .env 의 ELEVENLABS_STABILITY / ELEVENLABS_SIMILARITY_BOOST /
    ELEVENLABS_STYLE / ELEVENLABS_USE_SPEAKER_BOOST 를 set.
    """
    import httpx

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload: dict = {"text": text, "model_id": model_id}

    # 사용자가 .env 에 명시 override 한 값만 voice_settings 에 채움.
    overrides: dict = {}
    if (v := os.environ.get("ELEVENLABS_STABILITY")):
        overrides["stability"] = float(v)
    if (v := os.environ.get("ELEVENLABS_SIMILARITY_BOOST")):
        overrides["similarity_boost"] = float(v)
    if (v := os.environ.get("ELEVENLABS_STYLE")):
        overrides["style"] = float(v)
    if (v := os.environ.get("ELEVENLABS_USE_SPEAKER_BOOST")):
        overrides["use_speaker_boost"] = v.strip().lower() in ("1", "true", "yes")
    if overrides:
        payload["voice_settings"] = overrides

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pause-sec",
        type=float,
        default=0.5,
        help="문장(cue)과 문장 사이 무음 길이 초. 기본 0.5. 자연 broadcast 톤은 "
        "0.4~0.7 권장. 더 짧으면 빠른 호흡, 더 길면 차분.",
    )
    parser.add_argument(
        "--lead-sec",
        type=float,
        default=0.5,
        help="영상 시작 후 첫 음성까지 lead-in 무음. 기본 0.5.",
    )
    parser.add_argument(
        "--tail-sec",
        type=float,
        default=0.5,
        help="마지막 음성 끝난 뒤 영상 끝까지 tail 무음. 기본 0.5.",
    )
    args = parser.parse_args(argv)

    if args.pause_sec < 0 or args.lead_sec < 0 or args.tail_sec < 0:
        print("error: pause/lead/tail 값은 0 이상이어야 합니다.", file=sys.stderr)
        return 1

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

    # 1) 각 cue 음성 합성 + 실 길이 측정.
    print(
        f"build_narration: {len(CUE_TEXTS)} cue 합성 (voice={voice_id}, model={model_id}, "
        f"lead={args.lead_sec}s, pause={args.pause_sec}s, tail={args.tail_sec}s)",
        flush=True,
    )
    seg_paths: list[Path] = []
    seg_durs: list[float] = []
    for i, text in enumerate(CUE_TEXTS, start=1):
        seg = workdir / f"cue_{i:02d}.mp3"
        print(f"  [{i}/{len(CUE_TEXTS)}] {text[:30]}...", flush=True)
        mp3_bytes = synth_one(text, api_key, voice_id, model_id)
        seg.write_bytes(mp3_bytes)
        dur = probe_duration(seg)
        print(f"    → {seg.name} ({dur:.2f}s)", flush=True)
        seg_paths.append(seg)
        seg_durs.append(dur)

    # 2) 누적 시점 계산 — 자막 cue 가 정확히 음성 시작과 sync.
    cue_starts: list[float] = []
    t = args.lead_sec
    for i, dur in enumerate(seg_durs):
        cue_starts.append(round(t, 3))
        t += dur
        if i < len(seg_durs) - 1:
            t += args.pause_sec
    total_duration = round(t + args.tail_sec, 3)
    print(f"build_narration: 누적 timing 계산 완료, total={total_duration:.2f}s", flush=True)

    # 3) lead/pause/tail 무음 끼워 concat.
    parts: list[Path] = []
    lead_path = workdir / "_lead.mp3"
    write_silence(lead_path, args.lead_sec)
    parts.append(lead_path)
    for i, seg in enumerate(seg_paths):
        parts.append(seg)
        if i < len(seg_paths) - 1:
            pause_path = workdir / f"_pause_{i:02d}.mp3"
            write_silence(pause_path, args.pause_sec)
            parts.append(pause_path)
    tail_path = workdir / "_tail.mp3"
    write_silence(tail_path, args.tail_sec)
    parts.append(tail_path)

    concat_mp3s(parts, OUTPUT_PATH)
    final_dur = probe_duration(OUTPUT_PATH)
    print(f"build_narration mp3: {OUTPUT_PATH} ({final_dur:.2f}s)", flush=True)

    # 4) cuesync.json 출력 — render_demo 가 index.html 자동 patch 용.
    sync_data = {
        "leadInSec": args.lead_sec,
        "interPauseSec": args.pause_sec,
        "tailSec": args.tail_sec,
        "totalDurationSec": total_duration,
        "cues": [
            {
                "t": cue_starts[i],
                "len": round(seg_durs[i], 3),
                "text": CUE_TEXTS[i],
            }
            for i in range(len(CUE_TEXTS))
        ],
    }
    CUESYNC_PATH.write_text(
        json.dumps(sync_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"build_narration sync: {CUESYNC_PATH}", flush=True)

    # 작업물 정리.
    for p in seg_paths:
        p.unlink()
    for p in workdir.glob("_*.mp3"):
        p.unlink()
    workdir.rmdir()

    print("", flush=True)
    print("다음 단계:", flush=True)
    print(f"  python hyperframes/scripts/render_demo.py", flush=True)
    print(f"  (또는 build_narration 까지 한 번에: python ... --with-narration)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
