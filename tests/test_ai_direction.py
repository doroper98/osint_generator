"""AI 연출·시각 검수 루프 (v3.1.0, docs/handoff/17 §1·§5, back_and_forth D-0047 작업 8).

가짜 워커·가짜 엔진으로 루프 제어만 검사한다 — 상한(rules visual_qa_loop_max), hard 검사 → 수정, 사람 연출은 루프 없음,
워커 입력 오류는 실패 기록(15 P6).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orchestrator import ai_direction
from rules import load_rules
from schemas.engine_models import StageResult
from schemas.models import TaskResult

LOOP_MAX = load_rules().qa_checks.visual_qa_loop_max


def _verdict(verdict: str) -> dict:
    issues = [] if verdict == "pass" else [{"frame": "p_0010.00", "severity": "soft", "category": "density",
                                            "evidence": "왼쪽 위 사진과 뱃지 세 개가 한 화면에 겹쳐 읽히지 않음"}]
    return {"schema_version": 1, "verdict": verdict, "issues": issues, "praise": []}


class _Stub:
    calls: list[str]

    def __init__(self, name: str, pdir: Path, calls: list[str], verdicts: list[str] | None = None, fail: bool = False,
                 raise_: bool = False) -> None:
        self.name, self.pdir, self.calls, self.verdicts, self.fail, self.raise_ = name, pdir, calls, verdicts, fail, raise_

    def run(self, args: object, task: object) -> TaskResult:
        self.calls.append(self.name)
        if self.raise_:
            raise FileNotFoundError("plan.json")
        if self.name == "visual_qa":
            prev = self.pdir / "prev"
            n = 1
            while (prev / f"qa_verdict.v{n}.json").exists():
                n += 1
            v = self.verdicts.pop(0) if self.verdicts else "revise"
            (prev / f"qa_verdict.v{n}.json").write_text(json.dumps(_verdict(v)), encoding="utf-8")
        return TaskResult(project_id="p", task_id="t", worker=self.name, status="failed" if self.fail else "completed",
                          errors=["x"] if self.fail else [])

    def write_result(self, args: object, res: TaskResult) -> None:
        pass


class LoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.pdir = Path(self._tmp.name) / "p"
        (self.pdir / "prev").mkdir(parents=True)
        self.calls: list[str] = []
        self.records: list[str] = []

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def ai(self) -> None:
        (self.pdir / "direction.meta.json").write_text(json.dumps({"origin": "ai"}), encoding="utf-8")

    def workers(self, verdicts: list[str] | None = None, **kw: object) -> dict:
        return {n: (lambda n=n: _Stub(n, self.pdir, self.calls, verdicts, **kw))  # type: ignore[misc]
                for n in ("director", "visual_qa", "revise_direction")}

    def engine(self, hard_seq: list[int]):  # noqa: ANN201
        def run(stage: str) -> StageResult:
            self.calls.append(stage)
            if stage == "preview":
                hard = hard_seq.pop(0) if hard_seq else 0
                (self.pdir / "prev" / "checks.json").write_text(json.dumps({"hard": hard}), encoding="utf-8")
                return StageResult(ok=hard == 0, stage="preview", errors=[] if hard == 0 else ["checks hard"])
            return StageResult(ok=True, stage=stage)
        return run

    def loop(self, hard_seq: list[int], verdicts: list[str] | None = None, **kw: object) -> tuple[bool, dict]:
        return ai_direction.qa_loop(self.pdir, self.engine(hard_seq), lambda r: self.records.append(r.stage),
                                    workers=self.workers(verdicts, **kw))

    def test_human_direction_no_loop(self) -> None:
        ok, s = self.loop([0])
        self.assertTrue(ok)
        self.assertEqual(self.calls, ["preview"])

    def test_human_direction_hard_stays(self) -> None:
        ok, _ = self.loop([2])
        self.assertFalse(ok)
        self.assertEqual(self.calls, ["preview"])   # 사람 연출은 LLM 이 고치지 않는다

    def test_pass_first(self) -> None:
        self.ai()
        ok, s = self.loop([0], ["pass"])
        self.assertTrue(ok)
        self.assertEqual(self.calls, ["preview", "visual_qa"])
        self.assertEqual(s["iterations"], 0)

    def test_hard_checks_go_to_revise_without_visual_qa(self) -> None:
        self.ai()
        ok, s = self.loop([3, 0], ["pass"])
        self.assertTrue(ok)
        self.assertEqual(self.calls, ["preview", "revise_direction", "validate", "preview", "visual_qa"])
        self.assertEqual(s["iterations"], 1)

    def test_loop_cap(self) -> None:
        self.ai()
        ok, s = self.loop([], ["revise"] * 10)
        self.assertTrue(ok)                                   # 상한 도달 — 잔여 이슈와 함께 게이트 ②
        self.assertEqual(self.calls.count("visual_qa"), LOOP_MAX + 1)
        self.assertEqual(self.calls.count("revise_direction"), LOOP_MAX)
        self.assertEqual(s["iterations"], LOOP_MAX)
        self.assertEqual(len(s["verdicts"]), LOOP_MAX + 1)

    def test_loop_cap_with_hard_left_stays(self) -> None:
        self.ai()
        ok, _ = self.loop([1] * 10)
        self.assertFalse(ok)                                  # hard 검사가 남으면 게이트 ②로 가지 않는다
        self.assertEqual(self.calls.count("revise_direction"), LOOP_MAX)
        self.assertNotIn("visual_qa", self.calls)

    def test_worker_failure_stays(self) -> None:
        self.ai()
        ok, _ = self.loop([0], fail=True)
        self.assertFalse(ok)
        self.assertEqual(self.records, ["preview", "visual_qa"])

    def test_worker_exception_recorded(self) -> None:
        res = ai_direction.run_worker("director", self.pdir, workers=self.workers(raise_=True))
        self.assertFalse(res.ok)
        self.assertIn("plan.json", res.errors[0])


if __name__ == "__main__":
    unittest.main()
