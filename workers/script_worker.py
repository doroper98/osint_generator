"""ScriptWorker — Phase 6 Script Agent (수직 슬라이스에서 Blueprint 단계 흡수).

`research_dossier.json` (주장-근거) + `ProjectManifest` (제목/주제/목표 길이) 를 읽어
`FullScript` (챕터 + 나레이션 세그먼트) 를 생성하고
`projects/{pid}/05_script/full_script.json` 으로 저장합니다.

수직 슬라이스 결정 (v0.9.0): 별도 6C Blueprint(argument_map/episode_blueprint) 산출물을
만들지 않고, ScriptWorker 가 dossier 에서 곧장 챕터 구조 + 대본을 뽑는다. 깊은
blueprint 모델링은 실물 영상으로 구조를 검증한 뒤로 미룬다.

원칙
----
- `BaseLLMWorker` 상속, `llm_mode="response"` (외부 자료 미접근 → allow_agent_mode 불필요).
- `response_model = FullScript`.
- build_user_prompt 는 `.replace()` 로만 합성 (C2: `.format()` 금지).
- 사용자 질문 금지 (C4). 라벨링: 미검증/추론/주장/반박 주장을 인용하는 세그먼트는
  segment.label 에 해당 라벨(<미검증> 등)을 박는다 (docs/06 §6, GOAL G4).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import ClassVar, Literal, Type

from orchestrator.script_io import full_script_path
from schemas.models import (
    CLAIM_STATUS_LABELS,
    FullScript,
    ProjectManifest,
    ResearchDossier,
    TaskQueueItem,
    VersionedModel,
)
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.prompt_loader import load_prompt


# `.replace()` 만 사용. `.format()` 금지 (C2). schemas/models.py 의 FullScript 와 동기화.
# system prompt: prompts/script.md / user template: prompts/script_user.md (v2.0.0, 15 P3)


class ScriptWorker(BaseLLMWorker):
    """Script Agent — `FullScript` 산출.

    출력: `projects/{pid}/05_script/full_script.json`
    """

    worker_name = "script"
    task_type = "script"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    prompt_name: ClassVar[str] = "script"
    response_model: ClassVar[Type[VersionedModel]] = FullScript
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
        dossier = ResearchDossier.model_validate(
            json.loads(dossier_path.read_text(encoding="utf-8"))
        )

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
        return full_script_path(args.project_id)

    @staticmethod
    def _format_claims(dossier: ResearchDossier) -> str:
        """도시어 claim 을 한 줄 1주장 블록으로 직렬화 (status/label/근거 포함)."""
        if not dossier.claims:
            return "  (주장 없음 — 도입/맥락 위주의 짧은 대본을 신중히 작성)"
        lines: list[str] = []
        for c in dossier.claims:
            status = c.status if isinstance(c.status, str) else c.status.value
            label = CLAIM_STATUS_LABELS.get(status, "<미검증>")
            src = ",".join(
                e.source_id or (e.seed_id or "?") for e in c.evidence
            ) or "(근거 없음)"
            lines.append(
                f"  - claim_id={c.claim_id} | status={status} label={label} "
                f"| confidence={c.confidence} | 근거={src}\n"
                f"      statement: {c.statement}"
            )
        return "\n".join(lines)


if __name__ == "__main__":
    run_worker(ScriptWorker())
