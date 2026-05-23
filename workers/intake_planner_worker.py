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


# ---------------------------------------------------------------------------
# 카테고리별 인테이크 항목 가이드 (docs/04_DYNAMIC_INTAKE_PAGE_SPEC.md §4 와 동기화)
# ---------------------------------------------------------------------------
#
# 각 카테고리에서 planner 가 우선적으로 제안해야 할 표준 항목 카탈로그.
# LLM 이 자유롭게 추가/조정 가능하지만 본 목록은 baseline.
# 변경 시 docs/04 §4 도 함께 갱신.
CATEGORY_GUIDANCE: dict[str, str] = {
    "geopolitics": (
        "지정학 카테고리 표준 항목:\n"
        "- 핵심 사건 / 발표 출처 (정부·국방부·외교부 공식 채널)\n"
        "- 관련 지역 좌표 / 지명 (지도 장면용)\n"
        "- 양측 입장 (해당국 + 상대국 공식 성명)\n"
        "- OSINT 분석가 트윗 / 해외 전문가 견해\n"
        "- 과거 유사 사례 (역사적 맥락)\n"
        "- 에너지·해운 경로 등 인프라 지도\n"
        "- 미검증 주장 (음모론 라벨 필요 항목)"
    ),
    "war_military": (
        "전쟁/군사 카테고리 표준 항목:\n"
        "- 핵심 사건 영상 (X/Telegram 링크, rights_status 기록 필수)\n"
        "- 위치 좌표 / 지명 (전선 지도용)\n"
        "- 공식 발표 (정부·국방부 양측)\n"
        "- OSINT 분석가 트윗 (geolocation 검증 가능)\n"
        "- 과거 유사 작전 사례\n"
        "- 위성 사진 (Maxar/Planet 등)\n"
        "- 무기 체계명 / 식별 정보"
    ),
    "economy": (
        "경제/금융/산업 카테고리 표준 항목:\n"
        "- 핵심 지표 (유가, 환율, 금리, 운임 등)\n"
        "- 시계열 데이터 출처 (Bloomberg/Reuters/공식 통계)\n"
        "- 산업 보고서 (PDF 또는 링크)\n"
        "- 관련 기업 (티커, 시가총액, 사업 영역)\n"
        "- 정책 발표 (중앙은행 / 정부 / 규제 당국)\n"
        "- 공급망 다이어그램 자료"
    ),
    "disinformation": (
        "정보전/해외 음모론 카테고리 표준 항목 (국내 정치/인물은 GOAL.md G2/G5 에서 범위 외):\n"
        "- 원 주장 출처 (누가 처음 퍼뜨렸는가)\n"
        "- 확산 경로 (어느 플랫폼 / 시간순)\n"
        "- 반박 자료 (팩트체크 / 공식 부인)\n"
        "- 검증 / 미검증 상태 (각 주장 단위)\n"
        "- 영상 내 `<미검증>` 라벨이 필요한 항목 표시\n"
        "- 관련 음모론 클러스터 / 변종"
    ),
    "earthquake": (
        "자연재해/지진 카테고리 표준 항목:\n"
        "- 진앙 좌표 / 규모 / 진원 깊이\n"
        "- 발생 시각 (UTC + 현지)\n"
        "- 1차 출처 (USGS / JMA / CWA / CENC / KMA 등)\n"
        "- 여진 추이 (시계열)\n"
        "- 쓰나미 경보 유무 / 영향 해안\n"
        "- 인근 도시 / 인구 노출\n"
        "- 판 경계 / 해구 / 단층 구조\n"
        "- 현장 영상 / CCTV (rights_status 기록)\n"
        "- 피해 사진\n"
        "- 과거 유사 지진 (재현 주기 / 비교군)"
    ),
}


