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
    }


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
    revs = [{"direction_version": r.get("direction_version"), "changes": len(r.get("changelog", []))}
            for r in (json.loads(p.read_text(encoding="utf-8")) for p in _versions(root / "prev", "revision", ".json"))]
    used = next((int(v.stem.rsplit(".v", 1)[1]) for v in reversed(vers) if v.read_bytes() == cur), None)
    loop_p = root / "prev" / "qa_loop.json"
    loop = json.loads(loop_p.read_text(encoding="utf-8")) if loop_p.exists() else {}
    return {"origin": "ai+human_edit" if edited else "ai", "model": meta.get("model"), "prompt_sha1": meta.get("prompt_sha1"),
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


def camera_summary(root: Path, keys: list[CamKey]) -> dict:
    """provenance `camera` (v3.3.0 D-0056 작업 5·9): 제안(suggested)과 사용(used)을 가른다 — 제안은 옵션(P8).
    suggested = prev/camera_suggest.json 이 있고 제안이 나온 숏 수(없으면 0, 파일 없음 = 돌지 않음 → 기록 false).
    used = 지금 카메라 키 가운데 제안값과 같은(소수 셋째 자리) 키 수. given_to_director = 연출가가 제안 파일을 입력으로 받았나."""
    from engine.camera_suggest import load_suggest  # noqa: PLC0415
    from engine.projection import lat_of  # noqa: PLC0415

    cs = load_suggest(root)
    meta_p = root / "direction.meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    given = bool(meta.get("camera_suggest_sha1"))
    if cs is None:
        return {"suggest_ran": False, "suggested": 0, "used": 0, "given_to_director": given}
    dp = root / "direction.yaml"
    cur_sha = hashlib.sha1(dp.read_bytes()).hexdigest() if dp.exists() else ""
    sug = [s.suggested for s in cs.shots if s.suggested is not None]
    used = sum(1 for k in keys if any(round(g.lon, 3) == round(k.x, 3) and round(g.lat, 3) == round(lat_of(k.y), 3)
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
