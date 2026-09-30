"""statement_diff — 성명서·정책 문구 비교 (v4.2.0, docs/handoff/20 §3·§3.1·§10 "성명서 문구 비교", back_and_forth D-0081 작업 5).

목적: 같은 문서의 이전 문구와 새 문구를 나란히 두고, 빠진 말(붉은 취소선)과 들어온 말(초록)을 보여 준다.
데이터: 두 문구 원문(`before`·`after`) + 출처·날짜. 삭제·추가 표시는 코드가 원문에서 단어 단위로 계산한다
(공통 접두·접미 + 가운데 difflib, 비교 키는 문장 부호 무시 — v4.4.0) — 연출이 표시를 손으로 적지 않으므로 원문과 표시가 어긋날 수 없다.
기존 요소로 안 되는 이유: 카드(`card`)는 줄 단위 문자열만 있고 단어별 색·취소선이 없다. 패널 `statement` 는 전면 덮개 패널이다.

불변 층(20 §1.1): 출처·날짜 줄 필수(빈 값 = 오류), 판독 최소 크기(rules layout_480p.min_font_px 이상 — glyph_size 검사 대상,
역할 예외 없음), 등장은 페이드 + 짧은 슬라이드(rules primitives.statement_diff.fade_sec, 20 §4.2 0.4~0.6초).
색 의미: 장르 프로필 color_semantics `added`·`removed`(없으면 렌더 전 오류). 크기·간격 = rules primitives.statement_diff.
배치: 카드와 같은 오른쪽 슬롯(`place: card_right`, 세로 = y 또는 카드 기본 y).
"""

from __future__ import annotations

import difflib
from typing import Literal, Optional

import cairo
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engine.style import C, CARD, CARD_BG, PRIMITIVES, QUOTE_MAX_CHARS, W_OUT
from engine.timebase import ease_out, window
from engine.typography import rrect, text, tw
from script.schema import DATE_RE

L = PRIMITIVES["statement_diff"]
COLOR_KEYS: tuple[str, ...] = ("added", "removed")
AXIS = "none"   # v4.4.0 — 값 축 없음(정직성 검사 해당 없음, engine/honesty.py)
Op = Literal["same", "removed", "added"]


