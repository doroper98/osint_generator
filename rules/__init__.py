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


_RULES_CACHE: dict[Path, tuple[tuple[int, int, int, int], int, str, VideoRules]] = {}
_RACY_NS = 2_000_000_000   # 파일 시각 해상도(거친 시계)보다 넉넉히 — 이 안에 바뀐 파일은 내용 sha1 로 다시 확인(git racy-index 와 같은 방식)


def load_rules(path: Path | None = None) -> VideoRules:
    """규칙 파일을 읽어 `VideoRules`(extra=forbid, frozen)로 검증해 반환한다.

    파일이 없거나 모르는 키가 있으면 예외 — 기본값으로 조용히 폴백하지 않는다 (15 P6).
    캐시(v7.4.0 back_and_forth D-1000 S1): 키 = (resolve 한 경로, st_mtime_ns, st_size, st_ino, st_ctime_ns). 같은 키면 **같은 객체**를
    돌려준다 — 렌더·검사가 프레임마다 부르던 YAML 재파싱·검증 비용 제거(R-0318 §4.2: 1초 프레임 45~60초). 파일이 바뀌면 다시 읽는다
    (시험의 임시 규칙 파일·렌더 전 규칙 개정). 캐시한 뒤 2초 안에 수정된 파일(같은 시계 눈금 안 재기록 가능)은 내용 sha1 로 확인한다.
    공유 객체라 VideoRules 는 frozen 이다(속성 대입 = 오류).
    """
    import time  # noqa: PLC0415

    target = (path or RULES_PATH).resolve()
    st = target.stat()
    key = (st.st_mtime_ns, st.st_size, st.st_ino, st.st_ctime_ns)
    hit = _RULES_CACHE.get(target)
    if hit is not None and hit[0] == key:
        if max(st.st_mtime_ns, st.st_ctime_ns) < hit[1] - _RACY_NS:
            return hit[3]
        if hashlib.sha1(target.read_bytes()).hexdigest() == hit[2]:   # racy — 내용으로 확인, 확인 시각을 새로 찍어 다음부터는 stat 만
            _RULES_CACHE[target] = (key, time.time_ns(), hit[2], hit[3])
            return hit[3]
    cached_at = time.time_ns()
    data = target.read_bytes()
    rules = VideoRules.model_validate(yaml.safe_load(data.decode("utf-8")))
    _RULES_CACHE[target] = (key, cached_at, hashlib.sha1(data).hexdigest(), rules)
    return rules


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
