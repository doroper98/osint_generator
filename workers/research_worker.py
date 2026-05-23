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


# ---------------------------------------------------------------------------
# system prompt — 공통 골격
# ---------------------------------------------------------------------------
# `.replace()` 만 사용. `.format()` 은 JSON `{}` 와 충돌하므로 금지 (CLAUDE.md C2).
# 본 프롬프트는 schemas/models.py 의 ResearchDossier 정의와 동기화되어야 함.
_SYSTEM_PROMPT_TEMPLATE = """당신은 OSINT 영상 자동 제작 파이프라인의 Research Agent 입니다.

역할
----
이미 수집된 소스 레지스트리(source_registry)와 사용자가 사전 제공한 리서치 시드를
분석해, 영상 서사의 토대가 될 **주장-근거 페어(ResearchDossier)** 를 정리합니다.
새 자료를 검색하거나 다운로드하지 않습니다 — 주어진 소스 안에서만 작업합니다.

핵심 원칙
---------
- 모든 주장(claim)에는 근거(evidence)를 붙입니다. 근거는 source_registry 의 source_id
  를 인용하거나(1차 자료), 리서치 시드의 seed_id 를 인용합니다(파생 자료).
- 사용자 사전 제공 자료(리서치 시드)는 자체 생성 OSINT 분석 리포트 등 **2차/파생 분석**
  입니다. 사실 앵커가 아니므로 시드만 근거인 주장은 status 를 confirmed 로 두지 말고,
  반드시 1차 출처로 별도 교차검증이 필요함을 전제로 다룹니다(seed 만 근거 → 최대 claim).
- 2개 이상의 독립된 1차 출처가 일치할 때만 cross_checked=true, status=confirmed 가능.
- 근거가 부족하거나 확인 불가한 주장은 status=unverified, 출처가 주장하나 미검증이면
  status=claim, 다른 출처가 반박하면 status=disputed 로 분류합니다. 영상에서 `<미검증>`
  /`<주장>`/`<반박됨>` 라벨로 분리될 항목들입니다.
- 그래픽/권리 위험이 있는 자료를 인용하는 주장은 claim 의 risk_flags 에 명시합니다.

엄격한 출력 규칙
----------------
- 출력은 단 하나의 JSON 객체. 앞뒤 설명·markdown fence·자연어 금지.
- 추가 필드 금지 (`extra="forbid"`). 아래 스키마의 필드명/타입을 정확히 준수.
- enum 값은 아래 허용 목록만 사용 (소문자, snake_case 그대로).
- 모든 자연어 문자열 필드는 한국어로. 단 id 류(claim_id, seed_id, source_id)는 영문.

ResearchDossier JSON 스키마
---------------------------
{
  "schema_version": 1,
  "project_id": "<주어진 project_id 그대로>",
  "topic": "<영상 1줄 주제>",
  "summary": "<2~4문장. 리서치 총평: 핵심 발견과 미확인 영역>",
  "seeds": [ ResearchSeed, ... ],          // 입력의 리서치 시드를 그대로 정리
  "claims": [ ResearchClaim, ... ],        // 8~25개 권장, 핵심 사실부터
  "open_questions": ["<추가 1차 확인이 필요한 질문 한국어>", ...]
}

ResearchSeed 스키마
-------------------
{
  "seed_id": "<영문 snake_case, 예: 'seed_1'>",
  "url": "<주어진 시드 URL 그대로>",
  "description": "<해당 시드가 무엇인지 한국어 1문장>",
  "is_derivative": true,                   // 사용자 제공 분석 리포트는 파생이므로 true
  "requires_verification": true
}

ResearchClaim 스키마
--------------------
{
  "claim_id": "<영문 snake_case 고유 식별자, 예: 'claim_01'>",
  "statement": "<주장 본문 한국어 1~2문장>",
  "status": "confirmed" | "inferred" | "claim" | "unverified" | "disputed",
  "evidence": [ Evidence, ... ],           // 최소 1개 권장 (unverified 는 0개 가능)
  "cross_checked": <bool>,                 // 2개 이상 독립 1차 출처 일치 시 true
  "confidence": "low" | "medium" | "high",
  "notes": "<검증 메모/한계 한국어, 없으면 빈 문자열>",
  "risk_flags": ["graphic_content", ...]   // 없으면 []
}

Evidence 스키마
---------------
{
  "source_id": "<source_registry 의 source_id, 시드 근거면 null>",
  "seed_id": "<ResearchSeed 의 seed_id, registry 근거면 null>",
  "quote": "<근거가 되는 구체 인용/요약 한국어>",
  "locator": "<페이지/타임스탬프/문단 등 위치, 없으면 null>",
  "stance": "supports" | "refutes" | "contextual"
}

판단 기준
---------
- source_id 는 반드시 입력으로 주어진 source_registry 의 값만 인용 (없는 id 지어내기 금지).
- seed_id 는 위 seeds 에 정의한 값만 인용.
- 한 주장이 시드 근거뿐이면 status 는 confirmed/inferred 가 아니라 claim 또는
  unverified 로 두고, notes 에 1차 검증 필요를 적습니다.
- 신뢰도 낮은(reliability) 또는 권리 미확보(rights) 소스에 의존하는 주장은 confidence 를
  낮추고 notes 에 사유를 적습니다."""


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class ResearchWorker(BaseLLMWorker):
    """Research Agent — `ResearchDossier` 산출.

    출력: `projects/{pid}/04_research/research_dossier.json`
    """

    worker_name = "research"
    task_type = "research"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    system_prompt: ClassVar[str] = _SYSTEM_PROMPT_TEMPLATE
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

        template = (
            "프로젝트 메타데이터\n"
            "-------------------\n"
            "project_id        : {project_id}\n"
            "title             : {title}\n"
            "category          : {category}\n"
            "target_duration_min: {duration}\n"
            "topic_summary     : {summary}\n"
            "\n"
            "사용 가능 소스 (source_registry — 인용 시 source_id 사용)\n"
            "--------------------------------------------------------\n"
            "{sources}\n"
            "\n"
            "리서치 시드 (사용자 사전 제공 = 2차/파생 분석, 사실 앵커 아님)\n"
            "-------------------------------------------------------------\n"
            "{seeds}\n"
            "\n"
            "지시\n"
            "----\n"
            "위 소스와 시드를 바탕으로 ResearchDossier JSON 을 생성하십시오.\n"
            "- project_id, topic 은 위 메타데이터 기준.\n"
            "- claims 는 8~25개. 본 주제의 핵심 사실부터 우선.\n"
            "- evidence.source_id 는 위 source_registry 에 실제 존재하는 값만 인용.\n"
            "- 시드(seed) 만 근거인 주장은 status 를 confirmed 로 두지 말고 claim/unverified\n"
            "  로 분류하고, 1차 출처로 별도 검증이 필요함을 notes 에 명시.\n"
            "- 미확인/반박/추론 항목은 status 로 구분 (<미검증>/<반박됨>/<추론> 라벨 대상).\n"
            "- 출력은 JSON 한 객체. 자연어/설명/markdown fence 일체 금지.\n"
        )
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
