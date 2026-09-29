"""series band(목표 범위 띠)·scatter 레코드(점도표)·month_last 변환 (v4.4.0, back_and_forth D-0090 작업 2·8, docs/handoff/20 §5.1·§5.2)."""

from __future__ import annotations

import copy
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml
from pydantic import ValidationError

from data.series import SeriesError, apply_transform, load_series, load_series_file, sep_dots
from engine.layers.series import band_pairs, lane_range, record_ids, source_line, value_text
from engine.project import ProjectError
from engine.registry import RegistryError, validate_events
from schemas.data_models import SeriesRecord
from tests.test_series_layer import FED, draw, near, setup

BAND = {"type": "series", "t0": 0.0, "t1": 20.0, "lane": "policy_rate", "series_id": "DFEDTARL", "upper_id": "DFEDTARU",
        "style": "band", "grow": False, "col": "amber"}


class MonthLastTest(unittest.TestCase):
    def test_last_observation_of_month(self) -> None:
        raw = [(date(2024, 1, 2), 5.5), (date(2024, 1, 31), 5.25), (date(2024, 2, 1), None), (date(2024, 2, 15), 5.0),
               (date(2024, 3, 3), None)]
        vals, miss = apply_transform("month_last", raw, date(2024, 1, 1))
        self.assertEqual(vals, [(date(2024, 1, 1), 5.25), (date(2024, 2, 1), 5.0)])
        self.assertEqual(miss, [date(2024, 3, 1)])   # 관측 없는 달 = 빈 날짜(채우지 않는다)

    def test_committed_target_range(self) -> None:
        lo, hi = load_series("DFEDTARL"), load_series("DFEDTARU")
        self.assertEqual(lo.transform.op, "month_last")
        self.assertEqual([d for d, _ in lo.values], [d for d, _ in hi.values])
        self.assertTrue(all(b - a == 0.25 for (_, a), (_, b) in zip(lo.values, hi.values)))   # 목표 범위 폭 0.25%p


class BandEventTest(unittest.TestCase):
    def test_upper_id_rules(self) -> None:
        validate_events([BAND])
        for bad in ({**BAND, "upper_id": None}, {**FED, "upper_id": "DFEDTARU"}, {**BAND, "upper_id": "DFEDTARL"}):
            with self.subTest(bad=bad), self.assertRaises((RegistryError, ValidationError, ValueError)):
                validate_events([bad])

    def test_record_ids_and_range(self) -> None:
        ev = validate_events([BAND])
        self.assertEqual(record_ids(ev[0]), ["DFEDTARL", "DFEDTARU"])
        lo, hi = lane_range(ev, "policy_rate")
        self.assertEqual(lo, 0.0)
        self.assertEqual(hi, max(v for _, v in load_series("DFEDTARU").values))

    def test_value_text_and_source(self) -> None:
        ev = validate_events([BAND])[0]
        self.assertEqual(value_text(ev, 3.75, "%", 4.0), "3.75–4%")
        self.assertEqual(source_line(ev).count("기준"), 1)   # 같은 출처·기준 시점은 한 번만

    def test_band_renders_fill(self) -> None:
        st, ev, R, cams = setup([BAND])
        _, img, drawn = draw(st, ev, R, cams[0], 10.0)
        self.assertGreater(near(img, "amber", 120).sum(), 500)
        self.assertTrue(any("–" in s and s.endswith("%") for s in drawn))

    def test_mismatched_dates_fail(self) -> None:
        ev = validate_events([{**BAND, "series_id": "FEDFUNDS"}])[0]   # FEDFUNDS 는 2026-08 까지, 상한은 2026-09
        with self.assertRaises(ValueError):
            band_pairs(ev)
        with self.assertRaises(ProjectError):
            setup([{**BAND, "series_id": "FEDFUNDS"}])


