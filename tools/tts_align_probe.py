"""ElevenLabs 정렬 검증 — 문장 몇 개만 실제 합성해 at_word 정렬값과 비율 추정값을 비교 (v2.3.0, D31·D-0022).

    python tools/tts_align_probe.py projects/hormuz_korea --sids ask_1 ask_4 past_3 \
        --out docs/handoff/reports/phase4/align_probe.json --fixtures tests/fixtures/tts

- 합성은 지정한 문장만(과금 — 전편 재합성 금지, D31). 앞뒤 문장을 previous_text/next_text 로 보낸다.
- 음성은 `<proj>/tts_el/`(gitignore). 픽스처에는 **alignment 와 문장 메타(텍스트·길이·trim_offset)만** 쓴다.
  audio·요청 헤더·voice_id 는 어떤 파일에도 쓰지 않는다(D-0022, C9).
- 비교 단어는 연출(direction.yaml)이 at_word 로 부르는 (문장, 단어) 쌍을 그대로 쓴다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from script.plan import load_script  # noqa: E402
from script.schema import Plan  # noqa: E402
from script.timeline import sentence_rows  # noqa: E402
from script.tts import align, elevenlabs  # noqa: E402
from script.tts.cache import cache_key, cached, mp3_path  # noqa: E402
from script.tts.trim import trim_to_npy  # noqa: E402


def direction_words(proj: Path) -> list[tuple[str, str]]:
    """연출이 at_word 로 부르는 (sid, 단어) — 기존 plan.json 으로 연출을 한 번 평가해 기록을 모은다."""
    from engine.project import load_direction  # noqa: PLC0415
    from engine.timebase import Timebase  # noqa: PLC0415

    plan = Plan.model_validate(json.loads((proj / "plan.json").read_text(encoding="utf-8")))
    tb = Timebase(plan)
    load_direction(proj, tb)   # direction.yaml(v3.1.0)
    return [(a["sid"], a["word"]) for a in tb.word_anchors]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ElevenLabs 정렬 검증(소수 문장)")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--sids", nargs="+", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--fixtures", type=Path, default=None)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    try:
        elevenlabs.require_allowed()   # 키 접근·폴더 생성·과금 전에 차단(v5.13.0 D-0153 Q0, 가이드 23 §19 P0)
    except elevenlabs.ElevenLabsRefused as e:
        print(e, file=sys.stderr)
        return 2
    if not elevenlabs.available():
        print("ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID 없음", file=sys.stderr)
        return 2
    rows = sentence_rows(load_script(proj))
    idx = {r["sid"]: k for k, r in enumerate(rows)}
    pairs = [p for p in direction_words(proj) if p[0] in args.sids]
    d = proj / "tts_el"
    d.mkdir(exist_ok=True)
    vid = elevenlabs.voice_id()
    sents: dict[str, dict] = {}
    for sid in args.sids:
        k = idx[sid]
        x = rows[k]
        p = mp3_path(d, sid, cache_key(x["tts"], vid))
        if not (cached(p) and align.align_path(p).exists()):
            elevenlabs.eleven_one(x["tts"], p, rows[k - 1]["tts"] if k else None,
                                  rows[k + 1]["tts"] if k + 1 < len(rows) else None)
        _, dur, off = trim_to_npy(p)
        al = json.loads(align.align_path(p).read_text(encoding="utf-8"))
        sents[sid] = dict(text=x["text"], tts=x["tts"], dur=round(dur, 6), trim_offset=round(off, 6), alignment=al)
        if args.fixtures:
            args.fixtures.mkdir(parents=True, exist_ok=True)
            (args.fixtures / f"{sid}.align.json").write_text(json.dumps(sents[sid], ensure_ascii=False, indent=1),
                                                             encoding="utf-8")
    table = []
    for sid, word in pairs:
        s = sents[sid]
        chars = "".join(s["alignment"]["characters"])
        i = chars.find(word)
        aligned = None if i < 0 else s["alignment"]["character_start_times_seconds"][i] - s["trim_offset"]
        j = s["text"].find(word)
        ratio = max(0, j) / len(s["text"]) * s["dur"]
        table.append(dict(sid=sid, word=word, aligned_rel=None if aligned is None else round(aligned, 3),
                          ratio_rel=round(ratio, 3), diff=None if aligned is None else round(ratio - aligned, 3)))
    out = dict(schema_version=1, voice=elevenlabs.voice_label(), sids=args.sids,
               sentences={k: {kk: v for kk, v in s.items() if kk != "alignment"} for k, s in sents.items()}, words=table)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in table:
        print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
