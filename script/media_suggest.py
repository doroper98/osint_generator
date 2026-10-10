"""문장 → 미디어 형태 자동 제안 (v2.5.5, back_and_forth D-0036 작업 6, 14 §10.2·§10.3-1).

문장 내용의 트리거 낱말(rules media_beats.triggers)로 형태(영상·사진·컷아웃·기사)를 **제안만** 한다.
연출 확정·자산 선택은 LLM+사용자(15 P8) — 이벤트를 만들지 않는다. 원고가 문장에 `media` 를 이미 적었으면 그것을 따른다.
provenance `media.suggested/used` 로 제안과 실제 사용을 나란히 남긴다(뱃지 제안과 같은 방식).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from rules import load_rules
from script.schema import Plan

PRIORITY: tuple[str, ...] = ("article", "clip", "cutout", "photo")   # 인용 문장은 기사, 움직임은 영상(14 §10.2 표 순서)
EVENT_OF = {"photo": "photo", "clip": "clip", "cutout": "cutout", "article": "article"}


class MediaSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sid: str
    scene: str
    kind: Literal["photo", "clip", "cutout", "article"]
    trigger: str
    at: float                      # 문장 시작(확정 시각은 연출이 단어 앵커로 정한다)
    source: Literal["trigger", "script"]
    asset_id: Optional[str] = None


def suggest_media(plan: Plan, script_media: dict[str, dict] | None = None,
                  article_sids: set[str] | None = None) -> list[MediaSuggestion]:
    """article_sids(v5.19.0 D-0163 §2) = 확인된 기사 출처를 인용한 문장 — 기사 트리거("밝혔·확인했" 등)는 매체가 주어일 때만 기사라서
    이 문장들에서만 센다. None = 원고·claims 를 모름(옛 호출) — 모든 문장에서 센다."""
    trig = load_rules().media_beats.triggers
    out: list[MediaSuggestion] = []
    for s in plan.sentences:
        cue = (script_media or {}).get(s.sid)
        if cue:
            out.append(MediaSuggestion(sid=s.sid, scene=s.scene, kind=cue["kind"], trigger=cue.get("at") or "",
                                       at=round(s.t0, 2), source="script", asset_id=cue.get("asset_id")))
            continue
        for kind in PRIORITY:
            if kind == "article" and article_sids is not None and s.sid not in article_sids:
                continue
            hit = next((w for w in trig.get(kind, []) if w in s.text), None)
            if hit:
                out.append(MediaSuggestion(sid=s.sid, scene=s.scene, kind=kind, trigger=hit, at=round(s.t0, 2), source="trigger"))
                break
    return out


def media_usage(plan: Plan, events: list[dict], article_sids: set[str] | None = None) -> dict:
    """provenance `media`: 제안 장면·형태, 실제 쓰인 미디어, 둘이 맞은 장면."""
    sug = suggest_media(plan, article_sids=article_sids)
    used = [{"mid": e["mid"], "kind": EVENT_OF[e["type"]], "t0": round(e["t0"], 2)} for e in events if e["type"] in EVENT_OF]
    scene_of = {s.sid: s.scene for s in plan.sentences}
    by_t = sorted((s.t0, s.scene) for s in plan.sentences)

    def scene_at(t: float) -> str:
        sc = by_t[0][1]
        for t0, name in by_t:
            if t0 <= t + 1e-6:
                sc = name
        return sc

    used_pairs = {(scene_at(u["t0"]), u["kind"]) for u in used}
    sug_pairs = {(scene_of[s.sid], s.kind) for s in sug}
    return {"suggested": [s.model_dump() for s in sug], "used": used,
            "suggested_and_used": sorted(f"{sc}:{k}" for sc, k in sug_pairs & used_pairs)}
