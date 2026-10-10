"""앵커 청취 표본 — 믹스 30초 구간에 단어 앵커 시각마다 클릭음 (v5.17.0, back_and_forth D-0167 §3-5, R-0195 §4).

사람이 귀로 "자막·연출 앵커가 실제 발음 시작에 맞는가" 를 확인하는 자료다(Fable 은 들을 수 없다).
- 앵커 시각 = engine.timebase.at_word 와 같은 식: `t0 + start − trim_offset`(정렬 어절 첫 글자, `.align.json`).
- 문장 안 어절 = 원본 음성에서 edge·MMS 와 무관한 무음(`script.tts.align_gate.silences`) 밖에서 시작하는 어절,
  쉼 뒤 어절 = 무음 안 또는 문장 첫 어절. 구간 안에서 문장 안 n_in(10)·쉼 뒤 n_pause(5) 를 고르게 뽑는다.
- 클릭 = 1.5kHz 15ms 감쇠 사인. 믹스(`out/mix.f32`, 44.1k 스테레오 float32)는 손대지 않고 표본 파일만 만든다.

    python tools/click_sample.py projects/hormuz_korea --out docs/handoff/reports/phaseV3/click_sample [--start 초]
→ `click_sample.mp3`, `click_sample.md`(구간 시각·문장·어절·종류·자막), `click_sample.json`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from script.tts import align as tts_align  # noqa: E402
from script.tts.align_gate import silences  # noqa: E402
from script.tts.trim import SR, decode  # noqa: E402

WINDOW_SEC = 30.0
N_IN, N_PAUSE = 10, 5
CLICK_HZ, CLICK_SEC, CLICK_AMP = 1500.0, 0.015, 0.5


def word_anchors(plan: dict) -> list[dict]:
    """plan 전체 어절 앵커 [{t, sid, word, kind, text}] — kind = in(문장 안) | pause(쉼 뒤)."""
    out = []
    for s in plan["sentences"]:
        mp3 = Path(s["mp3"])
        al = tts_align.read(mp3)
        if al is None:
            raise ValueError(f"정렬 파일 없음: {mp3}")
        sil = silences(decode(mp3))
        text, pos = s["tts"], 0
        for k, w in enumerate(text.split()):
            i = text.index(w, pos)
            pos = i + len(w)
            start = float(al["character_start_times_seconds"][i])
            pause = k == 0 or any(a <= start < b for a, b in sil)
            t = s["t0"] + min(max(start - (s.get("trim_offset") or 0.0), 0.0), s["dur"])
            out.append({"t": round(t, 3), "sid": s["sid"], "word": w, "kind": "pause" if pause else "in", "text": s["text"]})
    return out


def _spread(items: list[dict], n: int) -> list[dict]:
    if len(items) <= n:
        return items
    idx = np.linspace(0, len(items) - 1, n).round().astype(int)
    return [items[i] for i in sorted(set(idx.tolist()))]


def choose_window(anchors: list[dict], total: float, start: float | None) -> tuple[float, list[dict]]:
    """조건(문장 안 ≥ N_IN, 쉼 뒤 ≥ N_PAUSE)을 만족하는 첫 30초 구간. start 를 주면 그 구간."""
    cands = [start] if start is not None else [x * 1.0 for x in range(0, max(1, int(total - WINDOW_SEC)) + 1)]
    for a in cands:
        inside = [x for x in anchors if a + 0.2 <= x["t"] <= a + WINDOW_SEC - 0.2]
        ins = [x for x in inside if x["kind"] == "in"]
        pau = [x for x in inside if x["kind"] == "pause"]
        if len(ins) >= N_IN and len(pau) >= N_PAUSE:
            return a, sorted(_spread(ins, N_IN) + _spread(pau, N_PAUSE), key=lambda x: x["t"])
    raise ValueError(f"문장 안 {N_IN}·쉼 뒤 {N_PAUSE} 어절을 담는 {WINDOW_SEC:g}초 구간이 없다")


def click() -> np.ndarray:
    n = int(CLICK_SEC * SR)
    t = np.arange(n) / SR
    return (CLICK_AMP * np.sin(2 * np.pi * CLICK_HZ * t) * np.exp(-t / (CLICK_SEC / 4))).astype(np.float32)


def render(mix_f32: Path, a: float, picks: list[dict], dest: Path) -> None:
    y = np.fromfile(mix_f32, np.float32).reshape(-1, 2)
    seg = y[int(a * SR): int((a + WINDOW_SEC) * SR)].copy()
    c = click()
    for p in picks:
        i = int(round((p["t"] - a) * SR))
        seg[i:i + len(c)] += c[: max(0, min(len(c), len(seg) - i)), None]
    seg = np.clip(seg, -1.0, 1.0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "libmp3lame", "-b:a", "192k", str(dest)], input=seg.tobytes(), check=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="tools.click_sample")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--start", type=float, default=None)
    args = ap.parse_args(argv)
    plan = json.loads((args.proj / "plan.json").read_text(encoding="utf-8"))
    a, picks = choose_window(word_anchors(plan), float(plan["total"]), args.start)
    args.out.mkdir(parents=True, exist_ok=True)
    render(args.proj / "out" / "mix.f32", a, picks, args.out / "click_sample.mp3")
    rows = [{**p, "t_in_sample": round(p["t"] - a, 3)} for p in picks]
    (args.out / "click_sample.json").write_text(json.dumps({"schema_version": 1, "window_start": a, "window_sec": WINDOW_SEC,
                                                            "voice": plan.get("voice"), "clicks": rows},
                                                           ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"구간 {a:.1f}~{a + WINDOW_SEC:.1f}초(전편 기준), 목소리 {plan.get('voice')}. 클릭 = 앵커 시각(어절 발음 시작이어야 한다).", "",
          "| 표본 안 초 | 전편 초 | 문장 | 어절 | 종류 | 자막 |", "|---|---|---|---|---|---|"]
    md += [f"| {r['t_in_sample']:.2f} | {r['t']:.2f} | {r['sid']} | {r['word']} | {'쉼 뒤' if r['kind'] == 'pause' else '문장 안'} | {r['text']} |"
           for r in rows]
    (args.out / "click_sample.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"window_start": a, "clicks": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
