"""report_bundle 수신/검증 (외부 연동, 계약 v1) — v3.2.0 에서 변환부 삭제(D52).

agents_reviewer 가 emit 한 report_bundle.json 을 `ReportBundle`(extra="forbid")로 fail-closed 검증 로드한다.
옛 변환(`bundle_to_research_dossier`·`bundle_to_source_registry`)은 ResearchDossier·SourceRegistry 와 함께 삭제됐다.
번들 → sources.json·claims.json 변환은 Phase 9(번들 어댑터, 12 §7)에서 복귀한다 — 그때까지 `import-bundle` 은 명시 오류.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from schemas.models import ReportBundle

logger = logging.getLogger(__name__)


def _warn_unknown_top_level(raw: object) -> None:
    """bundle 에 우리 모델이 모르는 top-level 필드가 있으면 로그로 알린다(무시하되 인지).

    관대한 수신자라 모르는 필드는 검증을 통과(무시)하지만, agents_reviewer 가 새 블록을
    추가했음을 운영자가 알아채고 소비할지 결정하도록 surface 한다(예: v5.5.2 의 timeline).
    """
    if not isinstance(raw, dict):
        return
    unknown = sorted(set(raw) - set(ReportBundle.model_fields))
    if unknown:
        logger.warning(
            "report_bundle 에 모델 미정의 top-level 필드(무시됨): %s "
            "— 영상에 쓰려면 schemas/models.py 의 ReportBundle 에 추가하라.",
            unknown,
        )


def load_report_bundle(path: Path) -> ReportBundle:
    """report_bundle.json 을 로드 → `ReportBundle` (fail-closed 검증).

    raise
    -----
    FileNotFoundError
        파일 없음.
    json.JSONDecodeError / pydantic.ValidationError(=ValueError)
        손상/스키마 위반은 건너뛰지 않고 전파.
    """
    if not path.exists():
        raise FileNotFoundError(f"report_bundle 파일이 없습니다: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    _warn_unknown_top_level(raw)
    return ReportBundle.model_validate(raw)
