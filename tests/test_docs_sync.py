"""문서 동기화 (v4.0.0, back_and_forth D-0072 작업 8·D-0073 요건 3).

대상 = 저장소 루트와 `docs/` 바로 아래의 마크다운 중 머리말 `tier: 1|2` 인 문서(DOCS_GOVERNANCE §1 표의 문서 포함).
`docs/handoff/` 는 핸드오프 원문 묶음(개정은 DECISIONS 한 줄 + 본문 주석)이라 대상이 아니다.
① `last_synced_with` = `v` + VERSION ② 인용한 `rules:키`·`config:키` 가 실제 파일에 있다
③ Tier 2 문서에 `[deprecated` 배너가 없다 ④ 삭제된 레거시 경로를 가리키는 링크·경로가 없다(상대 링크는 전부 실재).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests._doc_keys import missing_keys
from tests.anti_inertia.test_no_legacy_imports import DELETED_DOC_PATHS, LEGACY_NAMES

REPO = Path(__file__).resolve().parent.parent
VERSION = "v" + (REPO / "VERSION").read_text(encoding="utf-8").strip()
HEADER = re.compile(r"^<!--\s*\n(.*?)\n-->", re.S)
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
TICK = re.compile(r"`([^`]+)`")
# 삭제된 경로·레거시 모듈 이름은 tests/anti_inertia/test_no_legacy_imports 가 정본(목록 한 곳, 검사기 자신은 레거시 검사 제외).
DELETED_PATHS = DELETED_DOC_PATHS
DELETED_RE = re.compile("|".join(r"(?<![A-Za-z0-9_])" + re.escape(d.split("/")[-1] or d) for d in DELETED_PATHS))
LEGACY_TOKEN = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(LEGACY_NAMES) + r")(?![A-Za-z0-9_])")
HISTORY_MARKERS = ("삭제", "폐기", "archive/", "이력", "legacy", "없다", "대체", "v1")   # 이 줄은 옛 경로를 '없다'고 말하는 줄


def header(path: Path) -> dict[str, str]:
    m = HEADER.match(path.read_text(encoding="utf-8"))
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def governed_docs() -> list[Path]:
    cands = sorted(REPO.glob("*.md")) + sorted((REPO / "docs").glob("*.md"))
    return [p for p in cands if header(p).get("tier") in ("1", "2")]


def governance_listed() -> list[str]:
    """DOCS_GOVERNANCE §1 Tier 1·2 목록의 경로(삭제·정정 표시 줄 제외, 00~16 범위는 실제 파일로 펼침)."""
    text = (REPO / "DOCS_GOVERNANCE.md").read_text(encoding="utf-8")
    sec = text[text.index("### Tier 1"):text.index("### Tier 3")]
    out: list[str] = []
    for line in sec.splitlines():
        if line.startswith("- ") and "~" in line and "00_PROJECT_BRIEF" in line:
            out += [p.relative_to(REPO).as_posix() for p in sorted((REPO / "docs").glob("[01][0-9]_*.md"))]
            continue
        if not line.startswith("- ") or line.startswith("- (v") or "docs/handoff/" in line:
            continue
        out += [t for t in TICK.findall(line) if t.endswith(".md")]
    return out


class HeaderVersionTest(unittest.TestCase):
    def test_governed_docs_found(self) -> None:
        self.assertGreaterEqual(len(governed_docs()), 20)

    def test_last_synced_with_is_version(self) -> None:
        bad = [(p.relative_to(REPO).as_posix(), header(p).get("last_synced_with")) for p in governed_docs()
               if header(p).get("last_synced_with") != VERSION]
        self.assertEqual(bad, [], f"기대 {VERSION}")

    def test_governance_list_exists_and_governed(self) -> None:
        listed = governance_listed()
        self.assertIn("GOAL.md", listed)
        self.assertIn("docs/07_VIDEO_STYLE_GUIDE.md", listed)
        missing = [p for p in listed if not (REPO / p).is_file()]
        self.assertEqual(missing, [])
        governed = {p.relative_to(REPO).as_posix() for p in governed_docs()}
        self.assertEqual([p for p in listed if p not in governed], [])


class RuleKeysTest(unittest.TestCase):
    def test_cited_keys_exist(self) -> None:
        bad = {p.relative_to(REPO).as_posix(): m for p in governed_docs()
               if (m := missing_keys(p.read_text(encoding="utf-8")))}
        self.assertEqual(bad, {})

    def test_rewritten_docs_cite_keys(self) -> None:
        """재작성한 안내도 07·08·09·10 은 수치를 규칙 키로 가리킨다(키 인용이 실제로 있다)."""
        from tests._doc_keys import cited_keys  # noqa: PLC0415
        for name in ("07_VIDEO_STYLE_GUIDE", "08_AUDIO_AND_TTS_SPEC", "09_MAP_AND_GEO_SPEC", "10_RENDERING_PIPELINE_SPEC"):
            self.assertGreaterEqual(len(cited_keys((REPO / "docs" / f"{name}.md").read_text(encoding="utf-8"))), 5, name)


class DeprecatedBannerTest(unittest.TestCase):
    def test_no_deprecated_banner_in_tier2(self) -> None:
        bad = [p.relative_to(REPO).as_posix() for p in governed_docs()
               if header(p).get("tier") == "2" and "[deprecated" in p.read_text(encoding="utf-8")]
        self.assertEqual(bad, [])


class LegacyLinkTest(unittest.TestCase):
    def test_relative_links_resolve(self) -> None:
        bad = []
        for p in governed_docs():
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for target in LINK.findall(line):
                    if "://" in target or target.startswith("mailto:"):
                        continue
                    if not (p.parent / target).resolve().exists():
                        bad.append(f"{p.relative_to(REPO).as_posix()}:{n} → {target}")
        self.assertEqual(bad, [])

    def test_no_live_reference_to_deleted_paths(self) -> None:
        bad = []
        for p in governed_docs():
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if any(m in line for m in HISTORY_MARKERS):
                    continue
                for tok in TICK.findall(line) + LINK.findall(line):
                    if DELETED_RE.search(tok) or LEGACY_TOKEN.search(tok.replace("archive/hyperframes-briefing", "")):
                        bad.append(f"{p.relative_to(REPO).as_posix()}:{n} {tok}")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
