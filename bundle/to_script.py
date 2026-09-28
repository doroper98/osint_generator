"""번들 → 원고 초안 `script.draft.yaml` (v3.5.0, docs/handoff/12 §2·§5·§7, back_and_forth D-0063 작업 3).

번들은 **원고 재료**다(12 §5-1). 문장·강조어를 가져오되 장면 구성은 새로 한다.

장면 경계(12 §5-2) — 섹션 경계가 아니라 **공간·정보 유형**이 바뀔 때:
- 공간 = 섹션 `map_ref`(있으면), 없으면 섹션 문장이 부르는 지도 마커 집합(`bundle.entities.mentions`, 폴백).
- 정보 유형 = 섹션 `chart_refs` 차트 종류 집합.
- 섹션의 공간이 지금 장면의 공간과 **겹치지 않으면**, 또는 차트 종류가 지금 장면과 **다르면** 새 장면.
  공간·차트가 없는 섹션은 지금 장면에 합친다(같은 공간 이어 가기). 인트로·아웃트로 문장도 같은 규칙.
- 그래서 장면 수는 섹션 수와 같을 이유가 없다(12막 1:1 금지, 12 §5). 경계 근거는 초안 주석에 남는다.

문장 규칙: heading 은 화면 문장에 넣지 않는다(유튜브 챕터명 후보 `chapters` 로만, 12 §5-3). text = narration,
tts = narration_tts(있으면 그대로) · 없으면 `bundle.text.tts_of`(03 §4 규칙). 금지 문구(`banned_phrases`)에 걸린 문장은
**다시 쓰지 않고** `rewrite_required` 로 표시만 한다(15 P8 — 재작성은 ScriptWorker 몫, 게이트 ① 전 린트가 차단).
출력은 `script.schema:Script` 를 그대로 통과한다(15 P4). 표시·근거는 YAML 주석과 `DraftNotes` 에 둔다.
"""

from __future__ import annotations

import re
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

from bundle.entities import EntityJoin, mentions
from bundle.text import tts_of
from engine.entities import EntityRegistry
from rules import load_rules
from schemas.models import BundleSection, ReportBundle
from script.schema import Scene, Script, Sentence

INTRO = "intro"
OUTRO = "outro"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Boundary(_Strict):
    """장면 하나와 그 근거 — 어느 섹션을 합쳤고, 왜 여기서 새 장면이 시작됐나."""

    scene: str
    sections: list[str]
    space: list[str] = Field(default_factory=list)     # map:<ref> 또는 마커 id
    charts: list[str] = Field(default_factory=list)    # 차트 종류
    reason: str


class Chapter(_Strict):
    scene: str
    title: str                                          # 섹션 heading — 화면 문장이 아니다(유튜브 챕터명 후보)


class RewriteMark(_Strict):
    sid: str
    patterns: list[str]


class TtsNote(_Strict):
    sid: str
    source: Literal["bundle", "rule"]                   # bundle = narration_tts, rule = tts_of(03 §4)
    issue: Optional[str] = None                         # 규칙 변환 뒤에도 숫자·기호가 남음 등


class DraftNotes(_Strict):
    """초안 주석의 기계용 사본(`script.draft.notes.json`). 장면 경계 근거·금지 문구 표시·챕터 후보·폴백 기록."""

    schema_version: Literal[1] = 1
    bundle_id: str
    sections: int
    scenes: int
    boundaries: list[Boundary]
    chapters: list[Chapter]
    rewrite_required: list[RewriteMark] = Field(default_factory=list)
    tts: list[TtsNote] = Field(default_factory=list)
    emphasis_dropped: list[str] = Field(default_factory=list)      # 어느 문장에도 부분 문자열로 없는 강조어
    date_sources: dict[str, Literal["timeline", "report"]] = Field(default_factory=dict)   # sid → 날짜 출처(D-0064 쟁점 4)
    mentions: dict[str, list[str]] = Field(default_factory=dict)    # sid → 언급 엔티티 id(폴백 탐지)
    unmatched: list[str] = Field(default_factory=list)              # 엔티티 조인 실패 id(bundle.entities)
    skipped_sections: list[str] = Field(default_factory=list)       # 문장이 없는 섹션


class _Part(_Strict):
    """장면 묶기 전 단위 — 섹션 하나 또는 인트로·아웃트로."""

    id: str
    heading: str = ""
    narration: list[str]
    tts: list[str] = Field(default_factory=list)
    emphasis: list[str] = Field(default_factory=list)
    space: list[str] = Field(default_factory=list)
    charts: list[str] = Field(default_factory=list)


