"""site_diagram — 사건 현장 개념도(벡터, 축척 아님) (v4.4.0, dmz_mine_2026 사용자 요청 2026-09-29).

목적: 접경 사건의 현장 구조(북방한계선·군사분계선·남방한계선, 사고 지점, 공식 발표 거리)를 한 장의 개념도로 두고,
내레이션이 사건을 설명하는 순간마다 표시(폭발 아이콘·지뢰·메모)를 **같은 화면 위에 차례로 더한다**.
기존 요소로 안 되는 이유: `photo` 는 래스터라 켄 번스 배율이 정수 픽셀로 바뀌어 글자가 계단식으로 흔들리고(사용자 지적 "끊김"),
한 장의 그림에 시간에 따라 표시를 더할 수 없다(사진을 바꿔 끼우면 화면이 깜박인다). 패널은 지도 무대를 덮는 문서형이다.

불변 층(20 §1.1): 출처 줄(`source`)·기준 날짜(`date`) 필수, "축척·실제 지형 아님"을 적는 `footnote` 필수(개념도를 실제 지도로 오인하지 않게),
판독 최소 크기(rules layout_480p.min_font_px 이상 — glyph_size 검사 대상). 표시(marks)의 문구·거리는 원고·claim 에서 온다(연출이 지어내지 않는다).
등장: 상자 페이드 + 연속 배율(scale_from → 1, cairo 변환 — 래스터 계단 없음). 폭발은 제 시각(t)에 튀어나옴 + 번쩍임, 라벨 페이드.
색 의미: 장르 프로필 color_semantics `confrontation`(군사분계선) · `explosion_opposition`(폭발) · `emphasis`(거리) · `neutral`(메모).
배치: 화면 가운데 고정 상자(rules primitives.site_diagram.x·y·w·h, 자막 영역 위).
"""

from __future__ import annotations

import math
from typing import Literal

import cairo
from pydantic import BaseModel, ConfigDict, Field, field_validator

from engine.style import C, PRIMITIVES
from engine.timebase import ease_out, window
from engine.typography import rrect, text
from script.schema import DATE_RE

L = PRIMITIVES["site_diagram"]
COLOR_KEYS: tuple[str, ...] = ("confrontation", "explosion_opposition", "emphasis", "neutral")
AXIS = "none"   # 값 축 없음(정직성 검사 해당 없음)


