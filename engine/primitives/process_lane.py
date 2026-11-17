"""process_lane — 과정 도식(단계 알약 · 공개 선 · 인물 표지 · 두 줄 비교) (v7.4.0, 사용자 의견 UF-400 — 영상 분석 보고
docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md §4 D5).

목적: 한 체제·조직이 일을 처리하는 **순서**(예: 내부 결정 → 경쟁자 정리 → | 공개 | → 국내 공개 → 외부 반응 확인)를
한 번 세워 두고, 이야기가 진행되는 동안 인물 표지를 그 단계 위로 옮기거나, 두 사례를 위아래 두 줄로 놓고 걸린 기간을 비교한다.
레퍼런스 영상은 같은 도식을 네 번 다시 불러 "첫 번째 방식 = 두 번째 방식"을 보여 줬다 — 도식은 한 번 세우고 다시 쓰는 설명 모형이다.
기존 요소로 안 되는 이유: `fork`(갈림길)·`gantt`(날짜 막대)·`timeline`(월 눈금)은 단계 순서·공개 경계·표지 이동을 표현하지 못한다.
`flow` 무대(registries.stages_planned)는 구현 전이다.

불변 층(20 §1.1): 출처 줄(`source`)·기준 날짜(`date`) 필수 — 도식은 해석(분석 보고서의 정리)이므로 누구의 분석인지 화면에 남긴다.
판독 최소 크기(rules layout_480p.min_font_px 이상 — glyph_size 검사 대상). 단계 이름·표지 이름·기간 문구는 원고·claim 에서 온다.
등장: 상자 페이드 → 단계 알약이 왼쪽부터 차례로(step_stagger_sec) → 공개 선이 위에서 아래로 자람. 표지는 `moves` 시각에 5차 이징으로
옆 단계로 미끄러진다(카메라 이징과 같은 곡선). 표지가 아직 닿지 않은 단계는 옅게(ghost_alpha) — 앞으로 갈 길을 미리 보인다.
색 의미: 장르 프로필 color_semantics `emphasis`(표지·도달한 단계 테두리·기간 괄호) · `secondary_text`(공개 선·비공개 구역 이름).
배치: 화면 가운데 고정 상자(rules primitives.process_lane.x·y·w, 자막 영역 위). 높이 = 줄 수로 정한다.
"""

from __future__ import annotations

import math
from typing import Optional

import cairo
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engine import skin
from engine.primitives import geo, ink, skin_card, skin_on, skin_rule, skin_text
from engine.style import C, CARD, CARD_BG, PRIMITIVES, SKIN, hexc
from engine.timebase import ease_out, ease_quintic, window
from engine.typography import rrect, text, tw, wrap
from script.schema import DATE_RE

L = PRIMITIVES["process_lane"]
SK = SKIN.primitives.process_lane   # v7.4.0 3c(UF-906) — skin 무대 판(rules skin.primitives.process_lane)
META = "media_meta"   # 출처·날짜 메타 글자 역할(qa_checks.glyph_size_exempt)
COLOR_KEYS: tuple[str, ...] = ("emphasis", "secondary_text")
AXIS = "none"   # 값 축 없음(정직성 검사 해당 없음, engine/honesty.py)


class Move(BaseModel):
    """표지 이동 하나 — 시각 t(연출 앵커 → 초)에 단계 at 으로 미끄러진다."""

    model_config = ConfigDict(extra="forbid")

    t: float
    at: int = Field(ge=0)


class Span(BaseModel):
    """기간 괄호 — 단계 from_step ~ to_step 위에 걸리는 문구(예: "6년"). 시각 t 에 나타난다."""

    model_config = ConfigDict(extra="forbid")

    from_step: int = Field(ge=0)
    to_step: int = Field(ge=0)
    label: str = Field(min_length=1)
    t: float


class Row(BaseModel):
    """한 줄(한 사례). label 은 왼쪽 열 이름(두 줄 비교 때 "첫 번째" 등), token 은 표지 이름(인물)."""

    model_config = ConfigDict(extra="forbid")

    label: str = ""
    token: str = Field(min_length=1)
    at: int = Field(default=0, ge=0)          # 처음 자리
    moves: list[Move] = Field(default_factory=list)
    span: Optional[Span] = None
    t: Optional[float] = None                 # 이 줄이 나타나는 시각(없으면 상자와 함께). 두 번째 줄을 나중에 붙일 때

    @field_validator("moves")
    @classmethod
    def _ordered(cls, v: list[Move]) -> list[Move]:
        if any(b.t < a.t for a, b in zip(v, v[1:])):
            raise ValueError("moves 는 시각 순서대로")
        return v


