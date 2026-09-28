"""ScriptWorker — 원고 작성 (v3.0.0, 16 §3 개조, back_and_forth D-0040 작업 5·D-0043).

`research_dossier.json` (주장-근거) + `ProjectManifest` (제목/주제/목표 길이) 를 읽어
`script.schema:Script`(장면 자유 구성, 자막 text / 발음 tts 분리, sources) 를 생성하고
`projects/{pid}/script.yaml` 로 저장합니다. 옛 FullScript(챕터·세그먼트)는 삭제(15 P2).

원칙
----
- `BaseLLMWorker` 상속, `llm_mode="response"` (외부 자료 미접근 → allow_agent_mode 불필요).
- `response_model = Script`. 저장은 YAML(사람이 고친다).
- build_user_prompt 는 `.replace()` 로만 합성 (C2: `.format()` 금지).
- 사용자 질문 금지 (C4).
- **검증 라벨은 LLM 이 쓰지 않는다**(D-0043, 15 P8). 문장 `sources` = 도시어 claim_id 만 —
  도시어 밖 id 는 check_parsed 오류. 라벨은 코드(script/labels)가 도시어 status 로 계산해
  `script_labels.json` 에 저장한다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import ClassVar, Literal, Type

from pydantic import BaseModel

from orchestrator.script_io import dump_script_yaml, labels_path, script_path
from schemas.models import (
    ProjectManifest,
    ResearchDossier,
    TaskQueueItem,
)
from script.labels import compute_labels
from script.schema import Script
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.prompt_loader import load_prompt


# `.replace()` 만 사용. `.format()` 금지 (C2). script/schema.py 의 Script 와 동기화(parity 테스트).
# system prompt: prompts/script.md / user template: prompts/script_user.md (v2.0.0, 15 P3)


class ScriptWorker(BaseLLMWorker):
    """Script Agent — `Script` 산출.

    출력: `projects/{pid}/script.yaml` + 파생 `script_labels.json`
    """

    worker_name = "script"
    task_type = "script"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    prompt_name: ClassVar[str] = "script"
    response_model: ClassVar[Type[BaseModel]] = Script
    # 긴 원고 1-shot 생성은 기본 타임아웃을 넘기는 경우가 관측됨(실측 526초 성공 / 600초
    # 타임아웃). 값은 config.yaml `llm.script_timeout_sec` (v2.0.0 SSOT).
    invoke_timeout_key: ClassVar[Literal["invoke_timeout_sec", "script_timeout_sec"]] = "script_timeout_sec"

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        """ProjectManifest + research_dossier.json 을 읽어 user prompt 를 구성.

        - manifest / research_dossier 가 없으면 FileNotFoundError 전파 (run() 흡수).
        - 모든 치환은 `.replace()` (C2).
        """
        pdir = self.project_dir(args)

        manifest_path = pdir / "project_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"project_manifest.json 이 없습니다: {manifest_path}")
        manifest = ProjectManifest.model_validate(
            json.loads(manifest_path.read_text(encoding="utf-8"))
        )

        dossier_path = pdir / "04_research" / "research_dossier.json"
        if not dossier_path.exists():
            raise FileNotFoundError(f"research_dossier.json 이 없습니다: {dossier_path}")
        dossier = self._dossier(args)

        claims_block = self._format_claims(dossier)
        topic = dossier.topic or manifest.title

        template = load_prompt("script_user", self.rules)
        return (
            template
            .replace("{project_id}", manifest.project_id)
            .replace("{title}", manifest.title)
            .replace("{topic}", topic)
            .replace("{duration}", str(manifest.target_duration_min))
            .replace("{summary}", dossier.summary or "(요약 없음)")
            .replace("{claims}", claims_block)
        )

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return script_path(args.project_id)

    def _dossier(self, args: argparse.Namespace) -> ResearchDossier:
        p = self.project_dir(args) / "04_research" / "research_dossier.json"
        return ResearchDossier.model_validate(json.loads(p.read_text(encoding="utf-8")))

    def _statuses(self, args: argparse.Namespace) -> dict[str, str]:
        return {c.claim_id: (c.status if isinstance(c.status, str) else c.status.value)
                for c in self._dossier(args).claims}

    def check_parsed(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        """sources ⊂ 도시어 claim_id (D-0043 §1). 위반은 LabelError(ValueError) — 출력 없음."""
        assert isinstance(parsed, Script)
        compute_labels(parsed, self._statuses(args))

    def serialize(self, parsed: BaseModel) -> str:
        assert isinstance(parsed, Script)
        return dump_script_yaml(parsed)

    def after_output(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        """라벨은 코드가 계산해 script_labels.json 으로(D-0043 §2·§3). task.output_refs 에 있어야 한다."""
        assert isinstance(parsed, Script)
        outp = labels_path(args.project_id)
        self._validate_output_path(args, task, outp)
        outp.write_text(compute_labels(parsed, self._statuses(args)).model_dump_json(indent=2), encoding="utf-8")

    @staticmethod
    def _format_claims(dossier: ResearchDossier) -> str:
        """도시어 claim 을 한 줄 1주장 블록으로 직렬화 (status/label/근거 포함)."""
        if not dossier.claims:
            return "  (주장 없음 — 도입/맥락 위주의 짧은 대본을 신중히 작성)"
        lines: list[str] = []
        for c in dossier.claims:
            status = c.status if isinstance(c.status, str) else c.status.value
            src = ",".join(
                e.source_id or (e.seed_id or "?") for e in c.evidence
            ) or "(근거 없음)"
            lines.append(
                f"  - claim_id={c.claim_id} | status={status} "
                f"| confidence={c.confidence} | 근거={src}\n"
                f"      statement: {c.statement}"
            )
        return "\n".join(lines)


if __name__ == "__main__":
    run_worker(ScriptWorker())
