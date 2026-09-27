"""test_prompt_schema_parity — 프롬프트 예시 출력 = 스키마 통과 (docs/handoff/15 P4, 19 부록 B).

agents_reviewer CHART-AP-44(프롬프트가 가르친 모양을 검증기가 100% 무경고 드롭) 재발 방지.
`prompts/*.md` 의 ```yaml / ```json 예시 블록을 추출해 대응 Pydantic 모델로 파싱한다.

Phase 0: 대응 모델(`Script`·`Direction`·`QAVerdict`·`Facts`)이 아직 없다 → strict xfail.
Phase 4(Script)·6.9(Direction·QAVerdict·Facts)에서 모델과 예시가 생기면 XPASS → 마커 제거.
"""

from __future__ import annotations

import importlib
import json
import re
import unittest

import pytest
import yaml

from tests.anti_inertia._ast_util import REPO

# 프롬프트 이름 → "모듈:모델" (docs/handoff/17 §5 프롬프트 5종)
PROMPT_MODELS: dict[str, str] = {
    "script": "script.schema:Script",
    "director": "engine.direction:Direction",
    "visual_qa": "engine.qa:QAVerdict",
    "research": "script.schema:Facts",
}
_FENCE = re.compile(r"```(yaml|json)\n(.*?)```", re.DOTALL)


def _model(ref: str) -> type:
    mod, name = ref.split(":")
    return getattr(importlib.import_module(mod), name)


class PromptSchemaParityTest(unittest.TestCase):
    @pytest.mark.xfail(strict=True, reason="Phase 4/6.9 — Script·Direction·QAVerdict·Facts 모델과 프롬프트 예시 미구현")
    def test_examples_validate(self) -> None:
        checked = 0
        for name, ref in PROMPT_MODELS.items():
            model = _model(ref)
            text = (REPO / "prompts" / f"{name}.md").read_text(encoding="utf-8")
            blocks = _FENCE.findall(text)
            self.assertTrue(blocks, f"prompts/{name}.md 에 예시 블록이 없다")
            for kind, body in blocks:
                data = json.loads(body) if kind == "json" else yaml.safe_load(body)
                model.model_validate(data)  # type: ignore[attr-defined]
                checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
