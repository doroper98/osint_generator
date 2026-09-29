"""시간축 무대(TimelineStage) — x = 시간, y = 레인 (v4.3.0, docs/handoff/20 §2.1·§2.3·§6, back_and_forth D-0084 작업 3·D-0085).

월드 좌표:
- x = 무대 시작일(`start`, 기준일)로부터의 **일수**(float). 압축 구간(`compress: [{from, to, factor}]`) 안은 일수 × factor.
  `to_world`·`from_world` 가 압축을 왕복한다(경계에서 연속·단조 증가).
- y = 레인. 레인 i(위에서부터 0) 의 띠는 [n − i − 1, n − i], 가운데 n − i − 0.5. 레인 간격 1.0, bounds = [0, 0, x(end), n].
- 세로 척도는 무대가 고정한다(D-0085 A): `y_px_per_unit` = rules stage_timeline.lane_h(설계 px). 카메라 w 는 시간 폭만 바꾼다.
  레인 총높이가 레인 영역(area_top ~ area_bottom)보다 작으면 영역 가운데, 크면 카메라 y 로 세로 위치를 고른다(`frame_y1`).

그리기: render_base = 바탕·레인 띠·시간 격자(LOD)·압축 구간 물결 + "압축" 라벨(20 §2.3·§5.3 정직성).
draw_labels = 레인 이름(왼쪽 고정, 단위 포함)·날짜 눈금 라벨(LOD — 넓으면 연도, 확대하면 분기·월·일, 20 §6).
수치·색은 전부 `rules stage_timeline`(코드 리터럴 0, tests/anti_inertia/test_no_magic_numbers).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Any, Optional, Union

import cairo
from pydantic import BaseModel, ConfigDict, Field, model_validator

from engine.style import C, TIMELINE, W_OUT
from engine.typography import text
from schemas.genre_models import TimelineLane

if TYPE_CHECKING:
    from engine.assets import Assets
    from engine.projection import View

DateLike = Union[str, date]
MONTHS = 12


class TimelineError(ValueError):
    """시간축 무대 구성·앵커 오류(15 P6)."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Compress(_Strict):
    """압축 구간 — [from, to) 의 하루를 factor 일로 그린다(0 < factor < 1). 화면에는 물결 + "압축" 라벨이 반드시 보인다."""

    from_: date = Field(alias="from")
    to: date
    factor: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def _order(self) -> "Compress":
        if self.to <= self.from_:
            raise ValueError(f"압축 구간 from {self.from_} ≥ to {self.to}")
        return self


class TimelineConfig(_Strict):
    """direction `stage_config.timeline`(레인은 장르 프로필 stage.timeline.lanes 가 기본값, direction 이 덮는다)."""

    start: date
    end: date
    lanes: list[TimelineLane] = Field(min_length=1)
    compress: list[Compress] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> "TimelineConfig":
        if self.end <= self.start:
            raise ValueError(f"timeline end {self.end} ≤ start {self.start}")
        ids = [ln.id for ln in self.lanes]
        if len(set(ids)) != len(ids):
            raise ValueError(f"레인 id 중복: {ids}")
        zs = sorted(self.compress, key=lambda z: z.from_)
        for z in zs:
            if z.from_ < self.start or z.to > self.end:
                raise ValueError(f"압축 구간 {z.from_}~{z.to} 가 무대 {self.start}~{self.end} 밖")
        for a, b in zip(zs, zs[1:]):
            if b.from_ < a.to:
                raise ValueError(f"압축 구간이 겹친다: {a.from_}~{a.to} / {b.from_}~{b.to}")
        self.compress = zs
        return self


def as_date(v: DateLike) -> date:
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(v)
    except (TypeError, ValueError) as ex:
        raise TimelineError(f"날짜 앵커는 YYYY-MM-DD: {v!r}") from ex


