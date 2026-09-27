"""v2 엔진 실행 환경 점검 (docs/handoff/19 §5.1) — 표준 라이브러리만 사용.

Phase 1(골든 재현)의 첫 관문. 누락 항목이 있으면 표를 출력하고 exit 1.

사용법:
    python tools/check_env.py
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

MIN_PYTHON: tuple[int, int] = (3, 11)
MODULES: tuple[tuple[str, str], ...] = (
    ("cairo", "pycairo"),
    ("numpy", "numpy"),
    ("PIL", "Pillow"),
    ("shapely", "shapely"),
    ("scipy", "scipy"),
    ("yaml", "PyYAML"),
    ("pydantic", "pydantic"),
    ("edge_tts", "edge-tts"),
    ("requests", "requests"),
    ("cairosvg", "cairosvg"),
    ("fontTools", "fonttools"),
    ("rembg", "rembg"),
)
FONT_FAMILIES: tuple[str, ...] = (
    "IBM Plex Sans KR",
    "Noto Serif CJK KR",
    "GmarketSans",
    "IBM Plex Mono",
)
MIN_FREE_GB: float = 5.0


def _ffmpeg_path() -> str | None:
    found = shutil.which("ffmpeg")
    if found:
        return found
    if importlib.util.find_spec("imageio_ffmpeg") is not None:
        try:
            import imageio_ffmpeg  # type: ignore[import-not-found]

            return str(imageio_ffmpeg.get_ffmpeg_exe())
        except Exception:  # noqa: BLE001 — 점검 도구: 원인은 표에 missing 으로 드러난다
            return None
    return None


def _font_families() -> set[str] | None:
    if shutil.which("fc-list") is None:
        return None
    out = subprocess.run(
        ["fc-list", ":", "family"], capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout
    fams: set[str] = set()
    for line in out.splitlines():
        for name in line.split(","):
            fams.add(name.strip())
    return fams


def collect() -> list[tuple[str, str, bool, str]]:
    """(분류, 항목, 통과 여부, 비고) 목록."""
    rows: list[tuple[str, str, bool, str]] = []
    ver = sys.version_info
    rows.append(("python", f">= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}", ver[:2] >= MIN_PYTHON, sys.version.split()[0]))

    ff = _ffmpeg_path()
    rows.append(("binary", "ffmpeg (PATH 또는 imageio-ffmpeg)", ff is not None, ff or "missing"))
    fc = shutil.which("fc-list")
    rows.append(("binary", "fc-list", fc is not None, fc or "missing"))

    for mod, pkg in MODULES:
        ok = importlib.util.find_spec(mod) is not None
        rows.append(("module", mod, ok, pkg if not ok else "ok"))

    fams = _font_families()
    for fam in FONT_FAMILIES:
        if fams is None:
            rows.append(("font", fam, False, "fc-list 없음"))
        else:
            ok = any(f.startswith(fam) for f in fams)
            rows.append(("font", fam, ok, "ok" if ok else "missing (tools/fetch_data.py fonts — Phase 1)"))

    free_gb = shutil.disk_usage(Path(__file__).resolve().parent.parent).free / 1e9
    rows.append(("disk", f"free >= {MIN_FREE_GB:.0f} GB", free_gb >= MIN_FREE_GB, f"{free_gb:.1f} GB"))
    return rows


def main() -> int:
    rows = collect()
    width = max(len(r[1]) for r in rows)
    print(f"{'kind':<7} {'item':<{width}}  status  note")
    for kind, item, ok, note in rows:
        print(f"{kind:<7} {item:<{width}}  {'OK ' if ok else 'MISS'}    {note}")
    missing = [r for r in rows if not r[2]]
    print(f"\nsummary: {len(rows) - len(missing)} ok / {len(missing)} missing")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
