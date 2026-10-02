"""Phase G14 v5.3.0(back_and_forth D-0139) — 겹침 카드(cascade) 채택: 연출 문법 한 줄·프롬프트 반영."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace as NS
from unittest import mock

from engine import checks
from engine.cascade import layout, text_sec
from engine.layers.labels import _lb
from engine.style import CASCADE
from rules import load_rules
from tests._fonts import NO_FONTS_REASON, fonts_ready
from tests.anti_inertia._ast_util import REPO
from workers.direction_io import event_fields_table
from workers.prompt_loader import load_prompt


class CascadeGrammarTest(unittest.TestCase):
    def test_grammar_line_in_rules_and_prompts(self) -> None:
        """§2 — direction_grammar 한 줄(사람 승인 = D117 + D-0139). 프롬프트는 {{RULES.direction_grammar}} 로만 받는다(P3)."""
        rules = load_rules()
        lines = [g for g in rules.direction_grammar if "겹침 카드(cascade) 하나" in g]
        self.assertEqual(len(lines), 1)
        self.assertIn("[cascade-*] hard", lines[0])
        for name in ("director", "revise_direction"):
            self.assertIn("겹침 카드(cascade) 하나", load_prompt(name, rules), name)

    def test_event_fields_has_cascade_items(self) -> None:
        """§2-2 — 사용자 메시지 이벤트 필드 표에 cascade items[]{at, flag, date, title, line?, accent?}."""
        t = event_fields_table()
        self.assertIn("- cascade: items*: list[CascadeItem]", t)
        self.assertIn("CascadeItem = {at*: float; flag*: str; date*: str; title*: str; line: Optional[str]; accent: str}", t)


def _cascade(n: int = 7, gap: float = 3.0) -> dict:
    items = [dict(at=1.0 + i * gap, flag="ir", date=f"09. 2{i}", title=f"사건 {i}", accent="ru") for i in range(n)]
    return {"type": "cascade", "t0": 0.8, "t1": 1.0 + n * gap, "items": items}


class CascadeTextDelayTest(unittest.TestCase):
    def test_push_transition_waits_for_shift(self) -> None:
        """§3-2 — 새 앞 카드 글자: 밀기 없는 전환 = focus_sec 뒤 절반, 밀기 있는 전환(k ≥ max_back+1) = max(focus_sec, shift_sec) 뒤 절반."""
        e = _cascade()
        push = CASCADE.max_back + 1
        self.assertEqual(text_sec(1), CASCADE.focus_sec)
        self.assertEqual(text_sec(push), max(CASCADE.focus_sec, CASCADE.shift_sec))
        for k in range(1, len(e["items"])):
            at, half = e["items"][k]["at"], text_sec(k) / 2
            front = {c.i: c for c in layout(at + half - 0.01, e)}[k]
            self.assertLessEqual(front.title_a, 1e-9, k)                      # 앞 절반엔 글자 없음
            self.assertGreater({c.i: c for c in layout(at + half + 0.05, e)}[k].title_a, 0.0, k)
            self.assertAlmostEqual({c.i: c for c in layout(at + text_sec(k), e)}[k].title_a, 1.0, msg=str(k))
        at = e["items"][push]["at"] + CASCADE.focus_sec / 2 + 0.02   # 밀기 전환은 focus_sec 절반이 지나도 아직 비어 있다
        self.assertLessEqual({c.i: c for c in layout(at, e)}[push].title_a, 1e-9)


class _Stage:
    """회피를 흉내 내는 무대 — 해역 이름은 늘 그린다(회피 장치 없음), 도시 이름은 예약 상자와 겹치면 안 그린다."""

    name = "mercator"

    def draw_labels(self, ctx, v, reserved, alpha):  # noqa: ANN001, ANN201
        sea = _lb((60.0, 90.0, 140.0, 104.0), "오만만", "sea")
        city = (120.0, 70.0, 170.0, 83.0)
        out = [sea]
        if not any(checks._box_hit(city, r) for r in reserved):
            out.append(_lb(city, "두바이", "city"))
        return out


def _proj(extra: list[dict]) -> NS:
    e = _cascade(1)
    tb = NS(in_fullcard=lambda t: False)
    return NS(events=[e, *extra], cams=[None] * 1000, n_frames=1000, R=NS(stage=_Stage(), cache={}, tb=tb))


class _View:
    def __init__(self, stage, cam) -> None:  # noqa: ANN001
        pass

    def to_screen(self, x: float, y: float) -> tuple[float, float]:
        return x, y


@unittest.skipUnless(fonts_ready(), NO_FONTS_REASON)
class CascadeLabelSplitTest(unittest.TestCase):
    def test_background_labels_are_warning(self) -> None:
        """§3-1 — 문장과 무관한 배경 지명(해역 깔림·도시 회피)은 warning + hidden_labels, hard 0."""
        P = _proj([])  # noqa: N806
        with mock.patch.object(checks, "View", _View):
            self.assertFalse(any("label-under" in x for x in checks.check_cascade(P)))
            hid = checks.check_cascade_label_hidden(P)
        self.assertEqual(len(hid), 2)
        self.assertTrue(all(x.startswith("[cascade-label-hidden]") for x in hid))
        self.assertEqual({(h["name"], h["kind"], h["how"]) for h in P.R.cache["cascade_check"]["hidden_labels"]},
                         {("오만만", "sea", "깔림"), ("두바이", "city", "회피")})
        self.assertIn("cascade_label_hidden", checks.WARN)
        self.assertIn("cascade", checks.HARD)

    def test_sentence_places_are_hard(self) -> None:
        """§3-1 — 지금 보이는 마커(at_place 포함) 라벨이 카드와 교차 → hard. 같은 이름의 지도 라벨이 회피된 것만으로는 hard 가 아니다
        (그 이름은 마커 라벨이 보여 준다) — warning 으로 남는다."""
        far = {"type": "marker", "label": "두바이", "t0": 0.0, "t1": 9.0, "world": (400.0, 300.0)}   # 카드 밖 점 — 지도 라벨만 회피됨
        P = _proj([far])  # noqa: N806
        with mock.patch.object(checks, "View", _View):
            self.assertFalse(any("label-under" in x for x in checks.check_cascade(P)))
            self.assertEqual(len(checks.check_cascade_label_hidden(P)), 2)
        near = {"type": "marker", "label": "반다르아바스", "t0": 0.0, "t1": 9.0, "world": (100.0, 110.0)}  # 점·라벨이 카드 밑
        P = _proj([near])  # noqa: N806
        with mock.patch.object(checks, "View", _View):
            under = [x for x in checks.check_cascade(P) if "label-under" in x]
        self.assertEqual(len(under), 1)
        self.assertIn("반다르아바스", under[0])
        late = {**near, "t0": 5.0}   # 같은 구간이라도 아직 안 보이는 마커는 보지 않는다
        P = _proj([late])  # noqa: N806
        with mock.patch.object(checks, "View", _View):
            self.assertFalse(any("label-under" in x for x in checks.check_cascade(P)))


class HormuzGoldenRecordTest(unittest.TestCase):
    def test_hormuz_25_bytes_same_as_g12(self) -> None:
        """§5-2 — hormuz --preview golden 25컷 = phaseG12 기준선(25_END 는 도장 가린 md5). 승격 조건: 겹침 카드는 지도 무대 골든을 건드리지 않는다."""
        rec = json.loads((REPO / "docs" / "handoff" / "reports" / "phaseG14" / "hormuz_cascade.json").read_text(encoding="utf-8"))
        base = json.loads((REPO / "docs" / "handoff" / "reports" / "phaseG12" / "hormuz_baseline.json").read_text(encoding="utf-8"))
        want = {c["png"]: c.get("md5_masked") or c["md5"] for c in base["cuts"]}
        self.assertEqual(len(want), 25)
        self.assertEqual({c["png"]: c["md5"] for c in rec["cuts"]}, want)
        self.assertEqual(rec["same_as_g12"], 25)
        self.assertEqual(rec["checks"]["hard"], 0)


if __name__ == "__main__":
    unittest.main()
