"""구성 무대(structure)·순위 가로 막대 층(rank) 시험 (v7.4.0, back_and_forth D-1003 §3).

- 레지스트리 세 곳(무대·이벤트·island 종류)은 tests/anti_inertia/test_registry_complete·tests/test_stage_direction 이 본다.
- 여기서는: 정직성(막대 길이 = 값 비례, 0 기준), 픽셀 픽스처(막대 속 = 칠, 테두리 없음, 눈금 = 속빈 윤곽, 초점 = accent),
  글자 겹침 0, 레코드 계약(정부안/확정 구분·원본 지문·합계), 배선 점검(check_structure).
시험 레코드 값은 실데이터가 아니다(픽스처 — 화면에 내지 않는다).
"""

from __future__ import annotations

import unittest
from datetime import date

import cairo
import yaml

from engine.projection import View
from engine.stage_structure import StructureError, StructureStage
from engine.style import C, ISLAND, STRUCTURE, apply_palette
from schemas.data_models import CategoricalRecord
from tests.anti_inertia._ast_util import REPO

LABELS = [("welfare", "보건·복지·고용"), ("admin", "일반·지방행정"), ("education", "교육"), ("defense", "국방"),
          ("industry", "산업·중소기업·에너지"), ("soc", "SOC"), ("rnd", "R&D"), ("agri", "농림·수산·식품"),
          ("environment", "환경"), ("safety", "공공질서·안전"), ("culture", "문화·체육·관광"), ("diplomacy", "외교·통일")]
NOW = [200.0, 120.0, 95.0, 60.0, 40.0, 30.0, 32.0, 25.0, 15.0, 10.0, 9.0, 7.0]
PRIOR = [185.0, 100.0, 100.0, 57.0, 31.0, 28.0, 30.0, 24.0, 15.5, 9.5, 8.0, 6.5]


def record(rid: str, values: list[float], stage: str, year: int, **kw: object) -> CategoricalRecord:
    raw = {"record_id": rid, "source": "시험 픽스처 문서", "source_file": {"path": "fixture.pdf", "sha1": "0" * 40, "title": "시험",
                                                                     "publisher": "시험 기관", "published_on": "2026-09-01"},
           "retrieved_at": "2026-11-02", "transform": {"op": "document", "formula": ""}, "as_of": "2026-09", "unit": "조 원",
           "license": "kogl_1", "license_note": "시험", "budget_stage": stage, "fiscal_year": year,
           "rows": [{"id": i, "label": lb, "value": v, "page": 3, "locator": f"표 1 · {lb}"} for (i, lb), v in zip(LABELS, values)]}
    from rules import load_rules  # noqa: PLC0415

    raw["transform"]["formula"] = load_rules().data.transforms["document"]  # type: ignore[index]
    raw.update(kw)
    return CategoricalRecord.model_validate(raw)


def stage(**cfg: object) -> StructureStage:
    recs = {"NOW": record("NOW", NOW, "proposed", 2027), "PRIOR": record("PRIOR", PRIOR, "enacted", 2026)}
    c = {"box": "center_tall", "record": "NOW", "prior": "PRIOR", "title": "분야별 총지출", **cfg}
    return StructureStage(config=c, records=recs)


class _R:
    def __init__(self, events: list[dict], st: StructureStage) -> None:
        self.cache = {"island_structure": {"stage": st, "events": events}}


def events(t_focus: float = 3.0) -> list[dict]:
    return [{"type": "rank", "t0": 0.0, "t1": 20.0, "layer": "bars"},
            {"type": "rank", "t0": 1.0, "t1": 20.0, "layer": "prior"},
            {"type": "rank", "t0": 2.0, "t1": 20.0, "layer": "delta"},
            {"type": "rank", "t0": t_focus, "t1": 20.0, "layer": "focus", "row": "industry", "metric": "rate"}]


