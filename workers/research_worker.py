"""ResearchWorker — 검증된 주장(claims.json)으로 사실 목록(Facts)을 만든다 (v3.2.0, docs/handoff/17 §5.1, back_and_forth D-0051 작업 7, D47·D52).

입력: `project_manifest.json`(요청 요지) + `intake/sources.json`(소스 요약) + `intake/claims.json`(코드가 판정한 status).
출력: `facts.json`(`script.schema:Facts`). 모든 사실의 `source_ids` 는 claims.json 의 claim_id 만(밖 = 계약 위반, 재요청 1회).
분쟁 claim 을 인용한 사실은 `contested: true` + 양측(sides) — 한쪽 입장만으로 서술하지 않는다(18 §3-5).
웹 검색·x.com 접근 없음(response 모드). 옛 ResearchDossier·research_io 는 삭제(P2, D52).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import ClassVar, Literal, Type

from pydantic import BaseModel

from schemas.models import Category, ProjectManifest, TaskQueueItem
from schemas.source_models import ClaimsFile, SourcesFile, XPostSource
from script.schema import Facts
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.prompt_loader import load_prompt

FACTS_FILENAME = "facts.json"


def load_claims_file(pdir: Path) -> ClaimsFile:
    p = pdir / "intake" / "claims.json"
    if not p.exists():
        raise FileNotFoundError(f"claims.json 이 없습니다: {p} — 소스 검증(verify-sources) 먼저")
    return ClaimsFile.model_validate_json(p.read_text(encoding="utf-8"))


def check_facts(facts: Facts, claims: ClaimsFile) -> list[str]:
    """source_ids ⊆ claim id, 분쟁 claim 을 인용한 사실은 contested(+sides, 모델이 강제)."""
    have = claims.by_id()
    errs: list[str] = []
    for f in facts.facts:
        miss = [s for s in f.source_ids if s not in have]
        if miss:
            errs.append(f"{f.id}: claims.json 밖 id {miss}")
        if not f.contested and any(have[s].contested for s in f.source_ids if s in have):
            errs.append(f"{f.id}: 분쟁 claim({[s for s in f.source_ids if s in have and have[s].contested]})을 인용했는데 contested 가 아니다")
    return errs


class ResearchWorker(BaseLLMWorker):
    worker_name = "research"
    task_type = "research"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    prompt_name: ClassVar[str] = "research"
    response_model: ClassVar[Type[BaseModel]] = Facts
    retry_on_invalid: ClassVar[int] = 1
    invoke_timeout_key: ClassVar[Literal["invoke_timeout_sec", "script_timeout_sec"]] = "script_timeout_sec"

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        pdir = self.project_dir(args)
        mp = pdir / "project_manifest.json"
        if not mp.exists():
            raise FileNotFoundError(f"project_manifest.json 이 없습니다: {mp}")
        manifest = ProjectManifest.model_validate(json.loads(mp.read_text(encoding="utf-8")))
        sp = pdir / "intake" / "sources.json"
        sources = SourcesFile.model_validate_json(sp.read_text(encoding="utf-8")) if sp.exists() else SourcesFile()
        claims = load_claims_file(pdir)
        cat = manifest.category.value if isinstance(manifest.category, Category) else str(manifest.category)
        return (load_prompt("research_user", self.rules)
                .replace("{project_id}", manifest.project_id)
                .replace("{title}", manifest.title)
                .replace("{category}", cat)
                .replace("{duration}", str(manifest.target_duration_min))
                .replace("{summary}", manifest.topic_summary or "(요약 미입력)")
                .replace("{sources}", self._format_sources(sources))
                .replace("{claims}", self._format_claims(claims)))

    def check_parsed(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        assert isinstance(parsed, Facts)
        errs = check_facts(parsed, load_claims_file(self.project_dir(args)))
        if errs:
            raise ValueError("사실 목록 계약 위반:\n" + "\n".join(errs[:20]))

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return self.project_dir(args) / FACTS_FILENAME

    @staticmethod
    def _format_sources(sources: SourcesFile) -> str:
        if not sources.sources:
            return "  (소스 없음)"
        rows = []
        for s in sources.sources:
            if isinstance(s, XPostSource):
                rows.append(f"  - {s.id} | X 게시물 | {s.account_name} {s.handle} | {s.account_class} | {s.posted_at}")
            elif s.type == "article":
                rows.append(f"  - {s.id} | 기사 | {s.publisher} | {s.published_at} | {s.headline_original}")
            else:
                rows.append(f"  - {s.id} | 공문·자료 | {s.issuer} | {s.title}")
        return "\n".join(rows)

    @staticmethod
    def _format_claims(claims: ClaimsFile) -> str:
        rows = []
        for c in claims.claims:
            side = "" if not c.sides else " | 양측: " + " / ".join(f"{sd.party}: {sd.text}" for sd in c.sides)
            rows.append(f"  - claim_id={c.claim_id} | status={c.status} | contested={str(c.contested).lower()}"
                        f" | 사건일={c.event_date or '-'} | 소스={','.join(c.source_ids)}{side}\n      {c.text}")
        return "\n".join(rows)


if __name__ == "__main__":
    run_worker(ResearchWorker())
