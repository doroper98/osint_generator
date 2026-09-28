"""목소리 교체 무수정 싱크 증명표 (v2.3.0, back_and_forth D-0021 작업 8 · D-0026 §4, D31).

    python tools/voice_swap_report.py --a projects/hormuz_korea --b projects/hormuz_korea_sunhi \
        --eleven tests/fixtures/tts --out docs/handoff/reports/phase4/voice_swap

두 프로젝트(같은 원고·같은 direction.py, 목소리만 다름)의 plan 으로 각각 연출을 평가해
1. 단어 앵커: 연출 이벤트가 실제로 받은 전환 시각 − 정렬 파일에서 직접 계산한 단어 경계 시각(= 0 이어야 한다)
2. 목소리 교체 이동량: (B 전환 − A 전환) = (B 경계 − A 경계)
3. 골든 25 앵커의 절대 시각(A·B) — 같은 구성, 다른 절대 시각
4. direction.py 동일성(sha1)
을 JSON·Markdown 으로 쓴다. ElevenLabs 열은 실합성 3문장 픽스처(문장 기준 상대 시각)로 같은 계산을 한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.project import load_direction, load_plan  # noqa: E402
from engine.timebase import Timebase  # noqa: E402
from script.tts import align as tts_align  # noqa: E402
from tools.golden_compare import anchor_time, load_golden  # noqa: E402

TOL = 0.001  # word_anchors 의 t 는 소수 셋째 자리로 기록된다 — 반올림 오차 허용(1 ms, 1프레임 = 41.7 ms)


def boundary(plan_sent: object, word: str) -> float | None:
    """정렬 파일에서 직접: t0 + 발음 텍스트 속 단어 첫 글자 시작 − trim_offset."""
    al = tts_align.read(Path(plan_sent.mp3))  # type: ignore[attr-defined]
    if al is None:
        return None
    i = "".join(al["characters"]).find(word)
    if i < 0:
        return None
    return plan_sent.t0 + al["character_start_times_seconds"][i] - (plan_sent.trim_offset or 0.0)  # type: ignore[attr-defined]


def evaluate(proj: Path) -> dict:
    plan = load_plan(proj)
    tb = Timebase(plan)
    d = load_direction(proj).direct(tb)
    sent = {s.sid: s for s in plan.sentences}
    rows = []
    for a in tb.word_anchors:
        b = boundary(sent[a["sid"]], a["word"])
        rows.append(dict(sid=a["sid"], word=a["word"], mode=a["mode"], source=a["alignment_source"],
                         transition=round(a["t"], 3), boundary=None if b is None else round(b, 3),
                         diff=None if b is None else round(a["t"] - b, 4)))
    # 연출 이벤트가 실제로 받은 값 — relation 패널 state_changes[].at, statement joiner.t_join, 연표 t0
    used = []
    for e in d.events:
        for r in e.get("state_changes", []) or []:
            if "at" in r:
                used.append(round(r["at"], 3))
        j = e.get("joiner")
        if isinstance(j, dict) and "t_join" in j:
            used.append(round(j["t_join"], 3))
        for it in e.get("items", []) or []:
            if isinstance(it, dict) and "t0" in it:
                used.append(round(it["t0"], 3))
    golden = load_golden()
    pj = json.loads((proj / "plan.json").read_text(encoding="utf-8"))
    anchors = [dict(n=i, anchor=f["anchor"], offset=f["offset"], t=round(anchor_time(f["anchor"], float(f["offset"]), pj), 3))
               for i, f in enumerate(golden["frames"], 1)]
    return dict(voice=plan.voice, total=round(plan.total, 3), words=rows, event_times=sorted(set(used)), anchors=anchors,
                direction_sha1=hashlib.sha1((proj / "direction.py").read_bytes()).hexdigest())


def eleven(fixtures: Path, pairs: list[tuple[str, str]]) -> list[dict]:
    out = []
    for sid, word in pairs:
        f = fixtures / f"{sid}.align.json"
        if not f.exists():
            continue
        fx = json.loads(f.read_text(encoding="utf-8"))
        al = fx["alignment"]
        i = "".join(al["characters"]).find(word)
        b = al["character_start_times_seconds"][i] - fx["trim_offset"]
        # at_word 정렬 경로와 같은 식을 문장 시작 0 기준으로 — engine/timebase._aligned
        t = min(max(b, 0.0), fx["dur"])
        out.append(dict(sid=sid, word=word, transition_rel=round(t, 3), boundary_rel=round(b, 3), diff=round(t - b, 4)))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="목소리 교체 무수정 싱크 증명표")
    ap.add_argument("--a", type=Path, required=True)
    ap.add_argument("--b", type=Path, required=True)
    ap.add_argument("--eleven", type=Path, default=None)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    A, B = evaluate(args.a.resolve()), evaluate(args.b.resolve())  # noqa: N806
    shift = []
    for x, y in zip(A["words"], B["words"]):
        assert (x["sid"], x["word"]) == (y["sid"], y["word"])
        dt_tr = round(y["transition"] - x["transition"], 3)
        dt_b = None if x["boundary"] is None or y["boundary"] is None else round(y["boundary"] - x["boundary"], 3)
        shift.append(dict(sid=x["sid"], word=x["word"], d_transition=dt_tr, d_boundary=dt_b,
                          equal=dt_b is not None and abs(dt_tr - dt_b) < 1e-3))
    el = eleven(args.eleven, [(w["sid"], w["word"]) for w in A["words"]]) if args.eleven else []
    res = dict(schema_version=1, a=A, b=B, shift=shift, elevenlabs=el,
               direction_identical=A["direction_sha1"] == B["direction_sha1"],
               tolerance_sec=TOL,
               all_zero=all(w["diff"] is not None and abs(w["diff"]) <= TOL for w in A["words"] + B["words"] + el),
               all_shift_equal=all(s["equal"] for s in shift))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "voice_swap.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# 목소리 교체 증명표 — {A['voice']} → {B['voice']}", "",
          f"direction.py sha1 A `{A['direction_sha1'][:12]}` / B `{B['direction_sha1'][:12]}` → 동일 {res['direction_identical']}",
          f"총 길이 A {A['total']}초 / B {B['total']}초", "",
          "## 1. 전환 시각 − 단어 경계 시각 (초, 0 이어야 함 — 기록 반올림 허용 1 ms)", "",
          "| 문장 | 단어 | InJoon | SunHi | ElevenLabs(3문장) |", "|---|---|---|---|---|"]
    elm = {(e["sid"], e["word"]): e for e in el}
    for x, y in zip(A["words"], B["words"]):
        e = elm.get((x["sid"], x["word"]))
        md.append(f"| {x['sid']} | {x['word']} | {x['diff']} ({x['mode']}) | {y['diff']} ({y['mode']}) | "
                  f"{e['diff'] if e else '—'} |")
    md += ["", "## 2. 목소리 교체 이동량 (초) — 전환 이동 = 경계 이동", "",
           "| 문장 | 단어 | InJoon 전환 | SunHi 전환 | Δ전환 | Δ경계 | 같음 |", "|---|---|---|---|---|---|---|"]
    for x, y, s in zip(A["words"], B["words"], shift):
        md.append(f"| {s['sid']} | {s['word']} | {x['transition']} | {y['transition']} | {s['d_transition']} | {s['d_boundary']} | {s['equal']} |")
    md += ["", "## 3. 골든 25 앵커 절대 시각 (같은 구성, 다른 절대 시각)", "", "| # | 앵커 | InJoon | SunHi | 차 |", "|---|---|---|---|---|"]
    for x, y in zip(A["anchors"], B["anchors"]):
        md.append(f"| {x['n']:02d} | {x['anchor']}{x['offset']:+g} | {x['t']} | {y['t']} | {round(y['t'] - x['t'], 3)} |")
    (args.out / "voice_swap.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(dict(direction_identical=res["direction_identical"], all_zero=res["all_zero"],
                          all_shift_equal=res["all_shift_equal"]), ensure_ascii=False))
    return 0 if res["direction_identical"] and res["all_zero"] and res["all_shift_equal"] else 1


if __name__ == "__main__":
    sys.exit(main())
