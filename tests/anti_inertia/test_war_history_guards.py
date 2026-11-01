"""test_war_history_guards — 전쟁사 검사 넷이 실제로 실패를 낸다 (v7.4.0 W2, back_and_forth D-0600 §4, UF-150 장치).

[evidence-layer-missing]·[period-art-label-missing]·[symbol-set-mixed]·[casualty-unsourced] 를 엔진 검사 진입점
(`engine.checks.check_war_history`, HARD ids)으로 합성 프로젝트에 돌려, 빠진 경우마다 hard 문구가 나오고
다 갖춘 경우 빈 목록인지 본다. 장르가 war_history 가 아니면 검사하지 않는다(기존 영상 불변).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import yaml

from schemas.media_models import MediaAsset
from tests.test_war_history import art

ORDER = {"topic": "칸나이 전투", "genre": "war_history", "instructions": ["t"], "media": {"wanted": ["period_art"], "rights": "PD"}}
FORCES = {"figures": [{"id": "roman_dead", "side": "로마군", "metric": "killed", "source_kind": "ancient_text",
                       "ancient": {"author": "Polybius", "work": "Histories", "book": "III", "chapter": "117", "translation": "Paton",
                                   "translation_url": "https://example.org/p", "translation_license": "Public domain"},
                       "band": {"kind": "modern_estimate", "low": 45000, "high": 70000, "source": "Goldsworthy(2001)"}}]}


def _project(root: Path, *, cite: bool, order: bool = True) -> None:
    if order:
        (root / "order.yaml").write_text(yaml.safe_dump(ORDER, allow_unicode=True), encoding="utf-8")
    (root / "forces.yaml").write_text(yaml.safe_dump(FORCES, allow_unicode=True), encoding="utf-8")
    script = {"title": "t", "subtitle": "s", "date": "2026.11.01", "scenes": [{"id": "a", "sentences": [
        {"date": "-216.08.02", "text": "로마군 전사자는 7만 명이었다고 전합니다.", "sources": ["force:roman_dead"] if cite else ["c1"]}]}]}
    (root / "script.yaml").write_text(yaml.safe_dump(script, allow_unicode=True), encoding="utf-8")


def _P(root: Path, events: list[dict], genre: str = "war_history") -> NS:  # noqa: N802
    assets = {"art": MediaAsset.model_validate(art()),
              "art_nodate": MediaAsset.model_validate(art(created="-216")).model_copy(update={"created": None}),
              "site": MediaAsset.model_validate(art(kind="photo", created=None, work_kind=None, holder=None, art_history=None,
                                                    art_history_source=None, site_report="발굴 보고"))}
    return NS(root=root, events=events, plan=NS(sentences=[NS(sid="a_0", t0=0.0, date="-216.08.02")]),
              R=NS(cache={"genre": {"name": genre}}, assets=NS(media_assets=assets)))


FULL = [{"type": "photo", "mid": "art", "t0": 1.0}, {"type": "photo", "mid": "site", "t0": 5.0},
        {"type": "marker", "toponymy": "cannae", "t0": 0.5}, {"type": "marker", "symbol": "heavy_inf", "t0": 0.5}]


class WarHistoryGuardsTest(unittest.TestCase):
    def run_checks(self, events: list[dict], *, cite: bool = True, genre: str = "war_history") -> dict[str, list[str]]:
        from engine.checks import HARD, check_war_history

        for k in ("evidence_layer", "period_art_label", "casualty_unsourced", "symbol_set"):
            self.assertIn(k, HARD)
        with tempfile.TemporaryDirectory() as d:
            _project(Path(d), cite=cite, order=genre == "war_history")
            return check_war_history(_P(Path(d), events, genre))

    def test_full_passes(self) -> None:
        self.assertEqual(self.run_checks(FULL), {"evidence_layer": [], "period_art_label": [], "casualty_unsourced": [], "symbol_set": []})

    def test_evidence_layer_missing_fails(self) -> None:
        r = self.run_checks([e for e in FULL if e.get("mid") != "site"])
        self.assertTrue(r["evidence_layer"] and r["evidence_layer"][0].startswith("[evidence-layer-missing]"))

    def test_period_art_label_missing_fails(self) -> None:
        r = self.run_checks([*FULL, {"type": "photo", "mid": "art_nodate", "t0": 9.0}])
        self.assertTrue(r["period_art_label"] and r["period_art_label"][0].startswith("[period-art-label-missing]"))

    def test_symbol_set_mixed_fails(self) -> None:
        r = self.run_checks([*FULL, {"type": "marker", "symbol": "app6_arm", "t0": 2.0}])
        self.assertTrue(r["symbol_set"] and r["symbol_set"][0].startswith("[symbol-set-mixed]"))

    def test_casualty_unsourced_fails(self) -> None:
        r = self.run_checks(FULL, cite=False)
        self.assertTrue(r["casualty_unsourced"] and r["casualty_unsourced"][0].startswith("[casualty-unsourced]"))

    def test_other_genre_untouched(self) -> None:
        r = self.run_checks([], genre="geopolitics")
        self.assertEqual(sum(map(len, r.values())), 0)


if __name__ == "__main__":
    unittest.main()
