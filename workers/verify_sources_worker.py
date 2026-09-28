"""VerifySourcesWorker — 소스 검증(claim 후보 + 인용) (v3.2.0, docs/handoff/18 §3, back_and_forth D-0051 작업 6, D-0052 D50).

입력: 사용자 확인된 `intake/sources.json` 전부 + 소스 본문(`orchestrator.source_intake.body_text`, untrusted envelope).
출력: `intake/verify_draft.json`(`VerifyDraft`). status 는 LLM 이 매기지 않는다 — `orchestrator.source_verify.judge` 가
인용 대조로 정한다. 인용이 본문에 없거나 길면 계약 위반으로 1회 재요청하고, 그래도 어기면 중단(16 §3, 15 P6).
웹 검색·x.com 접근 없음(response 모드, 18 §1).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import ClassVar, Literal, Type

from pydantic import BaseModel

from schemas.models import TaskQueueItem
from schemas.source_models import ArticleSource, DocumentSource, VerifyDraft, XPostSource
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.prompt_loader import load_prompt
from workers.prompt_safety import wrap_untrusted


class VerifySourcesWorker(BaseLLMWorker):
    worker_name = "verify_sources"
    task_type = "verify_sources"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    prompt_name: ClassVar[str] = "verify_sources"
    response_model: ClassVar[Type[BaseModel]] = VerifyDraft
    retry_on_invalid: ClassVar[int] = 1
    invoke_timeout_key: ClassVar[Literal["invoke_timeout_sec", "script_timeout_sec"]] = "script_timeout_sec"

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        from orchestrator.source_verify import verify_inputs  # noqa: PLC0415

        sources, bodies = verify_inputs(self.project_dir(args))
        cap = self.rules.verification.body_max_chars
        blocks = []
        for s in sources.sources:
            if isinstance(s, XPostSource):
                head = f"[{s.id}] X 게시물 · {s.account_name} {s.handle} · 계정 분류 {s.account_class} · 게시 {s.posted_at}" \
                       + (" · 삭제된 게시물" if s.deleted else "")
            elif isinstance(s, ArticleSource):
                head = f"[{s.id}] 기사 · {s.publisher} · {s.published_at} · 제목 {s.headline_original}"
            else:
                assert isinstance(s, DocumentSource)
                head = f"[{s.id}] 공문·자료 · {s.issuer} · {s.title}"
            body = bodies[s.id]
            if len(body) > cap:
                body = body[:cap] + "\n(잘림)"
            blocks.append(head + "\n" + wrap_untrusted(body, source_label=s.id))
        return (load_prompt("verify_sources_user", self.rules)
                .replace("{quote_max}", str(self.rules.verification.quote_max_chars))
                .replace("{bundle_hints}", self._bundle_hints(args))
                .replace("{sources}", "\n\n".join(blocks)))

    def _bundle_hints(self, args: argparse.Namespace) -> str:
        """`intake/bundle_claims.json` 이 있을 때만 후보 블록(D-0064 쟁점 3). 없으면 빈 자리 — 기존 프로젝트 무영향."""
        from bundle.to_sources import BUNDLE_CLAIMS_FILE, BundleClaimsFile, format_hints  # noqa: PLC0415

        p = self.project_dir(args) / "intake" / BUNDLE_CLAIMS_FILE
        if not p.exists():
            return ""
        f = BundleClaimsFile.model_validate_json(p.read_text(encoding="utf-8"))
        if not f.hints:
            return ""
        return load_prompt("verify_sources_hints", self.rules).replace("{hints}", format_hints(f)) + "\n"

    def check_parsed(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        """코드 판정을 미리 돌려 버려질 근거가 있으면 계약 위반 — 재요청에 그 목록을 붙인다."""
        from orchestrator.source_verify import judge, verify_inputs  # noqa: PLC0415

        sources, bodies = verify_inputs(self.project_dir(args))
        _, drops = judge(parsed, sources, bodies)  # type: ignore[arg-type]
        if drops:
            raise ValueError("인용 대조 실패(인용은 본문의 연속 부분 문자열·상한 이하):\n" + "\n".join(drops[:20]))

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return self.project_dir(args) / "intake" / "verify_draft.json"


if __name__ == "__main__":
    run_worker(VerifySourcesWorker())
