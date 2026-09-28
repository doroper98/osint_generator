"""edge-tts 단어 경계 실측 — 비율 추정(at_word ratio)의 오차를 잰다 (v2.3.0, 보고 전용, D-0021 작업 8).

    python tools/edge_word_probe.py projects/hormuz_korea --sids ask_1 --voices ko-KR-InJoonNeural ko-KR-SunHiNeural \
        --out docs/handoff/reports/phase4/edge_word_probe.json

edge-tts 의 WordBoundary 이벤트(100ns 단위 offset)로 단어 발음 시작을 얻고, 같은 합성 음성을 plan 과 같은 규칙으로
트림해 `start − trim_offset` 을 문장 기준 시각으로 쓴다. 엔진은 이 값을 쓰지 않는다 — 비율 추정의 오차 보고용이다.
edge 합성은 호출마다 수 ms 다를 수 있으므로 비율 추정도 **이 합성의 길이**로 다시 계산해 같은 음성 안에서 비교한다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from orchestrator.config import load_config  # noqa: E402
from script.plan import load_script  # noqa: E402
from script.timeline import sentence_rows  # noqa: E402
from script.tts.trim import SR, decode, trim  # noqa: E402

TICKS = 1e7  # edge-tts offset 단위(100ns)


async def synth_words(text: str, voice: str, mp3: Path) -> list[tuple[str, float]]:
    import edge_tts  # noqa: PLC0415

    cfg = load_config().tts
    words: list[tuple[str, float]] = []
    com = edge_tts.Communicate(text, voice, rate=cfg.edge_rate, pitch=cfg.edge_pitch, boundary="WordBoundary")
    with mp3.open("wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append((ch["text"], ch["offset"] / TICKS))
    return words


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="edge-tts 단어 경계 실측(보고 전용)")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--sids", nargs="+", required=True)
    ap.add_argument("--voices", nargs="+", required=True)
    ap.add_argument("--words", nargs="*", default=None, help="없으면 연출의 at_word 단어")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    rows = {r["sid"]: r for r in sentence_rows(load_script(proj))}
    from tools.tts_align_probe import direction_words  # noqa: PLC0415

    pairs = [p for p in direction_words(proj) if p[0] in args.sids]
    out: dict = dict(schema_version=1, rate=load_config().tts.edge_rate, pitch=load_config().tts.edge_pitch, voices={})
    with tempfile.TemporaryDirectory() as d:
        for voice in args.voices:
            table = []
            for sid in args.sids:
                x = rows[sid]
                mp3 = Path(d) / f"{voice}_{sid}.mp3"
                words = asyncio.run(synth_words(x["tts"], voice, mp3))
                a, start = trim(decode(mp3))
                off, dur = start / SR, len(a) / SR
                for psid, w in pairs:
                    if psid != sid:
                        continue
                    hit = next((t for tok, t in words if tok.startswith(w)), None)
                    j = x["text"].find(w)
                    ratio = max(0, j) / len(x["text"]) * dur
                    meas = None if hit is None else hit - off
                    table.append(dict(sid=sid, word=w, measured_rel=None if meas is None else round(meas, 3),
                                      ratio_rel=round(ratio, 3), diff=None if meas is None else round(ratio - meas, 3),
                                      dur=round(dur, 3), trim_offset=round(off, 4)))
            out["voices"][voice] = table
            for r in table:
                print(voice, json.dumps(r, ensure_ascii=False))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
