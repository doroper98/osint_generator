"""make_bgm — 결정론적 앰비언트 BGM 생성 + 내레이션 더킹 믹스 (v0.40.0).

외부 음원 없이 ffmpeg lavfi 로 에디토리얼 톤의 앰비언트 베드를 합성한다 — 권리
100% 자체 생성(C9), 결정론. 내레이션 위에 사이드체인 더킹으로 깔아 말소리를
가리지 않게 한다.

음색: Cm9 계열 저음 패드(서브 C2 + C3·Eb3·G3·Bb3) + 느린 트레몰로 + 다크
lowpass + 공간 에코. 방송 다큐의 "잔잔한 긴장감".

사용:
    from make_bgm import generate_bed, duck_mix
    generate_bed(out_path, duration_sec)         # 베드만
    duck_mix(narration_mp3, bed_mp3, out_mp3)    # 내레이션+베드 더킹
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "hyperframes" / "scripts"))
from build_narration import FFMPEG_BIN  # noqa: E402

# Cm 계열 화성 (Hz) — 어둡고 차분한 긴장. 서브 + 3음 패드.
_VOICES = [
    (65.41, 0.55),   # C2 sub
    (130.81, 0.30),  # C3
    (155.56, 0.20),  # Eb3 (단3도 — 비장)
    (196.00, 0.22),  # G3 (완전5도)
    (233.08, 0.12),  # Bb3 (7음 — 여운)
]
BED_GAIN = 0.5  # 베드 자체 음량 (더킹 전)


def generate_bed(out_path: Path, duration_sec: float) -> None:
    """결정론적 앰비언트 베드 mp3 생성."""
    inputs: list[str] = []
    chains: list[str] = []
    labels: list[str] = []
    for i, (freq, vol) in enumerate(_VOICES):
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={freq}:sample_rate=44100"]
        # 보이스마다 느린 독립 LFO 로 미세한 움직임 (정적 드론 방지)
        lfo = 0.10 + 0.018 * i
        chains.append(f"[{i}]volume={vol},tremolo=f={lfo:.3f}:d=0.28[v{i}]")
        labels.append(f"[v{i}]")
    mix = (
        "".join(labels)
        + f"amix=inputs={len(_VOICES)}:normalize=0,"
        + "lowpass=f=540,"          # 다크 — 내레이션 대역(1~4kHz) 비움
        + "aecho=0.8:0.7:550:0.3,"  # 공간감
        + "highpass=f=38,"          # 럼블 컷
        + f"volume={BED_GAIN},"
        + f"afade=t=in:st=0:d=5,afade=t=out:st={max(0.1, duration_sec - 6):.2f}:d=6"
    )
    filt = ";".join(chains) + ";" + mix + "[out]"
    cmd = [
        FFMPEG_BIN, "-y", *inputs,
        "-filter_complex", filt, "-map", "[out]",
        "-t", f"{duration_sec:.3f}", "-ar", "44100", "-ac", "2",
        "-q:a", "5", "-acodec", "libmp3lame", str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def duck_mix(narration: Path, bed: Path, out_path: Path, bed_lufs: float = -23.0) -> None:
    """내레이션 + 베드 사이드체인 더킹 믹스.

    베드를 loudnorm 으로 bed_lufs(목표 음량)에 맞춘 뒤(생성 레벨이 -44dB 라
    고정 dB 곱은 이중 감쇠로 무음 사고 — v0.40.1), 내레이션을 키로 사이드체인
    더킹한다. 내레이션은 원음 그대로.
    """
    filt = (
        # 베드를 목표 LUFS 로 정규화 — 생성 레벨과 무관하게 일정한 가청 음량
        f"[1:a]loudnorm=I={bed_lufs}:LRA=7:TP=-4[bednorm];"
        # 사이드체인: 내레이션(0:a)을 키로 베드를 더킹 (말할 때 더 낮춤)
        "[bednorm][0:a]sidechaincompress="
        "threshold=0.05:ratio=6:attack=25:release=450:makeup=1[ducked];"
        "[0:a][ducked]amix=inputs=2:normalize=0:dropout_transition=0[mix]"
    )
    cmd = [
        FFMPEG_BIN, "-y", "-i", str(narration), "-i", str(bed),
        "-filter_complex", filt, "-map", "[mix]",
        "-ar", "44100", "-ac", "2", "-q:a", "4", "-acodec", "libmp3lame", str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def prepare_external(music: Path, out_path: Path, duration_sec: float,
                     fade_in: float = 3.0, fade_out: float = 6.0) -> None:
    """외부 음악 파일을 영상 길이에 맞춰 루프/트림 + 인/아웃 페이드.

    음악이 영상보다 짧으면 끊김 없이 반복(aloop), 길면 자른다. 끝 6초 페이드아웃.
    """
    subprocess.run(
        [FFMPEG_BIN, "-y", "-stream_loop", "-1", "-i", str(music),
         "-af",
         f"afade=t=in:st=0:d={fade_in},"
         f"afade=t=out:st={max(0.1, duration_sec - fade_out):.2f}:d={fade_out}",
         "-t", f"{duration_sec:.3f}", "-ar", "44100", "-ac", "2",
         "-q:a", "4", "-acodec", "libmp3lame", str(out_path)],
        check=True, capture_output=True,
    )


def make_bgm_external(narration: Path, music: Path, out_path: Path,
                      duration_sec: float, bed_lufs: float = -23.0) -> Path:
    """외부 음악 + 내레이션 더킹 믹스 (라이선스 음원 — 권장 경로)."""
    bed = narration.parent / "_extbed.mp3"
    prepare_external(music, bed, duration_sec)
    duck_mix(narration, bed, out_path, bed_lufs=bed_lufs)
    bed.unlink(missing_ok=True)
    return out_path


def make_bgm_for(narration: Path, out_path: Path, duration_sec: float) -> Path:
    """내레이션 mp3 → 베드 생성 + 더킹 믹스 → out_path."""
    bed = narration.parent / "_bed.mp3"
    generate_bed(bed, duration_sec)
    duck_mix(narration, bed, out_path)
    bed.unlink(missing_ok=True)
    return out_path


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("narration", help="내레이션 mp3")
    ap.add_argument("out", help="출력 믹스 mp3")
    ap.add_argument("--duration", type=float, required=True)
    a = ap.parse_args()
    make_bgm_for(Path(a.narration), Path(a.out), a.duration)
    print(f"[make_bgm] {a.out} 생성 (베드+더킹, {a.duration:.1f}s)")
