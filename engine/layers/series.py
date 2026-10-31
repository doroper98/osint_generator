"""시리즈 레이어 `series` — 데이터 레코드에서 직접 그린 계단선·꺾은선 (v4.3.0, docs/handoff/20 §5.1·§6, back_and_forth D-0084 작업 4·D-0086).

`{type: series, lane, series_id, style: step|line, grow, col}` — 값은 `data/series/<series_id>` 레코드에서만 온다(연출이 숫자를 주지 않는다).
- 세로: 레인 띠 안, 레인의 값 범위(`lane_range` — 그 레인 모든 series 의 [min(0, 최소), 최대]). 0 기준선과 범위 끝 값 라벨을 그린다.
- grow: 카메라와 함께 왼쪽→오른쪽으로 자란다(등장 문법 05). 앞끝 = (화면 왼쪽 + 화면 폭 × playhead)의 누적 최대 —
  되돌아가도 줄지 않는다. 등장 직후 grow_in_sec 동안 화면 왼쪽에서 앞끝까지 쓸어 나간다(`load_project` 가 프레임별로 미리 계산).
- 값 라벨은 드러난 마지막 점 하나(단위 포함). 레인 아래쪽에 출처·기준 시점 줄(20 §5.1 "YYYY년 M월 기준").
- 빈 달(레코드 missing, D-0086): 선을 끊고 그 자리에 "자료 없음" 표시. 보간 선분 없음.
- band(v4.4.0 D-0090 작업 2): 두 레코드(series_id = 아래 끝, upper_id = 위 끝) 사이를 계단 띠로 칠한다(목표 범위).
  값 라벨은 "아래–위단위", 두 레코드의 날짜는 같아야 한다(다르면 렌더 전 오류). 토큰 `rules stage_timeline.band`.
수치·색은 `rules stage_timeline.series`·`band`·`missing_mark`(코드 리터럴 0).
"""

from __future__ import annotations

import math
from datetime import date
from typing import TYPE_CHECKING

import cairo

from data.series import load_series
from engine.events import PART_STYLES
from engine.style import C, FPS, TIMELINE, island_rgb
from rules import load_rules
from engine.timebase import ease_out, window
from engine.typography import rrect, text, tw

if TYPE_CHECKING:
    from engine.context import RenderCtx
    from engine.projection import View
    from engine.stage_timeline import TimelineStage

MONTHS = 12
TAG = load_rules().panels.prov_tag   # 추정 태그 글자(size·font·alpha) 재사용 — D-0266 C
EPS = 1e-9          # v7.4.0 D-0263 — 눈금 반올림 부동소수 여유
ROUND_DP = 6        # 범위·눈금 값 소수 자릿수
DECADE = 10         # 눈금 간격 = 가수 × DECADE^k
NICE_TRIES = 4      # 가수 목록을 몇 자릿수 위까지 훑는가
DEC_LAST_DAY = 31   # 12월 마지막 날(전망 열 = 그 해 연말)
SOURCE_SEP = " · "  # 출처 줄 조각 구분(source_line·lane_source 가 쓰는 것과 같다)
TAG_PAD = 3         # 전망 띠 태그 줄 사이·레인 위 끝 여백(설계 px, D-0266 C)
SEP_RGB = (0.05, 0.06, 0.08)   # 쌓임 부문 틈·밝은 부문 위 글자(아일랜드 바탕에 가까운 어두운 잉크)
AXIS = "value"   # D-0087 — 값 축(정직성 검사 4개 전부, rules qa_checks.chart_targets)


def loss_rgb() -> tuple[float, float, float]:
    """손실 면(v7.4.0 D-0328 §1 — 테두리 없이 채도 낮춘 면) = down × neg_fill_mix + 바탕 × (1 − neg_fill_mix)."""
    from engine.style import bg_rgb  # noqa: PLC0415

    B = TIMELINE.bars  # noqa: N806
    g = bg_rgb(TIMELINE.bg_rgb)
    d, m = (C[B.loss_color], B.neg_fill_mix) if B.negative_fill == "muted_fill" else (bar_ink(), B.ladder[min(B.neg_ink_step, len(B.ladder) - 1)])   # ink_light = 사다리 neg_ink_step 단(D-0330)
    return tuple(a * m + b * (1 - m) for a, b in zip(d, g))  # type: ignore[return-value]


def bar_ink() -> tuple[float, float, float]:
    """막대·쌓임·인셋 잉크 — rules bars.ink 색(팔레트 text, 사다리는 그 위 알파 — D-0322 정정)."""
    return C[TIMELINE.bars.ink]


def record_ids(e: dict) -> list[str]:
    """이벤트가 읽는 레코드 id — band 면 아래 끝·위 끝 두 개(v4.4.0), stack 이면 합계 + 부문 레코드(v7.4.0 D-0309)."""
    return ([e["series_id"]] + ([e["upper_id"]] if e.get("upper_id") else []) + [i for p in e.get("parts") or [] for i in p["ids"]]
            + ([e["estimate_id"]] if e.get("estimate_id") else []))


def _raw(rec: object, d: date) -> float:
    """공시 원값(filing raw_value) — 없으면 레코드 값. 부문 합 검증은 반올림 전 값으로(D-0309)."""
    f = rec.filing(d) if getattr(rec, "source_kind", "") == "filing" else None  # type: ignore[attr-defined]
    return f.raw_value if f is not None else dict(rec.values)[d]  # type: ignore[attr-defined]


def stack_columns(e: dict) -> list[tuple[date, float, list[float]]]:
    """stack 의 열 (날짜, 합계 값, 부문 값들). 부문 값 = ids 레코드 값의 합(코드 계산). 부문 합 ≠ 합계(원값 기준, sum_tol_pct)면
    ValueError(P6) — 빈 부문 날짜도 오류(보간 금지)."""
    tot = load_series(e["series_id"])
    parts = [[load_series(i) for i in p["ids"]] for p in e["parts"]]
    out = []
    for d, v in tot.values:
        vals, raw = [], 0.0
        for recs in parts:
            have = [dict(r.values) for r in recs]
            if any(d not in h for h in have):
                raise ValueError(f"stack {e['series_id']}: 부문 {[r.series_id for r in recs]} 에 {d} 값이 없다")
            vals.append(sum(h[d] for h in have))
            raw += sum(_raw(r, d) for r in recs)
        t_raw = _raw(tot, d)
        if abs(raw - t_raw) > abs(t_raw) * TIMELINE.bars.sum_tol_pct / 100 + 1e-9:
            raise ValueError(f"stack {e['series_id']} {d}: 부문 합 {raw:g} ≠ 합계 {t_raw:g}(허용 {TIMELINE.bars.sum_tol_pct}%) — 부문을 빠짐없이(D-0309)")
        out.append((d, v, vals))
    return out


def stack_extent(e: dict) -> list[float]:
    """stack 이 차지하는 값(열마다 양수 합·음수 합·합계) — 레인 범위가 쌓임 전체를 품게."""
    return [x for _d, v, vals in stack_columns(e) for x in (sum(p for p in vals if p > 0), sum(p for p in vals if p < 0), v)]


def _quarter_back(d: date, n: int) -> date:
    """분기 마지막 날 d 에서 n 분기 앞의 분기 마지막 날."""
    q = d.year * 4 + (d.month - 1) // 3 - n
    y, m = q // 4, q % 4 * 3 + 3
    return date(y, m, 31 if m in (3, 12) else 30)


def pair_items(e: dict) -> tuple[date, date, list[tuple[str, float, float]]]:
    """dumbbell·diverging 의 (비교 기준 분기, 열 분기, [(부문 이름, 기준 값, 열 값)]) — v7.4.0 D-0315 §1-3.
    열 분기 = series_id 레코드의 마지막 분기, 기준 = dumbbell 전분기 · diverging 전년 동기. 부문 값 = ids 레코드 값의 합(코드 계산).
    빈 값 = ValueError(보간 금지, P6)."""
    d1 = load_series(e["series_id"]).values[-1][0]
    d0 = _quarter_back(d1, 1 if e["style"] == "dumbbell" else 4)   # diverging·slope = 전년 동기
    out = []
    for p in e["parts"]:
        have = [dict(load_series(i).values) for i in p["ids"]]
        miss = [d for d in (d0, d1) for h in have if d not in h]
        if miss:
            raise ValueError(f"{e['style']} 부문 {p['label']}: {p['ids']} 에 {sorted(set(miss))} 값이 없다")
        out.append((p["label"], sum(h[d0] for h in have), sum(h[d1] for h in have)))
    return d0, d1, out


def yoy_pct(v0: float, v1: float) -> float:
    """전년 동기 대비 %(코드 계산, rules data.transforms yoy_pct 와 같은 식 — 소수 첫째 자리 반올림은 표기에서)."""
    if v0 <= 0:
        raise ValueError(f"diverging: 기준 값 {v0} ≤ 0 — 증감률을 정의할 수 없다(손실 부문은 dumbbell 로)")
    return (v1 / v0 - 1) * 100


def pair_extent(e: dict) -> list[float]:
    """dumbbell·diverging 이 차지하는 값 — dumbbell 은 두 시점 값, diverging 은 ±% 와 0."""
    _d0, _d1, items = pair_items(e)
    if e["style"] == "dumbbell":
        return [x for _l, a, b in items for x in (a, b)]
    if e["style"] == "slope":   # D-0320 C2 — 값 그대로(구성비 아님 — 부문 매출에 내부 매출이 섞여 분모가 없다)
        return [x for _l, a, b in items for x in (a, b)]
    return [0.0] + [yoy_pct(a, b) for _l, a, b in items]



def band_pairs(e: dict) -> list[tuple[date, float, float]]:
    """band 의 (달, 아래, 위). 두 레코드의 날짜가 다르면 ValueError(보간 금지, D-0086), 위 < 아래 도 오류."""
    lo, hi = load_series(e["series_id"]), load_series(e["upper_id"])
    if [d for d, _ in lo.values] != [d for d, _ in hi.values]:
        raise ValueError(f"band {lo.series_id}·{hi.series_id}: 두 레코드의 날짜가 다르다 — 같은 달끼리만 띠를 칠한다")
    out = [(d, a, b) for (d, a), (_, b) in zip(lo.values, hi.values)]
    bad = [d for d, a, b in out if b < a]
    if bad:
        raise ValueError(f"band {lo.series_id}·{hi.series_id}: 위 끝 < 아래 끝 {bad[:3]}")
    return out


def regimes(values: list[tuple[date, float]], months: int) -> list[str]:
    """달마다 색 의미 키(v4.4.0 D-0091 ②) — 마지막 변화(앞 달과 다름)가 months 달 안이면 그 방향(hike 오름·cut 내림), 아니면 hold.
    첫 달·변화 기록 없음 = hold. 빈 달(끊김)은 앞뒤 값을 비교하지 않는다(보간 금지 — 끊긴 뒤 첫 달은 새로 시작)."""
    out: list[str] = []
    last: tuple[int, str] | None = None
    for i, (d, v) in enumerate(values):
        k = d.year * MONTHS + d.month
        if i:
            pd, pv = values[i - 1]
            if k - (pd.year * MONTHS + pd.month) == 1 and v != pv:
                last = (k, "hike" if v > pv else "cut")
        out.append(last[1] if last is not None and k - last[0] < months else "hold")
    return out


def month_colors(e: dict, R: object) -> dict[date, tuple[float, float, float]] | None:  # noqa: N803
    """color_by change 면 {달: RGB}(장르 프로필 color_semantics hike·cut·hold — 없으면 오류, P6). fixed 면 None."""
    if e.get("color_by", "fixed") != "change":
        return None
    from engine.primitives import semantic_rgba  # noqa: PLC0415
    from genres.load import load_genre  # noqa: PLC0415

    sem = load_genre(R.cache["genre"]["name"]).color_semantics  # type: ignore[attr-defined]
    missing = [k for k in ("hike", "cut", "hold") if k not in sem]
    if missing:
        raise ValueError(f"series color_by change: 장르 프로필 color_semantics 에 {missing} 가 없다")
    rgb = {k: semantic_rgba(sem[k])[:3] for k in ("hike", "cut", "hold")}
    vals = load_series(e["series_id"]).values
    return {d: rgb[r] for (d, _), r in zip(vals, regimes(vals, TIMELINE.series.change_regime_months))}


def lane_extent(events: list[dict], lane: str, stage: "TimelineStage | None" = None,
                secondary: bool = False) -> tuple[float, float, str | None]:
    """레인 데이터 극값(최소, 최대, 단위) — 무대 기간(stage cfg start~end) 안 그 레인 모든 레코드 값(실측 + 전망 점). 기간 밖뿐이면 레코드 전체.
    lane_range 와 [axis-empty-band] 가 같이 쓴다(v7.4.0 D-0277 §3)."""
    evs = [e for e in events if e["type"] == "series" and e["lane"] == lane and bool(e.get("secondary")) == secondary
           and not e.get("detail")]   # v7.4.0 D-0318 — 열 확대 인셋은 자기 척도(레인 범위에 넣지 않는다)   # v7.4.0 D-0309 — 보조 축은 따로
    recs = [load_series(sid) for e in evs if e.get("style") not in PART_STYLES for sid in record_ids(e)]
    lo_d = stage.cfg.start if stage is not None else None
    hi_d = stage.cfg.end if stage is not None else None
    vs = [v for r in recs for d, v in record_points(r) if (lo_d is None or d >= lo_d) and (hi_d is None or d <= hi_d)]
    vs += [x for e in evs if e.get("style") == "stack" for x in stack_extent(e)]
    recs += [load_series(e["series_id"]) for e in evs if e.get("style") == "stack"]
    pairs = [e for e in evs if e.get("style") in ("dumbbell", "diverging", "slope")]   # v7.4.0 D-0315 §1-3
    vs += [x for e in pairs for x in pair_extent(e)]
    recs += [load_series(e["series_id"]) for e in pairs]
    if not vs:   # 무대 기간 밖 레코드뿐 — 레코드 전체로(그려질 점은 없지만 범위는 정해야 한다)
        vs = [v for r in recs for _, v in record_points(r)]
    if any(e.get("style") == "diverging" for e in evs):   # 증감률 레인 — 단위 %(레코드 단위와 다르다, 같은 레인에 금액을 섞지 않는다)
        return min(vs), max(vs), "%"
    return min(vs), max(vs), (recs[0].unit if recs else None)


