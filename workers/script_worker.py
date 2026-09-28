"""ScriptWorker — 원고 작성 (v3.0.0, 16 §3 개조, back_and_forth D-0040 작업 5·D-0043 → v3.2.0 D-0051 작업 7).

`facts.json`(사실 목록) + `intake/claims.json`(검증 status) + `ProjectManifest` (제목/주제/목표 길이) 를 읽어
`script.schema:Script`(장면 자유 구성, 자막 text / 발음 tts 분리, sources) 를 생성하고
`projects/{pid}/script.yaml` 로 저장합니다. 옛 FullScript(챕터·세그먼트)는 삭제(15 P2).

원칙
----
- `BaseLLMWorker` 상속, `llm_mode="response"` (외부 자료 미접근 → allow_agent_mode 불필요).
- `response_model = Script`. 저장은 YAML(사람이 고친다).
- build_user_prompt 는 `.replace()` 로만 합성 (C2: `.format()` 금지).
- 사용자 질문 금지 (C4).
- **검증 라벨은 LLM 이 쓰지 않는다**(D-0043, 15 P8). 문장 `sources` = claims.json claim_id 만 —
  밖 id 는 check_parsed 오류. 라벨은 코드(script/labels)가 claims status 로 계산해
  `script_labels.json` 에 저장한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import ClassVar, Literal, Type

from pydantic import BaseModel

from orchestrator.script_io import dump_script_yaml, labels_path, script_path
from schemas.models import ProjectManifest, TaskQueueItem
from schemas.source_models import ClaimsFile
from script.labels import compute_labels
from script.schema import Facts, Script
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.prompt_loader import load_prompt

DRAFT_FILE = "script.draft.yaml"   # bundle.to_script 초안(v3.5.0) — 있으면 {draft_block}
META_FILE = "script.meta.json"     # 초안 사용 기록(provenance bundle.draft_used)


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
    retry_on_invalid: ClassVar[int] = 1      # v3.2.0 — claims 밖 id 등 계약 위반은 1회 재요청(16 §3)
    # 긴 원고 1-shot 생성은 기본 타임아웃을 넘기는 경우가 관측됨(실측 526초 성공 / 600초
    # 타임아웃). 값은 config.yaml `llm.script_timeout_sec` (v2.0.0 SSOT).
    invoke_timeout_key: ClassVar[Literal["invoke_timeout_sec", "script_timeout_sec"]] = "script_timeout_sec"

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        """ProjectManifest + facts.json + claims.json → user prompt. 없으면 FileNotFoundError(run() 흡수). `.replace()` 만(C2)."""
        pdir = self.project_dir(args)
        manifest_path = pdir / "project_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"project_manifest.json 이 없습니다: {manifest_path}")
        manifest = ProjectManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
        facts = self._facts(args)
        template = load_prompt("script_user", self.rules)
        return (
            template
            .replace("{project_id}", manifest.project_id)
            .replace("{title}", manifest.title)
            .replace("{topic}", manifest.topic_summary or manifest.title)
            .replace("{duration}", str(manifest.target_duration_min))
            .replace("{draft_block}", self._draft_block(args))
            .replace("{facts}", self._format_facts(facts, self._claims(args)))
        )

    def _draft_block(self, args: argparse.Namespace) -> str:
        """`script.draft.yaml`(번들 어댑터 초안)이 있을 때만 다듬기 블록(v3.5.0 D-0064 쟁점 4). 없으면 빈 자리 — 기존 프로젝트 무영향.
        초안은 이 프로젝트의 입력 재료다(15 P9 의 이전 영상·옛 템플릿이 아님)."""
        p = self.project_dir(args) / DRAFT_FILE
        if not p.exists():
            return ""
        return load_prompt("script_draft", self.rules).replace("{draft}", p.read_text(encoding="utf-8").rstrip()) + "\n"

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return script_path(args.project_id)

    def _facts(self, args: argparse.Namespace) -> Facts:
        p = self.project_dir(args) / "facts.json"
        if not p.exists():
            raise FileNotFoundError(f"facts.json 이 없습니다: {p} — build-research 먼저")
        return Facts.model_validate_json(p.read_text(encoding="utf-8"))

    def _claims(self, args: argparse.Namespace) -> ClaimsFile:
        p = self.project_dir(args) / "intake" / "claims.json"
        if not p.exists():
            raise FileNotFoundError(f"claims.json 이 없습니다: {p}")
        return ClaimsFile.model_validate_json(p.read_text(encoding="utf-8"))

    def _statuses(self, args: argparse.Namespace) -> dict[str, str]:
        return {c.claim_id: c.status for c in self._claims(args).claims}

    def check_parsed(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        """sources ⊂ claims.json claim_id (D-0043 §1). 위반은 LabelError(ValueError) — 출력 없음(재요청 대상)."""
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
        # v3.5.0 — 초안 블록을 받았는지 기록(provenance bundle.draft_used, D-0064 쟁점 4). 초안 없으면 draft_sha1 null
        meta = self.project_dir(args) / META_FILE
        self._validate_output_path(args, task, meta)
        dp = self.project_dir(args) / DRAFT_FILE
        meta.write_text(json.dumps({"schema_version": 1, "worker": self.worker_name,
                                    "draft_sha1": hashlib.sha1(dp.read_bytes()).hexdigest() if dp.exists() else None},
                                   indent=1), encoding="utf-8")

    @staticmethod
    def _format_facts(facts: Facts, claims: ClaimsFile) -> str:
        """사실 한 줄 + 인용할 claim_id 와 그 status(귀속 표현 판단용)."""
        st = {c.claim_id: c.status for c in claims.claims}
        rows = []
        for f in facts.facts:
            cl = ", ".join(f"{c}({st.get(c, '?')})" for c in f.source_ids)
            side = "" if not f.sides else " | 양측: " + " / ".join(f.sides)
            rows.append(f"  - {f.id} | 날짜 {f.date or '-'} | 인용 claim: {cl}{side}\n      {f.text}")
        return "\n".join(rows)

if __name__ == "__main__":
    run_worker(ScriptWorker())
