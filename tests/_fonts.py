"""글꼴 준비 여부 (v4.0.0, back_and_forth D-0072 §0 NB27).

`tests/conftest.py` 의 NB16 훅은 **같은 프로세스**에서 난 `FontMissingError` 만 skip 으로 바꾼다.
엔진 CLI 를 서브프로세스로 띄우는 테스트는 자식 프로세스가 글꼴 없음으로 끝나 부모에게는 일반 실패로 보인다.
그런 테스트는 이 판정으로 **사유 있는 skip** 을 건다. 글꼴이 설치된 환경에서는 그대로 실행된다.
"""

from __future__ import annotations

import shutil
import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def fonts_ready() -> bool:
    """렌더 경로 글꼴(engine.style.FONT 의 모든 패밀리)을 fontconfig 가 이름 그대로 찾는가."""
    if shutil.which("fc-match") is None:
        return False
    from engine.style import FONT  # noqa: PLC0415
    from engine.typography import family_found  # noqa: PLC0415

    try:
        return all(family_found(fam) for fam, _ in FONT.values())
    except (OSError, subprocess.CalledProcessError):
        return False


NO_FONTS_REASON = "환경: 프로젝트 글꼴 없음 — 엔진 CLI 서브프로세스가 FontMissingError 로 끝난다(`python tools/fetch_data.py fonts` 먼저, NB27)"
