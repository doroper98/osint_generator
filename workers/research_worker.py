"""ResearchWorker — Phase 6A 의 Research Agent.

`source_registry.json` (사용 가능 소스) + `ProjectManifest.initial_links` (리서치 시드)
를 읽어 `ResearchDossier` 를 생성하고 `projects/{pid}/04_research/research_dossier.json`
으로 저장합니다. 외부 자료를 직접 다운로드하지 않고 이미 수집된 registry 만 다루므로
`llm_mode="response"` 이며 `allow_agent_mode` 는 기본값(False) 유지 (LLM-AP-003 우회).

원칙
----
- `BaseLLMWorker` 상속. CLI 호출은 backend/mode 매핑이 책임.
- `response_model = ResearchDossier` (schemas/models.py).
- system_prompt 는 ResearchDossier JSON schema 강제. 입력 데이터 합성은
  `build_user_prompt` 에서 `.replace()` 로만 수행 (CLAUDE.md C2: `.format()` 금지).
- 사용자에게 질문하지 않는다 (C4). 판단이 필요하면 dossier 의 open_questions /
  claim.notes 에 남긴다.
- output_path 는 항상 project_dir 안 (`_validate_output_path` 가드가 강제).

backend 전환
-----------
기본값은 `claude` (한국어 지시 이해 우수). codex 로 바꾸려면 인스턴스 생성 시
`llm_backend = "codex"` 만 override.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import ClassVar, Type

from orchestrator.research_io import research_dossier_path
from schemas.models import (
    Category,
    ProjectManifest,
    ResearchDossier,
    SourceRegistry,
    TaskQueueItem,
    VersionedModel,
)
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.prompt_loader import load_prompt


# ---------------------------------------------------------------------------
# system prompt — 공통 골격
# ---------------------------------------------------------------------------
# `.replace()` 만 사용. `.format()` 은 JSON `{}` 와 충돌하므로 금지 (CLAUDE.md C2).
# 본 프롬프트는 schemas/models.py 의 ResearchDossier 정의와 동기화되어야 함.
# system prompt: prompts/research.md / user template: prompts/research_user.md (v2.0.0, 15 P3)


class ResearchWorker(BaseLLMWorker):
    """Research Agent — `ResearchDossier` 산출.

    출력: `projects/{pid}/04_research/research_dossier.json`
    """

    worker_name = "research"
    task_type = "research"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    prompt_name: ClassVar[str] = "research"
    response_model: ClassVar[Type[VersionedModel]] = ResearchDossier

    # -----------------------------------------------------------------
    # BaseLLMWorker 추상 메서드
    # -----------------------------------------------------------------

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        """ProjectManifest + source_registry.json 을 읽어 user prompt 를 구성합니다.

        - manifest / source_registry 가 없으면 `FileNotFoundError` 전파 (run() 흡수).
        - 모든 치환은 `.replace()` (CLAUDE.md C2 — `.format()` 금지).
        - source_registry 의 각 소스를 인용 가능한 형태(source_id + 권리/신뢰도)로 노출.
        - initial_links 는 리서치 시드로 번호를 매겨 노출 (파생 자료임을 명시).
        """
        pdir = self.project_dir(args)

        manifest_path = pdir / "project_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"project_manifest.json 이 없습니다: {manifest_path}"
            )
        manifest = ProjectManifest.model_validate(
            json.loads(manifest_path.read_text(encoding="utf-8"))
        )

        registry_path = pdir / "02_sources" / "source_registry.json"
        if not registry_path.exists():
            raise FileNotFoundError(
                f"source_registry.json 이 없습니다: {registry_path}"
            )
        registry = SourceRegistry.model_validate(
            json.loads(registry_path.read_text(encoding="utf-8"))
        )

        category = manifest.category
        category_str = (
            category.value if isinstance(category, Category) else str(category)
        )
        topic_summary = (
            manifest.topic_summary
            or "(요약 미입력 — title 기반으로 추론하십시오)"
        )

        sources_block = self._format_sources(registry)
        seeds_block = self._format_seeds(manifest.initial_links)

        template = load_prompt("research_user", self.rules)
        return (
            template
            .replace("{project_id}", manifest.project_id)
            .replace("{title}", manifest.title)
            .replace("{category}", category_str)
            .replace("{duration}", str(manifest.target_duration_min))
            .replace("{summary}", topic_summary)
            .replace("{sources}", sources_block)
            .replace("{seeds}", seeds_block)
        )

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return research_dossier_path(args.project_id)

    # -----------------------------------------------------------------
    # prompt 빌딩 헬퍼 (순수 — 단위 테스트 가능)
    # -----------------------------------------------------------------

    @staticmethod
    def _format_sources(registry: SourceRegistry) -> str:
        """source_registry 를 인용 가능한 한 줄 1소스 블록으로 직렬화."""
        if not registry.sources:
            return "  (사용 가능한 소스 없음 — 시드/일반 지식 기반으로 신중히 작성하고 미검증 항목을 명확히 라벨링)"
        lines: list[str] = []
        for s in registry.sources:
            rights = s.rights_status if isinstance(s.rights_status, str) else s.rights_status.value
            title = s.title or "(제목 없음)"
            lines.append(
                f"  - source_id={s.source_id} | platform={s.platform} | type={s.source_type} "
                f"| rights={rights} | reliability={s.reliability_score} "
                f"| verification={s.verification_status} | title={title}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_seeds(initial_links: list[str]) -> str:
        """initial_links 를 seed_N 번호와 함께 노출 (LLM 이 seed_id 로 그대로 사용)."""
        if not initial_links:
            return "  (사용자가 사전 제공한 리서치 시드 없음)"
        return "\n".join(
            f"  - seed_id=seed_{i} | url={link}"
            for i, link in enumerate(initial_links, start=1)
        )


if __name__ == "__main__":
    run_worker(ResearchWorker())
