"""test_no_legacy_imports — 옛 영상 경로가 코드에 남아 있지 않다 (docs/handoff/15 P2, 19 부록 B).

저장소 `*.py`(docs/handoff/ 제외)를 AST로 읽어, import 와 docstring 을 뺀 문자열 리터럴에 옛 경로
이름이 없는지 본다. 보존 브랜치 이름 `archive/hyperframes-briefing` 은 안내 문구로 허용한다.

v2.3.0(D32): 자산 부트스트랩 `tools/bootstrap_assets/`(v3 prep3·media3 실행본, Phase 5·6.5 에서 삭제)는
`tools/fetch_data.py`와 그 폴더 안에서만 이름이 나올 수 있다. 그 밖의 import·문자열 = 위반.
v2.4.0(D-0029 작업 4): people·flags 부트스트랩(`prep_people_flags`)은 `tools/commons_fetch.py`·`tools/portrait_fallback.py`로
옮겨 삭제했다. v2.5.5(D-0036 작업 5): media 부트스트랩(`media_first_pass`)도 `tools/media_fetch.py`로 옮겨
**폴더째 삭제**했다(D32 sunset 2/2). 폴더가 다시 생기거나 어디서든 그 이름을 부르면 위반.
주석은 검사하지 않는다 — 이관 출처 표시(`# moved from ...`, 19 §5.3)는 코드 참조가 아니다(D12).
"""

from __future__ import annotations

import ast
import re
import unittest


from tests.anti_inertia._ast_util import REPO, code_strings, iter_py, parse

LEGACY_NAMES: tuple[str, ...] = (
    "hyperframes", "remotion", "scene_builder", "scene_io", "render_io",
    "audio_service", "audio_io", "audio_demo", "subtitle_align", "legacy_v3",
    "tts_lint", "tts_pronounce",   # v3.0.0 — script/lint.py 로 병합 후 삭제(16 §3, D-0040 작업 8)
    "tts_backends", "ApprovalLog", "ThumbnailManifest",   # v4.0.0 — 사용처 0 v1 잔재 삭제(back_and_forth D-0073)
)
# v4.0.0 — 삭제된 문서·폴더 경로(19 §1.3·D32·D-0072 작업 9·D-0073). tests/test_docs_sync ④ 가 문서 링크 검사에 쓴다(목록 한 곳).
DELETED_DOC_PATHS: tuple[str, ...] = (
    "docs/ADDENDUM_02_PRE_PRODUCTION_DEBUG_LAYER.md", "docs/RUN_LOCAL.md", "docs/11_THUMBNAIL_SYSTEM_SPEC.md",
    "docs/PROFESSIONAL_REBUILD_PLAN.md", "docs/SHORTS_COLLAGE_OVERHAUL_PLAN.md", "docs/17_COLLAGE_DESIGN_SHEET.md",
    "tools/bootstrap_assets/", "workers/tts_backends.py", "agents/",
)
ALLOWED_MENTION = "archive/hyperframes-briefing"
_TOKEN = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(LEGACY_NAMES) + r")(?![A-Za-z0-9])")


BOOTSTRAP = "bootstrap_assets"
BOOTSTRAP_ALLOWED: tuple[str, ...] = ()           # v2.5.5 — 허용 범위 없음(폴더 삭제)
SUNSET: tuple[str, ...] = ("prep_people_flags", "media_first_pass")   # D-0029 작업 4 · D-0036 작업 5
_BOOT = re.compile(r"(?<![A-Za-z0-9])" + BOOTSTRAP + r"(?![A-Za-z0-9])")


def find_bootstrap_violations() -> list[str]:
    out: list[str] = []
    for path in iter_py():
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith(BOOTSTRAP_ALLOWED) or rel.startswith("tests/anti_inertia/"):
            continue
        tree = parse(path)
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""] + [a.name for a in node.names]
            for m in mods:
                if BOOTSTRAP in m.split("."):
                    out.append(f"{rel}:{node.lineno} import {m}")
        for const in code_strings(tree):
            if _BOOT.search(const.value):
                out.append(f"{rel}:{const.lineno} 문자열 {BOOTSTRAP!r}")
    return out


def find_violations() -> list[str]:
    out: list[str] = []
    for path in iter_py():
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith("tests/anti_inertia/"):
            continue  # 검사기 자신은 금지어 목록을 담는다
        tree = parse(path)
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""] + [a.name for a in node.names]
            for m in mods:
                if any(part in LEGACY_NAMES for part in m.split(".")):
                    out.append(f"{rel}:{node.lineno} import {m}")
        for const in code_strings(tree):
            text = const.value.replace(ALLOWED_MENTION, "")
            hit = _TOKEN.search(text)
            if hit:
                out.append(f"{rel}:{const.lineno} 문자열 {hit.group(0)!r}")
    return out


class NoLegacyImportsTest(unittest.TestCase):
    def test_no_legacy_references(self) -> None:
        violations = find_violations()
        self.assertEqual(violations, [], "옛 영상 경로 참조:\n" + "\n".join(violations))

    def test_bootstrap_assets_only_from_fetch_data(self) -> None:
        violations = find_bootstrap_violations()
        self.assertEqual(violations, [], "bootstrap_assets 는 tools/fetch_data.py 만 호출한다(D32):\n" + "\n".join(violations))

    def test_bootstrap_folder_gone(self) -> None:
        self.assertFalse((REPO / "tools" / "bootstrap_assets").exists(), "D32 sunset 2/2 — tools/bootstrap_assets 는 없어야 한다")

    def test_people_bootstrap_sunset(self) -> None:
        self.assertFalse((REPO / "tools" / "bootstrap_assets" / "prep_people_flags.py").exists())
        hits = []
        for path in iter_py():
            rel = path.relative_to(REPO).as_posix()
            if rel.startswith("tests/anti_inertia/"):
                continue
            for const in code_strings(parse(path)):
                if any(n in const.value for n in SUNSET):
                    hits.append(f"{rel}:{const.lineno}")
        self.assertEqual(hits, [], "삭제된 people 부트스트랩 참조(D-0029):\n" + "\n".join(hits))

    def test_legacy_dirs_absent_is_tracked(self) -> None:
        # 디렉터리 존재 자체는 19 §5.8 셸 검사가 본다. 여기서는 검사기 자체가 동작하는지만 확인.
        self.assertTrue(_TOKEN.search("from orchestrator.scene_builder import x"))
        self.assertIsNone(_TOKEN.search("archive/hyperframes-briefing".replace(ALLOWED_MENTION, "")))


if __name__ == "__main__":
    unittest.main()
