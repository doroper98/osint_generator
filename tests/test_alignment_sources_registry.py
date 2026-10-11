"""프로젝트 정렬 출처 ⊆ 등록부 + 옛 음성 보관본 재정렬 (v6.0.1, back_and_forth D-0214, PIPELINE-AP-022).

V4(edge 삭제) 감사가 빠른 묶음만 보고 slow 시험이 부르는 실제 프로젝트(artifacts 복원본)의 옛 정렬 파일을 놓쳤다.
이 빠른 시험은 저장소 안 모든 프로젝트의 plan 문장 정렬 파일 출처가 `rules tts_rules.alignment_sources` 안인지 본다
(복원하지 않은 컨테이너에선 대상이 0 이어도 통과 — 대신 재정렬 함수 자체는 아래 가짜 정렬로 항상 검사).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rules import load_rules
from script.tts import align as tts_align
from script.tts import forced_align as FA

REPO = Path(__file__).resolve().parent.parent


class ProjectSourcesTest(unittest.TestCase):
    def test_every_project_alignment_registered(self) -> None:
        allowed = set(load_rules().tts_rules.alignment_sources)
        bad = []
        for pp in sorted((REPO / "projects").glob("*/plan.json")):
            for s in json.loads(pp.read_text(encoding="utf-8"))["sentences"]:
                ap = tts_align.align_path(Path(s["mp3"]))
                if ap.exists():
                    src = json.loads(ap.read_text(encoding="utf-8")).get("alignment_source")
                    if src not in allowed:
                        bad.append((pp.parent.name, s["sid"], src))
        self.assertEqual(bad, [], "옛 출처 정렬 — `python -m script.tts.forced_align --realign projects/<pid>`(D-0214)")


class RealignTest(unittest.TestCase):
    def _proj(self, d: str) -> Path:
        proj = Path(d) / "p"
        (proj / "tts").mkdir(parents=True)
        mp3 = proj / "tts" / "a_1_x.mp3"
        mp3.write_bytes(b"x" * 2000)
        tts_align.align_path(mp3).write_text(json.dumps({"alignment_source": "edge_word_boundary", "characters": list("가나"),
                                                          "character_start_times_seconds": [0.1, 0.2]}), encoding="utf-8")
        plan = {"sentences": [dict(sid="a_1", scene="a", date="2026", text="가나", tts="가나", segments=[["가나", 0]], mp3=str(mp3),
                                   npy="x.npy", dur=1.0, t0=1.0, t1=2.0, trim_offset=0.05)],
                "cards": [], "scene_start": {"a": 1.0}, "total": 3.0, "voice": "edge-tts ko-KR-InJoonNeural",
                "title": "t", "subtitle": "s", "date": "2026"}
        (proj / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        return proj

    def test_realign_keeps_voice_records_old_source(self) -> None:
        new = {"alignment_source": "mms_forced_alignment", "characters": list("가나"), "character_start_times_seconds": [0.21, 0.32],
               "character_end_times_seconds": [0.32, 0.5], "score_mean": 0.8, "elapsed_ms": 10}
        with tempfile.TemporaryDirectory() as d:
            proj = self._proj(d)
            with mock.patch.object(FA, "align_file", return_value=dict(new)) as m:
                rep = FA.realign_project(proj)
                again = FA.realign_project(proj)          # 멱등 — 이미 MMS 면 다시 정렬하지 않는다
            self.assertEqual(m.call_count, 1)
            self.assertEqual((rep["realigned"], again["realigned"], again["kept"]), (1, 0, 1))
            plan = json.loads((proj / "plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["voice"], "edge-tts ko-KR-InJoonNeural")   # 옛 음성 그대로, 정직한 라벨
            self.assertEqual(plan["sentences"][0]["alignment"]["realigned_from"], "edge_word_boundary")
            self.assertEqual((plan["sentences"][0]["dur"], plan["total"]), (1.0, 3.0))   # 길이 그대로
            al = tts_align.read(Path(plan["sentences"][0]["mp3"]))
            self.assertEqual((al["alignment_source"], al["realigned_from"]), ("mms_forced_alignment", "edge_word_boundary"))


if __name__ == "__main__":
    unittest.main()
