"""G7 인물 뱃지 적응 크기 (v4.8.0, back_and_forth D-0101 §1, 사용자 결정 D89).

보이는 인물 뱃지 수 n(t): 1 → R_person_solo, 2 → R_person_group[1], ≥3 → R_person_group[0]. 바뀌면 resize_sec 동안 보간.
"""

from __future__ import annotations

import unittest

import cairo

from engine.events import BadgeEvent
from engine.layers.badges import assign_person_sizes, badge_box, badge_R, drop_person_R, label_sizes
from rules import load_rules

B = load_rules().layout_480p.badge
SOLO, (G_LO, G_HI) = B.R_person_solo, B.R_person_group


def person(pid: str, t0: float, t1: float, R: float | None = None) -> dict:  # noqa: N803
    return dict(type="badge", kind="person", pid=pid, flag="us", R=R, t0=t0, t1=t1, label=pid, role="역할")


class AdaptiveBadgeTest(unittest.TestCase):
    def test_rules_values(self) -> None:
        self.assertEqual((SOLO, G_LO, G_HI, B.resize_sec), (56, 30, 34, 0.6))
        self.assertEqual((tuple(B.label_solo), tuple(B.label_group)), ((15, 11), (12, 10)))

    def test_model_default_R_none(self) -> None:  # noqa: N802
        e = BadgeEvent.model_validate(dict(type="badge", t0=0, t1=1, lon=0, lat=0, kind="person", pid="a", flag="us"))
        self.assertIsNone(e.R)

    def test_solo_then_group_shrink_and_grow_back(self) -> None:
        a, b = person("a", 0.0, 20.0), person("b", 5.0, 12.0)
        assign_person_sizes([a, b])
        self.assertEqual(badge_R(a, 2.0), SOLO)
        c = 5.0 + B.popin_sec                           # b 팝인 완료 = a 축소 시작
        self.assertEqual(badge_R(a, c - 0.01), SOLO)
        mid = badge_R(a, c + B.resize_sec / 2)
        self.assertTrue(G_HI < mid < SOLO, mid)
        self.assertAlmostEqual(badge_R(a, c + B.resize_sec), G_HI)
        self.assertEqual(badge_R(b, 5.0), G_HI)          # 새 뱃지는 자기 자신을 세어 처음부터 group 크기
        back = 12.0 - B.fade_out_sec                     # b 페이드 아웃 시작 = a 다시 solo 로
        self.assertAlmostEqual(badge_R(a, back + B.resize_sec), SOLO)
        self.assertEqual(badge_R(a), SOLO)               # t 없음 = 구간 최대(보수값)
        self.assertAlmostEqual(badge_R(b, 11.9), G_HI)   # 사라지는 뱃지는 페이드 아웃 동안 커지지 않는다(자기 자신은 끝까지 센다)

    def test_three_people_small(self) -> None:
        ev = [person("a", 0, 20), person("b", 1, 20), person("c", 2, 20)]
        assign_person_sizes(ev)
        self.assertAlmostEqual(badge_R(ev[0], 10.0), G_LO)
        self.assertAlmostEqual(badge_R(ev[2], 10.0), G_LO)

    def test_direction_person_R_dropped(self) -> None:  # noqa: N802
        """D-0111 A — 인물 뱃지 연출 R 은 버리고 기록(provenance badge.R_ignored). 국기 R 은 그대로."""
        a = person("a", 0, 20, R=34)
        f = dict(type="badge", kind="flag", flag="kr", R=18, t0=0, t1=5, label="부산")
        ign = drop_person_R([a, f])
        self.assertEqual(ign, [{"i": 0, "pid": "a", "label": "a", "t0": 0, "R": 34}])
        self.assertIsNone(a["R"])
        self.assertEqual(f["R"], 18)
        assign_person_sizes([a, f])
        self.assertEqual(badge_R(a, 3.0), SOLO)
        self.assertEqual(badge_R(f, 3.0), 18)

    def test_explicit_R_wins_outside_direction(self) -> None:  # noqa: N802
        """패널 코드가 직접 준 R(이벤트가 아닌 뱃지)은 그대로 — assign_person_sizes 는 R 있는 뱃지를 적응시키지 않는다."""
        a, b = person("a", 0, 20, R=28), person("b", 5, 12)
        assign_person_sizes([a, b])
        self.assertEqual(badge_R(a, 2.0), 28)
        self.assertEqual(badge_R(a, 10.0), 28)
        self.assertAlmostEqual(badge_R(b, 10.0), G_HI)    # 명시 R 인물도 '보이는 인물' 로 센다
        self.assertEqual(label_sizes(a, 28), tuple(B.label_group))

    def test_flag_default_R_other(self) -> None:  # noqa: N802
        f = dict(type="badge", kind="flag", flag="kr", R=None, t0=0, t1=5, label="")
        assign_person_sizes([f])
        self.assertEqual(badge_R(f, 1.0), B.R_other)

    def test_panel_pool_separate(self) -> None:
        a, b = person("a", 0, 20), person("b", 5, 12)
        b["over_panel"] = True
        assign_person_sizes([a, b])
        self.assertEqual(badge_R(a, 10.0), SOLO)
        self.assertEqual(badge_R(b, 10.0), SOLO)

    def test_label_and_box_follow_R(self) -> None:  # noqa: N802
        a, b = person("a", 0, 20), person("b", 5, 12)
        assign_person_sizes([a, b])
        self.assertEqual(label_sizes(a, SOLO), tuple(B.label_solo))
        self.assertEqual(label_sizes(a, G_HI), tuple(B.label_group))
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        solo_box, group_box = badge_box(ctx, a, 400, 240, 2.0), badge_box(ctx, a, 400, 240, 10.0)
        self.assertGreater(solo_box[3] - solo_box[1], group_box[3] - group_box[1])
        self.assertEqual(badge_box(ctx, a, 400, 240), solo_box)   # t 없음 = 최대

    def test_timeline_badge_slot_fits_solo(self) -> None:
        """D-0111 — timeline_badge 점에서 solo 상자가 화면·레인 영역 안, 날짜 배지 아래, 축 값 자리 왼쪽."""
        from engine.hud import date_box
        from rules import load_rules as lr
        r = lr()
        x, y = r.placement.slots["timeline_badge"].point
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = person("워시", 0, 10)
        e["label"], e["role"] = "케빈 워시", "5월 연준 의장 취임"
        assign_person_sizes([e])
        b = badge_box(ctx, e, x, y, 5.0)
        st = r.stage_timeline
        self.assertGreaterEqual(b[1], max(st.area_top, date_box()[3]))
        self.assertLessEqual(b[3], st.area_bottom)
        self.assertLessEqual(b[2], 854 - st.series.axis_zone_px)
        self.assertGreaterEqual(b[0], 854 * 0.55)

    def test_legacy_group_box_unchanged(self) -> None:
        """명시 R 뱃지 상자(옛 리터럴 25·42 = 규칙 label_box 로 계산)는 v4.7.0 과 같다."""
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        e = person("a", 0, 5, R=30)
        self.assertAlmostEqual(badge_box(ctx, e, 400, 240)[3], 240 + 30 + 42)
        e["role"] = None
        self.assertAlmostEqual(badge_box(ctx, e, 400, 240)[3], 240 + 30 + 25)


if __name__ == "__main__":
    unittest.main()