def lane_range(events: list[dict], lane: str, stage: "TimelineStage | None" = None, secondary: bool = False) -> tuple[float, float]:
    """레인 값 범위(v7.4.0 back_and_forth D-0263, UF-140) — rules stage_timeline.lane_range. fit: 데이터 극값(lane_extent, 폭 하한 min_span 적용)에
    [최소 − pad, 최대 + pad], 양 끝은 end_round 단위(눈금 간격 또는 그 절반, D-0277 §3 정정)로 내림·올림, 데이터가 모두 0 이상이면 아래 끝 ≥ 0.
    중간 눈금(axis_values)은 간격의 배수 그대로. zero: 옛 [min(0, 최소), 최대]. 영상당 한 번(prepare_series)."""
    cfg = TIMELINE.lane_range
    dmin, dmax, unit = lane_extent(events, lane, stage, secondary)
    if not secondary and zero_lane(events, lane):   # v7.4.0 D-0278 §4.1 — 막대·쌓임 레인은 0 을 품는다([bars-from-zero])
        dmin, dmax = min(dmin, 0.0), max(dmax, 0.0)
    if cfg.mode == "zero":
        lo, hi = min(0.0, dmin), dmax
        return (lo, hi) if hi > lo else (lo, lo + 1)
    a, b = fit_extent(dmin, dmax, unit)
    pad = (b - a) * cfg.pad_ratio
    lo, hi = a - pad, b + pad
    if dmin >= 0 and lo < 0:
        lo, hi = 0.0, hi - lo
    unit_r = nice_step(hi - lo) / (2 if cfg.end_round == "half_step" else 1)
    lo, hi = math.floor(lo / unit_r + EPS) * unit_r, math.ceil(hi / unit_r - EPS) * unit_r
    if dmin >= 0:
        lo = max(lo, 0.0)
    return round(lo, ROUND_DP), round(hi, ROUND_DP)


def zero_lane(events: list[dict], lane: str) -> bool:
    """막대·쌓임이 있는 레인(주 축) — 0 기준(D-0308·D-0309). [axis-empty-band]·[flat-lane] 은 이 레인을 재지 않는다(감독 승인 2026-10-30)."""
    return any(e["type"] == "series" and e["lane"] == lane and e.get("style") in ("bars", "stack", "range") and not e.get("secondary") for e in events)


def fit_extent(dmin: float, dmax: float, unit: str | None) -> tuple[float, float]:
    """데이터 극값에 폭 하한 min_span(단위별, 가운데 기준)을 적용한 구간. 데이터가 모두 0 이상이면 아래 끝 ≥ 0."""
    cfg = TIMELINE.lane_range
    span = max(dmax - dmin, cfg.min_span.get(unit, 0.0) if unit else 0.0)
    if span <= 0:
        span = abs(dmax) or 1.0
    mid = (dmin + dmax) / 2
    a, b = min(dmin, mid - span / 2), max(dmax, mid + span / 2)
    if dmin >= 0 and a < 0:
        a, b = 0.0, b - a
    return a, b


def empty_bands(events: list[dict], lane: str, rng: tuple[float, float], stage: "TimelineStage | None" = None) -> tuple[float, float]:
    """축 범위 중 데이터 극값(폭 하한 적용) 밖 빈 띠 비율(아래, 위) — [axis-empty-band](v7.4.0 D-0277 §3)."""
    dmin, dmax, unit = lane_extent(events, lane, stage)
    dmin, dmax = fit_extent(dmin, dmax, unit)   # 폭 하한으로 넓힌 여백은 빈 띠가 아니다(납작한 선을 절벽처럼 늘리지 않는 장치, D-0263)
    lo, hi = rng
    h = (hi - lo) or 1.0
    return max(0.0, dmin - lo) / h, max(0.0, hi - dmax) / h


def column_date(label: str, cols: list) -> date:  # noqa: ANN001 — ScatterColumn
    """전망 열의 날짜(v7.4.0 D-0260 §2) — 연도 열 = 그 해 12월 31일(rules projection.column_date year_end), 장기 = 마지막 연도 열 + longer_run_gap_days."""
    from datetime import timedelta  # noqa: PLC0415

    if label.isdigit():
        return date(int(label), MONTHS, DEC_LAST_DAY)
    last = max(int(c.label) for c in cols if c.label.isdigit())
    return date(last, MONTHS, DEC_LAST_DAY) + timedelta(days=TIMELINE.projection.longer_run_gap_days)


def record_points(rec: object) -> list[tuple[date, float]]:
    """레코드의 (날짜, 값) — series 는 values, scatter 는 열마다 참가자 값(열 날짜). 레인 범위가 전망 점까지 본다(D-0263 §2①)."""
    if getattr(rec, "kind", "series") == "scatter":
        cols = rec.columns  # type: ignore[attr-defined]
        return [(column_date(c.label, cols), v) for c in cols for v in c.values]
    return list(rec.values)  # type: ignore[attr-defined]


def nice_step(span: float) -> float:
    """눈금 간격 — nice_mantissas × 10^k 중 (span ÷ 간격) ≤ ticks_max + 1 인 가장 작은 값(v7.4.0 D-0263)."""
    cfg = TIMELINE.lane_range
    k = math.floor(math.log10(span / (cfg.ticks_max + 1))) - 1
    for _ in range(NICE_TRIES):
        for m in sorted(cfg.nice_mantissas):
            st = m * DECADE ** k
            if span / st <= cfg.ticks_max + 1 + EPS:
                return st
        k += 1
    return span


def axis_values(rng: tuple[float, float]) -> list[float]:
    """축 값 — 위·아래 끝 + 그 사이 눈금(최대 ticks_max). 그리기와 검사([chart-edge-bleed])가 같이 쓴다."""
    lo, hi = rng
    if TIMELINE.lane_range.mode == "zero":
        return [lo, hi]
    st = nice_step(hi - lo)
    k0 = math.floor(lo / st + EPS) + 1   # 중간 눈금 = 간격의 배수(끝 값이 반 눈금이어도, D-0277 §3 정정)
    mids = [round(k * st, ROUND_DP) for k in range(k0, math.ceil(hi / st - EPS))][:TIMELINE.lane_range.ticks_max]
    return [lo, *mids, hi]


def axis_range_note(rng: tuple[float, float], unit: str) -> str | None:
    """0 이 아닌 곳에서 시작하는 레인의 출처 줄 표기(v7.4.0 D-0263 §2②) — 0 을 품으면(0 에서 시작·0 을 가로지름) None.
    v7.4.0 D-0328 — 0 기준선이 화면에 있는 레인(음수 막대 등)은 잘린 축이 아니다."""
    if rng[0] <= 0 <= rng[1]:
        return None
    return TIMELINE.lane_range.axis_range_note.replace("{lo}", fmt_value(rng[0], "")).replace("{hi}", fmt_value(rng[1], unit))


def value_y(stage: "TimelineStage", lane: str, rng: tuple[float, float], v: float) -> float:
    lo_y, hi_y = stage.lane_y(lane)
    S = TIMELINE.series  # noqa: N806
    bars = stage.lanes[stage.lane_index(lane)].kind == "bars"   # v7.4.0 감독 지시(R-0293 눈 확인) — 막대·쌓임 레인은 플롯이 레인을 더 쓴다
    pb, pt = (TIMELINE.bars.lane_pad_bottom, TIMELINE.bars.lane_pad_top) if bars else (S.lane_pad_bottom, S.lane_pad_top)
    b, t = lo_y + pb, hi_y - pt
    return b + (v - rng[0]) / (rng[1] - rng[0]) * (t - b)


def segments(values: list[tuple[date, float]], missing: list[date] | None = None) -> list[list[tuple[date, float]]]:
    """빈 날에서 끊은 연속 구간들 — 보간하지 않는다(D-0086). missing 이 None 이면 월별 규칙(한 달보다 긴 간격 = 빈 달),
    주면 레코드 missing 날짜를 사이에 둔 곳에서만 끊는다(v7.4.0 — daily 는 휴장일이 빈 날이 아니고, quarterly 는 분기 간격이 정상)."""
    out: list[list[tuple[date, float]]] = [[values[0]]]
    for a, b in zip(values, values[1:]):
        gap = (any(a[0] < m < b[0] for m in missing) if missing is not None
               else (b[0].year * MONTHS + b[0].month) - (a[0].year * MONTHS + a[0].month) != 1)
        if gap:
            out.append([])
        out[-1].append(b)
    return out


def fmt_value(v: float, unit: str) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".") + unit


def source_ids(e: dict) -> list[str]:
    """출처 줄에 쓰는 레코드 — stack 은 합계 레코드 하나(부문은 같은 공시 표, D-0309), 그 밖은 record_ids."""
    return [e["series_id"]] if e.get("style") in PART_STYLES else record_ids(e)


def source_line(e: dict) -> str:
    recs = [load_series(s) for s in source_ids(e)]
    srcs = list(dict.fromkeys(f"{r.source} · {r.as_of_label()}" for r in recs))
    return " / ".join(srcs)


def lane_source_join(evs: list[dict]) -> str:
    """레인 출처 한 줄(v7.4.0 back_and_forth D-0266 B) — 같은 매체(출처 첫 조각)는 한 번, 원출처는 겹치는 앞부분을 묶어 "·" 로,
    기준 시점은 같은 해면 달을 "·" 로 잇는다. 전망 점(style projection)의 출처는 레인 줄이 아니라 전망 띠 태그로 간다(D-0266 C)."""
    recs = [load_series(sid) for e in evs if e.get("style") != "projection" for sid in source_ids(e)]
    groups: dict[str, dict[str, list]] = {}
    for r in recs:
        head, *rest = r.source.split(SOURCE_SEP)
        g = groups.setdefault(head, {"orig": [], "asof": []})
        for piece in rest:
            if piece not in g["orig"]:
                g["orig"].append(piece)
        if r.as_of not in g["asof"]:
            g["asof"].append(r.as_of)
    out = []
    for head, g in groups.items():
        orig: list[str] = []
        for piece in sorted(g["orig"], key=len):
            base = next((o for o in orig if piece.startswith(o)), None)
            if base is None:
                orig.append(piece)
            else:
                orig[orig.index(base)] = base + "·" + piece[len(base):].strip()
        out.append(SOURCE_SEP.join([head, *orig, _asof_join(sorted(g["asof"]))]))
    out += [n for n in dict.fromkeys(daily_missing_note(r) for r in recs) if n]
    return SOURCE_SEP.join(out)


def daily_missing_note(rec: object) -> str | None:
    """일별 계열 missing 출처 줄 문구(v7.4.0 D-0319 ③) — 날 수와 사유(모두 급변일이면 daily_note_outlier). 월별·분기·빈 것 = None."""
    if rec.frequency != "daily" or not rec.missing:  # type: ignore[attr-defined]
        return None
    M = TIMELINE.missing_mark  # noqa: N806
    allo = all(m.note.startswith("급변일") for m in rec.missing)  # type: ignore[attr-defined]
    return (M.daily_note_outlier if allo else M.daily_note).replace("{n}", str(len(rec.missing)))  # type: ignore[attr-defined]


def lane_source_short(evs: list[dict]) -> str:
    """무대 표면 출처 한 줄(v7.4.0 D-0328 §1) — 레코드 출처의 머리(첫 " · " 앞, 같은 머리는 한 번) + 가장 늦은 기준 시점.
    세부(공시 표·변환·빈 날)는 엔딩 카드 자료 절(auto: series)이 말한다."""
    recs = [load_series(sid) for e in evs if e.get("style") != "projection" for sid in source_ids(e)]
    heads = list(dict.fromkeys(r.source.split(SOURCE_SEP)[0] for r in recs))
    last = max(recs, key=lambda r: r.as_of)
    return SOURCE_SEP.join([*heads, last.as_of_label()])


def _asof_join(asofs: list[str]) -> str:
    """["2026-08", "2026-09"] → "2026년 8·9월 기준"(같은 해), 해가 다르면 각자 "YYYY년 M월"."""
    pairs = [tuple(int(x) for x in a.split("-")) for a in asofs]
    if len({y for y, _ in pairs}) == 1:
        return f"{pairs[0][0]}년 " + "·".join(str(m) for _, m in pairs) + "월 기준"
    return "·".join(f"{y}년 {m}월" for y, m in pairs) + " 기준"


def lane_source_text(e: dict) -> str:
    """레인 출처 줄(v7.4.0 D-0256) — 같은 레인 series 전부의 출처를 한 줄로(load_project 가 lane_source 를 붙인다). 없으면 이 이벤트 것."""
    return e.get("lane_source") or source_line(e)