class ScatterRecordTest(unittest.TestCase):
    def test_committed_sep(self) -> None:
        r = load_series("SEP_20260916")
        self.assertEqual(r.kind, "scatter")
        self.assertEqual([c.label for c in r.columns], ["2026", "2027", "2028", "2029", "Longer run"])
        self.assertEqual(r.column("2026").median(), 4.125)
        self.assertEqual(len(r.column("2026").values), 18)
        self.assertEqual(r.as_of_label(), "2026년 9월 기준")

    def test_sep_dots_parser(self) -> None:
        html = ("<p>Figure 2. x</p><table><tr><th>Midpoint</th><th>2026</th><th>Longer run</th></tr>"
                "<tr><td>4.125</td><td>2</td><td></td></tr><tr><td>3.000</td><td>1</td><td>3</td></tr></table>")
        self.assertEqual(sep_dots(html), [{"label": "2026", "values": [3.0, 4.125, 4.125]}, {"label": "Longer run", "values": [3.0, 3.0, 3.0]}])
        with self.assertRaises(SeriesError):
            sep_dots("<table></table>")

    def test_scatter_shape_rules(self) -> None:
        base = load_series("SEP_20260916").model_dump(mode="json")
        for over in ({"values": [["2026-09-01", 1.0], ["2026-10-01", 2.0]]}, {"frequency": "monthly"}, {"released": None},
                     {"as_of": "2026-08"}, {"columns": []}):
            with self.subTest(over=over), self.assertRaises(ValidationError):
                SeriesRecord.model_validate({**base, **over})
        bad = copy.deepcopy(base)
        bad["columns"][0]["values"] = list(reversed(bad["columns"][0]["values"]))
        with self.assertRaises(ValidationError):
            SeriesRecord.model_validate(bad)

    def test_raw_reapply_detects_edit(self) -> None:
        src = Path(load_series_file.__code__.co_filename).parent / "series"
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "raw").mkdir()
            for rel in ("SEP_20260916.yaml", "SEP_20260916.csv", "raw/SEP_20260916.htm"):
                (d / rel).write_bytes((src / rel).read_bytes())
            load_series_file(d / "SEP_20260916.yaml")
            lines = (d / "SEP_20260916.csv").read_text(encoding="utf-8").splitlines()
            lines[1] = lines[1].replace("4.125", "4.25", 1) if "4.125" in lines[1] else lines[1].rsplit(",", 1)[0] + ",9.0"
            (d / "SEP_20260916.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaises(SeriesError):
                load_series_file(d / "SEP_20260916.yaml")

    def test_yaml_must_not_hold_values(self) -> None:
        src = Path(load_series_file.__code__.co_filename).parent / "series"
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            raw = yaml.safe_load((src / "SEP_20260916.yaml").read_text(encoding="utf-8"))
            raw["columns"] = [{"label": "2026", "values": [1.0]}]
            (d / "SEP_20260916.yaml").write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
            (d / "SEP_20260916.csv").write_bytes((src / "SEP_20260916.csv").read_bytes())
            with self.assertRaises(SeriesError):
                load_series_file(d / "SEP_20260916.yaml")


if __name__ == "__main__":
    unittest.main()


class ColorByChangeTest(unittest.TestCase):
    """v4.4.0 D-0091 ② — color_by change: 레코드 값 변화 → hike·cut·hold(코드 계산), 기본 fixed 는 기존 그대로."""

    def test_regimes(self) -> None:
        from engine.layers.series import regimes  # noqa: PLC0415

        v = [(date(2024, m, 1), x) for m, x in zip(range(1, 13), [5, 5, 5.25, 5.25, 5.25, 5.25, 5.25, 5.25, 5.25, 5, 5, 5])]
        self.assertEqual(regimes(v, 6), ["hold", "hold"] + ["hike"] * 6 + ["hold", "cut", "cut", "cut"])
        gap = [(date(2024, 1, 1), 5.0), (date(2024, 3, 1), 4.0)]   # 끊긴 뒤는 비교하지 않는다(보간 금지)
        self.assertEqual(regimes(gap, 6), ["hold", "hold"])

    def test_default_fixed_and_colors_drawn(self) -> None:
        from engine.style import C  # noqa: PLC0415

        self.assertEqual(validate_events([BAND])[0]["color_by"], "fixed")
        st, ev, R, cams = setup([{**BAND, "color_by": "change"}])
        R.cache["genre"] = {"name": "macro_monetary"}
        _, img, _ = draw(st, ev, R, cams[0], 10.0)
        import numpy as np  # noqa: PLC0415

        from engine.primitives import semantic_rgba  # noqa: PLC0415
        from genres.load import load_genre  # noqa: PLC0415

        sem = load_genre("macro_monetary").color_semantics
        for k in ("hike", "cut"):
            rgb = np.array(semantic_rgba(sem[k])[:3]) * 255
            self.assertGreater((np.abs(img - rgb).sum(axis=2) < 60).sum(), 20, k)
        self.assertLess(near(img, "amber", 40).sum(), 20)   # 한 색(col)으로 칠하지 않는다
        self.assertIn("amber", C)

    def test_missing_semantics_is_error(self) -> None:
        st, ev, R, cams = setup([{**BAND, "color_by": "change"}])
        R.cache["genre"] = {"name": "geopolitics"}
        with self.assertRaises(ValueError):
            draw(st, ev, R, cams[0], 10.0)
