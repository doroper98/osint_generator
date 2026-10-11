"""P1-0 기사·사진 노출 수정 (v5.19.0, back_and_forth D-0163 §2·D-0173 §3).

규칙 키 → 생성 프롬프트(리터럴 없음) · 기사 카드 후보 미사용 [article-unused](사유 = 기록만) · [article-density] ·
미디어 계획 표(문장 수 = 행 수) · 사진 목표 미달 + 사유 없음 = 오류 → 게이트 ① 승인 거부 · 검색 기록(통과 0)은 사유 ·
낡은 사유 = 오류 · 기사 트리거 10개(기사 출처 인용 문장에서만) · 사진 소싱 풀 순서·NC/ND 탈락·manual 안내 · 기사 = 비트 개수 밖.
기준 원고 = 골든 `projects/hormuz_korea`(script·intake·plan, git 추적).
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from engine.media_plan import article_candidate_usage, density_report
from rules import load_rules
from orchestrator.config import AppConfig, PathsConfig
from script import media_table as MT
from script.media_suggest import suggest_media
from script.schema import Plan
from workers.prompt_loader import load_prompt

REPO = Path(__file__).resolve().parent.parent
HORMUZ = REPO / "projects" / "hormuz_korea"


def _copy(dst: Path) -> Path:
    (dst / "intake").mkdir(parents=True)
    for f in ("script.yaml", "plan.json"):
        shutil.copy(HORMUZ / f, dst / f)
    for f in ("claims.json", "sources.json"):
        shutil.copy(HORMUZ / "intake" / f, dst / "intake" / f)
    return dst


class _Proj(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.proj = _copy(Path(self.tmp.name) / "p")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _notes(self, doc: dict) -> None:
        (self.proj / MT.NOTES_FILE).write_text(yaml.safe_dump({"schema_version": 1, **doc}, allow_unicode=True), encoding="utf-8")


class PromptRuleTest(unittest.TestCase):
    def test_density_from_rules_not_literal(self) -> None:
        for name in ("director", "genre_director"):
            raw = (REPO / "prompts" / f"{name}.md").read_text(encoding="utf-8")
            self.assertNotIn("40~60초", raw, f"{name}: 밀도 리터럴 — rules media.density 로(P3)")
        rules = load_rules()
        d = rules.model_copy(deep=True)
        d.media.density.article_per_min_max = 7
        d.media.density.per_item_sec = (33.0, 77.0)
        d.media.density.photo_target_per_min = 3
        base, changed = load_prompt("director", rules), load_prompt("director", d)
        self.assertIn("60초 구간마다 2개까지", base)
        self.assertIn("60초 구간마다 7개까지", changed)
        self.assertIn("33~77초에 하나", changed)
        self.assertIn("분당 3장", changed)
        self.assertEqual(base.replace("2개까지", "7개까지").replace("40~60초", "33~77초").replace("분당 1장", "분당 3장"), changed)


class ArticleUsageTest(_Proj):
    def setUp(self) -> None:
        super().setUp()
        self.plan = Plan.model_validate_json((self.proj / "plan.json").read_text(encoding="utf-8"))
        self.by = {s.sid: s for s in self.plan.sentences}

    def _art(self, sid: str, mid: str = "reuters_0904") -> dict:
        s = self.by[sid]
        return {"type": "article", "mid": mid, "t0": s.t0, "t1": s.t1}

    def test_candidates_need_confirmed_registered_article(self) -> None:
        c = MT.article_candidates(self.proj)
        self.assertEqual(c["route_0"], ["reuters_0904"])            # Reuters(src_art_0001) — url 없는 옛 항목은 매체·날짜로 잇는다
        self.assertNotIn("cost_0", c)                                # IMO(src_art_0005) — 등록 안 됨
        srcs = json.loads((self.proj / "intake" / "sources.json").read_text(encoding="utf-8"))
        for s in srcs["sources"]:
            s["confirmed_by"] = None
        (self.proj / "intake" / "sources.json").write_text(json.dumps(srcs, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(MT.article_candidates(self.proj), {})      # 확인 안 된 출처 = 후보 아님

    def test_unused_warns_and_reason_records(self) -> None:
        r = article_candidate_usage(self.proj, self.plan, [])
        first = [s for s in self.plan.sentences if s.t0 < 60]
        self.assertEqual(sum("[article-unused]" in w for w in r["warnings"] if " 0~60초" in w), 2)
        longest = max(first, key=lambda s: len(s.text)).sid
        self.assertTrue(any(w.startswith(f"[article-unused] {longest} ") for w in r["warnings"]))   # 긴 문장 먼저
        self._notes({"sentences": {longest: {"article": "테스트 사유 — 지도 장면 유지"}}})
        r2 = article_candidate_usage(self.proj, self.plan, [])
        self.assertFalse(any(w.startswith(f"[article-unused] {longest} ") for w in r2["warnings"]))
        self.assertIn({"sid": longest, "reason": "테스트 사유 — 지도 장면 유지"},
                      [{"sid": u["sid"], "reason": u["reason"]} for u in r2["unused"]])

    def test_used_cards_clear_bucket_and_density_cap(self) -> None:
        cands = MT.article_candidates(self.proj)
        first = [s.sid for s in self.plan.sentences if s.t0 < 60 and s.sid in cands]
        r = article_candidate_usage(self.proj, self.plan, [self._art(first[0]), self._art(first[1])])
        self.assertFalse([w for w in r["warnings"] if " 0~60초" in w])
        r = article_candidate_usage(self.proj, self.plan, [self._art(x) for x in first[:3]])
        self.assertTrue([w for w in r["warnings"] if w.startswith("[article-density] 0~60초")])

    def test_articles_outside_beat_count(self) -> None:
        tb = mock.Mock(scenes=["a"], SC=lambda s: 0.0)
        evs = [{"type": "article", "mid": f"a{i}", "t0": 10.0 * i, "t1": 10.0 * i + 4} for i in range(6)]
        evs.append({"type": "photo", "mid": "p", "t0": 5.0, "t1": 9.0})
        r = density_report(evs, tb, 60.0)
        self.assertEqual((r["count"], r["beat_count"]), (7, 1))
        self.assertFalse([w for w in r["warnings"] if "media-density-total" in w])


class MediaTableTest(_Proj):
    def test_rows_equal_sentences_and_zero_photo_without_reason_is_error(self) -> None:
        t = MT.media_table(self.proj)
        n = sum(len(sc.sentences) for sc in MT._script(self.proj).scenes)
        self.assertEqual(len(t.rows), n)
        self.assertEqual((t.photo_selected, t.photo_target, t.total_source), (0, 4, "plan"))   # 260.7초 × 분당 1 = 4
        need = {r.sid for r in t.rows if r.photo_candidate}
        self.assertEqual({e.split()[1].rstrip(":") for e in t.errors}, need)
        self.assertTrue(all(e.startswith("[photo-reason]") for e in t.errors))
        self._notes({"sentences": {sid: {"photo": "검색 0건(테스트)"} for sid in need}})
        self.assertEqual(MT.media_table(self.proj).errors, [])

    def test_search_log_with_zero_passed_is_reason(self) -> None:
        t = MT.media_table(self.proj)
        sid = next(r.sid for r in t.rows if r.photo_candidate)
        log = {"schema_version": 1, "searches": [
            {"sid": sid, "query": "q", "pool": "us_dod_pd", "on": "2026-10-11", "found": 3, "passed": 0, "rejected": ["CC BY-NC-ND 2.0 NC·ND"]}]}
        (self.proj / MT.SEARCH_FILE).write_text(json.dumps(log), encoding="utf-8")
        t2 = MT.media_table(self.proj)
        row = next(r for r in t2.rows if r.sid == sid)
        self.assertIn("통과 0", row.reason or "")
        self.assertFalse([e for e in t2.errors if f" {sid}:" in e])
        log["searches"][0]["passed"] = 2   # 통과 후보가 있는데 안 골랐으면 사유가 필요
        (self.proj / MT.SEARCH_FILE).write_text(json.dumps(log), encoding="utf-8")
        self.assertTrue([e for e in MT.media_table(self.proj).errors if f" {sid}:" in e and "권리 통과 후보 2건" in e])

    def test_selected_photo_meets_target(self) -> None:
        sc = yaml.safe_load((self.proj / "script.yaml").read_text(encoding="utf-8"))
        for k, (scene, i) in enumerate([("route", 0), ("war", 0), ("review", 1), ("past", 1)]):
            sc_ = next(s for s in sc["scenes"] if s["id"] == scene)
            sc_["sentences"][i]["media"] = {"kind": "photo", "asset_id": ("hormuz_transit", "rok_iraq")[k % 2]}
        (self.proj / "script.yaml").write_text(yaml.safe_dump(sc, allow_unicode=True), encoding="utf-8")
        t = MT.media_table(self.proj)
        self.assertEqual((t.photo_selected, t.errors), (4, []))

    def test_stale_note_is_error(self) -> None:
        self._notes({"sentences": {"nope_9": {"photo": "옛 사유입니다"}}})
        with self.assertRaises(MT.MediaTableError):
            MT.media_table(self.proj)

    def test_gate_one_refuses_without_reasons(self) -> None:
        from orchestrator.project_manager import MediaPlanError, approve_gate, new_project, transition_state  # noqa: PLC0415
        from schemas.models import ProjectState as S  # noqa: PLC0415

        cfg = AppConfig(paths=PathsConfig(projects_root=str(Path(self.tmp.name))))
        m = new_project("q", "t", "geopolitics", cfg=cfg)
        _copy_into = Path(self.tmp.name) / "q"
        for f in ("script.yaml", "plan.json"):
            shutil.copy(self.proj / f, _copy_into / f)
        (_copy_into / "intake").mkdir(exist_ok=True)
        for f in ("claims.json", "sources.json"):
            shutil.copy(self.proj / "intake" / f, _copy_into / "intake" / f)
        with mock.patch("orchestrator.source_completeness_checker.check_script_sources", return_value=[]):   # 출처 완결은 별개 검사
            for s in (S.INTAKE, S.SOURCE_VERIFY, S.RESEARCH, S.SCRIPT_DRAFT, S.SCRIPT_APPROVAL):
                m = transition_state(m, s, reason="test", cfg=cfg)
        with self.assertRaises(MediaPlanError):
            approve_gate(m, "script_approval", by="t", cfg=cfg)
        (_copy_into / MT.NOTES_FILE).write_text(yaml.safe_dump({"schema_version": 1, "sentences": {
            r.sid: {"photo": "검색 0건(테스트)"} for r in MT.media_table(self.proj).rows if r.photo_candidate}}, allow_unicode=True),
            encoding="utf-8")
        m = approve_gate(m, "script_approval", by="t", cfg=cfg)
        self.assertIn("사진 0/4", m.gate_decisions[-1].shown["media_plan"])


class TriggerTest(_Proj):
    def test_ten_article_triggers_only_in_citing_sentences(self) -> None:
        trig = load_rules().media_beats.triggers["article"]
        self.assertEqual(len(trig), 10)
        for w in ("보도했", "전했", "밝혔", "인용", "에 따르면", "보도에 따르면", "기고", "사설", "단독", "확인했"):
            self.assertIn(w, trig)
        plan = Plan.model_validate_json((self.proj / "plan.json").read_text(encoding="utf-8"))
        s0 = plan.sentences[0]
        p2 = plan.model_copy(deep=True)
        p2.sentences[0].text = "대통령실은 결정된 것이 없다고 밝혔습니다."
        hit = [m for m in suggest_media(p2, article_sids={s0.sid}) if m.sid == s0.sid]
        self.assertEqual((hit[0].kind, hit[0].trigger), ("article", "밝혔"))
        miss = [m for m in suggest_media(p2, article_sids=set()) if m.sid == s0.sid and m.kind == "article"]
        self.assertEqual(miss, [])   # 기사 출처를 인용하지 않은 문장 — "밝혔다" 주어가 매체가 아니다


class SourcingOrderTest(unittest.TestCase):
    def test_pools_in_rule_order_nc_nd_rejected_manual_hint_and_log(self) -> None:
        from tools.media_fetch import search_pools  # noqa: PLC0415

        order = [p.id for p in load_rules().media_beats.sources_order]
        self.assertEqual(order, ["us_dod_pd", "commons_cc", "gov_flickr_ccby"])
        seen: list[str] = []

        def fake(q: str, limit: int) -> list[dict]:
            seen.append(q)
            return [{"title": "File:A.jpg", "lic": "Public domain", "restrictions": [], "allowed": True, "page": "a"},
                    {"title": "File:N.jpg", "lic": "CC BY-NC-ND 2.0", "restrictions": [], "allowed": True, "page": "n"}]

        with tempfile.TemporaryDirectory() as d:
            rows = search_pools("Pakistan army", 5, log=Path(d), sid="war_0", searcher=fake)
            log = json.loads((Path(d) / MT.SEARCH_FILE).read_text(encoding="utf-8"))
        self.assertEqual(seen, ['Pakistan army hastemplate:"PD-USGov-Military"', "Pakistan army"])
        self.assertEqual([r["pool"] for r in rows], ["us_dod_pd", "us_dod_pd", "commons_cc", "commons_cc", "gov_flickr_ccby"])
        self.assertEqual([r.get("allowed") for r in rows[:2]], [True, False])   # NATO 류 BY-NC-ND 탈락
        self.assertTrue(rows[-1]["manual"])                                      # API 없는 풀 = 안내 줄(조용히 건너뛰지 않는다)
        self.assertEqual([(s["pool"], s["found"], s["passed"]) for s in log["searches"]], [("us_dod_pd", 2, 1), ("commons_cc", 2, 1)])


if __name__ == "__main__":
    unittest.main()