def end_label_plate_rect(box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """끝값 라벨 판 사각형 — 글자 상자(x0, top, x1, 기준선) + rules series.end_label_plate.pad_px. 아래 끝은 글자 내림(value_size × end_label_plate.descent)까지."""
    pd = TIMELINE.series.end_label_plate.pad_px
    x0, y0, x1, y1 = box
    return x0 - pd, y0 - pd, x1 + pd, y1 + TIMELINE.series.value_size * TIMELINE.series.end_label_plate.descent + pd


def draw_end_label_plate(ctx: cairo.Context, box: tuple[float, float, float, float], a: float) -> tuple[float, float, float, float]:
    """끝값 라벨 뒤 판(v7.4.0 D-0277 §2) — 바탕 = stage_timeline.bg_rgb × end_label_plate.alpha. 그린 사각형을 돌려준다(검사 기록)."""
    r = end_label_plate_rect(box)
    ctx.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
    ctx.set_source_rgba(*island_rgb(TIMELINE.bg_rgb), TIMELINE.series.end_label_plate.alpha * a)
    ctx.fill()
    return r


def pin_ring_boxes(R: "RenderCtx", view: "View", t: float, lane: str) -> list[tuple[float, float, float, float]]:
    """그 순간 같은 레인 값 핀의 맥동 고리 상자(화면) — load_project 가 남긴 R.cache["value_pins"](레인, 월드 x·y, t0, t1, 핀 라벨 단).
    핀 라벨 쪽(위·아래)은 리더선·라벨 자리라 고리 상자를 그쪽으로 끝까지 늘린다."""
    from engine.pin_labels import RING_PX  # noqa: PLC0415

    out = []
    for ln, wx, wy, t0, t1, *row in R.cache.get("value_pins") or ():
        if ln == lane and t0 <= t <= t1:
            x, y = view.to_screen(wx, wy)
            r = row[0] if row else None
            # 핀 라벨이 선 위(row > 0)면 고리 위쪽, 아래(row < 0)면 아래쪽 세로 띠(리더선·라벨 자리)도 막는다(152초 사례)
            y0 = y - RING_PX - (view.vh if r is not None and r > 0 else 0)
            y1 = y + RING_PX + (view.vh if r is not None and r < 0 else 0)
            out.append((x - RING_PX, y0, x + RING_PX, y1))
    return out


def clear_pin_rings(R: "RenderCtx", view: "View", t: float, lane: str, box: tuple[float, float, float, float], sx: float, sy: float,  # noqa: N803
                    lw: float) -> tuple[tuple[float, float, float, float], bool]:
    """끝값 라벨 판이 핀 맥동 고리와 겹치면 고리 위 → 고리 왼쪽 → 고리 아래 순으로 옮긴다(v7.4.0 D-0283 §2 — 핀 라벨 두 단과 같은 우선순위).
    (상자, 끝내 겹침) — 끝내 겹치면 기록해 검사가 hard 로 잡는다([island-pin-collision])."""
    rings = pin_ring_boxes(R, view, t, lane)
    hit = [r for r in rings if _hits(end_label_plate_rect(box), r)]
    if not hit:
        return box, False
    P = TIMELINE.series.end_label_plate  # noqa: N806
    h = box[3] - box[1]
    desc = TIMELINE.series.value_size * P.descent
    top, bot, lft = min(r[1] for r in hit), max(r[3] for r in hit), min(r[0] for r in hit)
    oy = getattr(view, "oy", 0.0)
    vx0, vy0, vx1, vy1 = getattr(view, "ox", 0.0), oy, getattr(view, "right", float("inf")), oy + getattr(view, "vh", float("inf"))
    for x0, by in ((box[0], top - P.pad_px - desc), (lft - P.pad_px - lw, box[3]), (box[0], bot + P.pad_px + h)):
        cand = (x0, by - h, x0 + lw, by)
        pr = end_label_plate_rect(cand)
        inside = vx0 <= pr[0] and pr[2] <= vx1 and vy0 <= pr[1] and pr[3] <= vy1   # 화면(뷰) 밖 자리는 쓰지 않는다
        if inside and not any(_hits(pr, r) for r in rings):
            return cand, False
    return box, True


def place_end_label(R: "RenderCtx", t: float, lane: str, y: float, v: float) -> float:  # noqa: N803
    """같은 프레임·같은 레인 끝값 라벨 기준선 세로 분산(v7.4.0 D-0256) — 이미 놓인 라벨과 rules series.end_label_min_gap_px 안이면
    값이 작으면 아래로, 크면 위로 민다. 놓인 자리는 R.cache["series_end_labels"] 에(검사 [series-label-overlap] 가 읽는다)."""
    gap = TIMELINE.series.end_label_min_gap_px
    reg = R.cache.get("series_end_labels")
    if reg is None or reg.get("t") != t:
        reg = R.cache["series_end_labels"] = {"t": t, "lanes": {}}
    placed = reg["lanes"].setdefault(lane, [])
    for _ in range(len(placed) + 1):
        hit = next(((py, pv) for py, pv, *_ in placed if abs(y - py) < gap), None)   # 놓인 항목 = (y, 값, 상자, 판, 가림) — 앞 둘만 본다
        if hit is None:
            break
        y = hit[0] + gap if v < hit[1] else hit[0] - gap
    return y


def value_text(e: dict, v: float, unit: str, hi: float | None = None) -> str:
    """끝점 값 라벨 — band 는 "아래–위단위"(rules stage_timeline.band.sep)."""
    if hi is None:
        return fmt_value(v, unit)
    return fmt_value(v, "") + TIMELINE.band.sep + fmt_value(hi, unit)


def draw_series(ctx: cairo.Context, R: "RenderCtx", view: "View", t: float, e: dict) -> None:  # noqa: N803
    S = TIMELINE.series  # noqa: N806
    if e.get("detail"):   # v7.4.0 D-0318 — 열 확대 인셋(island column_detail) — 등장·퇴장은 자기 규칙(island.column_detail.fade)
        _draw_column_detail(ctx, view, view.stage, t, e, R.cache["series_range"][e["lane"]], 1.0)  # type: ignore[arg-type]
        return
    a = window(t, e["t0"], e["t1"], S.fade_sec, S.fade_sec)
    if a <= S.min_alpha:
        return
    stage: "TimelineStage" = view.stage  # type: ignore[assignment]
    rec = load_series(e["series_id"])
    sec = bool(e.get("secondary"))   # v7.4.0 D-0309 §1-4 — 보조 축: 자기 범위·가는 선·일별 점·왼쪽 축
    rng = (R.cache["series_range2"] if sec else R.cache["series_range"])[e["lane"]]
    if e["style"] == "projection":   # v7.4.0 D-0260 §2 — 전망 점(같은 레인·같은 축척)
        _draw_projection(ctx, R, view, stage, t, e, rec, rng, a)
        _draw_axis(ctx, view, stage, e, rng, rec.unit, a, R, t)
        _draw_source(ctx, view, stage, e, a)
        return
    front = math.inf
    if e["grow"]:
        fr = R.cache["series_front"][e["key"]]   # 프레임별 앞끝(월드 x) — load_project 가 카메라 경로로 미리 계산
        front = float(fr[min(len(fr) - 1, max(0, int(t * FPS)))])
    col = C[e["col"]]
    mcol = month_colors(e, R)   # v4.4.0 D-0091 ② — None 이면 한 색(기존 그대로)
    pr = plot_right(ctx, view, stage, e["lane"], rng, rec.unit)   # v7.4.0 — 오른쪽 축 값 라벨 열은 선·띠·점이 들어가지 않는 예약 열
    fx = min(pr, view.to_screen(front, 0.0)[0] if front != math.inf else view.right)
    shown = min(front, view.x0 + (pr - view.ox) / view.s)   # 끝값은 선이 실제로 끝나는 자리(예약 열 왼쪽) 기준 — 열 안 자료는 그리지 않는다
    pl = plot_left(ctx, view, e["lane"], R)   # v7.4.0 D-0314 §1-2 — 보조 축 값은 왼쪽 예약 열(자료가 들어가지 않는다)
    ctx.save()
    ctx.rectangle(pl, view.oy, max(0.0, fx - pl), stage.area_bottom + TIMELINE.series.clip_below_px)
    ctx.clip()
    last: tuple[float, float, float] | None = None
    last_hi: float | None = None
    if e["style"] == "band":
        last, last_hi = _draw_band(ctx, view, stage, e, rng, col, a, shown, mcol)
    if e["style"] == "bars":   # v7.4.0 D-0278 §4.1·D-0308 — 캡슐·사다리·직접 라벨(끝값 라벨 없음)
        _draw_bars(ctx, view, stage, e, rng, rec, col, a, shown)
    if e["style"] in (*PART_STYLES, "range"):   # v7.4.0 D-0309 쌓임 · D-0315 §1-3 덤벨·diverging·가이던스 범위 — 직접 라벨(범례 없음)
        ctx.restore()
        ctx.save()
        ctx.rectangle(pl, view.oy - view.vh, max(0.0, pr - pl), view.vh * 3)   # 좌우 예약 열만 막는다(값 라벨은 위·아래로 나갈 수 있다)
        ctx.clip()
        if e["style"] == "stack":
            _draw_stack(ctx, view, stage, e, rng, col, a, shown, pr)
        elif e["style"] == "range":
            _draw_range(ctx, view, stage, e, rng, a, shown, t)
        else:
            _draw_pairs(ctx, view, stage, e, rng, col, a, shown)
        ctx.restore()
        _draw_axis(ctx, view, stage, e, rng, "", a, R, t)   # D-0308 감독 지시 ③ — 막대·쌓임 축은 숫자만(단위는 레인 이름)
        _draw_source(ctx, view, stage, e, a)
        return
    gaps = None if rec.frequency == "monthly" else rec.missing_dates()   # v7.4.0 — daily·quarterly 는 missing 에서만 끊는다
    for seg in ([] if e["style"] in ("band", "bars") or mcol is None else segments(rec.values, gaps)):   # 달마다 색(change)
        _draw_pieces(ctx, view, stage, e, rng, seg, mcol, a)
        for d, v in seg:
            x = stage.x_of(d)
            if x <= shown:
                last = (x, value_y(stage, e["lane"], rng, v), v)
    for seg in ([] if e["style"] in ("band", "bars") or mcol is not None else segments(rec.values, gaps)):
        pts = [(stage.x_of(d), value_y(stage, e["lane"], rng, v), v) for d, v in seg]
        if e["style"] == "step":   # 값은 그 달 첫날부터 다음 달 첫날까지 유지(월평균)
            nxt = stage.x_of(_next_month(seg[-1][0]))
            st: list[tuple[float, float, float]] = []
            for i, p in enumerate(pts):
                if i:
                    st.append((p[0], pts[i - 1][1], pts[i - 1][2]))
                st.append(p)
            pts = st + [(nxt, pts[-1][1], pts[-1][2])]
        ctx.new_path()
        for i, (x, y, _) in enumerate(pts):
            sx, sy = view.to_screen(x, y)
            (ctx.move_to if i == 0 else ctx.line_to)(sx, sy)
        ctx.set_source_rgba(*col, (TIMELINE.secondary.alpha if sec else 1.0) * a)
        ctx.set_line_width(TIMELINE.secondary.line_w if sec else S.line_w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
        for x, y, v in pts:
            if x <= shown:
                last = (x, y, v)
                if sec and TIMELINE.secondary.dot_r > 0:   # D-0308 §3 act4 — 일별 점 선
                    sx, sy = view.to_screen(x, y)
                    ctx.arc(sx, sy, TIMELINE.secondary.dot_r, 0, 2 * math.pi)
                    ctx.set_source_rgba(*col, TIMELINE.secondary.alpha * a)
                    ctx.fill()
    ctx.restore()
    _draw_missing(ctx, view, stage, rec, e, front, a, pr)
    if last is not None and not sec and not (e["style"] == "band" and e.get("lane_n", 1) > 1):   # 보조 계열은 끝값 판을 접는다(D-0314 §1-2 안 B — 값은 왼쪽 축·핀)   # v7.4.0 D-0256 — 다른 계열과 한 레인이면 띠는 끝값 라벨 없음(상·하한은 띠가 보여 준다)
        sx, sy = view.to_screen(last[0], last[1])
        if view.ox + S.value_min_x <= sx <= pr:
            tip = col if mcol is None else mcol[_month_of(stage, last[0], rec)]
            ctx.arc(sx, sy, S.tip_r, 0, 2 * math.pi)
            ctx.set_source_rgba(*tip, a)
            ctx.fill()
            s = value_text(e, last[2], rec.unit, last_hi)
            lw = tw(ctx, s, S.value_size, S.value_font)
            x0 = sx + S.value_dx if sx + S.value_dx + lw <= view.right - S.axis_zone_px else sx - S.value_dx - lw   # 오른쪽 축 값 자리를 비킨다
            by = place_end_label(R, t, e["lane"], sy + S.value_dy, last[2])
            by = clear_axis_labels(ctx, view, stage, e["lane"], rng, rec.unit, x0, lw, by)   # v7.4.0 — 축 눈금 라벨을 세로로 비킨다
            box = (x0, by - S.value_size, x0 + lw, by)
            box, covered = clear_pin_rings(R, view, t, e["lane"], box, sx, sy, lw)   # v7.4.0 D-0283 §2 — 판이 핀 맥동 고리를 덮지 않게(위 → 왼쪽)
            by = box[3]
            if not _hits(box, _lane_name_box(ctx, view, stage, e["lane"])):   # 레인 이름을 덮지 않는다(끝점은 그대로)
                plate = draw_end_label_plate(ctx, box, a)   # v7.4.0 D-0277 §2 — 강조 띠 위 대비
                text(ctx, s, box[0], by, S.value_size, S.value_font, tip, a, S.value_halo, "l")
                R.cache["series_end_labels"]["lanes"][e["lane"]].append((by, last[2], box, plate, covered))
    if sec:
        from engine.style import stage_surface  # noqa: PLC0415

        if stage_surface():   # v7.4.0 D-0328 §3 — 보조 축 숫자 금지(축 둘이 나란한 화면 금지), 끝값 핀만
            d0, v0 = next(((d, v) for d, v in rec.values if stage.cfg.start <= d), rec.values[0])   # D-0328 (c) — 내레이션이 말하는 시작값(무대 안 첫 값)
            first = (stage.x_of(d0), value_y(stage, e["lane"], rng, v0), v0) if stage.x_of(d0) <= shown else None
            _draw_end_pin(ctx, view, first, rec.unit, col, a, pr)
            _draw_end_pin(ctx, view, last, rec.unit, col, a, pr)
        else:
            _draw_secondary_axis(ctx, view, stage, e, rng, col, a)
    else:
        _draw_axis(ctx, view, stage, e, rng, "" if e["style"] == "bars" else rec.unit, a, R, t)
    _draw_source(ctx, view, stage, e, a)


def _draw_end_pin(ctx: cairo.Context, view: "View", last: "tuple[float, float, float] | None", unit: str,
                  col: tuple[float, float, float], a: float, right: float) -> None:
    """보조 계열 끝값 핀(v7.4.0 D-0328 §3) — 마지막으로 그린 점에 점 하나 + "92.07달러"(레코드 값 그대로·레코드 단위). 오른쪽 자리가
    없으면(예약 열에 닿으면) 점 왼쪽에. 축 숫자를 대신한다."""
    if last is None:
        return
    from engine.style import ISLAND, bg_rgb  # noqa: PLC0415

    SS = ISLAND.stage_surface  # noqa: N806
    sx, sy = view.to_screen(last[0], last[1])
    ctx.arc(sx, sy, SS.end_pin_r, 0, 2 * math.pi)
    ctx.set_source_rgba(*C["white"], a)
    ctx.fill()
    s = fmt_value(last[2], unit)
    lw = tw(ctx, s, SS.end_pin_size, SS.end_pin_font)
    x = sx + SS.end_pin_dx if sx + SS.end_pin_dx + lw <= right else sx - SS.end_pin_dx - lw
    by = sy - SS.end_pin_dx
    pad = SS.plate_pad   # D-0328 감독 지시 (a) — 글자 뒤 선(0 기준선·격자·계열)을 끊는다: 바탕색 판(UF-155 선·글씨 겹침 0)
    ctx.rectangle(x - pad, by - SS.end_pin_size * 0.85 - pad, lw + 2 * pad, SS.end_pin_size * 1.1 + 2 * pad)
    ctx.set_source_rgba(*bg_rgb(TIMELINE.bg_rgb), a)
    ctx.fill()
    text(ctx, s, x, by, SS.end_pin_size, SS.end_pin_font, C["white"], a, 0, "l")


def _draw_secondary_axis(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float],
                         col: tuple[float, float, float], a: float) -> None:
    """보조 축 값(v7.4.0 D-0309 §1-4) — 레인 왼쪽 끝, 계열 색, 숫자만(단위는 레인 이름). 눈금선은 그리지 않는다(주 축 격자만)."""
    S = TIMELINE.series  # noqa: N806
    name_box = _lane_name_box(ctx, view, stage, e["lane"])
    rx = secondary_col_right(ctx, view, rng) - TIMELINE.secondary.axis_label_margin_px   # 왼쪽 예약 열 안 오른쪽 정렬(D-0314 §1-2)
    for v in axis_values(rng):
        _, sy = view.to_screen(0.0, value_y(stage, e["lane"], rng, v))
        lw = tw(ctx, fmt_value(v, ""), S.axis_label_size, S.axis_label_font)
        lb = (rx - lw, sy + S.axis_label_dy - S.axis_label_size, rx, sy + S.axis_label_dy)
        if _hits(lb, name_box):   # 레인 이름과 겹치는 눈금 라벨은 접는다(R-0294 §2 — "140" 겹침)
            continue
        text(ctx, fmt_value(v, ""), rx, sy + S.axis_label_dy, S.axis_label_size,
             S.axis_label_font, col, a, S.axis_label_halo, "r")


def secondary_col_right(ctx: cairo.Context, view: "View", rng: tuple[float, float]) -> float:
    """보조 축 왼쪽 예약 열의 오른쪽 끝(화면 x) — 가장 긴 눈금 라벨 + 양옆 axis_label_margin_px(D-0314 §1-2, plot_right 의 거울)."""
    S = TIMELINE.series  # noqa: N806
    w = max((tw(ctx, fmt_value(v, ""), S.axis_label_size, S.axis_label_font) for v in axis_values(rng)), default=0.0)
    return view.ox + w + 2 * TIMELINE.secondary.axis_label_margin_px


def plot_left(ctx: cairo.Context, view: "View", lane: str, R: "RenderCtx") -> float:  # noqa: N803
    """자료를 그리는 영역의 왼쪽 끝 — 레인에 보조 축 계열이 있으면 그 축 값 열 오른쪽, 없으면 뷰 왼쪽 끝."""
    from engine.style import stage_surface  # noqa: PLC0415

    rng2 = (R.cache.get("series_range2") or {}).get(lane)
    return view.ox if rng2 is None or stage_surface() else secondary_col_right(ctx, view, rng2)   # D-0328 — 무대 표면은 보조 축 숫자 없음(열 예약 없음)


def projection_rgb(R: "RenderCtx") -> tuple[float, float, float]:  # noqa: N803
    """전망 색 = 장르 color_semantics.forecast(D-0264). 없으면 오류(P6 — 다른 색으로 대신하지 않는다)."""
    from engine.primitives import semantic_rgba  # noqa: PLC0415
    from genres.load import load_genre  # noqa: PLC0415

    sem = load_genre(R.cache["genre"]["name"]).color_semantics  # type: ignore[attr-defined]
    if "forecast" not in sem:
        raise ValueError("series projection: 장르 프로필 color_semantics 에 forecast 가 없다(D-0260 §2)")
    return semantic_rgba(sem["forecast"])[:3]


def projection_dots(stage: "TimelineStage", e: dict, rec: object, rng: tuple[float, float]) -> list[tuple[int, str, float, list[tuple[float, float]], float]]:
    """열마다 (순번, 열 이름, 열 x(월드), 점 [(월드 x 오프셋 px, 월드 y)], 중앙값 월드 y). 같은 값 점은 가로로 나란히(primitive.dot_plot 배치와 같은 규칙)."""
    D = _dot_rules()  # noqa: N806
    step = D.dot_r * 2 + D.dot_gap
    out = []
    cols = rec.columns  # type: ignore[attr-defined]
    for i, c in enumerate(cols):
        x = stage.x_of(column_date(c.label, cols))
        groups: dict[float, int] = {}
        for v in c.values:
            groups[v] = groups.get(v, 0) + 1
        pts = [((j * 2 - (k - 1)) * step / 2, value_y(stage, e["lane"], rng, v)) for v, k in groups.items() for j in range(k)]
        out.append((i, c.label, x, pts, value_y(stage, e["lane"], rng, c.median())))
    return out


def _dot_rules() -> object:
    """점 크기·간격·중앙값 선·열 이름 크기 = rules primitives.dot_plot(D-0264 — 키 신설 없이 재사용)."""
    from engine.style import PRIMITIVES  # noqa: PLC0415

    return PRIMITIVES["dot_plot"]


def _draw_projection(ctx: cairo.Context, R: "RenderCtx", view: "View", stage: "TimelineStage", t: float, e: dict,  # noqa: N803
                     rec: object, rng: tuple[float, float], a: float) -> None:
    """전망 점(v7.4.0 back_and_forth D-0260 §2) — scatter 레코드 열마다 그 해 연말 x 에 참가자별 점, 중앙값 짧은 선, 열 이름(장기),
    레코드 as_of 다음 달 1일부터 무대 끝까지 전망 음영 띠. 열마다 column_stagger_sec 간격으로 자란다(한꺼번에 금지)."""
    from engine.primitives.dot_plot import col_label  # noqa: PLC0415

    P, D = TIMELINE.projection, _dot_rules()  # noqa: N806
    rgb = projection_rgb(R)
    top, bot = stage.lane_screen(view, stage.lane_index(e["lane"]))
    asof = rec.as_of  # type: ignore[attr-defined]
    d0 = date.fromisoformat(f"{asof}-01")   # as_of "YYYY-MM" → 다음 달 1일
    band_start = date(d0.year + d0.month // MONTHS, d0.month % MONTHS + 1, 1)
    bx0, _ = view.to_screen(stage.x_of(band_start), 0.0)
    bx1, _ = view.to_screen(stage.bounds[2], 0.0)
    pr = plot_right(ctx, view, stage, e["lane"], rng, rec.unit)   # 축 값 라벨 예약 열 — 띠·점·열 이름이 들어가지 않는다
    ctx.save()
    if getattr(stage, "frame", None) is not None:
        ctx.rectangle(*stage.frame)
        ctx.clip()
    ctx.rectangle(view.ox, view.oy, max(0.0, pr - view.ox), stage.area_bottom + TIMELINE.series.clip_below_px)
    ctx.clip()
    ctx.rectangle(max(view.ox, bx0), top, max(0.0, min(pr, bx1) - max(view.ox, bx0)), bot - top)
    ctx.set_source_rgba(*rgb, P.band_alpha * a)
    ctx.fill()
    for i, label, x, pts, my in projection_dots(stage, e, rec, rng):
        ca = a * window(t, e["t0"] + i * P.column_stagger_sec, e["t1"], TIMELINE.series.fade_sec, TIMELINE.series.fade_sec)
        if ca <= TIMELINE.series.min_alpha:
            continue
        sx, _ = view.to_screen(x, 0.0)
        for dx, wy in pts:
            _, sy = view.to_screen(x, wy)
            ctx.arc(sx + dx, sy, D.dot_r, 0, 2 * math.pi)
            ctx.set_source_rgba(*rgb, D.dot_alpha * ca)
            ctx.fill()
        half = max(D.median_half, max((abs(dx) for dx, _ in pts), default=0.0) + D.dot_r)
        _, msy = view.to_screen(x, my)
        ctx.move_to(sx - half, msy)
        ctx.line_to(sx + half, msy)
        ctx.set_source_rgba(*rgb, P.median_alpha * ca)
        ctx.set_line_width(D.median_w)
        ctx.stroke()
        low = max(view.to_screen(x, wy)[1] for _, wy in pts)
        text(ctx, col_label(label), sx, low + P.label_dy, D.col_size, "sansm", rgb, ca, TIMELINE.series.value_halo, "c")
    for line, y in projection_tag_lines(view, stage, e, rec):   # D-0266 C — 전망 출처·고정 문구는 전망 띠 안 태그(레인 출처 줄 대신)
        text(ctx, line, view.right - TIMELINE.series.axis_zone_px, y, TAG.size, TAG.font, rgb, a * TAG.alpha, TIMELINE.series.value_halo, "r")
    ctx.restore()


def projection_tag_lines(view: "View", stage: "TimelineStage", e: dict, rec: object) -> list[tuple[str, float]]:
    """전망 띠 태그 두 줄(v7.4.0 back_and_forth D-0266 C) — (글자, 기준선 y). 레인 위쪽 오른쪽(축 값 자리 왼쪽), 오른쪽 정렬.
    1줄 = 레코드 출처·기준 시점, 2줄 = 고정 문구(primitives.dot_plot.note, 20 §5.2). 글자 = rules panels.prov_tag(추정 태그 글자 재사용)."""
    top, _ = stage.lane_screen(view, stage.lane_index(e["lane"]))
    first = SOURCE_SEP.join([rec.source, rec.as_of_label()])  # type: ignore[attr-defined]
    return [(first, top + TAG.size + TAG_PAD), (_dot_rules().note, top + 2 * TAG.size + 2 * TAG_PAD)]


def _month_of(stage: "TimelineStage", x: float, rec: object) -> date:
    """월드 x(그 달 첫날) → 레코드의 달."""
    return min((d for d, _ in rec.values), key=lambda d: abs(stage.x_of(d) - x))  # type: ignore[attr-defined]


def _draw_pieces(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float],
                 seg: list[tuple[date, float]], mcol: dict, a: float) -> None:
    """color_by change 의 선(v4.4.0 D-0091 ②) — 달마다 조각(step = 앞 달 값에서 오르내리는 세로 + 그 달 가로, line = 앞 점→이 점)."""
    S = TIMELINE.series  # noqa: N806
    ctx.set_line_width(S.line_w)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i, (d, v) in enumerate(seg):
        y = value_y(stage, e["lane"], rng, v)
        x0 = stage.x_of(d)
        pts: list[tuple[float, float]] = []
        if e["style"] == "step":
            if i:
                pts.append((x0, value_y(stage, e["lane"], rng, seg[i - 1][1])))
            pts += [(x0, y), (stage.x_of(_next_month(d)), y)]
        elif i:
            pd, pv = seg[i - 1]
            pts = [(stage.x_of(pd), value_y(stage, e["lane"], rng, pv)), (x0, y)]
        if len(pts) < 2:
            continue
        ctx.new_path()
        for j, (x, yy) in enumerate(pts):
            sx, sy = view.to_screen(x, yy)
            (ctx.move_to if j == 0 else ctx.line_to)(sx, sy)
        ctx.set_source_rgba(*mcol[d], a)
        ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)


