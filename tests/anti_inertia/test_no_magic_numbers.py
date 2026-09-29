"""test_no_magic_numbers — 데이터화된 패널 모듈에 기하·타이밍 리터럴 금지 (D-0032 작업 2·6, 15 P3).

08 §3 정돈된 관계선 규칙의 수치는 `rules/video_rules.yaml panels.*` 한 곳에만 있다. 모듈이 숫자를 다시 적으면
규칙을 바꿔도 영상이 그대로다(agents_reviewer 패턴 C). 허용: 0·1·2·3(인덱스·반분·RGB 성분 수).
대상 모듈은 Phase 6 에서 데이터화한 것부터 늘려 간다.
"""

from __future__ import annotations

import ast
import unittest

from tests.anti_inertia._ast_util import REPO, parse

DATA_DRIVEN_MODULES: dict[str, frozenset[float]] = {   # 모듈 → 추가 허용(달력 상수 등)
    "engine/panels/relation.py": frozenset(),
    "engine/panels/timeline.py": frozenset({12}),   # 12월 → 다음 해 1월
    "engine/reserved.py": frozenset({0.5}),         # 대각 방향 단위벡터 √0.5
    "engine/panels/dots.py": frozenset(),
    "engine/panels/gantt.py": frozenset(),
    "engine/panels/dual_line.py": frozenset(),
    "engine/panels/fork.py": frozenset(),
    "engine/panels/checklist.py": frozenset(),
    "engine/panels/network.py": frozenset(),
    "engine/framing.py": frozenset({4}),            # round(·, 4) 보고 자릿수
    "engine/shots.py": frozenset(),
    "engine/stage_timeline.py": frozenset({12, 4}),
    "engine/layers/series.py": frozenset({12}),
    "engine/honesty.py": frozenset(),     # v4.3.0 — 달력 상수(12달). 레이어 수치는 rules stage_timeline.series  # v4.3.0 — 달력 상수(12달 · 4분기). 무대 수치는 rules stage_timeline
    "engine/camera_suggest.py": frozenset({4}),     # round(·, 4) 보고 자릿수
    "audio/mix.py": frozenset({44100, 10, 20}),     # SR 코덱 상수 — rules audio.sample_rate 와 일치 테스트(test_audio_rules) · dB 정의(10^(dB/20), v4.6.0 셸프)
    "audio/qa.py": frozenset({44100, 20, 10, 4}),   # SR 코덱 상수 · dB 정의(20·log10, 10^(dB/20)) · round(·, 4) 보고 자릿수
    "audio/registry.py": frozenset(),
    "bundle/entities.py": frozenset({4}),           # round(·, 4) 보고 자릿수
    "bundle/to_script.py": frozenset({1000}),       # YAML 줄 폭(줄바꿈 안 함 — orchestrator/script_io 와 같음)
    "bundle/to_direction.py": frozenset({4, 10, 1000}),  # round(·, 4) 앵커 자릿수(v4.1.0 — framing 이 하던 반올림) · 10진 자릿수(10^floor(log10), 눈금 가수는 rules bundle.nice_mantissas) · YAML 줄 폭
    "bundle/to_sources.py": frozenset({10, 120}),   # ISO 날짜 길이(YYYY-MM-DD) · 오류 문구 자르기 길이(표시용)
}
ALLOWED_NUMBERS: frozenset[float] = frozenset({0, 1, 2, 3})


class NoMagicNumbersTest(unittest.TestCase):
    def test_no_numeric_literals(self) -> None:
        violations: list[str] = []
        for rel, extra in DATA_DRIVEN_MODULES.items():
            for node in ast.walk(parse(REPO / rel)):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                        and not isinstance(node.value, bool) and node.value not in ALLOWED_NUMBERS | extra:
                    violations.append(f"{rel}:{node.lineno} {node.value!r}")
        self.assertEqual(violations, [], "규칙 값은 rules/video_rules.yaml panels.* 에:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
