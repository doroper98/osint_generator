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


def build_description(plan: Plan, d: Description) -> str:
    ch = [f"{mmss(chapter_time(plan, c.at, i == 0))} {c.label}" for i, c in enumerate(d.chapters)]
    parts = [d.headline, "", d.summary, "", "챕터", *ch]
    if d.footer:
        parts += ["", *d.footer]
    return "\n".join(parts)


def load_description(proj: Path) -> Description:
    return Description.model_validate(yaml.safe_load((proj / "description.yaml").read_text(encoding="utf-8")))


def mux(proj: Path, total: float) -> Path:
    ln = load_rules().audio.loudnorm
    out = proj / "out" / "final.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(proj / "out" / "video_noaudio.mp4"),
                    "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(proj / "out" / "mix.f32"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", f"loudnorm=I={ln.I:g}:TP={ln.TP:g}:LRA={ln.LRA:g}",
                    "-ar", str(SR), "-c:a", "aac", "-b:a", AAC_BITRATE, "-t", f"{total:.3f}", "-movflags", "+faststart",
                    str(out)], check=True)
    return out


def asset_usage(P) -> dict:  # noqa: ANN001, N803 — engine.project.Project (순환 import 회피)
    """provenance `assets`: 렌더 전 점검이 불러온 이미지 키(= 렌더가 쓰는 이미지 전부)와 휘장 처리(D-0029 §2)."""
    from engine.provenance import emblem_usage  # noqa: PLC0415
    from script.badges import badge_usage  # noqa: PLC0415

    return {"images_used": sorted(P.R.assets.img), "emblems": emblem_usage(P.events, P.R.assets.emblem_flag),
            "badges": badge_usage(P.plan, P.events)}


def main(argv: list[str] | None = None) -> int:
    from engine.credits import RightsError, credit_lines, credit_summary, description_credits  # noqa: PLC0415
    from engine.project import ProjectError, load_project  # noqa: PLC0415
    from engine.provenance import build as build_prov  # noqa: PLC0415
    from engine.media_plan import density_report  # noqa: PLC0415
    from engine.reserved import avoidance_report  # noqa: PLC0415
    from script.media_suggest import media_usage  # noqa: PLC0415
    from orchestrator import __version__  # noqa: PLC0415
    from schemas.engine_models import StageResult  # noqa: PLC0415

    ap = argparse.ArgumentParser(description="engine.mux")
    ap.add_argument("proj", type=Path)
    args = ap.parse_args(argv)
    proj = args.proj.resolve()
    try:
        P = load_project(proj)  # noqa: N806 — 연출·권리 점검을 다시 통과해야 provenance 를 쓴다
        outd = proj / "out"
        for need in ("video_noaudio.mp4", "mix.f32"):
            if not (outd / need).exists():
                raise ProjectError(f"out/{need} 없음 — engine.render / audio.mix 먼저")
        final = mux(proj, P.plan.total)
        (outd / "final.srt").write_text(build_srt(P.plan), encoding="utf-8")
        (outd / "credits.txt").write_text("\n".join(credit_lines(P.R.credits, P.R.assets.rights, P.R.assets.media,
                                                                  P.R.cache.get("credit_refs"))) + "\n", encoding="utf-8")
        req = P.R.cache.get("credit_refs") or set()
        desc = build_description(P.plan, load_description(proj))
        dcred = description_credits(P.R.assets.rights, req)   # D-0030 — 카드에 안 넣는 종류(폰트)는 설명문에
        if dcred:
            desc += "\n\n" + DESCRIPTION_CREDITS_HEADING + "\n" + "\n".join(dcred)
        (outd / "description.txt").write_text(desc, encoding="utf-8")
        prov = build_prov(P.plan, P.keys, P.events, __version__,
                          {"plan": True, "render": True, "mix": True, "mux": True, "ai_direction": False, "visual_qa": False},
                          P.R.tb.word_anchors, asset_usage(P))
        prov["credits"] = credit_summary(req)   # D-0030 §3 — 표기 위치별 종류 개수
        prov["reserved"] = {"avoidance": avoidance_report(P)}   # D-0033 §2 — 카드 영역 때문에 비킨·흐린 뱃지
        prov["lint_warnings"] = P.warnings                       # 연출 경고(관계선 과다·연표 겹침·미디어 배치/밀도) — 오류 아님
        prov["media"] = {**media_usage(P.plan, P.events),        # v2.5.5 — 14 §10 제안·사용·밀도·배치(D-0036)
                         "density": density_report(P.events, P.R.tb, P.plan.total),
                         "placement": P.R.cache.get("media_placement", {})}
        (outd / "provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
        res = StageResult(ok=True, stage="mux", provenance=prov,
                          artifacts={"final": str(final), "srt": str(outd / "final.srt"),
                                     "description": str(outd / "description.txt"), "credits": str(outd / "credits.txt"), "provenance": str(outd / "provenance.json")})
    except (ProjectError, RightsError, KeyError, ValueError, OSError, subprocess.CalledProcessError) as ex:
        res = StageResult(ok=False, stage="mux", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
