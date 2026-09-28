"""direction.yaml 변환 충실도 (v3.1.0, back_and_forth D-0047 작업 3·9).

옛 direction.py 를 합성 plan 으로 푼 스냅샷(`tests/fixtures/direction/*_old_synthetic.json`, 삭제 전 생성)과
direction.yaml 을 같은 합성 plan 으로 푼 결과가 dict 단위로 같아야 한다. 자산·음성 없이 돈다.
실제 plan 에서의 동일성(변환기 `--check`, 551d48a — 변환 뒤 삭제)과 25컷 MAD 0 은 reports/phase6_9/hormuz_v3/ 에 기록.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from engine.direction import build, load_direction_doc
from engine.stage import MercatorStage
from engine.timebase import Timebase
from tests.direction_snapshot import snapshot, synthetic_plan

REPO = Path(__file__).resolve().parent.parent
# 변환 뒤 결정으로 바꾼 값(스냅샷 = 옛 연출). (프로젝트, 타입, label) → 바뀐 필드. 여기 없는 차이는 전부 실패
INTENDED: dict[tuple[str, str, str], dict] = {
    ("hormuz_korea", "badge", "중국"): {"lat": 25.2},   # D-0048 화면 밖 잘림 수정(23.35 → 25.2)
    ("hormuz_korea", "badge", "인도"): {"lat": 25.2},
}


class ConvertFidelityTest(unittest.TestCase):
    def test_yaml_equals_old_direction(self) -> None:
        for name in ("hormuz_korea", "taiwan_strait"):
            with self.subTest(project=name):
                proj = REPO / "projects" / name
                tb = Timebase(synthetic_plan(proj))
                keys, events, sound = build(load_direction_doc(proj / "direction.yaml"), tb, MercatorStage())
                got = snapshot(keys, events, sound, tb)
                want = json.loads((REPO / "tests" / "fixtures" / "direction" / f"{name}_old_synthetic.json").read_text(encoding="utf-8"))
                for (pj, typ, label), upd in INTENDED.items():
                    if pj == name:
                        hit = [e for e in want["events_by_type"][typ] if e.get("label") == label]
                        self.assertEqual(len(hit), 1, label)
                        hit[0].update(upd)
                self.assertEqual(got["keys"], want["keys"])
                self.assertEqual(sorted(got["events_by_type"]), sorted(want["events_by_type"]))
                for typ in want["events_by_type"]:
                    self.assertEqual(got["events_by_type"][typ], want["events_by_type"][typ], typ)
                self.assertEqual(got["sound"], want["sound"])
                self.assertEqual(got["word_anchors"], want["word_anchors"])

    def test_example_prompt_copy_matches_project(self) -> None:
        ex = REPO / "prompts" / "examples" / "hormuz_direction.yaml"
        self.assertEqual(load_direction_doc(ex), load_direction_doc(REPO / "projects" / "hormuz_korea" / "direction.yaml"))


if __name__ == "__main__":
    unittest.main()
