"""ReviseDirectionWorker — 연출 수정 (v3.1.0, docs/handoff/17 §5.5, back_and_forth D-0047 작업 8).

입력: 직전 `direction.yaml` + 최신 `prev/qa_verdict.v*.json` + `prev/checks.json` + 이벤트 필드 표.
출력: `direction.yaml`(수정본) + `direction.v{n}.yaml` + `prev/revision.v{n}.json`(changelog).
검증: 스키마·앵커·레지스트리 + **지적받지 않은 이벤트 불변**(engine.qa.unchanged_violations) — 위반이면 1회 재요청 후 중단.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import ClassVar, Literal, Type

from pydantic import BaseModel

from engine.direction import load_direction_doc
from engine.qa import QAVerdict, Revision, unchanged_violations
from schemas.models import TaskQueueItem
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.direction_io import (
    cards_table,
    check_direction,
    dump_direction_yaml,
    event_fields_table,
    load_plan,
    loop_history,
    next_version,
    plan_table,
)
from workers.prompt_loader import load_prompt
from workers.visual_qa_worker import checks_summary

HEADER = "# direction.yaml — AI 연출 수정본(ReviseDirectionWorker, v3.1.0, 17 §5.5). changelog 는 prev/revision.v*.json.\n"


def latest(pdir: Path, stem: str, suffix: str) -> Path | None:
    """{stem}.v{n}{suffix} 중 번호가 가장 큰 것. 번호는 v1 부터 이어지지 않을 수 있다(수정 기록은 v2 부터)."""
    pat = re.compile(rf"^{re.escape(stem)}\.v(\d+){re.escape(suffix)}$")
    hits = [(int(m.group(1)), p) for p in pdir.glob(f"{stem}.v*{suffix}") if (m := pat.match(p.name))] if pdir.exists() else []
    return max(hits)[1] if hits else None


class ReviseDirectionWorker(BaseLLMWorker):
    worker_name = "revise_direction"
    task_type = "revise_direction"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "response"
    prompt_name: ClassVar[str] = "revise_direction"
    response_model: ClassVar[Type[BaseModel]] = Revision
    retry_on_invalid: ClassVar[int] = 1
    invoke_timeout_key: ClassVar[Literal["invoke_timeout_sec", "script_timeout_sec"]] = "script_timeout_sec"

    def _verdict(self, pdir: Path) -> QAVerdict | None:
        p = latest(pdir / "prev", "qa_verdict", ".json")
        return QAVerdict.model_validate_json(p.read_text(encoding="utf-8")) if p else None

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        pdir = self.project_dir(args)
        doc = load_direction_doc(pdir / "direction.yaml")
        v = self._verdict(pdir)
        return (load_prompt("revise_direction_user", self.rules)
                .replace("{direction}", doc.model_dump_json())
                .replace("{qa_verdict}", v.model_dump_json() if v else "(검수 판정 없음 — checks 오류만 고친다)")
                .replace("{checks}", checks_summary(pdir))
                .replace("{plan_table}", plan_table(load_plan(pdir)))       # D-0049 쟁점 1 — 연출가와 같은 시각표
                .replace("{cards}", cards_table(load_plan(pdir)))
                .replace("{history}", loop_history(pdir))                   # D-0049 쟁점 2 — 같은 루프의 자기 이력
                .replace("{event_fields}", event_fields_table()))

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        return self.project_dir(args) / "direction.yaml"

    def check_parsed(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        assert isinstance(parsed, Revision)
        pdir = self.project_dir(args)
        check_direction(parsed.direction, pdir)
        touched = {c.issue_ref for c in parsed.changelog}
        v = self._verdict(pdir)
        if v is not None:
            touched |= {i.fix.event_ref for i in v.issues if i.fix} | {i.frame for i in v.issues}
        frames, checks = (json.loads(q.read_text(encoding="utf-8")) if q.exists() else None
                          for q in (pdir / "prev" / "frames.json", pdir / "prev" / "checks.json"))
        bad = unchanged_violations(load_direction_doc(pdir / "direction.yaml"), parsed.direction, touched, frames, checks)
        if bad:
            raise ValueError("지적받지 않은 부분을 바꿨다(17 §5.5):\n" + "\n".join(bad[:20]))

    def serialize(self, parsed: BaseModel) -> str:
        assert isinstance(parsed, Revision)
        return dump_direction_yaml(parsed.direction, HEADER)

    def after_output(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        assert isinstance(parsed, Revision)
        pdir = self.project_dir(args)
        n = next_version(pdir, "direction", ".yaml")
        rev = pdir / "prev" / f"revision.v{n}.json"
        for p in (pdir / f"direction.v{n}.yaml", rev):
            self._validate_output_path(args, task, p)
        shutil.copyfile(pdir / "direction.yaml", pdir / f"direction.v{n}.yaml")
        rev.write_text(json.dumps({"schema_version": 1, "direction_version": n,
                                   "changelog": [c.model_dump() for c in parsed.changelog]}, ensure_ascii=False, indent=1),
                       encoding="utf-8")


if __name__ == "__main__":
    run_worker(ReviseDirectionWorker())
