"""콘티 판(animatic) 레이어 — 막지도·자리표시 상자·표식 띠 (v4.9.0, back_and_forth D-0108, 사용자 결정 D97).

animatic = animation + -matic. 1930년대 디즈니가 스토리보드를 라이카 카메라로 찍어 음성과 함께 틀어 본 "Leica reel"이 원형이다.
본 저장소 용어 = **콘티 판**(한국어 "콘티" ← 일본어 コンテ ← continuity).

진입은 `engine.project.load_project(animatic=True)` 한 곳(15 P2 — 플래그 분기는 진입에서 끝난다). 이 모듈은 레이어 선택
`ANIMATIC_LAYERS`(engine.registry.LayerSet)를 내놓고, render_frame 은 전편과 같은 순서로 그린다.

- 지도: `engine.stage.FlatMercatorStage` 의 배경 = `draw_flat_map`(육지·바다 단색 + 국경선, 라벨 없음). 카메라·dip 그대로.
- 자리표시(`rules animatic.placeholder.kinds`): badge(인물·국기·휘장)·photo·clip·cutout·article·post·primitive 는
  같은 자리·크기(G7 값)·타이밍(팝인·페이드·슬라이드)의 상자 + `[종류: 이름]`. 상자 계산은 전편 레이어의 기하 함수를 그대로 부른다
  (badge_R·place_badge·media_box·article_layout·post_box·card_geom·primitive_box) — 자리를 따로 계산하지 않는다.
- 그대로: 마커·경로·타격 링·선박·국가 강조·시리즈·dip·자막·날짜·타이틀·엔딩 카드.
- v5.6.0(사용자 지적 2026-10-04 "콘티판에는 패널이라고만 나와서 대본 말고는 승인할 게 없다", PIPELINE-AP-018): 패널·카드는
  코드가 글자로 그리는 요소라 파일이 필요 없다 → 전편 렌더러 그대로(숫자·문구·도식을 콘티 판에서 승인). 패널 안 인물·국기
  뱃지만 `R.cache["badge_placeholder"]`(= 이 모듈 `_badge_at`)로 자리표시.
- 표식: 전체 페이드 뒤 화면 위 가운데 띠(`rules animatic.band`) — 암전 중에도 보인다.
이미지·영상·타일 파일을 읽지 않는다(자산 없는 환경에서 렌더 가능, D-0108 합격 조건).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable, Optional

import cairo

from engine.context import RenderCtx
from engine.layers.badges import badge_R, place_badge, resolve_kind
from engine.layers.borders import path_rings
from engine.projection import View
from engine.registry import Entry, LayerSet, resolve
from engine.style import ANIMATIC, BADGE, CARD, W_OUT
from engine.timebase import ease_back, ease_out, window
from engine.typography import rrect, text, tw

REPO = Path(__file__).resolve().parents[2]
PH = ANIMATIC.placeholder
BAND = ANIMATIC.band
FM = ANIMATIC.flat_map


# ------------------------------------------------------------------ 막지도
def load_flat_polygons(crimea_to_ua: bool) -> dict[str, list]:
    """저장소 막지도 자료(tools/build_flat_map.py) → 국가 키 → 폴리곤 [[바깥, 구멍…]…]. crimea_to_ua 면 크림을 RU → UA(04 §3.2)."""
    doc = json.loads((REPO / FM.data).read_text(encoding="utf-8"))
    polys: dict[str, list] = doc["countries"]
    if crimea_to_ua:
        from shapely.geometry import MultiPolygon, Polygon  # noqa: PLC0415
        from shapely.ops import unary_union  # noqa: PLC0415

        from geo.prep_geometry import CRIMEA_GAP, polys as flat  # noqa: PLC0415

        def geom(v: list) -> Any:
            return MultiPolygon([Polygon(p[0], p[1:]) for p in v]).buffer(0)

        def back(g: Any) -> list:
            return [[[list(c) for c in q.exterior.coords], *[[list(c) for c in r.coords] for r in q.interiors]] for q in flat(g)]

        cr = geom(doc["crimea"])
        polys = dict(polys, UA=back(unary_union([geom(polys["UA"]), cr])), RU=back(geom(polys["RU"]).difference(cr.buffer(CRIMEA_GAP))))
    return polys


def flat_map_source() -> dict:
    """provenance animatic_run.flat_map — 막지도 자료 파일과 원본 기록(C9)."""
    import hashlib  # noqa: PLC0415

    p = REPO / FM.data
    doc = json.loads(p.read_text(encoding="utf-8"))
    return {"data": FM.data, "md5": hashlib.md5(p.read_bytes()).hexdigest(), **{k: doc["source"][k] for k in ("countries", "license")}}


def flat_stage_factory(proj: Path, out: Any) -> Callable[[Optional[dict]], Any]:
    """StageSet modes["mercator"] — 경계 = 프로젝트 geo.yaml 티어 W bbox(tiers.pkl 과 같은 값, geo.prep tier_record)."""
    from engine.stage import FlatMercatorStage, StageError  # noqa: PLC0415
    from geo.prep import load_conf  # noqa: PLC0415

    def make(config: Optional[dict]) -> Any:
        bad = sorted(set(config or {}) - {"border_glow"})
        if bad:   # v5.3.1 — 전편 MercatorStage 와 같은 키 검사. 막지도에는 글로우를 그리지 않는다(자리표시 지도)
            raise StageError(f"mercator 무대 stage_config 는 border_glow 만 — 받은 키 {bad}")
        conf = load_conf(proj)
        w = next((t for t in conf.tiers if t.name == "W"), None)
        if w is None:
            raise KeyError("티어 W(광역, 카메라 경계)가 없다 — geo.yaml tiers 에 name: W 를 둔다")
        tier = dict(lon0=w.bbox[0], lat0=w.bbox[1], lon1=w.bbox[2], lat1=w.bbox[3])
        return FlatMercatorStage(tier, load_flat_polygons(conf.crimea_to_ua), out)

    return make


def draw_flat_map(ctx: cairo.Context, stage: Any, view: View) -> None:
    """막지도 배경 — 바다 단색 → 보이는 육지 채움(국가별 고리, 짝홀 규칙) → 국경선."""
    ctx.set_source_rgba(*FM.sea)
    ctx.paint()
    ctx.new_path()
    for rings in stage.bord["coarse"].values():
        path_rings(ctx, view, rings)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgba(*FM.land)
    ctx.fill_preserve()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*FM.border)
    ctx.set_line_width(FM.border_w)
    ctx.stroke()


# ------------------------------------------------------------------ 자리표시
def label(kind: str, name: str) -> str:
    """`[종류: 이름]` — 종류 이름은 rules animatic.placeholder.kinds(목록 밖 = 오류, P10)."""
    if kind not in PH.kinds:
        raise KeyError(f"콘티 판 자리표시 종류 {kind!r} 가 rules animatic.placeholder.kinds 에 없다")
    s = " ".join(str(name).split())
    if len(s) > PH.max_chars:
        s = s[:PH.max_chars - 1] + "…"
    return f"[{PH.kinds[kind]}: {s}]"


def _lines(ctx: cairo.Context, lines: list[str], cx: float, cy: float, a: float) -> None:
    n = len(lines)
    for i, s in enumerate(lines):
        y = cy + (i - (n - 1) / 2) * PH.line_gap + PH.size * 0.35
        text(ctx, s, cx, y, PH.size, PH.font, PH.text[:3], a * PH.text[3], 2, "c")


def _stroke(ctx: cairo.Context, a: float) -> None:
    ctx.set_source_rgba(*PH.fill[:3], PH.fill[3] * a)
    ctx.fill_preserve()
    ctx.set_dash(list(PH.dash))
    ctx.set_source_rgba(*PH.stroke[:3], PH.stroke[3] * a)
    ctx.set_line_width(PH.stroke_w)
    ctx.stroke()
    ctx.set_dash([])


def box(ctx: cairo.Context, x: float, y: float, w: float, h: float, lines: list[str], a: float) -> None:
    """사각 자리표시 — 요소 상자 그대로(x, y, 폭, 높이), 글자는 가운데."""
    if a <= 0.01:
        return
    ctx.new_path()
    ctx.rectangle(x, y, w, h)
    _stroke(ctx, a)
    _lines(ctx, lines, x + w / 2, y + h / 2, a)


def circle(ctx: cairo.Context, x: float, y: float, r: float, lines: list[str], a: float) -> None:
    """원형 자리표시(뱃지) — 반지름 = 그 순간의 뱃지 R × 팝인 배율."""
    if a <= 0.01 or r <= 0.1:
        return
    ctx.new_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    _stroke(ctx, a)
    _lines(ctx, lines, x, y, a)


def badge_name(R: RenderCtx, e: dict) -> tuple[str, str]:  # noqa: N803
    kind, flag = resolve_kind(R, e)   # 휘장 flag_fallback(D5) = 국기
    if e["kind"] == "person":
        return "person", e.get("label") or e["pid"]
    if kind == "flag":
        return "flag", (flag or "").upper()
    return "emblem", e.get("label") or e["img"]


def _badge_at(ctx: cairo.Context, R: RenderCtx, x: float, y: float, e: dict, t: float, a: float) -> None:  # noqa: N803
    """badges.badge_at 의 자리표시판 — 같은 R(적응 크기)·팝인(ease_back)·예약 영역."""
    from engine.layers.badges import head_factor  # noqa: PLC0415

    Rr = badge_R(e, t)  # noqa: N806
    k = ease_back((t - e["t0"]) / BADGE.popin_sec)
    if k <= 0.01:
        return
    circle(ctx, x, y, Rr * k, [label(*badge_name(R, e))], a)
    R.reserved.append((x - Rr - 10, y - Rr * (head_factor(e) if e["kind"] == "person" else BADGE.reserve_top_factor), x + Rr + 10,
                       y + Rr + BADGE.reserve_bottom_px))


def draw_badge(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    if e.get("over_panel"):
        return
    a = window(t, e["t0"], e["t1"], BADGE.fade_in_sec, BADGE.fade_out_sec)
    if a <= 0.01:
        return
    x, y = view.to_screen(*e["world"])
    dx, dy, ka = place_badge(ctx, e, x, y, t, R.zones)
    _badge_at(ctx, R, x + dx, y + dy, e, t, a * ka)


def draw_over_panel(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    a = window(t, e["t0"], e["t1"], BADGE.fade_in_sec, BADGE.fade_out_sec)
    if a <= 0.01:
        return
    x, y = e["screen"]
    dx, dy, ka = place_badge(ctx, e, x, y, t, R.zones)
    _badge_at(ctx, R, x + dx, y + dy, e, t, a * ka)


def draw_photo(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    """media.draw_photo 와 같은 페이드(0.5)·올라옴(0.6초 12px), 상자 = media_box(캡션 바 포함)."""
    from engine.media_plan import media_box  # noqa: PLC0415

    a = window(t, e["t0"], e["t1"], 0.5, 0.5)
    x0, y0, x1, y1 = media_box(e, R.assets.media_assets)
    dy = (1 - ease_out((t - e["t0"]) / 0.6)) * 12
    box(ctx, x0, y0 + dy, x1 - x0, y1 - y0, [label("photo", R.assets.media_assets[e["mid"]].caption)], a)


def draw_backdrop(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    """배경 사진 자리표시(v5.1.0 D-0123 §3) — 회색 판(자리표시 바탕) 전체 + 가운데 위 `[배경: id]`. 페이드 = backdrop_alpha(crossfade)."""
    from engine.layers.backdrop import backdrop_alpha  # noqa: PLC0415

    a = backdrop_alpha(t, e)
    if a <= 0.01:
        return
    ctx.set_source_rgba(*PH.fill[:3], PH.fill[3] * a)
    ctx.paint()
    _lines(ctx, [label("backdrop", e["img"])], W_OUT / 2, PH.line_gap * 2, a)


def draw_clip(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    from engine.media_plan import media_box  # noqa: PLC0415

    a = window(t, e["t0"], e["t1"], 0.35, 0.45)
    x0, y0, x1, y1 = media_box(e, R.assets.media_assets)
    box(ctx, x0, y0, x1 - x0, y1 - y0, [label("clip", R.assets.media_assets[e["mid"]].caption)], a)


def draw_cutout(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> None:  # noqa: N803
    """media.draw_cutout 와 같은 페이드·옆에서 들어옴·흔들림. 높이 = 폭 × rules cutout_h_ratio(레지스트리에 비율이 없어 근사 —
    파일을 열지 않는다)."""
    a = window(t, e["t0"], e["t1"], 0.6, 0.5)
    if a <= 0.01:
        return
    m = R.assets.media_assets[e["mid"]]
    w = e["w"]
    h = w * PH.cutout_h_ratio
    lt = t - e["t0"]
    x, y = view.to_screen(*e["world"])
    x -= (1 - ease_out(lt / 1.2)) * 40
    y += math.sin(t * 1.3) * 2.2
    box(ctx, x - w / 2, y - h / 2, w, h, [label("cutout", m.caption)], a)
    R.reserved.append((x - w / 2, y - h / 2, x + w / 2, y + h / 2))


def draw_article(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    """기사 프레스 v2(D-0121 §C 콘티 판): 프레스 사진 = 회색 판 + `[프레스: id]`(없으면 블러 무대 폴백 그대로), 덮개·헤드라인 글자는 전편과 같다."""
    from engine.layers.article import article_phase, draw_article_text, draw_press  # noqa: PLC0415

    pa, ta = article_phase(t, e)
    if pa <= 0.01:
        return
    if e.get("press"):
        ctx.set_source_rgba(*PH.fill[:3], PH.fill[3] * pa)
        ctx.paint()
        _lines(ctx, [label("press", e["press"])], W_OUT / 2, PH.line_gap * 2, pa)
    else:
        draw_press(ctx, R, e, pa)
    if ta > 0.01:
        draw_article_text(ctx, e, ta)


def draw_post(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    """layers.post 와 같은 상자(load_project 의 post_box)·페이드·슬라이드."""
    from engine.layers.post import PC, post_alpha  # noqa: PLC0415

    a = post_alpha(t, e)
    if a <= 0.01:
        return
    x0, y, w, h = e["post_box"]
    x = x0 + (1 - ease_out((t - e["t0"]) / PC.fade_sec)) * PC.slide_px
    s = R.cache["sources"][e["src"]]
    who = "개인 계정" if s.account_class == "private" else s.handle
    box(ctx, x, y, w, h, [label("post", who)], a)


def draw_primitive(ctx: cairo.Context, R: RenderCtx, view: View, t: float, e: dict) -> tuple[float, float, float, float]:  # noqa: N803
    """프리미티브 = 제자리 상자(primitive_box — 그리지 않고 잰 상자)·카드 페이드. 예약 영역은 전편처럼 더한다."""
    from engine.primitives import primitive_box  # noqa: PLC0415

    b = primitive_box(e)
    box(ctx, b[0], b[1], b[2] - b[0], b[3] - b[1], [label("primitive", e["id"])],
        window(t, e["t0"], e["t1"], CARD.fade_sec, CARD.fade_sec))
    R.reserved.append(b)
    return b


def draw_band(ctx: cairo.Context, R: RenderCtx, t: float) -> None:  # noqa: N803
    """표식 띠 — 화면 위 가운데(모서리는 날짜만). 전체 페이드 뒤에 그려 암전·타이틀·엔딩 중에도 보인다."""
    w = tw(ctx, BAND.text, BAND.size, BAND.font) + BAND.pad_x * 2
    x = (W_OUT - w) / 2
    ctx.new_path()
    rrect(ctx, x, -BAND.h / 2, w, BAND.h * 1.5, BAND.h / 2)
    ctx.set_source_rgba(*BAND.bg)
    ctx.fill()
    text(ctx, BAND.text, W_OUT / 2, BAND.baseline, BAND.size, BAND.font, BAND.fg[:3], BAND.fg[3], 0, "c")


# ------------------------------------------------------------------ 레이어 선택
def draw_cascade(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    """겹침 카드 = 전편과 같은 자리(cascade.layout)·물러남·밀기. 앞 카드 `[사건: 날짜 · 국기]` + 제목, 뒤 카드 = 보이는 폭만 `[사건: 날짜]`."""
    from engine.cascade import cascade_alpha, layout  # noqa: PLC0415

    ea = cascade_alpha(t, e)
    for c in layout(t, e):
        it = e["items"][c.i]
        w = min(c.w, c.clip_x1 - c.x)
        lines = [label("cascade", it["date"])] if c.back >= 1 / 2 else [label("cascade", f"{it['date']} · {it['flag'].upper()}"), it["title"]]
        box(ctx, c.x, c.y, w, c.h, lines, ea * c.a)


def draw_quote(ctx: cairo.Context, R: RenderCtx, t: float, e: dict) -> None:  # noqa: N803
    """인용(시안) = 전편과 같은 덮개·자리(quote_box — center·upper·lower) — 상자 `[인용: 말한 사람]` + 인용문."""
    from engine.quote import quote_alpha, quote_box, quote_lines  # noqa: PLC0415
    from engine.style import QUOTE as Q  # noqa: PLC0415

    a = quote_alpha(t, e)
    lines = quote_lines(ctx, e)
    if R.cache.get("quote_scrim_t") != t:
        R.cache["quote_scrim_t"] = t
        ctx.rectangle(0, 0, W_OUT, 10_000)
        ctx.set_source_rgba(*Q.scrim_rgb, Q.scrim_alpha * a)
        ctx.fill()
    x0, y0, x1, y1 = quote_box(ctx, e)
    box(ctx, x0, y0, x1 - x0, y1 - y0, [label("quote", e["speaker"]), *lines], a)


PLACEHOLDERS: dict[str, Callable[..., Any]] = {
    "badge": draw_badge, "photo": draw_photo, "clip": draw_clip, "cutout": draw_cutout, "article": draw_article,
    "post": draw_post, "primitive": draw_primitive,   # card·panel 은 v5.6.0 부터 실제로 그린다(PIPELINE-AP-018 — 승인할 수 있는 콘티 판)
    "backdrop": draw_backdrop,   # v5.1.0 D-0123
    "cascade": draw_cascade,         # v5.2.0 겹침 카드(v5.3.0 D-0139 채택)
    "quote": draw_quote,             # v5.3.1 인물 발언 중앙 인용(시안)
}


def resolve_animatic(e: dict | str) -> Entry:
    """전편 레지스트리로 검사(P10)한 뒤, 자리표시 종류면 렌더러만 바꾼 항목. 나머지(마커·경로·시리즈·dip…)는 그대로."""
    ent = resolve(e)
    typ = e if isinstance(e, str) else e["type"]
    typ = typ.split(":", 1)[0]
    return Entry(ent.model, PLACEHOLDERS[typ], ent.stage) if typ in PLACEHOLDERS else ent


ANIMATIC_LAYERS = LayerSet("animatic", resolve_animatic, draw_over_panel, draw_band)

__all__ = ["ANIMATIC_LAYERS", "PLACEHOLDERS", "draw_band", "draw_flat_map", "flat_map_source", "flat_stage_factory", "label", "load_flat_polygons",
           "resolve_animatic"]
