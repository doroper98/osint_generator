"""commit-msg hook — 병합 커밋도 `vX.Y.Z: …` 첫 줄을 요구한다(v7.4.0 감독 지적: 자동 "Merge remote-tracking branch …" 가 C5.3 밖으로 남음)."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / ".githooks" / "commit-msg"


def _run(first_line: str) -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(first_line + "\n\nbody\n")
    try:
        env = {k: v for k, v in os.environ.items() if k != "SKIP_VERSION_CHECK"}
        return subprocess.run(["bash", str(HOOK), f.name], cwd=REPO, capture_output=True, env=env).returncode
    finally:
        os.unlink(f.name)


class CommitMsgHookTest(unittest.TestCase):
    def test_auto_merge_message_rejected(self) -> None:
        self.assertNotEqual(_run("Merge remote-tracking branch 'origin/x' into tmp/y"), 0)
        self.assertNotEqual(_run("Merge branch 'a' of https://example.com/r into b"), 0)

    def test_versioned_merge_and_normal_pass(self) -> None:
        v = (REPO / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(_run(f"v{v}: merge origin/claude/war-history-2026 — UF-170 체리픽과 합침"), 0)
        self.assertEqual(_run(f"v{v}: 문서 보강"), 0)
        self.assertNotEqual(_run("v0.0.1: 다른 버전"), 0)


if __name__ == "__main__":
    unittest.main()
