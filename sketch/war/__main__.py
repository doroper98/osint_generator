"""전쟁사 스케치 CLI(v7.4.0 전쟁사 W3·W4, back_and_forth D-0600 §6).

    python -m sketch.war projects/<pid>                 # → out/sketch_war.mp4 · sketch_war_sheet.jpg · sketch_provenance.json
    python -m sketch.war projects/<pid> --frames 6,20   # 정지 화면(480p)
    python -m sketch.war projects/<pid> --check         # 렌더 없이 검사만(종료 코드 1 = hard 위반)

먼저 `python -m geo.prep projects/<pid>`(지형), `python tools/fetch_ancient_geo.py projects/<pid> --bbox …`(고대 지명),
`python -m sketch.war.fetch projects/<pid>`(증거 카드 원본 — media.json 레코드의 Commons 파일). 검사 hard 위반이면 렌더하지 않는다(P6).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import ValidationError

from sketch.common.checks import CheckReport, SketchCheckError, spec_errors
from sketch.common.cli import base_parser, parse_frames
from sketch.common.render import base_provenance, render_video, sha1_file, write_frames, write_provenance
from sketch.common.spec import SPEC_FILE, DataFile, RenderRecord, load_spec
from sketch.war.checks import check_render, check_spec
from sketch.war.spec import WarSpec

FAIL = 1
OUT_DIR = "out"
STEM = "sketch_war"


def load_checked(project: Path) -> tuple[WarSpec | None, CheckReport]:
    report = CheckReport()
    try:
        spec = load_spec(project, WarSpec)
    except ValidationError as e:
        spec_errors(report, e)
        return None, report
    check_spec(report, spec, project)
    return spec, report


def data_files(spec: WarSpec, project: Path) -> list[DataFile]:
    from sketch.war.scene import MEDIA_DIR, load_media  # noqa: PLC0415

    out: list[DataFile] = []
    media = load_media(project)
    for e in spec.evidence:
        a = media[e.mid]
        f = project / MEDIA_DIR / (a.file or "")
        out.append(DataFile(path=f"{MEDIA_DIR}/{a.file}", sha1=sha1_file(f), source=a.url or "", license=a.license))
    pl = project / "ancient_geo" / "places.json"
    if pl.is_file() and any(p.pleiades for p in spec.places):
        src = json.loads((project / "ancient_geo" / "sources.json").read_text(encoding="utf-8"))
        row = next(r for r in src["layers"] if r["layer"] == "places")
        out.append(DataFile(path="ancient_geo/places.json", sha1=sha1_file(pl), source=f"{row['repo']}@{row['commit']} {row['path']}",
                            license=row["license"]))
    tp = project / "toponymy.yaml"
    if tp.is_file():
        out.append(DataFile(path="toponymy.yaml", sha1=sha1_file(tp), source="toponymy.yaml 레코드 출처 칸", license="사실 기록(출처 귀속)"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = base_parser("python -m sketch.war", "전쟁사 화면 스케치 — 시대 부호 세트·EraDate 뱃지·고대 기반 지도·전술 무대·증거 카드")
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
    from sketch.war.scene import WarScene  # noqa: PLC0415 — 검사만 할 때는 지형 자산을 읽지 않는다

    scene = WarScene(spec, project, args.res)
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
    prov.approximations = ["부대 위치·모양·이동: 사료 서술(spec sources)의 개략 — 크기·간격은 축척이 아니다",
                           "강 경로: 개략 선(spec rivers)", "지명 좌표: Pleiades 대표 좌표(있는 것) · 그 밖 개략"]
    prov.checks = report.record()
    print(write_provenance(prov, out))
    if report.hard:
        print(SketchCheckError(report.hard), file=sys.stderr)
        return FAIL
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
