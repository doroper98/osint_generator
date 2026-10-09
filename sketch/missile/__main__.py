"""미사일 발사 사건 스케치 CLI(D-0140 §3).

    python -m sketch.missile projects/<pid>                 # 2D → out/sketch_2d.mp4 · sketch_2d_sheet.jpg · sketch_provenance.json
    python -m sketch.missile projects/<pid> --globe         # 3D 전환편 → out/sketch_globe.mp4 · sketch_globe_sheet.jpg · provenance
    python -m sketch.missile projects/<pid> --frames 5,27   # 정지 화면 → out/sketch_2d_005.0.png …
    python -m sketch.missile projects/<pid> --check         # 렌더 없이 검사만(종료 코드 1 = hard 위반)

검사 hard 위반이면 렌더하지 않는다(SketchCheckError, P6). 렌더 뒤 provenance 대조 검사도 hard 면 실패한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import ValidationError

from sketch.common.checks import CheckReport, SketchCheckError, spec_errors
from sketch.common.cli import base_parser, parse_frames
from sketch.common.render import base_provenance, render_video, sha1_file, write_frames, write_provenance
from sketch.common.spec import SPEC_FILE, DataFile, RenderRecord, load_spec
from engine.style import output_profile
from sketch.missile.checks import MEDIA_DIR, check_globe_render, check_globe_spec, check_render, check_spec
from sketch.missile.spec import MissileSpec

FAIL = 1
OUT_DIR = "out"
STEM = "sketch_2d"
STEM_GLOBE = "sketch_globe"
KIND_GLOBE = "missile_globe"


def load_checked(project: Path) -> tuple[MissileSpec | None, CheckReport]:
    """spec 로드 + 렌더 전 검사. 스키마 위반도 SK 번호로 보고한다."""
    report = CheckReport()
    try:
        spec = load_spec(project, MissileSpec)
    except ValidationError as e:
        spec_errors(report, e)
        return None, report
    check_spec(report, spec, project)
    return spec, report


def approximations(spec: MissileSpec) -> list[str]:
    out = []
    if spec.track.approx:
        out.append(f"착탄: {spec.track.ref.name} 기준 발표 거리('약') → 반경 {spec.track.uncertainty_km:g}km 영역")
    out += [f"{c.code}: {c.sub}" for c in spec.eez.claim_lines if c.approx]
    out += [f"{s.name}: {s.tag}" for s in spec.sensors if s.tag]
    return out


def data_files(spec: MissileSpec, project: Path, eez_source: str) -> list[DataFile]:
    import json  # noqa: PLC0415

    out = [DataFile(path=spec.eez.file, sha1=sha1_file(project / spec.eez.file), source=eez_source, license=spec.eez.prep.license)]
    rights = json.loads((project / MEDIA_DIR / "RIGHTS.json").read_text(encoding="utf-8"))["files"] if spec.media else {}
    for m in spec.media:
        p = project / MEDIA_DIR / m.file
        out.append(DataFile(path=f"{MEDIA_DIR}/{m.file}", sha1=sha1_file(p), source=rights[m.file]["source_url"], license=m.license))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = base_parser("python -m sketch.missile", "미사일 발사 사건 화면 스케치 — EEZ·탐지 자산·궤적·착탄·고도 단면(2D), 지구본 전환(3D)")
    ap.add_argument("--globe", action="store_true", help="2D → 3D 지구본 전환편")
    args = ap.parse_args(argv)
    project: Path = args.project
    spec, report = load_checked(project)
    if args.globe and spec is not None:
        if spec.globe is None:
            print("spec 에 globe 블록이 없다 — 3D 전환편을 만들 수 없다", file=sys.stderr)
            return FAIL
        check_globe_spec(report, spec, output_profile(args.res))
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
    from sketch.missile.scene import MissileScene  # noqa: PLC0415 — 검사만 할 때는 지형 자산을 읽지 않는다

    scene = MissileScene(spec, project, args.res)
    out = project / OUT_DIR
    times = parse_frames(args.frames)
    if args.globe:
        return run_globe(spec, project, scene, report, times, out)
    prov = base_provenance(spec.kind, project / SPEC_FILE)
    if times:
        paths = write_frames(scene, times, out, STEM)
        rec = RenderRecord(profile=scene.out.name, frames=len(paths), duration_sec=0, elapsed_sec=0)
        covered = max(times)
        for p in paths:
            print(p)
    else:
        mp4, sheet, rec = render_video(scene, spec.duration_sec, spec.sheet_times, out, STEM)
        covered = spec.duration_sec
        print(mp4, sheet)
    check_render(report, spec, scene.features_drawn(), scene.nums, scene.overlap_boxes, covered)
    prov.render = rec
    prov.data_files = data_files(spec, project, scene.eez.source)
    prov.features_drawn = scene.features_drawn()
    prov.approximations = approximations(spec)
    prov.numbers_shown = [f"{k}={v}" for k, v in sorted(scene.nums.shown.items())]
    prov.checks = report.record()
    print(write_provenance(prov, out))
    for f in report.warnings:
        print(f"{f.id} {f.message}", file=sys.stderr)
    if report.hard:
        print(SketchCheckError(report.hard), file=sys.stderr)
        return FAIL
    return 0


def run_globe(spec: MissileSpec, project: Path, flat: "MissileScene", report: CheckReport, times: list[float],  # noqa: F821
              out: Path) -> int:
    """3D 전환편 — 2D 장면을 handoff_2d_t 에서 이어받아 교차 전환(CrossfadeScene) 뒤 지구본."""
    from sketch.common.render import CrossfadeScene  # noqa: PLC0415
    from sketch.missile.globe_scene import G, GlobeScene  # noqa: PLC0415

    g = spec.globe
    assert g is not None
    gs = GlobeScene(spec, project, flat)
    scene = CrossfadeScene(flat, gs, lambda t: g.handoff_2d_t + t * G.handoff_rate, g.t_2d, g.t_x, g.duration_sec,
                           G.fade_open, G.fade_close)
    prov = base_provenance(KIND_GLOBE, project / SPEC_FILE)
    if times:
        paths = write_frames(scene, times, out, STEM_GLOBE)
        rec = RenderRecord(profile=scene.out.name, frames=len(paths), duration_sec=0, elapsed_sec=0)
        for p in paths:
            print(p)
    else:
        mp4, sheet, rec = render_video(scene, g.duration_sec, g.sheet_times, out, STEM_GLOBE)
        print(mp4, sheet)
    drawn = dict(flat.features_drawn())
    for k_, v in gs.drawn.items():
        drawn[k_] = drawn.get(k_, 0) + v
    check_globe_render(report, spec, flat.nums, gs.drawn)
    prov.render = rec
    prov.data_files = data_files(spec, project, flat.eez.source)
    prov.features_drawn = drawn
    prov.approximations = approximations(spec) + [f"{s.name}: 3D 방위·고각 = 개념값" for s in spec.sensors if s.el_deg]
    prov.numbers_shown = [f"{k_}={v}" for k_, v in sorted(flat.nums.shown.items())]
    prov.numbers_computed = sorted(flat.nums.computed_log.values(), key=lambda c: c.key)
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