def render(st: StructureStage, t: float, evs: list[dict], cam: tuple[float, float, float] | None = None) -> cairo.ImageSurface:
    from engine.layers.structure import draw_structure  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(st.bw), int(st.bh))
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    x, y = st.to_world()
    v = View(st, np.array(cam or (x, y, st.fixed_w)), viewport=(st.bw, st.bh))
    draw_structure(ctx, _R(evs, st), v, t, evs)  # type: ignore[arg-type]
    surf.flush()
    return surf


def px(surf: cairo.ImageSurface, x: float, y: float) -> tuple[int, int, int]:
    d = surf.get_data()
    o = int(y) * surf.get_stride() + int(x) * 4
    return d[o + 2], d[o + 1], d[o]


class StructureStageTest(unittest.TestCase):
    def setUp(self) -> None:
        apply_palette("noturno")

    def tearDown(self) -> None:
        apply_palette(None)

    def test_rank_order_and_anchor(self) -> None:
        st = stage()
        self.assertEqual([r.id for r in st.rows][:3], ["welfare", "admin", "education"])
        self.assertEqual(st.by_id["rnd"].rank, 5)   # 32 > 30(SOC) — 금액 순
        x, y = st.to_world(row="welfare")
        self.assertAlmostEqual(y, st.row_y(0))
        with self.assertRaises(StructureError):
            st.to_world(row="nope")
        with self.assertRaises(StructureError):
            st.to_world(lon=1.0)

    def test_bar_length_proportional_zero_based(self) -> None:
        """정직성 — 막대 길이 / 값 = 한 배율(0 기준), 확대해도 비는 그대로."""
        import numpy as np  # noqa: PLC0415

        from engine.layers.structure import bar_rect  # noqa: PLC0415

        st = stage()
        for cam in [None, (st.x_of(40), st.row_y(4), st.bw / 2)]:
            x, y = st.to_world()
            v = View(st, np.array(cam or (x, y, st.fixed_w)), viewport=(st.bw, st.bh))
            ratios = []
            for r in st.rows:
                x0, _, x1, _ = bar_rect(st, v, r)
                self.assertAlmostEqual(x0, v.to_screen(st.x_of(0.0), 0)[0])
                ratios.append((x1 - x0) / r.value)
            self.assertLess(max(ratios) - min(ratios), 1e-9)

    def test_longest_fits_with_value_column(self) -> None:
        st = stage()
        self.assertAlmostEqual(st.x_of(max(NOW + PRIOR)), st.bw - STRUCTURE.value_col)
        self.assertLessEqual(STRUCTURE.pad_top + st.row_h * len(st.rows), st.bh - STRUCTURE.pad_bottom + 1e-9)

    def test_pixels(self) -> None:
        """픽셀 픽스처 — 막대 속은 칠(테두리 없음: 가장자리 안쪽과 가운데가 같은 색), 행 사이 틈은 바탕, 초점 행은 accent,
        감소 행(교육)은 손실 면, 눈금은 속빈 윤곽(가운데가 막대 칠 그대로)."""
        from engine.layers.series import loss_rgb  # noqa: PLC0415

        st = stage()
        surf = render(st, 10.0, events())
        r = st.by_id["welfare"]
        cy = st.bh - st.row_y(r.rank)
        x_mid = (st.x_of(0) + st.x_of(r.prior or 0)) / 2
        mid = px(surf, x_mid, cy)
        edge = px(surf, x_mid, cy - st.bar_h / 2 + 2)
        self.assertEqual(mid, edge, "막대 안쪽 가장자리와 가운데 색이 다르다 — 테두리")
        self.assertGreater(sum(mid), 3 * 40, "막대가 칠해지지 않았다")
        gap = px(surf, x_mid, STRUCTURE.pad_top + st.row_h * (r.rank + 1))   # 행 경계 = 막대 사이 틈
        self.assertEqual(gap, (0, 0, 0))
        f = st.by_id["industry"]   # 초점 행(D-1008): 늘어난 구간(눈금 → 막대 끝) = accent 솔리드, 0 → 눈금 = accent 옅게
        gold = tuple(round(c * 255) for c in C["gold"])
        fc = px(surf, (st.x_of(f.prior or 0) + st.x_of(f.value)) / 2 + 2, st.bh - st.row_y(f.rank))
        self.assertTrue(all(abs(a - b) <= 2 for a, b in zip(fc, gold)), f"초점 행 늘어난 구간 {fc} ≠ accent {gold}")
        fb = px(surf, st.x_of((f.prior or 0) / 2), st.bh - st.row_y(f.rank))
        self.assertTrue(fb != gold and fb[0] > fb[2], f"초점 행 0 → 눈금 구간 {fb} 는 accent 옅게")
        d = st.by_id["education"]   # 95 < 100 — 감소: 막대 끝 → 눈금 구간 = 손실 A 면(D-1008 §1-3)
        loss = tuple(round(c * 255) for c in loss_rgb())
        pre = render(st, 10.0, events(t_focus=30.0))   # 초점 층 전
        dc = px(pre, (st.x_of(d.value) + st.x_of(d.prior or 0)) / 2, st.bh - st.row_y(d.rank))
        self.assertTrue(sum(abs(a - b) for a, b in zip(dc, loss)) <= 6, f"감소 구간 {dc} ≠ 손실 면 {loss}")
        w = st.by_id["admin"]   # 120 > 100 — 늘어난 구간은 0 → 눈금 구간보다 밝다(같은 막대 위 한 단계 밝게)
        lo = px(pre, st.x_of((w.prior or 0) / 2), st.bh - st.row_y(w.rank))
        hi = px(pre, (st.x_of(w.prior or 0) + st.x_of(w.value)) / 2 + 2, st.bh - st.row_y(w.rank))
        self.assertGreater(sum(hi), sum(lo) + 3 * 20, f"늘어난 구간 {hi} 가 앞 구간 {lo} 보다 밝아야")
        early = render(st, 1.8, events())   # prior 층만(delta 전) — 눈금 가운데(속빈) = 막대 칠
        self.assertEqual(px(early, st.x_of(r.prior or 0), cy), px(early, x_mid, cy))

    def test_text_no_overlap(self) -> None:
        """겹침 0 — 모든 층이 뜬 프레임의 글자 상자(이름·금액·증감·머리·태그·출처)끼리 교차 없음, 상자 안."""
        from engine.layers.structure import DRAWN_TEXT, text_overlaps  # noqa: PLC0415

        st = stage()
        render(st, 10.0, events())
        names = [n for n, _ in DRAWN_TEXT]
        self.assertIn("head", names)
        self.assertIn("tag:prior", names)
        self.assertEqual(sum(n.startswith("delta:") for n in names), len(st.rows) - 1)   # 초점 행은 초점 라벨이 대신(D-1008)
        self.assertIn("focus:industry", names)
        self.assertNotIn("value:industry", names)
        self.assertEqual(text_overlaps(list(DRAWN_TEXT)), [])
        for n, (x0, y0, x1, y1) in DRAWN_TEXT:
            self.assertTrue(x0 >= -0.5 and y0 >= -0.5 and x1 <= st.bw + 0.5 and y1 <= st.bh + 0.5, f"{n} 상자 밖 {x0, y0, x1, y1}")

    def test_focus_label_says_spoken_number(self) -> None:
        """D-1008 §1 — metric amount 초점 = "+증감액" 크게 + " · +증감률" 작게, rate 초점 = 거꾸로."""
        from engine.layers.structure import focus_label  # noqa: PLC0415

        st = stage()
        self.assertEqual(focus_label(st, st.by_id["admin"], "amount"), ("+20.0조", " · +20.0%"))
        self.assertEqual(focus_label(st, st.by_id["industry"], "rate"), ("+29.0%", " · +9.0조"))

    def test_layers_appear_in_order(self) -> None:
        from engine.layers.structure import DRAWN_TEXT  # noqa: PLC0415

        st = stage()
        render(st, 0.55, events())
        self.assertFalse(any(n.startswith("delta:") or n == "tag:prior" for n, _ in DRAWN_TEXT))
        render(st, 1.8, events())
        names = [n for n, _ in DRAWN_TEXT]
        self.assertIn("tag:prior", names)
        self.assertFalse(any(n.startswith("delta:") for n in names))

    def test_config_errors(self) -> None:
        with self.assertRaises(StructureError):
            stage(box="nope")
        with self.assertRaises(StructureError):
            StructureStage(config=None)
        recs = {"NOW": record("NOW", NOW, "proposed", 2027), "P2": record("P2", PRIOR[:-1], "enacted", 2026,
                                                                           rows=[{"id": i, "label": lb, "value": v, "page": 1, "locator": "x"}
                                                                                 for (i, lb), v in zip(LABELS[:-1], PRIOR)])}
        with self.assertRaisesRegex(StructureError, "행 id 가 다르다"):
            StructureStage(config={"box": "center_tall", "record": "NOW", "prior": "P2", "title": "t"}, records=recs)


