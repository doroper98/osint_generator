"""IntakePlannerWorker — Phase 3 의 첫 도메인 LLM worker.

ProjectManifest 의 사용자 입력 (title, category, target_duration_min, topic_summary)
을 읽어 `IntakePlan` 을 생성하고 `projects/{pid}/01_intake/intake_plan.json` 으로
저장합니다. 외부 자료는 읽지 않으므로 `llm_mode="response"` 이며 `allow_agent_mode`
는 기본값 (False) 유지 — LLM-AP-003 우회.

원칙
----
- `BaseLLMWorker` 상속. CLI 호출은 backend/mode 매핑이 책임.
- `response_model = IntakePlan` (schemas/models.py).
- system_prompt 는 공통 골격 + IntakePlan JSON schema 강제. 카테고리별 guidance 는
  `build_user_prompt` 에서 `.replace()` 로 합성 (CLAUDE.md C2: `.format()` 금지).
- output_path 는 항상 project_dir 안 (`_validate_output_path` 가드가 강제).

backend 전환
-----------
기본값은 `claude` (한국어 지시 이해 우수). codex 로 바꾸려면 인스턴스 생성 시
`llm_backend = "codex"` 만 override 하면 됩니다. JSONL stream unwrap 은 v0.2.4
부터 정식 지원 (LLM-AP-002 resolved).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import ClassVar, Type

from schemas.models import (
    Category,
    IntakePlan,
    ProjectManifest,
    TaskQueueItem,
    VersionedModel,
)
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.prompt_loader import load_prompt, load_prompt_data


# ---------------------------------------------------------------------------
# 프롬프트 — v2.0.0 부터 코드 상수가 아니라 파일에서 로드 (docs/handoff/15 P3)
# ---------------------------------------------------------------------------
# system prompt : prompts/intake_planner.md
# user template : prompts/intake_planner_user.md
# 카테고리 가이드: prompts/intake_planner_category_guidance.yaml
#   (docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md §4 와 동기화)
CATEGORY_GUIDANCE: dict[str, str] = load_prompt_data("intake_planner_category_guidance")


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class IntakePlannerWorker(BaseLLMWorker):
    """Dynamic Intake Planner — `IntakePlan` 산출.

    출력: `projects/{pid}/01_intake/intake_plan.json`
    """

    worker_name = "intake_planner"
    task_type = "intake"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    prompt_name: ClassVar[str] = "intake_planner"
    response_model: ClassVar[Type[VersionedModel]] = IntakePlan

    # 클래스 변수로 노출해 단위 테스트와 외부 도구에서 직접 확인 가능.
    CATEGORY_GUIDANCE: ClassVar[dict[str, str]] = CATEGORY_GUIDANCE

    # -----------------------------------------------------------------
    # BaseLLMWorker 추상 메서드
    # -----------------------------------------------------------------

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        """ProjectManifest 를 읽어 user prompt 를 구성합니다.

        - manifest 가 없으면 `FileNotFoundError` 를 그대로 전파 (run() 의 try 가 흡수).
        - category 의 enum/문자열 모두 안전하게 처리.
        - 모든 치환은 `.replace()` (CLAUDE.md C2 — `.format()` 금지).
        - manifest 파일 경로는 `BaseWorker.project_dir(args)` 가 책임지므로
          `args.projects_root` (단위 테스트의 임시 디렉토리 포함) 가 그대로 존중됨.
        """
        manifest_path = self.project_dir(args) / "project_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"project_manifest.json 이 없습니다: {manifest_path}"
            )
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = ProjectManifest.model_validate(raw)
        category = manifest.category
        category_str = category.value if isinstance(category, Category) else str(category)
        guidance = self.CATEGORY_GUIDANCE.get(
            category_str,
            "(해당 카테고리의 표준 가이드가 등록되지 않았습니다. 일반 OSINT 원칙에 따라 항목을 도출하십시오.)",
        )
        topic_summary = manifest.topic_summary or "(요약 미입력 — title 기반으로 추론하십시오)"

        # 사용자가 생성 시 제공한 자료 링크. 한 줄에 하나씩 번호를 매겨 prompt 에 노출.
        if manifest.initial_links:
            links_block = "\n".join(
                f"  {i}. {link}" for i, link in enumerate(manifest.initial_links, start=1)
            )
        else:
            links_block = "  (사용자가 사전 제공한 링크 없음)"

        template = load_prompt("intake_planner_user", self.rules)
        return (
            template
            .replace("{project_id}", manifest.project_id)
            .replace("{title}", manifest.title)
            .replace("{category}", category_str)
            .replace("{duration}", str(manifest.target_duration_min))
            .replace("{summary}", topic_summary)
            .replace("{links}", links_block)
            .replace("{guidance}", guidance)
        )

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return self.project_dir(args) / "01_intake" / "intake_plan.json"


if __name__ == "__main__":
    run_worker(IntakePlannerWorker())
