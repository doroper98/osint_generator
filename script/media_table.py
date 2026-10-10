"""미디어 계획 표 (v5.19.0, back_and_forth D-0163 §2·D-0173 §3 P1-0).

사용자 지적(D156): "기사 조판이나 기사에 들어간 사진이 영상에 적게 또는 아예 안 나오는 일이 많다." 원인 중 하나는 "0건이어도
막지 않는다"(2026-10-05)가 조용한 빈약으로 이어진 것 — 요약은 있었지만 사용자가 연출 전에 보지 못했다(PIPELINE-AP-019).

이 모듈은 연출 **전**(게이트 ①)에 문장별 표를 만든다:
  인용 출처(claims → sources) · 기사 등록 여부(레지스트리 article) · 사진(찾은 수/권리 통과 수/선택) · 사유.
- 기사 카드 후보 = 확인된(confirmed) 기사 출처를 인용하고 그 기사가 레지스트리에 등록된 문장(`article_candidates`).
  연출이 쓰지 않으면 엔진 검사 `[article-unused]`(engine.media_plan.article_usage).
- 사진 목표 = 러닝타임(분) × rules media.density.photo_target_per_min(내림). 선택 수(원고 문장 media 의 사진 asset_id)가 모자라면
  사진 후보 문장(트리거·검색 기록·원고 query) 마다 사유가 있어야 한다 — media_notes.yaml photo, 또는 검색 기록의 권리 통과 0.
  사유가 없으면 표의 errors → 게이트 ① 승인 거부(orchestrator.project_manager.require_media_plan, P6).
파일은 읽기만 한다.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

from rules import load_rules
from schemas.media_models import MediaNotes, MediaSearch, MediaSearchLog
from script.schema import Script

NOTES_FILE = "media_notes.yaml"
SEARCH_FILE = "media_search.json"
CHARS_PER_MIN: int = 320   # 예상 길이 추정(plan.json 이 아직 없을 때): 한국어 발화 분당 글자 수(prompts/script.md 가정과 같음)
PHOTO_KINDS: tuple[str, ...] = ("photo", "clip", "cutout")   # 사진 후보 문장을 정하는 트리거 형태(rules media_beats.triggers)


class MediaTableError(ValueError):
    """media_notes.yaml·media_search.json 이 깨졌거나 원고와 맞지 않는다."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MediaRow(_Strict):
    sid: str
    text: str
    claims: list[str]
    article_sources: list[str]            # 확인된 기사 출처 id
    article_mids: list[str]               # 그중 레지스트리에 등록된 기사 조판 mid
    article_unregistered: list[str]       # 등록 안 된 기사 출처 id(tools/article_register.py 로 등록)
    article_trigger: Optional[str] = None   # 기사 트리거 낱말(기사 출처를 인용한 문장에서만 센다 — "매체 주어")
    photo_candidate: bool                 # 사진 후보 문장(트리거·검색 기록·원고 query)
    photo_trigger: Optional[str] = None
    found: int = 0
    passed: int = 0
    selected: Optional[str] = None        # 원고 문장 media 의 사진 asset_id(레지스트리 등록)
    reason: Optional[str] = None          # 사진 사유(media_notes photo 또는 검색 기록 요약)
    article_note: Optional[str] = None


class MediaTable(_Strict):
    schema_version: int = 1
    total_sec: float
    total_source: str                     # plan | chars
    photo_target: int
    photo_selected: int
    article_candidates: int
    rows: list[MediaRow] = Field(default_factory=list)
    project_photo: Optional[str] = None
    errors: list[str] = Field(default_factory=list)


def _script(pdir: Path) -> Script:
    return Script.model_validate(yaml.safe_load((pdir / "script.yaml").read_text(encoding="utf-8")))


def sentence_ids(sc: Script) -> list[tuple[str, object]]:
    return [(f"{scene.id}_{k}", s) for scene in sc.scenes for k, s in enumerate(scene.sentences)]


def load_notes(pdir: Path, sids: set[str] | None = None) -> MediaNotes:
    """media_notes.yaml(없으면 빈 것). sids 를 주면 원고에 없는 문장 id = MediaTableError(낡은 사유)."""
    p = pdir / NOTES_FILE
    if not p.exists():
        return MediaNotes()
    try:
        doc = MediaNotes.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    except (ValueError, yaml.YAMLError) as ex:
        raise MediaTableError(f"{p}: {ex}") from ex
    stale = sorted(set(doc.sentences) - sids) if sids is not None else []
    if stale:
        raise MediaTableError(f"{p}: 원고에 없는 문장 id {stale} — 원고가 바뀌었다. 사유를 지우거나 새 id 로 옮긴다")
    return doc


