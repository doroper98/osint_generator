"""test_no_old_states — 옛 상태 머신 값이 저장소 코드에 남지 않았다 (v3.0.0, D-0040 §2, 15 P2).

16 §2 로 상태 머신을 교체했다. 옛 24개 상태 중 새 상태와 이름이 겹치지 않는 값이
코드(.py)에 문자열로 남아 있으면 실패한다. 테스트 파일과 핸드오프 참고 코드는 뺀다.
config.yaml 의 옛 게이트 키는 작업 6(게이트 2개)에서 이 검사에 넣는다.
"""

from __future__ import annotations

import re
import unittest

from tests.anti_inertia._ast_util import REPO, iter_py

OLD_STATES: tuple[str, ...] = (
    "intake_planning", "intake_pending_user", "source_collecting", "source_completeness_review",
    "research_in_progress", "blueprint_review", "script_writing", "script_review", "scene_planning",
    "asset_production", "scene_review", "audio_production", "render_debug", "debug_review",
    "render_preview", "preview_review", "thumbnail_production", "thumbnail_review", "render_final",
    "final_review", "publish_ready", "published", "archived",
)
PATTERN = re.compile(r"\b(" + "|".join(OLD_STATES) + r")\b|ProjectState\.(" + "|".join(s.upper() for s in OLD_STATES) + r")\b")


class NoOldStatesTest(unittest.TestCase):
    def test_code_has_no_old_state_values(self) -> None:
        hits: list[str] = []
        for p in iter_py():
            rel = p.relative_to(REPO).as_posix()
            if rel.startswith("tests/"):
                continue
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if PATTERN.search(line):
                    hits.append(f"{rel}:{n}: {line.strip()[:100]}")
        self.assertEqual(hits, [], "옛 상태 값이 남았다:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
