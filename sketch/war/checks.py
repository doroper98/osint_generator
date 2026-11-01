"""전쟁사 스케치 검사(v7.4.0 W3·W4) — 공통 SK 검사 + 전쟁사 판정(schemas.war_history, 엔진 검사와 같은 함수 — C12-3).

| ID | 등급 | 검사 |
|---|---|---|
| SK-H1 | hard | 화면 문구(이름·지명·태그·출처·인용)에 단위 붙은 숫자 없음 |
| SK-H5 | hard | 부대·경로·지명(개략)이 보이는 전 구간에 '개략' 출처 줄, 엔딩 자료에도 |
| SK-C1 | hard | 카메라 연속성·무대 경계(작전 지도 ↔ 전술 무대 = 같은 좌표계 확대) |
| SK-W1 | hard | [symbol-set-mixed] — 이 스케치 시대의 부호 세트 밖 부호 |
| SK-W2 | hard | [period-art-label-missing] — 작품 카드마다 당대/후대 라벨·미술사 한 문장·출처 |
| SK-W3 | warning | [evidence-layer-missing] — 시대별 필수 증거 층 중 이 스케치에 없는 층(스케치는 몇 컷이라 경고, 본편은 hard) |
| SK-W4 | hard | 지명 Pleiades id·지명 유래 id 가 자료에 있다(출처 없는 좌표·유래 금지) |
| SK-R1 | hard | 증거 카드 레코드(media.json, MediaAsset)·파일·md5, 라이선스 = rules war_history.rights |
| SK-E1 | hard | 엔딩 자료 줄 수·폭 |
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pydantic import ValidationError

from engine.style import FPS
from schemas.era_date import parse_era_date
from schemas.war_history import asset_layers, era_of, evidence_missing, period_art_label, symbol_set_mixed
from sketch.common.camera import CameraPath, bounds_stage
from sketch.common.checks import CheckReport, check_camera, check_end_card, check_label_overlap
from sketch.common.draw import SK
from sketch.common.numbers import unit_numbers
from sketch.war.scene import MEDIA_DIR, date_at, load_media, load_places
from sketch.war.spec import WarSpec


def display_strings(spec: WarSpec) -> list[tuple[str, str]]:
    out = [("title", spec.title)]
    out += [(f"units[{i}].name", u.name) for i, u in enumerate(spec.units) if u.name]
    out += [(f"places[{i}]", p.name) for i, p in enumerate(spec.places)]
    out += [(f"routes[{i}]", r.name) for i, r in enumerate(spec.routes)]
    out += [(f"quotes[{i}]", q.text) for i, q in enumerate(spec.quotes)]
    out += [(f"source_lines[{i}]", n.text) for i, n in enumerate(spec.notes.source_lines)]
    out += [(f"sources[{i}]", s.text) for i, s in enumerate(spec.sources)]
    out += [(f"factions.{k}", f.name) for k, f in spec.factions.items()]
    return out


def used_layers(spec: WarSpec, media: dict) -> set[str]:
    used = {lay for e in spec.evidence if e.mid in media for lay in asset_layers(media[e.mid])}
    if any(p.toponymy for p in spec.places):
        used.add("toponymy")
    return used


def check_spec(report: CheckReport, spec: WarSpec, project: Path) -> None:
    th = SK.checks
    report.ran_check("SK-H1")
    for path, s in display_strings(spec):
        for tok, _, _ in unit_numbers(s):
            report.add("SK-H1", f"{path}: {tok!r} — 화면 문구에 단위 수치를 쓰지 않는다(병력은 엔딩 자료 범위로도 이 스케치에서는 쓰지 않음)")
    report.ran_check("SK-H5")
    word = th.approx_word
    end_t0 = spec.duration_sec - spec.notes.end_sec
    need0, need1 = SK.fade.open_sec, end_t0 - th.approx_note_end_gap_sec
    if (spec.units or spec.routes) and not any(word in n.text and n.t0 <= need0 and n.t1 >= need1 for n in spec.notes.source_lines):
        report.add("SK-H5", f"부대·경로(개략)가 보이는 {need0:.1f}~{need1:.1f}s 전 구간에 '{word}' 출처 줄이 없다")
    if not any(word in s.text for s in spec.sources):
        report.add("SK-H5", f"엔딩 자료(sources)에 '{word}' 이 없다")
    cam = SK.camera
    path = CameraPath(tuple(spec.shots), spec.duration_sec, cam.push_in[spec.kind], cam.hold_min_sec)
    check_camera(report, path.track(FPS), FPS, th, bounds_stage(project))
    era = era_of(spec.dates[0].date)
    report.ran_check("SK-W1")
    for m in symbol_set_mixed(era, [u.symbol for u in spec.units]):
        report.add("SK-W1", m)
    report.ran_check("SK-R1")
    try:
        media = load_media(project)
    except (ValidationError, ValueError) as ex:
        report.add("SK-R1", f"media.json 레코드 오류: {ex}")
        media = {}
    for e in spec.evidence:
        a = media.get(e.mid)
        if a is None:
            report.add("SK-R1", f"evidence {e.mid}: media.json 에 없다")
            continue
        f = project / MEDIA_DIR / (a.file or "")
        if not f.is_file():
            report.add("SK-R1", f"{e.mid}: 파일 없음 {f} — python -m sketch.war.fetch {project}")
        elif hashlib.md5(f.read_bytes()).hexdigest() != a.source_hash:
            report.add("SK-R1", f"{e.mid}: 파일 md5 ≠ 레코드 source_hash")
        if a.rights_status != "rights_clear":
            report.add("SK-R1", f"{e.mid}: rights_status {a.rights_status}")
    report.ran_check("SK-W2")
    for e in spec.evidence:
        a = media.get(e.mid)
        if a is None or a.kind != "period_art":
            continue
        if period_art_label(a.created, parse_era_date(date_at(spec, e.t0))) is None:
            report.add("SK-W2", f"[period-art-label-missing] {e.mid} — 당대/후대 라벨을 못 만든다(created={a.created})")
        if not (a.art_history and a.art_history_source):
            report.add("SK-W2", f"[period-art-label-missing] {e.mid} — 미술사 한 문장·출처 없음")
    report.ran_check("SK-W3")
    for m in evidence_missing(era, used_layers(spec, media)):
        report.warn("SK-W3", m)
    report.ran_check("SK-W4")
    places = load_places(project)
    from schemas.war_history import load_toponymy  # noqa: PLC0415

    topo = load_toponymy(project)
    tids = set(topo.by_id()) if topo is not None else set()
    for p in spec.places:
        if p.pleiades is not None and p.pleiades not in places:
            report.add("SK-W4", f"지명 {p.name}: Pleiades id {p.pleiades} 가 ancient_geo/places.json 에 없다 — python tools/fetch_ancient_geo.py")
        if p.toponymy and p.toponymy not in tids:
            report.add("SK-W4", f"지명 {p.name}: 유래 레코드 {p.toponymy!r} 가 toponymy.yaml 에 없다")
    report.ran_check("SK-R1")
    if spec.ancient_roads_t:
        import json  # noqa: PLC0415

        sp = project / "ancient_geo" / "sources.json"
        row = next((r for r in json.loads(sp.read_text(encoding="utf-8"))["layers"] if r["layer"] == "roads"), None) if sp.is_file() else None
        if row is None or row.get("status") != "ok":
            report.add("SK-R1", "ancient_roads_t 인데 ancient_geo/roads.json 이 받아지지 않았다 — python tools/fetch_ancient_geo.py … --date")
        elif not any(row["attribution"] in s.text for s in spec.sources):
            report.add("SK-R1", f"AWMC 가도를 그리는데 엔딩 자료에 고지 {row['attribution']!r} 가 없다(D-0601 ① b)")
    E, Ln = SK.war.end, SK.text.end_line
    check_end_card(report, [s.text for s in spec.sources], E.x, Ln.y0, Ln.dy, E.line_size, Ln.font, E.note_y)


def check_render(report: CheckReport, boxes: list[tuple[float, list]]) -> None:
    check_label_overlap(report, boxes, SK.checks)
