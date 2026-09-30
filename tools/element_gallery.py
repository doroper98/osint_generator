"""요소 갤러리 (v4.2.0, docs/handoff/20 §12 G2, back_and_forth D-0081 작업 6) — 등록 요소 전부를 실제 엔진으로 한 장씩 + 컨택트 시트.

    python tools/element_gallery.py --proj projects/hormuz_korea --out docs/handoff/reports/phaseG2/gallery

대상 = rules registries 의 등록 요소 전부: event_types(운반 타입 panel·primitive·badge 포함) · panel_kinds · badge_kinds · primitives.
예제 = prompts/examples/{events,panels,badges}/<이름>.yaml 의 event, 프리미티브는 모듈 PREVIEW_FIXTURE.
운반 타입은 대표 예제로 그린다: panel → panels/relation, badge → badges/person, primitive → 첫 등록 프리미티브.
예제가 없거나 모델을 통과하지 못하면 오류로 끝난다(빠진 예제 0 이 합격 조건, P6·P10). `--only` 는 확인용(합격 판정은 전체).

그리는 시각 = 예제 gallery.t, 없으면 t1 − 1(표시 3초 초과) 또는 가운데. 카메라 = 그 시각 프로젝트 카메라(예제 시각은 hormuz 연출의
실제 시각). 색 의미가 필요한 요소(프리미티브)는 그 요소를 쓰는 장르 프로필(기본 장르 우선)로 그린다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402

from engine.primitives import module  # noqa: E402
from engine.project import load_project, prepare_series  # noqa: E402
from engine.stage import make_stage  # noqa: E402
from engine.sheet import grid  # noqa: E402
from engine.registry import MAP_LAYER_ORDER, resolve  # noqa: E402
from engine.style import FPS, ISLAND  # noqa: E402
from genres.load import DEFAULT_GENRE, genre_names, load_genre  # noqa: E402
from rules import load_rules  # noqa: E402
from tools._element_render import prepare, render_event, set_genre  # noqa: E402

EXAMPLES = REPO / "prompts" / "examples"
CARRIER_EXAMPLE = {"panel": ("panels", "relation"), "badge": ("badges", "person")}   # 운반 타입 → 대표 예제
LONG_SHOW_SEC = 3.0   # 표시가 이보다 길면 t1 − 1초(등장 완료)에 찍는다


class GalleryError(RuntimeError):
    pass


def _yaml_example(sub: str, name: str) -> dict:
    p = EXAMPLES / sub / f"{name}.yaml"
    if not p.exists():
        raise GalleryError(f"예제 없음: {p.relative_to(REPO)}")
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def badge_variants() -> list[str]:
    """뱃지 종류별 추가 예제 파일 이름(badges/<종류>_<이름>.yaml) — 갤러리 칸 수 = 등록 요소 + 이 목록."""
    kinds = load_rules().registries.badge_kinds
    return sorted(p.stem for k in kinds for p in (EXAMPLES / "badges").glob(f"{k}_*.yaml"))


def items() -> list[tuple[str, str, dict]]:
    """(이름, 예제 출처, 예제 문서{event, gallery?}) — 등록 요소 전부. 예제가 없으면 GalleryError(모아서)."""
    reg = load_rules().registries
    out: list[tuple[str, str, dict]] = []
    errs: list[str] = []

    def add(label: str, sub: str, name: str) -> None:
        try:
            if sub == "primitives":
                out.append((label, f"engine/primitives/{name}.py PREVIEW_FIXTURE", {"event": module(name).PREVIEW_FIXTURE}))
            else:
                out.append((label, f"prompts/examples/{sub}/{name}.yaml", _yaml_example(sub, name)))
        except (GalleryError, ValueError) as ex:
            errs.append(f"{label}: {ex}")

    for t in reg.event_types:
        if t == "primitive":
            if not reg.primitives:
                errs.append("event_primitive: 등록 프리미티브가 없다")
                continue
            add(f"event_{t}", "primitives", reg.primitives[0])
        else:
            add(f"event_{t}", *CARRIER_EXAMPLE.get(t, ("events", t)))
    for k in reg.panel_kinds:
        add(f"panel_{k}", "panels", k)
    for k in reg.badge_kinds:
        add(f"badge_{k}", "badges", k)
    for name in badge_variants():   # v4.8.0 D-0109 — 같은 종류의 추가 예제(badges/<종류>_<이름>.yaml, 예: 청와대 휘장)
        add(f"badge_{name}", "badges", name)
    for p in reg.primitives:
        add(f"primitive_{p}", "primitives", p)
    if errs:
        raise GalleryError("요소 예제 점검 실패:\n" + "\n".join(errs))
    return out


def genre_for(ev: dict) -> str:
    """이 요소를 쓸 수 있는 장르(기본 장르 우선). 프리미티브의 색 의미가 여기서 온다."""
    from genres.elements import event_elements  # noqa: PLC0415

    need = set(event_elements(ev))
    for g in [DEFAULT_GENRE, *[n for n in genre_names() if n != DEFAULT_GENRE]]:
        if need <= load_genre(g).elements():
            return g
    raise GalleryError(f"{sorted(need)} 를 쓰는 장르 프로필이 없다")


def stage_for_example(opts: dict) -> object:
    """예제 gallery.stage_config(무대 이름 → 설정) + gallery.genre 의 프로필 기본값 → 그 무대(레지스트리 경로 그대로)."""
    (name, cfg), = opts["stage_config"].items()
    prof = load_genre(opts["genre"]).stage.settings().get(name)
    base = prof.model_dump() if prof is not None else {}
    return make_stage(name, config={**base, **cfg})


def shot_time(ev: dict, opts: dict) -> float:
    if "t" in opts:
        return float(opts["t"])
    return ev["t1"] - 1.0 if ev["t1"] - ev["t0"] > LONG_SHOW_SEC else (ev["t0"] + ev["t1"]) / 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--proj", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="PNG 폴더. 컨택트 시트는 그 부모의 gallery.jpg")
    ap.add_argument("--only", nargs="*", default=None, help="확인용 부분 렌더(이름 접두어)")
    args = ap.parse_args(argv)
    todo = items()
    if args.only:
        todo = [x for x in todo if any(x[0].startswith(o) for o in args.only)]
    P = load_project(args.proj)  # noqa: N806
    args.out.mkdir(parents=True, exist_ok=True)
    cells, rows = [], []
    for label, src, doc in todo:
        opts = doc.get("gallery") or {}
        sources = None
        if "sources" in opts:   # post 카드 — 소스 레코드(18 §5)
            from schemas.source_models import SourcesFile  # noqa: PLC0415

            sources = SourcesFile.model_validate_json((REPO / opts["sources"]).read_text(encoding="utf-8")).by_id()
        stage0 = P.R.stage
        island = doc["event"]["type"] == "island"   # v5.1.0 D-0126 — 차트 아일랜드: 무대는 그대로, 예제 시간축을 상자 안 뷰포트로
        if "stage_config" in opts and island:
            chart_stage = stage_for_example(opts)
            chart_stage.fit_island(next(iter(ISLAND.boxes.values()))[3], ISLAND.chart.pad_top, ISLAND.chart.pad_bottom)
            ccam = np.array([*chart_stage.to_world(**{k: v for k, v in opts["cam"].items() if k != "w"}), opts["cam"]["w"]], float)
            n_ = int(doc["event"]["t1"] * FPS) + 1
            P.R.cache["island_chart"] = {"stage": chart_stage, "cams": np.tile(ccam, (n_, 1)), "order": MAP_LAYER_ORDER, "events": [],
                                         "resolve": resolve}
        elif "stage_config" in opts:   # v4.3.0 — 지도가 아닌 무대의 요소(series): 예제가 준 무대·카메라로 그린다
            P.R.stage = stage_for_example(opts)
        try:
            ev = prepare(P, doc["event"], sources)
            genre = opts.get("genre") or genre_for(ev)
            set_genre(P, genre)
            t = shot_time(ev, opts)
            if "stage_config" in opts and not island:
                cam = np.array([*P.R.stage.to_world(**{k: v for k, v in opts["cam"].items() if k != "w"}), opts["cam"]["w"]], float)
                prepare_series(P.R, [ev], np.tile(cam, (int(ev["t1"] * FPS) + 1, 1)), int(ev["t1"] * FPS) + 1)
            else:
                cam = P.cams[min(P.n_frames - 1, max(0, int(t * FPS)))]
            im, glyphs = render_event(P, ev, t, cam)
        finally:
            P.R.stage = stage0
        png = args.out / f"{label}.png"
        im.save(png)
        cells.append((im, f"{label}  t={t:.2f}  {genre}"))
        rows.append({"element": label, "example": src, "genre": genre, "t": round(t, 3), "png": png.name, "glyphs": len(glyphs)})
        print(f"{label}: {png}")
    sheet = args.out.parent / "gallery.jpg"
    grid(cells, 4, sheet)
    reg = load_rules().registries
    rep = {"schema_version": 1, "project": args.proj.name, "full": args.only is None, "count": len(rows),
           "expected": {"event_types": len(reg.event_types), "panel_kinds": len(reg.panel_kinds), "badge_kinds": len(reg.badge_kinds),
                        "primitives": len(reg.primitives)},
           "elements": rows}
    (args.out.parent / "gallery.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(sheet, len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
