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
from typing import ClassVar, Type

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


# `.replace()` 만 사용. `.format()` 금지 (C2). schemas/models.py 의 FullScript 와 동기화.
_SYSTEM_PROMPT_TEMPLATE = """당신은 OSINT 영상 자동 제작 파이프라인의 Script Agent 입니다.

역할
----
리서치 도시어(주장-근거 페어)를 받아 영상 나레이션 대본(FullScript)을 작성합니다.
챕터 구조를 잡고, 각 챕터를 나레이션 세그먼트(TTS 가 읽을 최소 단위)로 나눕니다.

핵심 원칙
---------
- 모든 나레이션은 리서치 도시어의 claim 에 근거합니다. 각 세그먼트의 claim_refs 에
  근거가 된 claim_id 를 적습니다. 도시어에 없는 새 사실을 지어내지 않습니다.
- claim 의 status 가 confirmed 가 아닌 경우(inferred/claim/unverified/disputed), 그
  내용을 말하는 세그먼트의 label 에 해당 영상 라벨을 박습니다:
  inferred=<추론>, claim=<주장>, unverified=<미검증>, disputed=<반박됨>.
  confirmed 사실만 말하는 세그먼트는 label 을 null 로 둡니다.
- 미검증/추론/주장/반박 내용은 단정적으로 말하지 말고 "~라는 주장이 있다 / ~로 추정된다 /
  아직 확인되지 않았다" 식으로 서술합니다.
- 도입(왜 중요한가) → 핵심 사실 → 맥락/배경 → 미확인 쟁점 → 정리 흐름을 권장합니다.
- 목표 영상 길이에 맞춰 분량을 조절합니다. 한국어 나레이션은 대략 분당 320자 내외로
  가정하고 각 세그먼트의 est_duration_sec 를 추정합니다.

엄격한 출력 규칙
----------------
- 출력은 단 하나의 JSON 객체. 앞뒤 설명·markdown fence·자연어 금지.
- 추가 필드 금지 (extra="forbid"). 아래 스키마의 필드명/타입을 정확히 준수.
- 자연어 문자열은 한국어. 단 id 류(chapter_id, segment_id, claim_id)는 영문 snake_case.

FullScript JSON 스키마
----------------------
{
  "schema_version": 1,
  "project_id": "<주어진 project_id 그대로>",
  "title": "<영상 제목 한국어>",
  "topic": "<영상 1줄 주제>",
  "target_duration_min": <int, 주어진 값 그대로>,
  "chapters": [ ScriptChapter, ... ],     // 3~6개 권장
  "segments": [ ScriptSegment, ... ],     // 챕터당 2~6개
  "total_est_duration_sec": <number>      // 모든 segment est_duration_sec 합과 근사
}

ScriptChapter 스키마
--------------------
{ "chapter_id": "<영문, 예: 'ch_intro'>", "title": "<챕터 제목 한국어>", "summary": "<1문장 요약>" }

ScriptSegment 스키마
--------------------
{
  "segment_id": "<영문, 예: 'seg_01'>",
  "chapter_id": "<위 chapters 의 chapter_id 중 하나>",
  "narration": "<TTS 가 읽을 나레이션 본문 한국어 1~4문장>",
  "on_screen_caption": "<화면에 띄울 짧은 캡션 한국어>",
  "claim_refs": ["<research_dossier 의 claim_id>", ...],
  "label": "<확인>" | "<추론>" | "<주장>" | "<미검증>" | "<반박됨>" | null,
  "est_duration_sec": <number>
}

판단 기준
---------
- claim_refs 는 반드시 입력 도시어에 존재하는 claim_id 만 사용.
- 한 세그먼트가 여러 claim 을 묶을 수 있으나, 미검증 claim 과 confirmed claim 을 한
  세그먼트에 섞지 말고 분리해 라벨을 명확히 합니다.
- 제목(title)에는 미검증/추론 내용을 넣지 않습니다 (확정 사실 기반)."""


class ScriptWorker(BaseLLMWorker):
    """Script Agent — `FullScript` 산출.

    출력: `projects/{pid}/05_script/full_script.json`
    """

    worker_name = "script"
    task_type = "script"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    system_prompt: ClassVar[str] = _SYSTEM_PROMPT_TEMPLATE
    response_model: ClassVar[Type[VersionedModel]] = FullScript

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

        template = (
            "프로젝트 메타데이터\n"
            "-------------------\n"
            "project_id        : {project_id}\n"
            "title             : {title}\n"
            "topic             : {topic}\n"
            "target_duration_min: {duration}\n"
            "\n"
            "리서치 도시어 요약\n"
            "------------------\n"
            "{summary}\n"
            "\n"
            "주장 목록 (claim_id 로 인용 — status/label 을 대본 라벨에 반영)\n"
            "--------------------------------------------------------------\n"
            "{claims}\n"
            "\n"
            "지시\n"
            "----\n"
            "위 도시어를 바탕으로 FullScript JSON 을 생성하십시오.\n"
            "- project_id, target_duration_min 은 위 값 그대로 사용.\n"
            "- chapters 3~6개, 챕터당 segments 2~6개.\n"
            "- 각 segment 의 claim_refs 는 위 주장 목록의 claim_id 만 인용.\n"
            "- confirmed 가 아닌 claim 을 말하는 segment 는 label 에 해당 라벨을 박고\n"
            "  단정적 표현을 피한다 (<미검증>/<추론>/<주장>/<반박됨>).\n"
            "- 출력은 JSON 한 객체. 자연어/설명/markdown fence 일체 금지.\n"
        )
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
