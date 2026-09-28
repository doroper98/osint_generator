"""rules/official_accounts.yaml — 공식 계정 목록 (v3.2.0, 18 §3-1, back_and_forth D-0051 작업 4)."""

from __future__ import annotations

import unittest
from pathlib import Path

from rules import classify_handle, load_official_accounts

REPO = Path(__file__).resolve().parent.parent


class OfficialAccountsTest(unittest.TestCase):
    def test_loads_with_source_and_date(self) -> None:
        f = load_official_accounts()
        self.assertGreaterEqual(len(f.accounts), 10)
        for a in f.accounts:
            self.assertTrue(a.source_url.startswith("https://"), a.handle)
            self.assertIsNotNone(a.checked_on)

    def test_lookup_case_insensitive(self) -> None:
        a = load_official_accounts().accounts[0]
        self.assertEqual(classify_handle(a.handle.upper()), a.account_class)
        self.assertEqual(classify_handle(a.handle.lstrip("@")), a.account_class)

    def test_impersonation_is_unknown(self) -> None:
        """이름이 그럴듯해도 목록에 없으면 unknown — 사칭 계정 흔함(18 §3-1)."""
        a = load_official_accounts().accounts[0]
        for fake in (a.handle + "_News", a.handle[:-1], "@" + a.handle.lstrip("@") + "1"):
            self.assertEqual(classify_handle(fake[:16]), "unknown", fake)

    def test_no_handle_literals_in_code(self) -> None:
        """핸들은 규칙 파일에만 — 코드 리터럴 금지(D-0051 작업 4, 15 P3)."""
        handles = [a.handle for a in load_official_accounts().accounts]
        hits = []
        for py in REPO.glob("**/*.py"):
            rel = py.relative_to(REPO).as_posix()
            if rel.startswith(("tests/", "archive/", ".git/", "projects/")) or "/site-packages/" in rel:
                continue
            txt = py.read_text(encoding="utf-8", errors="ignore")
            hits += [f"{rel}: {h}" for h in handles if f'"{h}"' in txt or f"'{h}'" in txt]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
