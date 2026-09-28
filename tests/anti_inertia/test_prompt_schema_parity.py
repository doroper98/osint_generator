"""test_prompt_schema_parity — 프롬프트 예시 출력 = 스키마 통과 (docs/handoff/15 P4, 19 부록 B).

agents_reviewer CHART-AP-44(프롬프트가 가르친 모양을 검증기가 100% 무경고 드롭) 재발 방지.
`prompts/*.md` 의 ```yaml / ```json 예시 블록을 추출해 **그 프롬프트를 쓰는 워커가 실제로 검증하는 모델**로 파싱한다.

v2.3.0(back_and_forth D-0025, DECISIONS D33): script 는 ScriptWorker 의 `response_model`인 FullScript 로 검사한다.
research·director·visual_qa 는 모델과 예시가 Phase 6.9 에 생긴다 — 그때까지 `PENDING_6_9`에 두고, 모델이 아직
없음을 확인하는 테스트로 "생기면 옮기라"를 강제한다(생기는 순간 실패).
"""

from __future__ import annotations

import importlib
import json
import re
import unittest

import yaml

from tests.anti_inertia._ast_util import REPO

# 프롬프트 이름 → "모듈:모델" (docs/handoff/17 §5 프롬프트 5종)
ACTIVE: dict[str, str] = {
    # Phase 6.8 ScriptWorker→Script 전환 시 `script.schema:Script`로 바꾼다
    "script": "schemas.models:FullScript",
}
PENDING_6_9: dict[str, str] = {
    "director": "engine.direction:Direction",
    "visual_qa": "engine.qa:QAVerdict",
    "research": "script.schema:Facts",
}
_FENCE = re.compile(r"```(yaml|json)\n(.*?)```", re.DOTALL)


def _model(ref: str) -> type:
    mod, name = ref.split(":")
    return getattr(importlib.import_module(mod), name)


def examples(name: str) -> list[object]:
    text = (REPO / "prompts" / f"{name}.md").read_text(encoding="utf-8")
    return [json.loads(body) if kind == "json" else yaml.safe_load(body) for kind, body in _FENCE.findall(text)]


class PromptSchemaParityTest(unittest.TestCase):
    def test_examples_validate(self) -> None:
        checked = 0
        for name, ref in ACTIVE.items():
            model = _model(ref)
            blocks = examples(name)
            self.assertTrue(blocks, f"prompts/{name}.md 에 예시 블록이 없다")
            for data in blocks:
                model.model_validate(data)  # type: ignore[attr-defined]
                checked += 1
        self.assertGreater(checked, 0)

    def test_script_example_passes_lint(self) -> None:
        # 예시가 금지 문구·발음 기호를 가르치면 안 된다(D-0025 §3) — 나레이션을 원고 린트에 그대로 통과시킨다
        from script.lint import lint  # noqa: PLC0415
        from script.schema import Script  # noqa: PLC0415

        for data in examples("script"):
            assert isinstance(data, dict)
            sents = [{"date": "2026.09.18", "text": s["narration"], "sources": ["예시"]} for s in data["segments"]]
            script = Script.model_validate({"title": data["title"], "subtitle": data["topic"], "date": "2026.09.18",
                                            "scenes": [{"id": "example", "sentences": sents}]})
            self.assertEqual([i.line() for i in lint(script).errors], [])

    def test_pending_models_not_yet_defined(self) -> None:
        for name, ref in PENDING_6_9.items():
            with self.assertRaises((ImportError, AttributeError), msg=f"{ref} 가 생겼다 → {name} 을 ACTIVE 로 옮긴다"):
                _model(ref)


if __name__ == "__main__":
    unittest.main()