def quarter_span(stage: "TimelineStage", d: date) -> tuple[float, float]:
    """분기 마지막 날 d → 그 분기의 월드 x 구간 [분기 첫날, 다음 분기 첫날)."""
    q0 = date(d.year, (d.month - 1) // 3 * 3 + 1, 1)
    q1 = date(d.year + (q0.month == 10), 1 if q0.month == 10 else q0.month + 3, 1)
    return stage.x_of(q0), stage.x_of(q1)


def bar_rects(stage: "TimelineStage", e: dict, rng: tuple[float, float], rec: object) -> list[tuple[date, float, float, float, float, float]]:
    """(날짜, 값, 막대 x0, x1, 0 의 y, 값의 y) — 월드 좌표. 그리기와 검사가 같이 쓴다."""
    B = TIMELINE.bars  # noqa: N806
    y0 = value_y(stage, e["lane"], rng, 0.0)
    out = []
    for d, v in rec.values:  # type: ignore[attr-defined]
        qa, qb = quarter_span(stage, d)
        half = (qb - qa) * B.w_ratio / 2
        mid = (qa + qb) / 2
        out.append((d, v, mid - half, mid + half, y0, value_y(stage, e["lane"], rng, v)))
    return out


def _bar_path(ctx: cairo.Context, x0: float, x1: float, yz: float, ye: float, r: float) -> None:
    """막대 경로(v7.4.0 D-0310 §1-2, UF-155) — 0 쪽(yz)은 각, 바깥 끝(ye — 양수면 위, 음수면 아래) 두 모서리만 반지름 r. 화면 좌표."""
    h = abs(ye - yz)
    r = max(0.0, min(r, (x1 - x0) / 2, h))
    ctx.new_sub_path()
    if ye <= yz:   # 위로 선 막대
        ctx.move_to(x0, yz)
        ctx.line_to(x0, ye + r)
        ctx.arc(x0 + r, ye + r, r, math.pi, 3 * math.pi / 2)
        ctx.arc(x1 - r, ye + r, r, 3 * math.pi / 2, 2 * math.pi)
        ctx.line_to(x1, yz)
    else:          # 0 아래로 내려간 막대
        ctx.move_to(x0, yz)
        ctx.line_to(x1, yz)
        ctx.line_to(x1, ye - r)
        ctx.arc(x1 - r, ye - r, r, 0, math.pi / 2)
        ctx.arc(x0 + r, ye - r, r, math.pi / 2, math.pi)
        ctx.line_to(x0, yz)
    ctx.close_path()


def ladder_alpha(rank: int, steps: list[float]) -> float:
    """잉크 사다리 농도 — rank 0 = 최신 열(steps[0]), 1 부터 차례(넘으면 마지막 값). accent 열은 부르는 쪽이 솔리드로."""
    return steps[min(rank, len(steps) - 1)]


def _grow(front: float, x0: float, x1: float) -> float:
    return 1.0 if front == math.inf else ease_out(max(0.0, min(1.0, (front - x0) / max(x1 - x0, 1e-9))))


def accent_of(e: dict) -> str:
    """이벤트의 accent 대상(D-0310 감독 지시 ① — 그 순간 내레이션이 말하는 층·부문 하나). 기본 latest(최신 열·최신 합계)."""
    return e.get("accent") or "latest"


def _draw_bars(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float], rec: object,
               col: tuple[float, float, float], a: float, front: float) -> None:
    """분기 막대(v7.4.0 D-0278 §4.1·D-0308·D-0310) — 0 에서 자란다(앞끝이 막대를 지나는 동안 높이 0 → 값). 바닥 각·위 모서리만 top_radius.
    accent latest 면 최신 분기만 accent(col) 솔리드, 나머지는 단일 잉크 사다리. 값 라벨은 막대 끝에 직접(범례 없음)."""
    B = TIMELINE.bars  # noqa: N806
    rects = bar_rects(stage, e, rng, rec)
    ink = bar_ink()
    acc = accent_of(e)
    for n, (_d, v, x0, x1, y0, yv) in enumerate(rects):
        rank = len(rects) - 1 - n
        k = _grow(front, x0, x1)
        if k <= 0:
            continue
        sx0, sy0 = view.to_screen(x0, y0)
        sx1, sy1 = view.to_screen(x1, y0 + (yv - y0) * k)
        hot = acc == "latest" and rank == 0
        _bar_path(ctx, sx0, sx1, sy0, sy1, B.top_radius)
        if v < 0 and not hot:   # D-0328 — 손실 막대 = 채도 낮춘 면(테두리 없음)
            ctx.set_source_rgba(*loss_rgb(), a)
        else:
            ctx.set_source_rgba(*(col if hot else ink), (1.0 if hot else ladder_alpha(rank, B.ladder)) * a)
        ctx.fill()
        if k >= 1.0:
            s = fmt_value(v, "")
            lw = tw(ctx, s, B.value_size, B.value_font)
            by = sy1 - B.value_gap if v >= 0 else sy1 + B.value_gap + B.value_size
            text(ctx, s, (sx0 + sx1) / 2 - lw / 2, by, B.value_size, B.value_font, col if hot else ink, a, B.value_halo, "l")
    if e.get("estimate_id"):
        _draw_estimate(ctx, view, stage, e, rng, rects, front, a)


