"""국기 채움 — country 이벤트 fill: flag (v7.4.0 UF-900 R2·UF-901(D904), 레퍼런스 실측 benchmark_wartech_2026-11-17.md §2.3·§2.7).

국기(assets/flags/<flag>_4x3.png)를 나라 외곽 상자(화면 투영)에 비율 무시로 늘려 나라 모양(codes 의 모든 고리, even-odd)으로 자른다.
지형이 국기 위로 비친다: 지형 베이스(stage.frame_base — 국경·강·도로 전, 화면과 같은 장치 화소) 휘도 ÷ 그 나라 땅 지형 휘도 중앙값(ref_luma) = f,
국기 × clip(base + gain·(f − 1), lo, hi). 그 위에 흰 심선 + 겹친 halo 윤곽, 아래에 오른쪽 아래 그림자(들뜸), 안쪽 왼쪽 위 밝은 면.
등장 구간(transition.element.country 의 in)에는 국기가 어둡게 시작해 밝아지고 그림자 오프셋이 0 에서 자란다(되튐 없음).
수치는 전부 rules flag_fill. 국기 파일이 없으면 오류(단색으로 대신 칠하지 않는다, 15 P6). 분쟁 지역을 막는 검사는 두지 않는다(UF-901).
"""

from __future__ import annotations

import math

import cairo
import numpy as np

from engine.context import RenderCtx
from engine.layers.borders import path_rings
from engine.projection import View
from engine.stage import MERCATOR_LOD as LOD
from engine.style import ELEM
from engine.timebase import smooth, window
from rules import load_rules

FF = load_rules().flag_fill


class FlagFillError(ValueError):
    """국기 채움을 그릴 수 없다(나라 코드가 무대 경계 자료에 없음·무대에 지형 베이스 없음)."""


def ref_luma(R: RenderCtx, view: View, codes: list[str]) -> float:  # noqa: N803
    """기준 휘도(0~255) = 그 나라 땅(codes 고리 안) 지형 화소 휘도의 중앙값 — 광역 티어 W 의 가장 거친 레벨에서 한 번 재고 R.cache 에 둔다.
    카메라·줌과 무관한 상수라 국기 밝기가 프레임마다 떨리지 않고, 테마마다 다른 고도 색(slate 고지대 밝음·light 고지대 어두움)을
    지운다 — 남는 것은 그 나라 안의 지형 음영(비침)뿐. 모든 테마(dark·light·slate)에 같은 식."""
    st = view.stage
    memo = R.cache.setdefault("flag_fill_ref", {})
    key = (st.theme_name, tuple(codes))
    if key in memo:
        return memo[key]
    T = st.tiers["W"]  # noqa: N806
    lv = min(T["levels"])
    im = st.assets.base[("W", lv)]
    wx0, wy0, wx1, wy1 = world_box(view, codes)
    ty1 = st.to_world(lon=T["lon0"], lat=T["lat1"])[1]
    x0, y0 = max(0, math.floor((wx0 - T["lon0"]) * lv)), max(0, math.floor((ty1 - wy1) * lv))
    x1, y1 = min(im.width, math.ceil((wx1 - T["lon0"]) * lv)), min(im.height, math.ceil((ty1 - wy0) * lv))
    if x1 <= x0 or y1 <= y0:
        raise FlagFillError(f"국기 채움: {codes} 가 광역 티어 W 밖 — 지형 기준을 잴 수 없다(geo.yaml tiers W bbox)")
    mask = cairo.ImageSurface(cairo.FORMAT_A8, x1 - x0, y1 - y0)
    mc = cairo.Context(mask)
    mc.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    mc.set_antialias(cairo.ANTIALIAS_NONE)
    for c in codes:
        for uv, _mn, _mx in _rings(view, FF.bbox_lod, c):
            pts = (np.asarray(uv, dtype=float) - (T["lon0"], ty1)) * (lv, -lv) - (x0, y0)
            mc.move_to(*pts[0])
            for x, y in pts[1:]:
                mc.line_to(x, y)
            mc.close_path()
    mc.fill()
    mask.flush()
    m = np.ndarray((y1 - y0, mask.get_stride()), dtype=np.uint8, buffer=mask.get_data())[:, : x1 - x0] > 0
    if not m.any():
        raise FlagFillError(f"국기 채움: {codes} 땅 화소가 광역 티어 W 에 없다 — 지형 기준을 잴 수 없다")
    lum = np.asarray(im.crop((x0, y0, x1, y1)), dtype=np.float64) @ np.array(FF.luma)
    memo[key] = float(np.median(lum[m]))
    return memo[key]


