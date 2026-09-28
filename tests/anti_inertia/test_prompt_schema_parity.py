"""test_prompt_schema_parity — 프롬프트 예시 출력 = 스키마 통과 (docs/handoff/15 P4, 19 부록 B).

agents_reviewer CHART-AP-44(프롬프트가 가르친 모양을 검증기가 100% 무경고 드롭) 재발 방지.
`prompts/*.md` 의 ```yaml / ```json 예시 블록을 추출해 **그 프롬프트를 쓰는 워커가 실제로 검증하는 모델**로 파싱한다.

v2.3.0(D33) → v3.0.0(D-0040 작업 5): script 는 ScriptWorker 의 `response_model`인 `script.schema:Script` 로 검사한다.
v3.1.0: 파리티 대상 5종 전부 ACTIVE(script·director·visual_qa·revise_direction·research). research 는 현 워커의 ResearchDossier(D-0048), Facts 는 픽스처(6.95 에서 워커 전환). PENDING 이 다시 생기면 "모델이 아직 없음" 을 검사한다.
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
    # v3.0.0 ScriptWorker→Script 전환 완료(D33 예고, D-0040 작업 5)
    "script": "script.schema:Script",
    # v3.1.0 연출·검수(D-0047 작업 7)
    "director": "engine.direction:Direction",
    "visual_qa": "engine.qa:QAVerdict",
    "revise_direction": "engine.qa:Revision",
    # v3.2.0 D-0051 작업 7: ResearchWorker → Facts 전환 완료(D47 예고, ResearchDossier 삭제 D52)
    "research": "script.schema:Facts",
    # v3.2.0 소스 인테이크(D-0051 작업 5·6)
    "capture_read": "schemas.source_models:CaptureDraft",
    "verify_sources": "schemas.source_models:VerifyDraft",
}
# 예시 YAML 파일 → 모델 (프롬프트 밖 예시. v3.1.0 D-0047 작업 2 — director 모델이 생겼다)
EXAMPLE_FILES: dict[str, str] = {
    "tests/fixtures/direction/minimal.yaml": "engine.direction:Direction",
    "prompts/examples/hormuz_direction.yaml": "engine.direction:Direction",   # 17 §5.3 director 예시(변환기 산출)
    "tests/fixtures/facts_minimal.json": "script.schema:Facts",
}
PENDING_6_9: dict[str, str] = {}
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
            sc = Script.model_validate(data)
            claims = {c: "corroborated" for s in (x for scn in sc.scenes for x in scn.sentences) for c in s.sources}
            self.assertEqual([i.line() for i in lint(sc, claims).errors], [])   # v3.2.0 — 예시 claim id 는 claims 안으로 본다

    def test_example_files_validate(self) -> None:
        for rel, ref in EXAMPLE_FILES.items():
            from engine.direction import yaml_load  # noqa: PLC0415 — off 키 보존 로더(17 §2)
            _model(ref).model_validate(yaml_load((REPO / rel).read_text(encoding="utf-8")))  # type: ignore[attr-defined]

    def test_pending_models_not_yet_defined(self) -> None:
        for name, ref in PENDING_6_9.items():
            with self.assertRaises((ImportError, AttributeError), msg=f"{ref} 가 생겼다 → {name} 을 ACTIVE 로 옮긴다"):
                _model(ref)


if __name__ == "__main__":
    unittest.main()