class CategoricalRecordTest(unittest.TestCase):
    def test_budget_stage_required(self) -> None:
        with self.assertRaises(ValueError):
            record("X", NOW, "draft", 2027)

    def test_total_mismatch_needs_note(self) -> None:
        with self.assertRaisesRegex(ValueError, "total_note"):
            record("X", NOW, "proposed", 2027, total=1.0)
        r = record("X", NOW, "proposed", 2027, total=1.0, total_note="분야 간 중복 계상")
        self.assertEqual(r.total, 1.0)

    def test_sha1_and_dup_rows(self) -> None:
        with self.assertRaises(ValueError):
            record("X", NOW, "proposed", 2027, source_file={"path": "a.pdf", "sha1": "abc", "title": "t", "publisher": "p",
                                                             "published_on": "2026-09-01"})
        with self.assertRaisesRegex(ValueError, "중복"):
            record("X", NOW[:2], "proposed", 2027, rows=[{"id": "a", "label": "a", "value": 1, "page": 1, "locator": "x"},
                                                       {"id": "a", "label": "b", "value": 2, "page": 1, "locator": "x"}])

    def test_retrieved_after_published(self) -> None:
        with self.assertRaises(ValueError):
            record("X", NOW, "proposed", 2027, retrieved_at=date(2026, 8, 1).isoformat())


