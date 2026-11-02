"""doc_excerpt — 1차 문서 발췌(원문 단락 · 번역 · 핵심 구절 밑줄) (v7.4.0, 사용자 의견 UF-400 — 영상 분석 보고
docs/handoff/reports/video_analysis_nk_succession_2026-11-02.md §4 D6).

목적: 주장의 근거가 정보기관·연구소·정부의 **1차 문서**(보고서·사전·회의록)일 때, 그 문서의 한 단락을 원문 그대로 보이고
바로 아래에 한국어 번역을 붙이며, 내레이션이 짚는 구절에 밑줄을 긋는다. 레퍼런스 영상은 CIA·RAND 보고서 스캔을 화면 가득 띄우고
나머지 줄을 흐렸다 — 여기서는 스캔 이미지 대신 **원문 텍스트를 코드로 조판**한다(C9 "사실 텍스트는 코드 렌더", 권리 기록이 없는 스캔 재배포 금지).
앞뒤 문맥은 읽을 수 없는 옅은 막대로만 보인다(지어낸 글자를 그리지 않는다).
기존 요소로 안 되는 이유: `article`(프레스 규약)은 기사 헤드라인 한 줄 + 부제 문법이고 단락·번역 병기·구절 밑줄이 없다.
`post`(게시물)는 SNS 카드다. `statement_diff` 는 두 문구 비교다. `document` 무대(registries.stages_planned)는 구현 전이다.

불변 층(20 §1.1): 발행 기관(`issuer`)·문서 이름(`doc_title`)·문서 날짜(`doc_date`)·출처 줄(`source`) 필수. 원문은 인용 상한
(rules verification.quote_max_chars) 이하 — 소스 본문의 연속 부분 문자열이어야 한다는 원칙은 verification 과 같다.
밑줄 구절(`highlight`)은 원문 안에 그대로 있어야 한다(없으면 오류 — 원문과 표시가 어긋날 수 없다). 판독 최소 크기 이상.
등장: 종이 상자 페이드 + 연속 배율(scale_from → 1) → 번역이 trans_delay_sec 뒤 떠오름 → 밑줄이 highlight_t 에 왼쪽부터 그어진다.
색 의미: 장르 프로필 color_semantics `emphasis`(밑줄·번역 왼쪽 선). 종이·잉크 색은 rules primitives.doc_excerpt 토큰.
배치: 화면 가운데 고정 상자(rules primitives.doc_excerpt.x·y·w, 자막 영역 위). 높이 = 줄 수로 정한다.
"""

from __future__ import annotations

from typing import Optional

import cairo
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engine.style import CARD, PRIMITIVES, QUOTE_MAX_CHARS
from engine.timebase import ease_out, window
from engine.typography import rrect, text, tw, wrap
from script.schema import DATE_RE

L = PRIMITIVES["doc_excerpt"]
COLOR_KEYS: tuple[str, ...] = ("emphasis",)
AXIS = "none"   # 값 축 없음(정직성 검사 해당 없음)
_MEASURE = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))


def _inner_w() -> float:
    return L.w - L.pad_x * 2


def _trans_w() -> float:
    return _inner_w() - L.trans_pad_x


