"""지도 위 글자 대비 측정 한 경로 (v5.21.2, back_and_forth D-0186 §2-1).

검사(`engine.checks.measure_contrast`)와 국소 보정(`engine.layers.labels`)이 **같은 식**으로 잰다 — 보정이 검사와 다른 값을 보고
고치거나 놓치지 않게. 글자 상자(장치 px, 1px 여유) 휘도 중앙값 = 배경, 글자색 쪽 극값(3·97 백분위) = 글자(가이드 23 §7).
"""

from __future__ import annotations

from typing import Optional

import cairo
import numpy as np


def rel_lum(rgb: np.ndarray) -> np.ndarray:
    """sRGB(0~1) → 상대 휘도(WCAG)."""
    c = np.where(rgb <= 0.03928, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722


def ratio(a: float, b: float) -> float:
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def text_box_ratio(L: np.ndarray, box: tuple[float, float, float, float], col: tuple) -> Optional[dict]:  # noqa: N803
    """휘도 배열 L 위 글자 상자 box(장치 px)의 대비. 상자가 너무 작으면 None."""
    h, w = L.shape
    x0, y0, x1, y1 = (max(0, int(box[0]) - 1), max(0, int(box[1]) - 1), min(w, int(box[2]) + 2), min(h, int(box[3]) + 2))
    if x1 - x0 < 3 or y1 - y0 < 3:
        return None
    core = L[y0:y1, x0:x1].ravel()
    bg = float(np.median(core))
    fl = float(rel_lum(np.asarray(col, np.float64)))
    fg = float(np.percentile(core, 3 if fl < bg else 97))
    return {"ratio": round(ratio(fg, bg), 2), "fg": round(fg, 3), "bg": round(bg, 3)}


def surface_text_ratio(ctx: cairo.Context, box: tuple[float, float, float, float], col: tuple) -> Optional[float]:
    """지금 그리고 있는 표면(RGB24·ARGB32 = BGRX)에서 글자 상자 대비 — 상자 주변만 잘라 잰다."""
    s = ctx.get_target()
    s.flush()
    w, h, st = s.get_width(), s.get_height(), s.get_stride()
    x0, y0 = max(0, int(box[0]) - 1), max(0, int(box[1]) - 1)
    x1, y1 = min(w, int(box[2]) + 2), min(h, int(box[3]) + 2)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return None
    buf = np.ndarray((h, st // 4, 4), np.uint8, buffer=s.get_data())[y0:y1, x0:x1, :3][..., ::-1]
    L = rel_lum(buf.astype(np.float64) / 255.0)  # noqa: N806
    r = text_box_ratio(L, (1, 1, x1 - x0 - 2, y1 - y0 - 2), col)
    return None if r is None else r["ratio"]


__all__ = ["ratio", "rel_lum", "surface_text_ratio", "text_box_ratio"]
