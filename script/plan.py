"""원고 → 음성 → 타임라인 CLI (v2.1.0, plan3 `__main__`, 16 §4).

    python -m script.plan <proj> [--tts supertonic|elevenlabs]   → <proj>/plan.json, <proj>/tts/

기본 백엔드 = config.yaml tts.backend_default(v5.11.0 사용자 결정 D146 = supertonic). Supertonic 은 단어 시각을 내지 않아
`.align.json` 을 V2 강제 정렬(script/tts/forced_align, v5.16.0 D-0164 §5-4)이 합성 직후 문장마다 쓴다. 정렬이 이미 있는
캐시는 다시 정렬하지 않는다. 정렬 실패 = plan 실패(P6 — 비율 추정으로 넘어가지 않는다, 사용자 결정 D151).

린트 위반이 있으면 음성을 만들지 않고 실패한다. 마지막 줄에 StageResult JSON(표준 출력).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from orchestrator.config import load_config
from rules import load_rules
from script import lint_waivers
from script.lint import lint, load_claims_for, load_pronounce_dict, pronounce_tts, tempo_density, transition_points
from script.schema import Plan, Script
from script.timeline import layout, sentence_rows
from script.tts import align as tts_align
from script.tts import elevenlabs, forced_align, prosody, supertonic
from script.tts.align import align_path
from script.tts.cache import cache_key, cached, mp3_path
from script.tts.trim import decode, trim_to_npy


def load_script(proj: Path) -> Script:
    return Script.model_validate(yaml.safe_load((proj / "script.yaml").read_text(encoding="utf-8")))


def build(proj: Path, tts: str, warnings: list[str] | None = None) -> Plan:
    if tts not in ("supertonic", "elevenlabs"):   # v5.23.0 V4(D-0212) — edge 백엔드 삭제
        raise ValueError(f"TTS 백엔드 {tts!r} 없음 — supertonic(표준, C0.2) 또는 elevenlabs(호출 차단)")
    if tts == "elevenlabs":
        elevenlabs.require_allowed()   # 다른 단계보다 먼저(린트·합성 전에 거부) — 공통 함수(D-0153 Q0)
    script = load_script(proj)
    rep = lint(script, load_claims_for(proj))   # v3.2.0 — 출처는 claims.json 기준(D-0051 작업 8)
    rep, waived = lint_waivers.apply(rep, lint_waivers.load(proj), script)   # v5.17.0 D-0168 — 정확 일치 면제만
    if rep.errors:
        raise ValueError("원고 린트 위반:\n" + "\n".join(i.line() for i in rep.errors))
    if warnings is not None:
        warnings.extend(lint_waivers.waived_lines(waived) + [i.line() for i in rep.warnings])
    rows = sentence_rows(script)
    tts_dir = proj / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)
    use_eleven = tts == "elevenlabs"
    if use_eleven and not elevenlabs.available():
        raise ValueError("--tts elevenlabs 인데 ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID 가 없다(.env)")
    vid = elevenlabs.voice_id() if use_eleven else None
    st_cfg = supertonic.config() if tts == "supertonic" else None
    st_salt = supertonic.cache_salt(st_cfg) if st_cfg else None
    jobs: list[tuple[str, Path]] = []
    resynth: list[str] = []
    pron = load_pronounce_dict()
    for x in rows:   # v5.1.0 D-0121 §D — 합성 직전 발음 사전(명시 tts 포함, 멱등). 캐시 키 = 치환 뒤 텍스트
        x["tts"] = pronounce_tts(x["tts"], pron)
    for k, x in enumerate(rows):
        p = mp3_path(tts_dir, x["sid"], cache_key(x["tts"], vid, st_salt))
        x["mp3"] = str(p)
        if st_cfg is not None:
            x["chunks"] = supertonic.chunks(x["tts"], st_cfg)
            if not cached(p):
                jobs.append((x["tts"], p))
            continue
        if cached(p):
            if align_path(p).exists():
                continue
            resynth.append(x["sid"])   # 정렬 없는 캐시 mp3 = 재합성(D34, 조용히 비율로 떨어지지 않는다)
        if use_eleven:
            elevenlabs.eleven_one(x["tts"], p, rows[k - 1]["tts"] if k else None,
                                  rows[k + 1]["tts"] if k + 1 < len(rows) else None)
        else:
            jobs.append((x["tts"], p))
    if st_cfg is not None:
        supertonic.synth_all(jobs, st_cfg)
    ff = load_rules().tts_rules.prosody.final_fall
    for x in rows:
        audio = None
        if st_cfg is not None:
            x["alignment"] = forced_alignment(Path(x["mp3"]), x["tts"])
            audio, rec = final_fall_audio(Path(x["mp3"]), x["tts"], x["sid"], ff)   # v5.20.0 D-0175 — 트림 앞, npy 가 제품 음성
            x["prosody"] = {"final_fall": rec.model_dump()}
        else:   # elevenlabs 정렬은 절대 시각이 아니다(TTS-AP-082) — 보정하지 않는다(기록 없음 = 돌지 않은 단계, P5)
            al = tts_align.read(Path(x["mp3"]))
            x["alignment"] = {"source": al["alignment_source"]} if al else None
        npy, dur, off = trim_to_npy(Path(x["mp3"]), audio)
        x["npy"], x["dur"], x["trim_offset"] = str(npy), dur, round(off, 6)
    transitions: list = []
    from genres.load import load_order  # noqa: PLC0415

    order = load_order(proj)
    gap = load_rules().tempo.sentence_gap_sec if order is not None and order.tempo == "breath" else None   # v7.4.0 D-0229 §2.9
    cards, scene_start, total = layout(rows, transitions, gap)
    if warnings is not None:
        warnings.extend(tempo_density(rows))
    kinds = {rows[i]["sid"]: k for i, k, _ in transition_points(script)}   # v7.4.0 D-0229 §2.2 — 전환 종류(무대·날짜)
    order = [x["sid"] for x in rows]
    for tr in transitions:   # bridge 가 경계의 뒤 장면 첫 문장(같은 sid)이거나 앞 장면 마지막 문장(다음 sid)
        j = order.index(tr.sid)
        tr.kind = sorted({k for s_, ks in kinds.items() if order.index(s_) in (j, j + 1) for k in ks})
    return Plan(sentences=rows, cards=cards, scene_start=scene_start, total=total,
                voice=(supertonic.voice_label(st_cfg) if st_cfg else
                       elevenlabs.voice_label()),
                title=script.title, subtitle=script.subtitle, date=script.date, tts_resynthesized=resynth,
                lint_waived=waived or None, transitions=transitions)


def final_fall_audio(mp3: Path, pron_text: str, sid: str, cfg):  # noqa: ANN001, ANN201 — (np.ndarray, FinalFallRecord)
    """문장 끝 억양 보정(v5.20.0 D-0175) — 원본 mp3 디코드(정렬과 같은 시각 축)에 적용. mp3·.align.json 은 바꾸지 않는다."""
    try:
        return prosody.final_fall(decode(mp3), tts_align.read(mp3) or {}, pron_text, cfg)
    except prosody.ProsodyError as ex:
        raise ValueError(f"{sid}: 문장 끝 억양 보정 실패 — {ex}") from ex


def forced_alignment(mp3: Path, pron_text: str) -> dict:
    """Supertonic 문장 정렬 — 있으면 읽고(같은 발음 텍스트일 때만), 없으면 정렬해 쓴다. → plan row alignment."""
    al = tts_align.read(mp3)
    if al is None or "".join(al["characters"]) != pron_text or al["alignment_source"] != "mms_forced_alignment":
        try:
            al = forced_align.align_file(mp3, pron_text)
        except (forced_align.ForcedAlignError, tts_align.AlignmentError) as ex:
            raise ValueError(f"강제 정렬 실패 — {ex}") from ex
        tts_align.write(mp3, al)
    return {"source": al["alignment_source"], "score_mean": al.get("score_mean"), "elapsed_ms": al.get("elapsed_ms")}


def main(argv: list[str] | None = None) -> int:
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="script.plan")
    ap.add_argument("proj", type=Path)
    ap.add_argument("--tts", choices=["supertonic", "elevenlabs"], default=load_config().tts.backend_default)   # edge 삭제 v5.23.0 V4(D-0212)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    warnings: list[str] = []
    try:
        plan = build(proj, args.tts, warnings)
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