def _draw_estimate(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float],
                   rects: list, front: float, a: float) -> None:
    """예상치 = 속빈 막대(D-0308 §1-1·D-0310 §1-2 — 같은 모양, 윤곽 hollow_w). 실제보다 먼저 떠 있고(자라지 않는다) 실제가 그 안을 채운다.
    라벨: 실제가 있는 열 = 값 라벨 위 한 줄 "예상 v · ±p%"(코드 계산), 실제가 없는 열 = 속빈 막대 위 "예상 v"."""
    B = TIMELINE.bars  # noqa: N806
    ink = bar_ink()
    act = {d: (v, x0, x1, yv, k) for d, v, x0, x1, _y0, yv in rects for k in [_grow(front, x0, x1)]}
    for d, v in load_series(e["estimate_id"]).values:
        qa, qb = quarter_span(stage, d)
        half = (qb - qa) * B.w_ratio / 2
        x0, x1 = (qa + qb) / 2 - half, (qa + qb) / 2 + half
        y0 = value_y(stage, e["lane"], rng, 0.0)
        sx0, sy0 = view.to_screen(x0, y0)
        sx1, sy1 = view.to_screen(x1, value_y(stage, e["lane"], rng, v))
        w2 = B.hollow_w
        _bar_path(ctx, sx0 + w2 / 2, sx1 - w2 / 2, sy0, sy1 + (w2 / 2 if v >= 0 else -w2 / 2), B.top_radius)
        ctx.set_source_rgba(*ink, 0.9 * a)
        ctx.set_line_width(w2)
        ctx.stroke()
        hit = act.get(d)
        if hit is not None and hit[4] >= 1.0:   # 실제 값 라벨 위 한 줄
            av = hit[0]
            top = min(sy1, view.to_screen(0.0, value_y(stage, e["lane"], rng, av))[1]) if av >= 0 else sy1
            pct = (av - v) / abs(v) * 100 if v else None
            s = f"예상 {fmt_value(v, '')}" + (f" · {pct:+.0f}%" if pct is not None else "")
            by = top - B.value_gap - B.value_size - 3
        elif hit is None:
            s = f"예상 {fmt_value(v, '')}"
            by = sy1 - B.value_gap
        else:
            continue
        lw = tw(ctx, s, B.part_label_size, B.part_label_font)
        text(ctx, s, (sx0 + sx1) / 2 - lw / 2, by, B.part_label_size, B.part_label_font, ink, a, B.value_halo, "l")


def _seg_style(e: dict, i: int, v: float, col: tuple[float, float, float]) -> tuple[tuple[float, float, float], float, bool]:
    """쌓임 부문 칠 (rgb, 알파, 손실 윤곽 — 지금은 늘 False) — accent 부문 = col 솔리드, 손실(음수) = 채도 낮춘 면(loss_rgb, D-0328),
    나머지 = 잉크 사다리(부문 순서)."""
    B = TIMELINE.bars  # noqa: N806
    if accent_of(e) == e["parts"][i]["label"]:
        return col, 1.0, False
    if v < 0:
        return loss_rgb(), 1.0, False   # D-0328 — 손실 = 채도 낮춘 면, 테두리 없음
    return bar_ink(), B.stack_ladder[min(i, len(B.stack_ladder) - 1)], False


def label_rgb(fill: tuple[float, float, float], al: float, under: tuple[float, float, float]) -> tuple[tuple[float, float, float], bool]:
    """칠(알파 al, 아래 under 위 합성) 위 글자색 — 잉크(text)·바탕 중 대비가 큰 쪽(D-0314 §1-4). 둘 다 label_contrast_min 미만이면
    (중간 농도 칠) 바탕색 작은 판 위 잉크 글자(판 = True) — 판 위 대비가 그 값 미만이면 오류(P6)."""
    import numpy as np  # noqa: PLC0415

    from engine.contrast import ratio, rel_lum  # noqa: PLC0415

    def lum(c: tuple[float, float, float]) -> float:
        return float(rel_lum(np.asarray(c, np.float64)))

    ink = bar_ink()
    lm = lum(tuple(f * al + u * (1 - al) for f, u in zip(fill, under)))
    best = max(((ratio(lm, lum(c)), c) for c in (ink, under)), key=lambda r: r[0])
    if best[0] >= TIMELINE.bars.label_contrast_min:
        return best[1], False
    if ratio(lum(ink), lum(under)) < TIMELINE.bars.label_contrast_min:
        raise ValueError(f"부문 라벨 판 위 대비 < {TIMELINE.bars.label_contrast_min} — 팔레트 text·island 를 바꾼다(D-0314 §1-4)")
    return ink, True


def _draw_stack(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float],
                col: tuple[float, float, float], a: float, front: float, pr: float) -> None:
    """부문 쌓임(v7.4.0 D-0309 §1-2·3·D-0310) — 열마다 양수 부문은 0 위로, 음수 부문은 0 아래로. 부문 칠 = _seg_style(accent 하나·손실 down·잉크 사다리),
    부문 사이 1px 바탕색 틈. 합계 = 점 + 선(accent total 이면 accent). 부문 이름: 칸 높이 ≥ part_label_min_h 면 막대마다 안에,
    아니면 최신 막대 오른쪽에 지시선과 함께(범례 없음). 바깥 끝 모서리만 top_radius."""
    B = TIMELINE.bars  # noqa: N806
    ink = bar_ink()
    sep = island_rgb(SEP_RGB)
    acc = accent_of(e)
    cols = stack_columns(e)
    tots: list[tuple[float, float, float, bool, float]] = []   # (x, 점 y, 값, 최신, 라벨 기준 y)
    leaders: list[tuple[float, float, str, tuple[float, float, float]]] = []   # (막대 오른쪽 x, 칸 가운데 y, 이름, 글자색)
    for n, (d, tot, vals) in enumerate(cols):
        latest = n == len(cols) - 1
        qa, qb = quarter_span(stage, d)
        half = (qb - qa) * B.w_ratio / 2
        mid = (qa + qb) / 2
        x0, x1 = mid - half, mid + half
        k = _grow(front, x0, x1)
        if k <= 0:
            continue
        y0 = value_y(stage, e["lane"], rng, 0.0)
        pos = sum(v for v in vals if v > 0) * k
        neg = sum(v for v in vals if v < 0) * k
        sx0, sy0 = view.to_screen(x0, y0)
        sx1, _ = view.to_screen(x1, y0)
        ytop = view.to_screen(0.0, value_y(stage, e["lane"], rng, pos))[1]
        ybot = view.to_screen(0.0, value_y(stage, e["lane"], rng, neg))[1]
        segs: list[tuple[int, float, float, float]] = []   # (부문 번호, 화면 y 시작, 끝, 값)
        up = down = 0.0
        for i, v in enumerate(vals):
            if v == 0:
                continue
            a0 = up if v > 0 else down
            a1 = a0 + v * k
            if v > 0:
                up = a1
            else:
                down = a1
            segs.append((i, view.to_screen(0.0, value_y(stage, e["lane"], rng, a0))[1],
                         view.to_screen(0.0, value_y(stage, e["lane"], rng, a1))[1], v))
        for ye in (ytop, ybot):   # 양수·음수 막대 — 바깥 끝만 둥글게(0 쪽은 각, 0 기준선이 또렷)
            if abs(ye - sy0) < 0.5:
                continue
            ctx.save()
            _bar_path(ctx, sx0, sx1, sy0, ye, B.top_radius)
            ctx.clip()
            for i, s0, s1, v in segs:
                if (v > 0) == (ye < sy0):
                    rgb, al, loss = _seg_style(e, i, v, col)
                    ctx.rectangle(sx0, min(s0, s1), sx1 - sx0, abs(s1 - s0))
                    ctx.set_source_rgba(*rgb, al * a)
                    ctx.fill()
                    if loss:   # 손실 윤곽(clip 안 — 바깥 끝 둥근 모서리를 따른다)
                        w2 = B.neg_outline_w
                        ctx.rectangle(sx0 + w2 / 2, min(s0, s1) + w2 / 2, sx1 - sx0 - w2, abs(s1 - s0) - w2)
                        ctx.set_source_rgba(*C[B.loss_color], a)
                        ctx.set_line_width(w2)
                        ctx.stroke()
                    if B.stack_sep_w > 0:   # 부문 경계 1px 바탕색(바깥 끝 쪽)
                        ctx.rectangle(sx0, s1 - B.stack_sep_w / 2, sx1 - sx0, B.stack_sep_w)
                        ctx.set_source_rgba(*sep, a)
                        ctx.fill()
            ctx.restore()
        if k < 1.0:
            continue
        ty = view.to_screen(0.0, value_y(stage, e["lane"], rng, tot))[1]
        ly = min(ty, ytop) - B.value_gap - B.total_dot_r if tot >= 0 else max(ty, ybot) + B.value_gap + B.total_dot_r + B.value_size
        tots.append(((sx0 + sx1) / 2, ty, tot, latest, ly))
        part_named = any(p["label"] == acc for p in e["parts"])   # 부문 이름은 부문을 말하는 문장(accent = 부문)에서만 — 합계·주가 층에서는 접는다(UF-154 동시 가시 상한)
        for i, s0, s1, v in (segs if part_named else []):   # 부문 이름(직접 라벨)
            lab = e["parts"][i]["label"]
            lw = tw(ctx, lab, B.part_label_size, B.part_label_font)
            rgb, al, _loss = _seg_style(e, i, v, col)
            fg, plate = label_rgb(rgb, al, sep)
            if abs(s1 - s0) >= B.part_label_min_h and lw <= (sx1 - sx0) - 4:
                lx, by = (sx0 + sx1) / 2 - lw / 2, (s0 + s1) / 2 + B.part_label_size * 0.35
                if plate:   # 중간 농도 칠 — 바탕색 판(끝값 판과 같은 여백·알파 1)
                    pad = TIMELINE.series.end_label_plate.pad_px / 2
                    ctx.rectangle(lx - pad, by - B.part_label_size * 0.85 - pad / 2, lw + 2 * pad, B.part_label_size * 1.05 + pad)
                    ctx.set_source_rgba(*sep, a)
                    ctx.fill()
                text(ctx, lab, lx, by, B.part_label_size, B.part_label_font, fg, a, 0, "l")
            elif latest:
                leaders.append((sx1, (s0 + s1) / 2, lab, rgb if al >= 0.5 else (C[B.loss_color] if _loss else ink)))
    _draw_leaders(ctx, leaders, a)
    if not e.get("total", True):
        return
    if len(tots) > 1:   # 합계 선
        ctx.new_path()
        for j, (x, y, _v, _l, _ly) in enumerate(tots):
            (ctx.move_to if j == 0 else ctx.line_to)(x, y)
        ctx.set_source_rgba(*(col if acc == "total" else ink), (1.0 if acc == "total" else B.total_alpha) * a)
        ctx.set_line_width(B.total_line_w)
        ctx.stroke()
    for x, y, v, latest, ly in tots:   # 합계 점·값 — accent total 이면 전부, latest 면 최신만
        hot = acc == "total" or (acc == "latest" and latest)
        rgb = col if hot else ink
        ctx.arc(x, y, B.total_dot_r * (1.3 if hot else 1.0), 0, 2 * math.pi)
        ctx.set_source_rgba(*rgb, a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*sep, a)
        ctx.set_line_width(1.0)
        ctx.stroke()
        s = fmt_value(v, "")
        lw = tw(ctx, s, B.value_size, B.value_font)
        text(ctx, s, x - lw / 2, ly, B.value_size, B.value_font, rgb, a, B.value_halo, "l")


def _pair_fill(e: dict, lab: str, worse: bool, col: tuple[float, float, float]) -> tuple[tuple[float, float, float], float, bool]:
    """덤벨 채움 원·diverging 막대 칠 (rgb, 알파, 손실 윤곽 — 지금은 늘 False) — accent 부문 = col 솔리드,
    감소 = 채도 낮춘 면(loss_rgb, D-0328 — 강조색과 구별), 나머지 = 잉크 stack_ladder 첫 단."""
    B = TIMELINE.bars  # noqa: N806
    if accent_of(e) == lab:
        return col, 1.0, False
    if worse:
        return loss_rgb(), 1.0, False   # D-0328 — 감소 = 채도 낮춘 면, 테두리 없음
    return bar_ink(), B.stack_ladder[0], False


