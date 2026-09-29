"""test_registry_complete — 레지스트리 양방향 일치 (docs/handoff/15 P10, 19 부록 B).

`rules.registries.event_types` ∪ `panel_kinds` 각각에 대해 `engine/registry.py` 에 모델·렌더러가 있고
`tests/fixtures/preview/{type}.yaml` 예제가 있어야 한다. 역으로 코드에만 있는 타입도 금지.
계획 항목(`event_types_planned`·`panel_kinds_planned`)이 몰래 등록되는 것도 금지(D26 조건 2).
예제는 해당 모델을 그대로 통과해야 한다(P4).

Phase 2(v2.1.0)에서 xfail 해제.
v4.2.0(D-0081 작업 4): `registries.primitives` 마다 engine/primitives/<id>.py 모듈·SCHEMA·COLOR_KEYS·draw·PREVIEW_FIXTURE,
PREVIEW_FIXTURE 가 레지스트리 모델 통과, rules primitives.<id> 레이아웃 토큰, 모듈 안 hex 리터럴·함수 본문 숫자(0·1·2 밖) 0(20 §4.2).
프리미티브 항목의 프리뷰 예제는 모듈의 PREVIEW_FIXTURE 다(yaml 파일 아님).
"""

from __future__ import annotations

import ast
import importlib
import re
import unittest

import yaml

from rules import load_rules
from tests.anti_inertia._ast_util import REPO


class RegistryCompleteTest(unittest.TestCase):
    def test_bidirectional(self) -> None:
        registry = importlib.import_module("engine.registry")
        rules = load_rules()
        declared = (set(rules.registries.event_types) | {f"panel:{k}" for k in rules.registries.panel_kinds}
                    | {f"primitive:{k}" for k in rules.registries.primitives})
        implemented = set(registry.REGISTRY)  # type: ignore[attr-defined]
        self.assertEqual(declared, implemented)
        for key, entry in registry.REGISTRY.items():  # type: ignore[attr-defined]
            self.assertIsNotNone(entry.model, key)
            self.assertTrue(callable(entry.render), key)
            if key == "primitive" or key.startswith("primitive:"):
                continue   # 예제 = 모듈 PREVIEW_FIXTURE(test_primitive_contract · test_fixtures_validate)
            fixture = REPO / "tests" / "fixtures" / "preview" / f"{key.replace(':', '_')}.yaml"
            self.assertTrue(fixture.exists(), f"프리뷰 예제 없음: {fixture}")

    def test_panel_axis_declared(self) -> None:
        """v4.3.0 D-0087 보정 2 — 패널 모듈마다 AXIS(value|date|none), 값 축이면 정직성 메타 함수(engine.honesty.PANEL_META)."""
        from engine.honesty import PANEL_META  # noqa: PLC0415

        targets = load_rules().qa_checks.chart_targets
        for k in load_rules().registries.panel_kinds:
            axis = getattr(importlib.import_module(f"engine.panels.{k}"), "AXIS", None)
            self.assertIn(axis, targets, f"engine/panels/{k}.py AXIS")
            self.assertEqual(axis == "value", k in PANEL_META, f"값 축 패널 {k} 의 정직성 메타")
        self.assertIn(importlib.import_module("engine.layers.series").AXIS, targets)

    def test_primitive_axis_declared(self) -> None:
        """v4.4.0 D-0090 작업 3 — 프리미티브 모듈마다 AXIS(value|date|none), 값 축이면 chart_meta(정직성 대상)."""
        targets = load_rules().qa_checks.chart_targets
        for k in load_rules().registries.primitives:
            mod = importlib.import_module(f"engine.primitives.{k}")
            self.assertIn(getattr(mod, "AXIS", None), targets, f"engine/primitives/{k}.py AXIS")
            self.assertEqual(mod.AXIS == "value", callable(getattr(mod, "chart_meta", None)), f"값 축 프리미티브 {k} 의 chart_meta")

    def test_planned_not_registered(self) -> None:
        registry = importlib.import_module("engine.registry")
        rules = load_rules()
        planned = set(rules.registries.event_types_planned) | {f"panel:{k}" for k in rules.registries.panel_kinds_planned}
        self.assertEqual(planned & set(registry.REGISTRY), set())  # type: ignore[attr-defined]
        self.assertEqual(planned & (set(rules.registries.event_types) | {f"panel:{k}" for k in rules.registries.panel_kinds}),
                         set(), "계획 항목이 등재 목록에도 있다")
        self.assertEqual(set(rules.registries.primitives_planned) & set(rules.registries.primitives), set(),   # v4.2.0 D-0082
                         "계획 프리미티브가 등록 목록에도 있다")

    def test_fixtures_validate(self) -> None:
        registry = importlib.import_module("engine.registry")
        for key in registry.REGISTRY:  # type: ignore[attr-defined]
            if key == "primitive" or key.startswith("primitive:"):   # 운반 타입·id 항목 모두 모듈 PREVIEW_FIXTURE 로(중복 예제 파일 없음)
                from engine.primitives import module  # noqa: PLC0415

                pids = load_rules().registries.primitives if key == "primitive" else [key.split(":", 1)[1]]
                self.assertTrue(pids, "운반 타입 primitive 가 등록됐는데 프리미티브가 하나도 없다")
                for pid in pids:
                    self.assertEqual(len(registry.validate_events([module(pid).PREVIEW_FIXTURE])), 1, pid)  # type: ignore[attr-defined]
                continue
            doc = yaml.safe_load((REPO / "tests" / "fixtures" / "preview" / f"{key.replace(':', '_')}.yaml").read_text(encoding="utf-8"))
            out = registry.validate_events([doc["event"]])  # type: ignore[attr-defined]
            self.assertEqual(len(out), 1, key)