class DocExcerpt(BaseModel):
    """데이터 모양 — 이벤트 필드(봉투 type·id·t0·t1 밖)."""

    model_config = ConfigDict(extra="forbid")

    issuer: str = Field(min_length=1)          # 발행 기관(예: "CIA", "RAND")
    doc_title: str = Field(min_length=1)       # 문서 이름(원어 그대로)
    doc_date: str = Field(description="문서 날짜 YYYY | YYYY.MM | YYYY.MM.DD")
    original: str = Field(description=f"원문 단락 ≤ {QUOTE_MAX_CHARS}자(소스 본문의 연속 부분 문자열)")
    translation: str = Field(description="한국어 번역(뜻을 바꾸지 않는다)")
    highlight: Optional[str] = Field(default=None, description="밑줄 구절 — original 안에 그대로 있어야 한다")
    highlight_t: Optional[float] = None        # 밑줄 시각(연출 앵커 → 초). 없으면 t0 + underline_delay_sec
    source: str = Field(min_length=1)          # 출처 줄(문서 번호·URL 등)

    @field_validator("doc_date")
    @classmethod
    def _date(cls, v: str) -> str:
        if not DATE_RE.match(v):
            raise ValueError(f"doc_date 형식 {v!r} — YYYY | YYYY.MM | YYYY.MM.DD")
        return v

    @field_validator("original")
    @classmethod
    def _orig(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("빈 원문")
        if len(v) > QUOTE_MAX_CHARS:
            raise ValueError(f"원문 {len(v)}자 > rules verification.quote_max_chars {QUOTE_MAX_CHARS} — 짚는 단락만 인용한다")
        n = len(wrap(_MEASURE, v, _inner_w(), L.orig_size, "serif"))
        if n > L.orig_lines_max:
            raise ValueError(f"원문 {n}줄 > orig_lines_max {L.orig_lines_max}")
        return v

    @field_validator("translation")
    @classmethod
    def _trans(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("빈 번역 — doc_excerpt 는 번역 병기가 필수")
        n = len(wrap(_MEASURE, v, _trans_w(), L.trans_size, "sansm"))
        if n > L.trans_lines_max:
            raise ValueError(f"번역 {n}줄 > trans_lines_max {L.trans_lines_max}")
        return v

    @model_validator(mode="after")
    def _hl(self) -> "DocExcerpt":
        if self.highlight is not None and self.highlight not in self.original:
            raise ValueError(f"highlight {self.highlight!r} 가 원문에 없다 — 원문 그대로의 구절만 밑줄")
        return self


SCHEMA = DocExcerpt


def _rgba(v: str) -> tuple[float, float, float, float]:
    from engine.primitives import semantic_rgba  # noqa: PLC0415 — 순환 import 회피

    return semantic_rgba(v)


def _word_spans(ctx: cairo.Context, line: str, start: int) -> list[tuple[int, int, float, float]]:
    """줄 안 단어 → (원문 시작 글자, 끝 글자, x, 폭). start = 이 줄이 원문에서 시작하는 글자 위치."""
    out: list[tuple[int, int, float, float]] = []
    sp = tw(ctx, " ", L.orig_size, "serif")
    x = 0.0
    pos = start
    for w_ in line.split(" "):
        ww = tw(ctx, w_, L.orig_size, "serif")
        out.append((pos, pos + len(w_), x, ww))
        x += ww + sp
        pos += len(w_) + 1
    return out


def layout(e: dict) -> dict:
    """제자리 기하(설계 px) — 줄 목록·각 블록 기준선·상자 높이."""
    orig = wrap(_MEASURE, e["original"], _inner_w(), L.orig_size, "serif")
    trans = wrap(_MEASURE, e["translation"], _trans_w(), L.trans_size, "sansm")
    pitch = L.ghost_h + L.ghost_gap
    y = L.y + L.pad_top                                # 머리 줄 기준선
    g0 = y + L.head_gap                                # 앞 문맥 막대 첫 위 끝
    o0 = g0 + pitch * L.ghost_before + L.orig_gap      # 원문 첫 줄 기준선
    t0 = o0 + L.orig_line_h * (len(orig) - 1) + L.trans_gap + L.trans_size   # 번역 첫 줄 기준선
    g1 = t0 + L.trans_line_h * (len(trans) - 1) + L.after_gap                # 뒤 문맥 막대 첫 위 끝
    s = g1 + pitch * L.ghost_after + L.src_gap          # 출처 줄 기준선
    h = s + L.pad_bottom - L.y
    return {"orig": orig, "trans": trans, "head_y": y, "g0": g0, "o0": o0, "t0": t0, "g1": g1, "src_y": s, "h": h,
            "box": (L.x, L.y, L.x + L.w, L.y + h)}


def _ghosts(ctx: cairo.Context, x: float, y: float, n: int, k0: int, col: tuple, a: float) -> None:
    """읽을 수 없는 문맥 막대 n 개(폭 = 안쪽 폭 × ghost_widths 순환) — 지어낸 글자 대신."""
    for i in range(n):
        fw = L.ghost_widths[(k0 + i) % len(L.ghost_widths)]
        rrect(ctx, x, y + i * (L.ghost_h + L.ghost_gap), _inner_w() * fw, L.ghost_h, L.ghost_h / 2)
        ctx.set_source_rgba(*col[:-1], col[-1] * a)
        ctx.fill()


def draw(ctx: cairo.Context, view: object, t: float, e: dict, style: object) -> tuple[float, float, float, float]:
    """종이 상자: 머리(기관 · 문서 · 날짜) · 앞 문맥 막대 · 원문(세리프) · 밑줄 · 번역(왼쪽 선) · 뒤 문맥 막대 · 출처 줄."""
    g = layout(e)
    box = g["box"]
    a = window(t, e["t0"], e["t1"], L.fade_sec, L.fade_sec)
    if a <= 0:
        return box
    em = style.color("emphasis")   # type: ignore[attr-defined]
    paper, ink, muted, ghost = _rgba(L.paper), _rgba(L.ink), _rgba(L.ink_muted), _rgba(L.ghost)
    x0 = L.x + L.pad_x
    cx, cy = L.x + L.w / 2, L.y + g["h"] / 2
    sc = L.scale_from + (1 - L.scale_from) * ease_out((t - e["t0"]) / L.fade_sec)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(sc, sc)
    ctx.translate(-cx, -cy)
    rrect(ctx, L.x, L.y, L.w, g["h"], L.radius)
    ctx.set_source_rgba(*paper[:-1], paper[-1] * a)
    ctx.fill()
    text(ctx, f"{e['issuer']} · {e['doc_title']}", x0, g["head_y"], L.head_size, "sansb", muted[:-1], a * muted[-1], 0, "l")
    text(ctx, e["doc_date"], L.x + L.w - L.pad_x, g["head_y"], L.head_size, "sansb", muted[:-1], a * muted[-1], 0, "r")
    _ghosts(ctx, x0, g["g0"], L.ghost_before, 0, ghost, a)
    hl = e.get("highlight")
    h0 = e["original"].find(hl) if hl else -1
    h1 = h0 + len(hl) if hl else -1
    ut = e.get("highlight_t")
    ut = e["t0"] + L.underline_delay_sec if ut is None else ut
    grow = ease_out((t - ut) / L.underline_grow_sec) if hl else 0.0
    segs: list[tuple[float, float, float]] = []   # (x0, x1, 기준선) — 밑줄 조각
    pos = 0
    for i, ln in enumerate(g["orig"]):
        yy = g["o0"] + i * L.orig_line_h
        text(ctx, ln, x0, yy, L.orig_size, "serif", ink[:-1], a * ink[-1], 0, "l")
        start = e["original"].find(ln, pos)
        start = pos if start < 0 else start
        if hl:
            ws = [w for w in _word_spans(ctx, ln, start) if w[0] < h1 and w[1] > h0]
            if ws:
                _, _, wx0, _ = ws[0]
                _, _, wx1, ww1 = ws[-1]
                segs.append((x0 + wx0, x0 + wx1 + ww1, yy))
        pos = start + len(ln)
    if segs and grow > 0:
        total = sum(b - a_ for a_, b, _ in segs)
        left = total * grow
        ctx.set_source_rgba(*em[:-1], em[-1] * a)
        ctx.set_line_width(L.underline_w)
        for sx0, sx1, yy in segs:
            if left <= 0:
                break
            run = min(sx1 - sx0, left)
            ctx.move_to(sx0, yy + L.underline_dy)
            ctx.line_to(sx0 + run, yy + L.underline_dy)
            ctx.stroke()
            left -= run
    ta = a * ease_out((t - e["t0"] - L.trans_delay_sec) / L.trans_fade_sec)
    if ta > 0:
        rise = (1 - ta / max(a, L.alpha_floor)) * L.trans_rise_px
        tx = x0 + L.trans_pad_x
        top = g["t0"] - L.trans_size + rise
        bar_h = L.trans_line_h * (len(g["trans"]) - 1) + L.trans_size + L.trans_bar_pad
        ctx.set_source_rgba(*em[:-1], em[-1] * ta)
        ctx.rectangle(x0, top - L.trans_bar_pad / 2, L.trans_bar_w, bar_h)
        ctx.fill()
        for j, ln in enumerate(g["trans"]):
            text(ctx, ln, tx, g["t0"] + j * L.trans_line_h + rise, L.trans_size, "sansm", ink[:-1], ta * ink[-1], 0, "l")
    _ghosts(ctx, x0, g["g1"], L.ghost_after, L.ghost_before, ghost, a)
    text(ctx, e["source"], x0, g["src_y"], CARD.src_size, "sans", muted[:-1], a * muted[-1], 0, "l")
    ctx.restore()
    return box


PREVIEW_FIXTURE: dict = {
    "type": "primitive",
    "id": "doc_excerpt",
    "t0": 0.0,
    "t1": 9.0,
    "issuer": "예시 기관",
    "doc_title": "Example Assessment",
    "doc_date": "1982.02",
    "original": "The regime used the party congress to introduce the successor officially to the rest of the world.",
    "translation": "정권은 당대회를 계기로 후계자를 국제사회에 공식적으로 소개했다.",
    "highlight": "introduce the successor officially",
    "highlight_t": 3.0,
    "source": "예시 문서(실제 문서 아님)",
}
