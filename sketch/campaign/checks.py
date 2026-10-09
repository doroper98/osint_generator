"""전황 작전도 결정적 검사(D-0140 §4, D-0145).

| ID | 내용 |
|---|---|
| SK-G1 | fronts.json 정합 잔차 ≤ checks.georef_residual_deg(없으면 prep_georef 먼저) |
| SK-G2 | 포위망 레시피 다각형 shapely valid·면적 > 0. 미세 자기 교차 조각 비율 ≤ checks.pocket_sliver_ratio 면 warning(D-0146) |
| SK-G3 | 제대·병종(스키마 단계) |
| SK-H5 | approx 층(전선 전부·부대 위치) — '개략' 출처 줄이 화면이 열린 뒤 ~ 엔딩 직전 전 구간, 엔딩 자료에 '개략' |
| SK-H1 | 화면 문구에 단위 붙은 숫자 없음(발표값 표가 없는 전황 — 병력 수치는 엔딩 자료 범위로만) |
| SK-R1 | 참고 작전도·media 권리(프로젝트 RIGHTS.json, D139) |
| SK-C1 | 카메라 연속성 |
| SK-C2 | 부대·집게 예약 상자 겹침(warning, 렌더 뒤) |
"""

from __future__ import annotations

from pathlib import Path

from shapely.geometry import Polygon
from shapely.validation import explain_validity, make_valid

from engine.style import FPS
from rules import load_rules
from sketch.campaign.fronts import FrontData
from sketch.campaign.pockets import build_polygon
from sketch.campaign.spec import CampaignSpec
from sketch.common.camera import CameraPath
from sketch.common.checks import CheckReport, check_camera, check_label_overlap, check_rights, check_rights_files
from sketch.common.numbers import unit_numbers

SK = load_rules().sketch
MEDIA_DIR = "media"


def display_strings(spec: CampaignSpec) -> list[tuple[str, str]]:
    out = [("title", spec.title), ("date", spec.date)]
    out += [(f"sources[{i}]", s.text) for i, s in enumerate(spec.sources)]
    out += [(f"notes.source_lines[{i}]", s.text) for i, s in enumerate(spec.notes.source_lines)]
    out += [("notes.end_title", spec.notes.end_title), ("notes.end_note", spec.notes.end_note)]
    out += [(f"nations.{k}.label", n.label) for k, n in spec.nations.items()]
    out += [(f"units[{i}].name", u.name) for i, u in enumerate(spec.units)]
    if spec.arrows:
        out += [(f"arrows[{i}].name", a.name) for i, a in enumerate(spec.arrows.items)]
    out += [(f"places[{i}]", f"{p.name} {p.now or ''}") for i, p in enumerate(spec.places)]
    out += [(f"rivers_label[{i}]", r.name) for i, r in enumerate(spec.rivers_label)]
    out += [(f"dates[{i}]", d.text) for i, d in enumerate(spec.dates)]
    out += [(f"tags[{i}]", tg.text) for i, tg in enumerate(spec.tags)]
    if spec.pincer:
        out.append(("pincer.text", spec.pincer.text))
    if spec.legend:
        out.append(("legend.caption", spec.legend.caption))
    out += [(f"pockets[{i}].name", p.name) for i, p in enumerate(spec.pockets)]
    return out