_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
ALLOWED_NUMBERS = {0, 1, 2}


def primitive_literal_violations(src: str) -> list[str]:
    """프리미티브 모듈 소스 → 토큰 규칙 위반(hex 문자열 어디서나, 함수 본문의 0·1·2 밖 숫자). 20 §4.2 "색·크기는 토큰만"."""
    tree = ast.parse(src)
    out = [f"{n.lineno}: hex {n.value!r}" for n in ast.walk(tree)
           if isinstance(n, ast.Constant) and isinstance(n.value, str) and _HEX.search(n.value)]
    for fn in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
        for n in ast.walk(fn):
            if (isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)
                    and n.value not in ALLOWED_NUMBERS):
                out.append(f"{n.lineno}: 숫자 {n.value!r} ({fn.name})")
    return out


class PrimitiveContractTest(unittest.TestCase):
    def test_registered_primitives_have_contract(self) -> None:
        from engine.primitives import CONTRACT, module  # noqa: PLC0415
        from engine.style import PRIMITIVES  # noqa: PLC0415

        registry = importlib.import_module("engine.registry")
        for pid in load_rules().registries.primitives:
            with self.subTest(primitive=pid):
                mod = module(pid)
                for attr in CONTRACT:
                    self.assertTrue(hasattr(mod, attr), attr)
                self.assertTrue(callable(mod.draw))
                self.assertEqual(mod.SCHEMA.model_config.get("extra"), "forbid")
                self.assertIn(pid, PRIMITIVES, f"rules primitives.{pid} 레이아웃 토큰 없음")
                self.assertEqual(mod.PREVIEW_FIXTURE["id"], pid)
                out = registry.validate_events([mod.PREVIEW_FIXTURE])  # type: ignore[attr-defined]   # P4 — 예제 = 스키마 통과
                self.assertEqual(len(out), 1)

    def test_modules_are_registered(self) -> None:
        """역방향 — engine/primitives/ 의 모듈은 전부 registries.primitives 에 있다(코드에만 있는 요소 금지)."""
        mods = {p.stem for p in (REPO / "engine" / "primitives").glob("*.py") if p.stem != "__init__"}
        self.assertEqual(mods, set(load_rules().registries.primitives))

    def test_tokens_only(self) -> None:
        for p in sorted((REPO / "engine" / "primitives").glob("*.py")):
            if p.stem == "__init__":
                continue
            with self.subTest(module=p.name):
                self.assertEqual(primitive_literal_violations(p.read_text(encoding="utf-8")), [])

    def test_literal_detector(self) -> None:
        bad = 'X = "#ff0000"\ndef draw(ctx, view, t, e, style):\n    return (0, 0, 12.5, 1)\n'
        self.assertEqual(len(primitive_literal_violations(bad)), 2)
        self.assertEqual(primitive_literal_violations('def draw(ctx, view, t, e, s):\n    return s.layout.w * 2\n'), [])

    def test_planned_primitive_is_error(self) -> None:
        registry = importlib.import_module("engine.registry")
        for pid in load_rules().registries.primitives_planned:
            with self.subTest(primitive=pid), self.assertRaisesRegex(registry.RegistryError, "planned"):  # type: ignore[attr-defined]
                registry.resolve({"type": "primitive", "id": pid, "t0": 0, "t1": 1})  # type: ignore[attr-defined]
        with self.assertRaisesRegex(registry.RegistryError, "레지스트리에 없음"):  # type: ignore[attr-defined]
            registry.resolve({"type": "primitive", "id": "hologram"})  # type: ignore[attr-defined]


if __name__ == "__main__":
    unittest.main()
