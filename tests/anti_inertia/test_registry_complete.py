"""test_registry_complete — 레지스트리 양방향 일치 (docs/handoff/15 P10, 19 부록 B).

`rules.registries.event_types` ∪ `panel_kinds` 각각에 대해 `engine/registry.py` 에 모델·렌더러가 있고
`tests/fixtures/preview/{type}.yaml` 예제가 있어야 한다. 역으로 코드에만 있는 타입도 금지.
계획 항목(`event_types_planned`·`panel_kinds_planned`)이 몰래 등록되는 것도 금지(D26 조건 2).
예제는 해당 모델을 그대로 통과해야 한다(P4).

Phase 2(v2.1.0)에서 xfail 해제.
"""

from __future__ import annotations

import importlib
import unittest

import yaml

from rules import load_rules
from tests.anti_inertia._ast_util import REPO


class RegistryCompleteTest(unittest.TestCase):
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

    def test_planned_not_registered(self) -> None:
        registry = importlib.import_module("engine.registry")
        rules = load_rules()
        planned = set(rules.registries.event_types_planned) | {f"panel:{k}" for k in rules.registries.panel_kinds_planned}
        self.assertEqual(planned & set(registry.REGISTRY), set())  # type: ignore[attr-defined]
        self.assertEqual(planned & (set(rules.registries.event_types) | {f"panel:{k}" for k in rules.registries.panel_kinds}),
                         set(), "계획 항목이 등재 목록에도 있다")

    def test_fixtures_validate(self) -> None:
        registry = importlib.import_module("engine.registry")
        for key in registry.REGISTRY:  # type: ignore[attr-defined]
            doc = yaml.safe_load((REPO / "tests" / "fixtures" / "preview" / f"{key.replace(':', '_')}.yaml").read_text(encoding="utf-8"))
            out = registry.validate_events([doc["event"]])  # type: ignore[attr-defined]
            self.assertEqual(len(out), 1, key)


if __name__ == "__main__":
    unittest.main()
