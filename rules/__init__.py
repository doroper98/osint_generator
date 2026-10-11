"""영상 규칙 SSOT 로더 (v2.0.0, docs/handoff/15 §3 P3).

코드·프롬프트·린트·검증기가 모두 `rules/video_rules.yaml` 한 파일을 읽는다.
규칙 값을 모듈 상수로 다시 적지 않는다 (tests/anti_inertia/test_single_config).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from schemas.feedback_models import FeedbackLedger
from schemas.rules_models import VideoRules
from schemas.source_models import AccountClass, OfficialAccountsFile

RULES_PATH: Path = Path(__file__).resolve().parent / "video_rules.yaml"
OFFICIAL_ACCOUNTS_PATH: Path = Path(__file__).resolve().parent / "official_accounts.yaml"
SERIES_REGISTRY_PATH: Path = Path(__file__).resolve().parent / "series_registry.yaml"
USER_FEEDBACK_PATH: Path = Path(__file__).resolve().parent / "user_feedback.yaml"   # v5.22.0 D-0200 — 사용자 의견 원장(정본)


def load_rules(path: Path | None = None) -> VideoRules:
    """규칙 파일을 읽어 `VideoRules`(extra=forbid)로 검증해 반환한다.

    파일이 없거나 모르는 키가 있으면 예외 — 기본값으로 조용히 폴백하지 않는다 (15 P6).
    """
    target = path or RULES_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    return VideoRules.model_validate(raw)


def rules_hash(path: Path | None = None) -> str:
    """규칙 파일 바이트의 sha1 (provenance `rules_hash`, 15 P5)."""
    target = path or RULES_PATH
    return hashlib.sha1(target.read_bytes()).hexdigest()


def load_official_accounts(path: Path | None = None) -> OfficialAccountsFile:
    """공식 계정 목록(v3.2.0, 18 §3-1). 파일이 없거나 형식이 틀리면 예외(P6)."""
    target = path or OFFICIAL_ACCOUNTS_PATH
    return OfficialAccountsFile.model_validate(yaml.safe_load(target.read_text(encoding="utf-8")))


def classify_handle(handle: str, accounts: OfficialAccountsFile | None = None) -> AccountClass:
    """목록에 있으면 그 account_class, 없으면 unknown(사칭 흔함 — 이름이 그럴듯해도 공식으로 보지 않는다)."""
    a = (accounts or load_official_accounts()).lookup(handle)
    return a.account_class if a else "unknown"


def load_series_registry(path: Path | None = None):  # noqa: ANN201 — SeriesRegistry
    """영상 시리즈 레지스트리(v5.18.0 D-0171). 파일이 없거나 형식이 틀리면 예외(P6)."""
    from schemas.series_models import SeriesRegistry  # noqa: PLC0415

    target = path or SERIES_REGISTRY_PATH
    return SeriesRegistry.model_validate(yaml.safe_load(target.read_text(encoding="utf-8")))


def load_user_feedback(path: Path | None = None) -> FeedbackLedger:
    """사용자 의견 원장(v5.22.0 D-0200). 파일이 없거나 형식이 틀리면 예외(P6) — 원장 없이 게이트를 통과시키지 않는다."""
    target = path or USER_FEEDBACK_PATH
    return FeedbackLedger.model_validate(yaml.safe_load(target.read_text(encoding="utf-8")))
