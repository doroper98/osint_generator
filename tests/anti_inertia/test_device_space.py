"""test_device_space — 장치 해상도는 렌더 진입 한 곳 + 래스터 준비에서만 (v3.6.0, back_and_forth D-0067 요건 1).

`px()` 는 렌더 진입의 `ctx.translate(pad_x) · ctx.scale(k)` 한 번으로 전역 적용된다(D-0067 A). 레이어·패널·자막·배치·검사가
장치 크기를 직접 읽으면 설계 좌표(854×480)와 장치 좌표가 섞여 1080p 에서 그 요소만 어긋난다(조용한 결함). 그래서
출력 프로파일(`Output`: `.out`, `output_profile`, `Output`)을 읽는 engine 모듈은 아래 허용 목록뿐이다.
"""

from __future__ import annotations

import ast
import unittest

from tests.anti_inertia._ast_util import REPO, iter_py

ALLOWED: dict[str, str] = {
    "engine/style.py": "Output·output_profile 정의(config engine.output)",
    "engine/context.py": "RenderCtx.out 필드",
    "engine/project.py": "load_project(out=) — 프로파일을 RenderCtx 에 싣기만",
    "engine/render.py": "렌더 진입 변환·표면 크기·인코딩·prev_<프로파일>/",
    "engine/projection.py": "지도 베이스 장치 해상도(View.base)",
    "engine/assets.py": "래스터 장치 해상도 준비(raster·set_raster)",
    "engine/layers/badges.py": "인물·국기·휘장 래스터",
    "engine/layers/media.py": "사진·영상·컷아웃 래스터",
    "engine/checks.py": "media_upscaled 경고(원본 폭 < 장치 폭)",
    "engine/mux.py": "provenance render.resolution",
}
NAMES = frozenset({"Output", "output_profile"})


class DeviceSpaceTest(unittest.TestCase):
    def test_only_allowlist_reads_device(self) -> None:
        bad: list[str] = []
        for p in iter_py("engine"):
            rel = p.relative_to(REPO).as_posix()
            if rel in ALLOWED:
                continue
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Attribute) and node.attr == "out":
                    bad.append(f"{rel}:{node.lineno} .out")
                elif isinstance(node, ast.Name) and node.id in NAMES:
                    bad.append(f"{rel}:{node.lineno} {node.id}")
                elif isinstance(node, ast.ImportFrom) and any(a.name in NAMES for a in node.names):
                    bad.append(f"{rel}:{node.lineno} import")
        self.assertEqual(bad, [], "장치 크기는 허용 목록 모듈만 읽는다(D-0067):\n" + "\n".join(bad))

    def test_allowlist_real(self) -> None:
        for rel in ALLOWED:
            self.assertTrue((REPO / rel).exists(), rel)


if __name__ == "__main__":
    unittest.main()
