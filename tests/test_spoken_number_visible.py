"""[spoken-number-visible] — 말한 숫자는 그 문장 동안 데이터 무대 라벨에 보인다(v7.4.0 back_and_forth D-1008 §3, 사용자 의견 UF-304).

R-0608 주 컷 상태(문장은 "27조 6천억 원 … 늘어납니다", 화면은 "149.0조 · +22.8%" 만) = 오류, 고친 상태(초점 라벨 "+27.6조") = 통과.
프레임 그리기는 표본 시각마다 정해 둔 라벨 문자열을 GLYPH_LOG 에 남기는 대역으로 바꾼다(검사 논리만 본다 — 실제 그리기는 test_stage_structure).
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from engine import checks, typography


class SpokenNumbersParseTest(unittest.TestCase):
    def test_amounts_and_rates(self) -> None:
        got = checks.spoken_numbers("일반·지방행정은 27조 6천억 원이 늘어, 29.7%로 가장 높고 1,519조 8천억 원, 3조 1천억 원입니다.")
        self.assertEqual([(k, v) for k, v, _ in got], [("amount", 27.6), ("amount", 1519.8), ("amount", 3.1), ("pct", 29.7)])

    def test_years_dates_counts_ignored(self) -> None:
        self.assertEqual(checks.spoken_numbers("2027년 9월 3일, 열두 개 분야 가운데 네 번째입니다."), [])

    def test_label_numbers(self) -> None:
        self.assertEqual(sorted(checks.label_numbers(["+27.6조", " · +22.8%", "1,519.8조"])), [("amount", 27.6), ("amount", 1519.8), ("pct", 22.8)])


def fake_project(text: str, labels: list[str]) -> SimpleNamespace:
    snt = SimpleNamespace(sid="act2_1", text=text, t0=1.0, t1=5.0)
    tb = SimpleNamespace(in_fullcard=lambda t: False)
    return SimpleNamespace(plan=SimpleNamespace(sentences=[snt], total=10.0), n_frames=300,
                           R=SimpleNamespace(tb=tb, stage=SimpleNamespace(name="backdrop")),
                           events=[{"type": "island", "kind": "structure", "t0": 0.5, "t1": 9.0}]), labels


def run(text: str, labels: list[str]) -> list[str]:
    P, labs = fake_project(text, labels)  # noqa: N806

    def draw(_P: object, _i: int) -> None:  # noqa: N803
        typography.GLYPH_LOG.extend((14.0, None, s) for s in labs + [text])   # 자막(문장 그대로)도 그린다 — 검사는 자막을 뺀다

    with mock.patch("engine.render.render_frame", draw):
        return checks.check_spoken_number_visible(P)


class SpokenNumberVisibleTest(unittest.TestCase):
    TEXT = "일반·지방행정은 27조 6천억 원이 늘어, 열두 개 분야 가운데 가장 많이 늘어납니다."

    def test_r0608_state_fails(self) -> None:
        errs = run(self.TEXT, ["149.0조", " · +22.8%", "일반·지방행정"])
        self.assertEqual(len(errs), 1)
        self.assertIn("[spoken-number-visible] act2_1", errs[0])

    def test_fixed_state_passes(self) -> None:
        self.assertEqual(run(self.TEXT, ["+27.6조", " · +22.8%"]), [])

    def test_outside_data_stage_not_checked(self) -> None:
        P, _ = fake_project(self.TEXT, [])  # noqa: N806
        P.events = []
        self.assertEqual(checks.check_spoken_number_visible(P), [])

    def test_registered_hard(self) -> None:
        self.assertIn("spoken_number_visible", checks.HARD)


if __name__ == "__main__":
    unittest.main()
