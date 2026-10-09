"""미사일 스케치 결정적 검사(D-0140 §4) — spec 단계(`--check`, 렌더 전)와 렌더 뒤 provenance 대조.

| ID | spec 단계 | 렌더 뒤 |
|---|---|---|
| SK-H1 | 자리표시가 다 채워지는가, 자유 문구의 단위 숫자가 허용 값인가, track.flight_sec(시계) = announced sec 값(없으면 min × 60, D-0149) | numbers_shown 키가 포맷터 표 안인가(시계 = 원천 키) |
| SK-H2 | approx → uncertainty_km > 0(스키마) | 착탄 영역(impact_area)을 그렸는가 |
| SK-H3 | 비공개 자산 tag·범위(스키마) | 기준점을 그린 자산이 전부 위치 공개인가 |
| SK-H4 | 중첩 청구국 색 ≥ 2(스키마) | 한 색 사선이 없었는가 |
| SK-H5 | approx 층 설명 동안 출처 줄에 '개략', 엔딩 자료에 '개략' | — |
| SK-C1 | 카메라 연속성(D-0141) | — |
| SK-R1 | media 권리 기록 | — |
| SK-C2 | — | 라벨 예약 상자 겹침(warning) |

3D 전환편(`--globe`, D-0143): SK-C1(3D, D135) = 발사점·착탄점 화면 궤적 2차 차분 + 초점 거리 Δ ln f, 2D 구간은 S1 카메라 검사.
SK-H6(D136) = 수평선 패널 주석(spec globe.panel.note) 필수 + 패널 값 = horizon_altitude(gc_dist) ± checks.horizon_tol_km.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from engine.style import FPS, Output
from rules import load_rules
from sketch.common.camera import CameraPath
from sketch.common.checks import CheckReport, check_camera, check_label_overlap, check_rights
from sketch.common.geodesy import dest, gc_dist, horizon_altitude, to_local
from sketch.missile.globe import CameraPath3D, Keys, visible
from sketch.missile.numbers import Numbers, flight_source
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
    src, cands = flight_source(spec)
    if src is None:
        report.add("SK-H1", f"track.flight_sec {spec.track.flight_sec} — 비행 경과 시계의 원천이 될 발표값이 없다"
                            f"(announced sec 값, 없으면 min × 60; 후보 {cands or '없음'})")
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
    _shown_in_table(report, spec, nums)
    if spec.track.approx and covered_until > spec.track.t1 and not drawn.get("impact_area"):
        report.add("SK-H2", "track.approx 인데 착탄 영역(impact_area)을 그리지 않았다")
    public = {s.name for s in spec.sensors if s.location_public}
    for k in drawn:
        if k.startswith("sensor_point:") and k.split(":", 1)[1] not in public:
            report.add("SK-H3", f"위치 비공개 자산 {k.split(':', 1)[1]} 의 기준점을 그렸다")
    if drawn.get("overlap_hatch_colors:1"):
        report.add("SK-H4", "중첩 수역을 한 색 사선으로 그렸다")
    check_label_overlap(report, boxes, SK.checks)


def _shown_in_table(report: CheckReport, spec: MissileSpec, nums: Numbers) -> None:
    """SK-H1 렌더 뒤 — 화면에 채운 숫자 키가 포맷터 표(발표·track·profile·상수) 또는 그 자산의 sensor.* 값인가."""
    names = {s.name for s in spec.sensors}
    for key in nums.shown:
        base, _, who = key.partition(":")
        if key in nums.table or (base.startswith("sensor.") and who in names):
            continue
        if key == nums.clock_key() and nums.clock_source is not None:
            continue
        report.add("SK-H1", f"화면 숫자 {key} 가 포맷터 표 밖")


# ---------------------------------------------------------------- 3D 전환편(D-0143)
def globe_path(spec: MissileSpec, out: Output) -> CameraPath3D:
    g = spec.globe
    assert g is not None
    last = spec.shots[-1]
    keys = Keys(g.t_2d, g.t_x, g.t_k0, g.t_k1, g.t_side0, g.t_side1, g.t_fly0, g.t_fly1, g.duration_sec)
    return CameraPath3D(keys, last.lat, last.w * (1 - SK.camera.push_in[spec.kind]), out.width, out.height)


def globe_anchor_track(spec: MissileSpec, path: CameraPath3D, fps: int) -> tuple[list[float], np.ndarray, np.ndarray, np.ndarray]:
    """3D 구간(t ≥ t_2d) 프레임마다 발사점·착탄점 화면 좌표(n×2×2)·보임(n×2)·초점 거리(n)."""
    g = spec.globe
    assert g is not None
    tr = spec.track
    imp = dest(tr.ref.lon, tr.ref.lat, tr.bearing_deg, tr.distance_km)
    lon, lat = np.array([spec.launch.lon, imp[0]]), np.array([spec.launch.lat, imp[1]])
    ts = [i / fps for i in range(int(g.duration_sec * fps)) if i / fps >= g.t_2d]
    S, V, Fl = [], [], []
    for t in ts:
        k = path.k_at(max(t, g.t_k0))
        cam = path.cam(t)
        P = to_local(tuple(g.center), lon, lat, np.zeros(2), k)   # type: ignore[arg-type]
        sc, front = cam.project(P)
        S.append(sc)
        V.append(front & visible(cam, P, k))
        Fl.append(cam.f)
    return ts, np.array(S), np.array(V), np.array(Fl)


def check_camera_3d(report: CheckReport, ts: list[float], S: np.ndarray, V: np.ndarray, Fl: np.ndarray, width: int) -> dict[str, float]:
    """SK-C1(3D, D135) — 보이는 구간의 기준점 화면 궤적 |Δ² px|/W·|Δ² py|/W ≤ max_d2logw_per_frame, |Δ ln f| ≤ max_dlogw_per_frame."""
    th = SK.checks
    report.ran_check("SK-C1")
    worst = {"dlnf": float(np.abs(np.diff(np.log(Fl))).max(initial=0))}
    if worst["dlnf"] > th.max_dlogw_per_frame:
        report.add("SK-C1", f"3D 초점 거리 |Δ ln f| {worst['dlnf']:.4f} > {th.max_dlogw_per_frame}")
    for j, name in enumerate(("발사점", "착탄점")):
        d2 = np.abs(np.diff(S[:, j, :], 2, axis=0)) / width
        ok = V[2:, j] & V[1:-1, j] & V[:-2, j]
        if not ok.any():
            continue
        m = d2[ok].max(axis=1)
        worst[f"d2 {name}"] = float(m.max())
        bad = np.flatnonzero(m > th.max_d2logw_per_frame)
        if bad.size:
            t_bad = np.array(ts[1:-1])[ok][bad]
            report.add("SK-C1", f"3D {name} 화면 궤적 |Δ²|/W {m.max():.4f} > {th.max_d2logw_per_frame} — "
                                f"{bad.size}프레임(첫 t={t_bad[0]:.2f}s, 속도 급변)")
    return worst


def check_globe_spec(report: CheckReport, spec: MissileSpec, out: Output) -> dict[str, float]:
    """렌더 전 3D 검사 — SK-C1(2D 이어받기 구간 + 3D 기준점 궤적), SK-H6(패널 주석)."""
    g = spec.globe
    assert g is not None
    cam = SK.camera
    flat = CameraPath(tuple(spec.shots), spec.duration_sec, cam.push_in[spec.kind], cam.hold_min_sec)
    rate = SK.globe.handoff_rate
    n2 = [i / FPS for i in range(int(g.duration_sec * FPS)) if i / FPS < g.t_2d]
    worst = check_camera(report, np.array([flat.at(g.handoff_2d_t + t * rate) for t in n2]), FPS, SK.checks) if len(n2) > 2 else {}
    worst |= check_camera_3d(report, *globe_anchor_track(spec, globe_path(spec, out), FPS), out.width)
    report.ran_check("SK-H6")
    if not g.panel.note.strip():
        report.add("SK-H6", "수평선 패널 주석(globe.panel.note)이 없다 — 기하 계산값은 '지구 곡률만 계산 · 굴절·탐지 성능과 별개' 주석과 같은 창에(D136)")
    return worst


def check_globe_render(report: CheckReport, spec: MissileSpec, nums: Numbers, drawn: dict[str, int]) -> None:
    """렌더 뒤 — SK-H6 패널 값 재계산 대조 + 주석을 패널과 함께 그렸는가, SK-H1 화면 숫자 표."""
    th = SK.checks
    launch = (spec.launch.lon, spec.launch.lat)
    for s in spec.sensors:
        c = nums.computed_log.get(f"horizon.altitude_km:{s.name}")
        if c is None:
            continue
        want = horizon_altitude(gc_dist((s.lon, s.lat), launch))
        if abs(c.value - want) > th.horizon_tol_km:
            report.add("SK-H6", f"{s.name}: 패널 고도 {c.value:.2f} km ≠ 수평선 식 {want:.2f} km(± {th.horizon_tol_km})")
    if drawn.get("horizon_panel") and drawn.get("horizon_panel_note", 0) < drawn["horizon_panel"]:
        report.add("SK-H6", "수평선 패널을 주석 없이 그린 프레임이 있다")
    _shown_in_table(report, spec, nums)
