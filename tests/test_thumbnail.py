"""썸네일·전달 패키지 (v7.4.0, back_and_forth D-0320, 사용자 의견 UF-177).

"썸네일은 제목 페이지에서 제목을 좀 더 키우고(필요하다면 어색하지 않은 줄바꿈 가능) 주위에 금빛 얇은 선 테두리를 최외곽에서 조금 떨어진 곳에 …
이건 영상 줄때 매번 만들어서 주는 규칙으로 하자. 제목, 설명, 태그, 썸네일"
- 제목 폭 초과 → 띄어쓰기에서 2줄(어절 안 자르기 없음), 2줄도 넘으면 줄임, 그래도 넘으면 오류.
- 영상 타이틀 카드(scale 1)는 함수 분리 전과 바이트 동일 — 썸네일과 영상이 같은 코드.
- 테두리 수치는 규칙에서 읽힌다(두꺼운 선은 규칙 로드 오류).
- 전달 패키지 네 항목 중 하나라도 없거나 한도를 넘으면 오류.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

import cairo
import pytest
import yaml
from pydantic import ValidationError

from engine import fullcards as F
from engine.style import C, H_OUT, TITLE_CARD, W_OUT
from engine.timebase import ease_io, ease_out, smooth
from engine.typography import text, tw
from rules import RULES_PATH, load_rules
from schemas.rules_models import ThumbnailRules
from tools import deliver_package as D

REPO = Path(__file__).resolve().parent.parent
MID = REPO / "projects" / "us_midterms_2026"


def _ctx() -> tuple[cairo.ImageSurface, cairo.Context]:
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, W_OUT, H_OUT)
    return s, cairo.Context(s)


def _plan(title: str) -> object:
    return types.SimpleNamespace(title=title, subtitle="2026 미국 중간선거 — 주별 결과·격전지·역사 맥락", date="2026.11.05")


class TitleLinesTest(unittest.TestCase):
    T = load_rules().thumbnail

    def test_short_title_one_line_scaled(self) -> None:
        _, ctx = _ctx()
        lines, size = F.title_lines(ctx, "뒤집힌 일곱 자리", self.T.title_scale, self.T.title_line_gap, 2)
        self.assertEqual(lines, ["뒤집힌 일곱 자리"])
        self.assertAlmostEqual(size, TITLE_CARD.title_size * self.T.title_scale)

    def test_wide_title_breaks_at_space_not_inside_word(self) -> None:
        _, ctx = _ctx()
        title = "텍사스가 삼십팔 년 만에 파랗게 물든 밤"
        lines, size = F.title_lines(ctx, title, self.T.title_scale, self.T.title_line_gap, 2)
        self.assertEqual(len(lines), 2)
        self.assertEqual(" ".join(lines), title)                       # 어절 안에서 자르지 않는다
        room = W_OUT * TITLE_CARD.max_w_ratio
        self.assertTrue(all(tw(ctx, ln, size, "disp") <= room for ln in lines))

    def test_break_prefers_after_punctuation(self) -> None:
        _, ctx = _ctx()
        lines, _ = F.title_lines(ctx, "휴전안의 한 달 — 미국과 이란, 무엇이 먼저 풀려야 하나", self.T.title_scale, self.T.title_line_gap, 2)
        self.assertEqual(lines, ["휴전안의 한 달 — 미국과 이란,", "무엇이 먼저 풀려야 하나"])   # 구 안("미국과 / 이란")에서 끊지 않는다

    def test_two_lines_still_wide_shrinks_then_errors(self) -> None:
        _, ctx = _ctx()
        long = "아주 긴 제목이 두 줄로 나눠도 화면 폭을 넘어서 글자를 줄여야만 들어가는 경우"
        lines, size = F.title_lines(ctx, long, self.T.title_scale, self.T.title_line_gap, 2)
        self.assertEqual(len(lines), 2)
        self.assertLess(size, TITLE_CARD.title_size * self.T.title_scale)
        with self.assertRaises(F.TitleOverflowError):
            F.title_lines(ctx, "가나다라마바사아자차카타파하" * 6, self.T.title_scale, self.T.title_line_gap, 2)


class SameCodeAsVideoTest(unittest.TestCase):
    """scale 1 = 영상 타이틀 카드 — 함수 분리 전 코드와 바이트 동일(썸네일만 다른 모양 금지의 반대편: 영상은 그대로)."""

    @staticmethod
    def _legacy(ctx: cairo.Context, plan: object, a: float, lt: float) -> None:
        g = cairo.LinearGradient(0, 0, 0, H_OUT)
        for st, al in ((0, 0.86), (0.5, 0.7), (1, 0.92)):
            g.add_color_stop_rgba(st, 0.01, 0.015, 0.03, al * a)
        ctx.set_source(g)
        ctx.paint()
        k = ease_out(lt / 1.0)
        text(ctx, plan.title, W_OUT / 2, 232 - (1 - k) * 10, F.title_fit_size(ctx, plan.title), "disp", (1, 1, 1),
             a * smooth((lt - 0.1) / 0.6), 0, "c")
        ctx.set_source_rgba(*C["gold"], 0.95 * a)
        lw = TITLE_CARD.rule_w * ease_io((lt - 0.5) / 0.9)
        ctx.rectangle(W_OUT / 2 - lw / 2, 254, lw, 1.6)
        ctx.fill()
        text(ctx, plan.subtitle, W_OUT / 2, 290, TITLE_CARD.subtitle_size, "serifb", (0.92, 0.9, 0.88),
             a * smooth((lt - 0.8) / 0.6), 0, "c")
        text(ctx, plan.date.replace(".", ". "), W_OUT / 2, 322, 12, "mono", C["gold"], a * smooth((lt - 1.1) / 0.6), 0, "c")

    def test_scale_one_byte_equal(self) -> None:
        plan = _plan("뒤집힌 일곱 자리")
        for a, lt in ((1.0, 3.0), (0.6, 0.4), (0.9, 1.2)):
            s1, c1 = _ctx()
            self._legacy(c1, plan, a, lt)
            s2, c2 = _ctx()
            F.draw_title_card(c2, plan, a, lt)
            s1.flush()
            s2.flush()
            self.assertEqual(bytes(s1.get_data()), bytes(s2.get_data()), (a, lt))

    def test_thumbnail_group_center_kept(self) -> None:
        _, ctx = _ctx()
        d = F.draw_title_card(ctx, _plan("뒤집힌 일곱 자리"), 1.0, 99.0, scale=1.6, line_gap=1.08, max_lines=2,
                              border=load_rules().thumbnail.border)
        dh = d["size"] * F.TITLE_CAP - TITLE_CARD.title_size * F.TITLE_CAP
        self.assertAlmostEqual(d["shift_px"], round(dh / 2, 2), places=1)   # 위로 dh/2, 아래 요소 아래로 dh/2


class BorderRulesTest(unittest.TestCase):
    def test_border_from_rules_and_thick_rejected(self) -> None:
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))["thumbnail"]
        T = ThumbnailRules.model_validate(raw)  # noqa: N806
        self.assertEqual(T.border, load_rules().thumbnail.border)
        raw["border"]["width"] = 6.0   # "얇은 선" — 두꺼운 테두리는 규칙 로드 오류
        with self.assertRaises(ValidationError):
            ThumbnailRules.model_validate(raw)

    def test_border_drawn_inside_edge(self) -> None:
        s, ctx = _ctx()
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        b = load_rules().thumbnail.border
        F.draw_gold_border(ctx, b)
        s.flush()
        stride = s.get_stride()
        data = bytes(s.get_data())

        def px(x: int, y: int) -> int:
            return sum(data[y * stride + x * 4: y * stride + x * 4 + 3])

        y = H_OUT // 2
        self.assertEqual(px(2, y), 0)                       # 최외곽엔 아무것도 없다
        self.assertGreater(px(int(b.inset), y), 100)        # inset 자리에 금선
        self.assertEqual(px(int(b.inset) + 12, y), 0)       # 안쪽은 비어 있다(한 줄)


class PackageCheckTest(unittest.TestCase):
    def test_four_items_required(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            thumb = Path(d) / "thumbnail.jpg"
            thumb.write_bytes(b"x")
            ok = D.check_package("제목", "설명", ["태그"], ["#가", "#나", "#다"], thumb)
            self.assertEqual(ok, [])
            self.assertTrue(D.check_package(None, "설명", ["태그"], ["#가", "#나", "#다"], thumb))
            self.assertTrue(D.check_package("제목", "", ["태그"], ["#가", "#나", "#다"], thumb))
            self.assertTrue(D.check_package("제목", "설명", [], ["#가", "#나", "#다"], thumb))
            self.assertTrue(D.check_package("제목", "설명", ["태그"], ["#가", "#나", "#다"], Path(d) / "none.jpg"))

    def test_limits(self) -> None:
        DP = load_rules().delivery_package  # noqa: N806
        with tempfile.TemporaryDirectory() as d:
            thumb = Path(d) / "thumbnail.jpg"
            thumb.write_bytes(b"x")
            h = ["#가", "#나", "#다"]
            self.assertTrue(D.check_package("가" * (DP.title_max_chars + 1), "설명", ["태그"], h, thumb))
            self.assertTrue(D.check_package("제목", "가" * (DP.description_max_chars + 1), ["태그"], h, thumb))
            self.assertTrue(D.check_package("제목", "설명", ["가나다라마바사"] * 70, h, thumb))
            self.assertTrue(D.check_package("제목", "설명", ["태그"], ["#가", "#나"], thumb))

    def test_full_authors_replace_card_ellipsis(self) -> None:
        """D-0323 §2 — 엔딩 카드 폭 때문에 자른 credit_author '…' 는 설명문에서 레지스트리 원본 author 로."""
        m = types.SimpleNamespace(credit_author="U.S. Air National Guard photo by Senio… · Public domain",
                                  author="U.S. Air National Guard photo by Senior Airman Gwendalyn Smith")
        got = D.full_authors(["사진: 에이미 액턴 후보 — U.S. Air National Guard photo by Senio… · Public domain"], {"media.x"}, {"x": m})
        self.assertEqual(got, ["사진: 에이미 액턴 후보 — U.S. Air National Guard photo by Senior Airman Gwendalyn Smith · Public domain"])
        self.assertEqual(D.full_authors(["a — b…"], {"media.y"}, {"x": m}), ["a — b…"])   # 이번 영상이 쓰지 않은 자산은 손대지 않는다

    def test_key_links_by_id_or_url(self) -> None:
        a = types.SimpleNamespace(id="src_1", url="https://a.example/1", type="article", publisher="A",
                                  published_at=types.SimpleNamespace(month=11, day=4))
        b = types.SimpleNamespace(id="src_2", url="https://b.example/2", type="article", publisher="B",
                                  published_at=types.SimpleNamespace(month=11, day=3))
        self.assertEqual(D.key_links([a, b], ["src_2", "https://a.example/1"], 4), ["B (11.3) — https://b.example/2", "A (11.4) — https://a.example/1"])
        self.assertEqual(D.key_links([a, b], [], 1), ["A (11.4) — https://a.example/1"])
        with self.assertRaises(D.DeliveryError):
            D.key_links([a, b], ["src_9"], 4)
        with self.assertRaises(D.DeliveryError):
            D.key_links([a, b], ["src_1", "src_2"], 1)

    def test_tags_chars_youtube_count(self) -> None:
        self.assertEqual(D.tags_chars(["가나", "다 라"]), 2 + (3 + 2) + 1)

    def test_description_text_package_without_render_assets(self) -> None:
        """D-0322 — 지난 영상 소급: description_text 가 있으면 렌더 준비물 없이 네 항목을 만든다(한도 검사 같음)."""
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d)
            (proj / "out").mkdir()
            (proj / "out" / "thumbnail.jpg").write_bytes(b"x")
            body = {"schema_version": 1, "headline": "h", "summary": "s", "chapters": [{"at": "cold", "label": "c"}],
                    "title": "제목", "tags": ["가", "나 다"], "hashtags": ["#가", "#나", "#다"], "description_text": "설명 전문\n"}
            (proj / "description.yaml").write_text(yaml.safe_dump(body, allow_unicode=True), encoding="utf-8")
            rec = D.make_package(proj)
            self.assertEqual(rec["description_source"], "description_text")
            self.assertEqual((proj / "out" / "delivery" / "description.txt").read_text(encoding="utf-8"), "설명 전문\n")
            self.assertEqual(sorted(p.name for p in (proj / "out" / "delivery").iterdir()),
                             ["MD5SUMS", "description.txt", "tags.txt", "thumbnail.jpg", "title.txt"])
            body["description_text"] = "가" * (load_rules().delivery_package.description_max_chars + 1)
            (proj / "description.yaml").write_text(yaml.safe_dump(body, allow_unicode=True), encoding="utf-8")
            with self.assertRaises(D.DeliveryError):
                D.make_package(proj)

    def test_project_description_has_package_fields(self) -> None:
        from engine.mux import load_description  # noqa: PLC0415

        d = load_description(MID)
        self.assertEqual(D.check_package(d.title, "설명", d.tags, d.hashtags, REPO / "VERSION"), [])
        self.assertIn("basics", [c.at for c in d.chapters])   # 중간선거란 장(D-0320 §5)


class ThumbnailThemeTest(unittest.TestCase):
    """v7.4.0 D-0321(사용자 판정 UF-178 "지정경제학적 테마와 전쟁사/역사물에 대한 테마는 색조만 살짝 다르게 … 일관된 디자인", CLAUDE.md C13)."""

    T = load_rules().thumbnail

    def _draw(self, theme: object) -> tuple[bytes, int]:
        s, ctx = _ctx()
        ctx.set_source_rgb(0.4, 0.45, 0.5)
        ctx.paint()
        F.draw_title_card(ctx, _plan("뒤집힌 일곱 자리"), 1.0, 99.0, scale=self.T.title_scale, line_gap=self.T.title_line_gap,
                          max_lines=self.T.max_lines, border=self.T.border, theme=theme)
        s.flush()
        return bytes(s.get_data()), s.get_stride()

    def test_geo_econ_equals_no_theme(self) -> None:
        self.assertEqual(self._draw(self.T.themes["geo_econ"])[0], self._draw(None)[0])   # 합격본(md5 b8830301) 색 그대로

    def test_themes_differ_only_in_color(self) -> None:
        a, st = self._draw(self.T.themes["geo_econ"])
        b, _ = self._draw(self.T.themes["war_history"])
        self.assertNotEqual(a, b)

        def white(buf: bytes) -> set[int]:   # 흰 제목 글자 픽셀 마스크
            return {i for i in range(0, len(buf), 4) if min(buf[i], buf[i + 1], buf[i + 2]) > 235}

        self.assertEqual(white(a), white(b))
        inset = int(self.T.border.inset)
        y = H_OUT // 2
        for buf in (a, b):   # 테두리 자리 같음: inset 자리가 바로 안쪽보다 밝다
            at, inside = sum(buf[y * st + inset * 4: y * st + inset * 4 + 3]), sum(buf[y * st + (inset + 12) * 4: y * st + (inset + 12) * 4 + 3])
            self.assertGreater(at, inside)

    def test_unmapped_genre_falls_back(self) -> None:
        from tools.thumbnail import resolve_theme  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "order.yaml").write_text("genre: no_such_genre\n", encoding="utf-8")
            self.assertEqual(resolve_theme(Path(d))[0], self.T.theme_fallback)
            (Path(d) / "order.yaml").write_text("genre: geopolitics\n", encoding="utf-8")
            self.assertEqual(resolve_theme(Path(d))[:2], ("geo_econ", "genre:geopolitics"))
            from tools.thumbnail import ThumbnailError  # noqa: PLC0415

            with self.assertRaises(ThumbnailError):
                resolve_theme(Path(d), "war_history")                 # 덮어쓰기 = 사유 필수
            self.assertEqual(resolve_theme(Path(d), "war_history", "표본")[:2], ("war_history", "override"))

    def test_geometry_key_in_theme_rejected(self) -> None:
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))["thumbnail"]
        raw["themes"]["war_history"]["title_scale"] = 2.0   # 테마는 색만 — 기하·크기 키는 모델 오류
        with self.assertRaises(ValidationError):
            ThumbnailRules.model_validate(raw)
        raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))["thumbnail"]
        raw["theme_default_by_genre"]["history"] = "sepia"   # 없는 테마 이름
        with self.assertRaises(ValidationError):
            ThumbnailRules.model_validate(raw)


@pytest.mark.slow   # C8.3(D187) — 실제 프로젝트 720p 프레임
class ThumbnailRunTest(unittest.TestCase):
    def test_thumbnail_output_and_provenance(self) -> None:
        if not (MID / "plan.json").exists() or not (MID / "assets").exists():
            raise RuntimeError("us_midterms_2026 plan·assets 없음 — script.plan·geo.prep 먼저")
        env = {**os.environ}
        run = subprocess.run([sys.executable, "tools/thumbnail.py", str(MID)], cwd=REPO, capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stdout[-1500:] + run.stderr[-1500:])
        rec = json.loads((MID / "out" / "thumbnail.json").read_text(encoding="utf-8"))
        from PIL import Image  # noqa: PLC0415

        T = load_rules().thumbnail  # noqa: N806
        self.assertEqual(Image.open(MID / "out" / "thumbnail.png").size, (T.width, T.height))
        self.assertLessEqual((MID / "out" / "thumbnail.jpg").stat().st_size, T.jpg_max_bytes)
        self.assertEqual(rec["border"], T.border.model_dump())
        self.assertEqual(rec["title_scale"], T.title_scale)
        self.assertEqual(rec["png"]["md5"], hashlib.md5((MID / "out" / "thumbnail.png").read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
