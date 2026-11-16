"""규칙 로딩 캐시(v7.4.0 back_and_forth D-1000 S1).

① 같은 파일 = 같은 객체(프레임마다 YAML 재파싱·검증 제거, R-0318 §4.2).
② 파일이 바뀌면 다시 읽는다(임시 규칙 파일을 쓰는 시험·렌더 전 규칙 개정).
③ 공유 객체라 frozen — 속성 대입은 오류(조용한 변형 금지).
④ 캐시는 load_rules 한 곳(SSOT) — 엔진·워커가 규칙 객체를 따로 lru_cache·인스턴스 캐시로 붙잡지 않는다.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

REPO = Path(__file__).resolve().parents[2]


class RulesCacheTest(unittest.TestCase):
    def test_same_object(self) -> None:
        from rules import RULES_PATH, load_rules

        self.assertIs(load_rules(), load_rules())
        self.assertIs(load_rules(), load_rules(RULES_PATH))

    def test_reload_on_change(self) -> None:
        from rules import RULES_PATH, load_rules

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "video_rules.yaml"
            shutil.copy(RULES_PATH, p)
            a = load_rules(p)
            self.assertIs(a, load_rules(p))
            src = p.read_text(encoding="utf-8")
            m = re.search(r"^(\s+window_sec: )(\d+)", src, re.M)   # media.density.window_sec
            self.assertIsNotNone(m)
            p.write_text(src[:m.start(2)] + str(int(m.group(2)) + 1) + src[m.end(2):], encoding="utf-8")
            b = load_rules(p)
            self.assertIsNot(a, b)
            self.assertNotEqual(a.model_dump(), b.model_dump())

    def test_frozen(self) -> None:
        from rules import load_rules

        r = load_rules()
        with self.assertRaises(ValidationError):
            r.media = r.media  # type: ignore[misc]
        with self.assertRaises(ValidationError):
            r.media.density.window_sec = 1  # type: ignore[misc]

    def test_no_private_rules_cache(self) -> None:
        """load_rules() 결과를 lru_cache 함수나 인스턴스 사전에 붙잡는 코드 = 파일이 바뀌어도 옛 규칙(SSOT 위반)."""
        bad = []
        for root in ("engine", "script", "audio", "orchestrator", "workers", "sketch", "geo", "genres", "tools"):
            for f in (REPO / root).rglob("*.py"):
                src = f.read_text(encoding="utf-8")
                for m in re.finditer(r"@(?:functools\.)?lru_cache\([^)]*\)\s*\ndef (\w+)\([^)]*\)[^:]*:\s*\n((?:[ \t]+.*\n|\s*\n)+?)(?=\S)", src):
                    body = m.group(2)
                    if re.search(r"return load_rules\(\)\s*$", body.strip()) or re.fullmatch(r"\s*(\"\"\"[\s\S]*?\"\"\"\s*)?(from rules import load_rules.*\n\s*)?return load_rules\(\)[\w.]*\s*", body):
                        bad.append(f"{f.relative_to(REPO)}:{m.group(1)}")
                if "_rules_cache" in src:
                    bad.append(f"{f.relative_to(REPO)}: _rules_cache")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