def shade_factor(base_rgb: np.ndarray, ref_luma: float, brightness: float) -> np.ndarray:
    """지형 화소(h, w, 3, 0~255) → 국기에 곱할 배율(h, w). clip(base + gain·(f − 1), lo, hi) × 등장 밝기."""
    s = FF.shade
    f = (base_rgb.astype(np.float32) @ np.array(FF.luma, dtype=np.float32)) / np.float32(ref_luma)
    return np.clip(np.float32(s.base) + np.float32(s.gain) * (f - np.float32(1)), np.float32(s.lo), np.float32(s.hi)) * np.float32(brightness)


def _rings(view: View, lod: str, code: str) -> list:
    if code not in view.stage.bord[lod]:
        raise FlagFillError(f"국기 채움: 나라 코드 {code!r} 가 무대 경계 자료(geo.pkl {lod})에 없다 — codes 를 고친다")
    return view.stage.bord[lod][code]


def world_box(view: View, codes: list[str]) -> tuple[float, float, float, float]:
    """codes 고리 전체(화면 밖·작은 고리 포함, rules flag_fill.bbox_lod)의 월드 상자 (x0, y0, x1, y1)."""
    items = [it for c in codes for it in _rings(view, FF.bbox_lod, c)]
    mn = np.array([m for _, m, _ in items], dtype=float).reshape(-1, 2).min(axis=0)
    mx = np.array([m for _, _, m in items], dtype=float).reshape(-1, 2).max(axis=0)
    return float(mn[0]), float(mn[1]), float(mx[0]), float(mx[1])


def _path(ctx: cairo.Context, view: View, lod: str, codes: list[str]) -> int:
    ctx.new_path()
    return sum(path_rings(ctx, view, _rings(view, lod, c)) for c in codes)