class StructureWiringTest(unittest.TestCase):
    def test_check_structure(self) -> None:
        from engine.project import check_structure  # noqa: PLC0415

        st = stage()
        isl = {"type": "island", "kind": "structure", "box": "center_tall", "t0": 1.0, "t1": 10.0}
        ok = [isl, {"type": "rank", "layer": "bars", "t0": 1.2, "t1": 10.0}]
        self.assertEqual(check_structure(ok, "backdrop", st), [])
        bad = [isl, {"type": "rank", "layer": "bars", "t0": 0.2, "t1": 12.0}, {"type": "rank", "layer": "focus", "row": "zz", "t0": 2, "t1": 3}]
        errs = check_structure(bad, "backdrop", st)
        self.assertEqual(len(errs), 2)
        self.assertTrue(check_structure([isl], "backdrop", None))
        self.assertTrue(check_structure([{**isl, "box": "center"}, ok[1]], "backdrop", st))

    def test_preview_direction(self) -> None:
        from engine.direction import Direction, is_island_shot  # noqa: PLC0415

        raw = yaml.safe_load((REPO / "tests" / "fixtures" / "preview" / "stage_structure.yaml").read_text(encoding="utf-8"))["direction"]
        doc = Direction.model_validate(raw)
        self.assertEqual([is_island_shot(doc, s, doc.main_stage(), "structure") for s in doc.shots], [False, True, True])
        self.assertEqual([is_island_shot(doc, s, doc.main_stage(), "timeline") for s in doc.shots], [False, False, False])
        self.assertIn("center_tall", ISLAND.boxes)


