"""카탈로그 판(catalog) 레이어 — 전편 레이어 전부 + 왼쪽 위 라벨 층 (v7.4.0, back_and_forth D-0251 §1.1).

catalog ← 그리스어 katalogos("목록으로 세어 내려 적음", kata- 아래로 + legein 세다·말하다). 도서관 목록 카드처럼 "지금 화면에
무엇이 있는지" 를 한 장씩 적어 보이는 판이라 이 이름을 쓴다. 콘티 판(animatic)과 같은 구조의 **별도 산출물**이다.

진입은 `engine.project.load_project(catalog=True)` 한 곳(15 P2 — 플래그 분기는 진입에서 끝난다). 렌더러는 전편과 같다(`resolve`).
라벨은 전체 페이드 뒤 맨 위 층(`LayerSet.overlay`)이고, 내용은 코드가 provenance 와 같은 출처에서 뽑는다(P5 — 손으로 쓰지 않는다):
1) 지금 떠 있는 이벤트의 레지스트리 이름(`panel:<kind>`·`primitive:<id>`·`badge:<kind>`) + 무대·테마
2) 이 프레임에 실제로 그린 글꼴 키 → `rules fonts` 가족 이름(sans·serif·display·mono — 그린 것만, `typography.FONT_LOG`)
3) 음성 한 줄(config tts·rules tts_rules.prosody.final_fall)
줄 문구 틀·글꼴·크기·자리는 `rules catalog.label`(P3). `final.mp4` 에는 절대 들어가지 않는다 — mp4 표식(`rules catalog.mp4_comment`)을
mux(deliver)가 보면 거부한다(GOAL 불변 6 "Debug Layer 금지").
"""

from __future__ import annotations

from typing import Optional

import cairo

from engine import typography
from engine.context import RenderCtx
from engine.registry import REGISTRY, LayerSet, RegistryError, draw_over_panel, key_of, resolve
from engine.style import CATALOG, FONT
from engine.typography import text, tw
from rules import load_rules

LB = CATALOG.label


# ------------------------------------------------------------------ 라벨 내용(코드가 뽑는다)
def element_name(e: dict) -> str:
    """이벤트 → 레지스트리 이름. 레지스트리 밖이면 RegistryError(P10). 뱃지는 `badge:<kind>`(이벤트 모델이 검증한 kind)."""
    key = key_of(e)
    if key not in REGISTRY:
        resolve(key)   # 계획만 있음·없음 사유를 담은 RegistryError
    if e["type"] == "badge":
        return f"badge:{e['kind']}"
    return key


def font_family_keys() -> dict[str, str]:
    """engine.style.FONT 이름 → rules fonts 키(sans·serif·display·mono). 가족 이름 접두로 대응한다(상수 표 없음).
    어느 키에도 맞지 않는 글꼴 이름이 있으면 오류 — 라벨이 모르는 글꼴을 조용히 빼지 않는다(P6)."""
    fam = {k: v for k, v in load_rules().fonts.model_dump().items() if k in LB.font_keys}
    out: dict[str, str] = {}
    for name, (family, _) in FONT.items():
        hit = [k for k, v in fam.items() if family.startswith(v)]
        if len(hit) != 1:
            raise RegistryError(f"카탈로그 글꼴 대응 실패: {name!r}({family!r}) → {hit} (rules fonts {sorted(fam)})")
        out[name] = hit[0]
    return out


FONT_KEY = font_family_keys()


def fonts_line(names: set[str]) -> Optional[str]:
    keys = sorted({FONT_KEY[n] for n in names}, key=list(LB.font_keys).index)
    if not keys:
        return None
    fam = load_rules().fonts.model_dump()
    return LB.lines.fonts.replace("{items}", LB.sep.join(f"{k}={fam[k]}" for k in keys))


def voice_line() -> str:
    from orchestrator.config import load_config  # noqa: PLC0415

    tts = load_config().tts
    ff = load_rules().tts_rules.prosody.final_fall
    st = tts.supertonic
    s = (LB.lines.voice.replace("{backend}", tts.backend_default).replace("{style}", st.voice_style if st else "")
         .replace("{speed}", f"{st.speed:g}" if st else "").replace("{suffix}", ff.suffix).replace("{span}", str(ff.span_chars))
         .replace("{semitones}", f"{ff.semitones:g}"))
    return s if ff.enabled else LB.lines.voice_flat.replace("{backend}", tts.backend_default).replace(
        "{style}", st.voice_style if st else "").replace("{speed}", f"{st.speed:g}" if st else "")


def stage_line(R: RenderCtx, t: float) -> str:  # noqa: N803
    shots = R.cache["catalog"]["shots"]
    st = next((s.stage for s in reversed(shots) if s.t <= t and not s.island), R.stage.name)
    mt = R.cache.get("map_theme") or {}
    return LB.lines.stage.replace("{stage}", st).replace("{theme}", str(mt.get("effective") or LB.no_theme))


