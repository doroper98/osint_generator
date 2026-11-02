"""구성 무대(StructureStage) — 분야별 금액의 순위 가로 막대 (v7.4.0, back_and_forth D-1003 §3, D-1000 §B1).

형태는 하나: **순위 가로 막대**. 행 = 레코드(record)의 분야, 금액 큰 순(위 → 아래). 막대 = record 값, 막대 위 속빈 세로 눈금 =
견줄 레코드(prior) 값 — 같은 축척, 0 기준(정직성: 막대 길이 = 값 × 한 배율). 행 끝 직접 라벨 "금액 · ±증감률"(범례 없음).
데이터 층(막대·눈금·증감·초점)은 `rank` 이벤트(engine/layers/structure.py)가 문장마다 하나씩 그린다. 이 무대는 기하만 안다.

월드 좌표 = 전체 보기(카메라 w = 상자 폭)의 상자 px. 등방(View 기본) — 카메라가 행을 확대해도 막대 길이 비는 그대로(축척 불변).
- x = `x_of(value)` = 0 기준선 x + value × px_per_unit. 0 기준선 x = label_col + label_gap.
- y = 상자 높이 − 행 가운데 px(행 i 는 위에서 i 번째). bounds = (0, 0, 상자 폭, 상자 높이).
- 카메라 앵커: `row`(행 id — 그 행 가운데) · `value`(그 값의 x). 없으면 무대 가운데.
수치는 전부 `rules stage_structure`(코드 리터럴 0 — tests/anti_inertia/test_no_magic_numbers).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import cairo
from pydantic import BaseModel, ConfigDict, Field

from engine.style import ISLAND, STRUCTURE

if TYPE_CHECKING:
    from engine.assets import Assets
    from engine.projection import View
    from schemas.data_models import CategoricalRecord


class StructureError(ValueError):
    """구성 무대 구성·앵커 오류(15 P6)."""


class StructureConfig(BaseModel):
    """direction `stage_config.structure`. box = rules island.boxes 이름(구성 아일랜드 상자와 같아야 한다 — engine.project 검사)."""

    model_config = ConfigDict(extra="forbid")

    box: str = Field(min_length=1)
    record: str = Field(min_length=1)          # 막대 레코드(예: 2027 정부안)
    prior: Optional[str] = None                # 속빈 눈금 레코드(예: 2026 본예산) — 행 id 가 같아야 한다
    title: str = Field(min_length=1)           # 머리 짧은 이름(단위는 코드가 레코드에서 붙인다)


class Row(BaseModel):
    """배치된 행 하나(순위 순). published_pct = 원문 표 증감률(있으면 화면 라벨은 이 값 — 반올림 값으로 다시 계산하지 않는다, D-1006)."""

    id: str
    label: str
    rank: int
    value: float
    prior: Optional[float] = None
    published_pct: Optional[float] = None
    published_abs: Optional[float] = None   # D-1008 — 원문 표 증감액
    avg_pct: Optional[float] = None         # D-1009 — 예년(avg_growth) 연평균 증가율(코드 계산, 기준이 다른 행은 None)

    @property
    def delta_abs(self) -> Optional[float]:
        if self.published_abs is not None:
            return self.published_abs
        return None if self.prior is None else self.value - self.prior

    @property
    def delta_pct(self) -> Optional[float]:
        if self.published_pct is not None:
            return self.published_pct
        if self.prior is None or self.prior == 0:
            return None
        return (self.value - self.prior) / self.prior * 100

    @property
    def decreased(self) -> bool:
        return self.prior is not None and self.value < self.prior


def pct_bounds(a: float, b: float, step: float) -> tuple[float, float]:
    """반올림 값 a(전)·b(후) — 실제 값이 ±step/2 안에 있을 때 증감률(%)이 가질 수 있는 범위."""
    h = step / 2
    return ((b - h) / (a + h) - 1) * 100, ((b + h) / (a - h) - 1) * 100


class StructureStage:
    """구성 무대(20 §2.1 카탈로그 structure — D-1003 에서 순위 가로 막대 하나로 구현). 앵커 = row · value."""

    name = "structure"
    anchor_keys: tuple[str, ...] = ("row", "value")

    def __init__(self, assets: "Optional[Assets]" = None, *, out: object = None, config: Optional[dict] = None,
                 records: "Optional[dict[str, CategoricalRecord]]" = None) -> None:
        """records = 레코드 id → 레코드(시험용 주입). 없으면 data.categorical 로더."""
        if not config:
            raise StructureError("structure 무대는 stage_config.structure(box·record·title)가 필요하다")
        self.cfg = StructureConfig.model_validate(config)
        if self.cfg.box not in ISLAND.boxes:
            raise StructureError(f"stage_config.structure.box {self.cfg.box!r} 가 rules island.boxes {sorted(ISLAND.boxes)} 에 없다")
        self.assets = assets
        rec = self._load(self.cfg.record, records)
        pri = self._load(self.cfg.prior, records) if self.cfg.prior else None
        self.record, self.prior_record = rec, pri
        if pri is not None:
            if pri.unit != rec.unit:
                raise StructureError(f"prior 단위 {pri.unit!r} ≠ record 단위 {rec.unit!r} — 같은 축척이 아니다")
            a, b = {x.id for x in rec.rows}, {x.id for x in pri.rows}
            if a != b:
                raise StructureError(f"record·prior 행 id 가 다르다: record 만 {sorted(a - b)} · prior 만 {sorted(b - a)}")
        if rec.unit not in STRUCTURE.unit_suffix:
            raise StructureError(f"단위 {rec.unit!r} 의 화면 꼬리가 rules stage_structure.unit_suffix 에 없다")
        pv = {x.id: x.value for x in pri.rows} if pri is not None else {}
        bad = [x.id for x in rec.rows if x.value < 0] + [k for k, v in pv.items() if v < 0]
        if bad:
            raise StructureError(f"구성 무대는 0 기준 양수 막대만 — 음수 행 {bad}")
        if rec.change_vs is not None and (pri is None or rec.change_vs != pri.record_id):
            raise StructureError(f"record.change_vs {rec.change_vs!r} ≠ prior {self.cfg.prior!r} — 원문 증감률의 기준과 눈금 레코드가 다르다")
        step = STRUCTURE.value_step
        for x in rec.rows:   # 원문 증감률이 반올림 값과 모순이 없는지(P6) — 표의 미반올림 값으로 계산한 % 라 다를 수 있으나 범위 밖이면 오류
            if x.change_pct is not None:
                lo, hi = pct_bounds(pv[x.id], x.value, step)
                pr = STRUCTURE.pct_step / 2
                if not lo - pr <= x.change_pct <= hi + pr:
                    raise StructureError(f"행 {x.id}: 원문 증감률 {x.change_pct}% 가 {pv[x.id]}→{x.value} 반올림 범위 {lo:.2f}~{hi:.2f}% 밖")
            if x.change_abs is not None and abs(x.change_abs - (x.value - pv[x.id])) > step + step / 2:   # 반올림 값의 차 ± 반올림 단위
                raise StructureError(f"행 {x.id}: 원문 증감액 {x.change_abs} 가 {pv[x.id]}→{x.value} 차와 반올림 범위 밖")
        order = sorted(rec.rows, key=lambda x: (-x.value, x.id))
        ag = rec.avg_growth
        self.rows = [Row(id=x.id, label=x.label, rank=i, value=x.value, prior=pv.get(x.id), published_pct=x.change_pct, published_abs=x.change_abs,
                         avg_pct=(ag.pct(ag.rows[x.id]) if ag is not None and x.id in ag.rows else None))
                     for i, x in enumerate(order)]
        self.by_id = {r.id: r for r in self.rows}
        _, _, bw, bh = ISLAND.boxes[self.cfg.box]
        self.fit(bw, bh)

    @staticmethod
    def _load(rid: Optional[str], records: "Optional[dict[str, CategoricalRecord]]") -> "CategoricalRecord":
        assert rid is not None
        if records is not None:
            if rid not in records:
                raise StructureError(f"구성 레코드 {rid!r} 없음(주입 {sorted(records)})")
            return records[rid]
        from data.categorical import CategoricalError, load_categorical  # noqa: PLC0415

        try:
            return load_categorical(rid)
        except CategoricalError as ex:
            raise StructureError(str(ex)) from ex

    # ------------------------------------------------------------------ 기하
    def fit(self, bw: float, bh: float) -> None:
        """상자 크기 → 행 높이·배율. 가장 긴 값(record·prior 중)이 value_col 앞에서 끝난다."""
        S = STRUCTURE  # noqa: N806
        self.bw, self.bh = float(bw), float(bh)
        n = len(self.rows)
        self.row_h = min(S.row_h_max, (self.bh - S.pad_top - S.pad_bottom) / n)
        if self.row_h <= 0:
            raise StructureError(f"상자 {bw}×{bh} 에 행 {n} 개가 들어가지 않는다")
        self.zero_x = S.label_col + S.label_gap
        vmax = max([r.value for r in self.rows] + [r.prior for r in self.rows if r.prior is not None])
        span = self.bw - self.zero_x - S.value_col
        if span <= 0 or vmax <= 0:
            raise StructureError(f"막대 자리 없음(폭 {span:g}) 또는 최댓값 {vmax:g} ≤ 0")
        self.px_per_unit = span / vmax
        self.bar_h = self.row_h * S.bar_h_ratio

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (0.0, 0.0, self.bw, self.bh)

    @property
    def fixed_w(self) -> float:
        """전체 보기 카메라 폭(월드 = 상자 px)."""
        return self.bw

    def x_of(self, v: float) -> float:
        """값 → 월드 x(0 기준선에서 값에 비례 — 정직성)."""
        return self.zero_x + v * self.px_per_unit

    def row_top(self, i: int) -> float:
        """행 i 위 끝(상자 px, 위에서부터)."""
        return STRUCTURE.pad_top + i * self.row_h

    def row_y(self, i: int) -> float:
        """행 i 가운데의 월드 y."""
        return self.bh - (self.row_top(i) + self.row_h / 2)

    def to_world(self, **anchor: Any) -> tuple[float, float]:
        bad = set(anchor) - set(self.anchor_keys)
        if bad:
            raise StructureError(f"구성 무대 앵커는 row·value — {sorted(bad)} 금지(P10)")
        row, value = anchor.get("row"), anchor.get("value")
        if row is not None and row not in self.by_id:
            raise StructureError(f"row {row!r} 가 레코드 {self.cfg.record} 행 {sorted(self.by_id)} 에 없다")
        x = self.x_of(float(value)) if value is not None else self.bw / 2
        y = self.row_y(self.by_id[row].rank) if row is not None else self.bh / 2
        return x, y

    def from_world(self, x: float, y: float) -> dict[str, Any]:
        i = int((self.bh - y - STRUCTURE.pad_top) // self.row_h)
        out: dict[str, Any] = {"value": round((x - self.zero_x) / self.px_per_unit, 3)}
        if 0 <= i < len(self.rows):
            out["row"] = self.rows[i].id
        return out

    def render_base(self, ctx: cairo.Context, view: "View") -> None:
        """바탕 없음 — 구성 무대는 아일랜드 상자 안 뷰포트(무대 표면이면 사진 배경 위 바로, D-0328 §3). 0 기준선은 막대 층이 그린다."""

    def draw_labels(self, ctx: cairo.Context, view: "View", reserved: list, alpha: float = 1.0) -> None:
        """라벨은 rank 층(행 이름·금액은 막대와 함께 등장 — 문장마다 층)."""

    def lod_rules(self) -> dict[str, Any]:
        return {}

    def avg_span(self) -> str:
        """예년 비교 해 범위 "2018~26"(레코드 avg_growth)."""
        ag = self.record.avg_growth
        if ag is None:
            raise StructureError("레코드에 avg_growth(예년 비교)가 없다")
        return f"{ag.start_year}~{ag.end_year % 100:02d}"

    def total_info(self) -> tuple[float, float, Optional[float]]:
        """(총지출, 견줄 레코드 대비 증가율 %, 예년 연평균 %) — 표의 합계 줄(total)에서. 없으면 오류(P6)."""
        if self.record.total is None or self.prior_record is None or self.prior_record.total is None:
            raise StructureError("total 층은 record·prior 의 표 합계(total)가 필요하다")
        ag = self.record.avg_growth
        pct = (self.record.total / self.prior_record.total - 1) * 100
        return self.record.total, pct, (ag.pct(ag.total) if ag is not None and ag.total is not None else None)

    def stage_word(self, rec: "CategoricalRecord") -> str:
        return f"{rec.fiscal_year} {STRUCTURE.stage_words[rec.budget_stage]}"


__all__ = ["Row", "StructureConfig", "StructureError", "StructureStage"]