def flag_layer(R: RenderCtx, view: View, e: dict, box: tuple[int, int, int, int], dev_box: tuple[float, float, float, float],  # noqa: N803
               brightness: float) -> cairo.ImageSurface:
    """장치 화소 상자 box(x0, y0, x1, y1) 안의 국기 층 — 국기를 dev_box(나라 외곽 상자, 장치 좌표)에 늘려 그리고 지형 배율을 곱한다."""
    x0, y0, x1, y1 = box
    X0, Y0, X1, Y1 = dev_box  # noqa: N806
    src = R.assets.original(f"flag43:{e['flag']}")   # 없으면 AssetError(파일 경로를 밝힌다)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, x1 - x0, y1 - y0)
    fc = cairo.Context(surf)
    pat = cairo.SurfacePattern(src)
    sx, sy = src.get_width() / (X1 - X0), src.get_height() / (Y1 - Y0)
    pat.set_matrix(cairo.Matrix(xx=sx, yy=sy, x0=(x0 - X0) * sx, y0=(y0 - Y0) * sy))
    pat.set_filter(cairo.FILTER_GOOD)
    pat.set_extend(cairo.EXTEND_PAD)
    fc.set_source(pat)
    fc.paint()
    surf.flush()
    stage = view.stage
    base = stage.frame_base(view)   # 무대가 같은 view 로 방금 그린 지형(한 장 memo — render_base 와 같은 상)
    terr = np.asarray(base.crop((x0, y0, x1, y1)).convert("RGB"))
    k = shade_factor(terr, ref_luma(R, view, e["codes"]), brightness)
    px = np.ndarray((y1 - y0, surf.get_stride() // 4, 4), dtype=np.uint8, buffer=surf.get_data())[:, : x1 - x0]   # ARGB32 = 화소당 4바이트(B·G·R·A)
    col = px[..., :3].astype(np.float32) * k[..., None]
    px[..., :3] = np.minimum(col, px[..., 3:].astype(np.float32)).astype(np.uint8)   # 미리 곱한 알파 — 색 ≤ 알파
    surf.mark_dirty()
    return surf


def draw_flag_fill(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    fin, fout = ELEM["country"]
    a = window(t, e["t0"], e["t1"], fin, fout)
    if a <= 0.01:   # 보이지 않는 알파 문턱(areas.draw_country 단색 채움과 같은 값)
        return
    if not hasattr(view.stage, "frame_base"):
        raise FlagFillError(f"국기 채움은 지도 무대에서만 — 무대 {getattr(view.stage, 'name', '?')!r} 에 지형 베이스가 없다")
    pin = smooth((t - e["t0"]) / fin) if fin > 0 else 1.0   # 등장 진행(0 → 1) — 퇴장 쪽은 알파만
    lod = "fine" if view.w < LOD["borders_fine_below_w"] else "coarse"
    codes = e["codes"]
    ctx.save()
    if not _path(ctx, view, lod, codes):
        ctx.restore()
        return
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    path = ctx.copy_path()
    ex = ctx.fill_extents()
    wx0, wy0, wx1, wy1 = world_box(view, codes)
    sx0, sy0 = view.to_screen(wx0, wy1)   # 월드 y 위 = 화면 위
    sx1, sy1 = view.to_screen(wx1, wy0)
    X0, Y0 = ctx.user_to_device(sx0, sy0)  # noqa: N806
    X1, Y1 = ctx.user_to_device(sx1, sy1)  # noqa: N806
    ea, eb = ctx.user_to_device(ex[0], ex[1]), ctx.user_to_device(ex[2], ex[3])
    tgt = ctx.get_target()
    box = (max(0, math.floor(max(X0, ea[0]))), max(0, math.floor(max(Y0, ea[1]))),
           min(tgt.get_width(), math.ceil(min(X1, eb[0]))), min(tgt.get_height(), math.ceil(min(Y1, eb[1]))))
    sh = FF.shadow
    ctx.save()   # 그림자 — 나라 모양을 오른쪽 아래로(등장 중 0 → 전부), 지도 위·국기 아래
    ctx.translate(sh.offset[0] * pin, sh.offset[1] * pin)
    ctx.new_path()
    ctx.append_path(path)
    ctx.set_source_rgba(*sh.rgb, sh.alpha * a)
    ctx.fill_preserve()
    for wd, al in sh.soft:
        ctx.set_source_rgba(*sh.rgb, al * a)
        ctx.set_line_width(wd)
        ctx.stroke_preserve()
    ctx.restore()
    if box[2] > box[0] and box[3] > box[1] and X1 > X0 and Y1 > Y0:
        layer = flag_layer(R, view, e, box, (X0, Y0, X1, Y1), FF.rise.brightness_from + (1 - FF.rise.brightness_from) * pin)
        ctx.save()
        ctx.new_path()
        ctx.append_path(path)
        ctx.clip()
        m = ctx.get_matrix()
        ctx.identity_matrix()   # 국기 층은 장치 화소(지형 베이스와 같은 격자)
        ctx.set_source_surface(layer, box[0], box[1])
        ctx.paint_with_alpha(a)
        ctx.set_matrix(m)
        il = FF.inner_light   # 빛 받는 면 — 나라 모양 − (오른쪽 아래로 민 나라 모양) = 왼쪽 위 안쪽 가장자리
        if il.alpha > 0:
            ctx.new_path()
            ctx.rectangle(ex[0], ex[1], ex[2] - ex[0], ex[3] - ex[1])
            ctx.translate(il.offset, il.offset)
            ctx.append_path(path)
            ctx.set_matrix(m)
            ctx.set_source_rgba(*FF.outline.rgb, il.alpha * a)
            ctx.fill()
        ctx.restore()
    ol = FF.outline   # 흰 심선 + 겹친 halo(흐림 없음 — 국경 글로우와 같은 방식)
    ctx.new_path()
    ctx.append_path(path)
    for wd, al in (*ol.halo, (ol.width, ol.alpha)):
        ctx.set_source_rgba(*ol.rgb, al * a)
        ctx.set_line_width(wd)
        ctx.stroke_preserve()
    ctx.new_path()
    ctx.restore()