# ---------------------------------------------------------------------------
# system prompt — 공통 골격
# ---------------------------------------------------------------------------
# `.replace()` 만 사용. `.format()` 은 JSON `{}` 와 충돌하므로 금지 (CLAUDE.md C2).
# 본 프롬프트는 schemas/models.py 의 IntakePlan / IntakePlanItem 정의와 동기화되어야 함.
_SYSTEM_PROMPT_TEMPLATE = """당신은 OSINT 영상 자동 제작 파이프라인의 Dynamic Intake Planner 입니다.

역할
----
주제·카테고리·목표 길이를 분석해 영상 제작에 필요한 **인테이크 항목 목록** 을 생성합니다.
사용자는 이 항목 목록을 보고 각 항목별로 자료를 직접 제공할지 / AI Delegation 으로
맡길지 / 생략할지 결정합니다.

엄격한 출력 규칙
----------------
- 출력은 단 하나의 JSON 객체. 앞뒤 설명·markdown fence·자연어 금지.
- 추가 필드 금지 (`extra="forbid"`). 아래 스키마의 필드명/타입을 정확히 준수.
- enum 값은 아래 허용 목록만 사용 (소문자, snake_case 그대로).
- 모든 문자열 필드는 한국어로 (label, description, why_needed, orchestrator_assessment,
  ai_delegate_task, risk_notice). 단 `item_id` 만 영문 snake_case.

IntakePlan JSON 스키마
----------------------
{
  "schema_version": 1,
  "project_id": "<주어진 project_id 그대로>",
  "topic": "<영상 1줄 주제>",
  "category": "<주어진 category 그대로>",
  "target_duration_min": <int>,
  "orchestrator_assessment": "<2~3문장. 본 주제의 핵심 위험과 자료 확보 난이도 요약>",
  "required_items": [ IntakePlanItem, ... ]   // 5~12 항목 권장
}

IntakePlanItem 스키마
---------------------
{
  "item_id": "<영문 snake_case 고유 식별자, 예: 'core_event_video'>",
  "label": "<카드 헤더용 짧은 한국어 라벨>",
  "description": "<항목이 무엇인지 한국어 1~2문장>",
  "why_needed": "<왜 영상 제작에 필요한지 한국어 1문장>",
  "priority": "low" | "normal" | "high" | "must_use",
  "expected_input_types": ["text"|"url"|"video"|"image"|"pdf"|"geojson"|"audio", ...],
  "default_mode": <IntakeMode 한 값>,
  "user_options": [<IntakeMode>, ...],   // 사용자가 선택 가능한 모드들
  "ai_delegate_task": "<AI Delegation 선택 시 worker 가 수행할 작업 한국어 요약>",
  "risk_notice": "<권리/검증 리스크 한국어 안내, 없으면 빈 문자열 또는 null>",
  "status": "pending"
}

IntakeMode 허용 값
------------------
- "direct_provide"   사용자가 텍스트 직접 제공
- "link_provide"     URL 제공
- "gdrive_provide"   Google Drive 링크 제공
- "file_upload"      파일 직접 업로드
- "ai_delegate"      AI worker 가 알아서 수집
- "mixed"            사용자 일부 + AI Delegation
- "skip"             생략
- "must_use"         반드시 사용 (priority 도 must_use 로 승격)
- "reference_only"   참고만 (영상 노출 금지)

판단 기준
---------
- 권리·검증 위험이 큰 자료 (X/Telegram 영상 등) 는 `risk_notice` 에 그 사실을 명시.
- 공식 1차 출처가 존재할 가능성이 높은 항목은 `default_mode="link_provide"`.
- 사용자만 알 수 있는 맥락 (개인적 관심사·국내 영향) 은 `default_mode="direct_provide"`.
- 검색·수집 자동화가 합리적인 항목은 `default_mode="ai_delegate"` 와 `ai_delegate_task` 동시 작성.
- 미검증 주장 / 음모론은 disinformation 카테고리 외에서도 별도 항목으로 분리하고
  `risk_notice` 에 `<미검증>` 라벨 필요성을 명시.
- 모든 항목의 `status` 는 `"pending"` 으로 고정 (사용자 선택 전).

카테고리별 보조 지침은 user prompt 의 "카테고리별 가이드" 절을 참고하십시오."""


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class IntakePlannerWorker(BaseLLMWorker):
    """Dynamic Intake Planner — `IntakePlan` 산출.

    출력: `projects/{pid}/01_intake/intake_plan.json`
    """

    worker_name = "intake_planner"
    task_type = "intake_planning"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    system_prompt: ClassVar[str] = _SYSTEM_PROMPT_TEMPLATE
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

        template = (
            "프로젝트 메타데이터\n"
            "-------------------\n"
            "project_id        : {project_id}\n"
            "title             : {title}\n"
            "category          : {category}\n"
            "target_duration_min: {duration}\n"
            "topic_summary     : {summary}\n"
            "\n"
            "사용자 사전 제공 자료 (manual_user_provided 후보)\n"
            "------------------------------------------------\n"
            "{links}\n"
            "\n"
            "카테고리별 가이드 (참고 baseline, 자유롭게 추가/조정 가능)\n"
            "---------------------------------------------------------\n"
            "{guidance}\n"
            "\n"
            "지시\n"
            "----\n"
            "위 메타데이터를 바탕으로 IntakePlan JSON 을 생성하십시오.\n"
            "- required_items 는 5~12개. 본 주제에 핵심적인 자료부터 우선.\n"
            "- project_id, category, target_duration_min 은 위 값 그대로 사용.\n"
            "- topic 은 title 보다 간결한 1줄 표현 (필요 시 title 그대로 사용).\n"
            "- 사용자 사전 제공 자료가 있으면, 해당 자료로 충족되는 required_item 의\n"
            "  default_mode 를 link_provide 로, why_needed 에 어떤 링크가 관련되는지\n"
            "  명시. 단 사용자 제공 자료라도 사실 검증은 별도로 필요함을 전제로 한다.\n"
            "- 출력은 JSON 한 객체. 자연어/설명/markdown fence 일체 금지.\n"
        )
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
