"""원고 → 음성 → 타임라인 CLI (v2.1.0, plan3 `__main__`, 16 §4).

    python -m script.plan <proj> --tts edge|elevenlabs   → <proj>/plan.json, <proj>/tts/

린트 위반이 있으면 음성을 만들지 않고 실패한다. 마지막 줄에 StageResult JSON(표준 출력).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from script.lint import lint
from script.schema import Plan, Script
from script.timeline import layout, sentence_rows
from script.tts import edge, elevenlabs
from script.tts.cache import cache_key, cached, mp3_path
from script.tts.trim import trim_to_npy


def load_script(proj: Path) -> Script:
    return Script.model_validate(yaml.safe_load((proj / "script.yaml").read_text(encoding="utf-8")))


def build(proj: Path, tts: str, warnings: list[str] | None = None) -> Plan:
    script = load_script(proj)
    rep = lint(script)
    if rep.errors:
        raise ValueError("원고 린트 위반:\n" + "\n".join(i.line() for i in rep.errors))
    if warnings is not None:
        warnings.extend(i.line() for i in rep.warnings)
    rows = sentence_rows(script)
    tts_dir = proj / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)
    use_eleven = tts == "elevenlabs"
    if use_eleven and not elevenlabs.available():
        raise ValueError("--tts elevenlabs 인데 ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID 가 없다(.env)")
    vid = elevenlabs.voice_id() if use_eleven else None
    jobs: list[tuple[str, Path]] = []
    for k, x in enumerate(rows):
        p = mp3_path(tts_dir, x["sid"], cache_key(x["tts"], vid))
        x["mp3"] = str(p)
        if cached(p):
            continue
        if use_eleven:
            elevenlabs.eleven_one(x["tts"], p, rows[k - 1]["tts"] if k else None,
                                  rows[k + 1]["tts"] if k + 1 < len(rows) else None)
        else:
            jobs.append((x["tts"], p))
    edge.synth_all(jobs)
    for x in rows:
        npy, dur = trim_to_npy(Path(x["mp3"]))
        x["npy"], x["dur"] = str(npy), dur
    cards, scene_start, total = layout(rows)
    return Plan(sentences=rows, cards=cards, scene_start=scene_start, total=total,
                voice="elevenlabs" if use_eleven else edge.voice_label(),
                title=script.title, subtitle=script.subtitle, date=script.date)


def main(argv: list[str] | None = None) -> int:
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="script.plan")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--tts", choices=["edge", "elevenlabs"], default="edge")
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    warnings: list[str] = []
    try:
        plan = build(proj, args.tts, warnings)
        out = proj / "plan.json"
        out.write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"plan: {len(plan.sentences)} sentences, total {plan.total:.2f}s, voice {plan.voice}", file=sys.stderr)
        res = StageResult(ok=True, stage="plan", artifacts={"plan": str(out), "tts": str(proj / "tts")},
                          warnings=warnings)
    except (ValueError, RuntimeError, OSError) as ex:
        res = StageResult(ok=False, stage="plan", errors=[str(ex)], warnings=warnings)
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
