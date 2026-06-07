"""CompositionPlannerWorker — codex/claude 가 영상 '연출'을 판단하는 계층.

ADDENDUM_04 규약: 모든 LLM 호출은 BaseLLMWorker 를 상속한 Worker 가 subprocess(구독 CLI)로
수행하고, 입력/출력은 projects/{pid}/llm_calls/ 로 영속화된다. 본 워커의 산출물(CompositionPlan)
은 사실이 아니라 **연출 판단**만 담는다 — 사실·차트 데이터는 여전히 번들에서 결정론으로 나온다.

이 환경(클라우드)엔 codex CLI 가 없고 outbound 가 막혀 있어, `backend="stub"` 으로 결정론
stub 플랜을 BaseLLMWorker stub 경로(OSINT_LLM_STUB)로 흘려 전체 파이프라인(검증·소비·렌더)을
증명한다. 실 codex 호출은 사용자 PC 에서 `backend="codex"` 로 동일 코드가 돈다(C10 구도와 동일).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, ClassVar, Optional, Type

from schemas.models import (
    CompositionPlan,
    PlannedCaption,
    PlannedScene,
    ReportBundle,
    TaskQueueItem,
    TaskStatus,
    VersionedModel,
)
from workers.base_llm_worker import BaseLLMWorker


_SYSTEM_PROMPT = """너는 OSINT 데이터 브리핑 영상의 **연출 감독**이다. 입력으로 (1) 이미 검증된
보고서 번들의 핵심 사실과 (2) 결정론으로 펼쳐진 '씬 스켈레톤'(scene_id·종류·현재 헤드라인·
섹션 narration)을 받는다. 너의 일은 **사실을 바꾸는 게 아니라** 그 위에 연출을 얹는 것이다.

산출은 아래 JSON 한 덩어리(CompositionPlan)만. 코드펜스·설명 금지.

규칙(엄수):
- 숫자/수치/날짜는 **번들에 있는 값만** 써라. 파생·과장·추정 숫자를 쓰면 그 텍스트는
  자동으로 화면에서 <미검증> 라벨이 붙는다(그래도 되지만 남발 금지).
- 자막(captions)은 통문단을 그대로 쪼개지 말고, 각 씬에 맞춰 **순차적 key-takeaway** 한 줄씩
  자연스러운 한국어로 재작성. scene_ref 는 해당 씬의 scene_id. order 는 0부터.
- 씬 순서(order), 헤드라인(headline), 강조 단어(emphasis_words), full/strip 역할(role),
  카운트업 숫자(countup_value), 페이싱(duration_sec)을 영상미가 살도록 판단해 채워라.
- scene_id 는 입력 스켈레톤의 값을 그대로 써라(없는 id 는 무시된다).

