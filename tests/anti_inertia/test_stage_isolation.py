"""무대 격리 — Mercator 투영 계산은 engine/stage.py 에만 (v4.1.0, back_and_forth D-0076 작업 3, docs/handoff/20 §2.3).

엔진(`engine/`)의 다른 모듈은 월드 좌표와 `View` 만 쓴다. AST 로 다음을 0 으로 고정한다(허용 목록 = engine/stage.py):
① 투영 함수 이름 `ym`·`ymv`·`lat_of`·`to_uv`(정의·import·호출·속성) ② 옛 View 경위도 API(`.xy(`·`.uvs(`·`.u0`·`.v1`)
③ 위경도 직접 계산 — 이름·속성·첨자가 lon/lat 인 값을 산술(BinOp) 피연산자로 쓰기 ④ 삼각·각도 변환(tan·radians·deg2rad).
지형 자산 준비(`geo/`)와 타일 받기(`tools/fetch_data.py`)는 렌더 엔진 밖의 Mercator 자산 도구라 대상이 아니다.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ALLOW = {"engine/stage.py"}
PROJ_NAMES = {"ym", "ymv", "lat_of", "to_uv"}
OLD_VIEW_ATTRS = {"xy", "uvs", "u0", "v1"}
ANCHOR = {"lon", "lat"}
TRIG = {"tan", "radians", "deg2rad", "arctan"}


def _is_anchor(n: ast.AST) -> bool:
    if isinstance(n, ast.Name):
        return n.id in ANCHOR
    if isinstance(n, ast.Attribute):
        return n.attr in ANCHOR
    if isinstance(n, ast.Subscript):
        s = n.slice
        return isinstance(s, ast.Constant) and s.value in ANCHOR
    return False


def violations(src: str) -> list[str]:
    out: list[str] = []
    for n in ast.walk(ast.parse(src)):
        ln = getattr(n, "lineno", 0)
        if isinstance(n, ast.Name) and n.id in PROJ_NAMES:
            out.append(f"{ln}: 투영 함수 {n.id}")
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in PROJ_NAMES:
            out.append(f"{ln}: 투영 함수 정의 {n.name}")
        elif isinstance(n, ast.ImportFrom):
            out += [f"{ln}: import {a.name}" for a in n.names if a.name in PROJ_NAMES]
        elif isinstance(n, ast.Attribute):
            if n.attr in PROJ_NAMES:
                out.append(f"{ln}: 투영 함수 .{n.attr}")
            elif n.attr in OLD_VIEW_ATTRS:
                out.append(f"{ln}: 옛 View 경위도 API .{n.attr}")
            elif n.attr in TRIG:
                out.append(f"{ln}: 각도·삼각 변환 .{n.attr}")
        elif isinstance(n, ast.BinOp) and (_is_anchor(n.left) or _is_anchor(n.right)):
            out.append(f"{ln}: 위경도 직접 계산")
    return out


def engine_files() -> list[Path]:
    return sorted(p for p in (REPO / "engine").rglob("*.py") if p.relative_to(REPO).as_posix() not in ALLOW)


class StageIsolationTest(unittest.TestCase):
    def test_no_projection_math_outside_stage(self) -> None:
        self.assertGreater(len(engine_files()), 30)   # 빈 목록으로 통과하지 않게
        bad = {p.relative_to(REPO).as_posix(): v for p in engine_files() if (v := violations(p.read_text(encoding="utf-8")))}
        self.assertEqual(bad, {})

    def test_detector_catches_each_kind(self) -> None:
        """검사기 자체 — 네 종류를 하나씩 넣으면 잡는다(빈 검사기로 통과하는 것 방지)."""
        for src in ("from engine.stage import ym\n", "y = ym(lat)\n", "x, y = view.xy(a, b)\n", "p = view.u0 + 1\n",
                    "x = (e['lon'] - u0) * s\n", "d = p.lat * 2\n", "r = math.radians(a)\n", "t = np.tan(v)\n"):
            self.assertTrue(violations(src), src)

    def test_stage_itself_has_the_math(self) -> None:
        src = (REPO / "engine" / "stage.py").read_text(encoding="utf-8")
        self.assertTrue({"ym", "ymv", "lat_of", "to_uv"} <= {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)})

    def test_projection_module_is_stage_agnostic(self) -> None:
        self.assertEqual(violations((REPO / "engine" / "projection.py").read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
