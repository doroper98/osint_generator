"""차트 정직성 보고 (v4.3.0, back_and_forth D-0084 작업 5·10).

    python tools/chart_honesty_report.py --proj projects/hormuz_korea --out docs/handoff/reports/phaseG3/chart_honesty_hormuz.json
    python tools/chart_honesty_report.py --synthetic --out docs/handoff/reports/phaseG3/chart_honesty_synthetic.json

--proj: 그 프로젝트의 마지막 프리뷰 `prev/checks.json` 에서 정직성 4항목(판정·메모)을 옮긴다(프리뷰를 먼저 돌린다 — 검사기 하나, P12).
--synthetic: tests/fixtures/honesty/synthetic.yaml 의 위반 주입 9건을 engine.honesty.judge 로 판정한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from engine.honesty import CHECK_IDS, ChartMeta, judge  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--proj", type=Path)
    g.add_argument("--synthetic", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.synthetic:
        syn = yaml.safe_load((REPO / "tests" / "fixtures" / "honesty" / "synthetic.yaml").read_text(encoding="utf-8"))
        base_hard, _ = judge([ChartMeta(**syn["base"])])
        rows = []
        for c in syn["cases"]:
            hard, _ = judge([ChartMeta(**{**syn["base"], **c["over"]})])
            rows.append({"rule": c["rule"], "inject": c["over"], "expect": c["expect"],
                         "hard": {k: v for k, v in hard.items() if v}, "ok": bool(hard[c["expect"]])})
        rep = {"schema_version": 1, "role": "20 §5.3 위반 주입 9건 — 전부 hard 여야 한다(D-0084 작업 5)",
               "base_hard": sum(len(v) for v in base_hard.values()), "cases": rows, "all_hard": all(r["ok"] for r in rows)}
    else:
        chk = json.loads((a.proj / "prev" / "checks.json").read_text(encoding="utf-8"))
        items = [i for i in chk["items"] if i["id"] in CHECK_IDS]
        rep = {"schema_version": 1, "project": a.proj.name, "checks_items": len(chk["items"]), "checks_hard": chk["hard"],
               "honesty_hard": sum(i["count"] for i in items), "items": items}
    a.out.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(a.out, rep.get("all_hard", rep.get("honesty_hard")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
