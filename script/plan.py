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

from orchestrator.config import load_config
from script.lint import lint, load_claims_for, load_pronounce_dict, pronounce_tts
from script.schema import Plan, Script
from script.timeline import layout, sentence_rows
from script.tts import edge, elevenlabs
from script.tts.align import align_path
from script.tts.cache import cache_key, cached, mp3_path
from script.tts.trim import trim_to_npy


def load_script(proj: Path) -> Script:
    return Script.model_validate(yaml.safe_load((proj / "script.yaml").read_text(encoding="utf-8")))


def build(proj: Path, tts: str, warnings: list[str] | None = None, edge_voice: str | None = None) -> Plan:
    script = load_script(proj)
    rep = lint(script, load_claims_for(proj))   # v3.2.0 — 출처는 claims.json 기준(D-0051 작업 8)
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
    if edge_voice == load_config().tts.edge_voice:
        edge_voice = None           # 기본 목소리 = v3 캐시 키 그대로
    jobs: list[tuple[str, Path]] = []
    resynth: list[str] = []
    pron = load_pronounce_dict()
    for x in rows:   # v5.1.0 D-0121 §D — 합성 직전 발음 사전(명시 tts 포함, 멱등). 캐시 키 = 치환 뒤 텍스트
        x["tts"] = pronounce_tts(x["tts"], pron)
    for k, x in enumerate(rows):
        p = mp3_path(tts_dir, x["sid"], cache_key(x["tts"], vid, None if use_eleven else edge_voice))
        x["mp3"] = str(p)
        if cached(p):
            if align_path(p).exists():
                continue
            resynth.append(x["sid"])   # 정렬 없는 캐시 mp3 = 재합성(D34, 조용히 비율로 떨어지지 않는다)
        if use_eleven:
            elevenlabs.eleven_one(x["tts"], p, rows[k - 1]["tts"] if k else None,
                                  rows[k + 1]["tts"] if k + 1 < len(rows) else None)
        else:
            jobs.append((x["tts"], p))
    edge.synth_all(jobs, voice=edge_voice)
    for x in rows:
        npy, dur, off = trim_to_npy(Path(x["mp3"]))
        x["npy"], x["dur"], x["trim_offset"] = str(npy), dur, round(off, 6)
    cards, scene_start, total = layout(rows)
    return Plan(sentences=rows, cards=cards, scene_start=scene_start, total=total,
                voice=elevenlabs.voice_label() if use_eleven else edge.voice_label(edge_voice),
                title=script.title, subtitle=script.subtitle, date=script.date, tts_resynthesized=resynth)


def main(argv: list[str] | None = None) -> int:
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="script.plan")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--tts", choices=["edge", "elevenlabs"], default="edge")
    ap.add_argument("--edge-voice", default=None, help="edge 목소리 교체(기본 config tts.edge_voice) — 연출 무수정 싱크 검증(D31)")
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    warnings: list[str] = []
    try:
        plan = build(proj, args.tts, warnings, args.edge_voice)
        out = proj / "plan.json"
        out.write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"plan: {len(plan.sentences)} sentences, total {plan.total:.2f}s, voice {plan.voice}, "
              f"resynthesized(no align) {len(plan.tts_resynthesized)}", file=sys.stderr)
        res = StageResult(ok=True, stage="plan", artifacts={"plan": str(out), "tts": str(proj / "tts")},
                          warnings=warnings)
    except (ValueError, RuntimeError, OSError) as ex:
        res = StageResult(ok=False, stage="plan", errors=[str(ex)], warnings=warnings)
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