if __name__ == "__main__":
    unittest.main()


class PublishedPctTest(unittest.TestCase):
    """v7.4.0 D-1006 — 화면 증감률 = 원문 표 값(반올림 값으로 다시 계산하지 않는다), 반올림 범위 밖이면 오류."""

    def _recs(self, pct: float) -> dict:
        now = record("NOW", NOW, "proposed", 2027, change_vs="PRIOR",
                     rows=[{"id": i, "label": lb, "value": v, "page": 3, "locator": "x",
                            "change_pct": (pct if i == "welfare" else round((v - p) / p * 100, 1))}
                           for (i, lb), v, p in zip(LABELS, NOW, PRIOR)])
        return {"NOW": now, "PRIOR": record("PRIOR", PRIOR, "enacted", 2026)}

    def test_published_used(self) -> None:
        st = StructureStage(config={"box": "center_tall", "record": "NOW", "prior": "PRIOR", "title": "t"}, records=self._recs(8.1))
        self.assertEqual(st.by_id["welfare"].delta_pct, 8.1)

    def test_out_of_rounding_bounds(self) -> None:
        with self.assertRaisesRegex(StructureError, "반올림 범위"):
            StructureStage(config={"box": "center_tall", "record": "NOW", "prior": "PRIOR", "title": "t"}, records=self._recs(9.5))

    def test_change_vs_all_rows(self) -> None:
        with self.assertRaisesRegex(ValueError, "change_pct"):
            record("NOW", NOW, "proposed", 2027, change_vs="PRIOR")

    def test_real_records(self) -> None:
        """p.15 실레코드 — 12행, 새 기준 주석, 원문 증감률이 반올림 범위 안(원본이 있으면 sha1 대조)."""
        st = StructureStage(config={"box": "center_tall", "record": "BUDGET_2027_PROPOSED_SECTORS",
                                    "prior": "BUDGET_2026_ENACTED_SECTORS", "title": "분야별 총지출"})
        self.assertEqual(len(st.rows), 12)
        self.assertEqual(st.rows[0].id, "welfare")
        self.assertEqual(st.by_id["culture"].delta_pct, 20.4)   # 반올림 값 계산은 20.8 — 원문 값
        self.assertIn("군인연금기금", st.record.note or "")
        self.assertEqual((st.record.budget_stage, st.prior_record.budget_stage), ("proposed", "enacted"))


class RowsBandTest(unittest.TestCase):
    """D-1006 — 확대해도 행이 머리 줄·출처 줄 띠로 넘어가지 않는다(행 띠 클립)."""

    def test_zoomed_rows_clipped(self) -> None:
        import numpy as np  # noqa: PLC0415

        from engine.layers.structure import DRAWN_TEXT, rows_band  # noqa: PLC0415

        apply_palette("noturno")
        try:
            st = stage()
            cam = (st.x_of(60), st.row_y(len(st.rows) - 1), st.bw / 2)   # 마지막 행 쪽으로 2배
            surf = render(st, 10.0, events(), cam=cam)
            v = View(st, np.array(cam), viewport=(st.bw, st.bh))
            _, top, _, bot = rows_band(v)
            src = dict(DRAWN_TEXT)["source"]
            self.assertGreaterEqual(src[1], bot - 1e-6)
            self.assertLessEqual(dict(DRAWN_TEXT)["head"][3], top + 1e-6)
            for y in range(int(bot) + 1, int(st.bh)):   # 출처 줄 오른쪽(글자 없는 곳) 띠 아래 = 바탕
                self.assertEqual(px(surf, st.bw - 3, y), (0, 0, 0), f"y={y}")
        finally:
            apply_palette(None)


