"""v5.21.5 D-0190 §3-2 — 연출 수정 루프가 사람 손질 흔적을 잃지 않는다(P5).

사람이 고친 direction.yaml 을 바탕으로 수정 워커가 새 판을 만들면, 그 판이 보관본과 같아도 provenance origin 은 "ai+human_edit".
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.provenance import ai_direction_summary
from workers.revise_direction_worker import base_is_human_edit


def _proj(d: Path) -> Path:
    (d / "prev").mkdir(parents=True)
    (d / "direction.meta.json").write_text(json.dumps({"origin": "ai", "model": "m", "prompt_sha1": "x"}), encoding="utf-8")
    (d / "direction.v1.yaml").write_text("v1\n", encoding="utf-8")
    return d


class LineageTest(unittest.TestCase):
    def test_base_detection(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            p = _proj(Path(t))
            (p / "direction.yaml").write_text("v1\n", encoding="utf-8")
            self.assertFalse(base_is_human_edit(p))
            (p / "direction.yaml").write_text("v1 + 손질\n", encoding="utf-8")
            self.assertTrue(base_is_human_edit(p))

    def test_revision_on_human_base_marks_origin(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            p = _proj(Path(t))
            (p / "direction.v2.yaml").write_text("v2\n", encoding="utf-8")
            (p / "direction.yaml").write_text("v2\n", encoding="utf-8")   # 쓰인 판 = 보관본 v2 와 바이트 동일
            rev = {"schema_version": 1, "direction_version": 2, "changelog": []}
            (p / "prev" / "revision.v2.json").write_text(json.dumps(rev), encoding="utf-8")
            self.assertEqual(ai_direction_summary(p)["origin"], "ai")
            (p / "prev" / "revision.v2.json").write_text(json.dumps({**rev, "base_human_edit": True}), encoding="utf-8")
            s = ai_direction_summary(p)
            self.assertEqual((s["origin"], s["human_edit_revisions"]), ("ai+human_edit", [2]))

    def test_later_human_base_not_in_used_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            p = _proj(Path(t))
            for n in (2, 3):
                (p / f"direction.v{n}.yaml").write_text(f"v{n}\n", encoding="utf-8")
            (p / "prev" / "revision.v3.json").write_text(json.dumps({"direction_version": 3, "base_human_edit": True, "changelog": []}),
                                                         encoding="utf-8")
            (p / "direction.yaml").write_text("v2\n", encoding="utf-8")   # 판 선택으로 v2 를 썼다 — v3 의 손질 바탕은 계보 밖
            self.assertEqual(ai_direction_summary(p)["origin"], "ai")


if __name__ == "__main__":
    unittest.main()
