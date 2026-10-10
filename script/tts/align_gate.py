"""강제 정렬 게이트 — 음향 발화 시작 참값 대조 + 문장 안 간격 일치 (v5.16.0, back_and_forth D-0165, DECISIONS D159).

edge `WordBoundary` 는 절대 시각이 아니다(TTS-AP-082). 그래서 게이트 참값을 음성 자체에서 잰다.
1. 절대 시각: 원본 음성(44.1k mono)에서 `|a| <= silence_thr` 가 `silence_sec` 이상 이어진 뒤 첫 초과 샘플 = 발화 시작.
   문장 첫 소리도 참값이다. 참값 k 번째 ↔ 정렬 어절 시작은 순서·단조로 대응한다(±`match_window_sec` 안 가장 가까운 것).
   대응 없는 참값은 빼지 않고 `match_window_sec` 오차로 계상한다(실패).
2. 간격 일치: 같은 문장 안 연속 어절(둘 다 쉼 뒤가 아님)의 간격 차 `|(정렬_b − 정렬_a) − (edge_b − edge_a)|`.
   차이라서 edge 의 상수 치우침이 소거된다(상수를 고르지 않는다). 쉼 뒤 = edge 시작 시각이 무음 구간 안.
두 검사 모두 `rules tts_rules.forced_align.gate`(중앙값·p90, ms) 이하여야 합격.

    python -m script.tts.align_gate <proj> [<proj> ...] [--edge] [--out rows.json]
      --edge : 각 문장 edge `.align.json` 을 간격 기준으로 쓰고, 정렬은 MMS 로 새로 잰다(.align.json 은 쓰지 않는다).
      없으면 : 각 문장 `.align.json`(mms_forced_alignment)을 그대로 읽어 절대 시각만 잰다(제작 음성 = Supertonic).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from rules import load_rules
from script.tts import align as tts_align
from script.tts.trim import SR, decode


@dataclass(frozen=True)
class GateStats:
    n: int
    median_ms: float
    p90_ms: float
    passed: bool


def rules():  # noqa: ANN201 — ForcedAlignRules
    return load_rules().tts_rules.forced_align


def silences(a: np.ndarray, sr: int = SR) -> list[tuple[float, float]]:
    """무음 구간 [(시작초, 끝초)] — 진폭 ≤ silence_thr 가 silence_sec 이상. 첫 소리 앞 구간은 길이와 무관하게 넣는다."""
    r = rules()
    loud = np.abs(a) > r.silence_thr
    idx = np.flatnonzero(loud)
    if idx.size == 0:
        raise ValueError("음성에 소리가 없다")
    out = [(0.0, idx[0] / sr)]
    gaps = np.flatnonzero(np.diff(idx) > int(round(r.silence_sec * sr)))   # 사이 무음 샘플 ≥ silence_sec
    out += [((idx[g] + 1) / sr, idx[g + 1] / sr) for g in gaps]
    return out


def onsets(a: np.ndarray, sr: int = SR) -> list[float]:
    """발화 시작 참값(초, 원본 음성 기준) — 문장 첫 소리 + 긴 무음 뒤 첫 소리."""
    return [end for _, end in silences(a, sr)]


def match(truth: list[float], starts: list[float]) -> list[float]:
    """참값마다 오차(초). 순서·단조 대응, 창 밖이면 match_window_sec 로 계상(실패를 빼지 않는다)."""
    win = rules().match_window_sec
    errs: list[float] = []
    j = 0
    for t in truth:
        cand = [(abs(s - t), k) for k, s in enumerate(starts) if k >= j and abs(s - t) <= win]
        if not cand:
            errs.append(win)
            continue
        e, k = min(cand)
        errs.append(e)
        j = k + 1
    return errs


def in_silence(t: float, sil: list[tuple[float, float]]) -> bool:
    return any(a <= t < b for a, b in sil)


def interval_errors(mms: list[float], edge: list[float], sil: list[tuple[float, float]]) -> list[float]:
    """연속 어절 간격 차(초) — 두 어절 모두 edge 시각이 무음 밖(쉼 뒤가 아님)일 때만."""
    if len(mms) != len(edge):
        raise ValueError(f"어절 수 불일치: 정렬 {len(mms)} ↔ edge {len(edge)}")
    after = [in_silence(t, sil) for t in edge]
    return [abs((mms[k + 1] - mms[k]) - (edge[k + 1] - edge[k]))
            for k in range(len(mms) - 1) if not after[k] and not after[k + 1]]


def stats(errs_sec: list[float]) -> GateStats:
    g = rules().gate
    if not errs_sec:
        raise ValueError("게이트 표본이 없다")
    ms = np.asarray(errs_sec) * 1000
    med, p90 = float(np.median(ms)), float(np.percentile(ms, 90))
    return GateStats(len(ms), round(med, 1), round(p90, 1), med <= g.median_ms and p90 <= g.p90_ms)


def word_starts_of(al: dict, pron_text: str) -> list[float]:
    """공통 형식 정렬 → 어절 첫 글자 시작 시각."""
    chars = "".join(al["characters"])
    if chars != pron_text:
        raise ValueError(f"정렬 글자 ≠ 발음 텍스트: {chars!r} ↔ {pron_text!r}")
    out, pos = [], 0
    for w in pron_text.split():
        i = pron_text.index(w, pos)
        out.append(float(al["character_start_times_seconds"][i]))
        pos = i + len(w)
    return out


def sentence_rows(mp3: Path, pron_text: str, mms: list[float], edge: list[float] | None) -> dict:
    a = decode(mp3)
    sil = silences(a)
    truth = onsets(a)
    row = {"mp3": mp3.name, "truth": [round(t, 4) for t in truth], "mms": [round(t, 4) for t in mms],
           "abs_err": [round(e, 4) for e in match(truth, mms)]}
    if edge is not None:
        row["edge"] = [round(t, 4) for t in edge]
        row["interval_err"] = [round(e, 4) for e in interval_errors(mms, edge, sil)]
    return row


def run(projects: list[Path], use_edge: bool) -> dict:
    from script.tts import forced_align  # noqa: PLC0415 — 무거운 의존성은 --edge 경로에서만

    rows = []
    for proj in projects:
        plan = json.loads((proj / "plan.json").read_text(encoding="utf-8"))
        for s in plan["sentences"]:
            mp3 = Path(s["mp3"])
            al = tts_align.read(mp3)
            if al is None:
                raise ValueError(f"정렬 파일 없음: {mp3}")
            if use_edge:
                edge = word_starts_of(al, s["tts"])
                mms = forced_align.word_starts(forced_align.align_sentence(mp3, s["tts"]), s["tts"])
            else:
                edge, mms = None, word_starts_of(al, s["tts"])
            rows.append({"project": proj.name, "sid": s["sid"], **sentence_rows(mp3, s["tts"], mms, edge)})
    out = {"absolute": asdict(stats([e for r in rows for e in r["abs_err"]]))}
    if use_edge:
        out["interval"] = asdict(stats([e for r in rows for e in r["interval_err"]]))
    out["passed"] = all(v["passed"] for v in out.values() if isinstance(v, dict))
    out["unmatched"] = sum(1 for r in rows for e in r["abs_err"] if e >= rules().match_window_sec)
    out["rows"] = rows
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="script.tts.align_gate")
    ap.add_argument("projects", nargs="+", type=Path)
    ap.add_argument("--edge", action="store_true", help="edge 정렬을 간격 기준으로, MMS 를 새로 정렬")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    res = run([p.resolve() for p in args.projects], args.edge)
    if args.out:
        args.out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, ensure_ascii=False))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
