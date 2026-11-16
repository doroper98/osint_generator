"""게이트 기록이 확인하지 못한 값을 사실처럼 남기지 않는다(v7.4.0 감독 D621 ④⑤, PIPELINE-AP-027).

④ 린트 서브프로세스가 StageResult JSON 없이 끝나면 errors 는 stderr 꼬리다 — '린트 오류 6' 으로 세지 않고 승인 기록을 거부한다.
⑤ prev/ 없는 체크아웃에서 게이트 ② 기록의 cuts·밀도는 '확인 불가', media_used 에 배경 사진(backdrop) 수도 적는다.
"""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

import yaml

from orchestrator import engine_service
from orchestrator.gate_view import media_summary, preview_gate_view, script_gate_view
from orchestrator.project_manager import approve_gate
from tests.test_gates_pipeline import _Proj


def crash_runner(cmd: list[str], **kw: object) -> subprocess.CompletedProcess:
    """린트 CLI 가 결과 줄 없이 죽은 경우(감독 컨테이너 cairo 없음 사고) — stdout 비고 stderr 에 트레이스백."""
    tb = "Traceback (most recent call last):\n  File x\n  File y\n  File z\nModuleNotFoundError: No module named 'cairo'"
    return subprocess.CompletedProcess(cmd, 1, "", tb)


class CrashDetectTest(unittest.TestCase):
    def test_no_json_is_crash(self) -> None:
        r = engine_service.parse_result("direction_validate", 1, "", "Traceback\nboom")
        self.assertTrue(engine_service.is_crash(r))

    def test_bad_last_line_is_crash(self) -> None:
        r = engine_service.parse_result("direction_validate", 1, "not json", "")
        self.assertTrue(engine_service.is_crash(r))

    def test_real_lint_errors_are_not_crash(self) -> None:
        body = json.dumps({"ok": False, "stage": "lint", "errors": ["금지 문구"], "warnings": []})
        r = engine_service.parse_result("direction_validate", 1, body, "")
        self.assertFalse(engine_service.is_crash(r))


class ScriptGateCrashTest(_Proj):
    def test_crash_not_counted_and_approve_refused(self) -> None:
        text, shown = script_gate_view(self.root / "p", runner=crash_runner)
        self.assertIn("실행 실패", text)
        self.assertNotIn("린트 — 오류", text)
        self.assertTrue(shown["lint_errors"].startswith("확인 불가"))
        self.assertIn("StageResult JSON 없음", shown["lint_crash"])
        self.to_gate1()
        with self.assertRaisesRegex(ValueError, "린트 실행 실패"):
            approve_gate(self.m, "script_approval", by="user", shown=shown, cfg=self.cfg)
        self.assertEqual(getattr(self.m.current_state, "value", self.m.current_state), "script_approval")


class PreviewShownTest(_Proj):
    def _direction(self) -> None:
        evs = [{"type": "backdrop", "img": "a"}, {"type": "backdrop", "img": "b"}, {"type": "photo", "mid": "zz_missing"}]
        (self.root / "p" / "direction.yaml").write_text(yaml.safe_dump({"events": evs}), encoding="utf-8")

    def test_no_prev_is_unknown_not_zero(self) -> None:
        _, shown = preview_gate_view(self.root / "p")
        self.assertTrue(shown["cuts"].startswith("확인 불가"))
        self.assertTrue(shown["sheet"].startswith("확인 불가"))

    def test_media_used_counts_backdrop_and_density_unknown(self) -> None:
        self._direction()
        shown: dict[str, str] = {}
        media_summary(self.root / "p", shown)
        self.assertIn("real 1 · backdrop 2", shown["media_used"])
        self.assertIn("밀도 검사 확인 불가", shown["media_used"])

    def test_density_from_prev_provenance(self) -> None:
        self._direction()
        prev = Path(self.root / "p" / "prev")
        prev.mkdir()
        (prev / "provenance.json").write_text(json.dumps({"media_density": {"count": 11, "value": 1.629}}), encoding="utf-8")
        shown: dict[str, str] = {}
        media_summary(self.root / "p", shown)
        self.assertIn("밀도 검사 11개 · 1.629/분", shown["media_used"])
        _, s2 = preview_gate_view(self.root / "p")
        self.assertEqual(s2["cuts"], "0")


if __name__ == "__main__":
    unittest.main()