def _parts(b: ReportBundle, join: EntityJoin, reg: EntityRegistry) -> tuple[list[_Part], list[str]]:
    chart_type = {c.chart_id: c.type for c in b.charts}
    markers = [e for e in join.entities if e.origin == "marker"]
    mjoin = EntityJoin(entities=markers)

    def space_of(sec: Optional[BundleSection], lines: list[str]) -> list[str]:
        if sec is not None and sec.map_ref:
            return [f"map:{sec.map_ref}"]
        return sorted({m.id for t in lines for m in mentions(t, mjoin, reg)})

    out: list[_Part] = []
    skipped: list[str] = []
    rv = b.report.video
    if rv and rv.intro_narration:
        out.append(_Part(id=INTRO, narration=rv.intro_narration, tts=rv.intro_narration_tts,
                         space=space_of(None, rv.intro_narration)))
    for s in b.sections:
        v = s.video
        if v is None or not v.narration:
            skipped.append(s.section_id)
            continue
        out.append(_Part(id=s.section_id, heading=s.heading, narration=v.narration, tts=v.narration_tts,
                         emphasis=v.emphasis, space=space_of(s, v.narration),
                         charts=sorted({chart_type[c] for c in s.chart_refs if c in chart_type})))
    if rv and rv.outro_narration:
        out.append(_Part(id=OUTRO, narration=rv.outro_narration, tts=rv.outro_narration_tts,
                         space=space_of(None, rv.outro_narration)))
    return out, skipped


def group_parts(parts: list[_Part]) -> list[list[_Part]]:
    """장면 경계 규칙(12 §5-2). 공간이 겹치지 않거나 차트 종류가 다르면 새 장면, 둘 다 없으면 합친다."""
    groups: list[list[_Part]] = []
    space: set[str] = set()
    charts: list[str] = []
    for p in parts:
        new_space = bool(p.space) and not (set(p.space) & space)
        new_chart = bool(p.charts) and p.charts != charts
        if not groups or new_space or new_chart:
            groups.append([p])
            space, charts = set(p.space), list(p.charts)
        else:
            groups[-1].append(p)
            space |= set(p.space)
            charts = charts or list(p.charts)
    return groups


def _reason(k: int, g: list[_Part], prev: Optional[list[_Part]]) -> str:
    if prev is None:
        return "첫 장면"
    head = g[0]
    why = []
    if head.space:
        why.append(f"공간 바뀜 → {', '.join(head.space)}")
    if head.charts:
        why.append(f"차트 종류 바뀜 → {', '.join(head.charts)}")
    tail = f" · 합친 섹션 {len(g)}개(같은 공간·차트 없음)" if len(g) > 1 else ""
    return (" · ".join(why) or "경계") + tail


_MD = re.compile(r"(?<!\d)(\d{1,2})월\s*(\d{1,2})일")


def timeline_date(text: str, points: dict[tuple[int, int], str]) -> Optional[str]:
    """문장의 "M월 D일" 이 번들 timeline 날짜와 같으면 그 날짜(YYYY.MM.DD). 연도는 timeline 값 — 추측으로 붙이지 않는다."""
    for m in _MD.finditer(text):
        hit = points.get((int(m.group(1)), int(m.group(2))))
        if hit:
            return hit
    return None


def _timeline_points(b: ReportBundle) -> dict[tuple[int, int], str]:
    out: dict[tuple[int, int], str] = {}
    for p in (b.timeline.points if b.timeline else []):
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", p.date.strip())
        if m:
            out.setdefault((int(m.group(2)), int(m.group(3))), f"{m.group(1)}.{m.group(2)}.{m.group(3)}")
    return out


def banned_hits(text: str, patterns: Optional[list[str]] = None) -> list[str]:
    """금지 문구 패턴 중 문장에 걸린 것(rules banned_phrases — 린트와 같은 목록)."""
    return [p for p in (patterns if patterns is not None else load_rules().banned_phrases.patterns) if re.search(p, text)]