JSON 형식:
{
  "plan_engine": "codex",
  "title": "<전체 헤드라인 또는 null>",
  "scenes": [
    {"scene_id": "<id>", "order": 0, "headline": "<또는 null>",
     "emphasis_words": ["..."], "role": "full|strip|keep|null",
     "countup_value": "<숫자 문자열 또는 null>", "duration_sec": <숫자 또는 null>}
  ],
  "captions": [
    {"scene_ref": "<scene_id>", "order": 0, "text": "<자막 한 줄>"}
  ],
  "notes": "<연출 의도 메모(렌더 미반영)>"
}"""


class CompositionPlannerWorker(BaseLLMWorker):
    """번들+스켈레톤 → CompositionPlan. 기본 backend codex(연출/구조 판단 강점, ADDENDUM_04 §4.2)."""

    worker_name = "composition_planner"
    task_type = "compose_plan"
    llm_backend: str = "codex"
    llm_mode: ClassVar = "response"
    system_prompt: ClassVar[str] = _SYSTEM_PROMPT
    response_model: ClassVar[Type[VersionedModel]] = CompositionPlan

    # 인스턴스 페이로드(convenience 가 run 전에 주입). build_user_prompt 가 읽는다.
    _payload: ClassVar[str] = ""

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        return self._payload

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return self.project_dir(args) / "compose_plan.json"


# ---------------------------------------------------------------------------
# 스켈레톤·페이로드·stub
# ---------------------------------------------------------------------------


def _skeleton(bundle: ReportBundle) -> list[dict[str, Any]]:
    """결정론 스켈레톤 — 플랜이 매칭할 scene_id 목록(LLM 입력용 + stub 생성용).

    build_composed_scenes 를 plan 없이 호출해 얻는다(소비 함수와 동일 산출이라 scene_id 정합).
    """
    from orchestrator.hyperframes_compose import build_composed_scenes

    out: list[dict[str, Any]] = []
    for sc in build_composed_scenes(bundle):
        out.append({
            "scene_id": sc.scene_id,
            "kind": sc.kind,
            "component": sc.component,
            "section_id": sc.section_id,
            "headline": sc.heading or str(sc.variables.get("takeaway", "")),
        })
    return out


def _facts_digest(bundle: ReportBundle) -> dict[str, Any]:
    """번들의 핵심 사실 발췌(프롬프트용) — 헤드라인/섹션 prose/주장/차트 제목."""
    rep = bundle.report
    return {
        "headline": (rep.headline if rep else ""),
        "dek": (getattr(rep, "dek", "") if rep else ""),
        "sections": [
            {"section_id": s.section_id or f"s{i+1}", "heading": s.heading,
             "prose": s.prose or ""}
            for i, s in enumerate(bundle.sections)
        ],
        "charts": [{"title": c.title, "type": c.type} for c in bundle.charts],
        "claims": [getattr(c, "text", "") for c in (bundle.claims or [])][:30],
    }


def _build_payload(bundle: ReportBundle, skeleton: list[dict[str, Any]]) -> str:
    return (
        "## 씬 스켈레톤(scene_id 를 그대로 써라)\n"
        + json.dumps(skeleton, ensure_ascii=False, indent=2)
        + "\n\n## 번들 핵심 사실(숫자는 여기 있는 값만)\n"
        + json.dumps(_facts_digest(bundle), ensure_ascii=False, indent=2)
    )


def _stub_plan(bundle: ReportBundle, skeleton: list[dict[str, Any]]) -> dict[str, Any]:
    """결정론 stub 플랜 — codex 부재 환경에서 파이프라인 증명용.

    실제 codex 와 달리 '판단'은 단순하지만, 기계 분할과 **다른** 경로(섹션 prose 첫 문장을
    key-takeaway 자막으로, 헤드라인 토큰을 강조로)임을 보여 소비·검증·렌더 전 구간을 탄다.
    """
    import re

    prose_by_sid = {(s.section_id or f"s{i+1}"): (s.prose or "")
                    for i, s in enumerate(bundle.sections)}
    scenes: list[dict[str, Any]] = []
    captions: list[dict[str, Any]] = []
    seen_sid: set[str] = set()
    for idx, sk in enumerate(skeleton):
        emph = [w for w in re.split(r"[\s,·]+", sk["headline"]) if len(w) >= 2][:2]
        scenes.append({
            "scene_id": sk["scene_id"], "order": idx,
            "emphasis_words": emph, "role": "keep",
        })
        sid = sk["section_id"]
        if sid in seen_sid:
            continue
        seen_sid.add(sid)
        sents = [s.strip() for s in re.split(r"(?<=[.?!。])\s+", prose_by_sid.get(sid, "")) if s.strip()]
        for j, sent in enumerate(sents[:3]):
            captions.append({"scene_ref": sk["scene_id"], "order": j, "text": sent})
    return {"plan_engine": "stub", "title": None, "scenes": scenes,
            "captions": captions, "notes": "deterministic stub (no codex in this env)"}


# ---------------------------------------------------------------------------
# 편의 실행기 (compose-hyperframes CLI 가 호출)
# ---------------------------------------------------------------------------


def plan_for_bundle(
    bundle: ReportBundle,
    *,
    project_id: str,
    backend: str = "codex",
    projects_root: str = "projects",
) -> tuple[Optional[CompositionPlan], str]:
    """번들 → 검증 전 CompositionPlan. 실패 시 (None, 사유).

    backend="stub" 이면 결정론 stub 플랜을 BaseLLMWorker stub 경로로 흘린다(codex 불요).
    그 외(codex/claude)는 사용자 머신의 구독 CLI 를 subprocess 로 호출한다.
    """
    skeleton = _skeleton(bundle)
    payload = _build_payload(bundle, skeleton)

    worker = CompositionPlannerWorker()
    worker._payload = payload

    args = argparse.Namespace(
        project_id=project_id, projects_root=projects_root, task_id="compose_plan",
    )
    task = TaskQueueItem(
        task_id="compose_plan", assigned_worker="composition_planner",
        task_type="compose_plan", output_refs=["compose_plan.json"],
    )

    prev_stub = os.environ.get("OSINT_LLM_STUB")
    prev_resp = os.environ.get("OSINT_LLM_STUB_RESPONSE")
    try:
        if backend == "stub":
            worker.llm_backend = "claude"  # CLI_INVOCATION 유효 키(실 호출은 stub 가 가로챔)
            os.environ["OSINT_LLM_STUB"] = "1"
            os.environ["OSINT_LLM_STUB_RESPONSE"] = json.dumps(_stub_plan(bundle, skeleton))
        else:
            worker.llm_backend = backend
        result = worker.run(args, task)
    finally:
        _restore_env("OSINT_LLM_STUB", prev_stub)
        _restore_env("OSINT_LLM_STUB_RESPONSE", prev_resp)

    if result.status != TaskStatus.COMPLETED:
        return None, "; ".join(result.errors) or "planner failed"

    plan_file = (Path(__file__).resolve().parents[1] / projects_root / project_id / "compose_plan.json")
    try:
        data = json.loads(plan_file.read_text(encoding="utf-8"))
        return CompositionPlan.model_validate(data), ""
    except Exception as e:  # noqa: BLE001 — 편의 경계
        return None, f"plan read/validate failed: {e}"


def _restore_env(key: str, prev: Optional[str]) -> None:
    if prev is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = prev
