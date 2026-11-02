"""terrain3d 구간 레이어(v7.4.0 back_and_forth D-0614·D-0615) — 미리 렌더한 3D 프레임을 바탕으로 깔고, 그 위에 엔진이 그린다.

- 바탕: prev/terrain3d/<프로파일>/<구간>/frames/f_NNNN.png(engine.terrain3d_prep). manifest.inputs_sha1 이 지금 입력과 다르면 오류(P6).
- 글자·그림: 프레임마다 labels.json 의 화면 좌표에 부대 이름·지명(engine.typography, contrast="required" — map_contrast·대비 보정이
  지도 지명과 같이 돈다), 병종 픽토그램(engine.glyphs.arms), 진영 휘장 재현(engine.glyphs.emblems — 부대 옆 작은 판, 2D 스케치와 같은 자리 규칙).
- '개략' 출처 줄: 구간 동안 forces 파일 sources + rules sketch.checks.approx_word(D-0615 §2-1, [war-units-approx] 가 기록을 잰다).
크기·자리 수치는 rules(sketch.war.terrain3d·war_history.symbol_sets.glyph·faction_badge.emblem·source_note) — 3D 렌더 폭 기준 값을 설계 폭으로 환산.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import cairo

from engine.glyphs.arms import draw_glyph
from engine.glyphs.emblems import draw_emblem
from engine.stage_terrain3d import Terrain3DError
from engine.fullcards import STAMP
from engine.style import C, H_OUT, W_OUT
from engine.typography import text
from rules import load_rules

if TYPE_CHECKING:
    from engine.project import Project


@dataclass
class SegFrames:
    sid: str
    i0: int
    i1: int
    t_in: float
    t_out: float
    dir: Path
    labels: list[list[dict]]


def load_segments(P: "Project") -> list[SegFrames]:  # noqa: N803
    """구간마다 manifest·labels 를 읽고 입력 지문을 대조한다. 없거나 다르면 Terrain3DError(렌더 전, D-0615 §1)."""
    from engine.terrain3d_prep import forces_rel, inputs_sha1, seg_dir, view_rows  # noqa: PLC0415

    segs = P.R.cache.get("terrain3d_segments") or []
    out = []
    for seg in segs:
        d = seg_dir(P.root, P.R.out.name, seg)
        man_p = d / "manifest.json"
        hint = f"`python -m engine.terrain3d_prep {P.root}{' --animatic' if P.animatic else ''}` 로 다시 만든다"
        if not man_p.is_file():
            raise Terrain3DError(f"terrain3d {seg.sid} 미리 렌더 프레임 없음({d}) — {hint}")
        man = json.loads(man_p.read_text(encoding="utf-8"))
        want = inputs_sha1(P.root, forces_rel(P), seg, view_rows(P, seg), (P.R.out.width, P.R.out.height), P.R.stage.theme_name)
        if man.get("inputs_sha1") != want:
            raise Terrain3DError(f"terrain3d {seg.sid} 프레임이 지금 입력과 다르다(forces·카메라·구간·규칙·크기 중 바뀜) — {hint}")
        lab = json.loads((d / "frames" / "labels.json").read_text(encoding="utf-8"))["frames"]
        if len(lab) != man["frames"]:
            raise Terrain3DError(f"terrain3d {seg.sid} labels {len(lab)} ≠ 프레임 {man['frames']} — {hint}")
        out.append(SegFrames(seg.sid, man["i0"], man["i1"], seg.t_in, seg.t_out, d, lab))
    return out


def segment_at(P: "Project", i: int) -> Optional[SegFrames]:  # noqa: N803
    segs = P.R.cache.get("terrain3d_frames")
    if segs is None:
        segs = P.R.cache["terrain3d_frames"] = load_segments(P)
    return next((s for s in segs if s.i0 <= i < s.i1), None)


def draw_base(ctx: cairo.Context, seg: SegFrames, i: int) -> None:
    img = cairo.ImageSurface.create_from_png(str(seg.dir / "frames" / f"f_{i - seg.i0:04d}.png"))
    ctx.save()
    ctx.identity_matrix()   # 장치 해상도 그대로(무대 render_base 와 같은 자리)
    ctx.set_source_surface(img, 0, 0)
    ctx.paint()
    ctx.restore()


def _design(P: "Project", x: float, y: float) -> tuple[float, float]:  # noqa: N803
    """3D 렌더 장치 px → 설계 좌표(render_frame 변환의 역)."""
    o = P.R.out
    return (x - o.pad_x) / o.k, y / o.k


def approx_line(forces: Any) -> str:
    word = load_rules().sketch.checks.approx_word
    return f"부대 위치·크기: {' · '.join(forces.sources)} — {word}(축척 아님)"


def draw_labels(ctx: cairo.Context, P: "Project", seg: SegFrames, i: int, t: float) -> None:  # noqa: N803
    """부대 픽토그램·이름, 진영 휘장, 지명, '개략' 출처 줄. 뒤에 숨은 점(behind)은 그리지 않는다."""
    R = load_rules()  # noqa: N806
    T3, G, E = R.sketch.war.terrain3d, R.war_history.symbol_sets.glyph, R.war_history.faction_badge.emblem  # noqa: N806
    k = W_OUT / T3.width   # 스케치 3D 폭(규칙 값의 기준) → 설계 폭
    forces = P.R.cache["terrain3d_forces"]
    emb = P.R.cache.get("terrain3d_emblems") or {}
    for rec in seg.labels[i - seg.i0]:
        if rec.get("behind"):
            continue
        x, y = _design(P, rec["x"], rec["y"])
        if rec["k"] == "unit":
            if rec.get("glyph"):
                draw_glyph(ctx, rec["glyph"], x, y - T3.glyph_px * k / 2, T3.glyph_px * k, (1, 1, 1), G.alpha, tuple(G.halo_rgb), G.halo_px)
            fk = rec.get("faction")
            if fk in emb:
                draw_emblem(ctx, emb[fk], x + E.block_dx, y + E.block_dy - T3.glyph_px * k / 2, E.block_px, (1, 1, 1), E.alpha,
                            (0.05, 0.06, 0.08), E.halo_px)
            if rec.get("name"):
                text(ctx, rec["name"], x, y + T3.text.unit * k, T3.text.unit * k, "sansm", (1, 1, 1), 1.0, 3.0, "c",
                     contrast="required")
        elif rec["k"] == "place":
            p = next((q for q in forces.places if q.name == rec["name"]), None)
            if p is not None and (t < p.t or (p.t_out is not None and t >= p.t_out)):
                continue
            text(ctx, rec["name"], x, y, T3.text.place * k, "sansm", (1, 1, 1), 1.0, 3.0, "c", contrast="required")
    line = approx_line(forces)
    text(ctx, line, R.source_note.x, H_OUT - R.source_note.y_from_bottom, STAMP.size, STAMP.font, C["muted"], R.source_note.alpha, 0, "l",
         role="media_meta")
    log = P.R.cache.setdefault("terrain3d_approx_drawn", {})
    log.setdefault(seg.sid, {"line": line, "frames": 0})["frames"] += 1


def map_events_in_segments(events: list[dict], segs: list[Any], map_types: tuple[str, ...]) -> list[str]:
    """구간 안의 지도 층 이벤트(D-0614 ④ — route·포위망·마커 등은 첫 판 밖) — 오류 문구 한 줄씩."""
    out = []
    for e in events:
        if e.get("type") not in (*map_types, "cascade", "backdrop"):
            continue
        for s in segs:
            if e["t0"] < s.t_out and e["t1"] > s.t_in:
                out.append(f"[terrain3d-map-event] {e['type']} 이벤트 [{e['t0']:.1f}, {e['t1']:.1f}] 가 terrain3d 구간 {s.sid} "
                           f"[{s.t_in:.1f}, {s.t_out:.1f}) 와 겹친다 — 구간 위에는 부대·지명·강(forces 파일)과 화면 고정 층만(D-0614 ④)")
    return out


__all__ = ["SegFrames", "approx_line", "draw_base", "draw_labels", "load_segments", "map_events_in_segments", "segment_at"]
