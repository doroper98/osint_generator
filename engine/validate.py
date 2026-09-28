"""연출 점검 CLI (v3.1.0, docs/handoff/17 §1 `engine.validate`, 16 §4 direction_validate 계약).

    python -m engine.validate <proj>   → 마지막 줄 StageResult(stage="validate")

direction.yaml 을 렌더 입력과 **같은 경로**(engine.project.load_project)로 읽는다: 스키마·앵커·레지스트리(15 P10)·
엔티티·배치 슬롯·예약 영역. 렌더는 하지 않는다 — 프레임이 필요한 검사(겹침·화면 밖·글리프)는 preview 의 checks.json.
원고 린트(script.lint)와 별개 단계다: 게이트 ① 원고 린트는 연출 파일이 없을 때도 돈다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.project import ProjectError, load_project
from engine.registry import RegistryError
from schemas.engine_models import StageResult


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="engine.validate")
    ap.add_argument("proj", type=Path)
    args = ap.parse_args(argv)
    try:
        P = load_project(args.proj.resolve())  # noqa: N806
        feats = {"camera_keys": len(P.keys), "events": len(P.events), "frames": P.n_frames}
        res = StageResult(ok=True, stage="validate", artifacts={"direction": str(P.root / "direction.yaml"),
                                                                "summary": json.dumps(feats)}, warnings=P.warnings)
    except (ProjectError, RegistryError, RuntimeError, OSError, ValueError) as ex:
        res = StageResult(ok=False, stage="validate", errors=[str(ex)])
    print(json.dumps(res.model_dump(), ensure_ascii=False))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