def load_searches(pdir: Path) -> list[MediaSearch]:
    p = pdir / SEARCH_FILE
    if not p.exists():
        return []
    try:
        return MediaSearchLog.model_validate_json(p.read_text(encoding="utf-8")).searches
    except ValueError as ex:
        raise MediaTableError(f"{p}: {ex}") from ex


def _registry():  # noqa: ANN202 — dict[str, MediaAsset]
    from engine.media_registry import load_media_registry  # noqa: PLC0415

    return load_media_registry()


def article_mid_index(reg: dict) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    """레지스트리 기사 → (url → mid, (매체, 날짜) → mid). url 없는 옛 항목(v3 이관, D51)은 매체·날짜로 잇는다."""
    by_url: dict[str, str] = {}
    by_pub: dict[tuple[str, str], str] = {}
    for mid, a in reg.items():
        if a.kind != "article":
            continue
        if a.url:
            by_url.setdefault(a.url, mid)
        by_pub.setdefault((a.credit_author, str(a.date)), mid)
    return by_url, by_pub


def _trigger(text: str, kinds: tuple[str, ...], trig: dict[str, list[str]]) -> tuple[Optional[str], Optional[str]]:
    for kind in kinds:
        hit = next((w for w in trig.get(kind, []) if w in text), None)
        if hit:
            return kind, hit
    return None, None


def article_sids(pdir: Path) -> set[str]:
    """확인된 기사 출처를 인용한 문장 id — 기사 트리거("밝혔·확인했" 등 매체 주어)를 셀 수 있는 문장(D-0163 §2)."""
    return {r.sid for r in build_rows(pdir)[0] if r.article_sources}


def estimate_total(pdir: Path, sc: Script | None = None) -> tuple[float, str]:
    """러닝타임(초)과 근거. plan.json 이 있으면 실측, 없으면 글자 수 추정(CHARS_PER_MIN)."""
    pp = pdir / "plan.json"
    if pp.exists():
        return float(json.loads(pp.read_text(encoding="utf-8"))["total"]), "plan"
    sc = sc or _script(pdir)
    return sum(len(s.tts or s.text) for _, s in sentence_ids(sc)) / CHARS_PER_MIN * 60, "chars"


def build_rows(pdir: Path) -> tuple[list[MediaRow], MediaNotes]:
    from schemas.source_models import ClaimsFile, SourcesFile  # noqa: PLC0415

    sc = _script(pdir)
    ids = sentence_ids(sc)
    notes = load_notes(pdir, {sid for sid, _ in ids})
    cp, sp = pdir / "intake" / "claims.json", pdir / "intake" / "sources.json"
    claims = ClaimsFile.model_validate_json(cp.read_text(encoding="utf-8")).by_id() if cp.exists() else {}
    srcs = SourcesFile.model_validate_json(sp.read_text(encoding="utf-8")).by_id() if sp.exists() else {}
    rules = load_rules()   # 한 번만 읽는다(문장마다 YAML 을 다시 읽지 않게)
    refs, trig = rules.source_note.publishers, rules.media_beats.triggers
    reg = _registry()
    by_url, by_pub = article_mid_index(reg)
    searches: dict[str, list[MediaSearch]] = {}
    for s in load_searches(pdir):
        searches.setdefault(s.sid, []).append(s)
    rows: list[MediaRow] = []
    for sid, s in ids:
        cl = [c for c in s.sources if c in claims]
        art_src: list[str] = []
        for c in cl:
            for x in claims[c].source_ids:
                src = srcs.get(x)
                if (src is not None and src.type == "article" and src.confirmed and x not in art_src
                        and not any(str(src.publisher).startswith(p) for p in refs)):
                    art_src.append(x)
        mids: list[str] = []
        unreg: list[str] = []
        for x in art_src:
            src = srcs[x]
            mid = by_url.get(src.url or "") or by_pub.get((src.publisher, str(src.published_at)))
            if mid is None:
                unreg.append(x)
            elif mid not in mids:
                mids.append(mid)
        _, art_hit = _trigger(s.text, ("article",), trig) if art_src else (None, None)
        pk, phit = _trigger(s.text, PHOTO_KINDS, trig)
        cue = s.media
        sel = cue.asset_id if cue is not None and cue.kind == "photo" and cue.asset_id in reg and reg[cue.asset_id].kind == "photo" else None
        ss = searches.get(sid, [])
        found, passed = sum(x.found for x in ss), sum(x.passed for x in ss)
        cand = bool(pk) or bool(ss) or (cue is not None and cue.kind in PHOTO_KINDS)
        note = notes.sentences.get(sid)
        reason = note.photo if note is not None and note.photo else None
        if reason is None and ss and passed == 0:   # 검색 기록 자체가 사유(검색어·결과·라이선스 탈락)
            reason = "검색 " + "; ".join(f"{x.pool} '{x.query}' {x.found}건·통과 0" + (f"({', '.join(x.rejected[:2])})" if x.rejected else "")
                                         for x in ss)
        rows.append(MediaRow(sid=sid, text=s.text, claims=cl, article_sources=art_src, article_mids=mids, article_unregistered=unreg,
                             article_trigger=art_hit, photo_candidate=cand, photo_trigger=phit, found=found, passed=passed,
                             selected=sel, reason=reason, article_note=note.article if note is not None else None))
    return rows, notes


