"""v5.22.0 D-0200 — 장치 없는(open) 사용자 의견 게이트 ② + provenance user_feedback_guards.
v7.0.0 D217·D218 — 이 영상 의견 open = 경고 줄(UF 번호·원문), 앞선(다른) 영상 의견 open = 거부(기한 지남). 우회 플래그 없음."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from engine.provenance import feedback_guards
from orchestrator.project_manager import FeedbackUnguardedError, require_feedback_guards
from schemas.feedback_models import FeedbackLedger

ENTRY = """- id: UF-{n:02d}
  date: '2026-10-11'
  project: p
  at: '1초'
  quote: 원문 {n}
  category: c
  guards: {guards}
  status: {status}
  decision: D-0000
"""


def _ledger(d: Path, rows: list[tuple[int, str, str]]) -> Path:
    p = d / "uf.yaml"
    p.write_text("schema_version: 1\nentries:\n" + "".join(ENTRY.format(n=n, guards=g, status=s) for n, g, s in rows), encoding="utf-8")
    return p


class TestGate(unittest.TestCase):
    def test_open_entry_of_earlier_video_blocks(self) -> None:
        """앞선 영상(p) 의견이 장치 없이 다음 영상(q) 게이트에 오면 거부 — 기한 장치(D218). project 모름(None)도 거부."""
        with tempfile.TemporaryDirectory() as d:
            p = _ledger(Path(d), [(1, "[{kind: check, ref: card_exposure}]", "guarded"), (2, "[]", "open")])
            for proj in ("q", None):
                with self.assertRaises(FeedbackUnguardedError) as cm:
                    require_feedback_guards(p, project=proj)
                self.assertIn("UF-02", str(cm.exception))
                self.assertIn("원문 2", str(cm.exception))

    def test_open_entry_of_this_video_warns(self) -> None:
        """그 의견을 받은 영상(p)은 고쳐서 먼저 보낸다 — 거부 대신 경고 줄(UF 번호·원문), D217 "잠금 풀어"."""
        with tempfile.TemporaryDirectory() as d:
            p = _ledger(Path(d), [(1, "[{kind: check, ref: card_exposure}]", "guarded"), (2, "[]", "open")])
            msg = require_feedback_guards(p, project="p")
            for w in ("경고", "UF-02", "원문 2"):
                self.assertIn(w, msg)

    def test_all_guarded_passes(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = _ledger(Path(d), [(1, "[{kind: check, ref: card_exposure}]", "guarded")])
            self.assertIn("1건", require_feedback_guards(p))

    def test_model_rules(self) -> None:
        import yaml

        bad = [  # guarded 인데 장치 없음 / open 인데 장치 있음 / 번호 역순
            [(1, "[]", "guarded")], [(1, "[{kind: check, ref: x}]", "open")],
            [(2, "[]", "open"), (1, "[]", "open")]]
        for rows in bad:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValidationError):
                    FeedbackLedger.model_validate(yaml.safe_load(_ledger(Path(d), rows).read_text(encoding="utf-8")))

    def test_provenance_records_ran_checks(self) -> None:
        chk = {"items": [{"id": "card_exposure", "count": 0}, {"id": "camera_continuity", "count": 0, "skipped": True}]}
        got = {r["id"]: r["checks"] for r in feedback_guards(chk)}
        self.assertEqual(got["UF-01"], {"card_exposure": 0})
        self.assertEqual(got["UF-02"], {"camera_continuity": "skipped"})


if __name__ == "__main__":
    unittest.main()
