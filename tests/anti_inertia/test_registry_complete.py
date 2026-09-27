"""test_registry_complete — 레지스트리 양방향 일치 (docs/handoff/15 P10, 19 부록 B).

`rules.registries.event_types` ∪ `panel_kinds` 각각에 대해 `engine/registry.py` 에 모델·렌더러가 있고
`tests/fixtures/preview/{type}.yaml` 예제가 있어야 한다. 역으로 코드에만 있는 타입도 금지.

Phase 0: `engine/registry.py` 없음 → strict xfail. Phase 2 에서 해제.
"""

from __future__ import annotations

import importlib
import unittest

import pytest

from rules import load_rules
from tests.anti_inertia._ast_util import REPO


class RegistryCompleteTest(unittest.TestCase):
    @pytest.mark.xfail(strict=True, reason="Phase 2 — engine/registry.py 미구현")
    def test_bidirectional(self) -> None:
        registry = importlib.import_module("engine.registry")
        rules = load_rules()
        declared = set(rules.registries.event_types) | {f"panel:{k}" for k in rules.registries.panel_kinds}
        implemented = set(registry.REGISTRY)  # type: ignore[attr-defined]
        self.assertEqual(declared, implemented)
        for key, entry in registry.REGISTRY.items():  # type: ignore[attr-defined]
            self.assertIsNotNone(entry.model, key)
            self.assertTrue(callable(entry.render), key)
            fixture = REPO / "tests" / "fixtures" / "preview" / f"{key.replace(':', '_')}.yaml"
            self.assertTrue(fixture.exists(), f"프리뷰 예제 없음: {fixture}")


if __name__ == "__main__":
    unittest.main()