class StatementDiff(BaseModel):
    """데이터 모양 — 이벤트 필드(봉투 type·id·t0·t1 밖)."""

    model_config = ConfigDict(extra="forbid")

    tag: str                         # 머리(예: "FOMC 성명서 · 물가 문단")
    before_label: str                # 이전 문구 이름(예: "7월 성명")
    after_label: str                 # 새 문구 이름(예: "9월 성명")
    # v5.2.0 LLM-AP-011 — 연출 프롬프트 필드 표(workers.direction_io.event_fields_table)가 description 으로 제약을 보인다
    before: str = Field(description=f"원문 ≤ {QUOTE_MAX_CHARS}자, 바뀐 문장만")   # 이전 문구 원문
    after: str = Field(description=f"원문 ≤ {QUOTE_MAX_CHARS}자, 바뀐 문장만")    # 새 문구 원문
    source: str                      # 출처(불변 층 — 필수)
    date: str = Field(description="YYYY | YYYY.MM | YYYY.MM.DD(점, 하이픈 금지)")   # 기준 날짜(불변 층 — 필수)
    y: Optional[float] = None        # 세로 위치(설계 px). 없으면 카드 기본 y

    @field_validator("tag", "before_label", "after_label", "before", "after", "source")
    @classmethod
    def _filled(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("빈 문자열 — statement_diff 의 문구·이름·출처는 모두 필수")
        return v

    @field_validator("before", "after")
    @classmethod
    def _short(cls, v: str) -> str:
        if len(v) > QUOTE_MAX_CHARS:
            raise ValueError(f"문구 {len(v)}자 > rules verification.quote_max_chars {QUOTE_MAX_CHARS} — 바뀐 문장만 인용한다")
        return v

    @field_validator("date")
    @classmethod
    def _date(cls, v: str) -> str:
        if not DATE_RE.match(v):
            raise ValueError(f"date 형식 {v!r} — YYYY | YYYY.MM | YYYY.MM.DD")
        return v

    @model_validator(mode="after")
    def _changed(self) -> "StatementDiff":
        if self.before.split() == self.after.split():
            raise ValueError("before 와 after 가 단어 단위로 같다 — 비교할 변화가 없다")
        return self


SCHEMA = StatementDiff


PUNCT = ".,;:!?()[]\"'“”‘’"   # 비교 키에서 떼는 문장 부호(표시는 원문 그대로)


def _key(w: str) -> str:
    return w.strip(PUNCT).casefold()


def diff_tokens(before: str, after: str) -> tuple[list[tuple[str, Op]], list[tuple[str, Op]]]:
    """단어 단위 차이 → (이전 줄 [(단어, same|removed)], 새 줄 [(단어, same|added)]).

    v4.4.0(D-0090 작업 3): ① 공통 접두·접미 단어를 먼저 떼고 ② 가운데만 토큰 대조(difflib). 비교 키는 문장 부호를 떼고
    대소문자를 무시한다("elevated." = "elevated") — 문장 끝 마침표 하나 때문에 같은 단어가 삭제·추가로 보이지 않게. 표시는 원문."""
    a, b = before.split(), after.split()
    ka, kb = [_key(w) for w in a], [_key(w) for w in b]
    p = 0
    while p < min(len(a), len(b)) and ka[p] == kb[p]:
        p += 1
    q = 0
    while q < min(len(a), len(b)) - p and ka[len(a) - 1 - q] == kb[len(b) - 1 - q]:
        q += 1
    left: list[tuple[str, Op]] = [(w, "same") for w in a[:p]]
    right: list[tuple[str, Op]] = [(w, "same") for w in b[:p]]
    ma, mb = a[p:len(a) - q], b[p:len(b) - q]
    sm = difflib.SequenceMatcher(a=ka[p:len(a) - q], b=kb[p:len(b) - q], autojunk=False)
    for tag, i0, i1, j0, j1 in sm.get_opcodes():
        if tag == "equal":
            left += [(w, "same") for w in ma[i0:i1]]
            right += [(w, "same") for w in mb[j0:j1]]
            continue
        left += [(w, "removed") for w in ma[i0:i1]]
        right += [(w, "added") for w in mb[j0:j1]]
    left += [(w, "same") for w in a[len(a) - q:]]
    right += [(w, "same") for w in b[len(b) - q:]]
    return left, right


def _font(op: Op) -> str:
    return "sansm" if op == "same" else "sansb"


def _lines(ctx: cairo.Context, toks: list[tuple[str, Op]], maxw: float) -> list[list[tuple[str, Op, float]]]:
    """단어를 폭 maxw 안에서 줄로 나눈다 — (단어, 표시, 줄 안 x). 한 단어가 폭보다 길면 그 줄에 혼자 둔다."""
    sp = tw(ctx, " ", L.text_size, "sansm")
    lines: list[list[tuple[str, Op, float]]] = [[]]
    x = 0.0
    for w, op in toks:
        ww = tw(ctx, w, L.text_size, _font(op))
        if lines[-1] and x + ww > maxw:
            lines.append([])
            x = 0.0
        lines[-1].append((w, op, x))
        x += ww + sp
    return lines


def layout(ctx: cairo.Context, e: dict) -> tuple[float, float, float, list[tuple[str, list]]]:
    """(x0, y0, 높이, [(행 이름, 줄 목록)]) — 제자리 상자."""
    left, right = diff_tokens(e["before"], e["after"])
    inner = L.w - L.pad_x * 2
    rows = [(e["before_label"], _lines(ctx, left, inner)), (e["after_label"], _lines(ctx, right, inner))]
    h = L.pad_top + sum(L.label_gap + L.line_h * len(ls) for _, ls in rows) + L.row_gap * (len(rows) - 1) + L.src_gap + L.pad_bottom
    return W_OUT - L.w - CARD.x_right_margin, e.get("y") or CARD.y, h, rows


def draw(ctx: cairo.Context, view: object, t: float, e: dict, style: object) -> tuple[float, float, float, float]:
    """두 문구를 위아래로: 이전(빠진 단어 = removed 색 + 취소선), 새(들어온 단어 = added 색). 맨 아래 출처 · 날짜 줄."""
    x0, y0, h, rows = layout(ctx, e)
    box = (x0, y0, x0 + L.w, y0 + h)
    a = window(t, e["t0"], e["t1"], L.fade_sec, L.fade_sec)
    if a <= 0:
        return box
    x = x0 + (1 - ease_out((t - e["t0"]) / L.fade_sec)) * L.slide_px
    muted = C["muted"]
    rrect(ctx, x, y0, L.w, h, L.radius)
    ctx.set_source_rgba(*CARD_BG[:-1], CARD_BG[-1] * a)
    ctx.fill()
    ctx.set_source_rgba(*muted, a)
    ctx.rectangle(x, y0 + L.bar_inset, L.bar_w, h - L.bar_inset * 2)
    ctx.fill()
    text(ctx, e["tag"], x + L.pad_x, y0 + L.pad_top, L.tag_size, "sansb", muted, a, 0, "l", spacing=L.tag_spacing)
    y = y0 + L.pad_top
    for i, (label, lines) in enumerate(rows):
        y += (L.row_gap if i else 0) + L.label_gap
        text(ctx, label, x + L.pad_x, y, L.label_size, "sansb", muted, a, 0, "l")
        for j, line in enumerate(lines):
            yy = y + L.line_h * (j + 1)
            for w, op, dx in line:
                rgba = (*C["white"], 1.0) if op == "same" else style.color(op)   # type: ignore[attr-defined]
                col, ca = rgba[:-1], a * rgba[-1]
                text(ctx, w, x + L.pad_x + dx, yy, L.text_size, _font(op), col, ca, 0, "l")
                if op == "removed":
                    ww = tw(ctx, w, L.text_size, _font(op))
                    ctx.set_source_rgba(*col, ca)
                    ctx.set_line_width(L.strike_w)
                    ctx.move_to(x + L.pad_x + dx, yy - L.text_size * L.strike_rise)
                    ctx.line_to(x + L.pad_x + dx + ww, yy - L.text_size * L.strike_rise)
                    ctx.stroke()
        y += L.line_h * len(lines)
    text(ctx, f"{e['source']} · {e['date']}", x + L.pad_x, y0 + h - L.pad_bottom, CARD.src_size, "sans", muted, a, 0, "l")
    return box


PREVIEW_FIXTURE: dict = {
    "type": "primitive",
    "id": "statement_diff",
    "t0": 0.0,
    "t1": 8.0,
    "tag": "성명서 문구 비교 · 예시",
    "before_label": "이전 성명",
    "after_label": "이번 성명",
    "before": "위원회는 추가적인 정책 조정이 적절할 것으로 예상한다",
    "after": "위원회는 추가적인 정책 조정의 폭과 시기를 신중히 평가할 것이다",
    "source": "예시 문구(실제 성명 아님)",
    "date": "2026.09",
}
