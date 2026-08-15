"""나레이션 길이 추정 상수를 **새 목소리로 실측 재교정**한다 (계획 §5.4.2 레버 3).

현행 추정식 (`build_auto_narration.py:estimate_duration`)::

    dur = clamp(1.5, 9.0, 1.2 + 0.115 * len(text))

이 `1.2`(고정 오버헤드)와 `0.115`(글자당 초)는 **이전 목소리로 맞춘 값**이다. 목소리를
바꾸면 실제 발화 속도가 달라져 자막 타이밍·컷다운 예산이 전부 어긋난다.

본 스크립트는 길이가 고르게 분포된 표본 문장을 실제 ElevenLabs 목소리로 합성해 길이를
재고, 최소제곱 직선으로 `overhead` / `per_char` 를 다시 구한다.

사용 (사용자 머신 — `.env` 에 ELEVENLABS_API_KEY / VOICE_ID 필요)::

    python hyperframes/scripts/calibrate_pace.py
    python hyperframes/scripts/calibrate_pace.py --speed 1.05     # 속도 레버 함께 실측

산출::

    hyperframes/scripts/pace_calibration.json   재교정 결과 + 표본별 실측치
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_JSON = HERE / "pace_calibration.json"

#: 표본 문장 — 실번들(analysis_20260814_150031)에서 **길이가 고르게 퍼지도록** 뽑았다.
#: 짧은 것만 재면 오버헤드가, 긴 것만 재면 글자당 계수가 왜곡된다.
SAMPLES: list[str] = [
    "질문은 이미 옮겨갔습니다.",
    "학계가 이 물음을 다시 뜯어보고 있습니다.",
    "중국은 다 합쳐도 천이십억 달러로, 일곱 배 반 차이가 납니다.",
    "아랍에미리트에서는 데이터센터 전력 연결에 스물두 개월이 걸립니다.",
    "그런데 최상위 모델 성능 격차는 이 점 칠 퍼센트 포인트로 좁혀졌습니다.",
    "미국 대형 기술기업의 올해 에이아이 설비투자는 약 칠천육백사십억 달러입니다.",
    "민주주의가 느린 게 아니라, 국가역량이 무너진 것이라는 진단이 힘을 얻고 있습니다.",
    "그래서 인허가를 무시하고 자본을 몰아넣을 수 있는 권위주의가 더 유리하다는 말이 퍼졌습니다.",
]


def fit_line(xs: list[int], ys: list[float]) -> tuple[float, float]:
    """최소제곱 y = a + b*x. (a=오버헤드, b=글자당 초)"""
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        raise ValueError("표본 글자수가 모두 같아 기울기를 구할 수 없습니다.")
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    return my - b * mx, b


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--speed", type=float, default=None,
                    help="ELEVENLABS_SPEED 를 이 값으로 두고 측정 (계획 §5.4.2 상한 1.10)")
    ap.add_argument("--keep-audio", action="store_true", help="합성한 mp3 를 남긴다")
    args = ap.parse_args()

    if args.speed is not None:
        if not 0.7 <= args.speed <= 1.2:
            print(f"error: --speed {args.speed} 는 허용 범위(0.7~1.2) 밖입니다.")
            return 1
        os.environ["ELEVENLABS_SPEED"] = str(args.speed)

    sys.path.insert(0, str(HERE))
    try:
        from build_narration import probe_duration, synth_one  # type: ignore
    except ImportError as e:
        print(f"error: build_narration 의 합성 함수를 불러오지 못했습니다 — {e}")
        return 1

    # .env 를 읽어 환경에 실어 준다 (build_narration 과 같은 방식).
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
    # build_narration 과 같은 규칙으로 모델을 고른다 (측정 조건 일치).
    model_id = (os.environ.get("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2").strip()
    if not api_key or not voice_id:
        print("error: .env 의 ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID 가 필요합니다.")
        print("       (이 스크립트는 실제 음성을 합성해 길이를 재므로 키가 필수입니다)")
        return 1

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pace-cal-"))
    print(f"표본 {len(SAMPLES)}문장 합성 시작 (voice={voice_id[:8]}…, "
          f"speed={os.environ.get('ELEVENLABS_SPEED', '기본')})\n")

    rows: list[dict] = []
    for i, text in enumerate(SAMPLES):
        mp3 = tmp / f"s{i:02d}.mp3"
        try:
            # 앞뒤 문맥을 함께 넘긴다 — 낱개 합성은 억양이 흔들려 길이도 왜곡된다
            # (build_narration v0.38.3 학습). 실제 렌더와 같은 조건으로 재야 한다.
            audio = synth_one(
                text,
                api_key,
                voice_id,
                model_id,
                previous_text=SAMPLES[i - 1] if i > 0 else None,
                next_text=SAMPLES[i + 1] if i + 1 < len(SAMPLES) else None,
            )
            mp3.write_bytes(audio)
            dur = probe_duration(mp3)
        except Exception as e:  # noqa: BLE001
            print(f"  !! [{i}] 합성 실패 {type(e).__name__}: {e}")
            continue
        n = len(text)
        rows.append({"chars": n, "sec": round(dur, 3), "text": text})
        print(f"  {n:3}자  {dur:5.2f}s   {text[:42]}")

    if len(rows) < 3:
        print("\nerror: 유효 표본이 3개 미만이라 회귀할 수 없습니다.")
        return 1

    xs = [r["chars"] for r in rows]
    ys = [r["sec"] for r in rows]
    overhead, per_char = fit_line(xs, ys)

    def est(n: int) -> float:
        return overhead + per_char * n

    resid = [abs(est(r["chars"]) - r["sec"]) for r in rows]

    print("\n" + "=" * 58)
    print(f"재교정 결과:  dur = {overhead:.3f} + {per_char:.4f} * 글자수")
    print(f"  (현행 값:   dur = 1.200 + 0.1150 * 글자수)")
    print(f"  초당 글자수 = {1 / per_char:.1f}자  (현행 8.7자)")
    print(f"  평균 오차 = {statistics.mean(resid):.2f}s / 최대 {max(resid):.2f}s")

    for lo, hi, label in ((3.0, 5.0, "목표"), (4.0, 6.0, "구 규칙")):
        clo, chi = round((lo - overhead) / per_char), round((hi - overhead) / per_char)
        print(f"  {label} {lo:.0f}~{hi:.0f}초 창 = {clo}~{chi}자")

    OUT_JSON.write_text(
        json.dumps(
            {
                "voice_id": voice_id,
                "speed": os.environ.get("ELEVENLABS_SPEED", "default"),
                "overhead_sec": round(overhead, 4),
                "per_char_sec": round(per_char, 5),
                "chars_per_sec": round(1 / per_char, 2),
                "mean_abs_error_sec": round(statistics.mean(resid), 3),
                "samples": rows,
                "note": "계획 §5.4.2 레버 3 재교정 산출. estimate_duration 상수 갱신 근거.",
            },
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"\n[저장] {OUT_JSON}")
    print("\n다음: 이 값으로 build_auto_narration.py:estimate_duration 의 상수를 갱신하고")
    print("      계획 §5.4.1 의 자수 창 표를 실측값으로 교체합니다 (제가 반영하겠습니다).")

    if not args.keep_audio:
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)
    else:
        print(f"[audio] {tmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
