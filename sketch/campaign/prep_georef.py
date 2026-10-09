"""참고 작전도 정합 CLI — 참고 SVG + spec fronts.georef → `projects/<pid>/<spec.fronts.file>`(D-0145 §1, SK-G1).

    python -m sketch.campaign.prep_georef projects/<pid>

잔차가 rules sketch.checks.georef_residual_deg 를 넘거나 눈금 교차점이 모자라면 파일을 쓰지 않고 실패한다(P6).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rules import load_rules
from sketch.campaign.spec import CampaignSpec
from sketch.common.spec import load_spec
from sketch.common.svg_georef import georef

FAIL = 1


def build(project: Path, spec: CampaignSpec) -> dict:
    fr = spec.fronts
    out, fit = georef(project / fr.reference.file, [s.model_dump() for s in fr.style_map], fr.graticule.model_dump())
    lim = load_rules().sketch.checks.georef_residual_deg
    if fit.residual_deg > lim:
        raise ValueError(f"SK-G1 눈금 정합 잔차 {fit.residual_deg:.4f}° > {lim}°")
    return {"schema_version": 1, "source": fr.source, "residual_deg": round(fit.residual_deg, 6),
            "residual": {"lon": round(fit.residual_lon, 6), "lat": round(fit.residual_lat, 6)},
            "coef": {"lon": fit.coef_lon.tolist(), "lat": fit.coef_lat.tolist()}, **out}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m sketch.campaign.prep_georef", description="참고 작전도(SVG) → 경위도 전선·강(fronts.json)")
    ap.add_argument("project", type=Path)
    args = ap.parse_args(argv)
    spec = load_spec(args.project, CampaignSpec)
    try:
        doc = build(args.project, spec)
    except ValueError as e:
        print(e, file=sys.stderr)
        return FAIL
    for d, sides in doc["layers"].items():
        print(d, {s: len(v) for s, v in sides.items()})
    print("rivers", {k: len(v) for k, v in doc["rivers"].items()}, "잔차", doc["residual"])
    dest = args.project / spec.fronts.file
    dest.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
