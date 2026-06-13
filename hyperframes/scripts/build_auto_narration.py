"""build_auto_narration — auto 컴포지션 내레이션 합성 + 씬 시계 재계산 (v0.38.1).

auto.html 의 BRIEFING_DATA cue(text + tts)를 읽어:
    1. 문장별 ElevenLabs 합성 (cue.tts 우선, 없으면 cue.text)
    2. 문장별 실측 길이 → 씬 길이 재계산 (lead + Σ(문장+pause) + tail)
    3. 그 시계에 정확히 맞는 단일 mp3 조립 (무음 갭 채움)
    4. cuesync_auto.json 출력 → bundle_to_video.py --cuesync 가 소비

사용 (사용자 머신, .env 의 ELEVENLABS_API_KEY/VOICE_ID):
    python hyperframes/scripts/bundle_to_video.py <bundle.json> --narration=synth
    (위 한 줄이 본 스크립트를 내부 실행한다. 단독 실행도 가능:)
    python hyperframes/scripts/build_auto_narration.py [auto.html] [--estimate]

--estimate: API 없이 글자수 기반 길이 추정 + 무음 mp3 — sync 메커니즘 검증용.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
BRIEFING = REPO / "hyperframes" / "briefing"
sys.path.insert(0, str(REPO / "hyperframes" / "scripts"))

import subprocess

from build_narration import (  # noqa: E402 — demo 와 동일 계약 재사용
    FFMPEG_BIN,
    concat_mp3s,
    probe_duration,
    synth_one,
    write_silence,
)


def polish_tail(src: Path, dst: Path) -> None:
    """문장 꼬리의 무음·흡기음("흐흡") 제거 + 80ms 페이드아웃.

    역방향 트릭: 뒤집은 뒤 머리(=원본 꼬리)의 -38dB 이하 구간을 60ms 만 남기고
    잘라내고, 80ms 페이드인(=원본 페이드아웃)을 걸고 다시 뒤집는다.
    실측 커서 조립이라 길이가 줄어도 sync 는 자동 유지 (v0.38.2 검수 반영).
    """
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", str(src), "-af",
         "areverse,"
         "silenceremove=start_periods=1:start_threshold=-38dB:start_silence=0.06,"
         "afade=t=in:st=0:d=0.08,areverse",
         "-q:a", "4", "-acodec", "libmp3lame", str(dst)],
        check=True, capture_output=True,
    )

AUDIO_DIR = BRIEFING / "assets" / "audio"
AUDIO_OUT = AUDIO_DIR / "auto_narration.mp3"
CUESYNC_OUT = BRIEFING / "cuesync_auto.json"

LEAD_SEC = 1.1   # 씬 시작 후 첫 문장까지
PAUSE_SEC = 0.5  # 같은 씬 안 문장 사이
TAIL_SEC = 1.3   # 마지막 문장 후 씬 전환까지
MIN_SCENE = 5.0


def extract_data(html_path: Path) -> dict:
    html = html_path.read_text(encoding="utf-8")
    m = re.search(r"window\.BRIEFING_DATA = (\{.*?\});</script>", html, re.DOTALL)
    if not m:
        print(f"error: {html_path} 에서 BRIEFING_DATA 를 찾지 못함.", file=sys.stderr)
        sys.exit(1)
    return json.loads(m.group(1))


def estimate_duration(text: str) -> float:
    """한국어 TTS 추정 — 약 7.5자/초 + 문장 호흡."""
    return max(1.5, min(9.0, 1.2 + 0.115 * len(text)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", nargs="?", default=str(BRIEFING / "auto.html"))
    parser.add_argument("--estimate", action="store_true",
                        help="API 없이 길이 추정 + 무음 mp3 (sync 검증용)")
    parser.add_argument("--pause-sec", type=float, default=PAUSE_SEC)
    parser.add_argument("--lead-sec", type=float, default=LEAD_SEC)
    parser.add_argument("--tail-sec", type=float, default=TAIL_SEC)
    parser.add_argument("--bgm", action="store_true",
                        help="생성 앰비언트 BGM 을 더킹 믹스해 깐다 (make_bgm, 권리 자체생성).")
    args = parser.parse_args(argv)

    data = extract_data(Path(args.html))
    scenes = data["scenes"]
    cues = data["cues"]
    if not cues:
        print("error: cue 가 없습니다.", file=sys.stderr)
        return 1

    # ── 1. 문장별 합성/추정 ──
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="auto-narr-"))
    durs: list[float] = []
    parts: list[Path | None] = []
    if args.estimate:
        for c in cues:
            durs.append(round(estimate_duration(c.get("tts") or c["text"]), 3))
            parts.append(None)
        print(f"[auto_narration] 추정 모드 — {len(cues)}문장, 합성 생략")
    else:
        api_key = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
        voice_id = (os.environ.get("ELEVENLABS_VOICE_ID") or "").strip()
        model_id = (os.environ.get("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2").strip()
        if not api_key or not voice_id:
            print("error: ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID 필요 (.env 또는 환경변수).",
                  file=sys.stderr)
            return 1
        synth_texts = [c.get("tts") or c["text"] for c in cues]
        for i, c in enumerate(cues):
            text = synth_texts[i]
            print(f"[auto_narration] {i + 1}/{len(cues)} 합성: {text[:32]}…", flush=True)
            raw = tmp / f"raw{i:03d}.mp3"
            # 앞뒤 문맥 전달 — 평서문 끝 올림 억양 방지 (v0.38.3)
            raw.write_bytes(synth_one(
                text, api_key, voice_id, model_id,
                previous_text=synth_texts[i - 1] if i > 0 else None,
                next_text=synth_texts[i + 1] if i < len(cues) - 1 else None,
            ))
            mp3 = tmp / f"cue{i:03d}.mp3"
            polish_tail(raw, mp3)  # 꼬리 흡기음 컷 + 페이드아웃
            durs.append(round(probe_duration(mp3), 3))
            parts.append(mp3)

    # ── 2+3. 실측 커서 조립 — mp3 프레임 패딩 드리프트 방지 ──
    # 목표 시각을 먼저 정하고 무음을 끼우면 프레임 반올림이 누적된다 (v0.34.8 교훈).
    # 대신 조각(무음/문장)을 만들고 "실측 길이"를 누적한 커서가 곧 cue 시각이 된다.
    groups: list[list[int]] = [[] for _ in scenes]
    for ci, c in enumerate(cues):
        for si, sc in enumerate(scenes):
            if sc["t0"] <= c["t"] < sc["t1"]:
                groups[si].append(ci)
                break

    def silence_piece(name: str, sec: float) -> tuple[Path, float]:
        sil = tmp / f"{name}.mp3"
        write_silence(sil, sec)
        return sil, probe_duration(sil)

    seq: list[Path] = []
    scene_durs: list[float] = []
    cue_times: list[float] = [0.0] * len(cues)
    cursor = 0.0
    for si, sc in enumerate(scenes):
        start = cursor
        idxs = groups[si]
        if not idxs:
            pc, d = silence_piece(f"sc{si:02d}-empty", sc["t1"] - sc["t0"])
            seq.append(pc)
            cursor += d
        else:
            pc, d = silence_piece(f"sc{si:02d}-lead", args.lead_sec)
            seq.append(pc)
            cursor += d
            for j, ci in enumerate(idxs):
                cue_times[ci] = round(cursor, 3)
                if parts[ci] is None:  # 추정 모드 — 문장 자리 무음
                    pc, d = silence_piece(f"sc{si:02d}-cue{ci:03d}", durs[ci])
                else:
                    pc, d = parts[ci], durs[ci]
                seq.append(pc)
                cursor += d
                if j < len(idxs) - 1:
                    pc, d = silence_piece(f"sc{si:02d}-p{j}", args.pause_sec)
                    seq.append(pc)
                    cursor += d
            pc, d = silence_piece(f"sc{si:02d}-tail", args.tail_sec)
            seq.append(pc)
            cursor += d
            if cursor - start < MIN_SCENE:  # 짧은 씬 최소 길이 보장
                pc, d = silence_piece(f"sc{si:02d}-pad", MIN_SCENE - (cursor - start))
                seq.append(pc)
                cursor += d
        scene_durs.append(round(cursor - start, 3))
    total = round(cursor, 3)
    concat_mp3s(seq, AUDIO_OUT)
    actual = probe_duration(AUDIO_OUT)
    if abs(actual - total) > 0.1:
        print(f"warn: 조립 mp3 실측 {actual:.2f}s vs 계산 {total:.2f}s — 드리프트 확인 필요",
              file=sys.stderr)

    audio_rel = "assets/audio/auto_narration.mp3"
    if args.bgm and not args.estimate:
        from make_bgm import make_bgm_for  # noqa: E402
        bgm_out = AUDIO_DIR / "auto_narration_bgm.mp3"
        make_bgm_for(AUDIO_OUT, bgm_out, total)
        audio_rel = "assets/audio/auto_narration_bgm.mp3"
        print(f"[auto_narration] BGM 더킹 믹스 → {bgm_out.name}")

    CUESYNC_OUT.write_text(json.dumps({
        "mode": "estimate" if args.estimate else "synth",
        "total": total,
        "scene_durs": scene_durs,
        "cue_times": cue_times,
        "cue_durs": durs,
        "audio": audio_rel,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[auto_narration] total={total}s scenes={len(scenes)} cues={len(cues)} "
          f"-> {CUESYNC_OUT.name}, {AUDIO_OUT.relative_to(BRIEFING)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