class ProcessLane(BaseModel):
    """데이터 모양 — 이벤트 필드(봉투 type·id·t0·t1 밖)."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)          # 머리 한 줄(예: "후계자를 알리는 순서")
    steps: list[str] = Field(description=f"단계 이름 {L.steps_min}~{L.steps_max}개, 각 {L.step_chars_max}자 이하")
    gate_after: int = Field(ge=0, description="공개 선 앞(비공개 구역)의 마지막 단계 번호(0부터)")
    gate_label: str = Field(min_length=1)     # 공개 선 이름(예: "공개")
    hidden_label: str = Field(min_length=1)   # 비공개 구역 이름(예: "비공개")
    rows: list[Row] = Field(description=f"줄 1~{L.rows_max}개 — 두 줄이면 위아래로 두 사례 비교")
    source: str                               # 출처(불변 층 — 필수): 누구의 분석·정리인가
    date: str = Field(description="YYYY | YYYY.MM | YYYY.MM.DD(점, 하이픈 금지)")

    @field_validator("steps")
    @classmethod
    def _steps(cls, v: list[str]) -> list[str]:
        if not L.steps_min <= len(v) <= L.steps_max:
            raise ValueError(f"단계 {len(v)}개 — rules primitives.process_lane.steps_min~steps_max({L.steps_min}~{L.steps_max})")
        for s in v:
            if not s.strip():
                raise ValueError("빈 단계 이름")
            if len(s) > L.step_chars_max:
                raise ValueError(f"단계 이름 {s!r} {len(s)}자 > step_chars_max {L.step_chars_max}")
        return v

    @field_validator("rows")
    @classmethod
    def _rows(cls, v: list[Row]) -> list[Row]:
        if not 1 <= len(v) <= L.rows_max:
            raise ValueError(f"줄 {len(v)}개 — 1~{L.rows_max}")
        return v

    @field_validator("source")
    @classmethod
    def _filled(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("빈 출처 — process_lane 은 누구의 분석인지 출처 줄이 필수")
        return v

    @field_validator("date")
    @classmethod
    def _date(cls, v: str) -> str:
        if not DATE_RE.match(v):
            raise ValueError(f"date 형식 {v!r} — YYYY | YYYY.MM | YYYY.MM.DD")
        return v

    @model_validator(mode="after")
    def _indices(self) -> "ProcessLane":
        n = len(self.steps)
        if self.gate_after >= n - 1:
            raise ValueError(f"gate_after {self.gate_after} — 공개 선 뒤에 단계가 하나 이상 있어야 한다(단계 {n}개)")
        for r in self.rows:
            idx = [r.at, *(m.at for m in r.moves)]
            if r.span is not None:
                idx += [r.span.from_step, r.span.to_step]
                if r.span.to_step < r.span.from_step:
                    raise ValueError(f"span {r.span.from_step}→{r.span.to_step} — 거꾸로")
            bad = [i for i in idx if i >= n]
            if bad:
                raise ValueError(f"줄 {r.token!r} 단계 번호 {bad} ≥ 단계 수 {n}")
        return self


SCHEMA = ProcessLane


def _with_label_col(e: dict) -> bool:
    return any(r.get("label") for r in e["rows"])


def layout(e: dict) -> dict:
    """제자리 기하(설계 px) — 상자·줄 중심·알약 x 범위."""
    G = geo("process_lane")  # noqa: N806 — skin 무대면 skin.primitives.process_lane.layout 덮어쓰기
    n = len(e["steps"])
    rows = len(e["rows"])
    h = G.head_h + G.row_h * rows + G.foot_h
    x0 = G.x + G.pad_x + (G.label_col_w if _with_label_col(e) else 0)
    inner = G.x + G.w - G.pad_x - x0 - G.arrow_len
    pill_w = (inner - G.pill_gap * (n - 1)) / n
    pills = [(x0 + i * (pill_w + G.pill_gap), pill_w) for i in range(n)]
    gate_x = pills[e["gate_after"]][0] + pill_w + G.pill_gap / 2
    row_y = [G.y + G.head_h + G.row_h * (i + 1) - G.pill_dy for i in range(rows)]
    return {"box": (G.x, G.y, G.x + G.w, G.y + h), "h": h, "pills": pills, "pill_w": pill_w, "gate_x": gate_x, "row_y": row_y,
            "axis_x1": G.x + G.w - G.pad_x}


def token_pos(r: dict, t: float) -> float:
    """시각 t 의 표지 자리(단계 번호, 실수) — moves 사이 5차 이징(카메라와 같은 곡선)."""
    pos = float(r.get("at", 0))
    for m in r.get("moves") or []:
        if t <= m["t"]:
            break
        p = ease_quintic((t - m["t"]) / L.move_sec)
        pos = pos + (m["at"] - pos) * p
    return pos


def _pill_x(g: dict, pos: float) -> float:
    """단계 번호(실수) → 알약 가운데 x(선형 보간)."""
    i = min(int(pos), len(g["pills"]) - 1)
    f = pos - i
    cx = g["pills"][i][0] + g["pill_w"] / 2
    if f <= 0 or i + 1 >= len(g["pills"]):
        return cx
    nx = g["pills"][i + 1][0] + g["pill_w"] / 2
    return cx + (nx - cx) * f


def draw(ctx: cairo.Context, view: object, t: float, e: dict, style: object) -> tuple[float, float, float, float]:
    """상자 · 머리 · 줄마다 비공개 구역 · 단계 알약(도달 = 진하게, 미도달 = 옅게) · 축 화살표 · 공개 선 · 표지 · 기간 괄호 · 출처 줄."""
    g = layout(e)
    box = g["box"]
    a = window(t, e["t0"], e["t1"], L.fade_sec, L.fade_sec)
    if a <= 0:
        return box
    x, y = box[0], box[1]
    if skin_on():
        _draw_skin(ctx, t, e, g, a)
        return box
    em = style.color("emphasis")            # type: ignore[attr-defined]
    sec = style.color("secondary_text")     # type: ignore[attr-defined]
    white = C["white"]
    rrect(ctx, x, y, L.w, g["h"], L.radius)
    ctx.set_source_rgba(*CARD_BG[:-1], CARD_BG[-1] * a)
    ctx.fill()
    text(ctx, e["title"], x + L.pad_x, y + L.title_dy, L.title_size, "sansb", white, a, 0, "l")
    # 공개 선 — 머리 아래에서 마지막 줄 아래까지 자란다
    grow = ease_out((t - e["t0"] - L.gate_delay_sec) / L.gate_grow_sec)
    gx = g["gate_x"]
    gy0 = y + L.head_h - L.gate_over
    gy1 = g["row_y"][-1] + L.pill_h / 2 + L.gate_under
    if grow > 0:
        ctx.set_source_rgba(*sec[:-1], sec[-1] * a)
        ctx.set_line_width(L.gate_w)
        ctx.move_to(gx, gy0)
        ctx.line_to(gx, gy0 + (gy1 - gy0) * grow)
        ctx.stroke()
        text(ctx, e["gate_label"], gx, gy0 - L.gate_label_dy, L.gate_label_size, "sansb", sec[:-1], a * grow * sec[-1], 0, "c")
    for ri, r in enumerate(e["rows"]):
        ra = a if r.get("t") is None else a * window(t, r["t"], e["t1"], L.fade_sec, L.fade_sec)
        if ra <= 0:
            continue
        cy = g["row_y"][ri]
        if r.get("label"):
            text(ctx, r["label"], x + L.pad_x, cy + L.row_label_dy, L.row_label_size, "sansb", sec[:-1], ra * sec[-1], 0, "l")
        # 비공개 구역 — 공개 선 앞 알약을 감싸는 옅은 면 + 이름
        hx0 = g["pills"][0][0] - L.hidden_pad
        hy0 = cy - L.pill_h / 2 - L.hidden_top
        rrect(ctx, hx0, hy0, gx - L.hidden_gap - hx0, L.pill_h + L.hidden_top + L.hidden_pad, L.radius)
        ctx.set_source_rgba(*white, L.hidden_alpha * ra)
        ctx.fill()
        text(ctx, e["hidden_label"], hx0 + L.hidden_label_dx, hy0 + L.hidden_label_dy, L.hidden_label_size, "sansb", sec[:-1],
             ra * sec[-1], 0, "l")
        # 축 화살표(알약 가운데를 지나는 선)
        ctx.set_source_rgba(*white, L.axis_alpha * ra)
        ctx.set_line_width(L.axis_w)
        ctx.move_to(g["pills"][0][0], cy)
        ctx.line_to(g["axis_x1"], cy)
        ctx.stroke()
        ctx.move_to(g["axis_x1"], cy)
        ctx.line_to(g["axis_x1"] - L.arrow_len, cy - L.arrow_half)
        ctx.line_to(g["axis_x1"] - L.arrow_len, cy + L.arrow_half)
        ctx.close_path()
        ctx.fill()
        pos = token_pos(r, t)
        for i, (px, pw) in enumerate(g["pills"]):
            pa = ra * ease_out((t - (r.get("t") or e["t0"]) - L.step_stagger_sec * i) / L.step_fade_sec)
            if pa <= 0:
                continue
            reached = i <= pos + L.reach_eps
            k = 1.0 if reached else L.ghost_alpha
            rrect(ctx, px, cy - L.pill_h / 2, pw, L.pill_h, L.pill_h / 2)
            ctx.set_source_rgba(*CARD_BG[:-1], L.pill_base_alpha * pa)   # 축선이 글자 뒤로 비치지 않게 바닥을 먼저 막는다
            ctx.fill_preserve()
            ctx.set_source_rgba(*white, L.pill_fill_alpha * pa * k)
            ctx.fill_preserve()
            ctx.set_source_rgba(*(em[:-1] if reached else white), (em[-1] if reached else L.pill_line_alpha) * pa * k)
            ctx.set_line_width(L.pill_line_w)
            ctx.stroke()
            lines = wrap(ctx, e["steps"][i], pw - L.pill_pad_x * 2, L.step_size, "sansb")[:L.step_lines_max]
            top = cy - (len(lines) - 1) * L.step_line_h / 2 + L.step_size * L.step_baseline
            for j, ln in enumerate(lines):
                text(ctx, ln, px + pw / 2, top + j * L.step_line_h, L.step_size, "sansb", white, pa * k, 0, "c")
        # 기간 괄호(줄 위, 표지보다 먼저 그려 표지가 덮는다)
        sp = r.get("span")
        if sp is not None:
            sa = ra * ease_out((t - sp["t"]) / L.span_fade_sec)
            if sa > 0:
                bx0 = g["pills"][sp["from_step"]][0]
                bx1 = g["pills"][sp["to_step"]][0] + g["pill_w"]
                by = cy - L.pill_h / 2 - L.span_dy
                ctx.set_source_rgba(*em[:-1], em[-1] * sa)
                ctx.set_line_width(L.span_w)
                ctx.move_to(bx0, by + L.span_tick)
                ctx.line_to(bx0, by)
                ctx.line_to(bx1, by)
                ctx.line_to(bx1, by + L.span_tick)
                ctx.stroke()
                text(ctx, sp["label"], (bx0 + bx1) / 2, by - L.span_label_dy, L.span_size, "sansb", em[:-1], sa * em[-1], 0, "c")
        # 표지 — 단계 위에 떠 있는 원 + 이름
        tx = _pill_x(g, pos)
        ty = cy - L.pill_h / 2 - L.token_dy
        ta = ra * ease_out((t - (r.get("t") or e["t0"]) - L.token_delay_sec) / L.step_fade_sec)
        if ta > 0:
            ctx.arc(tx, ty, L.token_r, 0, 2 * math.pi)
            ctx.set_source_rgba(*em[:-1], em[-1] * ta)
            ctx.fill()
            text(ctx, r["token"], tx + L.token_r + L.token_label_dx, ty + L.token_label_dy, L.token_label_size, "sansb", white, ta, 0, "l")
    text(ctx, f"{e['source']} · {e['date']}", x + L.pad_x, y + g["h"] - L.src_dy, CARD.src_size, "sans", C["muted"], a, 0, "l")
    return box


def _draw_skin(ctx: cairo.Context, t: float, e: dict, g: dict, a: float) -> None:
    """skin 판(v7.4.0 3c·UF-906) — 흰 직각 카드. 머리(잉크) · 비공개 구역 = 가는 점선 윤곽(회색 면 없음) · 축 = 가는 잉크 선 + 작은 화살촉 ·
    단계 = 흰 알약(도달 = 잉크 윤곽 + 그림자, 미도달 = 옅은 윤곽 + 옅은 글자) · 번호 = 알약 위 끝에 걸친 작은 원(도달 = 강조, 흰 숫자) ·
    공개 선 = 잉크 · 기간 괄호 = 가는 잉크 + 강조 글자 · 표지 = 작은 짙은 원(흰 테) · 출처 위 가는 선 · 출처 줄. 시각·이동은 종전과 같다."""
    G = geo("process_lane")  # noqa: N806
    x, y = g["box"][0], g["box"][1]
    skin_card(ctx, (x, y, G.w, g["h"]), a)
    skin_text(ctx, SK.title, e["title"], x + G.pad_x, y + G.title_dy, a)
    white = hexc(SKIN.surface.fill)
    grow = ease_out((t - e["t0"] - G.gate_delay_sec) / G.gate_grow_sec)
    gx = g["gate_x"]
    gy0 = y + G.head_h - G.gate_over
    gy1 = g["row_y"][-1] + G.pill_h / 2 + G.gate_under
    if grow > 0:
        ctx.new_path()
        ctx.move_to(gx, gy0)
        ctx.line_to(gx, gy0 + (gy1 - gy0) * grow)
        ctx.set_source_rgba(*skin.INK, SK.gate.alpha * a)
        ctx.set_line_width(SK.gate.w)
        ctx.stroke()
        skin_text(ctx, SK.gate_label, e["gate_label"], gx, gy0 - G.gate_label_dy, a * grow, "c")
    for ri, r in enumerate(e["rows"]):
        ra = a if r.get("t") is None else a * window(t, r["t"], e["t1"], G.fade_sec, G.fade_sec)
        if ra <= 0:
            continue
        cy = g["row_y"][ri]
        if r.get("label"):
            skin_text(ctx, SK.row_label, r["label"], x + G.pad_x, cy + G.row_label_dy, ra)
        hx0 = g["pills"][0][0] - G.hidden_pad
        hy0 = cy - G.pill_h / 2 - G.hidden_top
        ctx.save()
        ctx.set_dash(list(SK.hidden.dash))
        ctx.rectangle(hx0, hy0, gx - G.hidden_gap - hx0, G.pill_h + G.hidden_top + G.hidden_pad)
        ctx.set_source_rgba(*skin.INK, SK.hidden.alpha * ra)
        ctx.set_line_width(SK.hidden.w)
        ctx.stroke()
        ctx.restore()
        skin_text(ctx, SK.hidden_label, e["hidden_label"], hx0 + G.hidden_label_dx, hy0 + G.hidden_label_dy, ra)
        ctx.new_path()
        ctx.move_to(g["pills"][0][0], cy)
        ctx.line_to(g["axis_x1"], cy)
        ctx.set_source_rgba(*skin.INK, SK.axis.alpha * ra)
        ctx.set_line_width(SK.axis.w)
        ctx.stroke()
        ctx.move_to(g["axis_x1"], cy)
        ctx.line_to(g["axis_x1"] - G.arrow_len, cy - G.arrow_half)
        ctx.line_to(g["axis_x1"] - G.arrow_len, cy + G.arrow_half)
        ctx.close_path()
        ctx.set_source_rgba(*skin.INK, SK.arrow_alpha * ra)
        ctx.fill()
        pos = token_pos(r, t)
        for i, (px, pw) in enumerate(g["pills"]):
            pa = ra * ease_out((t - (r.get("t") or e["t0"]) - G.step_stagger_sec * i) / G.step_fade_sec)
            if pa <= 0:
                continue
            reached = i <= pos + G.reach_eps
            pbox = (px, cy - G.pill_h / 2, pw, G.pill_h)
            skin.pill(ctx, pbox, white, pa, SK.pill_level if reached else None)
            ln_ = SK.pill_line if reached else SK.pill_ghost_line
            rrect(ctx, *pbox, G.pill_h / 2)
            ctx.set_source_rgba(*skin.INK, ln_.alpha * pa)
            ctx.set_line_width(ln_.w)
            ctx.stroke()
            col = ink(SK.step.ink if reached else SK.step_ghost_ink)
            lines = wrap(ctx, e["steps"][i], pw - G.pill_pad_x * 2, SK.step.size, SK.step.font)[:G.step_lines_max]
            top = cy - (len(lines) - 1) * G.step_line_h / 2 + SK.step.size * G.step_baseline
            for j, ln in enumerate(lines):
                skin_text(ctx, SK.step, ln, px + pw / 2, top + j * G.step_line_h, pa, "c", col=col)
            nx, ny = px + SK.num.dx, cy - G.pill_h / 2
            ctx.arc(nx, ny, SK.num.r, 0, 2 * math.pi)
            ctx.set_source_rgba(*(ink("accent") if reached else ink(SK.num.ghost_ink)), pa)
            ctx.fill()
            text(ctx, str(i + 1), nx, ny + SK.num.size * G.step_baseline, SK.num.size, SK.num.font, white, pa, 0, "c")
        sp = r.get("span")
        if sp is not None:
            sa = ra * ease_out((t - sp["t"]) / G.span_fade_sec)
            if sa > 0:
                bx0 = g["pills"][sp["from_step"]][0]
                bx1 = g["pills"][sp["to_step"]][0] + g["pill_w"]
                by = cy - G.pill_h / 2 - G.span_dy
                ctx.new_path()
                ctx.move_to(bx0, by + G.span_tick)
                ctx.line_to(bx0, by)
                ctx.line_to(bx1, by)
                ctx.line_to(bx1, by + G.span_tick)
                ctx.set_source_rgba(*skin.INK, SK.span.alpha * sa)
                ctx.set_line_width(SK.span.w)
                ctx.stroke()
                skin_text(ctx, SK.span_label, sp["label"], (bx0 + bx1) / 2, by - G.span_label_dy, sa, "c")
        tx = _pill_x(g, pos)
        ty = cy - G.pill_h / 2 - G.token_dy
        ta = ra * ease_out((t - (r.get("t") or e["t0"]) - G.token_delay_sec) / G.step_fade_sec)
        if ta > 0:
            tb = (tx - G.token_r, ty - G.token_r, G.token_r * 2, G.token_r * 2)
            skin.pill(ctx, tb, white, ta, SK.token_level)
            ctx.arc(tx, ty, G.token_r - SK.token_ring_w, 0, 2 * math.pi)
            ctx.set_source_rgba(*skin.INK, ta)
            ctx.fill()
            skin_text(ctx, SK.token_label, r["token"], tx + G.token_r + G.token_label_dx, ty + G.token_label_dy, ta)
    sy = y + g["h"] - G.src_dy
    skin_rule(ctx, x + G.pad_x, x + G.w - G.pad_x, sy - SK.foot_rule.dy, SK.foot_rule, a)
    skin_text(ctx, SK.src, f"{e['source']} · {e['date']}", x + G.pad_x, sy, a, role=META)


PREVIEW_FIXTURE: dict = {
    "type": "primitive",
    "id": "process_lane",
    "t0": 0.0,
    "t1": 10.0,
    "title": "후계를 알리는 순서 · 예시",
    "steps": ["내부 결정", "경쟁자 정리", "국내 공개", "외부 반응 확인"],
    "gate_after": 1,
    "gate_label": "공개",
    "hidden_label": "비공개",
    "rows": [
        {"label": "첫 사례", "token": "후계자 A", "at": 0, "moves": [{"t": 3.0, "at": 1}, {"t": 6.0, "at": 2}],
         "span": {"from_step": 0, "to_step": 1, "label": "6년", "t": 4.5}},
        {"label": "둘째 사례", "token": "후계자 B", "at": 1, "t": 5.0,
         "span": {"from_step": 1, "to_step": 1, "label": "1년여", "t": 7.0}},
    ],
    "source": "예시 도식(실제 분석 아님)",
    "date": "2026.11",
}