def _draw_pairs(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float],
                col: tuple[float, float, float], a: float, front: float) -> None:
    """부문 비교(v7.4.0 D-0308 §2·D-0315 §1-3) — 열 분기 안에 부문을 나란히(시간축 세계 안, 독립 패널 금지 UF-135).
    dumbbell: 속빈 원 = 전분기, 채움 원 = 이번 분기, 사이 선. 이름·두 값은 열 오른쪽 지시선 라벨("DC 6.3→7.3").
    diverging: 0 기준 위아래 막대(전년 동기 대비 %, 코드 계산), 값 라벨은 막대 바깥 끝, 이름은 그 바깥.
    accent 는 부문 하나(없으면 none). 감소 = 흐린 채움 + down 윤곽. 앞끝(front)이 묶음을 지나는 동안 자란다."""
    B = TIMELINE.bars  # noqa: N806
    ink = bar_ink()
    _d0, d1, items = pair_items(e)
    qa, qb = quarter_span(stage, d1)
    half = (qb - qa) * B.pair_w_ratio / 2
    gx0, gx1 = (qa + qb) / 2 - half, (qa + qb) / 2 + half
    k = _grow(front, gx0, gx1)
    if k <= 0:
        return
    slot = (gx1 - gx0) / len(items)
    yv = lambda v: view.to_screen(0.0, value_y(stage, e["lane"], rng, v))[1]  # noqa: E731
    leaders: list[tuple[float, float, str, tuple[float, float, float]]] = []
    for i, (lab, v0, v1) in enumerate(items):
        xc = view.to_screen(gx0 + slot * (i + 0.5), 0.0)[0]
        if e["style"] == "dumbbell":
            y0, y1 = yv(v0), yv(v0 + (v1 - v0) * k)
            rgb, al, loss = _pair_fill(e, lab, v1 < v0, col)
            ctx.move_to(xc, y0)
            ctx.line_to(xc, y1)
            ctx.set_source_rgba(*ink, B.pair_line_alpha * a)
            ctx.set_line_width(B.pair_line_w)
            ctx.stroke()
            ctx.arc(xc, y0, B.pair_dot_r - B.hollow_w / 2, 0, 2 * math.pi)   # 속빈 원 = 전분기(예상·이전 = 속빈, D-0308 §1-1)
            ctx.set_source_rgba(*island_rgb(SEP_RGB), a)
            ctx.fill_preserve()
            ctx.set_source_rgba(*ink, 0.9 * a)
            ctx.set_line_width(B.hollow_w)
            ctx.stroke()
            ctx.arc(xc, y1, B.pair_dot_r, 0, 2 * math.pi)
            ctx.set_source_rgba(*island_rgb(SEP_RGB), a)   # 흐린 채움이 선·바탕을 비치지 않게 바탕을 먼저
            ctx.fill_preserve()
            ctx.set_source_rgba(*rgb, al * a)
            ctx.fill_preserve()
            if loss:
                ctx.set_source_rgba(*C[B.loss_color], a)
                ctx.set_line_width(B.neg_outline_w)
                ctx.stroke()
            ctx.new_path()
            if k >= 1.0:
                fg = rgb if al >= 0.5 else ink   # 감소 글자는 잉크 — down 글자색은 강조(코랄)와 한눈에 같다(D-0314 §1-1)
                leaders.append((view.to_screen(gx1, 0.0)[0], y1, f"{lab} {fmt_value(v0, '')}→{fmt_value(v1, '')}", fg))
            continue
        p = yoy_pct(v0, v1)
        hw = slot * B.diverging_w_ratio / 2 * view.s
        yz, ye = yv(0.0), yv(p * k)
        rgb, al, loss = _pair_fill(e, lab, p < 0, col)
        _bar_path(ctx, xc - hw, xc + hw, yz, ye, B.top_radius)
        ctx.set_source_rgba(*rgb, al * a)
        ctx.fill()
        if loss:
            w2 = B.neg_outline_w
            _bar_path(ctx, xc - hw + w2 / 2, xc + hw - w2 / 2, yz, ye - w2 / 2 if p >= 0 else ye + w2 / 2, B.top_radius)
            ctx.set_source_rgba(*C[B.loss_color], a)
            ctx.set_line_width(w2)
            ctx.stroke()
        if k < 1.0:
            continue
        fg = rgb if al >= 0.5 else ink
        s = f"{p:+.0f}%"
        vb = ye - B.value_gap if p >= 0 else ye + B.value_gap + B.value_size   # 값 = 막대 바깥 끝 바로 옆
        nb = vb - B.value_size - 2 if p >= 0 else vb + B.part_label_size + 2   # 이름 = 그 바깥
        for w, by, size, font, fc in ((s, vb, B.value_size, B.value_font, fg), (lab, nb, B.part_label_size, B.part_label_font, ink)):
            text(ctx, w, xc - tw(ctx, w, size, font) / 2, by, size, font, fc, a, B.value_halo, "l")
    _draw_leaders(ctx, leaders, a)


def _guide_bar(ctx: cairo.Context, x0: float, x1: float, yv: "object", lo: float, hi: float, est: float | None, a: float,
               line_w: float, dot_r: float) -> tuple[float, float | None]:
    """가이던스 그림 한 벌(v7.4.0 D-0321 §2-1) — 다른 막대와 같은 폭의 속 빈 막대(0 → 위 끝, 바닥 각·위 모서리 top_radius),
    아래 끝~위 끝 띠(잉크 guide_band_alpha), 시장 예상 = 속 빈 동그라미 + 짧은 가로 획. yv = 값 → 화면 y. 열 안·열 확대 인셋이 같은 함수.
    돌려준다: (띠 가운데 y, 예상 y)."""
    from engine.style import stage_surface  # noqa: PLC0415

    B = TIMELINE.bars  # noqa: N806
    ink = bar_ink()
    ylo, yhi = yv(lo), yv(hi)
    w2 = line_w
    if stage_surface():   # D-0328 §1·D-0330 — 테두리 0: 몸통 = 사다리 가장 옅은 면(0 → 위 끝), 범위 = 같은 폭 띠(진한 단)
        from engine.style import bg_rgb  # noqa: PLC0415

        g, m = bg_rgb(TIMELINE.bg_rgb), B.ladder[-1]
        _bar_path(ctx, x0, x1, yv(0.0), yhi, B.top_radius)   # 불투명 합성색 — 열 accent 띠가 비쳐 손실 면(갈색)처럼 읽히지 않게(감독 판정 R-0306)
        ctx.set_source_rgba(*(i * m + b * (1 - m) for i, b in zip(ink, g)), a)
        ctx.fill()
        ctx.rectangle(x0, yhi, x1 - x0, ylo - yhi)
        ctx.set_source_rgba(*ink, B.guide_band_alpha * a)
        ctx.fill()
    else:
        ctx.rectangle(x0, yhi, x1 - x0, ylo - yhi)   # 띠(범위가 막대의 머리)
        ctx.set_source_rgba(*ink, B.guide_band_alpha * a)
        ctx.fill()
        _bar_path(ctx, x0 + w2 / 2, x1 - w2 / 2, yv(0.0), yhi + w2 / 2, B.top_radius)
        ctx.set_source_rgba(*ink, 0.95 * a)
        ctx.set_line_width(w2)
        ctx.stroke()
    ctx.set_source_rgba(*ink, 0.95 * a)
    ye = None
    if est is not None:
        ye = yv(est)
        xc = (x0 + x1) / 2
        hw = (x1 - x0) * B.guide_tick_ratio / 2
        ctx.move_to(xc - hw, ye)
        ctx.line_to(xc - dot_r, ye)
        ctx.move_to(xc + dot_r, ye)
        ctx.line_to(xc + hw, ye)
        ctx.set_line_width(max(1.0, w2 * 0.6))
        ctx.stroke()
        ctx.new_sub_path()
        ctx.arc(xc, ye, dot_r - w2 / 2, 0, 2 * math.pi)
        ctx.set_line_width(w2)
        ctx.stroke()
    return (ylo + yhi) / 2, ye


def _draw_range(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float], a: float, front: float,
                t: float) -> None:
    """가이던스(v7.4.0 D-0308 §1-1·D-0315 §1-3·D-0321 §2-1) — 분기 열마다 속 빈 막대 0 → 위 끝(upper_id), 아래 끝(series_id)~위 끝 띠,
    estimate_id = 시장 예상 속 빈 동그라미 + 가로 획(같은 열, 범위 날짜만). 자라지 않고 떠오른다(앞끝이 열을 지나는 동안 알파).
    라벨은 열 오른쪽 "가이던스 15~16" · "예상 17.1"(레코드 값 그대로, 범례 없음) — 같은 열의 확대 인셋이 떠 있는 동안은 접는다
    (인셋이 같은 수를 크게 말한다 — 되풀이 글자 금지)."""
    B = TIMELINE.bars  # noqa: N806
    ink = bar_ink()
    est = dict(load_series(e["estimate_id"]).values) if e.get("estimate_id") else {}
    yv = lambda v: view.to_screen(0.0, value_y(stage, e["lane"], rng, v))[1]  # noqa: E731
    hidden = any(t0 <= t <= t1 for t0, t1 in e.get("labels_hidden") or [])
    leaders: list[tuple[float, float, str, tuple[float, float, float]]] = []
    for d, lo, hi in band_pairs(e):
        qa, qb = quarter_span(stage, d)
        half = (qb - qa) * B.w_ratio / 2
        x0, x1 = (qa + qb) / 2 - half, (qa + qb) / 2 + half
        k = _grow(front, x0, x1)
        if k <= 0:
            continue
        sx0, sx1 = view.to_screen(x0, 0.0)[0], view.to_screen(x1, 0.0)[0]
        ym, ye = _guide_bar(ctx, sx0, sx1, yv, lo, hi, est.get(d), k * a, B.hollow_w, B.pair_dot_r)
        if k < 1.0 or hidden:
            continue
        leaders.append((sx1, ym, f"가이던스 {fmt_value(lo, '')}~{fmt_value(hi, '')}", ink))
        if ye is not None:
            leaders.append((sx1, ye, f"예상 {fmt_value(est[d], '')}", ink))
    _draw_leaders(ctx, leaders, a)


def detail_column(e: dict) -> tuple[date, str]:
    """열 확대 인셋이 가리키는 분기 열과 머리 줄 기간 문구. range = 아래 끝 레코드의 (첫) 분기, 그 밖 = pair_items 의 열 분기."""
    def q(d: date) -> str:
        return f"{d.year}년 {(d.month - 1) // 3 + 1}분기"

    if e["style"] == "range":
        d1 = band_pairs(e)[0][0]
        return d1, q(d1)
    d0, d1, _ = pair_items(e)
    return d1, (f"{q(d0)} → {(d1.month - 1) // 3 + 1}분기" if d0.year == d1.year else f"{q(d0)} → {q(d1)}")


def detail_unit(e: dict) -> str:
    return "%" if e["style"] == "diverging" else load_series(e["series_id"]).unit


def detail_rect(view: "View", side: str, ytop: float, ybot: float) -> tuple[float, float, float, float]:
    """인셋 상자(뷰 화면 좌표 x, y, w, h) — 가로 = 뷰 폭 × w_ratio(side = left|right, margin_px), 세로 = 레인 플롯 높이(ytop~ybot) × h_ratio
    가운데. 레인 이름 줄·출처 줄(레인 밖)을 덮지 않는다."""
    CD = load_rules().island.column_detail  # noqa: N806
    w, h = view.vw * CD.w_ratio, (ybot - ytop) * CD.h_ratio
    x = view.ox + CD.margin_px if side == "left" else view.ox + view.vw - CD.margin_px - w
    return x, ytop + (ybot - ytop - h) / 2, w, h


def detail_side_ok(side: str, fa: float, fb: float) -> bool:
    """뷰 폭 비율 [fa, fb] 의 열을 그 자리의 인셋이 가리지 않는가(margin 은 비율로 근사하지 않고 w_ratio 만 — 보수적으로 여유를 둔다)."""
    CD = load_rules().island.column_detail  # noqa: N806
    lo, hi = (0.0, CD.w_ratio + 0.03) if side == "left" else (1 - CD.w_ratio - 0.03, 1.0)
    return fb <= lo or fa >= hi


