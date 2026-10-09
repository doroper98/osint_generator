"""미사일 스케치 결정적 검사(D-0140 §4) — spec 단계(`--check`, 렌더 전)와 렌더 뒤 provenance 대조.

| ID | spec 단계 | 렌더 뒤 |
|---|---|---|
| SK-H1 | 자리표시가 다 채워지는가, 자유 문구의 단위 숫자가 허용 값인가 | numbers_shown 키가 포맷터 표 안인가 |
| SK-H2 | approx → uncertainty_km > 0(스키마) | 착탄 영역(impact_area)을 그렸는가 |
| SK-H3 | 비공개 자산 tag·범위(스키마) | 기준점을 그린 자산이 전부 위치 공개인가 |
| SK-H4 | 중첩 청구국 색 ≥ 2(스키마) | 한 색 사선이 없었는가 |
| SK-H5 | approx 층 설명 동안 출처 줄에 '개략', 엔딩 자료에 '개략' | — |
| SK-C1 | 카메라 연속성(D-0141) | — |
| SK-R1 | media 권리 기록 | — |
| SK-C2 | — | 라벨 예약 상자 겹침(warning) |
"""

from __future__ import annotations

from pathlib import Path

from engine.style import FPS
from rules import load_rules
from sketch.common.camera import CameraPath
from sketch.common.checks import CheckReport, check_camera, check_label_overlap, check_rights
from sketch.missile.numbers import Numbers
from sketch.missile.spec import MissileSpec, Sensor

SK = load_rules().sketch
MEDIA_DIR = "media"
TRACK_KEY = "track.distance_km"


def display_strings(spec: MissileSpec) -> list[tuple[str, str, Sensor | None]]:
    """화면에 나오는 spec 문구 전부(경로, 문자열, 자산 문맥)."""
    out: list[tuple[str, str, Sensor | None]] = [("title", spec.title, None), ("date", spec.date, None)]
    out += [(f"sources[{i}]", s.text, None) for i, s in enumerate(spec.sources)]
    n = spec.notes
    out += [(f"notes.source_lines[{i}]", s.text, None) for i, s in enumerate(n.source_lines)]
    out += [("notes.end_title", n.end_title, None), ("notes.end_note", n.end_note, None)]
    out += [("launch.label", spec.launch.label, None), ("launch.sub", spec.launch.sub, None)]
    tr = spec.track
    out += [("track.ref.name", tr.ref.name, None), ("track.hud.label", tr.hud.label, None),
            ("track.hud.range_line", tr.hud.range_line, None), ("track.hud.note", tr.hud.note, None),
            ("track.impact.label", tr.impact.label, None), ("track.impact.sub", tr.impact.sub, None),
            ("track.impact.tag", tr.impact.tag, None)]
    for i, s in enumerate(spec.sensors):
        out += [(f"sensors[{i}].{k}", v, s) for k, v in (("name", s.name), ("sub", s.sub), ("tag", s.tag)) if v]
    for k, ag in spec.announced.items():
        out += [(f"announced.{k}.who", ag.who, None)] + [(f"announced.{k}.rows[{j}]", r, None) for j, r in enumerate(ag.rows)]
    e = spec.eez
    out += [(f"eez.nations.{c}.label", nt.label, None) for c, nt in e.nations.items()]
    for i, r in enumerate(e.regions):
        out += [(f"eez.regions[{i}].label", r.label, None), (f"eez.regions[{i}].sub", r.sub, None)]
    for i, c in enumerate(e.claim_lines):
        out += [(f"eez.claim_lines[{i}].label", c.label, None), (f"eez.claim_lines[{i}].sub", c.sub, None)]
        if c.ext_tag:
            out.append((f"eez.claim_lines[{i}].ext_tag", c.ext_tag.text, None))
    if e.places:
        out += [(f"eez.places[{i}]", p.name, None) for i, p in enumerate(e.places.items)]
    out += [(f"media[{i}]", f"{m.caption} {m.credit}", None) for i, m in enumerate(spec.media)]
    if spec.card:
        out += [("card.title", spec.card.title, None), ("card.sub", spec.card.sub, None)]
    if spec.profile:
        p = spec.profile
        out += [(f"profile.{k}", v, None) for k, v in (("title", p.title), ("sub", p.sub), ("alt_axis", p.alt_axis),
                                                       ("range_axis", p.range_axis), ("apex_label", p.apex_label),
                                                       ("note", p.note), ("reference.label", p.reference.label))]
    return out


