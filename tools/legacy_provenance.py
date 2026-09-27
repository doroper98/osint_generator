"""Phase 1 provenance (v2.0.1, back_and_forth D-0006 §2 · D-0008 §3 · docs/handoff/15 P5).

legacy_v3 엔진은 provenance 를 쓰지 않는다. 이 도구는 `legacy_v3/render3.py`를 모듈로 불러 **실제 연출층**
(카메라 키 CAM, 이벤트 EV)을 세어 "이번 영상에 쓰인 기능"을 기록한다. 코드에 있는 기능이 아니라
이 plan·연출로 렌더될 때 호출되는 것만 센다. 돌지 않은 단계(AI 연출·시각 검수)는 기록하지 않는다(AP-V6-10).

사용법: python tools/legacy_provenance.py [--out docs/handoff/reports/phase1/provenance.json]
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


def load_render3() -> "object":
    os.environ.setdefault("V3_ROOT", "projects/hormuz_korea_legacy")
    argv, sys.argv = sys.argv, [sys.argv[0]]
    try:
        spec = importlib.util.spec_from_file_location("render3", REPO / "legacy_v3" / "render3.py")
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod


def features(r3: "object") -> dict:
    ev = r3.EV
    by = collections.Counter(e["type"] for e in ev)
    cams = r3.CAM
    media = {k: by.get(k, 0) for k in ("clip", "photo", "cutout", "article")}
    return {
        "camera_keys": len(cams),
        "camera_moves": sum(1 for c in cams if c[5] == "move"),
        "camera_cuts": sum(1 for c in cams if c[5] == "cut"),
        "dips": by.get("dip", 0),
        "dips_under": sum(1 for e in ev if e["type"] == "dip" and e.get("under")),
        "badges": by.get("badge", 0),
        "badge_kinds": dict(collections.Counter(e.get("kind") for e in ev if e["type"] == "badge")),
        "panels": [e["kind"] for e in ev if e["type"] == "panel"],
        "cards": by.get("card", 0),
        "media": media,
        "event_types": dict(sorted(by.items())),
        "label_lod": True,  # draw_labels 는 모든 프레임에서 w 별 LOD 로 호출된다(render_frame)
        "vignette": False,  # build_vignette 는 만들어지지만 render_frame 에서 칠하지 않는다(19a A.3)
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="legacy_v3 provenance")
    ap.add_argument("--out", type=Path, default=REPO / "docs/handoff/reports/phase1/provenance.json")
    args = ap.parse_args(argv)
    from orchestrator import __version__
    from rules import rules_hash

    r3 = load_render3()
    prov = {
        "schema_version": 1,
        "engine": "legacy_v3",
        "repo_version": __version__,
        "rules_hash": rules_hash(),
        "prompts": {},  # Phase 1 은 LLM 단계 없음 — 사람이 쓴 v3 원고·연출
        "voice": r3.P.get("voice"),
        "total_sec": round(float(r3.P["total"]), 3),
        "sentences": len(r3.P["sentences"]),
        "features_used": features(r3),
        "qa": {"auto_iterations": 0, "user_approved": False, "reviewer": "fable (back_and_forth)"},
        "drops": [],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(prov["features_used"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
