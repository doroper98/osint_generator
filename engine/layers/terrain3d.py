"""terrain3d 구간 레이어(v7.4.0 back_and_forth D-0614·D-0615) — 미리 렌더한 3D 프레임을 바탕으로 깔고, 그 위에 엔진이 그린다.

- 바탕: prev/terrain3d/<프로파일>/<구간>/frames/f_NNNN.png(engine.terrain3d_prep). manifest.inputs_sha1 이 지금 입력과 다르면 오류(P6).
- 글자·그림: 프레임마다 labels.json 의 화면 좌표에 부대 이름·지명(engine.typography, contrast="required" — map_contrast·대비 보정이
  지도 지명과 같이 돈다), 병종 픽토그램(engine.glyphs.arms), 진영 휘장 재현(engine.glyphs.emblems — 부대 옆 작은 판, 2D 스케치와 같은 자리 규칙).
- '개략' 출처 줄: 구간 동안 forces 파일 sources + rules sketch.checks.approx_word(D-0615 §2-1, [war-units-approx] 가 기록을 잰다).
크기·자리 수치는 rules(sketch.war.terrain3d·war_history.symbol_sets.glyph·faction_badge.emblem·source_note) — 3D 렌더 폭 기준 값을 설계 폭으로 환산.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import cairo

from engine.fullcards import STAMP
from engine.glyphs.arms import draw_glyph
from engine.glyphs.emblems import draw_emblem
from engine.stage_terrain3d import Terrain3DError
from engine.style import H_OUT, W_OUT, C
from engine.typography import text
from rules import load_rules as _load_rules_uncached

if TYPE_CHECKING:
    from engine.project import Project


# 규칙은 프로세스마다 한 번(load_rules 한 번 ≈ 0.3초 — 프레임마다 부르지 않는다)
load_rules = functools.lru_cache(maxsize=1)(_load_rules_uncached)


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


def seam_alpha(seg: SegFrames, t: float) -> float:
    """구간 이음(D-0619 ①) — 들어감 뒤·나옴 앞 rules stage_terrain3d.seam_sec 동안 0→1→0(smooth). 1 = 3D 만, 0 = mercator 만."""
    from engine.timebase import smooth  # noqa: PLC0415

    s = load_rules().stage_terrain3d.seam_sec
    return smooth(max(0.0, min(1.0, (t - seg.t_in) / s, (seg.t_out - t) / s)))


def draw_base(ctx: cairo.Context, seg: SegFrames, i: int, alpha: float = 1.0) -> None:
    """alpha < 1 = 이음 창 — 이미 그린 mercator 지도 위로 3D 바탕(부대·강 포함)이 녹아 든다(D-0619 ①)."""
    img = cairo.ImageSurface.create_from_png(str(seg.dir / "frames" / f"f_{i - seg.i0:04d}.png"))
    ctx.save()
    ctx.identity_matrix()   # 장치 해상도 그대로(무대 render_base 와 같은 자리)
    ctx.set_source_surface(img, 0, 0)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def _design(P: "Project", x: float, y: float) -> tuple[float, float]:  # noqa: N803
    """3D 렌더 장치 px → 설계 좌표(render_frame 변환의 역)."""
    o = P.R.out
    return (x - o.pad_x) / o.k, y / o.k


def label_box(P: "Project", rec: dict) -> tuple[float, float, float, float]:  # noqa: N803
    """부대가 화면에 차지하는 설계 상자 — 병종 그림(라벨 점 위) ∪ 블록 윗면 화면 상자(labels.json block, 있으면). 지명 = 이름 상자.
    진형 가운데 검사(D-0625)·카드 덮음 검사(D-0619 ②)가 쓴다. 이름 글자 자리는 layout_labels."""
    from engine.typography import adv  # noqa: PLC0415

    T3 = load_rules().sketch.war.terrain3d  # noqa: N806
    k = W_OUT / T3.width
    x, y = _design(P, rec["x"], rec["y"])
    if rec["k"] == "unit":
        g = T3.glyph_px * k
        bx = [x - g / 2, y - g, x + g / 2, y]
        blk = block_box(P, rec)
        if blk is not None:
            bx = [min(bx[0], blk[0]), min(bx[1], blk[1]), max(bx[2], blk[2]), max(bx[3], blk[3])]
        return tuple(bx)  # type: ignore[return-value]
    sz = T3.text.place * k
    half = adv(rec["name"], sz, "sansm") / 2
    return x - half, y - sz * 0.9, x + half, y + sz * 0.3


def block_box(P: "Project", rec: dict) -> "tuple[float, float, float, float] | None":  # noqa: N803
    """블록 윗면 화면 상자(설계 좌표) — labels.json 'block'(D-0627). 옛 기록에는 없다."""
    b = rec.get("block")
    if not b or not all(map(lambda v: v == v and abs(v) < 1e9, b)):
        return None
    x0, y0 = _design(P, b[0], b[1])
    x1, y1 = _design(P, b[2], b[3])
    return x0, y0, x1, y1


def _hit(a: tuple, b: tuple, tol: float) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > tol and min(a[3], b[3]) - max(a[1], b[1]) > tol


@dataclass
class Placed:
    rec: dict
    text: str
    x: float
    y: float
    size: float
    box: tuple


def layout_labels(P: "Project", recs: list[dict]) -> tuple[list[Placed], list[str]]:  # noqa: N803
    """부대 이름 자리(D-0627, UF-257) — 블록 윗면 상자 바깥, 진형 중심에서 먼 쪽 먼저(그다음 옆 둘, 마지막 안쪽).
    다른 이름·다른 부대 블록·모든 병종 그림·안전 영역(qa_checks.formation_centered)과 겹치지 않는 첫 자리. 없으면 short 이름, 그래도 없으면 접는다.
    같은 이름 블록이 여럿이면 이름은 한 번만(자리가 나는 첫 블록). 결정적(부대 순서 = forces 순서). 반환 = (자리, 접힌 이름)."""
    from engine.typography import adv  # noqa: PLC0415

    R = load_rules()  # noqa: N806
    T3, FC = R.sketch.war.terrain3d, R.qa_checks.formation_centered  # noqa: N806
    k = W_OUT / T3.width
    sz, gap, tol = T3.text.unit * k, R.stage_terrain3d.label_gap_px, 2.0
    units = [r for r in recs if r["k"] == "unit" and not r.get("behind")]
    if not units:
        return [], []
    pts = [_design(P, r["x"], r["y"]) for r in units]
    cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    g = T3.glyph_px * k
    glyphs = [(x - g / 2, y - g, x + g / 2, y) for x, y in pts]
    blocks = [block_box(P, r) or (x - g / 2, y - g, x + g / 2, y) for r, (x, y) in zip(units, pts)]
    top, side, bottom = (FC.safe_top_px, FC.safe_side_px, R.layout_480p.reserved_zones.subtitle.y_from) if FC else (0, 0, H_OUT)
    shorts = {u.name: u.short for u in P.R.cache["terrain3d_forces"].units if u.short}
    placed: list[Placed] = []
    folded: list[str] = []
    done: set[str] = set()

    def candidates(j: int, w: float) -> list[tuple[float, float, tuple]]:
        b, (x, y) = blocks[j], pts[j]
        mx, my = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        cand = {"below": (mx, b[3] + gap + sz * 0.85), "above": (mx, b[1] - gap - sz * 0.25),
                "left": (b[0] - gap - w / 2, my + sz * 0.3), "right": (b[2] + gap + w / 2, my + sz * 0.3)}
        dx, dy = x - cx, y - cy
        vert = ("below", "above") if dy >= 0 else ("above", "below")
        hor = ("right", "left") if dx >= 0 else ("left", "right")
        order = (vert[0], hor[0], hor[1], vert[1]) if abs(dy) >= abs(dx) else (hor[0], vert[0], vert[1], hor[1])
        return [(cand[o][0], cand[o][1], (cand[o][0] - w / 2, cand[o][1] - sz * 0.85, cand[o][0] + w / 2, cand[o][1] + sz * 0.25)) for o in order]

    def free(box: tuple, j: int) -> bool:
        if box[0] < side or box[2] > W_OUT - side or box[1] < top or box[3] > bottom:
            return False
        if any(_hit(box, p.box, tol) for p in placed) or any(_hit(box, gb, tol) for gb in glyphs):
            return False
        return not any(_hit(box, bb, tol) for m, bb in enumerate(blocks) if m != j)

    for j, r in enumerate(units):
        name = r.get("name")
        if not name or name in done:
            continue
        group = [m for m, q in enumerate(units) if q.get("name") == name]
        hit = None
        for label in [name] + ([shorts[name]] if name in shorts else []):
            w = adv(label, sz, "sansm")
            hit = next(((m, x, y, box) for m in group for x, y, box in candidates(m, w) if free(box, m)), None)
            if hit is not None:
                m, x, y, box = hit
                placed.append(Placed(units[m], label, x, y, sz, box))
                break
        if hit is None:
            folded.append(name)
        done.add(name)
    return placed, folded


def approx_line(forces: Any) -> str:
    word = load_rules().sketch.checks.approx_word
    return f"부대 위치·크기: {' · '.join(forces.sources)} — {word}(축척 아님)"


def draw_labels(ctx: cairo.Context, P: "Project", seg: SegFrames, i: int, t: float, fade: float = 1.0) -> None:  # noqa: N803
    """부대 픽토그램·이름, 진영 휘장, 지명, '개략' 출처 줄. 뒤에 숨은 점(behind)은 그리지 않는다. fade = 이음 창 알파(seam_alpha)."""
    R = load_rules()  # noqa: N806
    T3, G, E = R.sketch.war.terrain3d, R.war_history.symbol_sets.glyph, R.war_history.faction_badge.emblem  # noqa: N806
    k = W_OUT / T3.width   # 스케치 3D 폭(규칙 값의 기준) → 설계 폭
    forces = P.R.cache["terrain3d_forces"]
    emb = P.R.cache.get("terrain3d_emblems") or {}
    recs = seg.labels[i - seg.i0]
    for rec in recs:
        if rec.get("behind"):
            continue
        x, y = _design(P, rec["x"], rec["y"])
        if rec["k"] == "unit":
            if rec.get("glyph"):
                draw_glyph(ctx, rec["glyph"], x, y - T3.glyph_px * k / 2, T3.glyph_px * k, (1, 1, 1), G.alpha * fade, tuple(G.halo_rgb), G.halo_px)
            fk = rec.get("faction")
            if fk in emb:
                draw_emblem(ctx, emb[fk], x + E.block_dx, y + E.block_dy - T3.glyph_px * k / 2, E.block_px, (1, 1, 1), E.alpha * fade,
                            (0.05, 0.06, 0.08), E.halo_px)
        elif rec["k"] == "place":
            p = next((q for q in forces.places if q.name == rec["name"]), None)
            if p is not None and (t < p.t or (p.t_out is not None and t >= p.t_out)):
                continue
            text(ctx, rec["name"], x, y, T3.text.place * k, "sansm", (1, 1, 1), fade, 3.0, "c", contrast="required")
    placed, folded = layout_labels(P, recs)   # 부대 이름 — 블록 바깥 자리·접기(D-0627, UF-257)
    for pl in placed:
        text(ctx, pl.text, pl.x, pl.y, pl.size, "sansm", (1, 1, 1), fade, 3.0, "c", contrast="required")
    if folded:
        log = P.R.cache.setdefault("terrain3d_labels_folded", {})
        for nm in folded:
            log[nm] = log.get(nm, 0) + 1
    line = approx_line(forces)
    text(ctx, line, R.source_note.x, H_OUT - R.source_note.y_from_bottom, STAMP.size, STAMP.font, C["muted"], R.source_note.alpha * fade, 0, "l",
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


__all__ = ["Placed", "SegFrames", "approx_line", "block_box", "label_box", "layout_labels", "draw_base", "seam_alpha", "draw_labels", "load_segments", "map_events_in_segments", "segment_at"]
