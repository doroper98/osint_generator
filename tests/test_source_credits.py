"""소스 레코드 → 엔딩 카드 '보도 · 자료'·설명란 원문 링크 (v3.2.0, 18 §6, back_and_forth D-0051 작업 10)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from engine.credits import Credits, RightsError, check_credits, credit_sections, description_sources, source_label
from schemas.source_models import SourcesFile

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tests" / "fixtures" / "intake" / "post_sources.json"
RIGHTS = {"narration": {"tts": {"name": "AI 음성", "license": "AI 음성 합성"}}}


def _sources() -> list:
    return SourcesFile.model_validate(json.loads(FIX.read_text(encoding="utf-8"))).sources


def _credits(auto: bool) -> Credits:
    sec = {"title": "보도 · 자료", "column": 0}
    sec |= {"auto": "sources"} if auto else {"items": [{"main": "수동 행", "sources": ["src_x_0001"]}]}
    return Credits.model_validate({"sections": [sec, {"title": "음성", "column": 1,
                                                      "items": [{"main": "내레이션", "rights": ["narration.tts"]}]}]})


class SourceCreditsTest(unittest.TestCase):
    def test_labels(self) -> None:
        a, b, c = _sources()
        self.assertEqual(source_label(a), f"{a.account_name} {a.handle} (9.20)")
        self.assertEqual(source_label(c), "개인 계정 (9.21)")          # 개인 계정 가림(18 §5)

    def test_auto_section_pairs_two_per_line(self) -> None:
        secs = credit_sections(_credits(True), RIGHTS, {}, None, _sources())
        rows = dict(secs)["보도 · 자료"]
        self.assertEqual(len(rows), 2)
        self.assertIn("  ·  ", rows[0][0])

    def test_uncovered_cited_source_is_error(self) -> None:
        need = {"narration.tts"}
        check_credits(_credits(True), RIGHTS, {}, need, cited_ids={"src_x_0001", "src_x_0002"})
        check_credits(_credits(False), RIGHTS, {}, need, cited_ids={"src_x_0001"})
        with self.assertRaises(RightsError) as cm:
            check_credits(_credits(False), RIGHTS, {}, need, cited_ids={"src_x_0001", "src_x_0002"})
        self.assertIn("src_x_0002", str(cm.exception))

    def test_description_lists_every_source_with_reason_if_no_url(self) -> None:
        lines = description_sources(_sources())
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(" — " in ln for ln in lines))
        self.assertTrue(all("원문 URL 미확보" in ln for ln in lines))    # 픽스처엔 url 이 없다 — 지어내지 않는다

    def test_hormuz_cites_six_sources_and_end_card_text_unchanged(self) -> None:
        from engine.project import load_project  # noqa: PLC0415

        proj = REPO / "projects" / "hormuz_korea"
        if not (proj / "plan.json").exists():
            self.skipTest("hormuz_korea plan.json(로컬 생성물) 없음")
        P = load_project(proj)  # noqa: N806
        self.assertEqual(len(P.R.cache["cited_sources"]), 6)
        rows = dict(credit_sections(P.R.credits, P.R.assets.rights, P.R.assets.media, P.R.cache["credit_refs"],
                                    P.R.cache["cited_sources"]))["보도 · 자료"]
        self.assertEqual(rows[0][0], "Reuters (9.4)  ·  The Korea Herald (9.7)")   # v3 골든 문구 그대로(손으로 쓴 행)


if __name__ == "__main__":
    unittest.main()