class AvgAndTotalTest(unittest.TestCase):
    """D-1009 — 예년 비교(avg_growth, cagr 코드 계산)·총지출 줄·늘어난 구간 휘도 차."""

    def test_long_bar_focus_label_stays_inside(self) -> None:
        """감독 D616 — 막대가 가장 긴 행(보건·복지·고용)의 초점 줄이 오른쪽 끝에서 잘리던 컷(act2_14) 재현: 막대 안쪽으로 옮겨 상자 안.
        화면 밖 글자는 offscreen_text 가 잡는다(검사 [structure-text-offscreen]·[spoken-number-visible] 이 쓴다)."""
        from engine.layers.structure import DRAWN_STRINGS, DRAWN_TEXT, LAST_VIEW, offscreen_text  # noqa: PLC0415

        st = StructureStage(config={"box": "center_tall", "record": "BUDGET_2027_PROPOSED_SECTORS",
                                    "prior": "BUDGET_2026_ENACTED_SECTORS", "title": "분야별 총지출"})
        evs = events(t_focus=30.0)[:3] + [{"type": "rank", "t0": 3.0, "t1": 20.0, "layer": "focus", "row": "welfare", "metric": "rate",
                                            "note": "주택 융자 −5조 · 건설임대 +4조 7천억"}]
        render(st, 10.0, evs)
        self.assertEqual(offscreen_text(*LAST_VIEW), [])
        self.assertIn("주택 융자 −5조 · 건설임대 +4조 7천억 ", [s for _n, s, _a in DRAWN_STRINGS])
        DRAWN_TEXT.append(("focus_rest:x", (700.0, 10.0, 760.0, 20.0)))   # 잘린 글자 = 잡힌다
        self.assertEqual([n for n, _ in offscreen_text(*LAST_VIEW)], ["focus_rest:x"])

    def test_focus_note_replaces_small_line(self) -> None:
        """감독 지시(02:06Z) — focus note: 작은 줄 = 문장이 말한 분야 안 사업 숫자. compare 와 함께·focus 밖이면 오류."""
        from engine.events import RankEvent  # noqa: PLC0415
        from engine.layers.structure import focus_label  # noqa: PLC0415

        st = StructureStage(config={"box": "center_tall", "record": "BUDGET_2027_PROPOSED_SECTORS",
                                    "prior": "BUDGET_2026_ENACTED_SECTORS", "title": "t"})
        self.assertEqual(focus_label(st, st.by_id["soc"], "rate", None, "고속도로 1조 239억 → 8,189억")[1], " · 고속도로 1조 239억 → 8,189억")
        base = {"type": "rank", "t0": 0.0, "t1": 1.0, "layer": "focus", "row": "soc", "metric": "rate"}
        RankEvent.model_validate({**base, "note": "x"})
        with self.assertRaises(ValueError):
            RankEvent.model_validate({**base, "note": "x", "compare": "avg"})
        with self.assertRaises(ValueError):
            RankEvent.model_validate({"type": "rank", "t0": 0.0, "t1": 1.0, "layer": "bars", "note": "x"})

    def test_total_focus_grows_then_returns(self) -> None:
        """감독 판정 ②(R-0610) — focus row total: 문장 동안 +12.8% 가 focus_value_size, 연평균이 focus_rest_size, 금액은 head_size.
        문장이 끝나면 head_size 로 돌아간다. 행 초점과 겹침 0."""
        from engine.layers.structure import DRAWN_TEXT, text_overlaps  # noqa: PLC0415

        S = STRUCTURE  # noqa: N806
        st = StructureStage(config={"box": "center_tall", "record": "BUDGET_2027_PROPOSED_SECTORS",
                                    "prior": "BUDGET_2026_ENACTED_SECTORS", "title": "분야별 총지출"})
        evs = events(t_focus=30.0)[:3] + [{"type": "rank", "t0": 0.0, "t1": 20.0, "layer": "total"},
                                          {"type": "rank", "t0": 3.0, "t1": 8.0, "layer": "focus", "row": "total", "metric": "rate"}]

        def h(name: str) -> float:
            r = dict(DRAWN_TEXT)[name]
            return r[3] - r[1]

        render(st, 6.0, evs)
        on = (h("total:0"), h("total:1"))
        self.assertEqual(text_overlaps(list(DRAWN_TEXT)), [])
        render(st, 15.0, evs)
        off = (h("total:0"), h("total:1"))
        self.assertAlmostEqual(on[0], off[0], places=3)                      # 금액 그대로
        self.assertGreater(on[1] / off[1], S.focus_value_size / S.head_size * 0.9)   # +12.8% 커짐 → 돌아옴
        with self.assertRaisesRegex(ValueError, "metric rate"):
            render(st, 6.0, evs[:4] + [{**evs[4], "metric": "amount"}])

    def test_real_avg_labels(self) -> None:
        from engine.layers.structure import focus_label  # noqa: PLC0415

        st = StructureStage(config={"box": "center_tall", "record": "BUDGET_2027_PROPOSED_SECTORS",
                                    "prior": "BUDGET_2026_ENACTED_SECTORS", "title": "t"})
        self.assertEqual(focus_label(st, st.by_id["industry"], "rate", "avg"), ("+29.7%", " · 2018~26 연평균 +8.7%"))
        self.assertEqual(focus_label(st, st.by_id["environment"], "rate", "avg"), ("+5.2%", " · 2018~26 연평균 +9.1%"))
        self.assertEqual(focus_label(st, st.by_id["diplomacy"], "rate", "avg"), ("+1.1%", " · 2018~26 연평균 +5.1%"))
        with self.assertRaisesRegex(ValueError, "기준이 다른 행"):
            focus_label(st, st.by_id["welfare"], "rate", "avg")   # p.15 새 기준 ≠ p.16 종전 기준
        tot, pct, avg = st.total_info()
        self.assertEqual((tot, round(pct, 1), round(avg, 1)), (820.9, 12.8, 6.8))

    def test_total_line_no_overlap_and_contrast(self) -> None:
        """총지출 줄이 머리·태그와 겹치지 않고, 늘어난 구간이 기본 구간보다 휘도 60 단계 이상 밝다(noturno, 초점 행 아닌 행)."""
        import numpy as np  # noqa: PLC0415

        from engine.layers.structure import DRAWN_TEXT, draw_structure, text_overlaps  # noqa: PLC0415

        apply_palette("noturno")
        try:
            st = StructureStage(config={"box": "center_tall", "record": "BUDGET_2027_PROPOSED_SECTORS",
                                        "prior": "BUDGET_2026_ENACTED_SECTORS", "title": "분야별 총지출"})
            evs = events(t_focus=3.0) + [{"type": "rank", "t0": 0.0, "t1": 20.0, "layer": "total"}]
            evs[3] = {**evs[3], "row": "admin", "metric": "amount"}
            from engine.style import PALETTE  # noqa: PLC0415

            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(st.bw), int(st.bh))
            ctx = cairo.Context(surf)
            ctx.set_source_rgb(*PALETTE["bg"])
            ctx.paint()
            x, y = st.to_world()
            draw_structure(ctx, _R(evs, st), View(st, np.array((x, y, st.fixed_w)), viewport=(st.bw, st.bh)), 10.0, evs)
            surf.flush()
            names = [n for n, _ in DRAWN_TEXT]
            self.assertIn("total:2", names)
            self.assertEqual(text_overlaps(list(DRAWN_TEXT)), [])
            lum = lambda p: 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]  # noqa: E731
            for rid in ("welfare", "education", "rnd"):
                r = st.by_id[rid]
                yy = st.bh - st.row_y(r.rank)
                base = px(surf, st.x_of((r.prior or 0) / 2), yy)
                inc = px(surf, (st.x_of(r.prior or 0) + st.x_of(r.value)) / 2 + 1, yy)
                self.assertGreaterEqual(lum(inc) - lum(base), 60, f"{rid} {base} → {inc}")
        finally:
            apply_palette(None)