def add_months(d: date, n: int) -> date:
    k = d.year * MONTHS + d.month - 1 + n
    return date(k // MONTHS, k % MONTHS + 1, 1)


class TimelineStage:
    """시간축 캔버스(20 §2.1 `TimelineStage`). 앵커 = (date, lane). lane = 레인 id 문자열(D-0085 — 인덱스 숫자 금지)."""

    name = "timeline"
    anchor_keys = ("date", "lane")

    def __init__(self, assets: "Optional[Assets]" = None, *, out: object = None,
                 config: "Optional[Union[TimelineConfig, dict]]" = None) -> None:
        """out(출력 프로파일)은 받기만 한다 — 벡터만 그려 장치 해상도가 필요 없다(D-0067: 변환은 렌더 진입 한 곳)."""
        if config is None:
            raise TimelineError("timeline 무대는 설정이 필요하다 — direction stage_config.timeline {start, end, lanes?, compress?}")
        self.cfg = config if isinstance(config, TimelineConfig) else TimelineConfig.model_validate(config)
        self.assets = assets
        self.lanes = list(self.cfg.lanes)
        self.n = len(self.lanes)
        self._idx = {ln.id: i for i, ln in enumerate(self.lanes)}
        self.y_px_per_unit: float = TIMELINE.lane_h
        self._bounds = (0.0, 0.0, self.x_of(self.cfg.end), float(self.n))

    # --- 좌표
    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return self._bounds

    def x_of(self, d: DateLike) -> float:
        """날짜 → 월드 x(시작일부터 일수, 압축 적용)."""
        dd = as_date(d)
        raw = float((dd - self.cfg.start).days)
        for z in self.cfg.compress:
            a, b = float((z.from_ - self.cfg.start).days), float((z.to - self.cfg.start).days)
            inside = min(max(raw, a), b) - a
            raw -= inside * (1 - z.factor)
        return raw

    def date_of(self, x: float) -> float:
        """월드 x → 시작일부터 실제 일수(float). x_of 의 역."""
        raw = x
        for z in self.cfg.compress:
            a = self.x_of(z.from_)
            span = float((z.to - z.from_).days)
            if raw <= a:
                break
            inside = min(raw - a, span * z.factor)
            raw += inside / z.factor - inside
        return raw

    def lane_index(self, lane: str) -> int:
        if lane not in self._idx:
            raise TimelineError(f"레인 {lane!r} 없음 — 무대 레인: {list(self._idx)}")
        return self._idx[lane]

    def lane_y(self, lane: str) -> tuple[float, float]:
        """레인 띠의 월드 y 범위 (아래, 위)."""
        i = self.lane_index(lane)
        return float(self.n - i - 1), float(self.n - i)

    def to_world(self, **anchor: Any) -> tuple[float, float]:
        keys = set(anchor)
        if not keys <= set(self.anchor_keys) or "date" not in keys:
            raise TimelineError(f"timeline 앵커는 date(필수)·lane: {sorted(keys)}")
        lane = anchor.get("lane")
        if lane is None:
            y = self.n / 2
        else:
            if not isinstance(lane, str):
                raise TimelineError(f"lane 은 레인 id 문자열(인덱스 숫자 금지, D-0085): {lane!r}")
            lo, hi = self.lane_y(lane)
            y = (lo + hi) / 2
        return self.x_of(anchor["date"]), y

    def from_world(self, x: float, y: float) -> dict[str, Any]:
        d = self.cfg.start + timedelta(days=round(self.date_of(x)))
        i = min(self.n - 1, max(0, int(self.n - y)))
        return {"date": d.isoformat(), "lane": self.lanes[i].id}

    def frame_y1(self, cam_y: float, h: float) -> float:
        """View 의 위 끝 월드 y(D-0085): 레인 총높이 ≤ 레인 영역이면 영역 가운데 고정, 아니면 카메라 y 를 영역 안으로 클램프."""
        T = TIMELINE  # noqa: N806
        s = self.y_px_per_unit
        area = T.area_bottom - T.area_top
        total = self.n * s
        if total <= area:
            return self.n + (T.area_top + (area - total) / 2) / s
        hi = self.n + T.area_top / s
        lo = hi - (total - area) / s
        return min(max(cam_y + (T.area_top + T.area_bottom) / 2 / s, lo), hi)

    # --- LOD
    def lod_rules(self) -> dict[str, Any]:
        return TIMELINE.lod.model_dump()

    def tick_unit(self, w: float) -> str:
        """화면 폭 w(일) → 눈금 단위(20 §6 LOD: 넓으면 연도 → 분기 → 월 → 일)."""
        L = TIMELINE.lod  # noqa: N806
        if w < L.day_below_w:
            return "day"
        if w < L.month_below_w:
            return "month"
        if w < L.quarter_below_w:
            return "quarter"
        return "year"

    def ticks(self, view: "View") -> list[tuple[date, str]]:
        """보이는 눈금 [(날짜, 종류)] — 종류 = year(연 경계) 또는 minor. 압축 구간 안은 연 경계만."""
        unit = self.tick_unit(view.w)
        d0 = self.cfg.start + timedelta(days=int(self.date_of(max(view.x0, 0.0))) - 1)
        d1 = self.cfg.start + timedelta(days=int(self.date_of(min(view.x0 + view.w, self._bounds[2]))) + 1)
        out: list[tuple[date, str]] = []
        if unit == "day":
            step = TIMELINE.lod.day_label_every
            d = d0
            while d <= d1:
                if d.day == 1 and d.month == 1:
                    out.append((d, "year"))
                elif (d.day - 1) % step == 0:
                    out.append((d, "minor"))
                d += timedelta(days=1)
            return out
        months = {"month": 1, "quarter": MONTHS // 4, "year": MONTHS}[unit]
        d = date(d0.year, 1, 1)
        while d <= d1:
            if d >= d0:
                out.append((d, "year" if d.month == 1 else "minor"))
            d = add_months(d, months)
        return [(d, k) for d, k in out if k == "year" or not self.in_compress(d)]

    def in_compress(self, d: date) -> bool:
        return any(z.from_ <= d < z.to for z in self.cfg.compress)

    def tick_label(self, d: date, unit: str) -> str:
        if d.month == 1 and d.day == 1:
            return f"{d.year}"
        if unit == "day":
            return f"{d.month}.{d.day}"
        if unit == "quarter":
            return f"{(d.month - 1) // (MONTHS // 4) + 1}분기"
        return f"{d.month}월"

    # --- 배경
    def lane_screen(self, view: "View", i: int) -> tuple[float, float]:
        """레인 i 띠의 화면 y (위, 아래)."""
        _, top = view.to_screen(0.0, float(self.n - i))
        _, bot = view.to_screen(0.0, float(self.n - i - 1))
        return top, bot

    def render_base(self, ctx: cairo.Context, view: "View") -> None:
        T = TIMELINE  # noqa: N806
        ctx.set_source_rgb(*T.bg_rgb)
        ctx.paint()
        for i in range(self.n):
            top, bot = self.lane_screen(view, i)
            ctx.rectangle(0, top, W_OUT, bot - top)
            ctx.set_source_rgba(*C["white"], T.band_alpha[i % len(T.band_alpha)])
            ctx.fill()
            ctx.move_to(0, bot)
            ctx.line_to(W_OUT, bot)
            ctx.set_source_rgba(*C["white"], T.lane_line_alpha)
            ctx.set_line_width(T.lane_line_w)
            ctx.stroke()
        top, _ = self.lane_screen(view, 0)
        _, bot = self.lane_screen(view, self.n - 1)
        for d, kind in self.ticks(view):
            x, _ = view.to_screen(self.x_of(d), 0.0)
            ctx.move_to(x, top)
            ctx.line_to(x, bot)
            ctx.set_source_rgba(*C["white"], T.grid.year_alpha if kind == "year" else T.grid.minor_alpha)
            ctx.set_line_width(T.grid.line_w)
            ctx.stroke()
        for z in self.cfg.compress:
            self._draw_compress(ctx, view, z, top, bot)

    def _draw_compress(self, ctx: cairo.Context, view: "View", z: Compress, top: float, bot: float) -> None:
        """압축 구간: 옅은 가림 + 양 끝 물결 선 + "압축" 라벨(정직성 — 압축 메타가 있으면 화면에 반드시 보인다)."""
        W = TIMELINE.wave  # noqa: N806
        xa, _ = view.to_screen(self.x_of(z.from_), 0.0)
        xb, _ = view.to_screen(self.x_of(z.to), 0.0)
        if xb < 0 or xa > W_OUT:
            return
        ctx.rectangle(xa, top, xb - xa, bot - top)
        ctx.set_source_rgba(*TIMELINE.bg_rgb, W.shade_alpha)
        ctx.fill()
        for x in (xa, xb):
            ctx.new_path()
            y = top
            k = 0
            ctx.move_to(x, y)
            while y < bot:
                y = min(bot, y + W.period_px / 2)
                k += 1
                ctx.line_to(x + (W.amp_px if k % 2 else -W.amp_px), y)
            ctx.set_source_rgba(*C[W.color], W.alpha)
            ctx.set_line_width(W.line_w)
            ctx.stroke()
        cx = min(max((max(xa, 0.0) + min(xb, float(W_OUT))) / 2, W.label_margin_px), W_OUT - W.label_margin_px)
        text(ctx, W.label, cx, top + W.label_dy, W.label_size, W.label_font, C[W.color], W.alpha, W.label_halo, "c")

    def compress_on_screen(self, view: "View") -> list[Compress]:
        """화면에 걸친 압축 구간 — 정직성 검사가 '압축 메타 ↔ 표시'를 대조할 때 쓴다(render_base 가 그리는 조건과 같다)."""
        out = []
        for z in self.cfg.compress:
            xa, _ = view.to_screen(self.x_of(z.from_), 0.0)
            xb, _ = view.to_screen(self.x_of(z.to), 0.0)
            if not (xb < 0 or xa > W_OUT):
                out.append(z)
        return out

    # --- 라벨
    def draw_labels(self, ctx: cairo.Context, view: "View", reserved: list, alpha: float = 1.0) -> None:
        T = TIMELINE  # noqa: N806
        for i, ln in enumerate(self.lanes):
            top, _ = self.lane_screen(view, i)
            name = ln.label if not ln.unit else f"{ln.label} ({ln.unit})"   # engine.layers.series.lane_name 과 같은 문자열
            text(ctx, name, T.lane_label.x, top + T.lane_label.dy, T.lane_label.size, T.lane_label.font, C["white"], alpha,
                 T.lane_label.halo, "l")
        _, bot = self.lane_screen(view, self.n - 1)
        unit = self.tick_unit(view.w)
        G = T.grid  # noqa: N806
        last = -W_OUT
        for d, kind in self.ticks(view):
            x, _ = view.to_screen(self.x_of(d), 0.0)
            if x < G.label_margin_px or x > W_OUT - G.label_margin_px or x - last < G.min_label_gap_px:
                continue
            text(ctx, self.tick_label(d, unit), x, bot + G.label_dy, G.label_size, G.label_font,
                 C["white"] if kind == "year" else C["muted"], alpha, G.label_halo, "c")
            last = x


__all__ = ["Compress", "TimelineConfig", "TimelineError", "TimelineStage", "add_months", "as_date"]