def _push_apart(ys: list[float], gap: float, hi: float | None = None) -> list[float]:
    """세로 라벨 기준선 겹침 풀기 — 정렬 순서대로 앞 라벨과 gap 이상 떨어지게 아래로 민다(원래 순서 유지).
    hi(아래 한계)를 주면 넘친 만큼 아래에서부터 위로 되민다(상자 밖으로 흘러내리지 않게)."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    out = list(ys)
    last = -math.inf
    for i in order:
        out[i] = max(ys[i], last + gap)
        last = out[i]
    if hi is not None:
        nxt = math.inf
        for i in reversed(order):
            out[i] = min(out[i], hi, nxt - gap)
            nxt = out[i]
    return out


def _draw_column_detail(ctx: cairo.Context, view: "View", stage: "TimelineStage", t: float, e: dict,
                        rng: tuple[float, float], a: float) -> None:
    """열 확대 인셋(v7.4.0 D-0318·D-0319 ④) — 차트 아일랜드 안 한 분기 열(accent 띠)을 리더선으로 가리키는 둥근 사각.
    같은 레코드·같은 값을 크게(글자 ≥ 12px·점 ≥ 5px). 자리 = prepare_series 가 정한 detail_side(예측 — 생애 내내 열을 가리지 않는 첫 자리).
    등장: 열 쪽에서 미끄러지며 페이드(fade·slide_px), 값은 grow_sec 동안 자란다. 범례 없음(직접 라벨)."""
    CD = load_rules().island.column_detail  # noqa: N806
    B = TIMELINE.bars  # noqa: N806
    ink = bar_ink()
    col = C[e.get("col", "gold")]
    cin, cout = bool(e.get("detail_cont_in")), bool(e.get("detail_cont_out"))   # 앞·뒤 문장과 이어진 같은 인셋(accent 만 옮김)
    al = window(t, e["t0"], e["t1"], 0.0 if cin else CD.fade[0], 0.0 if cout else CD.fade[1]) * a
    if al <= 0.01:
        return
    d1, span = detail_column(e)
    qa, qb = quarter_span(stage, d1)
    cx0, cx1 = view.to_screen(qa, 0.0)[0], view.to_screen(qb, 0.0)[0]
    ytop = view.to_screen(0.0, value_y(stage, e["lane"], rng, rng[1]))[1]
    ybot = view.to_screen(0.0, value_y(stage, e["lane"], rng, rng[0]))[1]
    from engine.style import stage_surface  # noqa: PLC0415

    ctx.save()
    if stage_surface():   # 무대 표면(아일랜드 그룹 바탕 투명): 띠는 이미 그린 막대·띠 뒤로 — 막대 색이 띠에 물들지 않게(감독 판정 R-0306)
        ctx.set_operator(cairo.OPERATOR_DEST_OVER)
    ctx.rectangle(cx0, ytop, cx1 - cx0, ybot - ytop)   # 열 띠 — 무대 표면은 text 잉크 아주 옅게(band_ink_alpha), 그 밖은 accent
    ctx.set_source_rgba(*(C["white"] if stage_surface() else col), (CD.band_ink_alpha if stage_surface() else CD.band_alpha) * al)
    ctx.fill()
    ctx.restore()
    side = e.get("detail_side", CD.side_order[0])
    x, y, w, h = detail_rect(view, side, ytop, ybot)
    u = 1.0 if cin else ease_out(min(1.0, max(0.0, (t - e["t0"]) / max(CD.fade[0], 1e-6))))
    x += (1 - u) * CD.slide_px * (1 if side == "left" else -1) * (1 if (cx0 + cx1) / 2 > x + w / 2 else -1)
    k = 1.0 if cin else ease_out(min(1.0, max(0.0, (t - e["t0"] - CD.fade[0] * 0.5) / max(CD.grow_sec, 1e-6))))
    ex = x + w - CD.radius if side == "left" else x + CD.radius   # 리더선: 열의 인셋 쪽 변 → 인셋 위 변, 수평. 높이 = 레인 위 끝(값 라벨보다 위 — 가로지르지 않는다)
    ly = y + 0.5
    ctx.move_to(cx0 if side == "left" else cx1, ly)
    ctx.line_to(ex, ly)
    ctx.set_source_rgba(*ink, CD.leader_alpha * al)
    ctx.set_line_width(CD.leader_w)
    ctx.stroke()
    from engine.style import PALETTE  # noqa: PLC0415

    sep = PALETTE.get("island_deep", island_rgb(SEP_RGB))   # v7.4.0 D-0322 정정 — 르포 card_deep
    from engine.style import stage_surface  # noqa: PLC0415

    flat = stage_surface()
    rrect(ctx, x, y, w, h, 0.0 if flat else CD.radius)   # 무대 표면 = 모서리 0·테두리 0(D-0328 §3·D-0330)
    ctx.set_source_rgba(*sep, CD.fill_alpha * al)
    if flat:
        ctx.fill()
    else:
        ctx.fill_preserve()
        ctx.set_source_rgba(*ink, CD.edge_alpha * al)
        ctx.set_line_width(1.0)
        ctx.stroke()
    p = CD.pad_px
    if flat:   # D-0328 §3·D-0330 — 머리 줄 없이 짧은 이름 하나(연출 title — 기간·단위를 그 안에 짧게), 라벨 위계(sans muted)
        text(ctx, e["title"], x + p, y + p + CD.text_size * 0.8, CD.text_size, CD.text_font, C["muted"], al, 0, "l")
    else:
        head = f"{e['title']}({detail_unit(e)})" if e["style"] == "slope" else f"{span} · {e['title']}({detail_unit(e)})"   # slope 는 두 시점을 열 머리에(되풀이 글자 금지)
        text(ctx, head, x + p, y + p + CD.head_size * 0.8, CD.head_size, CD.head_font, ink, al, 0, "l")
    ax0, ax1 = x + p, x + w - p
    ay0, ay1 = y + p + CD.head_size + 16, y + h - p - CD.text_size - 8   # 맨 아래 줄 = 부문 이름
    ny = y + h - p   # 이름 기준선
    ts, vf, tf = CD.text_size, CD.value_font, CD.text_font

    def mapy(v: float, lo: float, hi: float) -> float:
        return ay1 - (v - lo) / (hi - lo) * (ay1 - ay0)

    if e["style"] == "range":   # D-0321 §2-2 — 4분기 열을 키운 그림(같은 막대·띠·동그라미, 위쪽만 확대 — 막대는 인셋 아래로 이어진다)
        (_d, lo, hi), = band_pairs(e)[:1]
        est = dict(load_series(e["estimate_id"]).values).get(d1) if e.get("estimate_id") else None
        top_v = max(hi, est if est is not None else hi)
        span_v = top_v - lo
        a_lo, a_hi = lo - span_v * 1.2, top_v + span_v * 0.35
        bw = (ax1 - ax0) * CD.guide_bar_ratio
        bx0 = ax0 + (ax1 - ax0) * 0.18
        ctx.save()
        ctx.rectangle(x, ay0 - 6, w, ay1 - ay0 + 12)
        ctx.clip()
        for tv in range(math.ceil(a_lo), math.floor(a_hi) + 1):   # 눈금(확대 척도를 숨기지 않는다)
            ty = mapy(tv, a_lo, a_hi)
            ctx.move_to(bx0 - 6, ty)
            ctx.line_to(bx0 - 2, ty)
            ctx.set_source_rgba(*ink, 0.5 * al)
            ctx.set_line_width(1.0)
            ctx.stroke()
            s_ = fmt_value(float(tv), "")
            text(ctx, s_, bx0 - 9 - tw(ctx, s_, ts, tf), ty + ts * 0.35, ts, tf, ink, al * 0.6, 0, "l")
        ym, ye = _guide_bar(ctx, bx0, bx0 + bw, lambda v: mapy(v, a_lo, a_hi), lo, hi, est, al, B.hollow_w * 1.5, CD.dot_r)
        ctx.restore()
        rows = [(ym, f"가이던스 {fmt_value(lo, '')}~{fmt_value(hi, '')}", ink)] + ([(ye, f"시장 예상 {fmt_value(est, '')}", ink)] if ye is not None else [])
        lys = _push_apart([r[0] + ts * 0.35 for r in rows], ts * CD.label_gap_ratio + 2)
        lx = bx0 + bw + 14
        for (yy, s_, rgb), ly in zip(rows, lys):
            if abs(ly - ts * 0.35 - yy) > 2:   # 밀려난 라벨은 가는 리더선으로 자기 자리에
                ctx.move_to(bx0 + bw + 2, yy)
                ctx.line_to(lx - 3, ly - ts * 0.35)
                ctx.set_source_rgba(*ink, 0.6 * al)
                ctx.set_line_width(1.0)
                ctx.stroke()
            text(ctx, s_, lx, ly, ts, vf, rgb, al, 0, "l")
        if est is not None:   # 차이(코드 계산) — 가이던스 끝 − 예상
            s_ = f"예상 대비 {lo - est:+.1f} ~ {hi - est:+.1f}"
            text(ctx, s_, lx, ny, ts, tf, ink, al, 0, "l")
        return
    _d0, _d1, items = pair_items(e)
    n = len(items)
    slot = (ax1 - ax0) / n
    acc = e.get("accent") or "none"
    if e["style"] == "slope":
        sh = items   # D-0320 C2 — 1년 전 → 지금 값(레코드 그대로)
        if e.get("accent") is None:   # 상승 accent 1(D-0308 §2) — 가장 크게 오른 부문
            ups = [(b - a_, lab) for lab, a_, b in sh if b > a_]
            acc = max(ups)[1] if ups else "none"
        vs = [v for _l, a_, b in sh for v in (a_, b)]
        a_lo, a_hi = min(vs), max(vs)
        pd_ = (a_hi - a_lo) * 0.12 or 1.0
        a_lo, a_hi = a_lo - pd_, a_hi + pd_
        xa, xb = ax0 + (ax1 - ax0) * 0.28, ax1 - (ax1 - ax0) * 0.34
        q0 = span.split(" → ")
        text(ctx, q0[0], xa - tw(ctx, q0[0], ts, tf) / 2, ay0 - 4, ts, tf, ink, al * 0.8, 0, "l")
        rlab = q0[1] if len(q0) > 1 else ""
        text(ctx, rlab, xb - tw(ctx, rlab, ts, tf) / 2, ay0 - 4, ts, tf, ink, al * 0.8, 0, "l")
        lrows, rrows = [], []
        for i, (lab, v0, v1) in enumerate(sh):
            hot = lab == acc
            rgb = col if hot else ink
            y0, y1 = mapy(v0, a_lo, a_hi), mapy(v0 + (v1 - v0) * k, a_lo, a_hi)
            ctx.move_to(xa, y0)
            ctx.line_to(xa + (xb - xa) * k, y1)
            ctx.set_source_rgba(*rgb, (1.0 if hot else B.stack_ladder[min(i, len(B.stack_ladder) - 1)]) * al)
            ctx.set_line_width(CD.line_w * (1.3 if hot else 1.0))
            ctx.stroke()
            for xx, yy in ((xa, y0), (xa + (xb - xa) * k, y1)):
                ctx.arc(xx, yy, CD.dot_r * 0.7, 0, 2 * math.pi)
                ctx.set_source_rgba(*rgb, al)
                ctx.fill()
            lrows.append((y0, f"{v0:.1f}", rgb))   # 공시 자릿수 그대로(조 원 소수 첫째)
            rrows.append((mapy(v1, a_lo, a_hi), f"{lab} {v1:.1f}", rgb))
        if k >= 1.0:   # D-0321 §3 — 라벨은 글자 크기 × label_gap_ratio 간격으로 밀고, 밀린 라벨은 가는 리더선으로 자기 점에
            lead = CD.dot_r + 12
            for rows, px, right in ((lrows, xa, True), (rrows, xb, False)):
                lys = _push_apart([r[0] + ts * 0.35 for r in rows], ts * CD.label_gap_ratio, y + h - p)
                xx = px - lead if right else px + lead
                for (yy, s, rgb), ly in zip(rows, lys):
                    ctx.move_to(px + (-CD.dot_r - 1 if right else CD.dot_r + 1), yy)
                    ctx.line_to(xx + (2 if right else -2), ly - ts * 0.35)
                    ctx.set_source_rgba(*rgb, 0.6 * al)
                    ctx.set_line_width(1.0)
                    ctx.stroke()
                    text(ctx, s, xx - (tw(ctx, s, ts, vf) if right else 0), ly, ts, vf, rgb, al, 0, "l")
        return
    if e["style"] == "dumbbell":
        vs = [v for _l, a_, b in items for v in (a_, b)]
        a_lo, a_hi = min(vs), max(vs)
        pd_ = (a_hi - a_lo) * 0.15 or 1.0
        a_lo, a_hi = a_lo - pd_, a_hi + pd_
        for i, (lab, v0, v1) in enumerate(items):
            xc = ax0 + slot * (i + 0.5) - slot * 0.12
            y0, y1 = mapy(v0, a_lo, a_hi), mapy(v0 + (v1 - v0) * k, a_lo, a_hi)
            rgb, fa, loss = _pair_fill(e, lab, v1 < v0, col) if acc != "none" or v1 < v0 else (ink, B.stack_ladder[0], False)
            ctx.move_to(xc, y0)
            ctx.line_to(xc, y1)
            ctx.set_source_rgba(*ink, B.pair_line_alpha * al)
            ctx.set_line_width(CD.line_w)
            ctx.stroke()
            ctx.arc(xc, y0, CD.dot_r - B.hollow_w / 2, 0, 2 * math.pi)   # 속빈 원 = 전분기
            ctx.set_source_rgba(*sep, al)
            ctx.fill_preserve()
            ctx.set_source_rgba(*ink, 0.9 * al)
            ctx.set_line_width(B.hollow_w)
            ctx.stroke()
            ctx.arc(xc, y1, CD.dot_r, 0, 2 * math.pi)
            ctx.set_source_rgba(*sep, al)
            ctx.fill_preserve()
            ctx.set_source_rgba(*rgb, fa * al)
            ctx.fill_preserve()
            if loss:
                ctx.set_source_rgba(*C[B.loss_color], al)
                ctx.set_line_width(B.neg_outline_w)
                ctx.stroke()
            ctx.new_path()
            fg = ink if v1 < v0 else (rgb if fa >= 0.5 else ink)   # 감소 항목의 글자는 잉크(면만 흐리게 — 글자가 바탕에 묻히지 않게, D-0330)
            text(ctx, fmt_value(v0, ""), xc + CD.dot_r + 5, y0 + ts * 0.35, ts, tf, ink, al * 0.75, 0, "l")
            if k >= 1.0:
                text(ctx, fmt_value(v1, ""), xc + CD.dot_r + 5, y1 + ts * 0.35, ts, vf, fg, al, 0, "l")
            text(ctx, lab, xc - tw(ctx, lab, ts, tf) / 2, ny, ts, tf, fg, al, 0, "l")
        return
    pcts = [yoy_pct(a_, b) for _l, a_, b in items]   # diverging
    a_lo, a_hi = min(0.0, *pcts), max(0.0, *pcts)
    pd_ = (a_hi - a_lo) * 0.18 or 1.0
    a_lo, a_hi = a_lo - (pd_ if a_lo < 0 else 0), a_hi + pd_
    yz = mapy(0.0, a_lo, a_hi)
    ctx.move_to(ax0, yz)
    ctx.line_to(ax1, yz)
    ctx.set_source_rgba(*ink, B.zero_alpha * al)
    ctx.set_line_width(B.zero_w)
    ctx.stroke()
    for i, ((lab, _v0, _v1), pc) in enumerate(zip(items, pcts)):
        xc = ax0 + slot * (i + 0.5)
        hw = slot * CD.bar_w_ratio / 2
        ye = mapy(pc * k, a_lo, a_hi)
        rgb, fa, loss = _pair_fill(e, lab, pc < 0, col) if acc != "none" or pc < 0 else (ink, B.stack_ladder[0], False)
        _bar_path(ctx, xc - hw, xc + hw, yz, ye, B.top_radius)
        ctx.set_source_rgba(*rgb, fa * al)
        ctx.fill()
        if loss:
            w2 = B.neg_outline_w
            _bar_path(ctx, xc - hw + w2 / 2, xc + hw - w2 / 2, yz, ye + (w2 / 2 if pc < 0 else -w2 / 2), B.top_radius)
            ctx.set_source_rgba(*C[B.loss_color], al)
            ctx.set_line_width(w2)
            ctx.stroke()
        fg = ink if pc < 0 else (rgb if fa >= 0.5 else ink)   # 감소 항목의 글자는 잉크(D-0330)
        if k >= 1.0:
            s = f"{pc:+.0f}%"
            by = ye - 6 if pc >= 0 else ye + 6 + ts
            text(ctx, s, xc - tw(ctx, s, ts, vf) / 2, by, ts, vf, fg, al, 0, "l")
        text(ctx, lab, xc - tw(ctx, lab, ts, tf) / 2, ny, ts, tf, fg, al, 0, "l")


def _draw_leaders(ctx: cairo.Context, leaders: list[tuple[float, float, str, tuple[float, float, float]]], a: float) -> None:
    """작은 부문 이름 — 최신 막대 오른쪽에 지시선(leader_len) + 이름. 이름끼리 겹치면 아래로 민다(글자 크기 + 2px 간격)."""
    B = TIMELINE.bars  # noqa: N806
    gap = B.part_label_size + 2
    placed: list[float] = []
    for x, y, lab, rgb in sorted(leaders, key=lambda r: r[1]):
        ly = max([y] + [p + gap for p in placed])
        placed.append(ly)
        ctx.move_to(x + 1, y)
        ctx.line_to(x + B.leader_len * 0.6, y)
        ctx.line_to(x + B.leader_len, ly)
        ctx.set_source_rgba(*rgb, 0.85 * a)
        ctx.set_line_width(1.0)
        ctx.stroke()
        text(ctx, lab, x + B.leader_len + B.part_label_dx * 0.5, ly + B.part_label_size * 0.35, B.part_label_size,
             B.part_label_font, rgb, a, 2.0, "l")


def _draw_band(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float],
               col: tuple[float, float, float], a: float, front: float,
               mcol: dict | None = None) -> tuple[tuple[float, float, float] | None, float | None]:
    """목표 범위 띠(v4.4.0 D-0090 작업 2) — 달마다 [그 달 첫날, 다음 달 첫날) 계단. 위·아래 끝 선 + 반투명 칠.
    돌려주는 값 = 드러난 마지막 달 (x, 아래 y, 아래 값), 위 값 — 끝점 라벨용. 이 함수가 부르는 쪽의 clip 안에서 그린다."""
    B = TIMELINE.band  # noqa: N806
    rows = band_pairs(e)
    last: tuple[float, float, float] | None = None
    last_hi: float | None = None
    for seg in segments([(d, i) for i, (d, _, _) in enumerate(rows)]):   # 빈 달에서 끊는다(보간 금지)
        lo_pts: list[tuple[float, float]] = []
        hi_pts: list[tuple[float, float]] = []
        for d, i in seg:
            _, lo, hi = rows[int(i)]
            x0, x1 = stage.x_of(d), stage.x_of(_next_month(d))
            ylo, yhi = value_y(stage, e["lane"], rng, lo), value_y(stage, e["lane"], rng, hi)
            lo_pts += [(x0, ylo), (x1, ylo)]
            hi_pts += [(x0, yhi), (x1, yhi)]
            if x0 <= front:
                last, last_hi = (x0, ylo, lo), hi
            if mcol is not None:   # v4.4.0 D-0091 ② — 달마다 색(아래 끝 레코드의 변화)
                s0, t0 = view.to_screen(x0, yhi)
                s1, t1 = view.to_screen(x1, ylo)
                ctx.rectangle(s0, t0, s1 - s0, t1 - t0)
                ctx.set_source_rgba(*mcol[d], B.fill_alpha * a)
                ctx.fill()
                for yy in (yhi, ylo):
                    ctx.move_to(s0, view.to_screen(x0, yy)[1])
                    ctx.line_to(s1, view.to_screen(x1, yy)[1])
                ctx.set_source_rgba(*mcol[d], B.edge_alpha * a)
                ctx.set_line_width(B.edge_w)
                ctx.stroke()
        if mcol is not None:
            continue
        ctx.new_path()
        for i, (x, y) in enumerate(hi_pts + lo_pts[::-1]):
            sx, sy = view.to_screen(x, y)
            (ctx.move_to if i == 0 else ctx.line_to)(sx, sy)
        ctx.close_path()
        ctx.set_source_rgba(*col, B.fill_alpha * a)
        ctx.fill()
        for pts in (hi_pts, lo_pts):
            ctx.new_path()
            for i, (x, y) in enumerate(pts):
                sx, sy = view.to_screen(x, y)
                (ctx.move_to if i == 0 else ctx.line_to)(sx, sy)
            ctx.set_source_rgba(*col, B.edge_alpha * a)
            ctx.set_line_width(B.edge_w)
            ctx.stroke()
    return last, last_hi


def lane_name(ln: object) -> str:
    """레인 이름표 — 이름 + (단위). 무대(draw_labels)와 레이어가 같은 문자열을 쓴다."""
    return ln.label if not ln.unit else f"{ln.label} ({ln.unit})"  # type: ignore[attr-defined]


def _lane_name_box(ctx: cairo.Context, view: "View", stage: "TimelineStage", lane: str) -> tuple[float, float, float, float]:
    L = TIMELINE.lane_label  # noqa: N806
    i = stage.lane_index(lane)
    top, _ = stage.lane_screen(view, i)
    return (view.ox + L.x, top + L.dy - L.size, view.ox + L.x + tw(ctx, lane_name(stage.lanes[i]), L.size, L.font), top + L.dy + L.size / 2)


def _hits(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _next_month(d: date) -> date:
    return date(d.year + d.month // MONTHS, d.month % MONTHS + 1, 1)


def _draw_missing(ctx: cairo.Context, view: "View", stage: "TimelineStage", rec: object, e: dict, front: float, a: float,
                  right: float) -> None:
    """빈 달 자리 표시(D-0086 보정 1) — 짧은 점선 + "자료 없음". 일별 계열은 찍지 않는다(D-0319 ③ — 선만 끊고 출처 줄 한 줄, daily_missing_note)."""
    M = TIMELINE.missing_mark  # noqa: N806
    if rec.frequency == "daily":  # type: ignore[attr-defined]
        return
    lo_y, hi_y = stage.lane_y(e["lane"])
    for d in rec.missing_dates():  # type: ignore[attr-defined]
        x = stage.x_of(d) + (stage.x_of(_next_month(d)) - stage.x_of(d)) / 2
        if x > front:
            continue
        sx, top = view.to_screen(x, hi_y)
        _, bot = view.to_screen(x, lo_y)
        if not 0 <= sx <= right:
            continue
        ctx.set_dash(M.dash)
        ctx.move_to(sx, top + M.inset_px)
        ctx.line_to(sx, bot - M.inset_px)
        ctx.set_source_rgba(*C[M.color], M.alpha * a)
        ctx.set_line_width(M.line_w)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, M.label, sx, bot - M.inset_px + M.label_dy, M.label_size, M.label_font, C[M.color], M.alpha * a, M.label_halo, "c")


def _draw_axis(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, rng: tuple[float, float], unit: str, a: float,
               R: "RenderCtx | None" = None, t: float | None = None) -> None:
    """0 기준선과 범위 끝 값(단위 포함) — 레인 오른쪽 끝에 고정. 레인의 첫 series 만 그린다(겹침 방지)."""
    if not e["axis"]:
        return
    S = TIMELINE.series  # noqa: N806
    reg = (R.cache.get("series_end_labels") or {}) if R is not None else {}
    ends = [p[2] for p in (reg.get("lanes") or {}).get(e["lane"], [])] if reg.get("t") == t else []
    labeled = {v for v, _ in axis_label_items(ctx, view, stage, e["lane"], rng, unit, ends)}
    for v in axis_values(rng):   # v7.4.0 D-0263 — 끝 + 중간 눈금
        _, sy = view.to_screen(0.0, value_y(stage, e["lane"], rng, v))
        ctx.move_to(view.ox, sy)
        ctx.line_to(view.right, sy)
        zb = v == 0 and e.get("style") in ("bars", "stack", "diverging")   # v7.4.0 D-0309 §1-2·D-0310 — 막대·쌓임 레인 0 기준선은 또렷하게
        from engine.style import PALETTE  # noqa: PLC0415

        za = PALETTE.get("zero_alpha", TIMELINE.bars.zero_alpha)   # v7.4.0 D-0322 정정 — 팔레트 0 기준선·격자 알파(르포)
        ga = min(S.grid_alpha, PALETTE.get("grid_alpha", S.grid_alpha))
        ctx.set_source_rgba(*C["white"], (za if zb else S.zero_alpha if v == 0 else ga) * a)
        ctx.set_line_width(TIMELINE.bars.zero_w if zb else S.grid_w)
        ctx.stroke()
        if v in labeled:   # v7.4.0 D-0268 §2 — 라벨 간격이 axis_label_min_gap_px 미만인 중간 눈금은 선만
            text(ctx, fmt_value(v, unit), view.right - S.axis_label_margin_px, sy + S.axis_label_dy, S.axis_label_size, S.axis_label_font,
                 C["muted"], a, S.axis_label_halo, "r")


def plot_right(ctx: cairo.Context, view: "View", stage: "TimelineStage", lane: str, rng: tuple[float, float], unit: str) -> float:
    """자료를 그리는 영역의 오른쪽 끝(화면 x) — 그 오른쪽은 축 값 라벨 예약 열(v7.4.0 감독 지시: 선이 "3.5%" 를 가로질렀다).
    열 폭 = 가장 긴 눈금 라벨 + 양옆 axis_label_margin_px. 시간 축척(x_of)은 그대로 — 열 안의 선·띠·점만 잘린다(UF-138 w 고정)."""
    S = TIMELINE.series  # noqa: N806
    w = max((tw(ctx, fmt_value(v, unit), S.axis_label_size, S.axis_label_font) for v in axis_values(rng)), default=0.0)
    return view.right - w - 2 * S.axis_label_margin_px


def axis_label_items(ctx: cairo.Context, view: "View", stage: "TimelineStage", lane: str, rng: tuple[float, float], unit: str,
                     avoid: list | None = None) -> list[tuple[float, tuple[float, float, float, float]]]:
    """그린 축 눈금 라벨 (값, 글자 상자)(_draw_axis 와 같은 자리). avoid(끝값 라벨 상자)와 겹치는 눈금 라벨은 생략(눈금선만, v7.4.0)."""
    S = TIMELINE.series  # noqa: N806
    out = []
    for v in axis_label_values(view, stage, lane, rng):
        _, sy = view.to_screen(0.0, value_y(stage, lane, rng, v))
        x1 = view.right - S.axis_label_margin_px
        by = sy + S.axis_label_dy
        b = (x1 - tw(ctx, fmt_value(v, unit), S.axis_label_size, S.axis_label_font), by - S.axis_label_size, x1, by)
        if not any(_hits(b, z) for z in avoid or []):
            out.append((v, b))
    return out


def axis_label_boxes(ctx: cairo.Context, view: "View", stage: "TimelineStage", lane: str, rng: tuple[float, float],
                     unit: str, avoid: list | None = None) -> list[tuple[float, float, float, float]]:
    """그린 축 눈금 라벨 글자 상자 — 끝값 라벨 비키기·검사([series-label-overlap])가 같이 쓴다."""
    return [b for _, b in axis_label_items(ctx, view, stage, lane, rng, unit, avoid)]


def clear_axis_labels(ctx: cairo.Context, view: "View", stage: "TimelineStage", lane: str, rng: tuple[float, float], unit: str,
                      x0: float, lw: float, by: float) -> float:
    """끝값 라벨 기준선 by 를 축 눈금 라벨과 겹치지 않게 세로로 민다(v7.4.0 — 감독 지적 preview_v8: "3.63%" ↔ "3.5%").
    end_label_min_gap_px 씩, 겹친 눈금의 반대쪽으로. 레인 띠 밖으로는 밀지 않는다(그때는 검사가 잡는다)."""
    S = TIMELINE.series  # noqa: N806
    ticks = axis_label_boxes(ctx, view, stage, lane, rng, unit)
    top, bot = stage.lane_screen(view, stage.lane_index(lane))
    for _ in range(len(ticks) + 1):
        box = (x0, by - S.value_size, x0 + lw, by)
        hit = next((b for b in ticks if _hits(box, b)), None)
        if hit is None:
            return by
        nb = by - S.end_label_min_gap_px if (box[1] + box[3]) / 2 <= (hit[1] + hit[3]) / 2 else by + S.end_label_min_gap_px
        if nb - S.value_size < top or nb > bot:
            return by
        by = nb
    return by


def axis_label_values(view: "View", stage: "TimelineStage", lane: str, rng: tuple[float, float]) -> list[float]:
    """라벨을 다는 축 값(v7.4.0 back_and_forth D-0268 §2) — 위·아래 끝은 늘, 중간 눈금은 앞 라벨·위 끝 라벨과 화면 간격이
    rules stage_timeline.series.axis_label_min_gap_px 이상일 때만. 그리기와 검사([chart-edge-bleed])가 같이 쓴다."""
    gap = TIMELINE.series.axis_label_min_gap_px
    vals = axis_values(rng)
    ys = {v: view.to_screen(0.0, value_y(stage, lane, rng, v))[1] for v in vals}
    out = [vals[0]]
    for v in vals[1:-1]:
        if abs(ys[v] - ys[out[-1]]) >= gap and abs(ys[vals[-1]] - ys[v]) >= gap:
            out.append(v)
    return out + [vals[-1]]


def source_lines(ctx: cairo.Context, view: "View", s: str) -> list[str]:
    """레인 출처 줄을 폭(틀·상자 폭 − 왼쪽 여백 − 오른쪽 축 값 자리)에 맞춰 " · " 경계에서 접는다(v7.4.0 back_and_forth D-0265 §3).
    최대 rules island.source_wrap_lines_max 줄 — 마지막 줄은 남은 조각을 모두 담는다(넘치면 [chart-edge-bleed] 가 잡는다, 자르지 않는다)."""
    from engine.style import ISLAND  # noqa: PLC0415

    L, S = TIMELINE.lane_label, TIMELINE.series  # noqa: N806
    max_w = view.vw - L.x - S.axis_zone_px
    parts, lines = s.split(SOURCE_SEP), []
    for p in parts:
        if lines and len(lines) < ISLAND.source_wrap_lines_max and tw(ctx, lines[-1] + SOURCE_SEP + p, S.source_size, S.source_font) > max_w:
            lines.append(p)
        elif lines:
            lines[-1] += SOURCE_SEP + p
        else:
            lines.append(p)
    return lines


def source_line_boxes(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict) -> list[tuple[str, float, float]]:
    """(줄, 왼쪽 x, 기준선 y) — 아래 줄이 레인 아래 끝 − source_dy, 그 위 줄은 source_step 씩 위. 그리기와 검사가 같이 쓴다."""
    L, S = TIMELINE.lane_label, TIMELINE.series  # noqa: N806
    _, bot = stage.lane_screen(view, stage.lane_index(e["lane"]))
    lines = source_lines(ctx, view, lane_source_text(e))
    n = len(lines)
    return [(ln, view.ox + L.x, bot - S.source_dy - (n - 1 - k) * S.source_step) for k, ln in enumerate(lines)]


def _draw_source(ctx: cairo.Context, view: "View", stage: "TimelineStage", e: dict, a: float) -> None:
    """출처·기준 시점 줄(20 §5.1·§5.3) — 레인 아래쪽, 왼쪽 고정. v7.4.0 D-0256 — 레인당 한 줄(레인 첫 series 가 레인 전체 출처를 그린다),
    D-0265 — 폭을 넘으면 두 줄로 접는다."""
    if e["slot"]:
        return
    S = TIMELINE.series  # noqa: N806
    for ln, x, y in source_line_boxes(ctx, view, stage, e):
        text(ctx, ln, x, y, S.source_size, S.source_font, C["muted"], a, S.source_halo, "l")


__all__ = ["lane_source_text", "place_end_label", "band_pairs", "month_colors", "regimes", "draw_series", "fmt_value", "lane_range", "nice_step", "axis_values", "axis_range_note", "column_date", "record_points", "projection_dots", "source_lines", "source_line_boxes", "lane_source_join", "projection_tag_lines", "axis_label_values", "axis_label_boxes", "axis_label_items", "clear_axis_labels", "record_ids", "segments", "source_line", "value_text", "value_y"]
