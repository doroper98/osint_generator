"""v5.3.1 시안 → v5.4.0 정규(사용자 결정 2026-10-02) — 인물 발언 인용(quote)·국경선 글로우(border_glow)·사용자 시청 지적 수정."""

from __future__ import annotations

import unittest

import cairo
import yaml

from engine.events import QuoteEvent
from engine.quote import QuoteError, quote_lines
from engine.stage import MercatorStage, StageError
from engine.style import BORDER_GLOW, QUOTE
from tests._fonts import NO_FONTS_REASON, fonts_ready
from tests.anti_inertia._ast_util import REPO


def _q(text: str) -> dict:
    return dict(type="quote", t0=1.0, t1=5.0, pid="putin", flag="ru", speaker="블라디미르 푸틴", role="러시아 대통령", text=text,
                src="로이터", date="2026. 10. 01", accent="ru")


class AdoptedStatusTest(unittest.TestCase):
    def test_adopted_by_user(self) -> None:
        """v5.4.0 — 사용자 결정(2026-10-02 "마음에 든다, 정규 규약으로 승격") = adopted, 국경 글로우 지도 기본 켜짐."""
        self.assertEqual(QUOTE.status, "adopted")
        self.assertEqual(BORDER_GLOW.status, "adopted")
        self.assertTrue(BORDER_GLOW.default_on)

    def test_grammar_lines_in_prompts(self) -> None:
        """연출 문법 2줄(직접 인용 = quote·맞선 인용 upper/lower, 통계 = 알맞은 차트) — 프롬프트는 {{RULES.direction_grammar}} 로만(P3)."""
        from rules import load_rules  # noqa: PLC0415
        from workers.prompt_loader import load_prompt  # noqa: PLC0415

        rules = load_rules()
        for key in ("**인용(quote)**", "알맞은 차트를 건다"):
            self.assertEqual(sum(key in g for g in rules.direction_grammar), 1, key)
            for name in ("director", "revise_direction"):
                self.assertIn(key, load_prompt(name, rules), name)


class QuoteModelTest(unittest.TestCase):
    def test_marks_drawn_by_code(self) -> None:
        """따옴표는 코드가 그린다 — text 에 넣으면 모델 오류(이중 따옴표 방지)."""
        QuoteEvent.model_validate(_q("모든 것이 올바르게 쓰였다"))
        with self.assertRaises(ValueError):
            QuoteEvent.model_validate(_q("“모든 것이 올바르게 쓰였다”"))

    @unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)
    def test_overflow_is_error(self) -> None:
        """quote_max_lines 를 넘으면 QuoteError — 자름·말줄임 없음(15 P6)."""
        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        self.assertLessEqual(len(quote_lines(ctx, _q("금지와 제재 때문에 세계시장에 나가지 못할 것"))), QUOTE.quote_max_lines)
        with self.assertRaises(QuoteError):
            quote_lines(ctx, _q(" ".join(["아주 긴 인용문이 이어집니다"] * 12)))


class BorderGlowConfigTest(unittest.TestCase):
    def test_mercator_config_only_border_glow(self) -> None:
        """지도 무대 stage_config 는 border_glow(bool) 하나 — 그 밖 키 = 오류(P10). v5.4.0 기본 켜짐, false 로 끈다."""
        self.assertTrue(MercatorStage().border_glow)
        self.assertFalse(MercatorStage(config={"border_glow": False}).border_glow)
        self.assertTrue(MercatorStage(config={"border_glow": True}).border_glow)
        with self.assertRaises(StageError):
            MercatorStage(config={"glow": True})
        with self.assertRaises(StageError):
            MercatorStage(config={"border_glow": "yes"})

    def test_no_project_turns_glow_off(self) -> None:
        """v5.4.0 — 정규 규약: 저장소 연출 중 국경 글로우를 끈 것은 없다(끄려면 사용자 결정)."""
        off = []
        for f in sorted((REPO / "projects").glob("*/direction.yaml")):
            d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            if ((d.get("stage_config") or {}).get("mercator") or {}).get("border_glow") is False:
                off.append(f.parent.name)
        self.assertEqual(off, [])


if __name__ == "__main__":
    unittest.main()


class GlowGoldenRecordTest(unittest.TestCase):
    def test_g15_baseline_and_delta(self) -> None:
        """v5.4.0 G15 — 글로우 켠 25컷 기준선 + expected_deltas g15_border_glow(25컷, 전/후·차이 사본), 끄면 = phaseG12 25/25(기록)."""
        import json  # noqa: PLC0415

        rec = json.loads((REPO / "docs" / "handoff" / "reports" / "phaseG15" / "hormuz_baseline.json").read_text(encoding="utf-8"))
        self.assertEqual((len(rec["cuts"]), rec["glow_off_same_as_g12"], rec["changed_vs_g12"]), (25, 25, 25))
        raw = json.loads((REPO / "docs" / "handoff" / "golden" / "expected_deltas.json").read_text(encoding="utf-8"))["deltas"]["g15_border_glow"]
        self.assertEqual(len(raw["cuts"]), 25)
        md5 = {c["png"]: c.get("md5_masked") or c["md5"] for c in rec["cuts"]}
        for c in raw["cuts"]:
            d = raw["cut_detail"][c]
            self.assertEqual(d["md5"], md5[d["render"]], c)
            self.assertTrue((REPO / "docs" / "handoff" / "reports" / "phaseG15" / "golden_delta" / d["render"].replace(".png", "_old_new_diff.jpg")).exists(), c)


@unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)
class UserFeedbackFixesTest(unittest.TestCase):
    """v5.3.1 사용자 지적(2026-10-02) 첫째~넷째 — 자막 겹침 검사·인용 위치·versus 접기·맞선 인용."""

    def test_subtitle_boxes_match_two_lines(self) -> None:
        from types import SimpleNamespace as NS2  # noqa: PLC0415

        from engine.subtitles import subtitle_boxes  # noqa: PLC0415
        from engine.style import SUBTITLE  # noqa: PLC0415

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        long = "발다이 토론클럽 연례회의는 9월 28일부터 10월 1일까지 모스크바 지역에서 열렸습니다."
        tb = NS2(order=["a"], sent={"a": NS2(t0=0.0, t1=5.0, segments=[(long, 0)])})
        b = subtitle_boxes(ctx, tb, 1.0)
        self.assertEqual(len(b), 2)
        self.assertLess(b[0][1], SUBTITLE.last_line_y - SUBTITLE.line_gap)
        self.assertEqual(subtitle_boxes(ctx, tb, 9.0), [])

    def test_lower_slots_clear_two_line_subtitles(self) -> None:
        """map_lower_* 슬롯의 solo 인물 뱃지 아래 끝(이름·역할 포함) < 두 줄 자막 글자 위 끝."""
        from engine.layers.badges import badge_box  # noqa: PLC0415
        from engine.style import BADGE, SUBTITLE  # noqa: PLC0415
        from rules import load_rules  # noqa: PLC0415

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        top2 = SUBTITLE.last_line_y - SUBTITLE.line_gap - SUBTITLE.size * 0.86
        for name in ("map_lower_left", "map_lower_right"):
            x, y = load_rules().placement.slots[name].point
            e = dict(kind="person", pid="putin", flag="ru", R=BADGE.R_person_solo, label="블라디미르 푸틴", role="러시아 대통령")
            self.assertLess(badge_box(ctx, e, x, y)[3], top2, name)

    def test_quote_center_vertical_middle(self) -> None:
        """인용 덩어리 세로 중심이 날짜 상자(50) 아래·두 줄 자막 위 공간 가운데 ±20px(사용자 지적 '너무 위')."""
        from engine.quote import quote_box  # noqa: PLC0415
        from engine.style import SUBTITLE  # noqa: PLC0415

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        b = quote_box(ctx, _q("모든 무기 사용 문제가 즉시 제기될 것"))
        top2 = SUBTITLE.last_line_y - SUBTITLE.line_gap - SUBTITLE.size * 0.86
        self.assertLess(abs((b[1] + b[3]) / 2 - (50 + top2) / 2), 20)
        self.assertLess(b[3], top2)

    def test_pair_layout(self) -> None:
        """맞선 인용: A(upper) = 왼쪽 위, B(lower) = 오른쪽 아래 — 상자가 겹치지 않고 자막 위."""
        from engine.quote import quote_box  # noqa: PLC0415

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        a = quote_box(ctx, {**_q("금지와 제재 때문에 세계시장에 나가지 못할 것"), "pos": "upper"})
        b = quote_box(ctx, {**_q("디젤 연료는 치지 마라. 그것이 세계를 해치고 있다"), "pos": "lower"})
        self.assertLess(a[0], b[0])
        self.assertLess(a[3], b[3])
        self.assertLessEqual(a[3], b[1] + 10)
        self.assertLess(b[3], 402)

    def test_versus_item_wraps_or_errors(self) -> None:
        """versus 항목: 한 줄에 들어가면 그대로, 넘치면 두 줄, 그래도 넘치면 오류(자름 없음)."""
        from engine.panels.versus import VersusOverflowError, item_lines  # noqa: PLC0415

        ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
        self.assertEqual(item_lines(ctx, "칼리닌그라드를 겨냥하지 않는다 · 방어 동맹"), ["칼리닌그라드를 겨냥하지 않는다 · 방어 동맹"])
        self.assertEqual(len(item_lines(ctx, "나토가 칼리닌그라드 봉쇄를 준비한다는 정보가 있다")), 2)
        with self.assertRaises(VersusOverflowError):
            item_lines(ctx, " ".join(["아주 긴 항목 문구가 계속 이어진다"] * 6))