def article_candidates(pdir: Path) -> dict[str, list[str]]:
    """기사 카드 후보: 문장 id → 등록된 기사 mid(확인된 기사 출처를 인용, D-0163 §2). 원고·claims 가 없으면 {}."""
    if not (pdir / "script.yaml").exists():
        return {}
    return {r.sid: r.article_mids for r in build_rows(pdir)[0] if r.article_mids}


def media_table(pdir: Path, total_sec: float | None = None) -> MediaTable:
    """게이트 ① 미디어 계획 표. errors 가 비어야 게이트 ① 승인(사진 목표 미달 = 문장 단위 사유 필수, P6)."""
    sc = _script(pdir)
    rows, notes = build_rows(pdir)
    src = "given"
    if total_sec is None:
        total_sec, src = estimate_total(pdir, sc)
    D = load_rules().media.density  # noqa: N806
    target = math.floor(total_sec / 60 * D.photo_target_per_min)
    selected = sum(1 for r in rows if r.selected)
    errs: list[str] = []
    if selected < target:
        cands = [r for r in rows if r.photo_candidate and not r.selected]
        for r in cands:
            if r.reason is None:
                why = f"권리 통과 후보 {r.passed}건이 있는데 고르지 않았다" if r.passed else "검색 기록·사유 없음"
                errs.append(f"[photo-reason] {r.sid}: 사진 후보 문장({r.photo_trigger or '검색·원고 query'}) — {why}. "
                            f"`tools/media_fetch.py search --log {pdir} --sid {r.sid} \"검색어\"` 또는 {NOTES_FILE} sentences.{r.sid}.photo")
        if not cands and not notes.project_photo:
            errs.append(f"[photo-reason] 사진 {selected}/{target}장(분당 {D.photo_target_per_min:g}) — 사진 후보 문장이 없다. "
                        f"{NOTES_FILE} project_photo 에 이 영상에 사진이 없는 이유를 적는다")
    return MediaTable(total_sec=round(total_sec, 1), total_source=src, photo_target=target, photo_selected=selected,
                      article_candidates=sum(1 for r in rows if r.article_mids), rows=rows,
                      project_photo=notes.project_photo, errors=errs)


def table_lines(t: MediaTable) -> list[str]:
    """게이트 ① 텍스트 표(사용자에게 원고와 함께 보낸다)."""
    D = load_rules().media.density  # noqa: N806
    out = [f"미디어 계획 표 — 사진 {t.photo_selected}/{t.photo_target}장(분당 {D.photo_target_per_min:g}, "
           f"{t.total_sec:.0f}초 {'실측' if t.total_source == 'plan' else '추정'}) · 기사 카드 후보 {t.article_candidates}문장"
           f"(60초당 {D.article_per_min_max}개까지 쓴다)",
           "  문장         인용 출처              기사(등록/미등록)        사진 찾음/통과/선택      사유"]
    for r in t.rows:
        art = (",".join(r.article_mids) or "-") + (f" / 미등록 {len(r.article_unregistered)}" if r.article_unregistered else "")
        ph = f"{r.found}/{r.passed}/{r.selected or '-'}" + (f" ({r.photo_trigger})" if r.photo_trigger else "")
        why = r.reason or ("" if not r.photo_candidate or r.selected else "(사유 없음)")
        out.append(f"  {r.sid:<12} {','.join(r.claims) or '(출처 없음)':<22} {art:<24} {ph:<22} {why}")
    if t.project_photo:
        out.append(f"  영상 전체 사진 사유: {t.project_photo}")
    out += [f"  오류 {e}" for e in t.errors] or ["  표 판정 — 통과"]
    return out


__all__ = ["MediaRow", "MediaTable", "MediaTableError", "article_candidates", "article_sids", "build_rows", "estimate_total",
           "load_notes", "load_searches", "media_table", "table_lines"]
