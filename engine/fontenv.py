"""글꼴 렌더 설정 — 단일 진입·시작 점검 (v7.4.0 RENDER-AP-032, back_and_forth D-0624).

엔진 글자 화소는 fontconfig 렌더 속성(힌팅·hintstyle·rgba·lcdfilter …)에 달려 있다. 표준 설정이 빠지면 렌더·시험은 오류 없이
다른 화소를 낸다(R-0329: 컨테이너 재시작으로 셸 설정이 사라져 골든 25컷 0/25, terrain3d 합성 골든이 틀린 설정에서 고정).

- 설정 파일 = config.yaml `engine.fontconfig.file`(저장소 추적, `config/fontconfig/fonts.conf`) 한 곳.
- `ensure()` 가 `FONTCONFIG_FILE` 을 그 파일로 정한다. 다른 값이 있으면 덮어쓰고 1줄 로그(stderr).
  fontconfig 는 처음 글꼴을 쓸 때 환경을 읽으므로 cairo·pango 가 글자를 그리기 전에 불려야 한다 — `engine.style` import 맨 앞(모든 렌더 경로가 지난다).
- 점검: `fc-match -v <probe_family>` 의 hinting·hintstyle 이 `engine.fontconfig.expect` 와 다르면 `FontRenderConfigError`(조용한 진행 금지, P6).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_DONE: dict[str, bool] = {}


class FontRenderConfigError(RuntimeError):
    """표준 글꼴 렌더 설정이 아니다 — 렌더·시험을 멈춘다."""


def probe(family: str, env: "dict[str, str] | None" = None) -> dict[str, "bool | int"]:
    """fc-match -v 의 hinting·hintstyle(실제 적용 값)."""
    try:
        out = subprocess.run(["fc-match", "-v", family], capture_output=True, text=True, env=env, check=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError) as ex:
        raise FontRenderConfigError(f"fc-match 를 실행할 수 없다({ex}) — 글꼴 렌더 설정을 확인할 수 없어 멈춘다(RENDER-AP-032)") from ex
    hinting = re.search(r"^\s*hinting:\s*(True|False)", out, re.M)
    style = re.search(r"^\s*hintstyle:\s*(\d+)", out, re.M)
    if hinting is None or style is None:
        raise FontRenderConfigError(f"fc-match -v {family!r} 출력에 hinting·hintstyle 이 없다 — 설정 파일을 확인한다(RENDER-AP-032)")
    return {"hinting": hinting.group(1) == "True", "hintstyle": int(style.group(1))}


def config_file() -> Path:
    from orchestrator.config import load_config  # noqa: PLC0415

    fc = load_config().engine.fontconfig
    if fc is None:
        raise FontRenderConfigError("config.yaml engine.fontconfig 가 없다 — 표준 글꼴 렌더 설정 없이 렌더하지 않는다(RENDER-AP-032)")
    return REPO / fc.file


def check(env: "dict[str, str] | None" = None) -> dict[str, "bool | int"]:
    """주 글꼴의 실제 렌더 속성이 표준과 같은지. 다르면 FontRenderConfigError."""
    from orchestrator.config import load_config  # noqa: PLC0415

    fc = load_config().engine.fontconfig
    if fc is None:
        raise FontRenderConfigError("config.yaml engine.fontconfig 가 없다(RENDER-AP-032)")
    got = probe(fc.probe_family, env)
    want = fc.expect.model_dump()
    if got != want:
        raise FontRenderConfigError(f"글꼴 렌더 설정이 표준과 다르다: {fc.probe_family} {got} ≠ {want} "
                                    f"(FONTCONFIG_FILE={(env or os.environ).get('FONTCONFIG_FILE')!r}) — 골든과 다른 글자 화소가 나온다(RENDER-AP-032)")
    return got


def ensure() -> Path:
    """FONTCONFIG_FILE = 표준 설정 파일, 그다음 점검. 프로세스당 한 번."""
    path = config_file()
    if not path.is_file():
        raise FontRenderConfigError(f"글꼴 렌더 설정 파일 없음: {path}(RENDER-AP-032)")
    key = str(path)
    if _DONE.get(key):
        return path
    old = os.environ.get("FONTCONFIG_FILE")
    if old != key:
        if old:
            print(f"[fontenv] FONTCONFIG_FILE {old} → {key}(표준 설정으로 덮어씀, RENDER-AP-032)", file=sys.stderr)
        os.environ["FONTCONFIG_FILE"] = key
    check()
    _DONE[key] = True
    return path


__all__ = ["FontRenderConfigError", "check", "config_file", "ensure", "probe"]
