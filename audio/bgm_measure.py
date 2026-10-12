"""BGM 실측 — 박 명확도·온셋 밀도·내레이션 대역 비중 (v7.2.0, 사용자 의견 UF-100, back_and_forth D-0222).

사용자 청취 판정(2026-10-12): "1번만 합격. 약간 박진감이 느껴지는 부분에서 점수를 줬어." — 합격곡과 불합격곡을 가른 실측
(뚜렷한 맥박·촘촘한 움직임)을 등록 하한(`rules audio.bgm_floor`)으로 둔다. 측정식은 BGM 조사 세션과 같다(같은 파일에서 같은 값,
Patriarch 7.12·2.9 % / Mario Bava 6.55·8.8 %). 레지스트리 available 곡은 `measured` 칸에 이 값을 적고, 하한 미달 = 오류.

CLI: `python -m audio.bgm_measure <파일.mp3>`(값 출력) · `python -m audio.bgm_measure --check`(레지스트리 available 곡 재측정 대조).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from rules import load_rules


class BgmMeasure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    beat_clarity: float      # 템포그램 명확도
    onsets_per_min: float    # 온셋 밀도
    voice_band: float        # 300~3000 Hz 파워 비중(0~1)


def measure(path: Path) -> BgmMeasure:
    """0~window_sec 모노 sr 로 읽어 세 값을 잰다(librosa — 지연 import: 렌더 경로는 이 의존이 없다)."""
    import librosa  # noqa: PLC0415

    fl = load_rules().audio.bgm_floor
    y, sr = librosa.load(str(path), sr=fl.sr, mono=True, duration=fl.window_sec)
    oenv = librosa.onset.onset_strength(y=y, sr=sr)
    tg = librosa.feature.tempogram(onset_envelope=oenv, sr=sr).mean(axis=1)[1:]   # 0 지연(자기 자신) 제외
    onsets = librosa.onset.onset_detect(onset_envelope=oenv, sr=sr)
    power = np.abs(librosa.stft(y, n_fft=fl.n_fft)) ** 2
    fr = librosa.fft_frequencies(sr=sr, n_fft=fl.n_fft)
    lo, hi = fl.voice_band_hz
    return BgmMeasure(beat_clarity=round(float(tg.max() / tg.mean()), 2),
                      onsets_per_min=round(len(onsets) / (len(y) / sr / 60), 1),
                      voice_band=round(float(power[(fr >= lo) & (fr <= hi)].sum() / power.sum()), 3))


def floor_failures(m: BgmMeasure) -> list[str]:
    """하한 미달 항목(빈 목록 = 통과)."""
    fl = load_rules().audio.bgm_floor
    out = []
    if m.beat_clarity < fl.beat_clarity_min:
        out.append(f"박 명확도 {m.beat_clarity} < {fl.beat_clarity_min}")
    if m.onsets_per_min < fl.onsets_per_min_min:
        out.append(f"온셋 분당 {m.onsets_per_min} < {fl.onsets_per_min_min}")
    if m.voice_band > fl.voice_band_max:
        out.append(f"내레이션 대역 {m.voice_band:.3f} > {fl.voice_band_max}")
    return out


def check_registry(remeasure: bool = True) -> list[str]:
    """레지스트리 available 곡: 기록값(measured) 하한 대조 + (remeasure) 파일 재측정이 기록값과 같은지."""
    from audio.registry import BGM_DIR, load_registry  # noqa: PLC0415

    bad = []
    for k, t in load_registry().tracks.items():
        if not t.available:
            continue
        bad += [f"{k}: {x}" for x in floor_failures(t.measured)]   # type: ignore[arg-type]
        if remeasure:
            got = measure(BGM_DIR / t.file)
            if got.model_dump() != t.measured.model_dump():   # type: ignore[union-attr] — python -m 실행 시 클래스가 __main__ 쪽이라 값으로 비교
                bad.append(f"{k}: 재측정 {got.model_dump()} ≠ 기록 {t.measured.model_dump()}")   # type: ignore[union-attr]
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m audio.bgm_measure", description="BGM 실측(UF-100 등록 하한)")
    ap.add_argument("file", nargs="?", type=Path)
    ap.add_argument("--check", action="store_true", help="레지스트리 available 곡 재측정·하한 대조")
    a = ap.parse_args(argv)
    if a.check:
        bad = check_registry()
        print(json.dumps({"ok": not bad, "errors": bad}, ensure_ascii=False))
        return 1 if bad else 0
    if a.file is None:
        ap.error("파일 또는 --check")
    m = measure(a.file)
    print(json.dumps({**m.model_dump(), "floor_failures": floor_failures(m)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
