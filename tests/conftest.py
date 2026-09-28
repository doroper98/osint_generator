"""테스트 공통 훅 (v3.6.0, back_and_forth D-0066 §0-3 NB16).

렌더 경로의 글꼴 선택(`engine.typography.font`)은 프로젝트 글꼴이 없으면 `FontMissingError` 를 낸다(대체 글꼴로 조용히 그리지 않음, 15 P6).
글꼴을 받지 않은 환경(`python tools/fetch_data.py fonts` 전)에서 그 오류로 끝난 테스트는 **실패가 아니라 사유 있는 skip** 으로 보고한다.
글꼴이 설치된 환경에서는 이 훅이 아무것도 바꾸지 않는다(오류가 나지 않으므로). 오류 자체를 검사하는 테스트는 assertRaises 로 잡는다.
"""

from __future__ import annotations

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):  # noqa: ANN001, ANN201
    outcome = yield
    rep = outcome.get_result()
    if call.excinfo is None or rep.passed:
        return
    from engine.typography import FontMissingError  # noqa: PLC0415

    if call.excinfo.errisinstance(FontMissingError):
        rep.outcome = "skipped"
        rep.longrepr = (str(item.path), item.location[1] or 0, f"환경: {call.excinfo.value}")