def check_spec(report: CheckReport, spec: MissileSpec, project: Path) -> Numbers:
    """렌더 전 검사(SK-H1·H5·C1·R1). 스키마 단계 H2·H3·H4 는 spec 로드에서 이미 걸렸다 — 통과 기록만."""
    th = SK.checks
    nums = Numbers(spec)
    report.ran_check("SK-H1")
    for path, s, sensor in display_strings(spec):
        for key in nums.placeholders_ok(s, sensor):
            report.add("SK-H1", f"{path}: 자리표시 {{{key}}} 를 채울 발표값이 없다")
        for tok in nums.free_text_violations(s):
            report.add("SK-H1", f"{path}: {tok!r} — 발표·사양 값(announced·track·sensors.range_km)에 없는 숫자")
    for cid in ("SK-H2", "SK-H3", "SK-H4"):
        report.ran_check(cid)
    # SK-H5 — approx 층(예: NLL 개략 재구성)이 라벨로 설명되는 동안 출처 줄에 '개략', 엔딩 자료에도
    report.ran_check("SK-H5")
    word = th.approx_word
    approx = [c for c in spec.eez.claim_lines if c.approx]
    for c in approx:
        start = c.t + SK.eez.claim_label_delay
        cover = [n for n in spec.notes.source_lines if word in n.text and n.t0 <= start and n.t1 >= c.end]
        if not cover:
            report.add("SK-H5", f"{c.code}: approx 층 설명 {start:.1f}~{c.end:.1f}s 동안 '{word}' 출처 줄이 없다")
    if approx and not any(word in s.text for s in spec.sources):
        report.add("SK-H5", f"approx 층({', '.join(c.code for c in approx)})이 있는데 엔딩 자료(sources)에 '{word}' 이 없다")
    cam = SK.camera
    path = CameraPath(tuple(spec.shots), spec.duration_sec, cam.push_in[spec.kind], cam.hold_min_sec)
    check_camera(report, path.track(FPS), FPS, th)
    check_rights(report, project / MEDIA_DIR, spec.media, SK.rights.allowed_licenses)
    return nums


def check_render(report: CheckReport, spec: MissileSpec, drawn: dict[str, int], nums: Numbers,
                 boxes: list[tuple[float, list]], covered_until: float) -> None:
    """렌더 뒤 provenance 대조(SK-H1·H2·H3·H4) + 라벨 겹침(SK-C2). covered_until = 렌더한 마지막 시각."""
    allowed = set(nums.table) | {f"sensor.range_km:{s.name}" for s in spec.sensors if s.range_km is not None}
    for key in nums.shown:
        if key not in allowed:
            report.add("SK-H1", f"화면 숫자 {key} 가 포맷터 표 밖")
    if spec.track.approx and covered_until > spec.track.t1 and not drawn.get("impact_area"):
        report.add("SK-H2", "track.approx 인데 착탄 영역(impact_area)을 그리지 않았다")
    public = {s.name for s in spec.sensors if s.location_public}
    for k in drawn:
        if k.startswith("sensor_point:") and k.split(":", 1)[1] not in public:
            report.add("SK-H3", f"위치 비공개 자산 {k.split(':', 1)[1]} 의 기준점을 그렸다")
    if drawn.get("overlap_hatch_colors:1"):
        report.add("SK-H4", "중첩 수역을 한 색 사선으로 그렸다")
    check_label_overlap(report, boxes, SK.checks)
