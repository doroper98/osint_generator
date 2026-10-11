"""edge-tts 백엔드 재유입 방지 (v5.23.0 V4, back_and_forth D-0212, P2·P10).

표준 음성은 Supertonic 3(CLAUDE.md C0.2). edge 백엔드는 플래그가 아니라 삭제로 끝냈다 — 모듈·설정·CLI 선택지·정렬 출처·의존성·
실행 경로의 import 어느 하나라도 다시 생기면 실패한다. 보관소 `docs/handoff/reference_code/` 는 실행 경로가 아니다(_ast_util 제외 목록).
"""

from __future__ import annotations

import ast
import re
import unittest

import yaml

from orchestrator.config import TTSConfig, load_config
from rules import load_rules
from tests.anti_inertia._ast_util import EXCLUDED_PREFIXES, REPO, iter_py

RUN_ROOTS = ("engine", "script", "audio", "orchestrator", "workers", "tools", "geo", "sketch", "schemas", "rules")


class NoEdgeTTSTest(unittest.TestCase):
    def test_modules_deleted(self) -> None:
        for rel in ("script/tts/edge.py", "tools/edge_word_probe.py"):
            self.assertFalse((REPO / rel).exists(), rel)

    def test_config_has_no_edge_keys(self) -> None:
        self.assertEqual([f for f in TTSConfig.model_fields if "edge" in f], [])
        raw = yaml.safe_load((REPO / "config.yaml").read_text(encoding="utf-8"))
        self.assertEqual([k for k in raw["tts"] if "edge" in k], [])
        self.assertNotEqual(load_config().tts.backend_default, "edge")

    def test_plan_cli_rejects_edge(self) -> None:
        from script import plan as plan_mod  # noqa: PLC0415

        self.assertFalse(hasattr(plan_mod, "edge"))
        with self.assertRaises(SystemExit):
            plan_mod.main(["projects/hormuz_korea", "--tts", "edge"])
        with self.assertRaises(ValueError):
            plan_mod.build(REPO / "projects" / "hormuz_korea", "edge")

    def test_alignment_source_not_registered(self) -> None:
        self.assertNotIn("edge_word_boundary", load_rules().tts_rules.alignment_sources)

    def test_dependency_removed(self) -> None:
        for req in ("requirements.txt", "requirements-engine.txt", "pyproject.toml"):
            self.assertIsNone(re.search(r"^\s*\"?edge[-_]tts", (REPO / req).read_text(encoding="utf-8"), re.M), req)

    def test_no_import_in_run_paths(self) -> None:
        self.assertIn("docs/handoff/", EXCLUDED_PREFIXES)   # 보관소(reference_code)는 검사 밖 = 실행 경로 아님
        hits = []
        for p in iter_py(*RUN_ROOTS):
            tree = ast.parse(p.read_text(encoding="utf-8"))
            for n in ast.walk(tree):
                names = ([a.name for a in n.names] if isinstance(n, ast.Import)
                         else [n.module or ""] if isinstance(n, ast.ImportFrom) else [])
                if any(x.split(".")[0] == "edge_tts" or x.endswith("tts.edge") for x in names):
                    hits.append(str(p.relative_to(REPO)))
                if isinstance(n, ast.ImportFrom) and n.module == "script.tts" and any(a.name == "edge" for a in n.names):
                    hits.append(str(p.relative_to(REPO)))
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
