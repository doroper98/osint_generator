"""먹싱·자막·설명문·provenance CLI (v2.1.0, 10 §5, 16 §4).

    python -m engine.mux <proj>   → out/final.mp4, out/final.srt, out/description.txt, out/provenance.json

- 영상: out/video_noaudio.mp4 + out/mix.f32 → loudnorm(rules audio.loudnorm) + AAC 192k.
- 자막: 문장마다 시작 t0, 끝 t1 + 0.15(골든 SRT 실측), 자막 텍스트(발음 텍스트 아님).
- 설명문: 프로젝트 description.yaml 문안 + plan 으로 계산한 챕터 시각.
- provenance: 이번 렌더에 쓰인 기능(15 P5).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from rules import load_rules
from script.schema import Plan

SR = 44100
SRT_TAIL_SEC = 0.15
AAC_BITRATE = "192k"
DESCRIPTION_CREDITS_HEADING = "크레딧 (영상 밖 표기 — 폰트 등)"
DESCRIPTION_SOURCES_HEADING = "출처 원문 (보도 · 자료 · X 게시물)"


class Chapter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    at: str      # 장면 id 또는 TITLE
    label: str


class Description(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    headline: str
    summary: str
    chapters: list[Chapter] = Field(min_length=1)
    footer: list[str] = Field(default_factory=list)


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(plan: Plan) -> str:
    out = []
    for i, x in enumerate(plan.sentences, 1):
        out.append(f"{i}\n{srt_time(x.t0)} --> {srt_time(x.t1 + SRT_TAIL_SEC)}\n{x.text}\n")
    return "\n".join(out)


def mmss(t: float) -> str:
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def chapter_time(plan: Plan, at: str, first: bool) -> float:
    if first:
        return 0.0
    if at == "TITLE":
        return next(c.t0 for c in plan.cards if c.kind == "title")
    if at not in plan.scene_start:
        raise KeyError(f"설명문 챕터의 장면 없음: {at}")
    return plan.scene_start[at]


def build_description(plan: Plan, d: Description, music: list[str] | None = None) -> str:
    """footer 의 `{music}` 자리는 이번 영상이 쓰는 BGM 의 레지스트리 문구(v3.4.0, 규칙 credits.music_description).
    음악을 쓰지 않는데 {music} 가 있으면 오류 — 빈칸으로 조용히 지우지 않는다(P6)."""
    from audio.registry import description_line  # noqa: PLC0415

    ch = [f"{mmss(chapter_time(plan, c.at, i == 0))} {c.label}" for i, c in enumerate(d.chapters)]
    parts = [d.headline, "", d.summary, "", "챕터", *ch]
    if d.footer:
        fmt = load_rules().credits.music_description
        mus = " · ".join(description_line(m, fmt) for m in music or [])
        for line in d.footer:
            if "{music}" in line and not mus:
                raise ValueError("description.yaml footer 에 {music} 가 있는데 이번 영상은 BGM 을 쓰지 않는다")
        parts += ["", *(line.replace("{music}", mus) for line in d.footer)]
    return "\n".join(parts)


def load_description(proj: Path) -> Description:
    return Description.model_validate(yaml.safe_load((proj / "description.yaml").read_text(encoding="utf-8")))


def mux(proj: Path, total: float) -> tuple[Path, dict]:
    """영상 + mix → final.mp4. 음량은 2패스 loudnorm(v3.4.0 D-0061 — 측정은 audio/qa.py 한 경로). (경로, loudnorm 기록)."""
    from audio.qa import loudnorm_two_pass, mix_inputs  # noqa: PLC0415

    out = proj / "out" / "final.mp4"
    af, rec = loudnorm_two_pass(proj / "out" / "mix.f32", total)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(proj / "out" / "video_noaudio.mp4"),
                    *mix_inputs(proj / "out" / "mix.f32", total),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", af,
                    "-ar", str(SR), "-c:a", "aac", "-b:a", AAC_BITRATE, "-t", f"{total:.3f}", "-movflags", "+faststart",
                    str(out)], check=True)
    return out, rec


def asset_usage(P) -> dict:  # noqa: ANN001, N803 — engine.project.Project (순환 import 회피)
    """provenance `assets`: 렌더 전 점검이 불러온 이미지 키(= 렌더가 쓰는 이미지 전부)와 휘장 처리(D-0029 §2)."""
    from engine.provenance import emblem_usage  # noqa: PLC0415
    from script.badges import badge_usage  # noqa: PLC0415

    return {"images_used": sorted(P.R.assets.img), "emblems": emblem_usage(P.events, P.R.assets.emblem_flag),
            "badges": badge_usage(P.plan, P.events)}


def project_provenance(P, stages: dict[str, bool]) -> dict:  # noqa: ANN001, N803 — engine.project.Project
    """이 프로젝트의 provenance 한 벌(15 P5). mux(out/)와 preview(prev/)가 같은 함수를 쓴다(D-0041 §2).
    `stages` 는 이번 산출물에 실제로 돈 단계 — 돌지 않은 단계는 false 로 명시한다."""
    from engine.credits import credit_summary  # noqa: PLC0415
    from engine.media_plan import density_report  # noqa: PLC0415
    from engine.provenance import ai_direction_summary  # noqa: PLC0415
    from engine.provenance import build as build_prov  # noqa: PLC0415
    from engine.provenance import bundle_summary  # noqa: PLC0415
    from engine.provenance import camera_summary  # noqa: PLC0415
    from engine.reserved import avoidance_report  # noqa: PLC0415
    from orchestrator import __version__  # noqa: PLC0415
    from script.labels import check_project_labels  # noqa: PLC0415
    from script.media_suggest import media_usage  # noqa: PLC0415
    from script.plan import load_script  # noqa: PLC0415

    ai = ai_direction_summary(P.root)   # D-0047 작업 9 — AI 연출·시각 검수가 실제로 돌았을 때만 true
    bun = bundle_summary(P.root)        # v3.5.0 D-0063 작업 5 — import-bundle 기록이 있을 때만
    stages = {**stages, "ai_direction": ai is not None, "visual_qa": bool(ai and ai["visual_qa"]), "bundle": bun is not None}
    req = P.R.cache.get("credit_refs") or set()
    prov = build_prov(P.plan, P.keys, P.events, __version__, stages, P.R.tb.word_anchors, asset_usage(P))
    prov["credits"] = credit_summary(req)   # D-0030 §3 — 표기 위치별 종류 개수
    prov["reserved"] = {"avoidance": avoidance_report(P)}   # D-0033 §2 — 카드 영역 때문에 비킨·흐린 뱃지
    mus = sorted(r for r in (P.R.cache.get("credit_refs") or set()) if r.startswith("music."))
    segs = P.R.cache.get("bgm_segments", 1 if mus else 0)
    prov["audio"] = {"bgm": mus or None, "bed_gain": load_rules().audio.bed_gain,    # v3.4.0 — bgm null = 음악 없음(명시 상태, F1)
                     "crossfades": max(0, segs - 1)}
    if stages.get("mix") and mus:   # v4.6.0 D-0097 작업 5 — 베드 저음 보강 적용 값·측정치(믹서 기록 out/bed_stats.json). 음악 없으면 기록 없음(P5)
        from audio.qa import load_bed_stats  # noqa: PLC0415

        bs = load_bed_stats(P.root / "out")
        if bs is not None:
            prov["audio"]["bed_bass"] = {"applied": bs.applied.model_dump(), "ratio_db": {"before": bs.before.ratio_db, "after": bs.after.ratio_db},
                                         "rise_db": bs.rise_db, "swell_at": bs.swell_at, "bands_hz": {"bass": list(bs.bass_band_hz), "mid": list(bs.mid_band_hz)}}
    if P.R.credits is not None and any(c.kind == "end" for c in P.plan.cards):   # v4.7.0 D-0106 1-C — 엔딩 카드 롤(없으면 기록 없음)
        from engine.fullcards import endcard_roll, project_credit_sections  # noqa: PLC0415

        dist, v = endcard_roll(project_credit_sections(P.R), [s.column for s in P.R.credits.sections])
        if dist > 0:
            prov["end_card"] = {"roll_px": round(dist, 1), "roll_px_per_sec": round(v, 2)}
    # v3.6.0 D-0066 작업 1 — 이 산출물의 출력 프로파일. 전편은 render 가 남긴 out/render.json(영상을 만든 프로파일), 프리뷰는 P.R.out
    rj = P.root / "out" / "render.json"
    prov["render"] = {"resolution": (json.loads(rj.read_text(encoding="utf-8"))["resolution"]
                                     if stages.get("render") and rj.exists() else P.R.out.record())}
    if P.R.cache.get("badge") is not None:   # v4.8.0 D-0111 A — 버린 인물 뱃지 연출 R(적응 크기)
        prov["badge"] = P.R.cache["badge"]
    gc = P.R.cache.get("geo_check") or {}
    if gc.get("unsourced") is not None:   # v4.7.0 D-0107 D2(b) — 지도 무대 좌표 중 근거 대조 안 된 것(checks [geo-unsourced] 와 같은 값). 지도 없으면 기록 없음(P5)
        prov["geo"] = {"unsourced": gc["unsourced"], "matched": gc.get("matched") or [],   # v4.10.0 D-0116 — 지명 사전과 맞은 좌표·불일치
                       "mismatch": gc.get("mismatch") or []}
    prov["animatic"] = bool(getattr(P, "animatic", False))   # v4.9.0 D-0108 — 콘티 판 여부(전편 false, 콘티 판 true + animatic_run)
    prov["stage"] = P.R.cache.get("stage")   # v4.1.0 D-0076 작업 7 — 무대(name·declared·shots_declared·instances)
    g = P.R.cache.get("genre") or {}
    prov["genre"] = {"name": g.get("name"), "declared": g.get("declared"), "status": g.get("status")}   # v4.2.0 D-0081 작업 3, v4.3.0 status(proposed 사용 기록)
    from genres.load import load_genre, load_order  # noqa: PLC0415

    order = load_order(P.root)   # v4.4.0 D-0090 작업 4 — 주문(20 §11)과 사용자 결정 상태(by default = 사용자 미확정)
    if order is not None:
        prov["order"] = {"topic": order.topic, "genre": order.genre,
                         "decisions": {k: {"value": d.value, "by": d.by, "ref": d.ref} for k, d in order.decisions.items()}}
    new = sorted({e["id"] for e in P.events if e["type"] == "primitive"} & set(load_genre(g["name"]).primitives.new)) if g.get("name") else []
    if new:   # v4.4.0 — 새 요소(20 §4.1)의 사용자 승인 상태. 주문에 없으면 pending
        appr = order.decisions.get("elements_approval") if order is not None else None
        prov["elements"] = {"new": new, "approval": appr.value if appr else "pending", "by": appr.by if appr else "default"}
    if P.R.cache.get("series_records"):   # v4.3.0 D-0084 작업 6 — 이번 영상이 그린 데이터 레코드(15 P5)
        prov["series"] = [{"series_id": r.series_id, "as_of": r.as_of, "license": r.license, "source_url": r.source_url,
                           "transform": r.transform.op, "missing": [d.isoformat() for d in r.missing_dates()]}
                          for r in P.R.cache["series_records"]]
    prov["camera"] = camera_summary(P.root, P.keys, P.R.stage)        # v3.3.0 — 카메라 제안 suggested/used(D-0056, 제안은 옵션)
    prov["lint_warnings"] = P.warnings                       # 연출 경고(관계선 과다·연표 겹침·미디어 배치/밀도) — 오류 아님
    prov["media"] = {**media_usage(P.plan, P.events),        # v2.5.5 — 14 §10 제안·사용·밀도·배치(D-0036)
                     "density": density_report(P.events, P.R.tb, P.plan.total),
                     "placement": P.R.cache.get("media_placement", {})}
    labels = check_project_labels(P.root, load_script(P.root))   # v3.0.0 — 검증 라벨 집계(D-0043 §4), 도시어 없으면 None
    prov["script"] = {"labels": labels.counts() if labels is not None else None}
    if bun is not None:
        prov["bundle"] = bun
    if ai is not None:
        prov["ai_direction"] = ai
        prov["prompts"] = {"director": ai["prompt_sha1"]}
        prov["qa"] = {**prov["qa"], "auto_iterations": len(ai["revisions"]),
                      "visual_qa": [q["verdict"] for q in ai["visual_qa"]]}
    return prov


class AnimaticDeliverError(RuntimeError):
    """deliver 가 콘티 판을 받았다(v4.9.0 D-0108 — 배포 사고 방지, 15 P6)."""


def refuse_animatic(video: Path) -> None:
    """영상 mp4 메타데이터 comment 가 콘티 판 표식(rules animatic.mp4_comment)이면 오류. 콘티 판을 video_noaudio.mp4 로 복사해도 잡는다."""
    tag = load_rules().animatic.mp4_comment
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags=comment", "-of", "default=nw=1:nk=1", str(video)],
                       capture_output=True, text=True, check=True)
    if r.stdout.strip() == tag:
        raise AnimaticDeliverError(f"{video.name} 은 콘티 판(animatic)이다 — 배포(deliver) 금지. 전편은 `python -m engine.render <proj> --jobs N`")


def main(argv: list[str] | None = None) -> int:
    from engine.credits import RightsError, credit_lines, description_credits, description_sources  # noqa: PLC0415
    from engine.project import ProjectError, load_project  # noqa: PLC0415
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="engine.mux")
    ap.add_argument("proj", type=Path)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    try:
        outd = proj / "out"
        if (outd / "video_noaudio.mp4").exists():
            refuse_animatic(outd / "video_noaudio.mp4")   # v4.9.0 D-0108 — 콘티 판은 deliver 거부(프로젝트 로드 전에)
        P = load_project(proj)  # noqa: N806 — 연출·권리 점검을 다시 통과해야 provenance 를 쓴다
        for need in ("video_noaudio.mp4", "mix.f32"):
            if not (outd / need).exists():
                raise ProjectError(f"out/{need} 없음 — engine.render / audio.mix 먼저")
        final, loud = mux(proj, P.plan.total)
        (outd / "final.srt").write_text(build_srt(P.plan), encoding="utf-8")
        (outd / "credits.txt").write_text("\n".join(credit_lines(P.R.credits, P.R.assets.rights, P.R.assets.media,
                                                                  P.R.cache.get("credit_refs"), P.R.cache.get("cited_sources"),
                                                                  P.R.cache.get("series_records"))) + "\n",
                                          encoding="utf-8")
        req = P.R.cache.get("credit_refs") or set()
        desc = build_description(P.plan, load_description(proj), sorted(r for r in req if r.startswith("music.")))
        dcred = description_credits(P.R.assets.rights, req)   # D-0030 — 카드에 안 넣는 종류(폰트)는 설명문에
        if dcred:
            desc += "\n\n" + DESCRIPTION_CREDITS_HEADING + "\n" + "\n".join(dcred)
        dsrc = description_sources(P.R.cache.get("cited_sources"))   # v3.2.0 18 §6 — 원문 링크 전부(없으면 사유)
        if dsrc:
            desc += "\n\n" + DESCRIPTION_SOURCES_HEADING + "\n" + "\n".join(dsrc)
        (outd / "description.txt").write_text(desc, encoding="utf-8")
        prov = project_provenance(P, {"plan": True, "geo": True, "preview": (proj / "prev" / "provenance.json").exists(),
                                      "render": True, "mix": True, "mux": True, "ai_direction": False, "visual_qa": False})
        from engine.checks import check_audio  # noqa: PLC0415 — v3.4.0 오디오 QA(검사기 하나)

        issues, warns, qa = check_audio(P)
        (outd / "audio_qa.json").write_text(json.dumps({**qa, "hard": issues, "warnings": warns}, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
        prov["audio"] = {**prov["audio"], "loudnorm": {"passes": 2, **loud}, "qa": {"hard": issues, "warnings": warns,
                                                 **{k: qa[k] for k in ("final_loudness", "music_under_narration_db", "mix_peak", "bed_bass_ratio_db", "bed_bass_rise_db")}}}
        (outd / "provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
        if issues:
            raise ProjectError("오디오 QA hard 실패:\n" + "\n".join(issues))
        res = StageResult(ok=True, stage="mux", provenance=prov, warnings=warns,
                          artifacts={"final": str(final), "srt": str(outd / "final.srt"),
                                     "description": str(outd / "description.txt"), "credits": str(outd / "credits.txt"), "provenance": str(outd / "provenance.json")})
    except (ProjectError, RightsError, AnimaticDeliverError, KeyError, ValueError, OSError, subprocess.CalledProcessError) as ex:
        res = StageResult(ok=False, stage="mux", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
