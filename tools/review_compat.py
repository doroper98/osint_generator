"""review_sheet 임시 의존(v7.4.0 D-0632·D744 ④) — a4abe7ac(D-1000 S3)의 engine.checks 함수·규칙 값 사본.

이 브랜치는 a4abe7ac 를 칸나이 전달 뒤에 들인다(새 hard 검사 셋을 켜기 때문). 그 전까지 review_sheet 가 돌도록
`_vis_span`·`_covered_ratio`·`map_event_windows` 와 rules qa_checks.map_event_covered 값을 여기 그대로 둔다.
**검사로 등록하지 않는다**(checks HARD/WARN·run_checks 에 없음 — 표·시트를 그리는 데만 쓴다).
a4abe7ac 반입 때: review_sheet 의 import 를 engine.checks·load_rules().qa_checks.map_event_covered 로 되돌리고 이 파일을 삭제한다.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Callable

import cairo

from engine.checks import element_full_span, place_over
from engine.projection import View
from engine.style import FPS, H_OUT, W_OUT

# a4abe7ac rules/video_rules.yaml qa_checks.map_event_covered 그대로(값 복사 — 반입 때 규칙 키로 교체)
MAP_EVENT_COVERED = SimpleNamespace(max_ratio=0.25, step_sec=0.1, appear_sec=2.0, boom_radius_px=56, box_pad_px=6,
                                    event_types=["route", "marker", "badge", "boom", "camera"], camera_modes=["move"],
                                    cover_types=["photo", "clip", "article", "quote"])


def _vis_span(e: dict) -> tuple[float, float]:
    """알파 ≥ 0.5 구간(근사) — 완전 노출 구간에서 등장·퇴장 페이드의 절반씩 넓힌다."""
    a, b = element_full_span(e)
    return (e["t0"] + a) / 2, (b + e["t1"]) / 2


def _covered_ratio(box: tuple, covers: list[tuple]) -> float:
    """상자 중 덮개 합집합에 가린 넓이 비율."""
    from shapely.geometry import box as sbox  # noqa: PLC0415
    from shapely.ops import unary_union  # noqa: PLC0415

    b = sbox(*box)
    if b.area <= 0 or not covers:
        return 0.0
    return b.intersection(unary_union([sbox(*c) for c in covers])).area / b.area


def map_event_windows(P) -> list[tuple[str, str, float, float, Callable[[float], "tuple | None"]]]:  # noqa: ANN001, N803
    """지도 무대의 자라나는·나타나는 사건 — (종류, 이름, 창 시작, 창 끝, t → 화면 상자 또는 None)."""
    from engine.layers.routes import DECLARED_SAMPLES, catmull  # noqa: PLC0415

    cfg = MAP_EVENT_COVERED
    if getattr(P.R.stage, "name", None) != "mercator":
        return []
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    pad = cfg.box_pad_px
    out: list = []

    def view(t: float) -> View:
        return View(P.R.stage, P.cams[min(P.n_frames - 1, max(0, int(t * FPS)))])

    for e in P.events:
        ty = e["type"]
        if ty not in cfg.event_types:
            continue
        if ty == "route" and e.get("world_pts"):
            grow = float(e.get("grow") or 0.0)
            end = e["t0"] + (grow if grow > 0.05 else cfg.appear_sec)
            curve = catmull(e["world_pts"], DECLARED_SAMPLES)

            def rbox(t: float, e=e, curve=curve, grow=grow) -> "tuple | None":  # noqa: ANN001
                S = view(t).to_screen_arr(curve)  # noqa: N806
                prog = min(1.0, max(0.0, (t - e["t0"]) / grow)) if grow > 0.05 else 1.0
                sub = S[:max(2, int(len(S) * prog))]
                x0, y0 = float(sub[:, 0].min()), float(sub[:, 1].min())
                x1, y1 = float(sub[:, 0].max()), float(sub[:, 1].max())
                return (x0 - pad, y0 - pad, x1 + pad, y1 + pad)

            out.append((ty, str(e.get("label") or e.get("col") or "route"), e["t0"], min(e["t1"], end), rbox))
        elif ty in ("marker", "badge") and not e.get("over_panel") and ("world" in e or ty == "badge"):
            def pbox(t: float, e=e) -> "tuple | None":  # noqa: ANN001
                r = place_over(P, ctx, e, t)
                return None if r is None else tuple(float(v) for v in r[1])

            out.append((ty, str(e.get("label") or ""), e["t0"], min(e["t1"], e["t0"] + cfg.appear_sec), pbox))
        elif ty == "boom" and "world" in e:
            def bbox(t: float, e=e) -> "tuple | None":  # noqa: ANN001
                x, y = view(t).to_screen(*e["world"])
                return (x - cfg.boom_radius_px, y - cfg.boom_radius_px, x + cfg.boom_radius_px, y + cfg.boom_radius_px)

            out.append((ty, str(e.get("label") or "boom"), e["t0"], min(e["t1"], e["t0"] + cfg.appear_sec), bbox))
    if "camera" in cfg.event_types:
        for k in P.keys:
            if k.mode in cfg.camera_modes and k.dur > 0:
                out.append(("camera", f"{k.mode} t={k.t:.1f}", k.t, k.t + k.dur, lambda t: (0.0, 0.0, float(W_OUT), float(H_OUT))))
    return out
