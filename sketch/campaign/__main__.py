"""전황 작전도 스케치 CLI(D-0140 §3).

    python -m sketch.campaign projects/<pid>                # → out/sketch_campaign.mp4 · sketch_campaign_sheet.jpg · sketch_provenance.json
    python -m sketch.campaign projects/<pid> --frames 6,20  # 정지 화면
    python -m sketch.campaign projects/<pid> --check        # 렌더 없이 검사만(종료 코드 1 = hard 위반)

먼저 `python -m sketch.campaign.prep_georef projects/<pid>`(참고 작전도 → fronts.json). 검사 hard 위반이면 렌더하지 않는다(P6).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import ValidationError

from sketch.campaign.checks import MEDIA_DIR, check_render, check_spec
from sketch.campaign.spec import CampaignSpec
from sketch.common.checks import CheckReport, SketchCheckError, spec_errors
from sketch.common.cli import base_parser, parse_frames
from sketch.common.render import base_provenance, render_video, sha1_file, write_frames, write_provenance
from sketch.common.spec import SPEC_FILE, DataFile, RenderRecord, load_spec

FAIL = 1
OUT_DIR = "out"
STEM = "sketch_campaign"


def load_checked(project: Path) -> tuple[CampaignSpec | None, CheckReport]:
    report = CheckReport()
    try:
        spec = load_spec(project, CampaignSpec)
    except ValidationError as e:
        spec_errors(report, e)
        return None, report
    check_spec(report, spec, project)
    return spec, report


def data_files(spec: CampaignSpec, project: Path) -> list[DataFile]:
    ref = spec.fronts.reference
    rights = json.loads((project / ref.rights).read_text(encoding="utf-8"))["files"]
    ent = rights[ref.file]
    fr = json.loads((project / spec.fronts.file).read_text(encoding="utf-8"))
    out = [DataFile(path=ref.file, sha1=sha1_file(project / ref.file), source=ent["source_url"], license=ent["license"]),
           DataFile(path=spec.fronts.file, sha1=sha1_file(project / spec.fronts.file), source=fr["source"], license=ent["license"])]
    for m in spec.media:
        out.append(DataFile(path=f"{MEDIA_DIR}/{m.file}", sha1=sha1_file(project / MEDIA_DIR / m.file), source=m.credit, license=m.license))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = base_parser("python -m sketch.campaign", "전황 작전도 화면 스케치 — 국가·제대별 부대 부호, 날짜별 전선, 진격 화살표, 포위망")
    args = ap.parse_args(argv)
    project: Path = args.project
    spec, report = load_checked(project)
    for f in report.hard + report.warnings:
        print(f"{f.id} {f.message}", file=sys.stderr)
    if args.check:
        print(f"검사 {', '.join(report.ran)} — hard {len(report.hard)} · warning {len(report.warnings)}")
        return FAIL if report.hard else 0
    try:
        report.raise_if_hard()
    except SketchCheckError as e:
        print(e, file=sys.stderr)
        return FAIL
    assert spec is not None
    from sketch.campaign.scene import CampaignScene  # noqa: PLC0415 — 검사만 할 때는 지형 자산을 읽지 않는다

    scene = CampaignScene(spec, project, args.res)
    out = project / OUT_DIR
    prov = base_provenance(spec.kind, project / SPEC_FILE)
    times = parse_frames(args.frames)
    if times:
        paths = write_frames(scene, times, out, STEM)
        rec = RenderRecord(profile=scene.out.name, frames=len(paths), duration_sec=0, elapsed_sec=0)
        for p in paths:
            print(p)
    else:
        mp4, sheet, rec = render_video(scene, spec.duration_sec, spec.sheet_times, out, STEM)
        print(mp4, sheet)
    check_render(report, scene.res_boxes)
    prov.render = rec
    prov.data_files = data_files(spec, project)
    prov.features_drawn = scene.features_drawn()
    prov.approximations = ["전선: 참고 작전도 경위도 눈금 정합 개략선(잔차 "
                           f"{scene.data.residual_deg:.4f}°)", "부대 위치·화살표 경로: 군 단위 개략(참고 지도 2종 대조)"]
    prov.checks = report.record()
    print(write_provenance(prov, out))
    for f in report.warnings:
        print(f"{f.id} {f.message}", file=sys.stderr)
    if report.hard:
        print(SketchCheckError(report.hard), file=sys.stderr)
        return FAIL
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
