"""VisualQAWorker — 시각 검수 (v3.1.0, docs/handoff/17 §4, back_and_forth D-0047 작업 8).

입력: `prev/sheet.jpg`(이미지 — `claude -p` Read 로 연다, D-0047 §0-3) + `prev/frames.json` + `prev/checks.json` 요약.
출력: `prev/qa_verdict.v{n}.json`(QAVerdict). 검수자는 연출 파일을 고치지 않는다(AP-V6-11).
판정·코멘트는 프롬프트·규칙에 자동 반영하지 않는다(15 P11).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import ClassVar, Literal, Type

from pydantic import BaseModel

from engine.qa import QAVerdict
from schemas.models import TaskQueueItem
from workers.base_llm_worker import BaseLLMWorker
from workers.base_worker import run_worker
from workers.direction_io import next_version
from workers.prompt_loader import load_prompt


def checks_summary(pdir: Path) -> str:
    c = json.loads((pdir / "prev" / "checks.json").read_text(encoding="utf-8"))
    rows = [f"- {i['id']} ({i['severity']}): {i['count']}" + (f" — {i['details'][:3]}" if i["count"] else "") for i in c["items"]]
    return f"hard {c['hard']} · warning {c['warnings']}\n" + "\n".join(rows)


def press_lead_empty(v: QAVerdict, pdir: Path, exempt: list[str]) -> list[str]:
    """empty 지적 중 기사 프레스 단독 구간 컷(frames.json article phase "press_lead")의 frame 목록(v5.1.0 D-0127 §5).
    조용히 버리지 않고 워커가 재요청한다(15 P6)."""
    if "article_press_lead" not in exempt:
        return []
    fp = pdir / "prev" / "frames.json"
    frames = json.loads(fp.read_text(encoding="utf-8"))["frames"] if fp.exists() else []
    lead = {Path(f["file"]).stem for f in frames
            if any(e.get("type") == "article" and e.get("phase") == "press_lead" for e in f["events"])}
    return [i.frame for i in v.issues if i.category == "empty" and i.frame in lead]


class VisualQAWorker(BaseLLMWorker):
    worker_name = "visual_qa"
    task_type = "visual_qa"

    llm_backend: str = "claude"
    llm_mode: ClassVar[str] = "vision"
    prompt_name: ClassVar[str] = "visual_qa"
    response_model: ClassVar[Type[BaseModel]] = QAVerdict
    retry_on_invalid: ClassVar[int] = 1
    invoke_timeout_key: ClassVar[Literal["invoke_timeout_sec", "script_timeout_sec"]] = "script_timeout_sec"

    def attachments(self, args: argparse.Namespace, task: TaskQueueItem) -> list[Path]:
        return [self.project_dir(args) / "prev" / "sheet.jpg"]

    def build_user_prompt(self, args: argparse.Namespace, task: TaskQueueItem) -> str:
        pdir = self.project_dir(args)
        imgs = "\n".join(f"- {p.resolve()}  (Read 도구로 연다)" for p in self.attachments(args, task))
        frames = json.loads((pdir / "prev" / "frames.json").read_text(encoding="utf-8"))
        return (load_prompt("visual_qa_user", self.rules)
                .replace("{images}", imgs)
                .replace("{frames}", json.dumps(frames["frames"], ensure_ascii=False))
                .replace("{checks}", checks_summary(pdir)))

    def check_parsed(self, args: argparse.Namespace, task: TaskQueueItem, parsed: BaseModel) -> None:
        """장르 루브릭(v4.4.0 D-0090 작업 1, 20 §9): 기본 장르가 아니면 rules genre_prompt.rubric_extra 항목마다 판정 한 번."""
        assert isinstance(parsed, QAVerdict)
        bad_empty = press_lead_empty(parsed, self.project_dir(args), self.rules.qa_checks.empty_exempt)
        if bad_empty:
            raise ValueError(f"empty 지적 {bad_empty} 은 기사 프레스 단독 구간(article phase press_lead) 컷이다 — "
                             "규약상 비어 보이는 순간이라 empty 로 지적하지 않는다(rules qa_checks.empty_exempt)")
        g = self.genre
        if g is None or g.genre == self.rules.genre_prompt.base_genre:
            if parsed.rubric:
                raise ValueError("기본 장르 검수에 rubric[] 이 있다 — 장르 루브릭은 장르 영상에서만")
            return
        bad = parsed.rubric_missing(len(self.rules.genre_prompt.rubric_extra))
        if bad:
            raise ValueError(f"장르 루브릭 항목 {bad} 의 판정이 없거나 중복이다 — 1~{len(self.rules.genre_prompt.rubric_extra)} 각각 한 번")

    def output_path(self, args: argparse.Namespace, task: TaskQueueItem) -> Path:
        pdir = self.project_dir(args)
        return pdir / "prev" / f"qa_verdict.v{next_version(pdir / 'prev', 'qa_verdict', '.json')}.json"


if __name__ == "__main__":
    run_worker(VisualQAWorker())