def pocket_validity(report: CheckReport, name: str, poly: Polygon, ratio: float) -> None:
    """SK-G2(D-0146) — valid 면 통과. invalid 면 make_valid 뒤 가장 큰 다각형 밖 면적 ÷ 전체 ≤ ratio 일 때 warning, 넘거나 면적 0 이면 hard.
    그리기는 레시피 그대로(검사와 화면 분리)."""
    if poly.is_empty or poly.area <= 0:
        report.add("SK-G2", f"{name}: 포위망 면적 0")
        return
    if poly.is_valid:
        report.ran_check("SK-G2")
        return
    mv = make_valid(poly)
    parts = sorted((g for g in getattr(mv, "geoms", [mv]) if g.geom_type == "Polygon" and g.area > 0), key=lambda g: -g.area)
    total = sum(g.area for g in parts)
    if not parts or total <= 0:
        report.add("SK-G2", f"{name}: 포위망 다각형을 복구할 수 없다({explain_validity(poly)})")
        return
    rest = total - parts[0].area
    frac = rest / total
    where = explain_validity(poly)
    if frac <= ratio:
        report.warn("SK-G2", f"{name}: 미세 자기 교차 조각 {len(parts) - 1}개 · {rest:.2e} deg² (전체의 {frac:.1e}) — {where}")
    else:
        report.add("SK-G2", f"{name}: 자기 교차 — 큰 다각형 밖 조각 비율 {frac:.3f} > {ratio}({where})")


def check_spec(report: CheckReport, spec: CampaignSpec, project: Path) -> FrontData | None:
    th = SK.checks
    # SK-H1 — 전황 화면에는 발표 수치 표가 없다: 단위 붙은 숫자는 문구 어디에도 없어야 한다(엔딩 자료 포함)
    report.ran_check("SK-H1")
    for path, s in display_strings(spec):
        for tok, _, _ in unit_numbers(s):
            report.add("SK-H1", f"{path}: {tok!r} — 전황 화면에 단위 수치를 쓰지 않는다(발표값 포맷터 없음)")
    report.ran_check("SK-G3")       # 제대·병종은 스키마에서 걸렸다
    # SK-G1
    report.ran_check("SK-G1")
    fpath = project / spec.fronts.file
    data = None
    if not fpath.is_file():
        report.add("SK-G1", f"{fpath} 없음 — python -m sketch.campaign.prep_georef {project} 먼저")
    else:
        data = FrontData(fpath)
        if data.residual_deg > th.georef_residual_deg:
            report.add("SK-G1", f"정합 잔차 {data.residual_deg:.4f}° > {th.georef_residual_deg}°")
    # SK-G2 + 조각 참조
    report.ran_check("SK-G2")
    if data is not None:
        for L in spec.fronts.layers:
            for ref in L.pieces:
                try:
                    data.piece(ref)
                except KeyError as e:
                    report.add("SK-SPEC", str(e))
        for p in spec.pockets:
            try:
                poly = Polygon(build_polygon(p, data))
            except (KeyError, ValueError) as e:
                report.add("SK-G2", f"{p.name}: 레시피를 다각형으로 만들 수 없다 — {e}")
                continue
            pocket_validity(report, p.name, poly, th.pocket_sliver_ratio)
    # SK-H5
    report.ran_check("SK-H5")
    word = th.approx_word
    end_t0 = spec.duration_sec - spec.notes.end_sec
    need0, need1 = SK.fade.open_sec, end_t0 - th.approx_note_end_gap_sec
    if not any(word in n.text and n.t0 <= need0 and n.t1 >= need1 for n in spec.notes.source_lines):
        report.add("SK-H5", f"전선·부대 위치(개략)가 보이는 {need0:.1f}~{need1:.1f}s 전 구간에 '{word}' 출처 줄이 없다")
    if not any(word in s.text for s in spec.sources):
        report.add("SK-H5", f"엔딩 자료(sources)에 '{word}' 이 없다")
    # SK-C1
    cam = SK.camera
    path = CameraPath(tuple(spec.shots), spec.duration_sec, cam.push_in[spec.kind], cam.hold_min_sec)
    check_camera(report, path.track(FPS), FPS, th)
    # SK-R1 — 참고 작전도(데이터 파일, D139) + media
    ref = spec.fronts.reference
    check_rights_files(report, project / ref.rights, [(ref.file, project / ref.file)], SK.rights.allowed_licenses)
    if spec.media:
        check_rights(report, project / MEDIA_DIR, spec.media, SK.rights.allowed_licenses)
    return data


def check_render(report: CheckReport, boxes: list[tuple[float, list]]) -> None:
    check_label_overlap(report, boxes, SK.checks)