def active(events: list[dict], t: float) -> list[dict]:
    """t 에 떠 있는 이벤트(그리는 창과 같은 기준 — render_frame 의 act 는 ±0.05 여유, 라벨은 실제 구간만)."""
    return [e for e in events if e["t0"] <= t <= e["t1"]]


def elements(events: list[dict], t: float) -> list[str]:
    return list(dict.fromkeys(element_name(e) for e in active(events, t)))


def label_lines(R: RenderCtx, t: float, fonts: set[str]) -> tuple[list[str], list[str]]:  # noqa: N803
    """라벨 줄 — 무대 · 요소(폭 max_w 를 넘으면 줄바꿈, 자르지 않는다) · 글꼴 · 음성. 줄 수가 max_lines 를 넘을 때만 요소 마지막 줄을
    `more`(+N)로 — (줄, 잘린 요소 이름). 잘린 이름은 provenance catalog_run.truncated 로 남는다(D-0252, P6 조용히 숨기지 않는다)."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    tail = [x for x in (fonts_line(fonts), R.cache["catalog"]["voice"]) if x]
    head = [stage_line(R, t)]
    rows: list[list[str]] = []
    for name in elements(R.cache["catalog"]["events"], t):
        if rows and tw(ctx, _row(rows[:-1], rows[-1] + [name]), LB.size, LB.font) <= LB.max_w:
            rows[-1].append(name)
        else:
            rows.append([name])
    room = LB.max_lines - len(head) - len(tail)
    cut: list[str] = []
    if len(rows) > room:
        cut = [x for r in rows[room - 1:] for x in r]
        rows = rows[:room - 1]
        body = [_row(rows[:i], r) for i, r in enumerate(rows)] + [LB.indent + LB.more.replace("{n}", str(len(cut)))]
    else:
        body = [_row(rows[:i], r) for i, r in enumerate(rows)]
    return head + body + tail, cut


def _row(before: list[list[str]], names: list[str]) -> str:
    """요소 한 줄 — 첫 줄은 rules 틀(lines.elements), 다음 줄은 들여쓰기."""
    items = LB.sep.join(names)
    return LB.lines.elements.replace("{items}", items) if not before else LB.indent + items


def label_box(lines: list[str]) -> tuple[float, float, float, float]:
    """라벨 바탕판 상자(설계 px) — (x0, y0, x1, y1). 검사 [catalog-label-overlap] 와 그리기가 같은 함수."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    x, y = LB.pos
    w = max((tw(ctx, s, LB.size, LB.font) for s in lines), default=0)
    h = LB.line_gap * len(lines)
    return x - LB.pad, y - LB.pad, x + w + LB.pad, y + h + LB.pad


# ------------------------------------------------------------------ 레이어
def frame_start(R: RenderCtx, t: float) -> None:  # noqa: N803
    """프레임 시작 — 이 프레임에 그린 글꼴 이름을 모은다(typography.text 의 실제 그리는 가지)."""
    typography.FONT_LOG = set()


def draw_label(ctx: cairo.Context, R: RenderCtx, t: float) -> None:  # noqa: N803
    """왼쪽 위 라벨 — 전체 페이드 뒤 맨 위. 라벨 자신의 글꼴은 기록하지 않는다(FONT_LOG 를 먼저 닫는다).
    타이틀·엔딩 카드 구간에는 그리지 않는다(D-0252 — 전면 카드와 교차 0). 기록(요소·글꼴)은 그 구간에도 남긴다."""
    fonts, typography.FONT_LOG = typography.FONT_LOG or set(), None
    lines, cut = label_lines(R, t, fonts)
    hidden = R.tb.in_fullcard(t)
    R.cache["catalog"]["last"] = {"t": t, "lines": [] if hidden else lines, "elements": elements(R.cache["catalog"]["events"], t),
                                  "fonts": sorted({FONT_KEY[n] for n in fonts}, key=list(LB.font_keys).index),
                                  "truncated": [] if hidden else cut}
    if hidden:
        return
    x0, y0, x1, y1 = label_box(lines)
    ctx.new_path()
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    ctx.set_source_rgba(*LB.plate)
    ctx.fill()
    for i, s in enumerate(lines):
        text(ctx, s, LB.pos[0], LB.pos[1] + LB.line_gap * i + LB.size, LB.size, LB.font, LB.color[:3], LB.color[3] * LB.alpha, 0)


CATALOG_LAYERS = LayerSet("catalog", resolve, draw_over_panel, draw_label, frame_start)

__all__ = ["CATALOG_LAYERS", "draw_label", "element_name", "elements", "fonts_line", "label_box", "label_lines", "voice_line"]