class Mark(BaseModel):
    """개념도 위에 제 시각에 더하는 표시 하나."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["burst", "mine", "note"]
    label: str = Field(min_length=1)
    t: float                            # 등장 시각(연출 앵커 → 초)


class SiteDiagram(BaseModel):
    """데이터 모양 — 이벤트 필드(봉투 type·id·t0·t1 밖)."""

    model_config = ConfigDict(extra="forbid")

    header: str                          # 오른쪽 위 한 줄(날짜 · 장소 · 관할)
    north: str                           # 북측 면 이름
    south: str                           # 남측 면 이름
    nll: str                             # 북방한계선 라벨
    mdl: str                             # 군사분계선 라벨
    sll: str                             # 남방한계선 라벨
    width_note: str                      # 비무장지대 폭 메모
    distance: str                        # 사고 지점 거리(공식 발표 문구)
    distance_src: str                    # 그 거리의 출처(예: "합참 발표(9.28)")
    marks: list[Mark] = Field(default_factory=list)
    footnote: str                        # 축척·지형 아님 표기(불변 층 — 필수)
    source: str                          # 출처(불변 층 — 필수)
    date: str                            # 기준 날짜(불변 층 — 필수)

    @field_validator("header", "north", "south", "nll", "mdl", "sll", "width_note", "distance", "distance_src", "footnote", "source")
    @classmethod
    def _filled(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("빈 문자열 — site_diagram 의 문구·출처·축척 표기는 모두 필수")
        return v

    @field_validator("date")
    @classmethod
    def _date(cls, v: str) -> str:
        if not DATE_RE.match(v):
            raise ValueError(f"날짜 형식 YYYY / YYYY.MM / YYYY.MM.DD 만 허용: {v!r}")
        return v

    @field_validator("marks")
    @classmethod
    def _bursts_fit(cls, v: list[Mark]) -> list[Mark]:
        n = sum(m.kind == "burst" for m in v)
        if n > len(L.burst_offsets):
            raise ValueError(f"폭발 표시 {n}개 > 자리 {len(L.burst_offsets)}개(rules primitives.site_diagram.burst_offsets)")
        return v


SCHEMA = SiteDiagram


def _rgba(v: str) -> tuple[float, float, float, float]:
    from engine.primitives import semantic_rgba  # noqa: PLC0415 — 순환 import 회피

    return semantic_rgba(v)


def _box() -> tuple[float, float, float, float]:
    return (L.x, L.y, L.x + L.w, L.y + L.h)


def _wave(x: float) -> float:
    return L.wave_amp_a * math.sin(x / L.wave_len_a) + L.wave_amp_b * math.sin(x / L.wave_len_b)


def _line_y(x: float, top: float, ph: float, v: float) -> float:
    return top + ph * v + _wave(x)


def _curve(ctx: cairo.Context, x0: float, x1: float, fy) -> None:  # noqa: ANN001
    ctx.move_to(x0, fy(x0))
    x = x0
    while x < x1:
        x = min(x1, x + L.wave_step)
        ctx.line_to(x, fy(x))


def _burst(ctx: cairo.Context, x: float, y: float, r: float, fill: tuple, rim: tuple, a: float) -> None:
    n = L.burst_points
    ctx.move_to(x + r, y)
    for i in range(1, n * 2 + 1):
        rr = r if i % 2 == 0 else r * L.burst_inner
        ang = math.pi * i / n
        ctx.line_to(x + rr * math.cos(ang), y + rr * math.sin(ang))
    ctx.close_path()
    ctx.set_source_rgba(*fill[:-1], fill[-1] * a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*rim[:-1], rim[-1] * a)
    ctx.set_line_width(1)
    ctx.stroke()


def _leader(ctx: cairo.Context, x0: float, y0: float, x1: float, y1: float, a: float) -> None:
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.set_source_rgba(*C["white"], L.leader_alpha * a)
    ctx.set_line_width(L.leader_w)
    ctx.stroke()


def draw(ctx: cairo.Context, view: object, t: float, e: dict, style: object) -> tuple[float, float, float, float]:
    """상자: 북측·남측 면 · 세 선 · 사고 지점과 거리 괄호 · 시각별 표시(폭발·지뢰·메모) · 아래 띠(축척 표기·출처)."""
    box = _box()
    a = window(t, e["t0"], e["t1"], L.fade_sec, L.fade_sec)
    if a <= 0:
        return box
    x0, y0, w, h = L.x, L.y, L.w, L.h
    ph = h - L.foot_h                               # 그림 영역 높이
    k = L.scale_from + (1 - L.scale_from) * ease_out((t - e["t0"]) / L.fade_sec)
    cx, cy = x0 + w / 2, y0 + h / 2
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(k, k)
    ctx.translate(-cx, -cy)
    rrect(ctx, x0, y0, w, h, L.radius)
    ctx.clip()

    mdl = lambda x: _line_y(x - x0, y0, ph, L.mdl_v)   # noqa: E731
    nll = lambda x: _line_y(x - x0, y0, ph, L.nll_v)   # noqa: E731
    sll = lambda x: _line_y(x - x0, y0, ph, L.sll_v)   # noqa: E731
    x1 = x0 + w
    # 북측·남측 면
    for fy, edge, col in ((mdl, y0, L.north_bg), (mdl, y0 + ph, L.south_bg)):
        _curve(ctx, x0, x1, fy)
        ctx.line_to(x1, edge)
        ctx.line_to(x0, edge)
        ctx.close_path()
        c = _rgba(col)
        ctx.set_source_rgba(*c[:-1], c[-1] * a)
        ctx.fill()
    fb = _rgba(L.foot_bg)
    ctx.rectangle(x0, y0 + ph, w, L.foot_h)
    ctx.set_source_rgba(*fb[:-1], fb[-1] * a)
    ctx.fill()
    # 남·북방한계선(점선), 군사분계선
    muted, white = C["muted"], C["white"]
    for fy in (nll, sll):
        ctx.save()
        ctx.set_dash(list(L.limit_dash))
        _curve(ctx, x0, x1, fy)
        ctx.set_source_rgba(*muted, L.limit_alpha * a)
        ctx.set_line_width(L.limit_w)
        ctx.stroke()
        ctx.restore()
    red = style.color("confrontation")
    _curve(ctx, x0, x1, mdl)
    ctx.set_source_rgba(*red[:-1], a)
    ctx.set_line_width(L.mdl_w)
    ctx.stroke()
    px = x0 + L.pad_x
    text(ctx, e["nll"], px, nll(px) - L.limit_label_size / 2, L.limit_label_size, "sansm", muted, a, 0, "l")
    text(ctx, e["mdl"], px, mdl(px) - L.mdl_label_size / 2, L.mdl_label_size, "sansb", red[:-1], a, 0, "l")
    text(ctx, e["sll"], px, sll(px) - L.limit_label_size / 2, L.limit_label_size, "sansm", muted, a, 0, "l")
    text(ctx, e["width_note"], px, y0 + ph * L.width_note_v, L.width_note_size, "sansm", muted, a, 0, "l")
    text(ctx, e["header"], x1 - L.pad_x, y0 + L.header_dy, L.header_size, "sansm", white, a, 0, "r")
    text(ctx, e["north"], x1 - L.pad_x, y0 + ph * L.width_note_v, L.side_size, "sansb", C["ru"], a, 0, "r")
    text(ctx, e["south"], x1 - L.pad_x, y0 + ph - L.side_size / 2, L.side_size, "sansb", C["us"], a, 0, "r")

    # 사고 지점 + 거리 괄호선
    sx = x0 + w * L.site_u
    sy = mdl(sx) + L.site_dy
    gold = style.color("emphasis")
    ctx.arc(sx, sy, L.site_ring_r, 0, math.pi * 2)
    ctx.set_source_rgba(*gold[:-1], a / 2 / 2)
    ctx.fill()
    ctx.arc(sx, sy, L.site_r, 0, math.pi * 2)
    ctx.set_source_rgba(*gold[:-1], a)
    ctx.fill()
    bx = sx + L.bracket_du
    ctx.move_to(bx, mdl(bx))
    ctx.line_to(bx, sy)
    for yy in (mdl(bx), sy):
        ctx.move_to(bx - L.bracket_half, yy)
        ctx.line_to(bx + L.bracket_half, yy)
    ctx.set_source_rgba(*gold[:-1], a)
    ctx.set_line_width(L.bracket_w)
    ctx.stroke()
    lx, ly = bx + L.dist_dx, mdl(bx) - L.dist_dy
    _leader(ctx, bx + L.bracket_half, (mdl(bx) + sy) / 2, lx, ly + L.dist_src_gap / 2, a)
    text(ctx, e["distance"], lx, ly, L.dist_size, "sansb", gold[:-1], a, 0, "l")
    text(ctx, e["distance_src"], lx, ly + L.dist_src_gap, L.dist_src_size, "sansm", muted, a, 0, "l")

    # 시각별 표시
    amber = style.color("explosion_opposition")
    teal = style.color("neutral")
    rim = _rgba(L.burst_rim)
    row_l = row_r = 0
    nb = 0
    for m in e.get("marks") or []:
        lt = t - m["t"]
        if lt < 0:
            if m["kind"] == "burst":
                nb += 1   # 아직 안 나온 폭발도 자리 순서는 차지한다
            continue
        la = a * min(1.0, lt / L.label_fade_sec)
        if m["kind"] == "burst":
            dx, dy = L.burst_offsets[nb]
            nb += 1
            bxp, byp = sx + dx, sy + dy
            pop = L.pop_from + (1 - L.pop_from) * ease_out(lt / L.pop_sec)
            fl = max(0.0, 1 - lt / L.flash_sec)
            if fl > 0:
                ctx.arc(bxp, byp, L.flash_r * (1 - fl / 2), 0, math.pi * 2)
                ctx.set_source_rgba(*rim[:-1], fl * a / 2)
                ctx.fill()
            _burst(ctx, bxp, byp, L.burst_r * pop, amber, rim, a)
            tx = x0 + w * L.left_x_u
            ty = y0 + ph * L.label_v + row_l * L.row_h
            row_l += 1
            text(ctx, m["label"], tx, ty, L.label_size, "sansb", white, la, 2, "l")
            _leader(ctx, sx - L.bracket_du * 2, ty - L.label_size / 2, bxp - L.burst_r, byp, la)
        else:
            if m["kind"] == "mine":
                mx, my = sx + L.mine_offset[0], sy + L.mine_offset[1]
                mc = _rgba(L.mine_color)
                ctx.rectangle(mx - L.mine_w / 2, my - L.mine_h / 2, L.mine_w, L.mine_h)
                ctx.set_source_rgba(*mc[:-1], la)
                ctx.fill_preserve()
                ctx.set_source_rgba(*white, la)
                ctx.set_line_width(L.leader_w)
                ctx.stroke()
            tx = x0 + w * L.right_x_u
            ty = y0 + ph * L.label_v + row_r * L.row_h
            row_r += 1
            col = white if m["kind"] == "mine" else teal[:-1]
            text(ctx, m["label"], tx, ty, L.label_size, "sansb" if m["kind"] == "note" else "sansm", col, la, 2, "l")
            if m["kind"] == "mine":
                _leader(ctx, tx - L.leader_w * 2, ty - L.label_size / 2, sx + L.mine_offset[0] + L.mine_w / 2, sy + L.mine_offset[1], la)

    # 아래 띠 — 축척 표기(불변 층) · 출처
    fy = y0 + ph + L.foot_h / 2 + L.foot_size / 2 - 1
    text(ctx, e["footnote"], px, fy, L.foot_size, "sansm", muted, a, 0, "l")
    text(ctx, f"자료: {e['source']}", x1 - L.pad_x, fy, L.foot_size, "sansm", muted, a, 0, "r")
    ctx.restore()
    rrect(ctx, x0 + (1 - k) * w / 2, y0 + (1 - k) * h / 2, w * k, h * k, L.radius)
    ctx.set_source_rgba(*white, a / 2 / 2 / 2)
    ctx.set_line_width(1)
    ctx.stroke()
    return box


PREVIEW_FIXTURE: dict = {
    "type": "primitive",
    "id": "site_diagram",
    "t0": 0.0,
    "t1": 9.0,
    "header": "예시 · 날짜 · 장소",
    "north": "북측",
    "south": "남측",
    "nll": "북방한계선",
    "mdl": "군사분계선(MDL)",
    "sll": "남방한계선",
    "width_note": "비무장지대 폭 약 4km",
    "distance": "MDL 남쪽 약 10m",
    "distance_src": "예시 출처",
    "marks": [
        {"kind": "burst", "label": "① 1차 폭발 — 예시", "t": 2.0},
        {"kind": "burst", "label": "② 2차 폭발 — 예시", "t": 4.0},
        {"kind": "mine", "label": "미폭발 지뢰 — 예시", "t": 5.5},
        {"kind": "note", "label": "추가 발견 — 예시", "t": 6.5},
    ],
    "footnote": "개념도 · 축척·실제 지형 아님",
    "source": "예시 자료(실제 사건 아님)",
    "date": "2026.09",
}
