"""provenance — 이번 영상에 실제로 쓰인 기능의 증명 (v2.1.0, 15 P5, tools/legacy_provenance 의 엔진 내장판).

코드에 있는 기능이 아니라 이 연출로 렌더될 때 호출되는 것만 센다. 돌지 않은 단계(AI 연출·시각 검수)는 기록하지 않는다.
"""

from __future__ import annotations

import collections

from engine.camera import CamKey
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


def build(plan: Plan, keys: list[CamKey], events: list[dict], repo_version: str, stages: dict[str, bool],
          word_anchors: list[dict] | None = None) -> dict:
    anchors = word_anchors or []
    modes = sorted({a["mode"] for a in anchors})
    return {
        "schema_version": 1,
        "engine": "engine",
        "repo_version": repo_version,
        "rules_version": load_rules().rules_version,
        "rules_hash": rules_hash(),
        "prompts": {},          # Phase 2 는 LLM 단계 없음 — 사람이 쓴 원고·연출
        "voice": plan.voice,
        "word_anchor": modes[0] if len(modes) == 1 else ("mixed" if modes else "none"),  # v2.3.0 aligned|ratio (03 §6.3)
        "word_anchors": anchors,
        "total_sec": round(float(plan.total), 3),
        "sentences": len(plan.sentences),
        "stages": stages,       # 이번 산출물에 실제로 쓰인 단계
        "features_used": features(keys, events),
        "qa": {"auto_iterations": 0, "user_approved": False, "reviewer": "fable (back_and_forth)"},
        "drops": [],
    }