def build_draft(b: ReportBundle, join: EntityJoin, reg: EntityRegistry) -> tuple[Script, DraftNotes]:
    """번들 → (Script 초안, 주석). 결정적이다. 문장을 다시 쓰지 않는다(P8)."""
    R = load_rules()  # noqa: N806
    forbidden = re.compile(R.tts_rules.forbidden_chars_regex)
    parts, skipped = _parts(b, join, reg)
    if not parts:
        raise ValueError(f"번들 {b.report.report_id}: 문장(narration)이 하나도 없다 — 초안을 만들 수 없다")
    day = (b.generated_at.strftime("%Y.%m.%d") if b.generated_at else None)
    if day is None:
        raise ValueError(f"번들 {b.report.report_id}: generated_at 이 없어 원고 날짜를 정할 수 없다(추측 금지)")
    groups = group_parts(parts)
    tl = _timeline_points(b)
    dsrc: dict[str, Literal["timeline", "report"]] = {}
    scenes: list[Scene] = []
    bounds: list[Boundary] = []
    chapters: list[Chapter] = []
    marks: list[RewriteMark] = []
    tts_notes: list[TtsNote] = []
    ment: dict[str, list[str]] = {}
    used_em: set[str] = set()
    all_em: list[str] = []
    for k, g in enumerate(groups, 1):
        sc = f"sc{k:02d}"
        sents: list[Sentence] = []
        for p in g:
            if p.heading:
                chapters.append(Chapter(scene=sc, title=p.heading))
            all_em += [e for e in p.emphasis if e not in all_em]
            for i, text in enumerate(p.narration):
                sid = f"{sc}_{len(sents)}"
                given = p.tts[i].strip() if len(p.tts) == len(p.narration) and p.tts[i].strip() else ""
                say = given or tts_of(text)
                hit = forbidden.search(say)
                tts_notes.append(TtsNote(sid=sid, source="bundle" if given else "rule",
                                         issue=f"발음 텍스트에 {hit.group(0)!r} 남음" if hit else None))
                em = [e for e in p.emphasis if e in text and e not in used_em]
                used_em |= set(em)
                tday = timeline_date(text, tl)
                dsrc[sid] = "timeline" if tday else "report"
                sents.append(Sentence(date=tday or day, text=text, tts=say if say != text else None, emphasis=em, sources=[]))
                pats = banned_hits(text, R.banned_phrases.patterns)
                if pats:
                    marks.append(RewriteMark(sid=sid, patterns=pats))
                ms = [m.id for m in mentions(text, join, reg)]
                if ms:
                    ment[sid] = ms
        scenes.append(Scene(id=sc, sentences=sents))
        bounds.append(Boundary(scene=sc, sections=[p.id for p in g], space=sorted({x for p in g for x in p.space}),
                               charts=sorted({x for p in g for x in p.charts}), reason=_reason(k, g, groups[k - 2] if k > 1 else None)))
    script = Script(title=b.report.headline, subtitle=b.report.deck or b.report.headline, date=day, scenes=scenes)
    notes = DraftNotes(bundle_id=b.report.report_id, sections=len(b.sections), scenes=len(scenes), boundaries=bounds,
                       chapters=chapters, rewrite_required=marks, tts=tts_notes,
                       emphasis_dropped=[e for e in all_em if e not in used_em], mentions=ment, date_sources=dsrc,
                       unmatched=[u.id for u in join.unmatched], skipped_sections=skipped)
    return script, notes


def _block(obj: object, indent: int) -> list[str]:
    text = yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=1000).rstrip("\n")
    return [" " * indent + ln for ln in text.split("\n")]


def dump_draft_yaml(script: Script, notes: DraftNotes) -> str:
    """사람이 고치는 초안 YAML — 장면 경계 근거·챕터·rewrite_required 를 주석으로. 주석을 떼면 `Script` 그대로."""
    by_scene = {bd.scene: bd for bd in notes.boundaries}
    chap: dict[str, list[str]] = {}
    for c in notes.chapters:
        chap.setdefault(c.scene, []).append(c.title)
    marks = {m.sid: m.patterns for m in notes.rewrite_required}
    lines = [f"# 번들 초안 — {notes.bundle_id} (bundle.to_script, 12 §5). 초안이다: 장면 구성·문장은 ScriptWorker·사람이 다듬는다.",
             f"# 섹션 {notes.sections}개 → 장면 {notes.scenes}개. sources 는 검증(claims.json) 뒤 채운다.",
             f"# 문장 날짜: 번들 timeline 과 대응 {sum(v == 'timeline' for v in notes.date_sources.values())}문장, "
             f"나머지 {sum(v == 'report' for v in notes.date_sources.values())}문장은 date_source: report(번들 generated_at — 사건일 아님, facts 날짜로 바로잡을 것)",
             f"# rewrite_required {len(notes.rewrite_required)}문장 · 엔티티 unmatched {len(notes.unmatched)}"
             + (f" ({', '.join(notes.unmatched)})" if notes.unmatched else "")]
    head = script.model_dump(mode="json", exclude_none=True)
    scenes = head.pop("scenes")
    lines += _block(head, 0) + ["scenes:"]
    for sc in scenes:
        bd = by_scene[sc["id"]]
        lines.append(f"# ── {sc['id']} ← 섹션 {', '.join(bd.sections)} · {bd.reason}")
        if chap.get(sc["id"]):
            lines.append(f"#    챕터명 후보(화면 문장 아님): {' / '.join(chap[sc['id']])}")
        lines.append(f"- id: {sc['id']}")
        lines.append("  sentences:")
        for k, s in enumerate(sc["sentences"]):
            sid = f"{sc['id']}_{k}"
            if sid in marks:
                lines.append(f"  # rewrite_required: true — 걸린 금지 문구 패턴: {' | '.join(marks[sid])}")
            if notes.date_sources.get(sid) == "timeline":
                lines.append("  # date_source: timeline")
            if sid in notes.mentions:
                lines.append(f"  # 언급(폴백 탐지): {', '.join(notes.mentions[sid])}")
            blk = _block([s], 2)
            lines += blk
    return "\n".join(lines) + "\n"


__all__ = ["timeline_date", "Boundary", "Chapter", "DraftNotes", "RewriteMark", "TtsNote", "banned_hits", "build_draft", "dump_draft_yaml",
           "group_parts"]
