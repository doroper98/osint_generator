"""provenance — 이번 영상에 실제로 쓰인 기능의 증명 (v2.1.0, 15 P5, tools/legacy_provenance 의 엔진 내장판).

코드에 있는 기능이 아니라 이 연출로 렌더될 때 호출되는 것만 센다. 돌지 않은 단계(AI 연출·시각 검수)는 false 로 둔다 — ai_direction_summary 가 워커 산출 파일로 증명할 때만 true(v3.1.0).
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
from pathlib import Path
from typing import Callable

from engine.camera import CamKey
from engine.refs import emblem_ids
from rules import load_rules, rules_hash
from script.schema import Plan


def features(keys: list[CamKey], events: list[dict]) -> dict:
    by = collections.Counter(e["type"] for e in events)
    media = {k: by.get(k, 0) for k in ("clip", "photo", "cutout", "article")}
    return {
        "camera_keys": len(keys),
        "camera_moves": sum(1 for c in keys if c.mode == "move"),
        "camera_cuts": sum(1 for c in keys if c.mode == "cut"),
        "dips": by.get("dip", 0),
        "dips_under": sum(1 for e in events if e["type"] == "dip" and e.get("under")),
        "badges": by.get("badge", 0),
        "badge_kinds": dict(collections.Counter(e.get("kind") for e in events if e["type"] == "badge")),
        "panels": [e["kind"] for e in events if e["type"] == "panel"],
        "cards": by.get("card", 0),
        "media": media,
        "event_types": dict(sorted(by.items())),
        "label_lod": True,   # draw_labels 는 패널이 화면을 덮지 않은 모든 프레임에서 w 별 LOD 로 호출된다
        "vignette": False,   # 비네트 없음(라운드 6) — 엔진에 이식하지 않았다(부록 D)
        "private_only_assets": private_only_assets(events),   # v7.3.0 사용자 결정 D234 — 비공개 시청 한정 자산(있으면 공개용 산출물이 아니다)
        **({"flight": {"count": len(fl), "kinds": dict(collections.Counter(e["kind"] for e in fl)),
                       "insets": sorted(e["inset"]["mid"] for e in fl if e.get("inset"))}}
           if (fl := [e for e in events if e["type"] == "flight"]) else {}),   # v7.3.0 D-0206 §4 — 비행·인셋 사용 수(없으면 기록 없음, P5)
        **({"route_cross_exempt": ex} if (ex := [{"label": e.get("label"), **e["route_cross_exempt"]} for e in events
                                                  if e.get("route_cross_exempt")]) else {}),   # v5.21.11 D-0203 — 적용된 면제(P5)
    }


def private_only_assets(events: list[dict]) -> list[str]:
    """v7.3.0 D234 — 이 연출이 쓰는 미디어 중 scope private_only(비공개 시청 한정)인 mid. 비어 있지 않으면 공개 배포 금지."""
    from engine.media_registry import cached_registry  # noqa: PLC0415

    reg = cached_registry()
    mids = {e.get("mid") for e in events} | {e["inset"]["mid"] for e in events if e["type"] == "flight" and e.get("inset")}
    return sorted(m for m in mids if m in reg and reg[m].scope == "private_only")


def feedback_guards(checks: dict) -> list[dict]:
    """v5.22.0 D-0200 — 이번 렌더에서 돈 사용자 의견 장치(check 종류)와 결과: [{id, checks: {검사 id: 건수 | "skipped"}}].
    원장 장치 중 본 엔진 검사만(테스트·규칙 키는 렌더에서 돌지 않는다 — 기록하지 않는다, P5)."""
    from rules import load_user_feedback  # noqa: PLC0415

    by = {i["id"]: ("skipped" if i.get("skipped") else i["count"]) for i in checks.get("items", [])}
    out = []
    for e in load_user_feedback().entries:
        ran = {g.ref: by[g.ref] for g in e.guards if g.kind == "check" and g.ref in by}
        if ran:
            out.append({"id": e.id, "checks": ran})
    return out


def direction_sha1(root: Path) -> str | None:
    """연출 파일 지문(v5.22.5 D208) — 프리뷰가 남기고 mux 가 대조한다. 연출 파일이 없으면 None."""
    dp = root / "direction.yaml"
    return hashlib.sha1(dp.read_bytes()).hexdigest() if dp.exists() else None


def preview_carry(root: Path) -> dict | None:
    """v5.22.5 D208 — 전편 provenance 에 옮겨 적을 프리뷰 검사 결과: {source, direction_sha1, from_current_direction,
    checks, user_feedback_guards}. 전편 렌더는 검사를 다시 돌리지 않으므로 게이트 ② 앞 프리뷰(prev/)의 결과를 출처와 함께 싣는다.
    프리뷰가 연출 지문을 남기지 않았으면 from_current_direction = None(대조 불가 — 숨기지 않고 그대로 적는다, P6).
    프리뷰가 돌지 않았으면 None(기록 없음, P5)."""
    pp = root / "prev" / "provenance.json"
    if not pp.exists():
        return None
    pv = json.loads(pp.read_text(encoding="utf-8"))
    if "checks" not in pv:
        return None
    psha = (pv.get("preview") or {}).get("direction_sha1")
    return {"source": "prev/provenance.json", "direction_sha1": psha,
            "from_current_direction": None if psha is None else psha == direction_sha1(root),
            "checks": pv["checks"], "user_feedback_guards": pv.get("user_feedback_guards", [])}


def _versions(d: Path, stem: str, suffix: str) -> list[Path]:
    """{stem}.v{n}{suffix} 를 번호순으로(수정 기록은 v2 부터 — v1 은 연출가 초안)."""
    pat = re.compile(rf"^{re.escape(stem)}\.v(\d+){re.escape(suffix)}$")
    hits = [(int(m.group(1)), q) for q in d.glob(f"{stem}.v*{suffix}") if (m := pat.match(q.name))] if d.exists() else []
    return [q for _, q in sorted(hits)]


def ai_direction_summary(root: Path) -> dict | None:
    """AI 연출·검수 기록(v3.1.0, 17 §1·D-0047 작업 9). 워커 산출 파일만 읽는다(엔진은 워커를 import 하지 않음, 15 P1).
    direction.meta.json(origin ai)이 없으면 None — 사람 연출. 현재 direction.yaml 이 마지막 AI 보관본과 다르면
    origin "ai+human_edit"(사람이 고친 AI 연출)로 적는다 — 돌지 않은 단계·바뀐 내용을 AI 산출로 주장하지 않는다(15 P5)."""
    meta_p = root / "direction.meta.json"
    if not meta_p.exists():
        return None
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    if meta.get("origin") != "ai":
        return None
    vers = _versions(root, "direction", ".yaml")
    cur = (root / "direction.yaml").read_bytes() if (root / "direction.yaml").exists() else b""
    edited = not any(v.read_bytes() == cur for v in vers)   # 판 선택(D-0049)으로 앞 판이 쓰일 수 있다
    qa = []
    for p in _versions(root / "prev", "qa_verdict", ".json"):
        v = json.loads(p.read_text(encoding="utf-8"))
        iss = v.get("issues", [])
        qa.append({"file": p.name, "verdict": v.get("verdict"), "hard": sum(1 for i in iss if i.get("severity") == "hard"),
                   "soft": sum(1 for i in iss if i.get("severity") == "soft")})
    raw = [json.loads(p.read_text(encoding="utf-8")) for p in _versions(root / "prev", "revision", ".json")]
    revs = [{"direction_version": r.get("direction_version"), "changes": len(r.get("changelog", [])),
             **({"base_human_edit": True} if r.get("base_human_edit") else {})} for r in raw]
    used = next((int(v.stem.rsplit(".v", 1)[1]) for v in reversed(vers) if v.read_bytes() == cur), None)
    # v5.21.5 D-0190 §3-2 — 쓰인 판의 계보(그 판 번호 이하 수정)에 사람 손질 바탕이 있으면 사람 손질이 섞인 연출이다
    upto = used if used is not None else max((r.get("direction_version") or 0 for r in raw), default=0)
    human = sorted(r["direction_version"] for r in raw if r.get("base_human_edit") and (r.get("direction_version") or 0) <= upto)
    edited = edited or bool(human)
    loop_p = root / "prev" / "qa_loop.json"
    loop = json.loads(loop_p.read_text(encoding="utf-8")) if loop_p.exists() else {}
    return {"origin": "ai+human_edit" if edited else "ai", **({"human_edit_revisions": human} if human else {}),
            "model": meta.get("model"), "prompt_sha1": meta.get("prompt_sha1"),
            "direction_versions": len(vers), "used_version": used, "selected": loop.get("selected"),
            "rounds": [{k: r.get(k) for k in ("version", "checks_hard", "qa_hard", "qa_soft")} for r in loop.get("rounds", [])],
            "revisions": revs, "visual_qa": qa}


def bundle_summary(root: Path) -> dict | None:
    """provenance `bundle`(v3.5.0 D-0063 작업 5): import-bundle 기록(intake/bundle_import.json)과 ScriptWorker 기록
    (script.meta.json draft_sha1)만 읽는다(엔진은 오케스트레이터·워커를 import 하지 않음, 15 P1). 번들 프로젝트가 아니면 None
    — 돌지 않은 단계를 기록하지 않는다(P5). draft_used = 지금 원고를 만든 ScriptWorker 가 초안 블록을 받았나."""
    p = root / "intake" / "bundle_import.json"
    if not p.exists():
        return None
    r = json.loads(p.read_text(encoding="utf-8"))
    d = r.get("draft", {})
    meta_p = root / "script.meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    return {"bundle_id": r.get("bundle_id"), "generated_at": r.get("generated_at"), "producer": r.get("producer"),
            "sources_imported": len(r.get("imported_sources", [])), "sources_unresolved": len(r.get("unresolved_sources", [])),
            "claim_hints": r.get("claim_hints", 0), "sections": d.get("sections"), "scenes": d.get("scenes"),
            "rewrite_required": d.get("rewrite_required"), "unmatched": d.get("unmatched"),
            "panels": d.get("panels"), "unsupported_charts": d.get("unsupported_charts"),
            "draft_used": bool(meta.get("draft_sha1"))}


def camera_summary(root: Path, keys: list[CamKey], stage: object) -> dict:
    """provenance `camera` (v3.3.0 D-0056 작업 5·9): 제안(suggested)과 사용(used)을 가른다 — 제안은 옵션(P8).
    suggested = prev/camera_suggest.json 이 있고 제안이 나온 숏 수(없으면 0, 파일 없음 = 돌지 않음 → 기록 false).
    used = 지금 카메라 키 가운데 제안값과 같은(소수 셋째 자리) 키 수. given_to_director = 연출가가 제안 파일을 입력으로 받았나."""
    from engine.camera_suggest import load_suggest  # noqa: PLC0415

    cs = load_suggest(root)
    meta_p = root / "direction.meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    given = bool(meta.get("camera_suggest_sha1"))
    if cs is None:
        return {"suggest_ran": False, "suggested": 0, "used": 0, "given_to_director": given}
    dp = root / "direction.yaml"
    cur_sha = hashlib.sha1(dp.read_bytes()).hexdigest() if dp.exists() else ""
    sug = [s.suggested for s in cs.shots if s.suggested is not None]
    anchors = [stage.from_world(k.x, k.y) for k in keys]   # type: ignore[attr-defined] — 월드 → 앵커(lon·lat, v4.1.0)
    used = sum(1 for k, a in zip(keys, anchors) if any(round(g.lon, 3) == round(a["lon"], 3) and round(g.lat, 3) == round(a["lat"], 3)
                                                       and round(g.w, 3) == round(k.w, 3) for g in sug))
    return {"suggest_ran": True, "suggested": len(sug), "used": used, "given_to_director": given,
            "from_current_direction": cs.direction_sha1 == cur_sha,
            "fits": sum(1 for s in cs.shots if s.fits), "current_fits_false": sum(1 for s in cs.shots if s.current_fits is False)}


def emblem_usage(events: list[dict], emblem_flag: Callable[[str], str | None]) -> dict:
    """휘장 뱃지의 실제 처리(D-0029 작업 3): 휘장 그대로 쓴 id 와 국기로 대체한 id."""
    used: set[str] = set()
    fallback: dict[str, str] = {}
    for e in events:
        for img in emblem_ids(e):   # 뱃지·패널 노드 모두
            fb = emblem_flag(img)
            if fb is None:
                used.add(img)
            else:
                fallback[img] = fb
    return {"used": sorted(used), "flag_fallback": dict(sorted(fallback.items()))}


def build(plan: Plan, keys: list[CamKey], events: list[dict], repo_version: str, stages: dict[str, bool],
          word_anchors: list[dict] | None = None, assets: dict | None = None) -> dict:
    anchors = word_anchors or []
    modes = sorted({a["mode"] for a in anchors})
    feats = features(keys, events)
    feats["at_word"] = {"aligned": sum(1 for a in anchors if a["mode"] == "aligned"),
                        "ratio": sum(1 for a in anchors if a["mode"] == "ratio")}
    if plan.lint_waived:   # v5.17.0 D-0168 — 면제로 통과한 린트(없으면 쓰지 않는다, P5)
        feats["lint"] = {"waived": plan.lint_waived}
    rows = [s.alignment for s in plan.sentences if s.alignment is not None]
    if rows:   # v5.16.0 D-0164 §5-4 — plan 이 정렬을 기록했을 때만(돌지 않은 단계는 적지 않는다, P5)
        scores = [r.score_mean for r in rows if r.score_mean is not None]
        feats["alignment"] = {"sources": dict(sorted({r.source: sum(1 for q in rows if q.source == r.source) for r in rows}.items())),
                              "score_mean_min": min(scores) if scores else None,
                              "elapsed_ms_total": sum(r.elapsed_ms or 0 for r in rows)}
    ff = [s.prosody.final_fall for s in plan.sentences if s.prosody is not None]
    if ff:   # v5.20.0 D-0175 — 문장 끝 억양 보정이 돌았을 때만(P5)
        feats["prosody"] = {"final_fall": {"applied_n": sum(r.applied for r in ff), "skipped_n": sum(not r.applied for r in ff)}}
    return {
        "schema_version": 1,
        "engine": "engine",
        "repo_version": repo_version,
        "rules_version": load_rules().rules_version,
        "rules_hash": rules_hash(),
        "prompts": {},          # 사람 연출이면 비어 있다 — AI 연출은 engine.mux.project_provenance 가 채운다(v3.1.0)
        "voice": plan.voice,
        "word_anchor": modes[0] if len(modes) == 1 else ("mixed" if modes else "none"),  # v2.3.0 aligned|ratio (03 §6.3)
        "word_anchors": anchors,
        "tts": {"resynthesized": list(plan.tts_resynthesized)},   # 정렬 없어 재합성한 문장(D34)
        "total_sec": round(float(plan.total), 3),
        "sentences": len(plan.sentences),
        "stages": stages,       # 이번 산출물에 실제로 쓰인 단계
        "features_used": feats,
        "qa": {"auto_iterations": 0, "user_approved": False, "reviewer": "fable (back_and_forth)"},
        "drops": [],
        **({"assets": assets} if assets is not None else {}),   # v2.4.0 — 이미지 키·휘장 처리·뱃지 제안/사용
        "panels": {"used": panels_used(events)},                 # v2.5.0 — 패널마다 종류·제목·추정 태그(08 §9)
    }


def panels_used(events: list[dict]) -> list[dict]:
    from engine.panels.base import prov_tag_text  # noqa: PLC0415

    return [{"kind": e["kind"], "title": e["title"], "t0": round(e["t0"], 2), "prov_tag": prov_tag_text(e.get("provenance"))}
            for e in events if e["type"] == "panel"]
