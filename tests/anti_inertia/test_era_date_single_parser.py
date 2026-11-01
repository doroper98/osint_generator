"""test_era_date_single_parser — 문장 날짜 파서는 schemas/era_date.py 하나 (v7.4.0 전쟁사 W1, back_and_forth D-0600 §3, 15 P3).

옛 날짜 정규식(`^\\d{4}(\\.\\d{2}...)`)이 한 곳이라도 남으면 기원전 날짜가 그 경로에서 조용히 떨어지거나 오류가 난다
(패턴 C — 진실의 원천이 여럿). 검사:
(a) 저장소 코드(테스트·핸드오프 참고 코드 제외)의 문자열 상수에 '네 자리 연도 + 점' 날짜 정규식이 era_date.py 밖에 없다
(b) 문장 날짜를 손으로 쪼개는 관용구(`.date[:4]`, `.date.replace(".", ". ")`, `.date.split(".")`)가 없다
(c) rules script_schema.date_formats 의 꼴마다 예시 문자열이 파서를 통과한다(규칙과 파서가 같은 말을 한다)
검사기 자신이 위반을 잡는지는 합성 소스로 따로 확인한다.
"""

from __future__ import annotations

import ast
import re
import unittest

from tests.anti_inertia._ast_util import REPO, docstring_nodes, iter_py

PARSER = "schemas/era_date.py"
YEAR_DOT_RE = re.compile(r"\\d\{4\}\)?\(?(?:\?:)?\\\.")          # 정규식 소스 안의 '\d{4}' 다음 '\.'
IDIOMS = re.compile(r"\.date\[:\d\]|\.date\.replace\(\"\.\"|\.date\.split\(\"\.\"\)")


def violations_in(src: str, rel: str) -> list[str]:
    out: list[str] = []
    tree = ast.parse(src)
    docs = docstring_nodes(tree)
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs and YEAR_DOT_RE.search(n.value):
            out.append(f"{rel}:{n.lineno} 날짜 정규식 {n.value[:60]!r}")
    for i, line in enumerate(src.splitlines(), 1):
        if IDIOMS.search(line):
            out.append(f"{rel}:{i} 문장 날짜 손 파싱 {line.strip()[:80]!r}")
    return out


class EraDateSingleParserTest(unittest.TestCase):
    def test_no_duplicate_date_parsers(self) -> None:
        bad: list[str] = []
        for p in iter_py():
            rel = p.relative_to(REPO).as_posix()
            if rel == PARSER or rel.startswith(("tests/", "archive/")):
                continue
            try:
                src = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            bad += violations_in(src, rel)
        self.assertEqual(bad, [], "문장 날짜는 schemas.era_date(parse_era_date·badge_text·day_date)로만:\n" + "\n".join(bad))

    def test_checker_catches_synthetic(self) -> None:
        src = 'import re\nDATE_RE = re.compile(r"^\\d{4}(\\.\\d{2}(\\.\\d{2})?)?$")\ny = s.date[:4]\nz = d.date.replace(".", ". ")\n'
        self.assertEqual(len(violations_in(src, "x.py")), 3)
        self.assertEqual(violations_in('X = re.compile(r"^D-\\d{4}$")\n', "x.py"), [])

    def test_rules_formats_parse(self) -> None:
        from rules import load_rules
        from schemas.era_date import is_era_date

        sample = {"YYYY": "2026", "YYYY.MM": "2026.07", "YYYY.MM.DD": "2026.07.07", "-YYYY": "-216", "-YYYY.MM": "-216.08",
                  "-YYYY.MM.DD": "-216.08.02", "c.-YYYY": "c.-216", "c.YYYY": "c.1450", "-YYYY~-YYYY": "-218~-201", "YYYY~YYYY": "1950~1953"}
        fmts = load_rules().script_schema.date_formats
        self.assertEqual(sorted(fmts), sorted(sample), "date_formats 를 바꾸면 이 표와 파서를 같이")
        for f in fmts:
            self.assertTrue(is_era_date(sample[f]), f)


if __name__ == "__main__":
    unittest.main()
