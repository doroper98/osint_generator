"""v7.4.0 back_and_forth D-0325 — 요소 등장·퇴장 시간 하한(사용자 의견 UF-159 "뭔가가 등장 했다가 사라지는 트랜지션(사진이나 기사 등 모든것)에
지금보다 한 50% 정도만 시간을 더 배정해 … 0.8초 → 1.2초 … 너무 성급해 보임").

규칙 파일을 패턴으로 훑는다(키 목록을 시험 상수로 두지 않는다 — 새 키가 생겨도 잡힌다):
- `*fade*_sec`·`popin_sec`·`appear*_sec`·`*xfade_sec` 스칼라 전부 ≥ rules transition.element_fade_min_sec
  (audio.*·tts_rules.*·camera·hold·show·grow 제외 — 음악·음성·카메라·보이는 시간·쓸기는 대상이 아니다)
- transition.element 의 [in, out] 전부 ≥ 하한
- 하한 예외는 transition.element_fade_exempt 에 사유와 함께, 그 목록은 이 시험이 고정
- 엔진 코드에 `window(…, 숫자, 숫자)` 리터럴이 다시 생기면 실패(값은 규칙 파일에서만, P3)
"""

from __future__ import annotations

import re
import unittest

import yaml

from tests.anti_inertia._ast_util import REPO

KEY = re.compile(r"(fade.*_sec|^popin_sec$|^appear.*_sec$|xfade_sec)$")
SKIP_ROOTS = ("audio", "tts_rules")
SKIP_WORDS = ("camera", "hold", "show", "grow")
EXEMPT = {"layout_480p.badge.fade_in_sec", "transition.element.boom", "transition.element.route_label_swap"}
WINDOW_LITERAL = re.compile(r"window\([^()]*,\s*[0-9]*\.?[0-9]+\s*,\s*[0-9]*\.?[0-9]+\s*\)")


def scalars(d: object, path: str = "") -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    if isinstance(d, dict):
        for k, v in d.items():
            p = f"{path}.{k}" if path else str(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and KEY.search(str(k)):
                out.append((p, float(v)))
            out += scalars(v, p)
    elif isinstance(d, list):
        for v in d:
            out += scalars(v, path)
    return out


class ElementFadeFloorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = yaml.safe_load((REPO / "rules" / "video_rules.yaml").read_text(encoding="utf-8"))
        self.tr = self.raw["transition"]
        self.mn = self.tr["element_fade_min_sec"]

    def test_floor_value(self) -> None:
        self.assertEqual(self.mn, 0.55)   # D-0325 표의 최솟값(quote_center.fade_sec 0.35 ×1.5)

    def test_exempt_list_fixed(self) -> None:
        self.assertEqual(set(self.tr["element_fade_exempt"]), EXEMPT)
        self.assertTrue(all(len(v) >= 8 for v in self.tr["element_fade_exempt"].values()))   # 사유 필수

    def test_rule_keys_above_floor(self) -> None:
        bad = [(p, v) for p, v in scalars(self.raw)
               if p.split(".")[0] not in SKIP_ROOTS and not any(w in p for w in SKIP_WORDS) and p not in EXEMPT and v < self.mn - 1e-9]
        self.assertEqual(bad, [], "UF-159 — 요소 등장·퇴장이 다시 성급해졌다")
        self.assertGreater(len(scalars(self.raw)), 30)   # 패턴이 실제로 키를 잡는다(빈 검사 방지)

    def test_element_pairs_above_floor(self) -> None:
        bad = [(k, v) for k, v in self.tr["element"].items() if f"transition.element.{k}" not in EXEMPT and min(v) < self.mn - 1e-9]
        self.assertEqual(bad, [])
        self.assertEqual(self.tr["element"]["photo"], [0.75, 0.75])   # 옛 draw_photo 리터럴 0.5 ×1.5

    def test_no_window_literals_in_engine(self) -> None:
        hits = []
        for f in sorted((REPO / "engine").rglob("*.py")):
            if f.name == "timebase.py":
                continue
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if WINDOW_LITERAL.search(line) and not line.lstrip().startswith("#"):
                    hits.append(f"{f.relative_to(REPO)}:{i}")
        self.assertEqual(hits, [], "등장·퇴장 시간 리터럴 — rules transition.element 로(P3, UF-159)")


if __name__ == "__main__":
    unittest.main()
